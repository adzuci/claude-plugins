"""Contract tests for the customer-problem-loop HarnessBench package."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent
ROOT = (
    REPO
    / "plugins"
    / "apollo-eng"
    / "skills"
    / "customer-problem-loop"
    / "evals"
    / "harnessbench"
)
SHARED = REPO / "plugins" / "apollo-eng" / "evals" / "harnessbench"
TASKS = ROOT / "tasks"
EXPERIMENT = ROOT / "experiments" / "customer-problem-loop-smoke" / "experiment.yaml"
STAGE_CONTRACT = ROOT / "stage-contract.json"
CHECKPOINT_CONTRACT = SHARED / "checkpoint-flow-contract.json"
SCENARIOS = ROOT / "stateful-scenarios.json"
AUDITOR = ROOT / "scripts" / "audit_stage_adherence.py"
STAGE_AUDIT_LIB = SHARED / "scripts" / "stage_audit_lib.py"
VALIDATOR = SHARED / "scripts" / "validate_checkpoint_flow.py"
PATCH_BUILDER = ROOT / "scripts" / "build_skill_variant_patch.py"
WORKFLOW = REPO / ".github" / "workflows" / "harnessbench.yml"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assistant(text: str, *tools: dict) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}, *tools],
        },
    }


def _tool(name: str, command: str) -> dict:
    return {"type": "tool_use", "name": name, "input": {"cmd": command}}


def test_package_has_independent_tasks_variants_and_contracts() -> None:
    task_ids = sorted(path.stem for path in TASKS.glob("*.yaml"))
    assert task_ids == [
        "customer-problem-loop-backend-smoke",
        "customer-problem-loop-regression-smoke",
        "customer-problem-loop-validation-recovery-smoke",
        "customer-problem-loop-wrong-premise-smoke",
    ]

    stage_contract = json.loads(STAGE_CONTRACT.read_text(encoding="utf-8"))
    assert sorted(stage_contract["tasks"]) == task_ids
    assert stage_contract["variants"] == [
        "baseline",
        "customer-problem-loop-before",
        "customer-problem-loop-current",
    ]
    assert "S1-approach-selection-before-write" in stage_contract["diagnostic_checks"]
    assert "S1-approach-selection-before-write" not in stage_contract["required_checks"]
    assert "S4-browser-gap-reported" in stage_contract["diagnostic_checks"]

    experiment = EXPERIMENT.read_text(encoding="utf-8")
    for task_id in task_ids:
        assert f"  - {task_id}" in experiment
    for variant in stage_contract["variants"][1:]:
        assert f"  - {variant}" in experiment


def test_checkpoint_package_is_ready_for_gold_review() -> None:
    validator = _load(VALIDATOR, "loopbot_checkpoint_validator")
    contract = json.loads(CHECKPOINT_CONTRACT.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))

    result = validator.validate_package(contract, scenarios)
    assert result["errors"] == []
    assert len(result["warnings"]) == 8


def test_stage_auditor_observes_top_down_flow_without_hard_approach_quota(tmp_path: Path) -> None:
    auditor = _load(AUDITOR, "loopbot_stage_auditor")
    lib = _load(STAGE_AUDIT_LIB, "stage_audit_lib")
    contract = json.loads(STAGE_CONTRACT.read_text(encoding="utf-8"))
    transcript = tmp_path / "customer-problem-loop-backend-smoke-current-transcript.jsonl"
    records = [
        _assistant(
            "customer-problem-loop-backend-smoke customer-problem-loop-current. "
            "Problem brief: observed behavior is missing display_label; confirmed facts come from "
            "the synthetic source and repository; unknowns: none material. Approach 1: add the "
            "method. Approach 2: use a presenter, but that adds scope; compare trade-offs and "
            "recommend approach 1. The authorization approves local scope for the named files and "
            "the plan is to implement, test, and verify in the local environment."
        ),
        _assistant("Inspect repository.", _tool("Bash", "git status --short")),
        _assistant("Implement approved plan.", _tool("apply_patch", "*** Begin Patch")),
        _assistant("Verify.", _tool("Bash", "bin/rspec path/to/spec.rb")),
        _assistant("Lint.", _tool("Bash", "bundle exec rubocop path/to/file.rb")),
        _assistant(
            "Browser verification is unavailable and skipped; push and PR creation are also "
            "unavailable. problem-review: PASS; approach-review: PASS; code-quality: PASS; "
            "solution-quality: constrained; verification: PASS locally; human-gate: preapproved."
        ),
    ]
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
    )

    cell = lib.audit_transcript(transcript, records, contract, auditor.build_checks)
    assert cell["status"] == "PASS"
    assert cell["checks"]["S1-approach-selection-before-write"]["status"] == "PASS"
    assert cell["checks"]["S6-final-quality-handoff"]["status"] == "PASS"


def test_variant_builder_emits_an_applicable_skill_patch(tmp_path: Path) -> None:
    builder = _load(PATCH_BUILDER, "loopbot_patch_builder")
    source = tmp_path / "skill"
    (source / "references").mkdir(parents=True)
    (source / "evals").mkdir()
    (source / "SKILL.md").write_text("---\nname: example\n---\n", encoding="utf-8")
    (source / "references" / "flow.md").write_text("# Flow\n", encoding="utf-8")
    (source / "evals" / "ignored.txt").write_text("ignore\n", encoding="utf-8")

    patch = builder.build_patch(source, PurePosixPath(".claude/skills/example"))
    assert ".claude/skills/example/SKILL.md" in patch
    assert ".claude/skills/example/references/flow.md" in patch
    assert "ignored.txt" not in patch

    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    patch_path = tmp_path / "variant.patch"
    patch_path.write_text(patch, encoding="utf-8")
    subprocess.run(["git", "apply", "--check", str(patch_path)], cwd=target, check=True)


def test_workflow_routes_changes_and_manual_runs_for_both_skills() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert '"plugins/apollo-eng/skills/auto-pr/**"' in workflow
    assert '"plugins/apollo-eng/skills/customer-problem-loop/**"' in workflow
    assert "leadgenie/auto-pr-smoke" in workflow
    assert "leadgenie/customer-problem-loop-smoke" in workflow
    assert "customer-problem-loop-before.patch" in workflow
    assert "customer-problem-loop-current.patch" in workflow
