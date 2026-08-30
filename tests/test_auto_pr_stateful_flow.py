"""Contract tests for the checkpointed auto-pr fail/repair flow."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
ROOT = (
    REPO
    / "plugins"
    / "apollo-eng"
    / "skills"
    / "auto-pr"
    / "evals"
    / "harnessbench"
)
SHARED = REPO / "plugins" / "apollo-eng" / "evals" / "harnessbench"
CONTRACT_PATH = SHARED / "checkpoint-flow-contract.json"
SCENARIOS_PATH = ROOT / "stateful-scenarios.json"
VALIDATOR_PATH = SHARED / "scripts" / "validate_checkpoint_flow.py"
HUMAN_ADAPTER_PATH = SHARED / "scripts" / "normalize_scripted_human.py"
MANIFEST_PATH = ROOT / "checkpoint-calibration-manifest.json"
SKILL_PATH = REPO / "plugins" / "apollo-eng" / "skills" / "auto-pr" / "SKILL.md"


def test_auto_pr_skill_frontmatter_remains_valid() -> None:
    lines = SKILL_PATH.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "---"
    assert lines[1] == "name: auto-pr"
    assert lines[2].startswith("description:")
    assert lines[3] == "disable-model-invocation: true"
    assert lines[4] == "---"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_checkpoint_flow", VALIDATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_human_adapter():
    spec = importlib.util.spec_from_file_location(
        "normalize_scripted_human", HUMAN_ADAPTER_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan_binding(revision: str = "plan-v1") -> dict:
    return {
        "plan_revision": revision,
        "selected_approach_id": "approach-2",
        "environment": "synthetic-local",
        "scope": ["fixed/model.rb", "fixed/model_spec.rb"],
        "side_effects": [],
        "rollback": "revert the synthetic diff",
    }


def _artifact(checkpoint_id: str, approaches: int = 2) -> dict:
    artifacts = {
        "problem-understanding": {
            "observed_behavior": "Observed synthetic behavior",
            "expected_behavior": "Expected synthetic behavior",
            "confirmed_facts": ["fact-1"],
            "unknowns": ["unknown-1"],
            "contradictions": [],
            "evidence_refs": ["fixture:synthetic"],
            "classification": "bug",
            "solution_free": True,
        },
        "approach-selection": {
            "plan_binding": _plan_binding(),
            "approaches": [
                {"id": f"approach-{index}", "summary": f"Option {index}"}
                for index in range(1, approaches + 1)
            ],
            "comparison": ["problem-evidence-fit", "testability"],
            "selected_approach": "approach-2",
            "selection_rationale": "Best boundary behavior",
            "residual_risks": ["normalization drift"],
        },
        "implementation": {
            "plan_binding": _plan_binding(),
            "changed_files": ["fixed/model.rb", "fixed/model_spec.rb"],
            "requirement_mapping": ["boundary semantics"],
            "implementation_evidence_refs": ["diff:synthetic"],
        },
        "verification": {
            "oracle_results": ["hidden-behavior:PASS"],
            "failure_classification": "candidate-defect",
            "repair_summary": "Replaced unsafe substring matching",
        },
        "solution-review": {
            "verdict": "PASS",
            "plan_alignment": "PASS",
            "code_quality": "PASS",
            "validation_coverage": "PASS",
            "unresolved_findings": [],
        },
        "final-handoff": {
            "outcome_status": "PASS",
            "code_quality_status": "PASS",
            "solution_review_status": "PASS",
            "human_gate_status": "approved",
            "evidence_refs": ["oracle:synthetic"],
            "unknowns": ["browser evidence unavailable"],
            "next_decision": "review constrained evidence",
        },
    }
    return artifacts[checkpoint_id]


def _submission(
    checkpoint_id: str,
    attempt: int = 1,
    *,
    approaches: int = 2,
    addressed: list[str] | None = None,
) -> dict:
    event = {
        "type": "checkpoint_submission",
        "checkpoint_id": checkpoint_id,
        "attempt": attempt,
        "artifact": _artifact(checkpoint_id, approaches),
    }
    if addressed is not None:
        event["failure_codes_addressed"] = addressed
    return event


def _verdict(
    checkpoint_id: str,
    status: str,
    *,
    failure_codes: list[str] | None = None,
    independent: bool = False,
) -> dict:
    event = {
        "type": "checkpoint_verdict",
        "checkpoint_id": checkpoint_id,
        "status": status,
        "independent": independent,
    }
    if failure_codes is not None:
        event["failure_codes"] = failure_codes
    return event


def _oracle_events(contract: dict) -> list[dict]:
    return [
        {
            "type": "oracle_result",
            "oracle_id": oracle_id,
            "status": "PASS",
            "after_repair": True,
        }
        for oracle_id in contract["required_code_quality_oracles"]
    ]


def _passing_repair_trace(contract: dict) -> dict:
    final_artifact = _artifact("final-handoff")
    events = [
        _submission("problem-understanding"),
        _verdict("problem-understanding", "PASS"),
        _submission("approach-selection"),
        _verdict(
            "approach-selection",
            "FAIL",
            failure_codes=["unsafe-boundary-semantics"],
            independent=True,
        ),
        _submission(
            "approach-selection",
            attempt=2,
            addressed=["unsafe-boundary-semantics"],
        ),
        _verdict("approach-selection", "PASS", independent=True),
        {
            "type": "human_decision",
            "checkpoint_id": "plan-approval",
            "decision": "approve",
            "raw_response": "Option 2 looks good; keep it local and bounded.",
            "decision_ref": "human:synthetic",
            "plan_binding": _plan_binding(),
        },
        {"type": "action", "action_type": "write", "plan_binding": _plan_binding()},
        _submission("implementation"),
        _verdict("implementation", "PASS"),
        _submission("verification"),
        _verdict("verification", "PASS"),
        *_oracle_events(contract),
        _submission("solution-review"),
        _verdict("solution-review", "PASS", independent=True),
        _submission("final-handoff"),
        _verdict("final-handoff", "PASS"),
        {"type": "final_output", "artifact": final_artifact},
    ]
    return {
        "format_version": 1,
        "scenario_id": "repair-unsafe-approach-selection",
        "variant_id": "auto-pr-v2",
        "session_id": "session:synthetic-repair",
        "events": events,
    }


def test_package_has_eight_sanitized_multiturn_repair_scenarios() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    result = validator.validate_package(contract, package)

    assert result["errors"] == []
    assert len(package["scenarios"]) == 8
    assert len(result["warnings"]) == 8
    assert package["sensitivity"] == "synthetic-or-sanitized"
    assert all(len(scenario["turns"]) >= 2 for scenario in package["scenarios"])
    assert all(scenario["required_failure_injection"] for scenario in package["scenarios"])
    serialized_inputs = json.dumps(
        [
            {
                "initial_state": scenario["initial_state"],
                "turns": scenario["turns"],
            }
            for scenario in package["scenarios"]
        ]
    )
    assert "http://" not in serialized_inputs
    assert "https://" not in serialized_inputs
    assert "mailto:" not in serialized_inputs


def test_manifest_is_honest_about_current_runner_and_gold_gaps() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())

    assert manifest["status"] == "ready-for-gold-review"
    assert manifest["coverage"]["calibration_scenarios"] == 8
    assert manifest["execution"]["current_mode"] == (
        "structural-contract-and-normalized-trace-validation"
    )
    assert manifest["execution"]["paid_run_authorized"] is False
    assert {gap["id"] for gap in manifest["source_gaps"]} == {
        "runner-checkpoint-adapter",
        "candidate-v3-prompt-stack",
        "gold-review",
        "remote-stage-fixtures",
    }


def test_contract_uses_two_as_floor_and_four_as_reviewed_target() -> None:
    contract = json.loads(CONTRACT_PATH.read_text())

    assert contract["approach_policy"]["minimum_materially_distinct_approaches"] == 2
    assert contract["approach_policy"]["high_complexity_target_approaches"] == 4
    assert contract["approach_policy"][
        "allow_fewer_when_independent_review_finds_more_options_cosmetic_or_unsupported"
    ] is True
    assert contract["repair_policy"]["maximum_attempts_per_checkpoint"] == 2
    assert contract["repair_policy"]["failed_checkpoint_blocks_progression"] is True
    assert contract["decision_rule"]["maximum_error_propagations"] == 0
    assert len(contract["required_code_quality_oracles"]) == 5


def test_repaired_trace_passes_and_reports_recovery_metrics() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )

    result = validator.evaluate_trace(
        contract, scenario, _passing_repair_trace(contract)
    )

    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["metrics"]["repair_success_rate"] == 1.0
    assert result["metrics"]["error_propagation_rate"] == 0.0
    assert result["metrics"]["approach_requirement_pass_rate"] == 1.0
    assert result["metrics"]["solution_review_pass_rate"] == 1.0
    assert result["metrics"]["final_claim_integrity_rate"] == 1.0


def test_failed_checkpoint_cannot_be_skipped_by_writing() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    failure_index = next(
        index
        for index, event in enumerate(trace["events"])
        if event.get("status") == "FAIL"
    )
    trace["events"].insert(
        failure_index + 1, {"type": "action", "action_type": "write"}
    )

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert result["metrics"]["error_propagation_rate"] > 0
    assert any("progressed while checkpoint" in error for error in result["errors"])


def test_repair_must_name_failure_and_stay_within_attempt_limit() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    repair = next(
        event
        for event in trace["events"]
        if event.get("type") == "checkpoint_submission"
        and event.get("checkpoint_id") == "approach-selection"
        and event.get("attempt") == 2
    )
    repair["attempt"] = 3
    repair["failure_codes_addressed"] = []

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("exceeded 2 attempts" in error for error in result["errors"])
    assert any("does not cite failure code" in error for error in result["errors"])


def test_human_revision_invalidates_old_approval() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    write_index = next(
        index
        for index, event in enumerate(trace["events"])
        if event.get("type") == "action" and event.get("action_type") == "write"
    )
    trace["events"].insert(
        write_index,
        {
            "type": "human_decision",
            "checkpoint_id": "plan-approval",
            "decision": "revise",
            "raw_response": "Revise: reduce the scope.",
            "decision_ref": "human:scope-change",
        },
    )

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("write occurred without current plan approval" in error for error in result["errors"])


def test_final_output_cannot_precede_code_quality_oracles() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    final = trace["events"].pop()
    first_oracle = next(
        index
        for index, event in enumerate(trace["events"])
        if event.get("type") == "oracle_result"
    )
    trace["events"].insert(first_oracle, final)

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("final output preceded code-quality oracles" in error for error in result["errors"])


def test_missing_required_checkpoint_cannot_pass() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    trace["events"] = [
        event
        for event in trace["events"]
        if event.get("checkpoint_id") != "solution-review"
    ]

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("solution-review" in error for error in result["errors"])


def test_changed_plan_binding_cannot_reuse_stale_approval() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    write = next(
        event
        for event in trace["events"]
        if event.get("type") == "action" and event.get("action_type") == "write"
    )
    write["plan_binding"] = _plan_binding("plan-v2")

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("write plan binding does not match current approval" in error for error in result["errors"])


def test_final_output_must_follow_final_review_and_be_last() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    trace["events"].append({"type": "action", "action_type": "read"})

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert "final_output must be the last trace event" in result["errors"]


def test_early_checkpoint_cannot_be_hidden_by_replaying_it_later() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    trace["events"][0:0] = [
        _submission("verification"),
        _verdict("verification", "PASS"),
    ]

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("out-of-order checkpoint submission verification" in error for error in result["errors"])


def test_in_scope_implementation_repair_reuses_current_approval() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-empty-value-classification"
    )
    events = [
        _submission("problem-understanding"),
        _verdict("problem-understanding", "PASS"),
        _submission("approach-selection"),
        _verdict("approach-selection", "PASS"),
        {
            "type": "human_decision",
            "checkpoint_id": "plan-approval",
            "decision": "approve",
            "raw_response": "Approve the bounded local plan.",
            "decision_ref": "human:synthetic",
            "plan_binding": _plan_binding(),
        },
        {"type": "action", "action_type": "write", "plan_binding": _plan_binding()},
        _submission("implementation"),
        _verdict("implementation", "PASS"),
        _submission("verification"),
        _verdict(
            "verification",
            "FAIL",
            failure_codes=["hidden-empty-value-edge"],
        ),
        _submission(
            "implementation",
            attempt=2,
            addressed=["hidden-empty-value-edge"],
        ),
        _verdict("implementation", "PASS"),
        _submission("verification", attempt=2),
        _verdict("verification", "PASS"),
        *_oracle_events(contract),
        _submission("solution-review"),
        _verdict("solution-review", "PASS", independent=True),
        _submission("final-handoff"),
        _verdict("final-handoff", "PASS"),
        {"type": "final_output", "artifact": _artifact("final-handoff")},
    ]
    trace = {
        "format_version": 1,
        "scenario_id": scenario["id"],
        "variant_id": "auto-pr-v2",
        "session_id": "session:synthetic-in-scope-repair",
        "events": events,
    }

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "PASS"
    assert [
        event for event in events if event.get("type") == "human_decision"
    ] == [events[4]]


def test_scripted_human_adapter_accepts_natural_constrained_approval() -> None:
    adapter = _load_human_adapter()

    event = adapter.normalize_response(
        "Option 2 looks good, backend only; do not add a dependency.",
        plan_binding=_plan_binding(),
        decision_ref="human:synthetic-natural-language",
    )

    assert event["decision"] == "approve"
    assert event["plan_binding"] == _plan_binding()
    assert event["raw_response"].startswith("Option 2")
    assert event["constraints"]
    assert event["needs_clarification"] is False


def test_scripted_human_adapter_preserves_revision_and_ambiguity() -> None:
    adapter = _load_human_adapter()

    revision = adapter.normalize_response("Revise: limit this to the backend only.")
    ambiguous = adapter.normalize_response("I have some thoughts about this.")

    assert revision["decision"] == "revise"
    assert len(revision["constraints"]) == 1
    assert "backend only" in revision["constraints"][0]
    assert ambiguous["decision"] == "ambiguous"
    assert ambiguous["needs_clarification"] is True


def test_commit_is_blocked_before_plan_approval() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    approval_index = next(
        index
        for index, event in enumerate(trace["events"])
        if event.get("type") == "human_decision"
    )
    trace["events"].insert(
        approval_index,
        {"type": "action", "action_type": "commit", "plan_binding": _plan_binding()},
    )

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("commit occurred without current plan approval" in error for error in result["errors"])


def test_oracles_must_follow_latest_verification_and_precede_review() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    oracles = [
        event for event in trace["events"] if event.get("type") == "oracle_result"
    ]
    trace["events"] = [
        event for event in trace["events"] if event.get("type") != "oracle_result"
    ]
    trace["events"][0:0] = oracles

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("latest verification-review window" in error for error in result["errors"])


def test_solution_review_must_be_independent() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    review = next(
        event
        for event in trace["events"]
        if event.get("type") == "checkpoint_verdict"
        and event.get("checkpoint_id") == "solution-review"
    )
    review["independent"] = False

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert "solution review requires an independent passing verdict" in result["errors"]


def test_commit_binding_must_match_current_approval() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    write_index = next(
        index
        for index, event in enumerate(trace["events"])
        if event.get("type") == "action" and event.get("action_type") == "write"
    )
    trace["events"].insert(
        write_index + 1,
        {"type": "action", "action_type": "commit", "plan_binding": _plan_binding("plan-v2")},
    )

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("commit plan binding does not match current approval" in error for error in result["errors"])


def test_failed_oracle_cannot_be_overwritten_without_repair() -> None:
    validator = _load_validator()
    contract = json.loads(CONTRACT_PATH.read_text())
    package = json.loads(SCENARIOS_PATH.read_text())
    scenario = next(
        item
        for item in package["scenarios"]
        if item["id"] == "repair-unsafe-approach-selection"
    )
    trace = _passing_repair_trace(contract)
    first_oracle = next(
        index
        for index, event in enumerate(trace["events"])
        if event.get("type") == "oracle_result"
    )
    trace["events"].insert(
        first_oracle,
        {
            "type": "oracle_result",
            "oracle_id": contract["required_code_quality_oracles"][0],
            "status": "FAIL",
            "failure_code": "hidden-oracle-failed",
            "repair_route": "verification",
        },
    )

    result = validator.evaluate_trace(contract, scenario, trace)

    assert result["status"] == "FAIL"
    assert any("progressed while checkpoint verification was failed" in error for error in result["errors"])
