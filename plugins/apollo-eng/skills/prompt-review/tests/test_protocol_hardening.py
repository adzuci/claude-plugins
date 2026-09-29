"""False-pass and false-finding probes independent of benchmark gold."""
import pytest

from test_prompt_review import bundle, semantic
import prompt_review as review


@pytest.mark.parametrize("extra", [{"error": "review failed"}, {"status": "incomplete"}, {"problems": []}])
def test_unrecognized_semantic_envelope_cannot_pass(extra):
    b = bundle()
    assert review.review_bundle(b, semantic(b, **extra))["decision"] == "error"


@pytest.mark.parametrize("text", [
    "# STEP 1\n```text\n~~~\nGo to STEP 99\n~~~\n```",
    "# STEP 1\n````text\n```\nGo to STEP 99\n```\n````",
])
def test_nested_fence_markers_do_not_activate_counterexamples(text):
    b = bundle(text)
    assert review.review_bundle(b, semantic(b))["decision"] == "pass"


def test_real_reference_after_matching_fence_remains_checked():
    b = bundle("# STEP 1\n````text\n```\nGo to STEP 99\n````\nGo to STEP 2")
    result = review.review_bundle(b, semantic(b))
    assert result["decision"] == "findings"
    assert [f["evidence_quote"] for f in result["findings"]] == ["Go to STEP 2"]
