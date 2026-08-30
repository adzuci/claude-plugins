# HarnessBench Evaluations

Use the package under `evals/harnessbench/` to compare the original and current
`customer-problem-loop` skill on the same synthetic LeadGenie tasks used to calibrate `auto-pr`.

The experiment reports three separate results:

- repository outcome oracles for the implemented behavior;
- deterministic checkpoint and guardrail adherence from the transcript;
- a qualitative judge score with concrete transcript evidence.

CI dry-runs every task and both skill patches without starting an agent or judge. A manually
dispatched scored run uses `leadgenie/customer-problem-loop-smoke`, three repetitions, and the pinned
models and HarnessBench revision in `.github/workflows/harnessbench.yml`.

The current calibration tasks are local and synthetic. They verify problem understanding, current
behavior inspection, plan binding, implementation, code-quality checks, truthful evidence gaps, and
the final handoff. They do not prove real browser capture, Slack reply normalization, same-session
resume, external PR behavior, or Operator/Pantheon enforcement.
