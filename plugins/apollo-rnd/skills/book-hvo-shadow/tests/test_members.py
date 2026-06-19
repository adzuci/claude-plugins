"""Tests for members.py — pure lookup helpers, no network."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import members


def test_all_members_count() -> None:
    assert len(members.all_members()) == 43


def test_all_calendar_emails_are_apollomail() -> None:
    for email in members.all_calendar_emails():
        assert email.endswith("@apollomail.io"), f"Unexpected domain: {email}"


def test_find_by_exact_name() -> None:
    result = members.find_by_name("Ana Mejia")
    assert result is not None
    cal_email, slack_email = result
    assert cal_email == "ana.mejia@apollomail.io"
    assert slack_email == "ana.mejia@apollo.io"


def test_find_by_partial_name() -> None:
    result = members.find_by_name("perla")
    assert result is not None
    assert result[0] == "perla.salazar@apollomail.io"


def test_find_by_name_case_insensitive() -> None:
    assert members.find_by_name("sergio vega") == members.find_by_name("Sergio Vega")


def test_find_by_name_unknown_returns_none() -> None:
    assert members.find_by_name("Definitely Not A Person") is None


def test_display_name_for() -> None:
    assert members.display_name_for("ana.mejia@apollomail.io") == "Ana Mejia"


def test_display_name_for_unknown_returns_none() -> None:
    assert members.display_name_for("nobody@apollomail.io") is None


def test_no_duplicate_calendar_emails() -> None:
    emails = members.all_calendar_emails()
    assert len(emails) == len(set(emails)), "Duplicate calendar emails found"
