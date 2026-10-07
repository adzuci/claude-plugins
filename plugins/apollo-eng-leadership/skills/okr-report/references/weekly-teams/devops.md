# DevOps

## Slack

- **Aliases**: `devops`
- **Workspace**: `apolloio`
- **Channel ID**: `C0C2A75EMM4` (`#rnd-weekly-shareouts`)
- **Parent search phrase**: `Platform squad` (parents are often authorless `[Scheduled message]` posts)
- **Poster**: Adam Blackwell, `U0AD56G0YCS`

## Work Tracker

- **Type**: `jira`
- **Jira host**: `apollopde.atlassian.net` (also valid as `cloudId` for the claude.ai Atlassian connector)
- **Jira projects**: `INFRA`, `PLAT`
- **Blocked status name**: `Blocked` (status category In Progress, so query 2 must exclude it; confirmed 2026-10-05)

## OKR Tracker and Status

- **Status color source**: `metrics`
- **OKR trackers** (data, not proof of currency; verify the visible period and tab before citing):

| Period label | Source | Notes |
| --- | --- | --- |
| Q2 | [Engineering Q2 OKRs - DevOps tab](https://docs.google.com/spreadsheets/d/1On4W-vMS9Dv2P6IAAOIRFI6UGocbTj2V_oEl8csnmvE/edit?gid=443276456#gid=443276456) | Historical. Canonical KR wording for that period. |
| Q3 | [R&D FY27 Q3 OKRs](https://docs.google.com/spreadsheets/d/11kT9SoNIApo9l9V_V2H5yNUgUE3rTbGwLuAUSLPyaf4/edit) | Runs through 2026-10-31 (FY27 Q3, not calendar Q3). Confirmed rows: KR4.1 Apdex target >= 0.955 (second column 0.952 is the end-of-prior-period baseline). Candidate tabs `gid=21112414`, `gid=443276456`; which holds DevOps rows is unconfirmed. |
| Q4 | [R&D FY27 Q4 OKRs](https://docs.google.com/spreadsheets/d/1zUSppsF5p5IcYXrLj5u6AiIzMTzZ1BzE5TKZwrUKXc4/edit) | Next period; not current until it starts. |
| FY27Q1 | [R&D FY27Q1 OKRs + Initiatives](https://docs.google.com/spreadsheets/d/1VdsO-mQ54zrYZQNUhV4OkmqhZxunT4rubzrjErsxWUg/edit?gid=1405873114#gid=1405873114) | Historical only. Jira links may still point here. |

When the reporting date is past a tracker's period, search for the next period's tracker instead of reusing the newest row above.

## Metrics

Both skills are `disable-model-invocation: true`. Never call them through the Skill tool; print the commands and ask the user to paste values (manual) or mark them unavailable (routine).

| Metric | Slash command | Trend (needs prior week) | Manual source |
| --- | --- | --- | --- |
| Apdex | `/apollo-eng-devops:check-apdex --from <WEEK_START> --to <DATA_THROUGH>` | yes | Apollo Admin BE Performance Monitoring page, `https://app.apollo.io/#/admin/performance-monitoring`. Paste the precise Apdex in parentheses (for example 0.9464, not the rounded 0.950) for the reporting week, the prior week, and every earlier week of the current period (the period ends 2026-10-31 for FY27 Q3), with each window's dates, so reachability can be tested |
| Uptime and 10+ min incidents | `/apollo-eng-devops:check-uptime --from <WEEK_START> --to <DATA_THROUGH>` | no | Uptime and the count of 10+ minute downtime incidents for the window from `sasta.oncall.io` (exclude scheduled maintenance). Per-component uptime is also on the Infrastructure section of the Admin page above. The same data may also be in Snowflake (unconfirmed; verify table and owner before relying on it). If no incident count is pasted, say it was not verified |

For the Apdex trend, also print the prior-week command with that week's dates.

## KR Targets (Last Known)

Verify against the current tracker before using. In these trackers a "Baseline" or second target column is the prior period's baseline (for example the earlier Apdex 0.965 next to a newer target), never current status or the current target.

| Period label | KR | Metric | Target | Recorded | Source |
| --- | --- | --- | --- | --- | --- |
| Q2 | Reliability (single KR) | Uptime, Apdex, incidents | Uptime > 99.93%, Apdex > 0.965, at most 2 downtime incidents of 10+ min | before 2026-09 | Q2 DevOps tab above |
| Q3 | KR4.1 | Apdex | Apdex >= 0.955 | 2026-10-05 | Q3 OKR sheet, Objective 4 rows (read via Glean 2026-10-05); tab gid unconfirmed, verify before use |
| Q3 | KR4.4 | Uptime and incidents | Uptime > 99.93%, at most 2 downtime incidents of 10+ min | 2026-10-05 | Q3 OKR sheet, Objective 4 rows (read via Glean 2026-10-05); tab gid unconfirmed, verify before use |

The Q2 reliability KR is one KR with three thresholds checked over the same window, not three KRs. Never apply one period's thresholds to another period's status call.

## Highlights Source

- **Conversation ID**: DevOps Bot DM `D0BKLJ9QD3K`
- **Header regex**: `^\*DevOps highlights \d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}\*` (matches `*DevOps highlights 2026-09-28 to 2026-10-02*`)
