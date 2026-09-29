import hashlib
import json

import pytest

review = pytest.importorskip("prompt_review")


def bundle(text="# STEP 1\nReturn the result from STEP 1."):
    return {"version": 1, "repository": "data-platform", "base_sha": "a" * 40,
            "head_sha": "b" * 40, "changed_paths": ["prompt.md"],
            "sources": [{"path": "prompt.md", "content": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}],
            "prompts": [{"id": "sample", "source_path": "prompt.md", "dependencies": ["prompt.md"],
                         "variants": [{"id": "default", "messages": [{"role": "system", "content": text}],
                                       "tools": [], "tools_complete": True, "output_schema": None,
                                       "output_examples": [], "call_examples": [], "required_variables": [],
                                       "provided_variables": [], "deferred_variables": []}]}],
            "coverage_gaps": [], "discovery_complete": True}


def semantic(b, **kwargs):
    return {"version": 1, "bundle_sha256": review.digest(b), "findings": [], "coverage_gaps": [], **kwargs}


@pytest.mark.parametrize("invalid", [{}, None, [], {"findings": None}, {"findings": False}, {"findings": 0},
                                    {"findings": ""}, {"findings": {}}, {"findings": []}])
def test_malformed_reviewer_result_never_passes(invalid):
    b = bundle()
    # None means no review, not a completed review with an empty list.
    result = review.review_bundle(b, invalid)
    assert result["decision"] in ("error", "incomplete")


def test_missing_semantic_is_not_clean_pass():
    assert review.review_bundle(bundle())["decision"] == "incomplete"


def test_valid_complete_clean_review_passes():
    b = bundle()
    assert review.review_bundle(b, semantic(b))["decision"] == "pass"


def test_missing_step_survives_extraction():
    b = bundle("# STEP 1\nReturn JSON as specified by STEP 99.")
    r = review.review_bundle(b, semantic(b))
    assert r["decision"] == "findings"
    assert r["findings"][0]["rule_id"] == "undefined-section"
    assert r["findings"][0]["source"]["line"] == 2
    assert r["findings"][0]["blocking"] is False


def test_quoted_counterexample_is_not_deterministic_reference():
    b = bundle('# STEP 1\nInvalid example, do not use:\n```text\nGo to STEP 99\n```')
    assert review.review_bundle(b, semantic(b))["decision"] == "pass"


def test_provided_and_deferred_variables_are_distinct_from_missing():
    b = bundle()
    v = b["prompts"][0]["variants"][0]
    v.update(required_variables=["context", "name"], provided_variables=["context"], deferred_variables=["name"])
    assert review.review_bundle(b, semantic(b))["decision"] == "pass"
    v["deferred_variables"] = []
    assert review.review_bundle(b, semantic(b))["decision"] == "incomplete"


def tool_bundle():
    b = bundle('Call lookup with {"id": "42"}, then read result.owner.')
    v = b["prompts"][0]["variants"][0]
    v["tools"] = [{"name": "lookup", "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"], "additionalProperties": False},
                   "output_schema": {"type": "object", "properties": {"owner": {"type": "string"}}, "additionalProperties": False}}]
    v["call_examples"] = [{"name": "lookup", "arguments": {"id": "42"}, "result_fields": ["owner"],
                           "source_quote": b["sources"][0]["content"]}]
    return b, v


@pytest.mark.parametrize("change,rule", [("arguments", "tool-arguments"), ("tool", "unavailable-tool"),
                                       ("result", "tool-result-field"), ("prerequisite", "tool-prerequisite")])
def test_tool_contract_failures(change, rule):
    b, v = tool_bundle()
    if change == "arguments":
        v["call_examples"][0]["arguments"] = {"id": 42}
    elif change == "tool":
        v["call_examples"][0]["name"] = "invented"
    elif change == "result":
        v["call_examples"][0]["result_fields"] = ["unknown"]
    else:
        v["tools"][0]["requires"] = ["search"]
    assert rule in [f["rule_id"] for f in review.review_bundle(b, semantic(b))["findings"]]


def test_tool_clean_control():
    b, _ = tool_bundle()
    assert review.review_bundle(b, semantic(b))["decision"] == "pass"


def test_unknown_tools_and_open_return_schema_are_incomplete_not_defects():
    b, v = tool_bundle()
    v["tools_complete"] = False
    v["tools"][0]["output_schema"] = {"type": "object"}
    r = review.review_bundle(b, semantic(b))
    assert r["decision"] == "incomplete" and not r["findings"]


def test_external_schema_reference_never_fetched():
    b, v = tool_bundle()
    v["tools"][0]["input_schema"] = {"$ref": "http://127.0.0.1:1/secret"}
    r = review.review_bundle(b, semantic(b))
    assert r["decision"] == "incomplete"
    assert any(g["code"] == "invalid-tool-schema" for g in r["coverage_gaps"])


def test_foreign_and_stale_evidence_rejected():
    b = bundle()
    f = {"rule_id": "contradiction", "prompt_id": "sample", "variant_id": "default", "severity": "high",
         "message": "Issue", "evidence_quote": "not in source", "recommendation": "Fix", "regression_test": "Check"}
    assert review.review_bundle(b, semantic(b, findings=[f]))["decision"] == "error"
    assert review.review_bundle(b, semantic(b, bundle_sha256="f" * 64))["decision"] == "error"
    b["sources"][0]["content"] += "edited"
    assert review.review_bundle(b, semantic(b))["decision"] == "error"


@pytest.mark.parametrize("bad", [None, [], False, {"version": 1}])
def test_invalid_bundle_is_error(bad):
    assert review.review_bundle(bad)["decision"] == "error"


def test_duplicate_tool_and_prompt_ids_are_errors():
    b, v = tool_bundle()
    v["tools"] *= 2
    assert review.review_bundle(b)["decision"] == "error"
    b = bundle()
    b["prompts"] *= 2
    assert review.review_bundle(b)["decision"] == "error"


def test_output_schema_and_missing_schema():
    b = bundle('Return {"score": 101}.')
    v = b["prompts"][0]["variants"][0]
    v["output_schema"] = {"type": "object", "properties": {"score": {"type": "number", "maximum": 100}}}
    v["output_examples"] = [{"value": {"score": 101}, "source_quote": '{"score": 101}'}]
    assert review.review_bundle(b, semantic(b))["findings"][0]["rule_id"] == "output-example"
    v["output_schema"] = None
    assert review.review_bundle(b, semantic(b))["decision"] == "incomplete"


def test_cli_invalid_json_emits_error_file(tmp_path):
    source, output = tmp_path / "bad.json", tmp_path / "report.json"
    source.write_text('{', encoding="utf-8")
    assert review.main(["--bundle", str(source), "--output", str(output)]) == 3
    assert json.loads(output.read_text())["decision"] == "error"


def test_empty_no_change_inventory_is_terminal_pass():
    b = bundle()
    b.update(prompts=[], sources=[], changed_paths=[])
    assert review.review_bundle(b)["decision"] == "pass"
