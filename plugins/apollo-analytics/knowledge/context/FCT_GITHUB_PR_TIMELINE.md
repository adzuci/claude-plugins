# FCT_GITHUB_PR_TIMELINE

> GitHub PR lifecycle events. One row per PR event (open, review, approve, merge, deploy).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_GITHUB_PR_TIMELINE` |
| **Grain** | One row per PR event (`EVENT_ID`) |
| **Row count** | ~311K (2026-03-06) — small table |
| **Refresh cadence** | Daily (likely via GitHub data ingestion) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely part of GitHub data ingestion pipeline. |

## Description

PR lifecycle event tracking (29 distinct users). Complements FCT_LEADGENIE_GITHUB_COMMIT_DATA with event-level granularity. Used for DORA metrics (lead time, deploy frequency) and PR review cycle analysis.

## Upstream Sources

| Source | Relationship |
|---|---|
| GitHub Events API | PR events (open, review, approve, merge) |
| Deploy tracking | Deployment events |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| EVENT_TYPE | TEXT | 30 | 1,162 | PR event type | opened/reviewed/approved/merged/deployed |
| EVENT_TIMESTAMP | TIMESTAMP | 30 | 1,156 | When the event occurred | |
| COMMIT_HASH | TEXT | 29 | 415 | Associated commit | FK to FCT_LEADGENIE_GITHUB_COMMIT_DATA |
| ACTOR_LOGIN | TEXT | 4 | 754 | GitHub user who triggered event | |
| PR_ID | TEXT | 4 | 751 | Pull request ID | |
| PR_URL | TEXT | 4 | 738 | PR link | |
| REPOSITORY | TEXT | 3 | 734 | GitHub repository | |

## How It's Used

### Common query patterns
- **DORA metrics**: Time between EVENT_TYPEs (open→approve→merge→deploy)
- **Review cycle analysis**: Time from open to first review
- **Deploy frequency**: Count of deploy events over time

### Key consumers
- Engineering leadership (DORA dashboards)
- Looker engineering explores
- Joined with GITHUB_DEVELOPER_TEAMS and FCT_LEADGENIE_GITHUB_COMMIT_DATA

## Known Issues & Gotchas

- Small table (~311K rows) — no performance concerns
- Top 3 columns (EVENT_TYPE, EVENT_TIMESTAMP, COMMIT_HASH) queried by 29-30 users, rest by only 3-4 — suggests dashboard-driven access
- EVENT_METADATA (variant) available but rarely used

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
