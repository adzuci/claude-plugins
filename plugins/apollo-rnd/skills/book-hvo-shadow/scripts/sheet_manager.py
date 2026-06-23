"""Manage the HVO shadow booking Google Sheet.

The live sheet has these human columns (A–H):
  A: Name of RnD member
  B: Host for HVO session
  C: Date
  D: Time slot
  E: Learnings
  F: Signed up On
  G: Attended ( Y/ N)
  H: Customer showed up ?
Plus four machine columns appended to the right (I–L):
  I: Status        (available / blocked / confirmed)
  J: Locked_By     (email of person holding the optimistic lock)
  K: Locked_At     (ISO 8601 timestamp)
  L: Cal_Event_Id  (Google Calendar event ID for the [Shadow] event)

"One shadow per call" is enforced by checking whether a confirmed row
already exists for the same host + date + time slot before booking.
Stale lock rule: if Status == "blocked" and Locked_At is >30s old → treat as available.
"""

from __future__ import annotations

import datetime
import time
from typing import Any

SHEET_ID = "1icwlNypb9fbtRscv5OY8I6NUTvOnrhZ4mcrxEifK_dE"
SHEET_RANGE = "Sheet1"
HEADER_ROW = 1  # 1-indexed; skip when reading data rows

# Column indices (0-indexed within a row list)
COL_RND_MEMBER = 0   # A
COL_HOST = 1         # B
COL_DATE = 2         # C
COL_TIME_SLOT = 3    # D
COL_LEARNINGS = 4    # E
COL_SIGNED_UP = 5    # F
COL_ATTENDED = 6     # G
COL_CUSTOMER = 7     # H
COL_STATUS = 8        # I
COL_LOCKED_BY = 9    # J
COL_LOCKED_AT = 10   # K
COL_CAL_EVENT_ID = 11  # L

LOCK_TTL_SECONDS = 30


# ---------------------------------------------------------------------------
# Pure helpers (testable without network)
# ---------------------------------------------------------------------------

def _pad(row: list[str], length: int) -> list[str]:
    """Extend row to at least `length` columns with empty strings."""
    return row + [""] * max(0, length - len(row))


def is_slot_taken(
    rows: list[list[str]],
    host: str,
    date: str,
    time_slot: str,
    exclude_locked_by: str | None = None,
) -> bool:
    """Return True if the slot is confirmed or has a live (non-stale) blocked lock.

    Treating non-stale blocked rows as taken prevents two concurrent bookers from
    both passing the pre-check, both appending rows, and both flipping to confirmed.

    Pass exclude_locked_by=booked_by on the post-append re-check so our own blocked
    row is not counted against us — only a competing user's live lock trips it.
    """
    for row in rows[HEADER_ROW:]:
        r = _pad(row, COL_STATUS + 1)
        if (
            r[COL_HOST].strip().lower() != host.strip().lower()
            or r[COL_DATE].strip() != date.strip()
            or r[COL_TIME_SLOT].strip() != time_slot.strip()
        ):
            continue
        status = r[COL_STATUS].strip().lower()
        if status == "confirmed":
            return True
        if status == "blocked" and not is_lock_stale(row):
            if exclude_locked_by is None:
                return True
            r_full = _pad(row, COL_LOCKED_BY + 1)
            if r_full[COL_LOCKED_BY].strip().lower() != exclude_locked_by.strip().lower():
                return True
    return False


def find_row_index(rows: list[list[str]], host: str, date: str, time_slot: str, booked_by: str) -> int | None:
    """Return 1-indexed sheet row for a blocked/confirmed row matching all fields, or None.

    Note: matches on Locked_By (email) rather than a unique token, so concurrent bookings
    by the same user for different slots could theoretically match the wrong row. Acceptable
    given that concurrent bookings by one person are not a real use case here.
    """
    for i, row in enumerate(rows[HEADER_ROW:], start=HEADER_ROW + 1):
        r = _pad(row, COL_LOCKED_BY + 1)
        if (
            r[COL_HOST].strip().lower() == host.strip().lower()
            and r[COL_DATE].strip() == date.strip()
            and r[COL_TIME_SLOT].strip() == time_slot.strip()
            and r[COL_LOCKED_BY].strip().lower() == booked_by.strip().lower()
        ):
            return i
    return None


def is_lock_stale(row: list[str]) -> bool:
    """Return True if the row's optimistic lock has expired."""
    r = _pad(row, COL_LOCKED_AT + 1)
    status = r[COL_STATUS].strip().lower()
    if status != "blocked":
        return False
    locked_at_str = r[COL_LOCKED_AT].strip()
    if not locked_at_str:
        return True
    try:
        locked_at = datetime.datetime.fromisoformat(locked_at_str.replace("Z", "+00:00"))
        age = (datetime.datetime.now(datetime.timezone.utc) - locked_at).total_seconds()
        return age > LOCK_TTL_SECONDS
    except ValueError:
        return True


def find_my_bookings(rows: list[list[str]], booked_by: str) -> list[dict]:
    """Return confirmed bookings belonging to booked_by as a list of dicts with row_index."""
    results = []
    for i, row in enumerate(rows[HEADER_ROW:], start=HEADER_ROW + 1):
        r = _pad(row, COL_CAL_EVENT_ID + 1)
        if (
            r[COL_RND_MEMBER].strip().lower() == booked_by.strip().lower()
            and r[COL_STATUS].strip().lower() == "confirmed"
        ):
            results.append({
                "row_index": i,
                "host": r[COL_HOST].strip(),
                "date": r[COL_DATE].strip(),
                "time": r[COL_TIME_SLOT].strip(),
                "event_id": r[COL_CAL_EVENT_ID].strip(),
            })
    return results


