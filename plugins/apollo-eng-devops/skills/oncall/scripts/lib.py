"""Shared helpers for the oncall skill — thin wrappers over the PagerDuty CLI (`pd`).

Design notes:
- All functions that touch the CLI take an injectable ``runner`` callable so tests can
  feed canned JSON without invoking ``pd``. The default runner shells out via subprocess.
- Pure helpers (parsing, classification, date windows, rendering) live at module scope
  with no I/O so they can be imported and unit-tested directly.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable, Sequence

# A runner takes the argv list (e.g. ["pd", "rest:get", "-e", "/oncalls"]) and returns
# the process stdout as text. Raises on nonzero exit.
Runner = Callable[[Sequence[str]], str]


class PdError(RuntimeError):
    """Raised when the `pd` CLI is missing or returns a nonzero exit code."""


def _subprocess_runner(argv: Sequence[str]) -> str:
    try:
        proc = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:  # pd not installed
        raise PdError(
            "PagerDuty CLI not found. Install it: `npm install -g @pagerduty/cli`, "
            "then authenticate with `pd login`."
        ) from exc
    if proc.returncode != 0:
        raise PdError(
            f"`{' '.join(argv)}` exited {proc.returncode}: {proc.stderr.strip()}"
        )
    return proc.stdout


# --- CLI wrappers ---------------------------------------------------------------------


def pd_rest_get(endpoint: str, runner: Runner | None = None) -> dict:
    """GET a PagerDuty REST endpoint via `pd rest:get -e <endpoint>` and parse JSON."""
    runner = runner or _subprocess_runner
    raw = runner(["pd", "rest:get", "-e", endpoint])
    return _loads(raw)


def pd_rest_post(endpoint: str, body: dict, runner: Runner | None = None) -> dict:
    """POST a JSON body to a PagerDuty REST endpoint via `pd rest:post`."""
    runner = runner or _subprocess_runner
    raw = runner(["pd", "rest:post", "-e", endpoint, "-d", json.dumps(body)])
    return _loads(raw)


def _loads(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PdError(f"Could not parse `pd` JSON output: {exc}") from exc


# --- pure helpers: schedules ----------------------------------------------------------

# Lowercased substrings that identify a team / role from a schedule's name. Override or
# extend via references/schedules.md when real schedule names differ.
TEAM_PATTERNS: dict[str, tuple[str, ...]] = {
    "devops": ("devops", "dev ops", "sre", "infra"),
    "platform": ("platform", "plat"),
}
ROLE_PATTERNS: dict[str, tuple[str, ...]] = {
    "secondary": ("secondary", "backup", "shadow", "2nd"),
    "primary": ("primary", "1st"),  # checked last so it doesn't shadow "secondary"
}


def _marker_pos(text: str, marker: str) -> int | None:
    """Return the start index of ``marker`` as a whole word in ``text``, else None.

    Whole-word matching (``\\b``) keeps short markers like ``2nd`` from matching inside
    longer tokens such as ``22nd``.
    """
    match = re.search(rf"\b{re.escape(marker)}\b", text)
    return match.start() if match else None


def classify_role(schedule_name: str) -> str:
    """Return 'primary' or 'secondary' inferred from a schedule name.

    Defaults to 'primary' when no secondary marker is present — most teams' default
    rotation is the primary.
    """
    low = schedule_name.lower()
    if any(_marker_pos(low, m) is not None for m in ROLE_PATTERNS["secondary"]):
        return "secondary"
    return "primary"


def classify_team(schedule_name: str) -> str | None:
    """Return 'devops' / 'platform' (or None) inferred from a schedule name.

    When markers for more than one team appear (e.g. a name with both ``platform`` and
    ``infra``), the team whose marker appears **earliest** in the name wins — the leading
    word is treated as the team label. This avoids fixed-dict-order bias.
    """
    low = schedule_name.lower()
    best_team: str | None = None
    best_pos: int | None = None
    for team, markers in TEAM_PATTERNS.items():
        positions = [p for p in (_marker_pos(low, m) for m in markers) if p is not None]
        if not positions:
            continue
        pos = min(positions)
        if best_pos is None or pos < best_pos:
            best_pos, best_team = pos, team
    return best_team


def resolve_schedules(
    schedules: Iterable[dict],
    teams: Sequence[str],
    on_collision: Callable[[tuple[str, str], dict, dict], None] | None = None,
) -> dict[tuple[str, str], dict]:
    """Map (team, role) -> schedule dict for the requested teams.

    ``schedules`` is the ``schedules`` array from ``GET /schedules``. When more than one
    schedule matches the same (team, role), the **first** one wins and later matches are
    dropped. Pass ``on_collision(key, kept, dropped)`` to be notified of each drop so the
    caller can surface it (the default is to silently keep the first match).
    """
    wanted = {t.lower() for t in teams}
    out: dict[tuple[str, str], dict] = {}
    for sched in schedules:
        name = sched.get("name", "") or sched.get("summary", "")
        team = classify_team(name)
        if team is None or team not in wanted:
            continue
        key = (team, classify_role(name))
        if key in out:
            if on_collision is not None:
                on_collision(key, out[key], sched)
            continue
        out[key] = sched
    return out


# --- pure helpers: date windows -------------------------------------------------------


def window_bounds(start: date, weeks: int) -> tuple[date, date]:
    """Return (start, end) dates for a window of ``weeks`` weeks beginning at ``start``."""
    if weeks < 1:
        raise ValueError("weeks must be >= 1")
    return start, start + timedelta(weeks=weeks)


def days_in_window(start: date, end: date) -> list[date]:
    """Inclusive list of dates from start up to (but not including) end."""
    if end <= start:
        raise ValueError("end must be after start")
    return [start + timedelta(days=i) for i in range((end - start).days)]


def iso_z(d: date) -> str:
    """Render a date as a ``Z``-suffixed ISO-8601 UTC midnight timestamp for PD since/until.

    Uses an explicit ``Z`` (not ``+00:00``) to match PagerDuty's examples and to avoid the
    ``%2B00%3A00`` URL-encoding surprise when the value is placed in a query string.
    """
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def parse_iso(ts: str) -> datetime:
    """Parse a PagerDuty ISO-8601 timestamp into an aware datetime (UTC if naive)."""
    cleaned = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
