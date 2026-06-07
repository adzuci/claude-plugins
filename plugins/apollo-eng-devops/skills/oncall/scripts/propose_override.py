"""Propose (and, only with --apply, create) a PagerDuty schedule override / shift swap.

Usage:
    python3 propose_override.py --schedule SCHED_ID --user USER_ID \\
        --start YYYY-MM-DDTHH:MM:SSZ --end YYYY-MM-DDTHH:MM:SSZ [--apply]

Dry-run by default: prints the exact REST call without making any change. Pass --apply to
actually create the override. This mirrors the skill's propose-never-apply discipline.
"""

from __future__ import annotations

import argparse
import json
import sys

import lib


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Propose a schedule override.")
    p.add_argument("--schedule", required=True, help="PagerDuty schedule ID")
    p.add_argument("--user", required=True, help="PagerDuty user ID to put on call")
    p.add_argument("--start", required=True, help="override start, ISO-8601 (e.g. 2026-06-10T09:00:00Z)")
    p.add_argument("--end", required=True, help="override end, ISO-8601")
    p.add_argument("--apply", action="store_true", help="actually create the override (default: dry-run)")
    return p.parse_args(argv)


def override_endpoint(schedule_id: str) -> str:
    return f"/schedules/{schedule_id}/overrides"


def override_body(user_id: str, start: str, end: str) -> dict:
    return {
        "override": {
            "start": start,
            "end": end,
            "user": {"id": user_id, "type": "user_reference"},
        }
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    endpoint = override_endpoint(args.schedule)
    body = override_body(args.user, args.start, args.end)

    if not args.apply:
        print("DRY RUN — no change made. To apply, re-run with --apply.\n")
        print(f"POST {endpoint}")
        print(json.dumps(body, indent=2))
        return 0

    try:
        resp = lib.pd_rest_post(endpoint, body)
    except lib.PdError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("Override created:")
    print(json.dumps(resp.get("override", resp), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
