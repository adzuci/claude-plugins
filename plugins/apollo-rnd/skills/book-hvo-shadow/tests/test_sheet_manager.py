"""Tests for sheet_manager.py pure helpers — no network."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import sheet_manager as sm


# Minimal fake sheet rows: [header] + data rows
_HEADER = [
    "Name of RnD member", "Host for HVO session", "Date", "Time slot",
    "Learnings", "Signed up On", "Attended ( Y/ N)", "Customer showed up ?",
    "Status", "Locked_By", "Locked_At",
]

def _make_rows(*data_rows):
    return [_HEADER] + list(data_rows)


def _confirmed_row(rnd_member, host, date, time_slot, locked_by=""):
    r = [""] * 11
    r[sm.COL_RND_MEMBER] = rnd_member
    r[sm.COL_HOST] = host
    r[sm.COL_DATE] = date
    r[sm.COL_TIME_SLOT] = time_slot
    r[sm.COL_STATUS] = "confirmed"
    r[sm.COL_LOCKED_BY] = locked_by
    return r


def _blocked_row(host, date, time_slot, locked_by, locked_at_iso):
    r = [""] * 11
    r[sm.COL_HOST] = host
    r[sm.COL_DATE] = date
    r[sm.COL_TIME_SLOT] = time_slot
    r[sm.COL_STATUS] = "blocked"
    r[sm.COL_LOCKED_BY] = locked_by
    r[sm.COL_LOCKED_AT] = locked_at_iso
    return r


# ---------------------------------------------------------------------------
# is_slot_taken
# ---------------------------------------------------------------------------

def test_slot_not_taken_empty_sheet() -> None:
    rows = _make_rows()
    assert not sm.is_slot_taken(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT")


def test_slot_taken_confirmed_row() -> None:
    rows = _make_rows(
        _confirmed_row("anshul@apollo.io", "Ana Mejia", "2026-06-20", "10:00 AM PDT")
    )
    assert sm.is_slot_taken(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT")


def test_slot_not_taken_different_host() -> None:
    rows = _make_rows(
        _confirmed_row("anshul@apollo.io", "Sergio Vega", "2026-06-20", "10:00 AM PDT")
    )
    assert not sm.is_slot_taken(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT")


def test_slot_not_taken_different_date() -> None:
    rows = _make_rows(
        _confirmed_row("anshul@apollo.io", "Ana Mejia", "2026-06-21", "10:00 AM PDT")
    )
    assert not sm.is_slot_taken(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT")


def test_slot_taken_fresh_blocked_row_other_user() -> None:
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    rows = _make_rows(
        _blocked_row("Ana Mejia", "2026-06-20", "10:00 AM PDT", "other@apollo.io", now_iso)
    )
    # A live (non-stale) blocked lock from another user counts as taken
    assert sm.is_slot_taken(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT")


def test_slot_not_taken_own_blocked_row_excluded() -> None:
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    rows = _make_rows(
        _blocked_row("Ana Mejia", "2026-06-20", "10:00 AM PDT", "me@apollo.io", now_iso)
    )
    # Post-append re-check: our own blocked row should not block us
    assert not sm.is_slot_taken(
        rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT", exclude_locked_by="me@apollo.io"
    )


def test_slot_taken_stale_blocked_row_excluded_owner() -> None:
    old_iso = (
        datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
    ).isoformat() + "Z"
    rows = _make_rows(
        _blocked_row("Ana Mejia", "2026-06-20", "10:00 AM PDT", "me@apollo.io", old_iso)
    )
    # Stale lock is treated as available even without exclusion
    assert not sm.is_slot_taken(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT")


# ---------------------------------------------------------------------------
# is_lock_stale
# ---------------------------------------------------------------------------

def test_lock_fresh_not_stale() -> None:
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    row = _blocked_row("Ana Mejia", "2026-06-20", "10:00 AM PDT", "other@apollo.io", now_iso)
    assert not sm.is_lock_stale(row)


def test_lock_old_is_stale() -> None:
    old_iso = (
        datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
    ).isoformat() + "Z"
    row = _blocked_row("Ana Mejia", "2026-06-20", "10:00 AM PDT", "other@apollo.io", old_iso)
    assert sm.is_lock_stale(row)


def test_confirmed_row_not_stale() -> None:
    row = _confirmed_row("anshul@apollo.io", "Ana Mejia", "2026-06-20", "10:00 AM PDT")
    assert not sm.is_lock_stale(row)


# ---------------------------------------------------------------------------
# find_row_index
# ---------------------------------------------------------------------------

def test_find_row_index_found() -> None:
    rows = _make_rows(
        _confirmed_row("anshul@apollo.io", "Ana Mejia", "2026-06-20", "10:00 AM PDT", "anshul@apollo.io")
    )
    idx = sm.find_row_index(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT", "anshul@apollo.io")
    assert idx == 2  # 1-indexed: row 1 is header, row 2 is data


def test_find_row_index_not_found() -> None:
    rows = _make_rows()
    assert sm.find_row_index(rows, "Ana Mejia", "2026-06-20", "10:00 AM PDT", "anshul@apollo.io") is None


# ---------------------------------------------------------------------------
# append_booking — verify column alignment and atomic row insertion
# ---------------------------------------------------------------------------

class _FakeSheets:
    """Minimal fake Sheets API that records calls and returns canned data."""

    def __init__(self, rows):
        self._rows = rows
        self.update_calls = []
        self.append_calls = []

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, **_kwargs):
        return self

    def update(self, *, spreadsheetId, range, valueInputOption, body):
        self.update_calls.append({"range": range, "values": body["values"]})
        return self

    def append(self, *, spreadsheetId, range, valueInputOption, insertDataOption, body):
        self.append_calls.append({"range": range, "values": body["values"]})
        return self

    def execute(self):
        # Return rows for read_all_rows, or empty for writes
        return {"values": self._rows}


def _fake_slot(date_iso="2026-07-02T15:00:00Z", member="Ana Ballesteros", meet_link=""):
    return {"start": date_iso, "end": date_iso, "member_name": member, "meet_link": meet_link}


def test_append_booking_uses_append_not_update_for_initial_row():
    """append_booking must use values().append() for atomic row insertion, not update()."""
    rows = _make_rows()  # just header, 1 row total
    fake = _FakeSheets(rows)
    sm.append_booking(fake, _fake_slot(), "anshul@apollo.io")
    assert fake.append_calls, "append() was never called — concurrent bookings may target the same row"


def test_append_booking_anchors_to_a1():
    """append() range must be anchored to A1 to avoid column-shift on sparse rows."""
    rows = _make_rows()
    fake = _FakeSheets(rows)
    sm.append_booking(fake, _fake_slot(), "anshul@apollo.io")
    append_range = fake.append_calls[0]["range"]
    assert append_range.endswith("!A1"), f"Expected range ending in !A1, got: {append_range}"


def test_append_booking_data_in_correct_columns():
    """Booker email must land in column A (index 0), not column I (index 8)."""
    rows = _make_rows()
    fake = _FakeSheets(rows)
    sm.append_booking(fake, _fake_slot(), "anshul@apollo.io")
    written_row = fake.append_calls[0]["values"][0]
    assert written_row[sm.COL_RND_MEMBER] == "anshul@apollo.io", \
        f"Email should be in col A (index {sm.COL_RND_MEMBER}), got: {written_row}"
    assert written_row[sm.COL_HOST] == "Ana Ballesteros", \
        f"Host should be in col B (index {sm.COL_HOST}), got: {written_row}"
