# Synthesizer Eval Corpus

Replay-eval cases for the `pr-tech-lead-synthesizer` agent. Implements the corpus required by `references/synthesizer-contract.md` § Eval corpus.

## Goal

Verify the synthesizer:

1. Applies the decision rubric correctly
1. Escalates on hard disagreement (precision ≥0.95 on disagreement detection)
1. Annotates dissent even on APPROVE
1. Drops fabricated / malformed findings citing missing evidence
1. Cites prior_decisions when reversing them

## Corpus structure

```
eval/synthesizer/
├── README.md            (this file)
├── cases.json           (canonical case list with metadata)
├── last-run.json        (most recent manually recorded eval results)
└── cases/
    ├── synth-c01-all-approve.json
    ├── synth-c02-all-request-changes.json
    ├── ...
    └── synth-c30-fabricated-finding.json
```

Each case file is a self-contained `synthesizer_input` envelope plus `expected` block:

```json
{
  "case_id": "synth-c01-all-approve",
  "category": "agreement",
  "synthesizer_input": { ... },
  "expected": {
    "verdict": "APPROVE",
    "confidence_min": 0.85,
    "findings_kept_count": 0,
    "escalated": false,
    "must_cite_prior_decision": false,
    "must_drop_finding_with_reason": null
  }
}
```

## Case categories (≥30 cases per contract)

| Category | Count | Description |
|---|---|---|
| `agreement` | 10 | All sub-agents agree on verdict; assert verdict matches; assert no escalation |
| `minor_disagreement` | 10 | Mixed non-blocker verdicts; assert REQUEST_CHANGES with consolidated findings; assert `synthesizer_low_confidence: true` flag where appropriate |
| `hard_disagreement` | 5 | Contradicting hard verdicts (BLOCK vs APPROVE); assert ESCALATE_HUMAN |
| `adversarial_fabrication` | 5 | One sub-agent emits a finding with no/weak evidence; assert synthesizer drops it citing missing evidence |
| `prior_decision_citation` | (subset) | Cases where `feature_memory.prior_decisions` is non-empty; assert citation when reversing |

Total ≥30 cases. Each case is independent — order-of-execution doesn't matter.

## Replay-Eval Thresholds (Per `synthesizer-contract.md`)

| Metric | Threshold |
|---|---|
| Verdict precision (verdict matches `expected.verdict`) | ≥0.85 |
| Disagreement-escalation precision (cases where ESCALATE_HUMAN was correct) | ≥0.95 |
| Fabrication detection (cases where fabricated finding was dropped) | ≥0.90 |
| Confidence calibration (confidence within ±0.15 of `expected.confidence_min`) | ≥0.80 |

## Running the eval

```bash
claude /eval pr-tech-lead-synthesizer
```

Run replay-eval manually when a PR touches:

- `agents/pr-tech-lead-synthesizer.md`
- `skills/code-review/SKILL.md`
- Any of the 4 reviewer sub-agents (`frontend-reviewer`, `backend-reviewer`, `security-reviewer`, `db-perf`)
- `.ai/claude-skills-framework/references/synthesizer-contract.md`

These thresholds report readiness but do not gate merges. The eval remains manual until CI integration exists.

## Phase F MVP exit

- [ ] All 30+ cases authored and committed
- [ ] First eval run lands `last-run.json` with all cases passing
- [ ] CI integration wired (per `.github/workflows/synthesizer-eval.yml`)
- [ ] After 90 days of human-resolved escalations, `analytics.synthesizer_decisions.human_resolution_verdict` populated → real-world precision computed and surfaced in framework SLO dashboard

## Authoring new cases

1. Pick a real PR (or construct a synthetic one) that exercises the rubric edge you want to test
1. Run the 4 sub-agents on the diff manually (or via fixture) → capture their envelopes
1. Build `cases/synth-cNN-<short-name>.json` with the captured envelopes as `synthesizer_input`
1. Set `expected` based on the rubric + your domain judgment
1. Run replay-eval locally: `claude /eval pr-tech-lead-synthesizer --case synth-cNN-<short-name>`
1. If it fails: either the case is wrong (fix `expected`) or the synthesizer is wrong (fix the agent prompt or the rubric in the contract)
1. Open the PR and include the manual eval result; no CI merge gate exists yet
