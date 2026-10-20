from __future__ import annotations

import pytest

dc = pytest.importorskip("drift_check")

CLEAN = {"workspace": "gcp-iam", "status": "clean", "run_url": "https://x/runs/r1",
         "counts": {"drift": 0, "cosmetic": 9, "add": 0, "change": 0, "destroy": 0, "replace": 0}, "drift": [], "pending": []}
DRIFT = {"workspace": "gcp-prod", "status": "drift", "run_url": "https://x/runs/r2",
         "counts": {"drift": 2, "cosmetic": 0, "add": 1, "change": 1, "destroy": 0, "replace": 1},
         "drift": [{"address": "google_compute_firewall.allow_ssh", "action": "update", "attrs": ["priority"]}],
         "pending": [{"address": "google_kms_crypto_key.k", "action": "replace", "attrs": ["purpose"]}]}
ERR = {"workspace": "gcp-ops", "status": "error", "error": "timeout after 900s", "run_url": None}


def test_all_clean_is_one_line():
    msg = dc.format_slack([CLEAN], "2026-10-07")
    assert msg.count("\n") <= 1
    assert "no drift" in msg.lower()


def test_drift_section_has_counts_addresses_and_link():
    msg = dc.format_slack([CLEAN, DRIFT], "2026-10-07")
    assert "gcp-prod" in msg and "google_compute_firewall.allow_ssh" in msg
    assert "<https://x/runs/r2|run>" in msg
    assert "1 replace" in msg
    assert "/apollo-eng-devops:resolve-drift gcp-prod" in msg


def test_errors_are_never_reported_as_clean():
    msg = dc.format_slack([CLEAN, ERR], "2026-10-07")
    assert "gcp-ops" in msg and "timeout" in msg
    assert "no drift" not in msg.lower()


def test_overall_status():
    assert dc.overall([CLEAN]) == "clean"
    assert dc.overall([CLEAN, ERR]) == "error"
    assert dc.overall([DRIFT, ERR]) == "drift"


def test_cosmetic_count_is_mentioned_but_not_alarming():
    msg = dc.format_slack([CLEAN], "2026-10-07")
    assert "9 cosmetic" in msg


def test_addresses_are_escaped_for_slack():
    r = dict(DRIFT, drift=[{"address": 'x["<@U123>&`rm`"]', "action": "update", "attrs": ["a<b"]}])
    msg = dc.format_slack([r], "2026-10-07")
    assert "<@U123>" not in msg and "&lt;@U123&gt;&amp;" in msg
    assert "`rm`" not in msg
    assert "a&lt;b" in msg


def test_cosmetic_note_also_shown_when_drift():
    r = dict(DRIFT, counts=dict(DRIFT["counts"], cosmetic=4))
    assert "4 cosmetic" in dc.format_slack([r], "2026-10-07")
