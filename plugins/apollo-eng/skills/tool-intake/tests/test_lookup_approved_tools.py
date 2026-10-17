from __future__ import annotations

import datetime as dt

import pytest


lookup_module = pytest.importorskip("lookup_approved_tools")


def snapshot(expires_at=None) -> dict:
    return {
        "snapshot": {"status": "AUTHORITATIVE"},
        "tools": [{
            "id": "omnigent",
            "names": ["Omnigent"],
            "domains": ["omnigent.ai"],
            "repositories": ["github.com/omnigent-ai/omnigent"],
            "packages": ["omnigent-ai"],
            "expires_at": expires_at,
        }],
    }


def test_matches_name_case_insensitively() -> None:
    result = lookup_module.lookup(snapshot(), "OMNIGENT")
    assert result["result"] == "CANDIDATE_RECORD_REQUIRES_SCOPE_CHECK"


def test_matches_url_domain() -> None:
    result = lookup_module.lookup(snapshot(), "https://www.omnigent.ai/docs")
    assert result["matches"][0]["id"] == "omnigent"


def test_matches_repository_url() -> None:
    result = lookup_module.lookup(snapshot(), "https://github.com/omnigent-ai/omnigent")
    assert result["matches"][0]["id"] == "omnigent"


def test_repository_lookup_does_not_match_every_github_record() -> None:
    payload = snapshot()
    payload["tools"].append(
        {
            "id": "other",
            "names": ["Other"],
            "domains": ["other.example"],
            "repositories": ["github.com/other/project"],
            "packages": [],
            "expires_at": None,
        }
    )

    result = lookup_module.lookup(payload, "https://github.com/omnigent-ai/omnigent")

    assert result["result"] == "CANDIDATE_RECORD_REQUIRES_SCOPE_CHECK"
    assert [item["id"] for item in result["matches"]] == ["omnigent"]


def test_unknown_is_not_a_denial() -> None:
    result = lookup_module.lookup(snapshot(), "https://baseten.co")
    assert result == {"result": "NO_MATCH_REVIEW_REQUIRED", "matches": []}


def test_unconfigured_snapshot_is_unavailable() -> None:
    result = lookup_module.lookup({"snapshot": {"status": "UNCONFIGURED"}, "tools": []}, "omnigent")
    assert result == {"result": "APPROVAL_SOURCE_UNCONFIGURED", "matches": []}


def test_expired_record_requires_reconfirmation() -> None:
    now = dt.datetime(2026, 7, 21, tzinfo=dt.timezone.utc)
    result = lookup_module.lookup(snapshot("2026-07-20T00:00:00Z"), "omnigent", now)
    assert result["result"] == "STALE_RECONFIRM"


def test_url_path_alone_does_not_match_other_records() -> None:
    payload = snapshot()
    payload["tools"].append(
        {"id": "docs", "names": ["docs"], "domains": [], "repositories": [], "packages": ["docs"], "expires_at": None}
    )
    result = lookup_module.lookup(payload, "https://omnigent.ai/docs")
    assert [item["id"] for item in result["matches"]] == ["omnigent"]


@pytest.mark.parametrize("expires_at", ["not-a-date", "2099-01-01T00:00:00"])
def test_malformed_or_naive_expiry_requires_reconfirmation(expires_at: str) -> None:
    result = lookup_module.lookup(snapshot(expires_at), "omnigent")
    assert result["result"] == "STALE_RECONFIRM"
