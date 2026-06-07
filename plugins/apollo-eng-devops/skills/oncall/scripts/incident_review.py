"""Review the last week of PagerDuty incidents for recurring failures and runbook gaps.

Usage:
    python3 incident_review.py [--days 7]

Why this matters (the argument the on-call should make every week):
- A recurring alert with no runbook is repeated toil and slow MTTR — each firing restarts
  diagnosis from scratch. Surfacing it once turns N future pages into one fix.
- An incident with no linked runbook/RCA is an undocumented failure mode — the next
  responder inherits zero context.

Pure analysis/rendering helpers live at module scope and are unit-tested.
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import lib

RECURRENCE_GAP_HOURS = 24  # same title firing > this far apart = recurring, not a dup


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Review recent incidents for gaps.")
    p.add_argument("--days", type=int, default=7, help="lookback window in days (default 7)")
    return p.parse_args(argv)


def incidents_endpoint(since: datetime, until: datetime) -> str:
    qs = urllib.parse.urlencode(
        {"since": since.isoformat(), "until": until.isoformat(), "limit": 100},
    )
    return f"/incidents?{qs}"


def normalize_title(title: str) -> str:
    """Strip volatile prefixes/suffixes so repeat firings of one alert group together."""
    t = title.strip()
    # Drop PD/Grafana firing markers like "[FIRING:3] " and "[RESOLVED:1] ".
    for marker in ("[FIRING:", "[RESOLVED:"):
        if marker in t:
            close = t.find("]", t.find(marker))
            if close != -1:
                t = (t[: t.find(marker)] + t[close + 1 :]).strip()
    return t


def find_recurring(incidents: list[dict]) -> list[dict]:
    """Group incidents by normalized title; flag titles that fired across a >24h span.

    Returns one summary dict per recurring title: {title, count, first, last}.
    """
    buckets: dict[str, list[datetime]] = defaultdict(list)
    for inc in incidents:
        created = inc.get("created_at")
        if not created:
            continue
        buckets[normalize_title(inc.get("title", ""))].append(lib.parse_iso(created))
    recurring = []
    for title, times in buckets.items():
        if len(times) < 2:
            continue
        times.sort()
        span = times[-1] - times[0]
        if span >= timedelta(hours=RECURRENCE_GAP_HOURS):
            recurring.append(
                {
                    "title": title,
                    "count": len(times),
                    "first": times[0].isoformat(),
                    "last": times[-1].isoformat(),
                }
            )
    return sorted(recurring, key=lambda r: r["count"], reverse=True)


def _has_runbook_signal(inc: dict) -> bool:
    """Best-effort check that an incident links a runbook/RCA.

    Looks for a runbook/RCA marker in inline fields. Note: PagerDuty serves incident
    notes via a separate sub-resource (``GET /incidents/{id}/notes``), not inline on the
    incident object, so a runbook linked only in a note will be missed here. This is a
    deliberate best-effort signal — false positives in the "no runbook" list are expected
    and cheap (the reviewer just confirms). Fetch notes per-incident if you need higher
    fidelity.
    """
    hay = " ".join(
        str(inc.get(k, "")) for k in ("body_details", "summary", "description", "notes")
    ).lower()
    return any(sig in hay for sig in ("runbook", "/rca", "rca:", "postmortem", "notion.so"))


def flag_no_runbook(incidents: list[dict]) -> list[dict]:
    """Return incidents with no detectable runbook/RCA link."""
    return [
        {"title": inc.get("title", "?"), "id": inc.get("id", "?")}
        for inc in incidents
        if not _has_runbook_signal(inc)
    ]


def render_review(total: int, recurring: list[dict], no_runbook: list[dict]) -> str:
    out = [f"## Weekly incident review — {total} incidents\n"]

    out.append("### Recurring failures (fired across >24h — likely missing a fix)\n")
    if recurring:
        out.append("| Count | First | Last | Alert |")
        out.append("| --- | --- | --- | --- |")
        for r in recurring:
            out.append(f"| {r['count']} | {r['first']} | {r['last']} | {r['title']} |")
    else:
        out.append("_None._")
    out.append("")

    out.append("### Incidents with no linked runbook / RCA\n")
    if no_runbook:
        out.append("| Incident | Title |")
        out.append("| --- | --- |")
        for n in no_runbook:
            out.append(f"| {n['id']} | {n['title']} |")
    else:
        out.append("_None — every incident links a runbook or RCA._")
    out.append("")

    out.append("### The argument")
    out.append(
        "- Each recurring alert above is repeated toil: every firing restarts diagnosis. "
        "Propose a runbook or a fix so the next page is the last."
    )
    out.append(
        "- Each no-runbook incident is an undocumented failure mode. File a runbook ticket "
        "before it pages someone with no context."
    )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=args.days)
    try:
        resp = lib.pd_rest_get(incidents_endpoint(since, until))
    except lib.PdError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    incidents = resp.get("incidents", [])
    print(render_review(len(incidents), find_recurring(incidents), flag_no_runbook(incidents)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
