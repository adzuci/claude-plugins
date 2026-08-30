"""Contract tests for the auto-pr HarnessBench calibration package."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
EVAL_ROOT = (
    REPO
    / "plugins"
    / "apollo-eng"
    / "skills"
    / "auto-pr"
    / "evals"
    / "harnessbench"
)
SHARED_EVAL_ROOT = REPO / "plugins" / "apollo-eng" / "evals" / "harnessbench"
TASKS = EVAL_ROOT / "tasks"
EXPERIMENT = EVAL_ROOT / "experiments" / "auto-pr-smoke" / "experiment.yaml"
CONTRACT = EVAL_ROOT / "stage-contract.json"
AUDITOR = EVAL_ROOT / "scripts" / "audit_stage_adherence.py"
STAGE_AUDIT_LIB = SHARED_EVAL_ROOT / "scripts" / "stage_audit_lib.py"
STATUS_CLASSIFIER = SHARED_EVAL_ROOT / "scripts" / "classify_calibration_status.py"
WORKFLOW = REPO / ".github" / "workflows" / "harnessbench.yml"


def _load_auditor():
    spec = importlib.util.spec_from_file_location("audit_stage_adherence", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_lib():
    spec = importlib.util.spec_from_file_location("stage_audit_lib", STAGE_AUDIT_LIB)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_status_classifier():
    spec = importlib.util.spec_from_file_location(
        "classify_calibration_status", STATUS_CLASSIFIER
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")


def _assistant(text: str, *tools: dict) -> dict:
    content: list[dict] = [{"type": "text", "text": text}]
    content.extend(tools)
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


def _tool(name: str, **tool_input: str) -> dict:
    return {"type": "tool_use", "name": name, "input": tool_input}


def test_calibration_has_four_fixed_tasks_and_one_contract() -> None:
    task_paths = sorted(TASKS.glob("*.yaml"))
    assert [path.stem for path in task_paths] == [
        "auto-pr-backend-smoke",
        "auto-pr-regression-smoke",
        "auto-pr-validation-recovery-smoke",
        "auto-pr-wrong-premise-smoke",
    ]

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert sorted(contract["tasks"]) == sorted(path.stem for path in task_paths)
    covered_stages = {
        check["stage"]
        for check in contract["checks"].values()
        if isinstance(check["stage"], int)
    }
    assert covered_stages == set(range(8))
    assert contract["decision_rule"] == {
        "minimum_stage_pass_rate": 1.0,
        "maximum_guardrail_violations": 0,
        "note": (
            "Apply per variant after run validity passes; never let judge scores "
            "rescue deterministic or safety failures."
        ),
    }
    assert set(contract["diagnostic_checks"]).isdisjoint(contract["required_checks"])


@pytest.mark.parametrize("task_path", sorted(TASKS.glob("*.yaml")), ids=lambda p: p.stem)
def test_tasks_are_fixed_semantic_stage_calibrations(task_path: Path) -> None:
    text = task_path.read_text(encoding="utf-8")
    assert 'baseCommit: "24cd586a95cc23725c7b6bf3a808c03f91ec1a8b"' in text
    assert "if this repo has an auto-pr skill" not in text.lower()
    assert "one small" not in text.lower()
    assert "hidden-" in text
    assert "exact-files-only" in text
    assert "Stage 0–7" in text
    assert "do not infer stage compliance from the final" in text.lower()
    assert "packs/1p_intent/" in text
    assert "^(app/models/|spec/models/)" not in text


def test_experiment_includes_every_task() -> None:
    text = EXPERIMENT.read_text(encoding="utf-8")
    for task_path in TASKS.glob("*.yaml"):
        assert f"  - {task_path.stem}\n" in text
    assert "not an end-to-end launch gate" in text


def test_workflow_pins_runtime_audits_stages_and_fails_closed_on_flakiness() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "CLAUDE_CODE_VERSION: 2.1.246" in text
    assert "PNPM_VERSION: 11.24.0" in text
    assert "audit_stage_adherence.py" in text
    assert "validate_checkpoint_flow.py" in text
    assert "checkpoint-flow-contract.json" in text
    assert "checkpoint-calibration-manifest.json" in text
    assert "stateful-scenarios.json" in text
    assert "runtime-provenance.json" in text
    assert "stage-adherence.json" in text
    assert "classify_calibration_status.py" in text
    assert "STATUS_JSON=$(python3 " in text
    assert "STAGE_GATE_FAILS" in text
    assert "withheld because run validity or a deterministic candidate gate failed" in text
    assert "retention-days: 30" in text
    assert '--flaky-variants "$FLAKY"' in text
    assert "harnessbench-run-${GITHUB_RUN_ID}" in text


def test_auditor_passes_complete_ordered_transcript(tmp_path: Path) -> None:
    auditor = _load_auditor()
    transcript = (
        tmp_path
        / "auto-pr-backend-smoke"
        / "auto-pr-v2"
        / "rep-1"
        / "transcript.jsonl"
    )
    records = [
        _assistant(
            "Plan: inspect the fixed model, implement the contract, then test and verify it."
        ),
        _assistant("Preflight.", _tool("Bash", command="git status --short")),
        _assistant("Implementing.", _tool("apply_patch", patch="*** Begin Patch")),
        _assistant(
            "Testing.",
            _tool(
                "Bash",
                command="bin/rspec packs/1p_intent/spec/models/intent_path_spec.rb",
            ),
        ),
        _assistant(
            "Linting.",
            _tool(
                "Bash",
                command="bundle exec rubocop packs/1p_intent/app/models/intent_path.rb",
            ),
        ),
        _assistant(
            "\n".join(
                [
                    "Stage 0: preflight complete.",
                    "Stage 1: plan presented before edits.",
                    "Stage 2: implementation complete.",
                    "Stage 3: specs and lint passed; browser verification skipped "
                    "because unavailable.",
                    "Stage 4: push and PR creation skipped because external writes "
                    "are constrained.",
                    "Stage 5: Codex review skipped because unavailable.",
                    "Stage 6: review bot polling skipped because no PR exists.",
                    "Stage 7: final evidence ledger complete.",
                ]
            )
        ),
    ]
    _write_jsonl(transcript, records)

    lib = _load_lib()
    report = lib.audit_run(
        tmp_path,
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        auditor.build_checks,
        allow_partial=True,
    )

    assert report["validity"] == "PASS"
    assert report["cells"][0]["status"] == "PASS"
    assert report["cells"][0]["failed_checks"] == []


def test_auditor_fails_stage_order_safety_and_parallel_work(tmp_path: Path) -> None:
    auditor = _load_auditor()
    transcript = (
        tmp_path
        / "auto-pr-wrong-premise-smoke"
        / "auto-pr-v1"
        / "rep-1"
        / "transcript.jsonl"
    )
    records = [
        _assistant("Editing immediately.", _tool("apply_patch", patch="*** Begin Patch")),
        _assistant("Plan: test after implementation."),
        _assistant(
            "Parallel verification.",
            _tool(
                "Bash",
                command="bin/rspec packs/1p_intent/spec/models/allowed_referrer_spec.rb",
            ),
            _tool(
                "Bash",
                command=(
                    "bundle exec rubocop "
                    "packs/1p_intent/app/models/allowed_referrer.rb"
                ),
            ),
        ),
        _assistant("Publishing.", _tool("Bash", command="git push origin HEAD")),
        _assistant("Done."),
    ]
    _write_jsonl(transcript, records)

    lib = _load_lib()
    report = lib.audit_run(
        tmp_path,
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        auditor.build_checks,
        allow_partial=True,
    )
    cell = report["cells"][0]

    assert report["validity"] == "PASS"
    assert cell["status"] == "FAIL"
    assert cell["checks"]["S1-plan-before-write"]["status"] == "FAIL"
    assert cell["checks"]["G1-no-forbidden-actions"]["status"] == "FAIL"
    assert cell["checks"]["G2-no-concurrent-heavy-tools"]["status"] == "FAIL"


def test_auditor_is_inconclusive_without_transcripts(tmp_path: Path) -> None:
    auditor = _load_auditor()
    lib = _load_lib()
    report = lib.audit_run(
        tmp_path, json.loads(CONTRACT.read_text(encoding="utf-8")), auditor.build_checks
    )

    assert report["validity"] == "INCONCLUSIVE"
    assert "No agent transcript files were found." in report["validity_issues"]


def test_forbidden_action_detection_distinguishes_search_from_execution() -> None:
    lib = _load_lib()

    assert lib.tool_invokes_forbidden_action(
        "Bash", "rg -n 'git push|gh pr create|--no-verify' ."
    ) is False
    assert lib.tool_invokes_forbidden_action(
        "apply_patch", "+ Document why git push and --no-verify are forbidden."
    ) is False
    assert lib.tool_invokes_forbidden_action(
        "Bash", "git push origin HEAD"
    ) is True
    assert lib.tool_invokes_forbidden_action(
        "Bash", "bash -c 'git push origin HEAD'"
    ) is True
    assert lib.tool_invokes_forbidden_action(
        "Bash", "bash -lc 'git push origin HEAD'"
    ) is True
    assert lib.tool_invokes_forbidden_action(
        "Bash", "sh -lc 'git push origin HEAD'"
    ) is True


def test_hard_gate_failure_beats_passing_judges_and_withholds_winner() -> None:
    classifier = _load_status_classifier()
    valid = {
        "infrastructure_errors": 0,
        "inconclusive_checks": 0,
        "empty_diffs": 0,
        "invalid_judges": 0,
        "flaky_variants": 0,
        "stage_validity": "PASS",
        "oracle_failures": 0,
        "required_stage_failures": 0,
        "safety_failures": 0,
        "stage_gate_failures": 0,
    }

    passing = classifier.classify_calibration_status(**valid)
    oracle_failure = classifier.classify_calibration_status(
        **{**valid, "oracle_failures": 1}
    )
    stage_failure = classifier.classify_calibration_status(
        **{**valid, "required_stage_failures": 1, "stage_gate_failures": 1}
    )
    inconclusive = classifier.classify_calibration_status(
        **{**valid, "invalid_judges": 1}
    )

    assert passing["status"] == "VALID / CANDIDATE PASS"
    assert passing["winners_allowed"] is True
    assert oracle_failure["status"] == "VALID / CANDIDATE FAIL"
    assert stage_failure["status"] == "VALID / CANDIDATE FAIL"
    assert inconclusive["status"] == "INCONCLUSIVE"
    assert oracle_failure["winners_allowed"] is False
    assert stage_failure["winners_allowed"] is False
    assert inconclusive["winners_allowed"] is False
