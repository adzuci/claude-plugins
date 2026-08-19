# Auto-PR Eval: Methodology Notes

Supporting material for [`auto-pr-eval-rubric.md`](auto-pr-eval-rubric.md) — the eval
methodology the rubric follows and the CI tooling decision behind it. Split out so the rubric
itself stays scoped to scoring criteria.

## Methodology Guardrails

Applied from [Anthropic's eval guidance](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests):

- **Volume over per-case quality.** Many cheap automated cases beat few hand-graded ones. Grow
  the trigger/guardrail matrix (target 20+ prompts, not the current 8) before adding more
  heavyweight harnessbench golden tasks.
- **Judge ≠ agent model.** Set harnessbench `judge.model` to a different model than the agent
  under test, or use Codex as judge for full independence.
- **Include adversarial inputs.** Vague asks, prompts that smuggle in "skip the plan gate", and
  tasks whose premise is wrong — not just happy-path phrasing.
- **Keep the bar multidimensional.** Report the composite (pass rate + token/time deltas + zero
  guardrail violations), never collapse to a single score.

## Layer 2 Judge Guidance

HarnessBench fixes its judge output to correctness, completeness, and convention adherence on a
1–5 scale. Each task's `judge.hint` maps rubric criteria into those three dimensions and requires
transcript evidence. Until criterion-level judge output lands upstream, do not report
criterion-level scores from this generic output.

Use regex or script assertions, not the LLM judge, for the deterministic items: G1, G3, P4, and
the T1 count.

## CI Tooling Decision (2026-07-22)

In-repo lint script (Layer 1) → **promptfoo** on PRs touching the skill (Layer 2 cheap slice) →
**harnessbench** for golden tasks and the A/B leaderboard (Layer 2 deep + Layer 3).

promptfoo was chosen for the cheap slice over `skill-bench/skill-eval-action` on maintenance
risk: promptfoo ships an official action and a native `claude-agent-sdk` provider with
`skill-used` / `not-skill-used` assertions, where skill-eval-action is a single-maintainer
project that would need vendoring or SHA-pinning. Only the harnessbench half of this stack is
landed today; the promptfoo trigger matrix is not yet written.
