"""Swap a user's on-call shifts to a covering user for a PTO window (PagerDuty overrides).

Usage:
    python3 swap_shifts.py --from YYYY-MM-DD [--to YYYY-MM-DD] --cover <user-id> \\
        [--me <user-id>] [--schedule <id>] [--apply]

The common ask: "I'm on PTO June 10–14, hand my shifts to Priya." This resolves the user's
on-call entries in the window (across all their schedules, or one via --schedule), clamps an
override to **only the overlapping portion** of each shift, and hands those windows to the
covering user.

Dry-run by default: prints a preview of every override it would create and changes nothing.
Pass --apply to create them. The SKILL.md drives user/schedule *name* resolution and the
confirm-by-number gate; this script works in resolved PagerDuty IDs.

Pure helpers (window localization, overlap clamping, override assembly) live at module scope
and are unit-tested in tests/test_swap_shifts.py.
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import lib
import propose_override


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Swap on-call shifts to a covering user for a PTO window.")
    p.add_argument("--from", dest="from_date", required=True, help="first PTO day, YYYY-MM-DD (inclusive)")
    p.add_argument("--to", dest="to_date", default=None, help="last PTO day, YYYY-MM-DD (inclusive); default = --from")
    p.add_argument("--cover", required=True, help="covering user's PagerDuty ID")
    p.add_argument("--me", default=None, help="user whose shifts to swap (PD ID); default = current token user")
    p.add_argument("--schedule", default=None, help="restrict to one schedule ID; default = all the user is on")
    p.add_argument("--tz", default=None, help="IANA timezone for interpreting PTO dates; default UTC, or the schedule's own tz when --schedule is given")
    p.add_argument("--apply", action="store_true", help="actually create the overrides (default: dry-run)")
    return p.parse_args(argv)


# --- pure helpers ---------------------------------------------------------------------


def localize_window(from_date: str, to_date: str | None, tzname: str) -> tuple[datetime, datetime]:
    """Return the aware [start, end) datetimes for a PTO range in ``tzname``.

    ``--from 2026-06-10 --to 2026-06-14`` means 2026-06-10T00:00 through 2026-06-15T00:00
    (exclusive end) in the given timezone — i.e. all of the 14th is covered. A missing
    ``to_date`` is treated as a single day equal to ``from_date``.
    """
    tz = ZoneInfo(tzname)
    start_d = datetime.strptime(from_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else start_d
    if end_d < start_d:
        raise ValueError("--to must not be before --from")
    start = datetime.combine(start_d, time.min, tzinfo=tz)
    end = datetime.combine(end_d + timedelta(days=1), time.min, tzinfo=tz)
    return start, end


def clamp_overlap(
    shift_start: datetime,
    shift_end: datetime,
    win_start: datetime,
    win_end: datetime,
) -> tuple[datetime, datetime] | None:
    """Return the [start, end) overlap of a shift with the PTO window, or None if disjoint.

    Clamps to the window so a shift that only partially overlaps PTO is overridden only for
    the overlapping portion — the original on-call keeps the rest of the shift.
    """
    start = max(shift_start, win_start)
    end = min(shift_end, win_end)
    if start >= end:
        return None
    return start, end


def overrides_from_oncalls(
    oncalls: list[dict],
    win_start: datetime,
    win_end: datetime,
    cover_id: str,
    me_id: str,
    cover_name: str | None = None,
) -> list[dict]:
    """Build one override descriptor per on-call entry that overlaps the PTO window.

    Only entries where ``me_id`` is the on-call user are considered. Each descriptor carries
    the schedule, the clamped absolute window, and who is being covered — enough to render a
    preview row and to POST the override. ``cover_name`` is the covering user's display name
    for a human-readable preview; it falls back to ``cover_id`` when not supplied.
    """
    out: list[dict] = []
    for entry in oncalls:
        user = entry.get("user") or {}
        if user.get("id") != me_id:
            continue
        sched = entry.get("schedule") or {}
        if not sched.get("id"):
            continue  # can't build /schedules/<id>/overrides without a schedule id
        start_s, end_s = entry.get("start"), entry.get("end")
        if not start_s or not end_s:
            continue  # permanent/unbounded entries aren't PTO-swappable as a window
        clamped = clamp_overlap(
            lib.parse_iso(start_s), lib.parse_iso(end_s), win_start, win_end
        )
        if clamped is None:
            continue
        c_start, c_end = clamped
        out.append(
            {
                "schedule_id": sched.get("id"),
                "schedule_name": sched.get("summary") or sched.get("id"),
                "current_user": user.get("summary") or user.get("id"),
                "cover_id": cover_id,
                "cover_name": cover_name or cover_id,
                "start": c_start.isoformat(),
                "end": c_end.isoformat(),
            }
        )
    return out


def render_preview(overrides: list[dict], tzname: str) -> str:
    """Render the mandatory before-write preview: one numbered row per override."""
    if not overrides:
        return "Nothing to do — no on-call shifts overlap the PTO window."
    lines = [
        f"Timezone for interpretation: {tzname}",
        "",
        "| # | Schedule | Currently on call | → Covered by | Override window (absolute) |",
        "| - | -------- | ----------------- | ------------ | -------------------------- |",
    ]
    for i, o in enumerate(overrides, 1):
        cover = o.get("cover_name") or o["cover_id"]
        cover_label = f"{cover} ({o['cover_id']})" if cover != o["cover_id"] else o["cover_id"]
        lines.append(
            f"| {i} | {o['schedule_name']} | {o['current_user']} | {cover_label} "
            f"| {o['start']} → {o['end']} |"
        )
    return "\n".join(lines)


# --- I/O orchestration ----------------------------------------------------------------


def _oncalls_endpoint(me_id: str, win_start: datetime, win_end: datetime, schedule_id: str | None) -> str:
    # Pad the fetch window by a day each side so shifts that straddle the PTO boundary in a
    # schedule's local timezone aren't dropped (the precise clamp still uses the exact window).
    params = {
        "user_ids[]": me_id,
        "since": (win_start - timedelta(days=1)).isoformat(),
        "until": (win_end + timedelta(days=1)).isoformat(),
    }
    if schedule_id:
        params["schedule_ids[]"] = schedule_id
    return "/oncalls?" + urllib.parse.urlencode(params, safe="[]")


def _resolve_me(me_arg: str | None) -> str:
    if me_arg:
        return me_arg
    data = lib.pd_rest_get("/users/me")
    return (data.get("user") or {}).get("id", "")


def _resolve_user_name(user_id: str) -> str:
    """Best-effort display name for a user id; falls back to the id if lookup fails."""
    try:
        data = lib.pd_rest_get(f"/users/{user_id}")
    except lib.PdError:
        return user_id
    return (data.get("user") or {}).get("name") or (data.get("user") or {}).get("summary") or user_id


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        me_id = _resolve_me(args.me)
        if not me_id:
            print("Could not resolve the current user. Pass --me <user-id>.", file=sys.stderr)
            return 1
        # Timezone: prefer an explicit --tz, else the target schedule's tz, else UTC.
        tzname = args.tz or "UTC"
        if not args.tz and args.schedule:
            sched = lib.pd_rest_get(f"/schedules/{args.schedule}")
            tzname = (sched.get("schedule") or {}).get("time_zone") or "UTC"
        win_start, win_end = localize_window(args.from_date, args.to_date, tzname)
        oncalls = lib.pd_rest_get(
            _oncalls_endpoint(me_id, win_start, win_end, args.schedule)
        ).get("oncalls", [])
        cover_name = _resolve_user_name(args.cover)
    except lib.PdError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    overrides = overrides_from_oncalls(
        oncalls, win_start, win_end, args.cover, me_id, cover_name=cover_name
    )
    print(render_preview(overrides, tzname))
    if not overrides:
        return 0

    if not args.apply:
        print("\nDRY RUN — no overrides created. Re-run with --apply after confirming.")
        return 0

    print("\nCreating overrides:")
    for o in overrides:
        endpoint = propose_override.override_endpoint(o["schedule_id"])
        body = propose_override.override_body(o["cover_id"], o["start"], o["end"])
        try:
            resp = lib.pd_rest_post(endpoint, body)
        except lib.PdError as exc:
            print(f"  FAILED on {o['schedule_name']}: {exc}", file=sys.stderr)
            print("  Stopping — some overrides above may already be applied.", file=sys.stderr)
            return 2
        ov = resp.get("override", resp)
        print(f"  {o['schedule_name']}: override {ov.get('id', '?')} → {o['cover_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
