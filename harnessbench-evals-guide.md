# Adding HarnessBench Evals for a Skill

`.github/workflows/harnessbench.yml` discovers HarnessBench files under
`plugins/**/evals/harnessbench/**` for PR triggering and copying. Execution is currently
LeadGenie-specific: it provisions the LeadGenie workspace and runs only
`leadgenie/auto-pr-smoke`. A skill targeting another repository needs explicit workspace,
variant-generation, and experiment-selection wiring before the shared dry-run validates it. See
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
1. For a LeadGenie experiment, open a PR and confirm the dry-run validates its schemas and patch
   application. For another repository, first extend the workflow to provision and select that
   workspace; until then, a green auto-pr dry-run does not validate the new fixture. Dispatch a
   scored run only after the selected experiment's dry-run is green.
