# Harnessbench Example: A/B Testing /auto-pr

Copy-ready [apolloio/harnessbench](https://github.com/apolloio/harnessbench) experiment that
runs the `/auto-pr` skill against a no-skill baseline on a real LeadGenie task, scored by
deterministic oracles + an LLM judge, and reported as a leaderboard. Criteria come from
[`auto-pr-eval-rubric.md`](auto-pr-eval-rubric.md).

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
BASE_COMMIT=$(grep -hm1 '^baseCommit:' "$EXAMPLE_DIR"/tasks/*.yaml | cut -d'"' -f2)
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
```

A dry-run is valid only when the command exits zero and every matrix row reports
`patchApply=true`. Piping through `tee` requires `set -o pipefail`; otherwise a failed
HarnessBench process can appear green.

Further revisions become `auto-pr-v3.patch` etc. — add each to `experiment.yaml`'s `variants`
and the leaderboard shows Δ vs. baseline per variant.

## GitHub Actions

`.github/workflows/harnessbench.yml` is the implementation source for triggers, secrets, and
runner setup. PR changes get free schema/patch validation. Paid scored runs remain manual and
upload `report.md`, `aggregate.json`, the manifest, and per-cell transcripts/diffs.

Cross-repo access: both jobs need the optional `APOLLOIO_TOKEN` secret (org secret with read access
to `apolloio/harnessbench` and `apolloio/leadgenie`); the default `github.token` can only read
this repo. Until the secret is provisioned, the dry-run job skips its harnessbench steps with
a notice (green, not red). The full run additionally uses the org-level `APOLLO_REVIEW_BOT_ANTHROPIC_KEY`.

## Known Limitations (v1)

<!-- Review flagged a "cross-reference loop" with the rubric. Not a loop: this section is the
     sole canonical copy (rubric one-directionally points here, doesn't restate content) — the
     intended fix from the earlier dedup pass. -->

- **Interactivity**: /auto-pr has four human touchpoints; harnessbench runs unattended. The
  task prompt pre-answers them (plan pre-approved, Codex skipped, no browser evidence) and the
  judge checks the skill *asked/reported correctly*. A scripted-user responder in harnessbench
  would remove this compromise.
- **Side effects**: the task prompt forbids pushing/PR-creation/bot-polling, so the bot-loop
  rubric items (P6) aren't covered here — they need a fixture PR outside harnessbench.
- **Heavy service deps**: docker/browser deps per cell are heavy; long-lived service boot is on
  the harnessbench roadmap but not landed. Start with the backend-only golden task.
- **baseCommit drift**: the pinned SHA must match what the variant patch applies to; refresh
  both together (the dry-run catches mismatches).

## Triggering the eval

- **Free validation** (dry-run): every PR touching any `plugins/**/evals/harnessbench/**`
  path (or the workflow itself). Result lands as a sub-50-word summary comment on the PR and the
  full matrix in the job log.
- **Scored run** (spends tokens): manually use GitHub → Actions → `harnessbench` → *Run
  workflow*, choose the PR branch, check `full_run`, and provide the PR number for the sticky
  result comment. The leaderboard and full evidence upload as `harnessbench-report`.
- **Locally**: see "Local Run" above.

## Adding evals for a new skill

This example is skill-specific, but the wiring pattern (auto-discovery, task/experiment schema,
variant-patch generation, dry-run vs. scored dispatch) applies to any skill. See the general
recipe in [`harnessbench-evals-guide.md`](https://github.com/apolloio/claude-plugins/blob/main/harnessbench-evals-guide.md)
at the repo root.
