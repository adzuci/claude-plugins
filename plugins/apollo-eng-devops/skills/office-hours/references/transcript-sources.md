# Transcript Sources

Use this reference when `/apollo-eng-devops:office-hours recap` needs office-hours notes
or transcripts. Keep the run token-efficient: use at most two transcript/note sources.

## Source Priority

| Priority | Source | Use when | Notes |
| --- | --- | --- | --- |
| 1 | Granola MCP | A Granola connector is available. | Prefer for meeting notes and transcripts. Summarize; do not paste full transcripts. |
| 2 | Notion meeting notes | The Notion meeting-notes tool is available. | Query by date first, then title terms if needed. |
| 3 | Glean MCP, app `zoom` | Direct Zoom or Granola access is missing. | Use short queries and date filters. |
| 4 | Local script fallback | MCP sources are missing or inconclusive. | Uses the local `glean` CLI against scriptable indexed sources. |

Slack is not a transcript source by default. Use Slack only for the final approved post,
or when the caller explicitly asks to include Slack context.

## Query Pattern

Start narrow and date-bounded:

1. `office hours`
1. `devops`
1. `xfn h devops`
1. `Adam Blackwell`
1. `Eng Design Office Hours`
1. `DOH`

For today, use the exact date in the caller's local timezone. If no result is found,
label the result as no match found instead of widening into unrelated historical office
hours.

## Script Fallback

From the skill directory (canonical usage):

```bash
python3 scripts/find_office_hours_transcript.py --date 2026-06-10 --query "office hours" --max-sources 2 --json
```

The script searches only scriptable indexed sources using the local `glean` CLI. It never
uses Slack, never posts, and never mutates data.

Default source order:

1. `zoom`
1. `notion`

The script emits:

- source status;
- a capped list of candidate titles and URLs;
- content/snippet preview;
- confidence;
- failure reason when no candidate is found.

## Review Gate

Before any Slack write, show:

1. sources checked;
1. proposed recap;
1. exact Slack message for `#xfn-h-devops`;
1. the approval phrase: `Reply "post this" if you want me to send this exact update`.

Approval must be explicit and must refer to the exact message shown.
