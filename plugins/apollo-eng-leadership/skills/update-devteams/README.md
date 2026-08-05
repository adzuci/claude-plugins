# /update-devteams

Shared skill for maintaining `apollo-dev-teams.yml` after engineering reorgs.

## Report Mode

Use this first. It inspects `apollo-dev-teams.yml` and nearby owner metadata without writing files:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report --repo-root . --teams apollo-dev-teams.yml
```

To save a report for review:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report --repo-root . --teams apollo-dev-teams.yml > /tmp/update-devteams-report.md
```

To create an HTML report for PR sharing:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" report \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --html /tmp/update-devteams-report.html
```

The HTML report is intentionally nudge-focused: a compact screenshot-friendly card first, current progress, owner groups that need attention, open cleanup buckets, last-10-days commit activity, and collapsed detail tables for backup. Red rows mean known drift to fix; yellow rows mean the expected on-call/PagerDuty posture needs confirmation.

Report mode caches progress snapshots in `/tmp` by default, with a repo-specific filename such as:

```text
/tmp/update-devteams-progress-history-<repo>.json
```

Use `--no-cache` to skip caching, `--cache <path>` to write history elsewhere, or `--goal-date YYYY-MM-DD` to pin the 100% target date. The HTML graph uses the last 10 days of `apollo-dev-teams.yml` commit history.

## Update Mode

Update mode is dry-run by default. It writes only when `--write` is present.

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" update \
  --teams apollo-dev-teams.yml \
  --set inbound.alerts_slack=#confirmed-inbound-alerts
```

Apply after verification:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" update \
  --teams apollo-dev-teams.yml \
  --set inbound.alerts_slack=#confirmed-inbound-alerts \
  --write
```

## Notion Mode

Read-only reconciliation of `apollo-dev-teams.yml` (source of truth) against the Notion Teams DB. It reports drift and never edits the YAML or Notion.

First export the Notion Teams DB via the Notion MCP (retrieve the data source, then query its pages) and save the JSON, e.g. `/tmp/notion-teams.json`. Then discover the schema — the tool lists Notion properties and YAML fields and stops, so it never guesses the mapping:

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" notion --repo-root . --teams apollo-dev-teams.yml --notion-json /tmp/notion-teams.json
```

Then reconcile with an explicit identifier and field mappings (case-insensitive match by default; add `--exact` for strict):

```bash
SCRIPT=$(find ~/.claude ~/.codex "$PWD" -maxdepth 10 -path '*/update-devteams/scripts/update-devteams.js' -print -quit 2>/dev/null)
node "$SCRIPT" notion \
  --repo-root . \
  --teams apollo-dev-teams.yml \
  --notion-json /tmp/notion-teams.json \
  --key-notion "Team" \
  --map name="Team" \
  --map team_slack="Slack Channel"
```

The report lists matched-team field differences, teams missing from Notion, and Notion rows missing from the YAML. Present the findings as concise draft changes, confirm with the caller, then apply confirmed YAML fixes with update mode. Notion-side edits are made by a human. Add `--json` for the raw reconciliation.

## Safety

- Do not delete or rename teams when ownership is ambiguous.
- Notion mode is read-only and never guesses the join key, field mappings, or unmatched rows — confirm draft changes before applying anything.
- Verify replacement Slack channels and on-call usergroups before writing.
- Keep metadata string fixes separate from ownership transfers.
- Treat generated ownership outputs as generated unless the repo workflow says otherwise.
