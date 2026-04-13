# LU_EMPLOYEE_ACTIVITY

> **Weekly activity digest per Apollo employee.** One row per (person, week). Aggregates signals from GitHub, SFDC, Gong, Jira, and Slack into per-source summaries. Squad rollup rows use IS_SQUAD_ROLLUP=TRUE.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_EMPLOYEE_ACTIVITY` |
| **Grain** | One row per employee email + week |
| **Row count** | ~671 (2026-04-06, first population) |
| **Refresh cadence** | Manual (`scripts/employee_activity/run_all.sh`) |
| **Trust level** | Playground — experimental, not production |
| **Owner** | Brighid Meredith |
| **Scripts** | `scripts/employee_activity/*.py` |

## Description

Lookup table combining weekly activity signals from multiple sources per employee. Each source column is populated independently by its own script. Used for org health scanning, manager previews, and OKR alignment analysis.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_SALESFORCE_USERS | Employee roster (email, name, department, squad) |
| FCT_SALESFORCE_OPPORTUNITIES | SFDC pipeline data (via update_sfdc.py) |
| REP_ACTIVITY_LOG_BY_CONTACT | SFDC pipeline activity (via update_sfdc.py) |
| FCT_SALESFORCE_TASKS | Task activity — calls, emails, to-dos (via update_sfdc_tasks.py) |
| STG_SALESFORCE_EVENTS | Meeting/demo events (via update_sfdc_tasks.py) |
| GONG_CALLS_AI_ANALYSIS | Gong call data (via update_gong.py) |
| GONG_OPPORTUNITY_CALLS_AI_ANALYSIS | Gong opp-call linkage (via update_gong.py) |
| GitHub API (apolloio org) | PR and commit data (via update_github.py) |

## Key Columns

| Column | Type | Description |
|---|---|---|
| EMAIL | VARCHAR | PK part 1 — employee email or "squad::<name>" for rollups |
| WEEK_OF | DATE | PK part 2 — Monday of the covered week |
| FULL_NAME | VARCHAR | Employee display name |
| SQUAD | VARCHAR | Team/squad from DIM_SALESFORCE_USERS.DEPARTMENT |
| DEPARTMENT | VARCHAR | Department |
| IS_SQUAD_ROLLUP | BOOLEAN | TRUE for squad-level aggregate rows |
| JIRA_SUMMARY | VARCHAR | Top tickets, status changes |
| GONG_SUMMARY | VARCHAR | Call count, accounts discussed, next steps |
| SLACK_SIGNALS | VARCHAR | Blockers, escalations, key threads |
| SFDC_PIPELINE | VARCHAR | SQOs, closed won, ARR delta |
| SFDC_TASKS | VARCHAR | Calls, emails, meetings from SFDC tasks/events |
| GITHUB_SUMMARY | VARCHAR | PRs merged/open, repos active |
| SQUAD_SUMMARY | VARCHAR | Squad rollup narrative (LLM-generated) |
| NOTION_SUMMARY | VARCHAR | Notion page activity summary |
| DATA_SOURCES | VARCHAR | Comma-separated list of populated sources |
| UPDATED_AT | TIMESTAMP | Last update timestamp |

## Gotchas

- **Playground table** — not production, no SLA, no automated refresh
- **Department gaps** — ~158 employees show "Unknown" department (DIM_SALESFORCE_USERS needs Darwinbox mapping)
- **GitHub login mapping** — ~12 GitHub logins couldn't be resolved to emails; those are skipped
- **Jira + Slack** — require API tokens in `.env`; currently unpopulated
- **Squad rollup** — requires all source columns populated first; LLM-synthesized
