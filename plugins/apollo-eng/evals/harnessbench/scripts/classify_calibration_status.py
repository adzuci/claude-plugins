#!/usr/bin/env python3
"""Classify calibration validity before rendering any paired winner.

Experimental: this scoring logic arguably belongs in the harnessbench repo itself
rather than here. Kept in claude-plugins for now to see how effective it is in
practice; easy to remove or move later if it doesn't earn its keep.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def classify_calibration_status(
    *,
    infrastructure_errors: int,
    inconclusive_checks: int,
    empty_diffs: int,
    invalid_judges: int,
    flaky_variants: int,
    stage_validity: str,
    oracle_failures: int,
    required_stage_failures: int,
    safety_failures: int,
    stage_gate_failures: int,
) -> dict[str, Any]:
    invalid_reasons = {
        "infrastructure_errors": infrastructure_errors,
        "inconclusive_checks": inconclusive_checks,
        "empty_diffs": empty_diffs,
        "invalid_judges": invalid_judges,
        "flaky_variants": flaky_variants,
    }
    invalid = any(invalid_reasons.values()) or stage_validity not in {
        "PASS",
        "NOT_APPLICABLE",
    }
    candidate_failures = {
        "oracle_failures": oracle_failures,
        "required_stage_failures": required_stage_failures,
        "safety_failures": safety_failures,
        "stage_gate_failures": stage_gate_failures,
    }

    if invalid:
        status = "INCONCLUSIVE"
    elif any(candidate_failures.values()):
        status = "VALID / CANDIDATE FAIL"
    else:
        status = "VALID / CANDIDATE PASS"
    return {
        "status": status,
        "winners_allowed": status == "VALID / CANDIDATE PASS",
        "invalid_reasons": invalid_reasons,
        "candidate_failures": candidate_failures,
        "stage_validity": stage_validity,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for name in (
        "infrastructure_errors",
        "inconclusive_checks",
        "empty_diffs",
        "invalid_judges",
        "flaky_variants",
        "oracle_failures",
        "required_stage_failures",
        "safety_failures",
        "stage_gate_failures",
    ):
        parser.add_argument(f"--{name.replace('_', '-')}", type=int, required=True)
    parser.add_argument("--stage-validity", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(classify_calibration_status(**vars(args)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
