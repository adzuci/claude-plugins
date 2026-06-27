---
name: update-devteams
description: Maintain apollo-dev-teams.yml after engineering reorganizations — report-only audits and safe metadata updates.
allowed-tools: Bash(node *update-devteams*/scripts/update-devteams.js *), Bash(find *update-devteams*), Bash(rg *), Bash(git diff *), Bash(git status *), Bash(bundle exec rspec packs/util/spec/lib/apollo_dev_team_spec.rb *), Bash(pnpm run generate:route-owners *), Read, Edit
disable-model-invocation: true
---

# Update Dev Teams

Use `/update-devteams` to keep `apollo-dev-teams.yml` accurate after engineering reorgs. The file drives dashboards, automations, ownership, on-call routing, Sentry/PagerDuty metadata, Slack notifications, GitHub teams, and generated ownership files.

## Workflow Contract

**Deterministic (script output):** The report and dry-run diff are reproducible — re-running with the same YAML produces the same findings.

**Requires human judgment:** Confirming canonical owners for ambiguous teams; verifying Slack channel and on-call usergroup names are live and correct; deciding whether to delete a team vs. rename it; reviewing ownership transfers that affect incident routing or PagerDuty.

**After running:** Review the report, open a PR for mechanical metadata cleanups (strings, empty members, stale slugs), and coordinate separately with the listed EMs for ownership transfers. Use the HTML report for async sharing with stakeholders.

## Safety Rules

- Do not publish the HTML report as an Artifact or share it to external services. Save it to a local path (e.g. `/tmp/update-devteams-report.html`) and share the path.
- Default to report mode. Do not edit when ownership is ambiguous.
- Never delete or rename a team silently.
- Separate string/metadata cleanups from ownership changes.
- Verify replacement Slack channels and Slack on-call usergroups before applying updates.
- If a team still owns packs, files, routes, alerts, or on-call routing, report it instead of deleting it.
- Keep PRs small and grouped by cleanup type or team area.
- Treat generated files (`CODEOWNERS`, `.github/teams.yml`, route owner constants) as generated outputs unless the repo workflow says to update them directly.
- Preserve comments and formatting where possible. For non-trivial YAML movement, prefer hand edits with review over broad serialization.
- Emit TODOs in the report for unclear cases instead of guessing.

## Report Mode

Run:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report --repo-root . --teams apollo-dev-teams.yml
```

Optional verification inputs:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --slack-channel-status-json /tmp/slack-channels.json \
  --usergroup-status-json /tmp/slack-usergroups.json
```

HTML report for PR sharing:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --html /tmp/update-devteams-report.html
```

Progress cache and goal controls:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --html /tmp/update-devteams-report.html \
  --cache /tmp/update-devteams-progress-history.json \
  --goal-date 2026-06-24
```

The report should include:

- total teams scanned
- compact screenshot-friendly nudge card
- progress toward 100% non-red and last-10-days `apollo-dev-teams.yml` commit activity
- owner groups that need a nudge
- open cleanup buckets and concise evidence
- red rows for known drift, yellow rows for missing on-call/PagerDuty expectations that need confirmation
- collapsible action-needed and no-action-needed detail tables
- detailed outside-reference groups in the HTML report

Initial targets to watch:

- `inbound`: detect Warm Outbound-era strings such as `#warm-outbound-alerts` and `oncall-warm-outbound`.
- `componentization`: likely dissolved/ghost-like; report if it still has active ownership before deletion.
- `zenleads`: pre-rebrand artifact; report as legacy and check `SKIP_AUTOMATION_FOR`/surface-owner references.
- `oncall-plays-fe`: stale owner metadata outside the YAML; detect references and require a confirmed replacement before editing.

Personnel facts (acting EMs, leave coverage, reorg-in-progress owners) go stale fast — do not hardcode them here. The report already flags any team with no EM in the YAML, which covers these cases generically.

## Update Mode

Only apply explicit, reviewable changes. The helper is dry-run by default and writes only with `--write`.

Set a known canonical YAML value:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" update \
  --teams apollo-dev-teams.yml \
  --set inbound.alerts_slack=#confirmed-inbound-alerts \
  --set inbound.on_call_usergroup_name=oncall-confirmed-inbound \
  --write
```

Replace duplicated owner metadata in specific files:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" update \
  --file scripts/performance-notification/metrics/plays-fe.ts \
  --replace-text oncall-plays-fe=oncall-confirmed-workflows \
  --write
```

Remove only obviously empty placeholder member entries:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" update \
  --teams apollo-dev-teams.yml \
  --team componentization \
  --remove-empty-members \
  --write
```

If a requested change implies transferring ownership (`packs_owned`, `files_owned`, `routes_owned`, PagerDuty keys, generated ownership outputs), stop and make a report/TODO unless the user has provided an explicit canonical mapping and verification source.

## Validation

After edits, run the narrow checks that match the change:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report --repo-root . --teams apollo-dev-teams.yml
git diff --check
```

For YAML/schema or ownership behavior changes, also run:

```bash
bundle exec rspec packs/util/spec/lib/apollo_dev_team_spec.rb
```

For route owner metadata changes, regenerate/verify route owner output according to the repo workflow:

```bash
pnpm run generate:route-owners
```
