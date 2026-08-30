# Harnessbench Example: A/B Testing /auto-pr

Copy-ready [apolloio/harnessbench](https://github.com/apolloio/harnessbench) calibration that
runs the `/auto-pr` skill against a no-skill baseline on four fixed LeadGenie tasks, scored by
semantic outcome oracles + a Stage 0–7 transcript auditor + an LLM judge. Criteria come from
[`auto-pr-eval-rubric.md`](auto-pr-eval-rubric.md).

This is a **calibration smoke**, not an end-to-end `/auto-pr` gate: remote PR, bot, Codex, and
browser stages are constrained in every task. Do not use its leaderboard alone to approve a skill
revision.

## Local Run

```bash
git clone git@github.com:apolloio/harnessbench.git && cd harnessbench && npm install
# 1. Target repo: clone leadgenie where repo.yaml expects it. The clone's origin URL
#    must match repo.yaml's url (a preflight check compares them).
git clone git@github.com:apolloio/leadgenie.git .harness/repositories/leadgenie
# 2. Copy this example into the workspace (adjust EXAMPLE_DIR to your claude-plugins clone)
EXAMPLE_DIR=../claude-plugins/plugins/apollo-eng/skills/auto-pr/evals/harnessbench
cp "$EXAMPLE_DIR"/tasks/*.yaml workspace/leadgenie/tasks/
cp -r "$EXAMPLE_DIR"/experiments/auto-pr-smoke workspace/leadgenie/experiments/
# Align repo setup with the tasks' pinned base and LeadGenie's package manager.
BASE_COMMIT=$(grep -h '^baseCommit:' "$EXAMPLE_DIR"/tasks/*.yaml | head -1 | cut -d'"' -f2)
sed -i.bak "s|defaultBaseCommit: .*|defaultBaseCommit: \"$BASE_COMMIT\"|" workspace/leadgenie/repo.yaml
sed -i.bak 's|installCmd: npm ci|installCmd: pnpm install --frozen-lockfile|' workspace/leadgenie/repo.yaml
rm workspace/leadgenie/repo.yaml.bak
# 3. Generate the variant patches (regenerate per revision)
#    v1 = original skill (leadgenie#97782); v2 = review-refined (leadgenie#97942 branch,
#    which also carries its CLAUDE.md additions — part of the same landing)
gh pr diff 97782 --repo apolloio/leadgenie > workspace/leadgenie/variants/auto-pr-v1.patch
V2_HEAD=$(gh api repos/apolloio/leadgenie/pulls/97942 --jq .head.sha)
gh api "repos/apolloio/leadgenie/compare/master...$V2_HEAD" \
  -H "Accept: application/vnd.github.v3.diff" > workspace/leadgenie/variants/auto-pr-v2.patch
# 4. Validate without spending tokens (schemas + git apply --check on every variant).
#    Note: the CLI script is `harnessbench` (harnessbench's own README says
#    `npm run harness`, which doesn't exist as of v0.2.0).
npm run harnessbench -- run leadgenie/auto-pr-smoke --dry-run
# 5. Run for real (needs ANTHROPIC_API_KEY in harnessbench's .env, claude CLI,
#    Node >= 24). Consider repetitions: 1 in experiment.yaml for a first smoke run.
npm run harnessbench -- run leadgenie/auto-pr-smoke
npm run harnessbench -- report leadgenie/auto-pr-smoke/latest
# Score stage adherence separately from outcome oracles and the generic judge.
RUN_DIR=$(find runs/leadgenie/auto-pr-smoke -mindepth 1 -maxdepth 1 -type d | sort | tail -1)
python "$EXAMPLE_DIR/scripts/audit_stage_adherence.py" "$RUN_DIR" \
  --contract "$EXAMPLE_DIR/stage-contract.json" \
  --output "$RUN_DIR/stage-adherence.json"
# Required stage/safety failures make the candidate fail. Wording-dependent skip reports and the
# exact Stage 0-7 ledger remain visible diagnostics and do not independently fail a cell.

# Validate the next checkpoint/repair contract and sanitized multi-turn calibration package.
# READY_FOR_GOLD_REVIEW is expected until the product owner approves the scenario labels.
python "$EXAMPLE_DIR/scripts/validate_checkpoint_flow.py" \
  --contract "$EXAMPLE_DIR/checkpoint-flow-contract.json" \
  --scenarios "$EXAMPLE_DIR/stateful-scenarios.json"
```

A dry-run is valid only when the command exits zero and every matrix row reports
`patchApply=true`. Piping through `tee` requires `set -o pipefail`; otherwise a failed
HarnessBench process can appear green.

The two `sed` edits in step 2 are **best-effort against HarnessBench's `repo.yaml` schema as of
2026-08-13** (`defaultBaseCommit: "master"`, `installCmd: npm ci` nested under `setup:`). They
match on literal text and will silently no-op if either key is renamed, re-nested, or already
holds a different value. Before running, confirm the keys still exist, and after running diff the
result rather than trusting exit status:

```bash
grep -nE 'defaultBaseCommit|installCmd' workspace/leadgenie/repo.yaml   # before and after
```

`defaultBaseCommit` must end up as the tasks' pinned SHA and `installCmd` as
`pnpm install --frozen-lockfile`; if not, edit `repo.yaml` by hand. Getting this wrong produces a
run against the wrong base or a broken install, not an obvious error.

Further revisions become `auto-pr-v3.patch` etc. — add each to `experiment.yaml`'s `variants`
and the leaderboard shows Δ vs. baseline per variant.

## GitHub Actions

`.github/workflows/harnessbench.yml` is the implementation source for triggers, secrets, and
runner setup. PR changes get free schema/patch validation. Paid scored runs remain manual and
upload `report.md`, `aggregate.json`, the manifest, per-cell transcripts/diffs,
`stage-adherence.json`, and `runtime-provenance.json` with 30-day retention.

Cross-repo access: both jobs need the optional `APOLLOIO_TOKEN` secret (org secret with read access
to `apolloio/harnessbench` and `apolloio/leadgenie`); the default `github.token` can only read
this repo. Until the secret is provisioned, the dry-run job skips its harnessbench steps with
a notice (green, not red). The full run additionally uses the org-level `APOLLO_REVIEW_BOT_ANTHROPIC_KEY`.

## Known Limitations (v1)

- **Judge model compatibility**: HarnessBench once hardcoded `temperature:0` on every judge call,
  which newer models (opus-4-7/4-8/5, sonnet-5, fable-5, mythos-5) reject.
  [apolloio/harnessbench#7](https://github.com/apolloio/harnessbench/pull/7) made it
  model-conditional — those judges only work when the pinned HarnessBench SHA includes that fix.
- **Interactivity**: /auto-pr normally has four human touchpoints, with additional questions only
  for material changes or true ambiguity; harnessbench runs unattended. The task
  prompt authorizes local work after the plan and constrains browser/Codex/remote stages. The
  transcript auditor checks that the plan still precedes writes and constrained stages are
  reported. A helper now normalizes scripted responses and binds natural-language approvals, but a
  responder that resumes the same agent session is still required to inject checkpoint failures,
  test repair routing, and test real approval state transitions. The
  checkpoint contract and scenarios are validated in CI, but they are not yet run against skill
  variants.
- **Side effects**: the task prompt forbids pushing/PR-creation/bot-polling, so the bot-loop
  rubric items (P6) aren't covered here — they need a fixture PR outside harnessbench.
- **Heavy service deps**: docker/browser deps per cell are heavy; long-lived service boot is on
  the harnessbench roadmap but not landed. The current four-task calibration remains backend-only.
- **baseCommit drift**: the pinned SHA must match what the variant patch applies to; refresh
  both together (the dry-run catches mismatches).
- **Provider revision identity**: the workflow pins the HarnessBench and Claude Code revisions and
  hashes tasks, variants, experiment, and stage contract. The configured agent/judge model IDs are
  retained, but immutable provider-side model revisions are not currently exposed.

## Triggering the eval

- **Free validation** (dry-run): every PR touching any `plugins/**/evals/harnessbench/**`
  path (or the workflow itself). Result lands as a sub-50-word summary comment on the PR and the
  full matrix in the job log.
- **Scored run** (spends tokens): manually use GitHub → Actions → `harnessbench` → *Run
  workflow*, choose the PR branch, check `full_run`, and provide the PR number for an append-only
  run summary. Four tasks × three variants × three repetitions = 36 paid cells. The summary leads
  with validity and stage adherence; full evidence uploads as `harnessbench-report`.
- **Locally**: see "Local Run" above.

## Adding evals for a new skill

This example is skill-specific, but the wiring pattern (auto-discovery, task/experiment schema,
variant-patch generation, dry-run vs. scored dispatch) applies to any skill. See the general
recipe in [`harnessbench-evals-guide.md`](../../../../../harnessbench-evals-guide.md) at the
`claude-plugins` repo root.
