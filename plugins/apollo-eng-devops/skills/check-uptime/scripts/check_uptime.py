#!/usr/bin/env python3
"""Pull Apollo uptime from Better Stack and build a severity-weighted report.

Severity model
--------------
Not all downtime is equal. A failed background job (Sidekiq worker, cron,
heartbeat, queue drain) usually retries and is not directly visible to users,
so it is treated as LESS impactful than downtime on a user-facing surface such
as app.apollo.io or the public API. Every monitor is classified into a tier:

    user-facing  weight 1.0   (the default — unknown/critical monitors are
                               never under-weighted)
    background   weight 0.2   (heartbeats and anything whose name or url looks
                               like a job/worker/cron/queue)

The headline availability number is a severity-weighted mean, so background
downtime moves it less than the same downtime on a user-facing monitor. The
plain unweighted mean is also shown for reference. Tune SEVERITY_WEIGHTS below
to change how much background downtime discounts.

Auth
----
Reads the Better Stack Uptime API token from the ``BETTERSTACK_API_TOKEN``
environment variable and sends it as ``Authorization: Bearer <token>``. The
token is never printed. Apollo's status page (status.apollo.io) is backed by
Better Stack team t76664.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

API_BASE = "https://uptime.betterstack.com/api/v2"
INCIDENTS_URL = "https://uptime.betterstack.com/api/v3/incidents"
TEAM = "t76664"

# The client only ever talks to Better Stack over https. Every request URL is
# validated against these before it is opened (see _http_get).
ALLOWED_SCHEME = "https"
ALLOWED_HOST = "uptime.betterstack.com"

# Severity weights per tier. The headline availability is a weighted mean using
# these; lower weight => that tier's downtime moves the headline number less.
# Tweak these to change how heavily background downtime is discounted.
SEVERITY_WEIGHTS = {"user-facing": 1.0, "background": 0.2}

# If a monitor's name or url contains one of these, it is a background job.
BACKGROUND_KEYWORDS = [
    "heartbeat",
    "worker",
    "cron",
    "sidekiq",
    "job",
    "queue",
    "async",
    "background",
    "batch",
]


# --- Pure helpers (importable, no network) ------------------------------------


def classify_monitor(name: str, url: str) -> str:
    """Return "background" if name/url looks like a job, else "user-facing".

    Defaults to "user-facing" so unknown or critical monitors are never
    accidentally under-weighted.
    """
    haystack = f"{name or ''} {url or ''}".lower()
    for keyword in BACKGROUND_KEYWORDS:
        if keyword in haystack:
            return "background"
    return "user-facing"


def severity_weight(tier: str) -> float:
    """Weight for a severity tier; unknown tiers fall back to user-facing."""
    return SEVERITY_WEIGHTS.get(tier, SEVERITY_WEIGHTS["user-facing"])


def format_duration(seconds) -> str:
    """Render a duration in seconds as "1h 34m", "8m 12s", or "0s"."""
    total = int(round(seconds or 0))
    if total <= 0:
        return "0s"
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def weighted_availability(rows) -> float:
    """Severity-weighted mean of availability across rows.

    Each row is a dict with "availability" (percent) and "tier". Background
    rows contribute less, so background downtime discounts the headline less.
    """
    total_weight = 0.0
    total = 0.0
    for row in rows:
        weight = severity_weight(row.get("tier", "user-facing"))
        total += weight * float(row.get("availability", 0.0))
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return total / total_weight


def _plain_mean(rows) -> float:
    if not rows:
        return 0.0
    return sum(float(r.get("availability", 0.0)) for r in rows) / len(rows)


def _fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def _monitor_table(rows) -> str:
    lines = [
        "| Monitor | Availability | Downtime | Incidents |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        down_flag = " ⚠️ DOWN" if row.get("status") == "down" else ""
        lines.append(
            f"| {row['name']}{down_flag} | {_fmt_pct(row['availability'])} | "
            f"{format_duration(row.get('total_downtime', 0))} | "
            f"{row.get('number_of_incidents', 0)} |"
        )
    return "\n".join(lines)


def _incident_date(value):
    """Best-effort parse of a Better Stack timestamp to a date; None if absent.

    Tolerates ISO ("2026-07-18T09:11:00Z") and space-separated
    ("2026-07-18 09:11 UTC") forms by reading the leading YYYY-MM-DD.
    """
    if not value:
        return None
    head = str(value).strip().replace("T", " ")[:10]
    try:
        return datetime.strptime(head, "%Y-%m-%d").date()
    except ValueError:
        return None


def filter_incidents_to_window(incidents, frm, to):
    """Keep only incidents whose active interval overlaps ``[frm, to]``.

    An incident with no ``resolved_at`` is still open, so it is kept when it
    started on or before ``to``. Incidents with an unparseable ``started_at``
    are kept (conservative — never silently hide a real incident).
    """
    kept = []
    for inc in incidents:
        start = _incident_date(inc.get("started_at"))
        end = _incident_date(inc.get("resolved_at"))
        if start is None:
            kept.append(inc)
            continue
        if start > to:
            continue
        if end is not None and end < frm:
            continue
        kept.append(inc)
    return kept


def build_report(monitors_rows, incidents, heartbeats_rows, frm, to) -> str:
    """Assemble the two-tier markdown uptime report.

    Heartbeats are always background. The user-facing table comes first; the
    background table is labeled as lower severity.
    """
    all_rows = list(monitors_rows) + list(heartbeats_rows)
    user_rows = [r for r in all_rows if r.get("tier") == "user-facing"]
    bg_rows = [r for r in all_rows if r.get("tier") == "background"]
    down_user = [r["name"] for r in user_rows if r.get("status") == "down"]
    down_bg = [r["name"] for r in bg_rows if r.get("status") == "down"]

    out = [
        "# Apollo Uptime Report",
        "",
        f"Window: {frm.isoformat()} → {to.isoformat()} ({(to - frm).days} days)",
        f"Source: Better Stack team {TEAM} (status.apollo.io)",
        "",
        f"Overall availability (severity-weighted): "
        f"{_fmt_pct(weighted_availability(all_rows) if all_rows else 0.0)}",
        f"Unweighted mean (reference): {_fmt_pct(_plain_mean(all_rows))}",
        "Background-job downtime is treated as lower impact than user-facing "
        "(app.apollo.io) downtime, so it moves the headline number less.",
        "",
        f"**Currently down (user-facing): {', '.join(down_user)}**"
        if down_user
        else "Currently down (user-facing): none",
        "",
        "## User-facing monitors",
        "",
        _monitor_table(user_rows) if user_rows else "No user-facing monitors in this window.",
        "",
        "## Background jobs (lower severity)",
        "",
        "These are jobs, workers, and heartbeats. Downtime here is weighted "
        "below user-facing surfaces because a failed background job typically "
        "retries and is not directly user-visible.",
        "",
        _monitor_table(bg_rows) if bg_rows else "No background jobs in this window.",
    ]
    if down_bg:
        out += ["", f"Down background jobs (lower impact): {', '.join(down_bg)}"]

    out += ["", "## Recent incidents", ""]
    if incidents:
        for inc in incidents:
            resolved = inc.get("resolved_at")
            state = f"resolved {resolved}" if resolved else "still open"
            out.append(
                f"- **{inc.get('name', 'incident')}** — started "
                f"{inc.get('started_at', '?')}, {state}"
            )
    else:
        out.append("No incidents in this window.")
    out.append("")

    return "\n".join(out)


# --- API client (network; not unit-tested) ------------------------------------


def _token() -> str:
    token = os.environ.get("BETTERSTACK_API_TOKEN")
    if not token:
        sys.exit(
            "BETTERSTACK_API_TOKEN is not set. Export your Better Stack Uptime "
            "API token (Uptime → API tokens) and rerun."
        )
    return token


def _http_get(url: str, token: str) -> dict:
    """GET a Better Stack API URL over https, guarding the scheme and host.

    Validates the URL is https on ``uptime.betterstack.com`` before opening it,
    so a URL built at runtime can never be pointed at ``file://`` or an
    arbitrary host (SSRF). Sends the token as a bearer header.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != ALLOWED_SCHEME or parts.hostname != ALLOWED_HOST:
        raise ValueError(
            f"refusing to fetch non-https or off-host URL: {url.split('?')[0]}"
        )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310 - scheme+host validated above (https, uptime.betterstack.com only)
        return json.loads(resp.read().decode("utf-8"))


