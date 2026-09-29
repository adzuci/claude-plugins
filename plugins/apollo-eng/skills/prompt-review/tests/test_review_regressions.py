"""Independent regressions for completeness, schema safety, and source evidence."""
import hashlib
import json

import pytest

review = pytest.importorskip("prompt_review")


def bundle(text="# STEP 1\nFollow STEP 1."):
    return {"version": 1, "repository": "data-platform", "base_sha": "a" * 40, "head_sha": "b" * 40,
            "sources": [{"path": "prompt.md", "content": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}],
            "changed_paths": ["prompt.md"], "discovery_complete": True, "coverage_gaps": [],
            "prompts": [{"id": "sample", "source_path": "prompt.md", "dependencies": ["prompt.md"],
                         "variants": [{"id": "default", "messages": [{"role": "system", "content": text}],
                                       "tools": [], "tools_complete": True, "output_schema": None,
                                       "output_examples": [], "call_examples": [], "required_variables": [],
                                       "provided_variables": [], "deferred_variables": []}]}]}


def complete_review(b):
    return review.review_bundle(b, {"version": 1, "bundle_sha256": review.digest(b), "findings": [], "coverage_gaps": []})


@pytest.mark.parametrize("schema", [{"type": "not-a-type"}, {"$ref": "https://example.invalid/schema"}])
@pytest.mark.parametrize("kind", ["input", "tool-output", "output"])
def test_unexercised_declared_schema_cannot_create_clean_pass(schema, kind):
    b = bundle()
    v = b["prompts"][0]["variants"][0]
    if kind == "output":
        v["output_schema"] = schema
    else:
        v["tools"] = [{"name": "lookup", "input_schema": schema if kind == "input" else {},
                       "output_schema": schema if kind == "tool-output" else None}]
    assert complete_review(b)["decision"] == "incomplete"


def test_pattern_defined_field_is_not_falsely_proven_absent():
    schema = {"type": "object", "additionalProperties": False, "patternProperties": {"^extra_": {"type": "string"}}}
    assert review.field_exists(schema, "extra_owner") is None
    assert review.field_exists({"properties": {"forbidden": False}}, "forbidden") is False


def test_local_references_resolve_without_remote_retrieval(monkeypatch):
    import urllib.request

    def fail_network(*args, **kwargs):
        pytest.fail("Schema validation attempted remote retrieval")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    schema = {"$id": "https://example.invalid/schema", "$defs": {"id": {"type": "string"}}, "$ref": "#/$defs/id"}
    assert review.schema_errors(schema, "x") == []
    assert review.schema_errors(schema, 1)
    with pytest.raises(Exception):
        review.schema_errors({"$id": "https://example.invalid/schema", "$ref": "#/$defs/missing"}, {})


@pytest.mark.parametrize("defined,referenced", [("1.1", "1.9"), ("3A", "3B")])
def test_section_suffixes_do_not_collapse_to_parent_number(defined, referenced):
    r = complete_review(bundle(f"# STEP {defined}\nFollow STEP {referenced}."))
    assert r["decision"] == "findings"
    assert r["findings"][0]["rule_id"] == "undefined-section"


def test_case_insensitive_substep_clean_control():
    assert complete_review(bundle("# STEP 3A\nFollow step 3a."))["decision"] == "pass"


def test_source_only_reference_is_unknown_until_includes_are_assembled():
    b = bundle("# STEP 1\nFollow STEP 2 from the included instructions.")
    b["coverage_gaps"] = [{"code": "runtime-composition-unavailable", "prompt_id": "sample", "required": True,
                            "message": "Included instruction renderer unavailable"}]
    r = complete_review(b)
    assert r["decision"] == "incomplete" and not r["findings"]
    assert any(g["code"] == "section-resolution-unverified" for g in r["coverage_gaps"])


@pytest.mark.parametrize("kind", ["tool-call", "output-example"])
def test_structured_example_cannot_claim_different_value_than_literal_source(kind):
    value = {"name": "lookup", "arguments": {"id": "42"}} if kind == "tool-call" else {"id": "42"}
    quote = f"```{kind}\n{json.dumps(value)}\n```"
    b = bundle(quote)
    v = b["prompts"][0]["variants"][0]
    if kind == "tool-call":
        v["tools"] = [{"name": "lookup", "input_schema": {}}]
        v["call_examples"] = [{"name": "lookup", "arguments": {"id": 42}, "source_quote": quote}]
    else:
        v["output_schema"] = {}
        v["output_examples"] = [{"value": {"id": 42}, "source_quote": quote}]
    assert complete_review(b)["decision"] == "error"
