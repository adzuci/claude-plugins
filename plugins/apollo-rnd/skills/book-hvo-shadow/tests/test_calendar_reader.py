"""Tests for calendar_reader.py pure helpers — no network."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import calendar_reader


_VALID_EVENT = {
    "summary": "Exclusive Customer Onboarding",
    "status": "confirmed",
    "id": "abc123",
    "start": {"dateTime": "2026-06-20T10:00:00-07:00"},
    "end": {"dateTime": "2026-06-20T10:45:00-07:00"},
    "conferenceData": {
        "entryPoints": [
            {"entryPointType": "video", "uri": "https://meet.google.com/abc-defg-hij"}
        ]
    },
}


def test_parse_slot_valid() -> None:
    slot = calendar_reader.parse_slot(_VALID_EVENT, "Ana Mejia", "ana.mejia@apollomail.io")
    assert slot is not None
    assert slot["member_name"] == "Ana Mejia"
    assert slot["meet_link"] == "https://meet.google.com/abc-defg-hij"
    assert slot["start"] == "2026-06-20T10:00:00-07:00"


def test_parse_slot_wrong_title() -> None:
    event = dict(_VALID_EVENT, summary="Team Sync")
    assert calendar_reader.parse_slot(event, "Ana Mejia", "ana.mejia@apollomail.io") is None


def test_parse_slot_cancelled() -> None:
    event = dict(_VALID_EVENT, status="cancelled")
    assert calendar_reader.parse_slot(event, "Ana Mejia", "ana.mejia@apollomail.io") is None


def test_parse_slot_no_meet_link_from_description() -> None:
    event = {
        "summary": "Exclusive Customer Onboarding",
        "status": "confirmed",
        "id": "xyz",
        "start": {"dateTime": "2026-06-21T09:00:00-07:00"},
        "end": {"dateTime": "2026-06-21T09:45:00-07:00"},
        "description": "Join here: https://meet.google.com/zzz-yyy-xxx more text",
    }
    slot = calendar_reader.parse_slot(event, "Sergio Vega", "sergio.vega@apollomail.io")
    assert slot is not None
    assert slot["meet_link"] == "https://meet.google.com/zzz-yyy-xxx"


def test_format_slot_label_contains_name() -> None:
    slot = calendar_reader.parse_slot(_VALID_EVENT, "Ana Mejia", "ana.mejia@apollomail.io")
    assert slot is not None
    label = calendar_reader.format_slot_label(slot)
    assert "Ana Mejia" in label