# ---------------------------------------------------------------------------
# Network calls (require credentials)
# ---------------------------------------------------------------------------

def cancel_booking(service, row_index: int) -> None:
    """Blank out a confirmed booking row, freeing the slot."""
    _update_row(service, row_index, _pad([], COL_CAL_EVENT_ID + 1))


def store_cal_event_id(service, row_index: int, event_id: str) -> None:
    """Write the Google Calendar event ID into col L of an existing confirmed row."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=_sheet_row_range(row_index))
        .execute()
    )
    row = result.get("values", [[]])[0] if result.get("values") else []
    updated = _pad(list(row), COL_CAL_EVENT_ID + 1)
    updated[COL_CAL_EVENT_ID] = event_id
    _update_row(service, row_index, updated)


def read_all_rows(service) -> list[list[str]]:
    """Return all rows from the booking sheet (including header)."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=f"{SHEET_RANGE}!A:L")
        .execute()
    )
    return result.get("values", [])


def _sheet_row_range(row_index: int) -> str:
    """Return the A1 range string for a specific 1-indexed row."""
    return f"{SHEET_RANGE}!A{row_index}:L{row_index}"


def _update_row(service, row_index: int, values: list[str]) -> None:
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=_sheet_row_range(row_index),
        valueInputOption="RAW",
        body={"values": [values]},
    ).execute()


def append_booking(service, slot: dict[str, Any], booked_by: str, cal_event_id: str = "") -> dict[str, str]:
    """Attempt to book a slot using an optimistic lock.

    Steps:
    1. Read all rows; check no confirmed booking exists.
    2. Append a new row with Status=blocked + lock fields.
    3. Wait 2s; re-read the row; confirm lock ownership.
    4. If lock held → update Status=confirmed; return success.
    5. If lock stolen → remove our row; return failure with message.

    Returns dict with keys: "success" (bool), "message" (str).
    """
    rows = read_all_rows(service)
    date_str = _format_date(slot["start"])
    time_str = _format_time(slot["start"])

    if is_slot_taken(rows, slot["member_name"], date_str, time_str):
        return {"success": False, "message": "This slot already has a confirmed shadow booking."}

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_row = _pad([], COL_CAL_EVENT_ID + 1)
    new_row[COL_RND_MEMBER] = booked_by
    new_row[COL_HOST] = slot["member_name"]
    new_row[COL_DATE] = date_str
    new_row[COL_TIME_SLOT] = time_str
    new_row[COL_SIGNED_UP] = now_iso
    new_row[COL_STATUS] = "blocked"
    new_row[COL_LOCKED_BY] = booked_by
    new_row[COL_LOCKED_AT] = now_iso

    # Use append() for atomic server-side row insertion — avoids the race where two
    # concurrent callers computing len(rows)+1 target the same row index.
    # Anchor to A1 (not A:K) so Sheets maps values from col A regardless of sparse rows;
    # the A:K range caused an 8-col rightward shift when existing rows lacked A-H data.
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_RANGE}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [new_row]},
    ).execute()

    time.sleep(2)

    # Re-read and find our row
    rows = read_all_rows(service)
    row_index = find_row_index(rows, slot["member_name"], date_str, time_str, booked_by)

    if row_index is None:
        return {"success": False, "message": "Lock verification failed — could not find our row. Please try again."}

    r = _pad(rows[row_index - 1], COL_CAL_EVENT_ID + 1)
    if r[COL_LOCKED_BY].strip().lower() != booked_by.strip().lower():
        # Someone else won the lock; remove our row by blanking it
        _update_row(service, row_index, _pad([], COL_CAL_EVENT_ID + 1))
        return {"success": False, "message": "Another booking was confirmed for this slot just now. Please pick a different slot."}

    if is_slot_taken(rows, slot["member_name"], date_str, time_str, exclude_locked_by=booked_by):
        # A confirmed row or a competing live lock appeared while we were locking
        _update_row(service, row_index, _pad([], COL_CAL_EVENT_ID + 1))
        return {"success": False, "message": "This slot was just taken. Please pick a different slot."}

    # Confirm our booking, storing the calendar event ID
    confirmed_row = list(r)
    confirmed_row[COL_STATUS] = "confirmed"
    confirmed_row[COL_CAL_EVENT_ID] = cal_event_id
    _update_row(service, row_index, confirmed_row)

    return {
        "success": True,
        "message": f"Booked! Shadow slot with {slot['member_name']} on {date_str} at {time_str}.",
        "date": date_str,
        "time": time_str,
        "meet_link": slot.get("meet_link", ""),
        "row_index": row_index,
    }


# ---------------------------------------------------------------------------
# Date/time helpers
# ---------------------------------------------------------------------------

def _mexico_tz():
    import zoneinfo
    return zoneinfo.ZoneInfo("America/Mexico_City")


def _format_date(iso_str: str) -> str:
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(_mexico_tz()).strftime("%Y-%m-%d")
    except Exception:
        return iso_str


def _format_time(iso_str: str) -> str:
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(_mexico_tz()).strftime("%-I:%M %p CT")
    except Exception:
        return iso_str
