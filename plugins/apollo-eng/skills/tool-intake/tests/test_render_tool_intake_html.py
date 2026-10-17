from __future__ import annotations

import json
from pathlib import Path

import pytest


renderer = pytest.importorskip("render_tool_intake_html")


def report() -> dict:
    return {
        "tool": {
            "name": "Baseten <script>",
            "primary_classification": "SaaS",
            "homepage_url": "https://www.baseten.co/",
            "logo_url": "https://example.com/logo.png",
            "related_components": [{"name": "Truss CLI", "url": "https://github.com/basetenlabs/truss", "role": "Ancillary client"}],
            "version": "unknown",
        },
        "company": {
            "name": "Baseten",
            "headquarters": "San Francisco, CA",
            "pricing_url": "https://www.baseten.co/pricing/",
            "pricing_summary": "Usage-based",
        },
        "open_source": {"repository_url": "https://github.com/basetenlabs/truss", "stars": 1234, "license": "MIT"},
        "market": {"competitors": [{"name": "Modal", "url": "https://modal.com", "why": "Hosted compute"}]},
        "approval": {
            "status": "NO_MATCH_REVIEW_REQUIRED",
            "summary": "No exact record",
            "scope": "unknown",
            "snapshot_version": "UNCONFIGURED",
            "owner": "Agentic Engineering",
            "apps_db_url": "https://example.com/apps-db",
            "initial_request_url": "https://example.com/request",
        },
        "verdict": {"action": "PREPARE_ZIP_INTAKE", "summary": "Use an isolated exploration path"},
        "evidence": [{"label": "[VERIFIED]", "claim": "Uploads code", "source_url": "https://example.com/docs"}],
        "risks": ["API keys"],
        "policies": [{"title": "AI policy", "relevance": "AI data flow applies", "url": "https://example.com/policy"}],
        "brand_risks": ["No verified jurisdiction concern"],
        "apollo_alternatives": [],
        "gaps": ["Retention"],
        "safe_test": ["Synthetic data only"],
        "intake_packet": {"business_problem": "Model test"},
        "sources": [{"title": "Docs", "url": "https://example.com/docs"}, {"title": "Bad", "url": "javascript:alert(1)"}],
        "generated_at": "2026-07-21T00:00:00Z",
    }


def test_render_is_standalone_and_escapes_content() -> None:
    payload = report()
    payload["tool"]["primary_classification"] = "hybrid"
    output = renderer.render_report(payload)

    assert output.startswith("<!doctype html>")
    assert "Baseten &lt;script&gt;" in output
    assert "javascript:alert" not in output
    assert "Approval not verified" in output
    assert "Synthetic data only" in output
    assert "<script" not in output
    assert "Primary type" in output
    assert "Truss CLI" in output
    assert "https://github.com/basetenlabs/truss" in output
    assert "https://apollo.zip.com/create-workflow-request" in output
    assert "GitHub stars" in output
    assert "1,234" in output
    assert "AI data flow applies" in output
    assert "Customer trust" in output
    assert "https://example.com/logo.png" in output
    assert output.count("<details") == 3
    assert "Evidence and risk" in output
    assert "Apollo fit and alternatives" in output
    assert "Test and intake" in output
    assert "Product site" in output
    assert "Pricing TL;DR" in output
    assert "https://www.baseten.co/pricing/" in output
    assert "Agentic Engineering" in output
    assert "https://example.com/apps-db" in output
    assert "https://example.com/request" in output
    assert 'rel="noopener noreferrer"' in output
    assert 'rel="noreferrer"' not in output
    assert "it does not grant approval" not in output.lower()
    assert "Read-only assessment" not in output


def test_saas_keeps_ancillary_oss_metrics_out_of_maturity_card() -> None:
    output = renderer.render_report(report())

    assert "Truss CLI" in output
    assert "GitHub stars" not in output
    assert "Baseten" in output
    assert "Usage-based" in output


@pytest.mark.parametrize(
    ("status", "expected_class"),
    [("RESTRICTED_OR_DENIED", "danger"), ("STALE_RECONFIRM", "stale")],
)
def test_high_attention_approval_states_have_distinct_styles(status: str, expected_class: str) -> None:
    payload = report()
    payload["approval"]["status"] = status

    output = renderer.render_report(payload)

    assert f'<span class="status {expected_class}">' in output


