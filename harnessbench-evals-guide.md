# Adding HarnessBench Evals for a Skill

`.github/workflows/harnessbench.yml` auto-discovers every skill's harnessbench files under
`plugins/**/evals/harnessbench/**` — no workflow edits needed for tasks/experiments. This is
the general recipe for wiring a new skill into it; see
[`plugins/apollo-eng/skills/auto-pr/evals/harnessbench/`](plugins/apollo-eng/skills/auto-pr/evals/harnessbench/)
for a worked example.

1. Create `plugins/<plugin>/skills/<skill>/evals/harnessbench/tasks/<task-id>.yaml` — schema per
   the auto-pr examples (`baseCommit` pinned to a full SHA, `agent.prompt` in natural language so a
   no-skill baseline can attempt the same work, `oracles` for deterministic PASS/FAIL, `judge.hint`
   carrying your rubric).
1. Create `.../evals/harnessbench/experiments/<experiment-id>/experiment.yaml` listing your tasks,
   variants, `baselineVariant: baseline`, and `repetitions`.
1. Variant patches are generated at run time, not committed. Add a generation step for your
   skill's source PR/branch to the "Generate variant patch" steps in
   `.github/workflows/harnessbench.yml` (the one per-skill edit), mirroring the auto-pr curls.
1. Open a PR — the dry-run validates your schemas and that every patch applies at your
   `baseCommit`. Then dispatch a scored run when you're ready to spend tokens.
