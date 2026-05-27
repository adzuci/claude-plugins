# FCT_LEADGENIE_GITHUB_COMMIT_DATA

> GitHub commit and PR data for engineering metrics. One row per commit/PR event.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LEADGENIE_GITHUB_COMMIT_DATA` |
| **Grain** | One row per commit/PR event (`COMMIT_HASH` or `PR_ID` + `RECORD_TYPE`) |
| **Row count** | ~42K (2026-03-06) — small table |
| **Refresh cadence** | Daily (likely via Data Platform ETL) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform / Engineering Analytics |
| **DAG** | Not explicitly found as standalone DAG. Likely part of GitHub data ingestion pipeline. |

## Description

Engineering metrics table (48 distinct users). Tracks commits, PRs, and associated metadata including AI productivity impact scores. Used for engineering velocity dashboards, developer surveys, and AI tooling ROI analysis. Small table but very widely queried.

## Upstream Sources

| Source | Relationship |
|---|---|
| GitHub API | Commits, PRs, reviews |
| Developer survey data | AI impact scores, what_worked_well |
| GITHUB_DEVELOPER_TEAMS | Team mapping |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| PR_AUTHOR | TEXT | 48 | 14,681 | PR author username | |
| OPENED_TS | TIMESTAMP | 47 | 10,899 | PR opened timestamp | |
| COMMIT_TS | TIMESTAMP | 46 | 15,231 | Commit timestamp | |
| RECORD_TYPE | TEXT | 46 | 13,938 | Event type (commit/PR) | |
| LINES_ADDED | NUMBER | 45 | 4,907 | Lines added | |
| LINES_REMOVED | NUMBER | 45 | 4,897 | Lines removed | |
| COMMIT_HASH | TEXT | 45 | 4,589 | Unique commit hash | |
| APPROVERS | ARRAY/TEXT | 45 | 3,852 | PR approvers | |
| COMMENTS_METADATA | VARIANT | 45 | 3,637 | PR comment data | Added by Arnab Chanda (Aug 2025) |
| PR_URL | TEXT | 45 | 2,691 | PR link | |
| DEPLOYED_TS | TIMESTAMP | 44 | 1,868 | Deployment timestamp | |
| PR_ID | TEXT | 28 | 3,268 | Pull request ID | |
| AI_SPEED_BOOST_IMPACT | TEXT/NUMBER | 27 | 761 | AI productivity impact score | Developer survey data |
| AI_IDEATION_HELP_IMPACT | TEXT/NUMBER | 27 | 756 | AI ideation help score | Developer survey data |
| TEAM | TEXT | 27 | 534 | Engineering team name | |
| PR_APPROVED_TS | TIMESTAMP | 26 | 728 | PR approval timestamp | |
| PR_APPROVALS_COUNT | NUMBER | 26 | 606 | Number of approvals | |
| DOCS_HELPFULNESS_SCORE | NUMBER | 26 | 540 | Docs quality score | |
| MERGED_TS | TIMESTAMP | 26 | 535 | PR merge timestamp | |

## How It's Used

### Common query patterns
- **Engineering velocity**: DORA metrics — time from open to merge, deploy frequency
- **AI productivity analysis**: AI_SPEED_BOOST_IMPACT and AI_IDEATION_HELP_IMPACT scores
- **Team-level output**: Commits/PRs per team, lines changed

### Key consumers
- Engineering leadership (velocity dashboards)
- #ai-productivity-metrics channel
- Looker engineering dashboards

## Known Issues & Gotchas

- COMMENTS_METADATA was added later (Aug 2025 by Arnab Chanda) — not available for older records
- Small table (~42K rows) — no performance concerns
- Related tables: GITHUB_DEVELOPER_TEAMS (team mapping), FCT_GITHUB_PR_TIMELINE (PR lifecycle events)

## Slack Context

- **COMMENTS_METADATA addition**: Arnab Chanda requested moving new variant column from sandbox to prod (#ai-productivity-metrics)
- **AI productivity tracking**: Table used for measuring AI tooling impact on engineering velocity

## Business Terms

| Term | Definition |
|---|---|
| DORA Metrics | DevOps Research and Assessment metrics (deploy frequency, lead time, MTTR, change failure rate) |
| AI Speed Boost Impact | Self-reported score of AI tool impact on developer speed |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history + Slack research | Brighid (via Claude) |
