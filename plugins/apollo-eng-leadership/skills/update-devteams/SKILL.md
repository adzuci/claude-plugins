---
name: update-devteams
description: Maintain apollo-dev-teams.yml after engineering reorganizations — report-only audits, safe metadata updates, and read-only reconciliation against the Notion Teams DB.
allowed-tools: Bash(node *update-devteams*/scripts/update-devteams.js *), Bash(find *update-devteams*), Bash(rg *), Bash(git diff *), Bash(git status *), Bash(bundle exec rspec packs/util/spec/lib/apollo_dev_team_spec.rb *), Bash(pnpm run generate:route-owners *), Read, Edit, mcp__notion__API-post-search, mcp__notion__API-retrieve-a-database, mcp__notion__API-retrieve-a-data-source, mcp__notion__API-query-data-source
disable-model-invocation: true
---

# Update Dev Teams

Use `/update-devteams` to keep `apollo-dev-teams.yml` accurate after engineering reorgs. The file drives dashboards, automations, ownership, on-call routing, Sentry/PagerDuty metadata, Slack notifications, GitHub teams, and generated ownership files.

Modes:

- `/update-devteams` (report) — audit the YAML and nearby owner metadata (default).
- `/update-devteams update` — apply explicit, reviewed metadata fixes.
- `/update-devteams notion` — read-only reconciliation of `apollo-dev-teams.yml` against the Notion Teams DB; reports what needs updating without guessing.

`apollo-dev-teams.yml` is the source of truth. The Notion Teams DB is a secondary view; when they disagree, prefer the YAML unless the caller confirms otherwise.

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
- In Notion mode, never guess the join key, field mappings, or unmatched rows. Ask the caller (or leave the item unmapped) instead of inferring. Notion mode is read-only — it does not write to the YAML or to Notion.

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

## Notion Mode

`/update-devteams notion` compares `apollo-dev-teams.yml` (source of truth) with the Notion Teams DB and reports what needs updating. It is **read-only**: it never edits the YAML or Notion, and it never guesses how the two systems line up.

Teams DB: <https://app.notion.com/p/apolloio/9c146c222de24dc7aba0d4a4ab7a1378?v=14f923ad1dac434b9f7ebd2172a0c7c5>

### Step 1 — Export the Notion Teams DB

Fetch the DB with the Notion MCP and save the raw response to a local JSON file. Use the page/database ID from the link above (`9c146c222de24dc7aba0d4a4ab7a1378`).

1. Retrieve the database, then its data source(s) (`API-retrieve-a-database` → `API-retrieve-a-data-source`). If the ID is not directly accessible, find it with `API-post-search` (filter `data_source`).
1. Query the data source pages (`API-query-data-source`), paging through all results.
1. Save the response as JSON, e.g. `/tmp/notion-teams.json`. The script accepts either the raw Notion query response (`{ "results": [ ... ] }`) or a flat array of rows.

Do not hand-transcribe values from the Notion UI — export the actual data so the comparison is deterministic.

Pass the export with `--notion-json <path>`, or pipe it on stdin when the flag is omitted (e.g. `... | node "$SCRIPT" notion --key-notion "Team"`). Both input paths accept the same two shapes.

### Step 2 — Discover the schema (no guessing)

Run without a key to list the Notion properties and YAML fields, then decide the mapping with the caller:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" notion \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --notion-json /tmp/notion-teams.json
```

The tool prints the detected Notion property names and the comparable YAML fields, then stops. It will not assume which property identifies a team or how fields correspond.

### Step 3 — Reconcile with an explicit mapping

Pass the identifier property (`--key-notion`) and one `--map yamlField=NotionProperty` per field to compare. Only mapped fields are checked; matching is case-insensitive by default (add `--exact` for strict equality). Confirm each mapping with the caller before relying on it.

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" notion \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --notion-json /tmp/notion-teams.json \
  --key-notion "Team" \
  --key-yaml name \
  --map name="Team" \
  --map team_slack="Slack Channel"
```

The report separates the work into clearly labeled sections:

- **Update** — matched teams and their mapped-field differences (`YAML="…" vs Notion[Property]="…"`). YAML is the source of truth, so update the Notion page to match. A field diff appears only for fields you mapped with `--map`; nothing is guessed.
- **Create** — teams in the YAML with no Notion page (and not on the exclude list): create/reconcile them in Notion.
- **Intentionally not synced** — excluded teams with no Notion page (see `--exclude` below): listed here rather than as create candidates.
- **Orphaned** — rows in Notion but missing from the YAML: flagged for a human decision (stale row, rename, or missing from source of truth). Never auto-deleted.
- rows/teams skipped because their identifier was blank.

Add `--json` to emit the raw reconciliation for further processing. Notion mode never writes — `--write` is rejected.

### Excluding teams that intentionally have no Notion page

Some teams are not product teams and intentionally have no Notion page — e.g. `db-migrations` (infra guild), and others such as `call-commander`, `fraud`, and `zenleads`. Without help, these show up under **Create** as if they need a Notion page. Pass `--exclude` (comma-separated, repeatable; normalized the same way as the join key) to move them into **Intentionally not synced** instead:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" notion \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --notion-json /tmp/notion-teams.json \
  --key-notion "Team" \
  --map name="Team" \
  --exclude db-migrations,call-commander,fraud
```

If an excluded team *does* have a Notion page, it is surfaced under **Excluded teams with a Notion page (possible cleanup)** so a human can decide whether to archive it. Confirm the exclusion list with the caller before syncing — the exclude flag is a CLI/report concern only; do not add an exclusion field to `apollo-dev-teams.yml` (it is validated by a Ruby spec).

### Step 4 — Confirm drafts, then apply

Summarize the findings concisely as draft changes and ask the caller to confirm before doing anything:

- YAML metadata fixes go through update mode after confirmation, e.g. `node "$SCRIPT" update --teams apollo-dev-teams.yml --set <team>.<field>=<confirmed-value> --write`.
- Notion-side edits are made by a human in the Notion UI — this skill does not write to Notion.
- Leave unmatched rows and unmapped fields as open TODOs for a human; never invent mappings or values.

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