def test_empty_intake_packet_lists_required_zip_fields_and_links() -> None:
    payload = report()
    payload["intake_packet"] = {}

    output = renderer.render_report(payload)

    assert "Business owner" in output
    assert "Data involved and classification" in output
    assert "#zip-help-desk" in output
    assert "https://apollo.zip.com/create-workflow-request" in output


def test_partial_custom_links_keep_required_zip_handoff() -> None:
    payload = report()
    payload["intake_packet"] = {
        "links": [
            {"title": "Vendor DPA", "url": "https://example.com/dpa"},
            {"title": "Start a Zip request", "url": "https://apollo.zip.com/create-workflow-request"},
        ]
    }

    output = renderer.render_report(payload)

    assert "https://example.com/dpa" in output
    assert "https://apollo.zip.com/create-workflow-request" in output
    assert "https://apolloio.slack.com/archives/C078HCHU1SL" in output
    # One decision link and one deduplicated process link.
    assert output.count("https://apollo.zip.com/create-workflow-request") == 2


def test_intake_guidance_is_marked_for_collection() -> None:
    payload = report()
    payload["intake_packet"] = {"business_owner": "Collect the accountable owner."}

    output = renderer.render_report(payload)

    assert '<li class="needed"><span>Collect</span><strong>Business owner</strong>' in output
    assert "Collect the accountable owner." in output


def test_tbd_intake_value_is_marked_for_collection() -> None:
    payload = report()
    payload["intake_packet"] = {"intended_users": "TBD: pilot scale"}

    output = renderer.render_report(payload)

    assert '<li class="needed"><span>Collect</span><strong>Users and expected scale</strong>' in output


def test_intake_can_omit_a_field_that_is_out_of_scope() -> None:
    payload = report()
    payload["intake_packet"] = {"omit_fields": ["retention_training_and_deletion"]}

    output = renderer.render_report(payload)

    assert "Retention, AI training, and deletion" not in output


def test_validate_requires_core_sections() -> None:
    with pytest.raises(ValueError, match="missing"):
        renderer.validate_report({"tool": {}})


def test_unknown_tool_requires_safe_test_plan() -> None:
    payload = report()
    payload["safe_test"] = []

    with pytest.raises(ValueError, match="safe_test"):
        renderer.validate_report(payload)


def test_deprecated_source_unavailable_is_not_user_facing_state() -> None:
    payload = report()
    payload["approval"]["status"] = "SOURCE_UNAVAILABLE"

    with pytest.raises(ValueError, match="user-facing approval state"):
        renderer.validate_report(payload)


def test_non_string_approval_state_has_clean_validation_error() -> None:
    payload = report()
    payload["approval"]["status"] = []

    with pytest.raises(ValueError, match="user-facing approval state"):
        renderer.validate_report(payload)


def test_report_schema_requires_safe_test_only_for_unknown_approval() -> None:
    schema_path = Path(__file__).parents[1] / "references" / "report-schema.json"
    schema = json.loads(schema_path.read_text())

    assert "safe_test" not in schema["required"]
    assert schema["allOf"][0]["then"]["required"] == ["safe_test"]
    assert set(schema["allOf"][0]["if"]["properties"]["approval"]["properties"]["status"]["enum"]) == {
        "NO_MATCH_REVIEW_REQUIRED",
        "STALE_RECONFIRM",
    }


def test_safe_url_allows_only_http_and_https() -> None:
    assert renderer.safe_url("https://example.com") == "https://example.com"
    assert renderer.safe_url("file:///tmp/private") is None
    assert renderer.safe_url("javascript:alert(1)") is None


def test_unsafe_unlabelled_source_is_not_echoed() -> None:
    payload = report()
    payload["sources"] = [{"url": "javascript:alert(1)"}]

    output = renderer.render_report(payload)

    assert "javascript:alert" not in output
    assert "Source" in output


def test_tool_logo_attributes_escape_quotes() -> None:
    payload = report()
    payload["tool"]["name"] = 'Baseten " onerror="alert(1)'
    payload["tool"]["logo_url"] = 'https://example.com/logo.png?x=" onerror="alert(1)'

    output = renderer.render_report(payload)

    assert '&quot; onerror=&quot;alert(1)' in output
    assert ' onerror="alert(1)"' not in output
