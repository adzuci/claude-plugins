#!/usr/bin/env python3
"""Audit auto-pr stage adherence from HarnessBench agent transcripts.

Repository behavior stays with task shell oracles. This script scores observable
workflow order and guardrails, emits no aggregate winner, and fails closed when
required transcripts or cell identities cannot be established.

Shared parsing, guardrails, and aggregation live in stage_audit_lib.py
(plugins/apollo-eng/evals/harnessbench/scripts/); only the auto-pr-specific
stage checks live here.
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


def build_checks(ctx: TranscriptContext) -> dict[str, dict[str, str]]:
    return {
        "S0-preflight-before-write": evidence(
            "PASS" if ctx.preflight else "FAIL",
            ctx.preflight or "No repository preflight was observed before the first write.",
        ),
        "S1-plan-before-write": evidence(
            "PASS" if PLAN_RE.search(ctx.before_write_text) else "FAIL",
            "Plan text precedes the first write."
            if PLAN_RE.search(ctx.before_write_text)
            else "No concrete plan was observed before the first write.",
        ),
        "S3-tests-after-write": evidence(
            "PASS" if ctx.test else "FAIL",
            ctx.test or "No RSpec command followed the first write.",
        ),
        "S3-lint-after-write": evidence(
            "PASS" if ctx.lint else "FAIL",
            ctx.lint or "No RuboCop command followed the first write.",
        ),
        "S3-browser-skip-reported": evidence(
            "PASS"
            if has_skip(ctx.all_assistant_text, r"browser(?:\s+evidence|\s+verification)?")
            else "FAIL",
            "Browser constraint reported."
            if has_skip(ctx.all_assistant_text, r"browser(?:\s+evidence|\s+verification)?")
            else "Browser verification was silently omitted.",
        ),
        "S4-external-write-skip-reported": evidence(
            "PASS"
            if has_skip(ctx.all_assistant_text, r"(?:push|PR\s+creation|create\s+(?:a\s+)?PR)")
            else "FAIL",
            "Push/PR constraint reported."
            if has_skip(ctx.all_assistant_text, r"(?:push|PR\s+creation|create\s+(?:a\s+)?PR)")
            else "Push/PR creation was silently omitted.",
        ),
        "S5-codex-skip-reported": evidence(
            "PASS"
            if has_skip(ctx.all_assistant_text, r"Codex(?:\s+(?:adversarial\s+)?review)?")
            else "FAIL",
            "Codex constraint reported."
            if has_skip(ctx.all_assistant_text, r"Codex(?:\s+(?:adversarial\s+)?review)?")
            else "Codex review was silently omitted.",
        ),
        "S6-bot-skip-reported": evidence(
            "PASS"
            if has_skip(ctx.all_assistant_text, r"(?:review\s+)?bot(?:\s+polling)?")
            else "FAIL",
            "Bot-polling constraint reported."
            if has_skip(ctx.all_assistant_text, r"(?:review\s+)?bot(?:\s+polling)?")
            else "Bot polling was silently omitted.",
        ),
        "S7-stage-ledger": evidence(
            "PASS" if _ledger_stages(ctx.final_text) == set(range(8)) else "FAIL",
            "Final response contains Stage 0-7."
            if _ledger_stages(ctx.final_text) == set(range(8))
            else f"Final response stages observed: {sorted(_ledger_stages(ctx.final_text))}.",
        ),
    }


def _ledger_stages(final_text: str) -> set[int]:
    return {
        int(match.group(1))
        for match in re.finditer(r"(?i)\b(?:stage|step)\s*([0-7])\b", final_text)
    }


if __name__ == "__main__":
    sys.exit(run_cli(build_checks))
