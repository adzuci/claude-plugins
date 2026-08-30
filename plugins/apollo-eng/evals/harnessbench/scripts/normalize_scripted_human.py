#!/usr/bin/env python3
"""Normalize a scripted human reply without pretending to understand ambiguity."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


STOP_RE = re.compile(r"(?i)\b(?:stop|cancel|do not proceed|don't proceed)\b")
REVISE_RE = re.compile(r"(?i)\b(?:revise|change|rework|not yet|needs? (?:a )?change)\b")
APPROVE_RE = re.compile(
    r"(?i)\b(?:approve|approved|go ahead|proceed|looks good|sounds good|option\s+[a-z0-9]+)\b"
)
CONSTRAINT_RE = re.compile(
    r"(?i)(?:^|[,;])\s*([^,;]*(?:\bonly\b|\blimit\b|\bkeep\b|\bwithout\b|\bdo not\b)[^,;]*)"
)


def normalize_response(
    raw_response: str,
    *,
    plan_binding: dict[str, Any] | None = None,
    decision_ref: str = "scripted-human:unbound",
) -> dict[str, Any]:
    raw = raw_response.strip()
    if STOP_RE.search(raw):
        decision = "stop"
    elif REVISE_RE.search(raw):
        decision = "revise"
    elif APPROVE_RE.search(raw):
        decision = "approve"
    else:
        decision = "ambiguous"

    constraints = [
        match.group(1).strip()
        for match in CONSTRAINT_RE.finditer(raw)
        if match.group(1).strip()
    ]
    event: dict[str, Any] = {
        "type": "human_decision",
        "checkpoint_id": "plan-approval",
        "decision": decision,
        "raw_response": raw_response,
        "decision_ref": decision_ref,
        "constraints": constraints,
        "needs_clarification": decision == "ambiguous",
    }
    if decision == "approve" and plan_binding is not None:
        event["plan_binding"] = plan_binding
    return event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("response")
    parser.add_argument("--plan-binding-json")
    parser.add_argument("--decision-ref", default="scripted-human:cli")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    binding = json.loads(args.plan_binding_json) if args.plan_binding_json else None
    print(
        json.dumps(
            normalize_response(
                args.response,
                plan_binding=binding,
                decision_ref=args.decision_ref,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
