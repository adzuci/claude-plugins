from __future__ import annotations

import pytest

dc = pytest.importorskip("drift_check")


def test_clean_plan_has_no_drift_or_changes(load):
    s = dc.summarize_plan(load("plan_clean"))
    assert s["counts"] == {"drift": 0, "cosmetic": 0, "add": 0, "change": 0, "destroy": 0, "replace": 0}
    assert s["drift"] == [] and s["pending"] == []


def test_drift_lists_managed_resources_only(load):
    s = dc.summarize_plan(load("plan_drift"))
    addrs = [d["address"] for d in s["drift"]]
    assert addrs == ["google_compute_firewall.allow_ssh", "google_service_account.ci"]
    assert s["counts"]["drift"] == 2


def test_drift_reports_attribute_names_never_values(load):
    s = dc.summarize_plan(load("plan_drift"))
    fw = s["drift"][0]
    assert fw["action"] == "update"
    assert fw["attrs"] == ["priority", "source_ranges"]
    assert "0.0.0.0/0" not in repr(s)


def test_deleted_outside_terraform(load):
    s = dc.summarize_plan(load("plan_drift"))
    assert s["drift"][1]["action"] == "delete"


def test_pending_counts_and_replace(load):
    s = dc.summarize_plan(load("plan_drift"))
    assert s["counts"] == {"drift": 2, "cosmetic": 1, "add": 1, "change": 1, "destroy": 0, "replace": 1}
    actions = {p["address"]: p["action"] for p in s["pending"]}
    assert actions["google_kms_crypto_key.k"] == "replace"
    assert "google_storage_bucket.logs" not in actions


def test_unknown_after_values_count_as_changed():
    attrs = dc.changed_attrs({"a": 1}, {"a": 1}, {"b": True})
    assert attrs == ["b"]


def test_changed_attrs_limit():
    before = {k: 1 for k in "abcdefgh"}
    after = {k: 2 for k in "abcdefgh"}
    assert dc.changed_attrs(before, after, {}, limit=3) == ["a", "b", "c", "+5"]


def test_top_truncates_resources(load):
    s = dc.summarize_plan(load("plan_drift"), top=1)
    assert len(s["drift"]) == 1 and s["counts"]["drift"] == 2


def test_drift_terraform_would_not_revert_is_cosmetic(load):
    s = dc.summarize_plan(load("plan_drift"))
    assert "google_storage_bucket.logs" not in [d["address"] for d in s["drift"]]
    assert s["counts"]["cosmetic"] == 1


def test_only_cosmetic_drift_is_clean():
    plan = {"resource_drift": [{"address": "a.b", "mode": "managed",
            "change": {"actions": ["update"], "before": {"etag": 1}, "after": {"etag": 2}, "after_unknown": {}}}],
            "resource_changes": []}
    s = dc.summarize_plan(plan)
    assert s["counts"]["drift"] == 0 and s["counts"]["cosmetic"] == 1 and s["drift"] == []
