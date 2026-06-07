from __future__ import annotations

import pytest

review = pytest.importorskip("incident_review")


def test_normalize_title_strips_firing_marker():
    assert (
        review.normalize_title("[FIRING:3] High 5XX error count [Infra] Cloudflare")
        == "High 5XX error count [Infra] Cloudflare"
    )
    assert review.normalize_title("[RESOLVED:1] DatasourceError") == "DatasourceError"
    assert review.normalize_title("Plain title") == "Plain title"


def test_find_recurring_flags_span_over_24h():
    incidents = [
        {"title": "[FIRING:1] Worker X failing", "created_at": "2026-06-01T00:00:00Z"},
        {"title": "[FIRING:1] Worker X failing", "created_at": "2026-06-03T00:00:00Z"},
        # a one-off should not be flagged
        {"title": "One off", "created_at": "2026-06-02T00:00:00Z"},
    ]
    recurring = review.find_recurring(incidents)
    assert len(recurring) == 1
    assert recurring[0]["title"] == "Worker X failing"
    assert recurring[0]["count"] == 2


def test_find_recurring_ignores_dups_within_24h():
    incidents = [
        {"title": "Flap", "created_at": "2026-06-01T00:00:00Z"},
        {"title": "Flap", "created_at": "2026-06-01T06:00:00Z"},
    ]
    assert review.find_recurring(incidents) == []


def test_flag_no_runbook():
    incidents = [
        {"id": "I1", "title": "Has runbook", "description": "see runbook: notion.so/abc"},
        {"id": "I2", "title": "No runbook", "description": "just an alert"},
    ]
    flagged = review.flag_no_runbook(incidents)
    assert [f["id"] for f in flagged] == ["I2"]


def test_render_review_contains_sections():
    out = review.render_review(
        total=5,
        recurring=[{"title": "T", "count": 3, "first": "a", "last": "b"}],
        no_runbook=[{"id": "I2", "title": "No runbook"}],
    )
    assert "Weekly incident review — 5 incidents" in out
    assert "Recurring failures" in out
    assert "no linked runbook" in out
    assert "The argument" in out
