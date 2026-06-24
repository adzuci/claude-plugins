#!/usr/bin/env python3
"""Collect weekly DevOps on-call fatigue telemetry.

The helper can read live PagerDuty and Slack CLI data, or load saved JSON for tests/offline
analysis. It buckets PagerDuty alerts and Slack messages by Monday-start weeks in NAM and
IST shift calendars so the handoff can describe on-call fatigue with evidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import urllib.parse
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 fallback is intentionally explicit.
    ZoneInfo = None  # type: ignore


DEFAULT_CHANNELS = {
    "xfn-devops": "C69FJ9NEM",
    "incident-response": "C0362RC2GR2",
    "devops-alerts": "CCHSWB3DK",
}

SHIFT_WINDOWS = {
    "NAM": {"timezone": "America/New_York", "start": "10:00", "end": "22:00"},
    "IST": {"timezone": "Asia/Kolkata", "start": "08:30", "end": "20:30"},
}

DEVOPS_SERVICE_MARKERS = (
    "devops-high-priority",
    "devops-low-priority",
)
DEVOPS_TEXT_MARKERS = (
    " devops",
    "[infra]",
    "infrastructure",
    "deployment pipeline",
    "cloudflare",
    "runner utilization",
    "es vm disk",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week-of", default=dt.date.today().isoformat(), help="Date inside the target week, YYYY-MM-DD")
    parser.add_argument("--output-json", help="Write metrics JSON")
    parser.add_argument("--markdown", help="Write Markdown summary")
    parser.add_argument("--pd-input-json", help="Saved PagerDuty incidents JSON")
    parser.add_argument("--slack-input-json", help="Saved Slack channel/message JSON")
    parser.add_argument("--pd-bin", default=os.environ.get("PD_BIN", "pd"))
    parser.add_argument("--slack-bin", default=os.environ.get("SLACK_BIN", "slack"))
    parser.add_argument("--channels", default=",".join("%s=%s" % item for item in DEFAULT_CHANNELS.items()))
    parser.add_argument("--skip-pd", action="store_true")
    parser.add_argument("--skip-slack", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def require_zoneinfo() -> None:
    if ZoneInfo is None:
        raise SystemExit("zoneinfo is required; use Python 3.9+")


def parse_clock(value: str) -> dt.time:
    hour, minute = value.split(":", 1)
    return dt.time(int(hour), int(minute))


def monday_for(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def calendar_bounds_utc(week_of: str, timezone_name: str) -> Tuple[dt.datetime, dt.datetime]:
    require_zoneinfo()
    local_zone = ZoneInfo(timezone_name)
    day = dt.datetime.strptime(week_of, "%Y-%m-%d").date()
    start_day = monday_for(day)
    local_start = dt.datetime.combine(start_day, dt.time(0, 0), tzinfo=local_zone)
    local_end = local_start + dt.timedelta(days=7)
    return local_start.astimezone(dt.timezone.utc), local_end.astimezone(dt.timezone.utc)


def iso_for_pd(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_json(stdout: str) -> Any:
    match = re.search(r"(\{|\[)", stdout)
    if not match:
        raise ValueError("no JSON object found in command output: %s" % stdout[:200])
    return json.loads(stdout[match.start() :])


def run_json(argv: List[str]) -> Any:
    proc = subprocess.run(argv, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return extract_json(proc.stdout)


def parse_channels(value: str) -> Dict[str, str]:
    out = {}
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if "=" not in raw:
            raise SystemExit("--channels entries must look like label=CHANNEL_ID")
        label, channel_id = raw.split("=", 1)
        out[label.strip()] = channel_id.strip()
    return out


def pd_endpoint(since: dt.datetime, until: dt.datetime, offset: int = 0, limit: int = 100) -> str:
    query = urllib.parse.urlencode(
        {"since": iso_for_pd(since), "until": iso_for_pd(until), "limit": limit, "offset": offset}
    )
    return "/incidents?%s" % query


def load_pd(args: argparse.Namespace, since: dt.datetime, until: dt.datetime) -> List[Dict[str, Any]]:
    if args.skip_pd:
        return []
    if args.pd_input_json:
        payload = json.loads(pathlib.Path(args.pd_input_json).read_text())
    else:
        incidents: List[Dict[str, Any]] = []
        offset = 0
        limit = 100
        while True:
            payload = run_json([args.pd_bin, "rest:get", "-e", pd_endpoint(since, until, offset, limit)])
            page = payload.get("incidents", []) if isinstance(payload, dict) else []
            incidents.extend(page)
            if not payload.get("more"):
                return incidents
            offset = int(payload.get("offset", offset)) + int(payload.get("limit", limit))
            if not page:
                raise SystemExit("PagerDuty pagination reported more results but returned an empty page")
    if isinstance(payload, list):
        return payload
    return payload.get("incidents", [])


def paginate_slack_history(slack_bin: str, channel_id: str, oldest: float, latest: float) -> List[Dict[str, Any]]:
    cursor = None
    messages = []
    while True:
        cmd = [
            slack_bin,
            "conversations",
            "history",
            "--channel",
            channel_id,
            "--oldest",
            str(oldest),
            "--latest",
            str(latest),
            "--limit",
            "200",
        ]
        if cursor:
            cmd.extend(["--cursor", cursor])
        payload = run_json(cmd)
        messages.extend(payload.get("messages", []))
        cursor = payload.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return messages


def load_slack(args: argparse.Namespace, since: dt.datetime, until: dt.datetime) -> Dict[str, List[Dict[str, Any]]]:
    if args.skip_slack:
        return {}
    channels = parse_channels(args.channels)
    if args.slack_input_json:
        payload = json.loads(pathlib.Path(args.slack_input_json).read_text())
        if isinstance(payload, dict) and "channels" not in payload:
            return payload
        out = {}
        for channel in payload.get("channels", []):
            label = channel.get("label") or channel.get("name") or channel.get("id")
            out[label] = channel.get("messages", [])
        return out
    if not os.environ.get("SLACK_API_TOKEN"):
        raise SystemExit("SLACK_API_TOKEN is required for live Slack CLI mode")
    oldest = since.timestamp()
    latest = until.timestamp()
    return {
        label: paginate_slack_history(args.slack_bin, channel_id, oldest, latest)
        for label, channel_id in channels.items()
    }


def parse_ts(ts: str) -> dt.datetime:
    return dt.datetime.fromtimestamp(float(ts), tz=dt.timezone.utc)


def parse_iso(ts: str) -> Optional[dt.datetime]:
    if not ts:
        return None
    cleaned = ts.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def in_shift(local_dt: dt.datetime, start: dt.time, end: dt.time) -> bool:
    local_time = local_dt.time()
    if start <= end:
        return start <= local_time < end
    return local_time >= start or local_time < end


def shift_key(stamp: dt.datetime, shift_name: str) -> Tuple[str, str]:
    require_zoneinfo()
    spec = SHIFT_WINDOWS[shift_name]
    local = stamp.astimezone(ZoneInfo(spec["timezone"]))
    start = parse_clock(spec["start"])
    end = parse_clock(spec["end"])
    return local.date().isoformat(), "in_shift" if in_shift(local, start, end) else "off_shift"


def is_devops_incident(incident: Dict[str, Any]) -> bool:
    service = ((incident.get("service") or {}).get("summary") or "").lower()
    title = (incident.get("title") or incident.get("summary") or "").lower()
    if any(marker in service for marker in DEVOPS_SERVICE_MARKERS):
        return True
    return any(marker in title for marker in DEVOPS_TEXT_MARKERS)


def in_bounds(stamp: dt.datetime, bounds: Tuple[dt.datetime, dt.datetime]) -> bool:
    return bounds[0] <= stamp < bounds[1]


def summarize_pd(
    incidents: Iterable[Dict[str, Any]],
    calendar_bounds: Dict[str, Tuple[dt.datetime, dt.datetime]],
) -> Dict[str, Any]:
    devops = [inc for inc in incidents if is_devops_incident(inc)]
    calendars: Dict[str, Any] = {}
    repeated = Counter()
    active = 0
    for inc in devops:
        title = inc.get("title") or inc.get("summary") or "unknown"
        repeated[title] += 1
        if inc.get("status") not in ("resolved",):
            active += 1

    for shift_name in SHIFT_WINDOWS:
        by_day: Dict[str, Counter] = defaultdict(Counter)
        for inc in devops:
            created = parse_iso(inc.get("created_at", ""))
            if not created:
                continue
            if not in_bounds(created, calendar_bounds[shift_name]):
                continue
            day, bucket = shift_key(created, shift_name)
            by_day[day][bucket] += 1
        calendars[shift_name] = {
            day: {"in_shift": counts.get("in_shift", 0), "off_shift": counts.get("off_shift", 0)}
            for day, counts in sorted(by_day.items())
        }

    return {
        "total": len(devops),
        "active": active,
        "by_shift_calendar": calendars,
        "repeated_titles": {title: count for title, count in repeated.most_common() if count > 1},
    }


def message_text(message: Dict[str, Any]) -> str:
    return message.get("text") or ""


def summarize_slack(
    channels: Dict[str, List[Dict[str, Any]]],
    calendar_bounds: Dict[str, Tuple[dt.datetime, dt.datetime]],
) -> Dict[str, Any]:
    by_channel: Dict[str, Any] = {}
    calendars: Dict[str, Any] = {name: defaultdict(lambda: defaultdict(Counter)) for name in SHIFT_WINDOWS}
    for label, messages in channels.items():
        nonblank = [m for m in messages if message_text(m).strip()]
        thread_parents = [m for m in nonblank if int(m.get("reply_count") or 0) > 0]
        by_channel[label] = {
            "messages": len(nonblank),
            "thread_parents": len(thread_parents),
            "replies": sum(int(m.get("reply_count") or 0) for m in thread_parents),
        }
        for message in nonblank:
            if "ts" not in message:
                continue
            stamp = parse_ts(message["ts"])
            for shift_name in SHIFT_WINDOWS:
                if not in_bounds(stamp, calendar_bounds[shift_name]):
                    continue
                day, bucket = shift_key(stamp, shift_name)
                calendars[shift_name][day][label][bucket] += 1

    normalized = {}
    for shift_name, day_map in calendars.items():
        normalized[shift_name] = {}
        for day, channel_map in sorted(day_map.items()):
            normalized[shift_name][day] = {}
            for label, counts in sorted(channel_map.items()):
                normalized[shift_name][day][label] = {
                    "in_shift": counts.get("in_shift", 0),
                    "off_shift": counts.get("off_shift", 0),
                }

    return {"by_channel": by_channel, "by_shift_calendar": normalized}


def compute(args: argparse.Namespace) -> Dict[str, Any]:
    nam_start, nam_end = calendar_bounds_utc(args.week_of, "America/New_York")
    ist_start, ist_end = calendar_bounds_utc(args.week_of, "Asia/Kolkata")
    calendar_bounds = {"NAM": (nam_start, nam_end), "IST": (ist_start, ist_end)}
    since = min(nam_start, ist_start)
    until = max(nam_end, ist_end)
    incidents = load_pd(args, since, until)
    slack_channels = load_slack(args, since, until)
    return {
        "week_of": args.week_of,
        "query_window_utc": {"since": iso_for_pd(since), "until": iso_for_pd(until)},
        "calendar_windows_utc": {
            name: {"since": iso_for_pd(bounds[0]), "until": iso_for_pd(bounds[1])}
            for name, bounds in calendar_bounds.items()
        },
        "shift_windows": SHIFT_WINDOWS,
        "channels": parse_channels(args.channels),
        "pagerduty": summarize_pd(incidents, calendar_bounds),
        "slack": summarize_slack(slack_channels, calendar_bounds),
        "caveat": "Slack and PagerDuty counts are API-visible operational telemetry, not a compliance export.",
    }


def markdown(metrics: Dict[str, Any]) -> str:
    lines = [
        "# DevOps On-call Fatigue Telemetry",
        "",
        "- Week containing: `%s`" % metrics["week_of"],
        "- Query window UTC: `%s` to `%s`" % (
            metrics["query_window_utc"]["since"],
            metrics["query_window_utc"]["until"],
        ),
        "- Caveat: %s" % metrics["caveat"],
        "",
        "## PagerDuty",
        "",
        "- DevOps PD alerts: **%s**" % metrics["pagerduty"]["total"],
        "- Active/unresolved at collection time: **%s**" % metrics["pagerduty"]["active"],
        "",
    ]
    for shift_name, days in metrics["pagerduty"]["by_shift_calendar"].items():
        lines.extend(["### PagerDuty by %s calendar" % shift_name, "", "| Day | In shift | Off shift |", "| --- | ---: | ---: |"])
        for day, counts in days.items():
            lines.append("| %s | %s | %s |" % (day, counts["in_shift"], counts["off_shift"]))
        lines.append("")

    repeated = metrics["pagerduty"]["repeated_titles"]
    if repeated:
        lines.extend(["### Repeated PD titles", "", "| Count | Title |", "| ---: | --- |"])
        for title, count in repeated.items():
            lines.append("| %s | %s |" % (count, title.replace("|", "\\|")))
        lines.append("")

    lines.extend(["## Slack", "", "| Channel | Messages | Thread parents | Replies |", "| --- | ---: | ---: | ---: |"])
    for label, row in metrics["slack"]["by_channel"].items():
        lines.append("| %s | %s | %s | %s |" % (label, row["messages"], row["thread_parents"], row["replies"]))
    lines.append("")
    for shift_name, days in metrics["slack"]["by_shift_calendar"].items():
        lines.extend(["### Slack by %s calendar" % shift_name, "", "| Day | Channel | In shift | Off shift |", "| --- | --- | ---: | ---: |"])
        for day, channels in days.items():
            for label, counts in channels.items():
                lines.append("| %s | %s | %s | %s |" % (day, label, counts["in_shift"], counts["off_shift"]))
        lines.append("")
    return "\n".join(lines)


def write(path_text: Optional[str], content: str, dry_run: bool) -> None:
    if not path_text:
        return
    path = pathlib.Path(path_text).expanduser()
    if dry_run:
        print("would write %s" % path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(path)


def main() -> int:
    args = parse_args()
    metrics = compute(args)
    if args.output_json:
        write(args.output_json, json.dumps(metrics, indent=2, sort_keys=True) + "\n", args.dry_run)
    if args.markdown:
        write(args.markdown, markdown(metrics) + "\n", args.dry_run)
    if not args.output_json and not args.markdown:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
