"""Exercise the documented example through the real local CLI, without a model."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

review = pytest.importorskip("prompt_review")
SKILL = Path(__file__).resolve().parents[1]
EXAMPLE = SKILL / "tests/examples/broken-prompt.json"


def run_cli(bundle, output, *extra):
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts/prompt_review.py"),
         "--bundle", str(bundle), "--output", str(output), *extra],
        capture_output=True, text=True, timeout=30, check=False,
    )
    return result.returncode, json.loads(output.read_text(encoding="utf-8"))


def test_documented_example_finds_both_defects_without_claiming_full_review(tmp_path):
    code, result = run_cli(EXAMPLE, tmp_path / "report.json")
    assert code == 2 and result["decision"] == "incomplete"
    assert {f["rule_id"] for f in result["findings"]} == {"undefined-section", "tool-arguments"}
    assert any(g["code"] == "semantic-review-not-run" for g in result["coverage_gaps"])


def test_corrected_example_preserves_call_and_clears_targeted_findings(tmp_path):
    bundle = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    variant = bundle["prompts"][0]["variants"][0]
    source = bundle["sources"][0]
    text = source["content"].replace("STEP 9", "STEP 1").replace('"id":42', '"id":"42"')
    source.update(content=text, sha256=hashlib.sha256(text.encode()).hexdigest())
    variant["messages"][0]["content"] = text
    variant["call_examples"][0]["arguments"] = {"id": "42"}
    variant["call_examples"][0]["source_quote"] = variant["call_examples"][0]["source_quote"].replace('"id":42', '"id":"42"')
    fixed = tmp_path / "fixed.json"
    fixed.write_text(json.dumps(bundle), encoding="utf-8")
    code, result = run_cli(fixed, tmp_path / "fixed-report.json")
    assert code == 2 and not result["findings"]  # No semantic reviewer was run.
    assert variant["call_examples"][0]["name"] == "lookup"

    # Protocol fixture only; this is not a model evaluation.
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps({"version": 1, "bundle_sha256": review.digest(bundle),
                                   "findings": [], "coverage_gaps": []}), encoding="utf-8")
    code, result = run_cli(fixed, tmp_path / "merged.json", "--semantic-review", str(semantic))
    assert code == 0 and result["decision"] == "pass"
