from __future__ import annotations

import pytest

check_idea_entry = pytest.importorskip("check_idea_entry")


def test_word_count_accepts_hyphenated_words():
    assert check_idea_entry.word_count("High-impact low-effort sequence fix") == 4


def test_clean_terms_limits_to_twelve_words():
    terms = check_idea_entry.clean_terms(
        "Sequences",
        "Hidden Manual Email Step Control",
        "one two three four five six seven eight nine ten",
    )
    assert terms == "Sequences Hidden Manual Email Step Control one two three four five six"


def test_valid_entry_returns_success(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_idea_entry.py",
            "--title",
            "Hidden Sequence Step Control",
            "--description",
            (
                "Customer could not find the manual email step control while building a sequence. "
                + "The action was hidden under a dropdown with no visible affordance, which caused "
                + "support to spend extra time walking through a basic setup path."
            ),
            "--product-area",
            "Sequences",
            "--entry-type",
            "Product Fix",
            "--impact",
            "High",
            "--effort",
            "Low",
            "--who",
            "Professional plan first-time sequence builders",
            "--next-step",
            "Route to Sequences squad for UX review",
        ],
    )

    assert check_idea_entry.main() == 0
    out = capsys.readouterr().out
    assert "OK: draft passes hard checks." in out
    assert "SUGGESTED GLEAN SEARCHES:" in out


def test_invalid_entry_reports_errors_and_warnings(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_idea_entry.py",
            "--title",
            "Sequences",
            "--description",
            "Too short.",
            "--product-area",
            "unknown",
            "--entry-type",
            "Product Fix",
            "--impact",
            "unclear",
            "--effort",
            "TBD",
            "--who",
            "?",
            "--next-step",
            "?",
        ],
    )

    assert check_idea_entry.main() == 1
    out = capsys.readouterr().out
    assert "Idea name must be 3-8 words" in out
    assert "Product Area is uncertain; use Glean or ask a clarification." in out
