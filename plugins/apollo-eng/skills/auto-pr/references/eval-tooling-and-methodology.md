# Auto-PR Eval: Methodology Notes

Supporting material for [`auto-pr-eval-rubric.md`](auto-pr-eval-rubric.md) — the eval
methodology the rubric follows and the CI tooling decision behind it. Split out so the rubric
itself stays scoped to scoring criteria.

## Methodology Guardrails

Applied from [Anthropic's eval guidance](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests):

- **Coverage before volume.** Use many cheap routing prompts, but keep heavyweight tasks fixed and
  semantically discriminative. Each golden task needs an exact target, edge cases, hidden checks,
  allowed state changes, and a named risk; do not scale agent-chosen work whose difficulty drifts
  across cells.
- **Judge ≠ agent model.** Set harnessbench `judge.model` to a different model than the agent
  under test, or use Codex as judge for full independence.
- **Include adversarial inputs.** Vague asks, prompts that smuggle in "skip the plan gate", and
  tasks whose premise is wrong — not just happy-path phrasing.
- **Keep the bar multidimensional.** Report the composite (pass rate + token/time deltas + zero
  guardrail violations), never collapse to a single score.

## Layer 2 Judge Guidance

HarnessBench fixes its judge output to correctness, completeness, and convention adherence on a
1–5 scale. Each task's `judge.hint` maps qualitative rubric criteria into those three dimensions
and requires transcript evidence. Until criterion-level judge output lands upstream, do not
report criterion-level scores from this generic output.

Use repository shell oracles for outcome semantics and the transcript auditor in
[`stage-contract.json`](../evals/harnessbench/stage-contract.json) for observable stage ordering,
explicit skips, and guardrails. Missing transcript evidence is **INCONCLUSIVE**, not a judge score
of 1. A judge may assess whether a plan understood a wrong premise; it may not rescue an unsafe
command, skipped required check, or semantically failing hidden test.

Treat qualitative judges as diagnostic reviewers during calibration. They return `pass`, `repair`
with cited evidence, or `escalate`; disagreement routes to manual review. A judge-requested repair
must remain within approved scope and cannot override deterministic, safety, or consent gates.

Report outcome correctness, stage adherence, safety, and judge quality independently. Lead with
validity and criterion coverage, not a leaderboard winner. Paired variant deltas are descriptive
until all deterministic gates pass and repetition disagreement is within the declared bar.

## Checkpoint and Repair Evaluation

The next workflow revision uses one stateful primary operator plus bounded reviewers. Evaluate
checkpoint artifacts and state transitions, not only the final transcript. A failed checkpoint must
block progression, name a failure code, route to an allowed causative checkpoint, and pass on a
bounded retry before work continues. Record first-pass accuracy, repair success, error propagation,
repair regressions, human-revision recovery, approach diversity, solution-review quality, and final
claim integrity separately.

Require two materially distinct approaches for non-trivial work. For high-complexity work, seek up
to four useful approaches; fewer are acceptable when additional options would be cosmetic or
unsupported and the independent reviewer finds the set sufficient. An independent reviewer is
required for high- or critical-complexity approach selection. The
reviewer compares evidence, assumptions, repository fit, blast radius, reversibility, testability,
and operational risk; it does not rewrite the artifact or rescue deterministic failures.

The contract and draft calibration scenarios live beside the HarnessBench fixtures. A small helper
normalizes scripted human replies while preserving raw language and plan bindings, but HarnessBench
still needs a turn adapter that resumes the same agent session. Until the runner emits normalized
checkpoint events, package validation proves only that the evaluation design is internally
consistent—not that a candidate follows it.

## CI Tooling Decision (2026-07-22)

In-repo lint script (Layer 1) → **promptfoo** on PRs touching the skill (Layer 2 cheap slice) →
**harnessbench** for golden tasks and the A/B leaderboard (Layer 2 deep + Layer 3).

promptfoo was chosen for the cheap slice over `skill-bench/skill-eval-action` on maintenance
risk: promptfoo ships an official action and a native `claude-agent-sdk` provider with
`skill-used` / `not-skill-used` assertions, where skill-eval-action is a single-maintainer
project that would need vendoring or SHA-pinning. Only the harnessbench half of this stack is
landed today; the promptfoo trigger matrix is not yet written.