def _get(url: str) -> dict:
    try:
        return _http_get(url, _token())
    except urllib.error.HTTPError as exc:  # never leak the token
        sys.exit(f"Better Stack API error {exc.code} for {url.split('?')[0]}")


def _paginate(url: str):
    """Yield every ``data`` item across pages, following pagination.next."""
    while url:
        payload = _get(url)
        for item in payload.get("data", []):
            yield item
        url = (payload.get("pagination") or {}).get("next")


def list_monitors():
    return list(_paginate(f"{API_BASE}/monitors?per_page=50"))


def get_sla(monitor_id, frm: date, to: date) -> dict:
    url = f"{API_BASE}/monitors/{monitor_id}/sla?from={frm.isoformat()}&to={to.isoformat()}"
    return (_get(url).get("data") or {}).get("attributes", {})


def list_incidents():
    return list(_paginate(f"{INCIDENTS_URL}?per_page=50"))


def list_heartbeats():
    return list(_paginate(f"{API_BASE}/heartbeats?per_page=50"))


def get_heartbeat_availability(heartbeat_id, frm: date, to: date) -> dict:
    url = f"{API_BASE}/heartbeats/{heartbeat_id}/availability?from={frm.isoformat()}&to={to.isoformat()}"
    return (_get(url).get("data") or {}).get("attributes", {})


