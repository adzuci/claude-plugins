"""Render the DevOps + Platform primary/secondary on-call schedule for a window.

Usage:
    python3 oncall_schedule.py [--weeks 2] [--teams devops,platform] [--at YYYY-MM-DD]

Shells out to the PagerDuty CLI (`pd`). Pure parsing/rendering helpers are at module
scope and unit-tested in tests/test_oncall_schedule.py.
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from datetime import date, datetime, timezone

import lib


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render the on-call schedule for a window.")
    p.add_argument("--weeks", type=int, default=2, help="window length in weeks (default 2)")
    p.add_argument(
        "--teams",
        default="devops,platform",
        help="comma-separated teams to include (default devops,platform)",
    )
    p.add_argument("--at", default=None, help="window start date YYYY-MM-DD (default today)")
    return p.parse_args(argv)


def _start_date(at: str | None) -> date:
    if at:
        return datetime.strptime(at, "%Y-%m-%d").date()
    return datetime.now(timezone.utc).date()


def oncall_endpoint(schedule_id: str, start: date, end: date) -> str:
    """Build the /oncalls REST path for one schedule over a window."""
    qs = urllib.parse.urlencode(
        {"schedule_ids[]": schedule_id, "since": lib.iso_z(start), "until": lib.iso_z(end)},
        safe="[]",
    )
    return f"/oncalls?{qs}"


def assignment_for_day(oncalls: list[dict], day: date) -> str:
    """Return the user name on call at **12:00 UTC** on ``day`` from /oncalls entries.

    An on-call entry covers [start, end). A null start/end means "always on call".

    The grid has one cell per day, so it samples a single instant — noon UTC, chosen to
    sit clear of the common midnight handoff boundary. A same-day mid-shift handoff will
    therefore show whoever holds the pager at noon, not both holders. Use `pd schedule:show`
    for sub-day resolution.
    """
    target_dt = lib.parse_iso(lib.iso_z(day)).replace(hour=12)
    for entry in oncalls:
        start = entry.get("start")
        end = entry.get("end")
        s = lib.parse_iso(start) if start else None
        e = lib.parse_iso(end) if end else None
        if (s is None or s <= target_dt) and (e is None or target_dt < e):
            user = entry.get("user") or {}
            return user.get("summary") or user.get("name") or "?"
    return "—"


def render_grid(
    days: list[date],
    columns: list[tuple[str, str]],
    assignments: dict[tuple[str, str], list[dict]],
) -> str:
    """Render a markdown table: one row per day, one column per (team, role)."""
    headers = ["Date"] + [f"{team} {role}" for team, role in columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for day in days:
        row = [day.isoformat()]
        for col in columns:
            row.append(assignment_for_day(assignments.get(col, []), day))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    teams = [t.strip() for t in args.teams.split(",") if t.strip()]
    start = _start_date(args.at)
    start, end = lib.window_bounds(start, args.weeks)
    days = lib.days_in_window(start, end)

    def _warn_collision(key: tuple[str, str], kept: dict, dropped: dict) -> None:
        print(
            f"Warning: multiple schedules match {key[0]} {key[1]} — using "
            f"{kept.get('name')!r} ({kept.get('id')}), ignoring {dropped.get('name')!r} "
            f"({dropped.get('id')}). Disambiguate via references/schedules.md.",
            file=sys.stderr,
        )

    try:
        sched_resp = lib.pd_rest_get("/schedules?limit=100")
        resolved = lib.resolve_schedules(
            sched_resp.get("schedules", []), teams, on_collision=_warn_collision
        )
        if not resolved:
            print(
                "No matching schedules found. Check team name patterns in lib.py / "
                "references/schedules.md, or run `pd schedule:list`.",
                file=sys.stderr,
            )
            return 1
        columns = sorted(resolved.keys())
        assignments: dict[tuple[str, str], list[dict]] = {}
        for col, sched in resolved.items():
            resp = lib.pd_rest_get(oncall_endpoint(sched["id"], start, end))
            assignments[col] = resp.get("oncalls", [])
    except lib.PdError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"## On-call schedule — {start.isoformat()} → {end.isoformat()}\n")
    print(render_grid(days, columns, assignments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
