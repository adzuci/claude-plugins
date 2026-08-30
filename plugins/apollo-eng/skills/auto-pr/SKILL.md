---
name: auto-pr
description: 'Mostly-unattended LeadGenie PR pipeline: preflight → plan approval → implement → verify → PR → reviews. Staging only; invoke /auto-pr in a LeadGenie checkout.'
disable-model-invocation: true
---

# Auto PR (Staging)

This is the staging home for the `/auto-pr` skill — a mostly-unattended LeadGenie pipeline
(preflight → plan approval → implement → before/after verification → PR → reviews → bot-comment
resolution). The runnable skill currently lives in `apolloio/leadgenie` at
`.claude/skills/auto-pr/` ([leadgenie#97782](https://github.com/apolloio/leadgenie/pull/97782),
refined by [leadgenie#97942](https://github.com/apolloio/leadgenie/pull/97942)). Whether the
runnable skill stays in leadgenie or moves here is still undecided; it will live in exactly one
of the two, never both, so routing stays unambiguous.

What ships from this directory today:

- `references/leadgenie-gotchas.md` — repo-wide LeadGenie gotchas (sensitive-file approval
  gates, pre-push hook escape hatch) for surfaces where leadgenie's `CLAUDE.md` is not in
  context (Cowork, Codex, other repos).
- `references/auto-pr-eval-rubric.md` — the three-layer evaluation rubric for this skill (static
  lint → scenario compliance → production signal).
- `references/eval-tooling-and-methodology.md` — the eval methodology guardrails, judge guidance,
  and CI tooling decision behind that rubric.
- `references/checkpointed-flow.md` — the target stateful problem-recognition → approach comparison
  → human approval → bounded repair → solution-review contract for the next revision.
- `evals/harnessbench/` — machine-executed [apolloio/harnessbench](https://github.com/apolloio/harnessbench)
  experiment that A/B tests skill versions against a no-skill baseline on real LeadGenie tasks.
  See `references/harnessbench-evals.md` for local and GitHub Actions usage.

Do not invoke this skill from the plugin yet — in a LeadGenie checkout, use the repo-local
`/auto-pr`.
