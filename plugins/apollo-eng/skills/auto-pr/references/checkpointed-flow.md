# Checkpointed Auto-PR Flow

This is the target workflow contract for the next `/auto-pr` revision. It keeps one stateful
primary coding agent, adds bounded independent reviews around high-leverage artifacts, and blocks
progress whenever a required checkpoint fails.

## Execution Model

```text
Problem recognition
  → problem-understanding gate ── fail → repair understanding
  → approach generation
  → approach-selection gate ───── fail → regenerate or reassess
  → human plan approval ───────── revise → replan and reapprove
  → implementation
  → code-quality oracles ───────── fail → repair implementation or selected approach
  → independent solution review ─ fail → repair the responsible checkpoint
  → final handoff
```

The primary operator retains the conversation, repository, decisions, and repair history. Reviewers
receive bounded artifacts and evidence references. They return verdicts and failure codes; they do
not silently rewrite artifacts or take over the task.

## Problem and Approach Gates

Problem understanding must separate observed behavior, expected behavior, confirmed facts,
unknowns, contradictions, evidence, and bug/feature/mixed classification before proposing a
solution.

Every non-trivial task compares at least two materially different approaches. High-complexity work
seeks up to four useful approaches when root cause is uncertain, multiple systems are involved,
rollback is difficult, permissions or security matter, scope options differ materially, or the
leading options score closely. Fewer are acceptable when more options would be cosmetic or
unsupported and an independent reviewer finds the set sufficient. High- and critical-complexity
selections require that review before the human sees the plan.

## Repair Semantics

- A failed checkpoint blocks all later work.
- A repair must name the failure code and remain in the same primary session.
- The repair may route to the failed checkpoint or an earlier causative checkpoint allowed by
  [`checkpoint-flow-contract.json`](../../../evals/harnessbench/checkpoint-flow-contract.json).
- Changing the selected approach invalidates prior human approval.
- Each checkpoint receives at most two attempts; exhaustion escalates to the human.
- Deterministic, safety, consent, and code-quality failures cannot be averaged away by a judge.

## Human Checkpoints

The flow preserves a small number of decision-quality interactions:

1. **Plan approval** — blocking; no write, commit, push, or PR creation before approval.
1. **Evidence availability** — records provided, unavailable, or intentionally skipped evidence.
1. **External review** — records whether independent review is run, skipped, or unavailable.

Human `revise` decisions invalidate the current approval and must produce a revised artifact plus a
new approval. An implementation-only repair that preserves the approved plan binding does not ask
again. Internal reviewers ask the human only when a material decision or true ambiguity remains.

## Evaluation Layers

Report these independently:

1. state-transition and repair conformance;
1. repository outcome and code-quality oracles;
1. solution-review quality;
1. final-claim integrity and human-handoff quality;
1. cost, latency, and attempt count.

The current HarnessBench experiment still runs one unattended Claude Code session per cell. It can
observe the old Stage 0–7 flow but cannot inject checkpoint verdicts or scripted human turns. The
new contract, scenario package, validator, and human-response normalizer are ready for an adapter
that resumes the same agent session between turns. Until that adapter exists, the checkpoint suite
is calibration scaffolding, not executed evidence for a skill revision.

The normalized adapter emits one trace with a stable `session_id` and ordered events of type
`checkpoint_submission`, `checkpoint_verdict`, `human_decision`, `action`, `oracle_result`, and
`final_output`. Validate structural readiness or one or more traces with:

```bash
python ../../evals/harnessbench/scripts/validate_checkpoint_flow.py \
  --contract ../../evals/harnessbench/checkpoint-flow-contract.json \
  --scenarios evals/harnessbench/stateful-scenarios.json \
  --trace /path/to/normalized-trace.json
```

The current calibration status and blocking source gaps are explicit in
[`checkpoint-calibration-manifest.json`](../evals/harnessbench/checkpoint-calibration-manifest.json).

## Scenario Sources

The initial scenarios were derived from recurring patterns in `#product-feedback`, Jira issues, and
the existing fixed LeadGenie fixtures: opaque incident references, unsafe premises, hidden
downstream constraints, empty-value edge cases, human scope reductions, incorrect reviewer advice,
and unsupported completion claims. Live source material is discovery evidence only; reusable
scenario text is synthetic and excludes customer, workspace, reporter, and account data.
