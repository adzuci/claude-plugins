"""Read HVO team member calendars to find shadow-eligible slots.

Fetches "Exclusive Customer Onboarding" events for one or all HVO members,
returning structured slot dicts. Pure parsing helpers are at module scope
so they can be unit-tested without network access.
"""

from __future__ import annotations

import datetime
from typing import Any

EVENT_TITLE = "Exclusive Customer Onboarding"
LOOKAHEAD_DAYS = 14


# ---------------------------------------------------------------------------
# Pure helpers (testable without network)
# ---------------------------------------------------------------------------

def parse_slot(event: dict[str, Any], member_name: str, member_email: str) -> dict[str, Any] | None:
    """Extract a slot dict from a raw Calendar API event dict.

    Returns None if the event is not a valid shadow slot.
    """
    if EVENT_TITLE.lower() not in event.get("summary", "").lower():
        return None
    if event.get("status") == "cancelled":
        return None

    start_raw = event.get("start", {})
    end_raw = event.get("end", {})

    start_str = start_raw.get("dateTime") or start_raw.get("date")
    end_str = end_raw.get("dateTime") or end_raw.get("date")
    if not start_str or not end_str:
        return None

    # Extract Meet/Zoom link from description or conferenceData
    meet_link = ""
    conf = event.get("conferenceData", {})
    for ep in conf.get("entryPoints", []):
        if ep.get("entryPointType") == "video":
            meet_link = ep.get("uri", "")
            break
    if not meet_link:
        desc = event.get("description", "") or ""
        for word in desc.split():
            if word.startswith("https://meet.google.com") or word.startswith("https://zoom.us"):
                meet_link = word.strip()
                break

    return {
        "member_name": member_name,
        "member_email": member_email,
        "start": start_str,
        "end": end_str,
        "meet_link": meet_link,
        "event_id": event.get("id", ""),
        "summary": event.get("summary", ""),
    }


def format_slot_label(slot: dict[str, Any]) -> str:
    """Return a human-readable one-liner for a slot."""
    try:
        dt = datetime.datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
        local = dt.astimezone()
        date_str = local.strftime("%a %b %-d, %Y")
        time_str = local.strftime("%-I:%M %p %Z")
    except Exception:
        date_str = slot["start"]
        time_str = ""
    return f"{slot['member_name']} — {date_str} at {time_str}"


# ---------------------------------------------------------------------------
# Network calls (require credentials)
# ---------------------------------------------------------------------------

MEXICO_TZ = "America/Mexico_City"


def date_window(anchor: str | None) -> tuple[str, str]:
    """Return (timeMin, timeMax) ISO strings for a single calendar day in Mexico City time.

    anchor: YYYY-MM-DD string (interpreted as Mexico City date), or None for today onward (14 days).
    """
    import zoneinfo
    mx = zoneinfo.ZoneInfo(MEXICO_TZ)
    if anchor:
        base = datetime.datetime.strptime(anchor, "%Y-%m-%d").replace(tzinfo=mx)
        t_min = base.isoformat()
        t_max = (base + datetime.timedelta(days=1)).isoformat()
    else:
        t_min = datetime.datetime.now(mx).isoformat()
        t_max = (datetime.datetime.now(mx) + datetime.timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    return t_min, t_max


def filter_by_time_range(slots: list[dict[str, Any]], time_from: str | None, time_to: str | None) -> list[dict[str, Any]]:
    """Filter slots whose start time (in Mexico City time) falls within [time_from, time_to).

    time_from / time_to: "HH:MM" strings in 24h Mexico City time, or None to skip that bound.
    """
    if not time_from and not time_to:
        return slots
    import zoneinfo
    mx = zoneinfo.ZoneInfo(MEXICO_TZ)
    result = []
    for slot in slots:
        try:
            dt = datetime.datetime.fromisoformat(slot["start"].replace("Z", "+00:00")).astimezone(mx)
            slot_hhmm = dt.strftime("%H:%M")
            if time_from and slot_hhmm < time_from:
                continue
            if time_to and slot_hhmm >= time_to:
                continue
            result.append(slot)
        except Exception:
            result.append(slot)
    return result


def fetch_slots(creds, calendar_emails: list[str], member_name_fn, date: str | None = None) -> list[dict[str, Any]]:
    """Fetch upcoming shadow slots for a list of HVO calendar emails.

    Args:
        creds: Google OAuth credentials.
        calendar_emails: List of @apollomail.io calendar emails to query.
        member_name_fn: Callable(calendar_email) -> display_name.
        date: Optional YYYY-MM-DD anchor date. Fetches that date ± 1 day.
              If None, fetches the next 14 days.

    Returns:
        List of slot dicts sorted by start time.
    """
    googleapiclient = __import__("googleapiclient.discovery", fromlist=["build"])
    service = googleapiclient.build("calendar", "v3", credentials=creds)

    now, future = date_window(date)

    slots: list[dict[str, Any]] = []
    for email in calendar_emails:
        try:
            result = (
                service.events()
                .list(
                    calendarId=email,
                    timeMin=now,
                    timeMax=future,
                    singleEvents=True,
                    orderBy="startTime",
                    q=EVENT_TITLE,
                )
                .execute()
            )
            member_name = member_name_fn(email) or email
            for event in result.get("items", []):
                slot = parse_slot(event, member_name, email)
                if slot:
                    slots.append(slot)
        except Exception as exc:
            import sys
            print(f"  [skip] {email}: {exc}", file=sys.stderr)

    slots.sort(key=lambda s: s["start"])
    return slots
