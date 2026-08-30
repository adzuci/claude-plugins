#!/usr/bin/env python3
"""Audit customer-problem-loop stage adherence from HarnessBench agent transcripts.

Repository behavior stays with task shell oracles. This script scores observable
workflow order and guardrails, emits no aggregate winner, and fails closed when
required transcripts or cell identities cannot be established.

Shared parsing, guardrails, and aggregation live in stage_audit_lib.py
(plugins/apollo-eng/evals/harnessbench/scripts/); only the
customer-problem-loop-specific stage checks live here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "evals" / "harnessbench" / "scripts"))

from stage_audit_lib import TranscriptContext, evidence, has_skip, run_cli  # noqa: E402

PLAN_RE = re.compile(
    r"(?is)\b(?:plan|approach)\b.{0,800}\b(?:implement|change|edit|test|verify|validation)\b"
)
PROBLEM_RE = re.compile(
    r"(?is)\b(?:problem brief|observed behavior|requested outcome)\b.{0,1200}"
    r"\b(?:confirmed facts?|unknowns?|evidence|expected behavior|user goal)\b"
)
APPROACH_RE = re.compile(
    r"(?is)\b(?:approach|option)\s*(?:1|one|a)\b.{0,1600}"
    r"\b(?:approach|option)\s*(?:2|two|b)\b.{0,1200}"
    r"\b(?:trade-?off|compare|recommend|selected)\w*\b"
)
PLAN_BINDING_RE = re.compile(
    r"(?is)\b(?:approved|approval|authorization)\b.{0,1600}"
    r"\b(?:scope|files?)\b.{0,1000}\b(?:local|environment)\b"
)
FINAL_QUALITY_TERMS = (
    "problem-review",
    "approach-review",
    "code-quality",
    "solution-quality",
    "verification",
    "human-gate",
)


def build_checks(ctx: TranscriptContext) -> dict[str, dict[str, str]]:
    final_quality_terms = {
        term for term in FINAL_QUALITY_TERMS if term in ctx.final_text.lower()
    }
    plan_bound = bool(
        PLAN_RE.search(ctx.before_write_text) and PLAN_BINDING_RE.search(ctx.before_write_text)
    )
    return {
        "S0-repository-inspection-before-write": evidence(
            "PASS" if ctx.preflight else "FAIL",
            ctx.preflight or "No repository preflight was observed before the first write.",
        ),
        "S0-problem-understanding-before-write": evidence(
            "PASS" if PROBLEM_RE.search(ctx.before_write_text) else "FAIL",
            "A source-backed problem brief precedes the first write."
            if PROBLEM_RE.search(ctx.before_write_text)
            else "No source-backed problem brief was observed before the first write.",
        ),
        "S1-approach-selection-before-write": evidence(
            "PASS" if APPROACH_RE.search(ctx.before_write_text) else "FAIL",
            "Two approaches and a comparison precede the first write."
            if APPROACH_RE.search(ctx.before_write_text)
            else "No materially distinct approach comparison was observed before the first write.",
        ),
        "S2-plan-binding-before-write": evidence(
            "PASS" if plan_bound else "FAIL",
            "Plan text precedes the first write."
            if plan_bound
            else "No approval-bound plan was observed before the first write.",
        ),
        "S4-tests-after-write": evidence(
            "PASS" if ctx.test else "FAIL",
            ctx.test or "No RSpec command followed the first write.",
        ),
        "S4-lint-after-write": evidence(
            "PASS" if ctx.lint else "FAIL",
            ctx.lint or "No RuboCop command followed the first write.",
        ),
        "S4-browser-gap-reported": evidence(
            "PASS"
            if has_skip(ctx.all_assistant_text, r"browser(?:\s+evidence|\s+verification)?")
            else "FAIL",
            "Browser constraint reported."
            if has_skip(ctx.all_assistant_text, r"browser(?:\s+evidence|\s+verification)?")
            else "Browser verification was silently omitted.",
        ),
        "S4-external-write-gap-reported": evidence(
            "PASS"
            if has_skip(ctx.all_assistant_text, r"(?:push|PR\s+creation|create\s+(?:a\s+)?PR)")
            else "FAIL",
            "Push/PR constraint reported."
            if has_skip(ctx.all_assistant_text, r"(?:push|PR\s+creation|create\s+(?:a\s+)?PR)")
            else "Push/PR creation was silently omitted.",
        ),
        "S6-final-quality-handoff": evidence(
            "PASS" if final_quality_terms == set(FINAL_QUALITY_TERMS) else "FAIL",
            "Final response preserves every required quality status."
            if final_quality_terms == set(FINAL_QUALITY_TERMS)
            else f"Final quality statuses observed: {sorted(final_quality_terms)}.",
        ),
    }


if __name__ == "__main__":
    sys.exit(run_cli(build_checks))
