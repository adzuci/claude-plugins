# 53 — Tracker Updates and the Intake Grill

## Pick the Update Tracker

Onboarding asks one tracker question. The recommended default comes first.

| Persona | Default |
|---|---|
| Engineer, QA | Jira |
| PM, EM, end to end | Jira and Notion |
| Designer, researcher | Notion |

The profile stores the choice under `updates`. Jira and `both` require `jira_project`.
`jira_issue` is an optional default issue. The Notion value reuses the profile's existing
`notion_parent`.

Jira updates require the Atlassian connector in doc 39. When it is unavailable, onboarding records
`tracker_blocked: jira` and updates go to Notion until the connector works. The selected tracker is
retained.

## Post a Stage Update

At a stage boundary, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/post-update.py" \
  --stage <stage> --summary <summary> --links <comma-separated-links> \
  --issue <optional-Jira-issue> --initiative <initiative> --run <run-id> \
  --event <stage-event-id> --agent <stage-agent> --outcome <stage-outcome> --profile <profile>
```

The script prints JSON. It never calls an MCP server. Execute each call in the plan.

- Notion uses the existing `storage.py ledger-entry` and `notion-update-page insert_content` flow. It
  publishes the stage's existing event, agent and outcome. The stage summary becomes the event note.
  In notion storage, this is the stage event append; do not append the same event first.
- Jira uses `mcp__atlassian__addCommentToJiraIssue`.
- Jira issue order is `--issue`, the selected initiative and run's current intake tracker issue, then
  profile `jira_issue`. Only the latest intake snapshot revision is read. If it says `jira: blocked:`,
  Jira stays blocked instead of falling back to an older revision or the profile default.
- With no Jira issue, the plan says `blocked: no Jira issue`. A `both` profile still posts to Notion.

Do not post the 5-to-10-minute progress pulse. Post only the stage-end summary.

## Complete the Intake Grill

Every persona completes the items in `templates/grill-checklist.yml`. Read artifacts and code first.
Ask only decisions that cannot be looked up, one at a time, with the recommendation first. A full
`grill-me` interview is only for an ambiguous idea with no artifacts.

The `A.context` snapshot contains:

```markdown
## Grill
- <item>: <answer> (source: <doc|user|code path>)
- <item>: deferred: <reason>
```

Run `scripts/grill-check.py <snapshot> --persona <persona>`. Missing items exit 2, list each missing
decision, and end with `Next:`. `record-sync.sh push` runs the same check for `A.context` snapshots.

For tracker `jira` or `both`, every stage snapshot also has `jira: <KEY-123>` or
`jira: blocked:<reason>`. Notion-only profiles do not need that line. Sync checks every run it publishes
and the latest revision of each snapshot. It validates each `A.context` grill with the `persona:`
recorded in that snapshot.
