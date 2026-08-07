# Auto-PR Eval: Tooling & Methodology Notes

Supporting material for [`auto-pr-eval-rubric.md`](auto-pr-eval-rubric.md) — the
general eval methodology this rubric follows, the standard formats it adopts, and the CI tooling
decision (with alternatives considered). Split out so the rubric itself stays scoped to scoring
criteria.

## Methodology Guardrails (from platform.claude.com/docs/en/test-and-evaluate/develop-tests)

- **Volume over quality**: "More questions with slightly lower signal automated grading is better than fewer questions with high-quality human hand-graded evals." → grow the cheap promptfoo matrix (dozens of trigger/guardrail prompts) before adding more heavyweight harnessbench golden tasks. Target 20+ trigger-matrix prompts, not 8.
- **Judge ≠ agent model**: "best practice to use a different model to evaluate than the model used to generate the evaluated output." → set harnessbench `judge.model` and promptfoo `llm-rubric` provider to a different model than the agent under test (or use Codex as judge for full independence).
- **Task distribution + edge cases**: include poor/ambiguous/adversarial user inputs in the trigger matrix (vague asks, requests that smuggle in "skip the plan gate", tasks whose premise is wrong).
- **Multidimensional bar, SMART-quantified**: keep the composite (pass_rate + token/time deltas + zero guardrail violations), not a single score.

## HarnessBench Compatibility Notes

HarnessBench previously hardcoded `temperature:0` for every judge call, which newer models
(opus-4-7/4-8/5, sonnet-5, fable-5, mythos-5) reject. Apolloio/harnessbench#7 fixed this
model-conditionally; those models are usable as judges when the pinned HarnessBench SHA includes
that fix. Keep this runner-specific compatibility detail out of the general methodology above.

## Standard Formats (Adopt, Don't Invent)

Future direction only: a promptfoo integration may adopt the
[agentskills.io / skill-creator conventions](https://agentskills.io/skill-creation/evaluating-skills):
`evals/evals.json`, per-run `grading.json`, and comparison `benchmark.json`. Those files do not
exist here today; the current HarnessBench experiment uses YAML and its own leaderboard output.

## Layer 2 Judge Guidance

Current HarnessBench fixes its judge output to correctness, completeness, and convention
adherence on a 1–5 scale. Each task's `judge.hint` tells the judge which rubric criteria to map
into those dimensions and requires transcript evidence. A future criterion-level judge should
emit rubric IDs with 0–2 scores and quoted evidence; until then, do not claim criterion-level
scores from the generic output.

Use regex or script assertions, not the LLM judge, for deterministic items G1, G3, P4, and the
T1 count.

## CI: OSS Tools, GHA-Triggered (Decided 2026-07-22)

Stack: in-repo lint script (Layer 1) → **promptfoo** via GHA on PRs touching `.claude/skills/auto-pr/**` (Layer 2 cheap slice) → **harnessbench** for golden tasks + A/B leaderboard (deep; its roadmap has a Docker image + GHA JSON-dispatch entrypoint for later CI wiring). promptfoo chosen over skill-eval-action for durability (8k★ vs 8★, official `promptfoo/promptfoo-action`, native `claude-agent-sdk` provider with `skill-used`/`not-skill-used` assertions and toolCall inspection). The harnessbench example lives in `harnessbench/` next to this doc; a promptfoo starter config for the trigger matrix is drafted but not yet landed.

## Alternative Borrowable GitHub Action

**`skill-bench/skill-eval-action`** (MIT, v1.3.0 Jun 2026, small but active): runs YAML eval cases from `<skill>/evals/`, each with `prompt`, `criteria`, `expect_skill` (routing assertion), `allowed_tools`, `timeout`; LLM-graded with evidence; upserts a PR comment with pass/fail table + tokens/cost; `pass-threshold` default 80%. Needs `ANTHROPIC_API_KEY` secret.

- Fit: ideal for Layer 2's cheap slice in leadgenie CI — trigger matrix (R1 via `expect_skill: true/false`) and touchpoint/guardrail criteria phrased as assertion strings. Not suited to the heavyweight golden tasks (docker/browser/PR side effects) — those stay in harnessbench.
- Small project (8 stars): consider vendoring the action or pinning a commit SHA rather than tracking `v1`.
- Alternatives: `anthropics/claude-code-action` (GA; generic `claude -p` runner — could drive skill-creator eval mode directly), `pulser-eval` action (structural lint ≈ Layer 1, ~15s), TribeAI/claude-evals `ci.yml` (pattern reference only).