# --- Assembly / CLI -----------------------------------------------------------


def _matches(monitor, needle: str) -> bool:
    """Case-insensitive name/id match, for both monitors and heartbeats.

    Monitors expose ``pronounceable_name``; heartbeats expose ``name``. Check
    both so ``--monitor`` narrows monitors and heartbeats alike.
    """
    if not needle:
        return True
    attrs = monitor.get("attributes", {})
    name = (attrs.get("pronounceable_name") or attrs.get("name") or "").lower()
    return needle.lower() in name or str(monitor.get("id")) == needle


def _sla_row(name, url, status, sla, tier) -> dict:
    # Better Stack can return these attributes as explicit `null` (not a
    # missing key) when a monitor has no data in the window -- e.g. a paused
    # monitor, or one created after the window started. `dict.get(key,
    # default)` only falls back on a missing key, so `or` is used here to also
    # catch the present-but-null case; otherwise float(None) raises.
    return {
        "name": name,
        "tier": tier,
        "status": status,
        "availability": float(sla.get("availability") or 0.0),
        "total_downtime": sla.get("total_downtime") or 0,
        "number_of_incidents": sla.get("number_of_incidents") or 0,
    }


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(description="Better Stack uptime report.")
    parser.add_argument("--from", dest="frm", type=_parse_date, default=None)
    parser.add_argument("--to", dest="to", type=_parse_date, default=None)
    parser.add_argument("--monitor", dest="monitor", default="")
    args = parser.parse_args()

    to = args.to or date.today()
    frm = args.frm or (to - timedelta(days=30))

    monitor_rows = []
    for monitor in list_monitors():
        if not _matches(monitor, args.monitor):
            continue
        attrs = monitor.get("attributes", {})
        name = attrs.get("pronounceable_name") or attrs.get("url") or str(monitor.get("id"))
        url = attrs.get("url", "")
        tier = classify_monitor(name, url)
        sla = get_sla(monitor.get("id"), frm, to)
        monitor_rows.append(_sla_row(name, url, attrs.get("status"), sla, tier))

    heartbeat_rows = []
    for hb in list_heartbeats():
        if not _matches(hb, args.monitor):
            continue
        attrs = hb.get("attributes", {})
        name = attrs.get("name") or attrs.get("url") or str(hb.get("id"))
        sla = get_heartbeat_availability(hb.get("id"), frm, to)
        # Heartbeats are always background.
        heartbeat_rows.append(_sla_row(name, "", attrs.get("status"), sla, "background"))

    incidents = [inc.get("attributes", {}) for inc in list_incidents()]
    incidents = filter_incidents_to_window(incidents, frm, to)

    print(build_report(monitor_rows, incidents, heartbeat_rows, frm, to))


if __name__ == "__main__":
    main()
