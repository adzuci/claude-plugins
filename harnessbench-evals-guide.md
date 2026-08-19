# Adding HarnessBench Evals for a Skill

1. Create `plugins/<plugin>/skills/<skill>/evals/harnessbench/tasks/<task-id>.yaml` — schema per
   the auto-pr examples (`baseCommit` pinned to a full SHA, `agent.prompt` in natural language so a
   no-skill baseline can attempt the same work, `oracles` for deterministic PASS/FAIL, `judge.hint`
   carrying your rubric).
1. Create `.../evals/harnessbench/experiments/<experiment-id>/experiment.yaml` listing your tasks,
   variants, `baselineVariant: baseline`, and `repetitions`.
1. Variant patches are generated at run time, not committed. Add a generation step for your
   skill's source PR/branch to the "Generate variant patch" steps in
   `.github/workflows/harnessbench.yml` (the one per-skill edit), mirroring the auto-pr curls.
1. Add the experiment to the workflow's `experiment` dispatch choices and wire its path into the
   dry-run and full-run steps, then confirm the dry-run validates its schemas and patch
   application. A green dry-run for a *different* experiment does not validate your fixture.
   Dispatch a scored run only after your own experiment's dry-run is green.

`.github/workflows/harnessbench.yml` provisions two workspaces — LeadGenie (for
`leadgenie/auto-pr-smoke`) and claude-plugins (for `claude-plugins/wtf-smoke`) — and selects
between them via the `experiment` dispatch input. A skill targeting a third repository needs its
own workspace registration in harnessbench, plus variant-generation, trigger, and
experiment-selection wiring here. See
[`plugins/apollo-eng/skills/auto-pr/evals/harnessbench/`](plugins/apollo-eng/skills/auto-pr/evals/harnessbench/)
for a worked example.
