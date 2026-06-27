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

## Safety

- Do not delete or rename teams when ownership is ambiguous.
- Verify replacement Slack channels and on-call usergroups before writing.
- Keep metadata string fixes separate from ownership transfers.
- Treat generated ownership outputs as generated unless the repo workflow says otherwise.
