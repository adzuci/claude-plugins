# Weekly Teams

Index for `--weekly <team>`. Each team keeps its own file in `weekly-teams/`. The skill reads only the matching file, so one team's details never leak into another team's draft.

| Team | Aliases | Team file | Status |
| --- | --- | --- | --- |
| DevOps | `devops` | [weekly-teams/devops.md](weekly-teams/devops.md) | Complete |
| Design System | `design-system`, `design systems` | [weekly-teams/design-system.md](weekly-teams/design-system.md) | Slack fields confirmed; tracker and status source TODO |
| AI Transformation | `ai-transformation` | [weekly-teams/ai-transformation.md](weekly-teams/ai-transformation.md) | Slack fields confirmed; tracker and status source TODO |

Several teams can share one channel and parent thread (for example the Platform squad thread). That is intentional: the `Poster` field in each team file is what tells the skill whose reply to use as the template, so identical channel and parent phrase across files are not copy-paste errors.

Teams without a file yet (for example BE Platform, FE Platform, Internal Eng) can be added with the recipe below.

## How to Add a Team

1. Copy `weekly-teams/_template.md` to `weekly-teams/<team-slug>.md` (lowercase, hyphens).
1. Fill the required fields. Find the channel ID and a parent `ts` from any weekly thread permalink: `https://<workspace>.slack.com/archives/<channel_id>/p<ts without dot>`.
1. Find the poster's Slack user ID from their profile ("Copy member ID").
1. Fill optional fields only with values you have confirmed. Write `TODO` for anything unknown; the skill treats `TODO` as missing and records a gap instead of guessing.
1. Add a row to the table above.
1. Dry-run `/apollo-eng-leadership:okr-report --weekly <team>` and review the Slack draft before sending.

## Required Fields

- **Team** and **aliases**: names accepted by `--weekly`, matched case-insensitively.
- **Slack workspace**: subdomain used for thread links (for example `apolloio`).
- **Slack channel ID**: where the weekly thread lives.
- **Parent search phrase**: text that appears in every weekly thread parent.
- **Poster**: name and Slack user ID of the person whose replies define the format.

## Optional Fields

- **Work tracker**: `jira` (host, project keys, blocked status name), another tool (for example a Notion workspace), or `none`.
- **OKR tracker**: link plus the period label it covers. Verify the period at run time.
- **Status color source**: `metrics` (KR targets in the team file), `tracker` (current tracker status column), or `none` (always `pending metrics`).
- **Metrics**: exact slash commands with `--from`/`--to`, whether a prior-week value is needed for trend, and the manual source the user can read values from.
- **KR targets**: last known values with the date and source they were recorded from.
- **Highlights source**: conversation ID plus a header regex that identifies the right post.
