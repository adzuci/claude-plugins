# <Team Name>

Worked example: [devops.md](devops.md) is the most complete team file; copy its structure.

Copy this file to `<team-slug>.md`. Replace every `<...>`. Write `TODO` for anything you have not confirmed.

## Slack

- **Aliases**: `<slug>`, `<other name>`
- **Workspace**: `<workspace subdomain>`
- **Channel ID**: `<C...>` (`#<channel-name>`)
- **Parent search phrase**: `<text in every weekly parent>`
- **Template filter hint** (optional): how to recognize this team's real updates if its posts do not have 2 bold or italic headers or a status emoji, for example a fixed title prefix. Delete if unused.
- **Poster**: <Name>, `<U...>`

## Work Tracker

- **Type**: `jira` | `<other tool>` | `none`
- **Jira host**: `<site>.atlassian.net`
- **Jira projects**: `<KEY>`, `<KEY>`
- **Blocked status name**: `<Blocked>`

## OKR Tracker and Status

- **OKR tracker**: <link> (period: <label as shown in the sheet>; verify before use)
- **Status color source**: `metrics` | `tracker` | `none`

## Metrics

| Metric | Slash command | Trend (needs prior week) | Manual source |
| --- | --- | --- | --- |
| <metric> | `/<plugin>:<skill> --from <YYYY-MM-DD> --to <YYYY-MM-DD>` | yes/no | <page the user reads> |

## KR Targets (Last Known)

Verify against the current OKR tracker before using. A "Baseline" or second target column is the prior period's baseline, never current status.

| KR | Metric | Target | Recorded | Source |
| --- | --- | --- | --- | --- |
| <KR id> | <metric> | <target> | <YYYY-MM-DD> | <tracker link or doc> |

## Highlights Source

- **Conversation ID**: `<D... or C...>`
- **Header regex**: `<regex>` (matches `<example first line>`). It is matched against the trimmed first line of the post, so anchor it with `^`.
