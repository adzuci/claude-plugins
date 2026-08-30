#!/usr/bin/env python3
"""Validate a checkpointed HarnessBench contract, scenarios, and normalized traces.

This is an evaluator/adapter boundary, not a second agent runner. HarnessBench or
another approved stateful runner must normalize its observable checkpoint events
to the trace schema consumed here.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TRACE_EVENT_TYPES = {
    "checkpoint_submission",
    "checkpoint_verdict",
    "human_decision",
    "action",
    "oracle_result",
    "final_output",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return value


def validate_package(
    contract: dict[str, Any], package: dict[str, Any]
) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if contract.get("schema_version") != 1:
        errors.append("checkpoint contract schema_version must be 1")
    checkpoints = contract.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        errors.append("checkpoint contract must define checkpoints")
        checkpoints = []
    checkpoint_ids = [item.get("id") for item in checkpoints if isinstance(item, dict)]
    if len(checkpoint_ids) != len(set(checkpoint_ids)):
        errors.append("checkpoint IDs must be unique")
    orders = [item.get("order") for item in checkpoints if isinstance(item, dict)]
    if orders != list(range(len(checkpoints))):
        errors.append("checkpoint order must be contiguous and start at zero")

    human_checkpoints = contract.get("human_checkpoints", [])
    human_ids = {
        item.get("id") for item in human_checkpoints if isinstance(item, dict)
    }
    known_checkpoints = set(checkpoint_ids) | human_ids
    required_oracles = set(contract.get("required_code_quality_oracles", []))
    if len(required_oracles) < 5:
        errors.append("contract must retain all five code-quality oracle categories")

    if package.get("format_version") != 2:
        errors.append("stateful scenarios format_version must be 2")
    scenarios = package.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("stateful scenarios must be a non-empty list")
        scenarios = []
    scenario_ids = [item.get("id") for item in scenarios if isinstance(item, dict)]
    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("scenario IDs must be unique")

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            errors.append("every scenario must be an object")
            continue
        scenario_id = scenario.get("id", "<missing-id>")
        turns = scenario.get("turns")
        if not isinstance(turns, list) or len(turns) < 2:
            errors.append(f"{scenario_id}: requires at least two turns")
            turns = []
        turn_ids = [turn.get("id") for turn in turns if isinstance(turn, dict)]
        if len(turn_ids) != len(set(turn_ids)):
            errors.append(f"{scenario_id}: turn IDs must be unique")
        for turn in turns:
            if not isinstance(turn, dict) or turn.get("expected_checkpoint") not in known_checkpoints:
                errors.append(f"{scenario_id}: turn references an unknown checkpoint")

        complexity = scenario.get("complexity")
        if complexity not in {"standard", "high", "critical"}:
            errors.append(f"{scenario_id}: complexity must be standard, high, or critical")
        failure = scenario.get("required_failure_injection")
        if not isinstance(failure, dict):
            errors.append(f"{scenario_id}: missing required_failure_injection")
        else:
            if failure.get("checkpoint_id") not in known_checkpoints:
                errors.append(f"{scenario_id}: failure injection checkpoint is unknown")
            route = failure.get("expected_repair_route")
            allowed = contract.get("repair_policy", {}).get("allowed_routes", {}).get(
                failure.get("checkpoint_id"), []
            )
            if route not in allowed:
                errors.append(
                    f"{scenario_id}: repair route {route!r} is not allowed from "
                    f"{failure.get('checkpoint_id')!r}"
                )

        scenario_oracles = set(scenario.get("deterministic_oracles", []))
        missing_oracles = sorted(required_oracles - scenario_oracles)
        if missing_oracles:
            errors.append(
                f"{scenario_id}: missing code-quality oracles {missing_oracles}"
            )
        if not scenario.get("source_pattern_refs"):
            errors.append(f"{scenario_id}: requires source_pattern_refs")
        if not scenario.get("judge_dimensions"):
            errors.append(f"{scenario_id}: requires judge dimensions")
        gold = scenario.get("gold_review", {})
        if gold.get("status") != "approved":
            warnings.append(f"{scenario_id}: gold review is pending")

    return {"errors": errors, "warnings": warnings}


def _checkpoint_fields(contract: dict[str, Any], checkpoint_id: str) -> set[str]:
    for checkpoint in contract["checkpoints"]:
        if checkpoint["id"] == checkpoint_id:
            return set(checkpoint["required_artifact_fields"])
    return set()


def _approval_binding_fields(contract: dict[str, Any]) -> set[str]:
    for checkpoint in contract["human_checkpoints"]:
        if checkpoint["id"] == "plan-approval":
            return set(checkpoint.get("approval_binding_fields", []))
    return set()


def _binding_errors(
    binding: Any, required_fields: set[str], *, label: str
) -> list[str]:
    if not isinstance(binding, dict):
        return [f"{label} needs a plan_binding object"]
    missing = sorted(
        field for field in required_fields if field not in binding or binding[field] in (None, "")
    )
    return [f"{label} plan_binding missing fields {missing}"] if missing else []


def evaluate_trace(
    contract: dict[str, Any], scenario: dict[str, Any], trace: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        return {
            "scenario_id": scenario["id"],
            "status": "INCONCLUSIVE",
            "errors": ["trace has no events"],
            "metrics": {},
        }
    if trace.get("format_version") != 1:
        errors.append("trace format_version must be 1")
    if trace.get("scenario_id") != scenario["id"]:
        errors.append("trace scenario_id does not match selected scenario")
    if not trace.get("session_id"):
        errors.append("trace must identify one primary stateful session")

    checkpoints = contract["checkpoints"]
    checkpoint_ids = {item["id"] for item in checkpoints}
    machine_checkpoint_ids = [
        item["id"] for item in checkpoints if item.get("owner") != "human"
    ]
    machine_checkpoint_set = set(machine_checkpoint_ids)
    checkpoint_order = {item["id"]: item["order"] for item in checkpoints}
    expected_order = 0
    human_ids = {item["id"] for item in contract["human_checkpoints"]}
    failure_spec = scenario["required_failure_injection"]
    max_attempts = contract["repair_policy"]["maximum_attempts_per_checkpoint"]
    required_oracles = set(contract["required_code_quality_oracles"])
    binding_fields = _approval_binding_fields(contract)
    approval_blocked_actions = set(
        next(
            item.get("blocks_actions", [])
            for item in contract["human_checkpoints"]
            if item["id"] == "plan-approval"
        )
    )
    submission_attempts: Counter[str] = Counter()
    submission_indices: dict[str, list[int]] = {}
    last_verdict_submission: dict[str, int] = {}
    pass_indices: dict[str, int] = {}
    latest_artifacts: dict[str, dict[str, Any]] = {}
    latest_passing_approach_binding: dict[str, Any] | None = None
    first_verdict: dict[str, str] = {}
    failure_count = 0
    recovered_count = 0
    propagation_count = 0
    repair_regression_count = 0
    expected_failure_seen = False
    blocked: dict[str, Any] | None = None
    repair_route_started = False
    plan_decisions: list[tuple[int, str]] = []
    active_plan_binding: dict[str, Any] | None = None
    plan_approval_index: int | None = None
    ambiguity_clarifications = 0
    human_decisions: dict[str, list[str]] = {}
    oracle_results: dict[str, tuple[int, str]] = {}
    approach_count = 0
    independent_approach_review = False
    solution_review_pass = False
    final_events: list[tuple[int, dict[str, Any]]] = []

    for index, event in enumerate(events):
        if not isinstance(event, dict) or event.get("type") not in TRACE_EVENT_TYPES:
            errors.append(f"event {index}: unknown or malformed event type")
            continue
        event_type = event["type"]
        checkpoint_id = event.get("checkpoint_id")

        if blocked:
            allowed_repair_event = (
                event_type == "checkpoint_submission"
                and checkpoint_id == blocked["route"]
            ) or (
                repair_route_started
                and event_type == "checkpoint_verdict"
                and checkpoint_id == blocked["route"]
            ) or (
                event_type == "human_decision"
                and blocked["route"] == "plan-approval"
                and checkpoint_id == "plan-approval"
            )
            if event_type not in {"checkpoint_submission", "checkpoint_verdict", "human_decision"}:
                propagation_count += 1
                errors.append(
                    f"event {index}: {event_type} progressed while checkpoint "
                    f"{blocked['checkpoint']} was failed"
                )
            elif not allowed_repair_event:
                propagation_count += 1
                errors.append(
                    f"event {index}: expected repair route {blocked['route']}, got "
                    f"{checkpoint_id}"
                )

        if event_type == "checkpoint_submission":
            if checkpoint_id not in machine_checkpoint_set:
                errors.append(f"event {index}: submission checkpoint is unknown or human-owned")
                continue
            if checkpoint_order[checkpoint_id] != expected_order:
                errors.append(
                    f"event {index}: out-of-order checkpoint submission {checkpoint_id}; "
                    f"expected order {expected_order}"
                )
            attempt = event.get("attempt")
            if not isinstance(attempt, int) or attempt < 1:
                errors.append(f"event {index}: checkpoint attempt must be a positive integer")
                continue
            submission_attempts[checkpoint_id] = max(
                submission_attempts[checkpoint_id], attempt
            )
            submission_indices.setdefault(checkpoint_id, []).append(index)
            if attempt > max_attempts:
                errors.append(
                    f"event {index}: {checkpoint_id} exceeded {max_attempts} attempts"
                )
            artifact = event.get("artifact")
            if not isinstance(artifact, dict):
                errors.append(f"event {index}: checkpoint submission needs an artifact")
                artifact = {}
            missing = sorted(_checkpoint_fields(contract, checkpoint_id) - set(artifact))
            if missing:
                errors.append(
                    f"event {index}: {checkpoint_id} artifact missing fields {missing}"
                )
            latest_artifacts[checkpoint_id] = artifact
            if checkpoint_id == "approach-selection":
                approaches = artifact.get("approaches", [])
                if isinstance(approaches, list):
                    approach_count = max(approach_count, len(approaches))
                errors.extend(
                    _binding_errors(
                        artifact.get("plan_binding"),
                        binding_fields,
                        label=f"event {index}: approach selection",
                    )
                )
                if (
                    isinstance(artifact.get("plan_binding"), dict)
                    and artifact["plan_binding"].get("selected_approach_id")
                    != artifact.get("selected_approach")
                ):
                    errors.append(
                        f"event {index}: selected approach does not match plan binding"
                    )
                if active_plan_binding and artifact.get("plan_binding") != active_plan_binding:
                    active_plan_binding = None
                    plan_approval_index = None
            if checkpoint_id == "implementation":
                errors.extend(
                    _binding_errors(
                        artifact.get("plan_binding"),
                        binding_fields,
                        label=f"event {index}: implementation",
                    )
                )
                if (
                    isinstance(artifact.get("plan_binding"), dict)
                    and artifact["plan_binding"] != active_plan_binding
                ):
                    errors.append(
                        f"event {index}: implementation plan binding does not match current approval"
                    )
            if blocked and checkpoint_id == blocked["route"]:
                addressed = set(event.get("failure_codes_addressed", []))
                if blocked["code"] not in addressed:
                    errors.append(
                        f"event {index}: repair does not cite failure code {blocked['code']}"
                    )
                repair_route_started = True

        elif event_type == "checkpoint_verdict":
            if checkpoint_id not in machine_checkpoint_set:
                errors.append(f"event {index}: verdict checkpoint is unknown or human-owned")
                continue
            status = event.get("status")
            if status not in {"PASS", "FAIL", "INCONCLUSIVE"}:
                errors.append(f"event {index}: invalid checkpoint verdict")
                continue
            submissions = submission_indices.get(checkpoint_id, [])
            latest_submission = submissions[-1] if submissions else None
            if latest_submission is None or latest_submission <= last_verdict_submission.get(
                checkpoint_id, -1
            ):
                errors.append(
                    f"event {index}: {checkpoint_id} verdict has no new checkpoint submission"
                )
            else:
                last_verdict_submission[checkpoint_id] = latest_submission
            first_verdict.setdefault(checkpoint_id, status)
            if checkpoint_id == "approach-selection" and event.get("independent") is True:
                independent_approach_review = status == "PASS"
            if checkpoint_id == "solution-review" and event.get("independent") is True:
                solution_review_pass = status == "PASS"
            if status == "FAIL":
                failure_count += 1
                codes = event.get("failure_codes")
                if not isinstance(codes, list) or not codes:
                    errors.append(f"event {index}: failed verdict needs failure_codes")
                    codes = []
                    code = "missing-failure-code"
                else:
                    code = str(codes[0])
                route = failure_spec["expected_repair_route"] if (
                    checkpoint_id == failure_spec["checkpoint_id"]
                    and failure_spec["failure_code"] in codes
                ) else checkpoint_id
                if (
                    checkpoint_id == failure_spec["checkpoint_id"]
                    and failure_spec["failure_code"] in codes
                ):
                    expected_failure_seen = True
                blocked = {"checkpoint": checkpoint_id, "code": code, "route": route}
                repair_route_started = False
                expected_order = checkpoint_order[route]
            elif blocked and checkpoint_id == blocked["route"] and status == "PASS":
                if repair_route_started:
                    recovered_count += 1
                    blocked = None
                    repair_route_started = False
                    expected_order = checkpoint_order[checkpoint_id] + 1
                else:
                    errors.append(f"event {index}: passing verdict has no repair submission")
            elif status == "INCONCLUSIVE":
                errors.append(f"event {index}: required checkpoint is inconclusive")
            elif status == "PASS":
                expected_order = checkpoint_order[checkpoint_id] + 1
            if status == "PASS":
                pass_indices[checkpoint_id] = index
                if checkpoint_id == "approach-selection":
                    binding = latest_artifacts.get(checkpoint_id, {}).get("plan_binding")
                    if isinstance(binding, dict):
                        latest_passing_approach_binding = dict(binding)

        elif event_type == "human_decision":
            if checkpoint_id not in human_ids:
                errors.append(f"event {index}: human checkpoint is unknown")
                continue
            decision = event.get("decision")
            allowed = next(
                item["allowed_decisions"]
                for item in contract["human_checkpoints"]
                if item["id"] == checkpoint_id
            )
            if decision not in allowed:
                errors.append(f"event {index}: human decision {decision!r} is invalid")
            human_decisions.setdefault(checkpoint_id, []).append(str(decision))
            if checkpoint_id == "plan-approval":
                if expected_order != checkpoint_order["plan-approval"]:
                    errors.append(
                        f"event {index}: plan decision occurred at order {expected_order}, "
                        f"expected {checkpoint_order['plan-approval']}"
                    )
                plan_decisions.append((index, str(decision)))
                if not event.get("raw_response"):
                    errors.append(f"event {index}: plan decision must preserve raw_response")
                if not event.get("decision_ref"):
                    errors.append(f"event {index}: plan decision needs decision_ref")
                if decision == "approve":
                    binding_errors = _binding_errors(
                        event.get("plan_binding"),
                        binding_fields,
                        label=f"event {index}: approval",
                    )
                    errors.extend(binding_errors)
                    if (
                        not binding_errors
                        and event.get("plan_binding") != latest_passing_approach_binding
                    ):
                        errors.append(
                            f"event {index}: approval plan binding does not match the latest passing approach"
                        )
                    if not binding_errors:
                        active_plan_binding = dict(event["plan_binding"])
                        plan_approval_index = index
                        expected_order = checkpoint_order["plan-approval"] + 1
                else:
                    active_plan_binding = None
                    plan_approval_index = None
                if decision == "revise":
                    codes = event.get("failure_codes", [])
                    if (
                        failure_spec["checkpoint_id"] == "plan-approval"
                        and failure_spec["failure_code"] in codes
                    ):
                        expected_failure_seen = True
                        failure_count += 1
                        route = failure_spec["expected_repair_route"]
                        blocked = {
                            "checkpoint": "plan-approval",
                            "code": failure_spec["failure_code"],
                            "route": route,
                        }
                        repair_route_started = False
                        expected_order = checkpoint_order[route]
                if decision == "ambiguous":
                    ambiguity_clarifications += 1
                    maximum = next(
                        item.get("maximum_ambiguity_clarifications", 1)
                        for item in contract["human_checkpoints"]
                        if item["id"] == "plan-approval"
                    )
                    if ambiguity_clarifications > maximum:
                        errors.append(
                            f"event {index}: plan decision exceeded {maximum} ambiguity clarification"
                        )

        elif event_type == "action":
            action_type = event.get("action_type")
            if action_type in approval_blocked_actions:
                prior = [decision for decision_index, decision in plan_decisions if decision_index < index]
                if not prior or prior[-1] != "approve" or not active_plan_binding:
                    errors.append(
                        f"event {index}: {action_type} occurred without current plan approval"
                    )
                errors.extend(
                    _binding_errors(
                        event.get("plan_binding"),
                        binding_fields,
                        label=f"event {index}: {action_type}",
                    )
                )
                if (
                    isinstance(event.get("plan_binding"), dict)
                    and event["plan_binding"] != active_plan_binding
                ):
                    errors.append(
                        f"event {index}: {action_type} plan binding does not match current approval"
                    )
            if action_type in {"push", "pr-create"}:
                errors.append(f"event {index}: external action is forbidden in calibration")

        elif event_type == "oracle_result":
            oracle_id = event.get("oracle_id")
            status = event.get("status")
            if oracle_id in required_oracles:
                oracle_results[str(oracle_id)] = (index, str(status))
                if event.get("after_repair") and status != "PASS":
                    repair_regression_count += 1
                if status != "PASS":
                    code = str(event.get("failure_code") or f"oracle-{oracle_id}-failed")
                    route = str(event.get("repair_route") or "verification")
                    allowed_routes = contract["repair_policy"]["allowed_routes"][
                        "verification"
                    ]
                    if route not in allowed_routes:
                        errors.append(
                            f"event {index}: oracle repair route {route!r} is not allowed"
                        )
                        route = "verification"
                    failure_count += 1
                    blocked = {
                        "checkpoint": "verification",
                        "code": code,
                        "route": route,
                    }
                    repair_route_started = False
                    expected_order = checkpoint_order[route]

        elif event_type == "final_output":
            final_events.append((index, event))

    if blocked:
        errors.append(f"unrepaired checkpoint failure: {blocked['checkpoint']}")
    if not expected_failure_seen:
        errors.append(
            "trace did not exercise the scenario's required failure injection"
        )

    minimum_approaches = contract["approach_policy"][
        "minimum_materially_distinct_approaches"
    ]
    approach_requirement_pass = approach_count >= minimum_approaches
    if not approach_requirement_pass:
        errors.append(
            f"approach selection produced {approach_count}; requires {minimum_approaches}"
        )
    if (
        scenario["complexity"] in contract["approach_policy"]["independent_review_required_for"]
        and not independent_approach_review
    ):
        errors.append("high-complexity approach selection lacks an independent passing review")

    for checkpoint_id in scenario["expected_human_checkpoints"]:
        if checkpoint_id not in human_decisions:
            errors.append(f"missing human checkpoint decision: {checkpoint_id}")
    revisions = human_decisions.get("plan-approval", []).count("revise")
    approvals_after_revision = bool(
        revisions and human_decisions.get("plan-approval", [])[-1] == "approve"
    )

    missing_oracles = sorted(required_oracles - set(oracle_results))
    failed_oracles = sorted(
        oracle_id
        for oracle_id, (_, status) in oracle_results.items()
        if status != "PASS"
    )
    if missing_oracles:
        errors.append(f"missing code-quality oracle results: {missing_oracles}")
    if failed_oracles:
        errors.append(f"non-passing code-quality oracle results: {failed_oracles}")
    verification_index = pass_indices.get("verification")
    solution_review_index = pass_indices.get("solution-review")
    stale_oracles = sorted(
        oracle_id
        for oracle_id, (index, _) in oracle_results.items()
        if verification_index is None
        or index <= verification_index
        or solution_review_index is None
        or index >= solution_review_index
    )
    if stale_oracles:
        errors.append(
            f"code-quality oracle results are outside the latest verification-review window: {stale_oracles}"
        )
    if not solution_review_pass:
        errors.append("solution review requires an independent passing verdict")

    final_claim_integrity = False
    missing_checkpoint_submissions = sorted(
        checkpoint_id
        for checkpoint_id in machine_checkpoint_ids
        if checkpoint_id not in submission_indices
    )
    missing_checkpoint_passes = sorted(
        checkpoint_id
        for checkpoint_id in machine_checkpoint_ids
        if checkpoint_id not in pass_indices
    )
    if missing_checkpoint_submissions:
        errors.append(
            f"missing required checkpoint submissions: {missing_checkpoint_submissions}"
        )
    if missing_checkpoint_passes:
        errors.append(f"missing passing checkpoint verdicts: {missing_checkpoint_passes}")

    ordered_checkpoint_indices: list[tuple[str, int]] = []
    for checkpoint in checkpoints:
        checkpoint_id = checkpoint["id"]
        if checkpoint.get("owner") == "human":
            if plan_approval_index is not None:
                ordered_checkpoint_indices.append((checkpoint_id, plan_approval_index))
        elif checkpoint_id in pass_indices:
            ordered_checkpoint_indices.append((checkpoint_id, pass_indices[checkpoint_id]))
    for (previous_id, previous_index), (current_id, current_index) in zip(
        ordered_checkpoint_indices, ordered_checkpoint_indices[1:]
    ):
        if current_index <= previous_index:
            errors.append(
                f"checkpoint order invalid: {current_id} did not follow {previous_id}"
            )

    final_event = final_events[-1] if final_events else None
    if not final_event:
        errors.append("trace has no final_output event")
    else:
        final_index, event = final_event
        if len(final_events) != 1:
            errors.append("trace must contain exactly one final_output event")
        if final_index != len(events) - 1:
            errors.append("final_output must be the last trace event")
        solution_review_index = pass_indices.get("solution-review")
        final_handoff_index = pass_indices.get("final-handoff")
        if solution_review_index is None or solution_review_index >= final_index:
            errors.append("final output requires a prior passing solution review")
        if final_handoff_index is None or final_handoff_index >= final_index:
            errors.append("final output requires a prior passing final-handoff review")
        if final_handoff_index is not None and final_handoff_index != final_index - 1:
            errors.append("final-handoff review must immediately precede final_output")
        artifact = event.get("artifact")
        if not isinstance(artifact, dict):
            errors.append("final_output needs an artifact")
            artifact = {}
        missing = sorted(_checkpoint_fields(contract, "final-handoff") - set(artifact))
        if missing:
            errors.append(f"final handoff missing fields {missing}")
        late_oracles = [
            oracle_id
            for oracle_id, (index, _) in oracle_results.items()
            if index > final_index
        ]
        if late_oracles:
            errors.append(f"final output preceded code-quality oracles: {late_oracles}")
        claims = " ".join(str(value) for value in artifact.values()).lower()
        unsupported = any(
            phrase in claims
            for phrase in ("fully validated", "ready to merge", "all checks passed")
        ) and bool(artifact.get("unknowns"))
        if unsupported:
            errors.append("final output makes an unsupported completion claim")
        final_claim_integrity = (
            not missing
            and not late_oracles
            and not unsupported
            and final_index == len(events) - 1
            and solution_review_index is not None
            and final_handoff_index is not None
        )

    total_first_verdicts = len(first_verdict)
    first_passes = sum(status == "PASS" for status in first_verdict.values())
    metrics = {
        "first_pass_checkpoint_rate": round(
            first_passes / total_first_verdicts, 4
        ) if total_first_verdicts else 0.0,
        "repair_success_rate": round(recovered_count / failure_count, 4)
        if failure_count else 0.0,
        "error_propagation_rate": round(propagation_count / failure_count, 4)
        if failure_count else 0.0,
        "repair_regression_count": repair_regression_count,
        "human_revision_recovery_rate": 1.0
        if revisions and approvals_after_revision
        else (0.0 if revisions else None),
        "approach_requirement_pass_rate": 1.0 if approach_requirement_pass else 0.0,
        "high_complexity_approach_target_met": (
            approach_count
            >= contract["approach_policy"]["high_complexity_target_approaches"]
            if scenario["complexity"] in {"high", "critical"}
            else None
        ),
        "solution_review_pass_rate": 1.0 if solution_review_pass else 0.0,
        "final_claim_integrity_rate": 1.0 if final_claim_integrity else 0.0,
        "attempt_count": sum(submission_attempts.values()),
    }
    return {
        "scenario_id": scenario["id"],
        "variant_id": trace.get("variant_id"),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "metrics": metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--trace", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = load_json(args.contract)
    package = load_json(args.scenarios)
    package_result = validate_package(contract, package)
    scenario_map = {item["id"]: item for item in package.get("scenarios", [])}
    trace_results = []
    for path in args.trace:
        trace = load_json(path)
        scenario_id = trace.get("scenario_id")
        if scenario_id not in scenario_map:
            trace_results.append(
                {
                    "scenario_id": scenario_id,
                    "status": "INCONCLUSIVE",
                    "errors": ["trace scenario is absent from the package"],
                    "metrics": {},
                }
            )
            continue
        trace_results.append(evaluate_trace(contract, scenario_map[scenario_id], trace))

    status = "FAIL" if package_result["errors"] else "READY_FOR_GOLD_REVIEW"
    if trace_results and any(item["status"] != "PASS" for item in trace_results):
        status = "FAIL"
    elif trace_results and not package_result["warnings"]:
        status = "PASS"
    report = {
        "schema_version": 1,
        "status": status,
        "package": package_result,
        "traces": trace_results,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if status in {"PASS", "READY_FOR_GOLD_REVIEW"} else 2


if __name__ == "__main__":
    sys.exit(main())
