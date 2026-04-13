# GITHUB_DEVELOPER_TEAMS

> Engineering team membership mapping from GitHub. Maps developers to teams.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GITHUB_DEVELOPER_TEAMS` |
| **Grain** | One row per developer-team-month mapping |
| **Row count** | ~6.9K (2026-03-06) — small reference table |
| **Refresh cadence** | Daily (external data ingestion) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely part of GitHub data ingestion pipeline. |

## Description

Engineering team mapping table (33 distinct users). Links GitHub usernames to Apollo engineering teams. Used as a join table for engineering metrics dashboards alongside FCT_LEADGENIE_GITHUB_COMMIT_DATA and FCT_GITHUB_PR_TIMELINE.

## Upstream Sources

| Source | Relationship |
|---|---|
| GitHub Teams API | Team membership |
| CODEOWNERS / sourcefile configs | Repository ownership |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| TEAM_NAME | TEXT | 32 | 7,915 | Engineering team name | **Primary join key** to FCT_LEADGENIE_GITHUB_COMMIT_DATA.TEAM |
| JIRA_IMPACTED_TEAM | TEXT | 31 | 4,222 | Jira team mapping | Cross-reference to Jira |
| MEMBER_GITHUB | TEXT | 6 | 334 | GitHub username | Join to PR_AUTHOR |
| IS_EM | BOOLEAN | 6 | 140 | Engineering Manager flag | |
| MONTH | DATE | 5 | 293 | Membership month | Historical team assignments |
| MEMBER_EMAIL | TEXT | 5 | 74 | Developer email | |
| MEMBER_NAME | TEXT | 5 | 74 | Developer name | |
| PRIMARY_TEAM | TEXT | 5 | 70 | Primary team assignment | For devs on multiple teams |

## How It's Used

### Common query patterns
- **Join to commit/PR data**: TEAM_NAME → FCT_LEADGENIE_GITHUB_COMMIT_DATA.TEAM
- **Jira cross-reference**: JIRA_IMPACTED_TEAM for incident/ticket attribution
- **Team headcount**: MEMBER_COUNT by team over time

### Key consumers
- Engineering leadership dashboards
- Looker engineering explores
- DARWINBOX_ACTIVE_ENGG_DATA (HR cross-reference)

## Known Issues & Gotchas

- Small table (~6.9K rows) — no performance concerns
- TEAM_NAME and JIRA_IMPACTED_TEAM dominate usage (dashboard-driven)
- MONTH column allows historical team membership — check for latest month if needed

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
