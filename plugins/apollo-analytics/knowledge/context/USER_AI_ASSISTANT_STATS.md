# USER_AI_ASSISTANT_STATS

> User-level lifetime AI Assistant stats for segmentation and lifecycle analysis. One row per user, all-time aggregation.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_STATS` |
| **Grain** | One row per apollo_user_id |
| **Row count** | ~384K (2026-04-02) |
| **Refresh cadence** | Daily |
| **Trust level** | Authoritative (DS-owned, part of AI platform model hierarchy) |
| **Owner** | Data Science (Sai Sarvepalli) |
| **DAG** | dbt model: `models/marts/data_science/ai_platform/user_ai_assistant_stats.sql` |

## Description

Lifetime aggregation of AI Assistant activity per user. Complements `USER_AI_ASSISTANT_DAILY` (the time-series table) with a single-row snapshot useful for user segmentation, cohort building, and lifecycle analysis. Use for "all users who have ever used AI Assistant" style queries without needing to aggregate the daily table.

## Upstream Sources

| Source | Relationship |
|---|---|
| `USER_AI_ASSISTANT_DAILY` | Aggregated to lifetime stats per user |
| `FCT_AI_ASSISTANT_THREADS` | May also be used directly for thread-level lifetime aggregation |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| APOLLO_USER_ID | TEXT (PK) | User identifier | |
| TEAM_ID_CURRENT | TEXT | User's current team | Point-in-time — may differ from team at first use |
| FIRST_ACTIVE_DATE | DATE | First date user had an active thread | |
| LAST_ACTIVE_DATE | DATE | Most recent active thread date | |
| TOTAL_THREADS_LIFETIME | NUMBER | All threads ever | Includes proactive/non-engaged |
| TOTAL_SUCCESSFUL_THREADS_LIFETIME | NUMBER | Threads with outcome = success | |
| LIFETIME_SUCCESS_RATE | FLOAT | successful / total (engaged) threads | |

## How It's Used

### Common query patterns
```sql
-- Users who churned AI Assistant (active >30 days ago, not since)
SELECT * FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_STATS
WHERE LAST_ACTIVE_DATE < CURRENT_DATE - 30
  AND LAST_ACTIVE_DATE >= CURRENT_DATE - 90;

-- Power users (high thread volume, high success rate)
SELECT * FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_STATS
WHERE TOTAL_THREADS_LIFETIME >= 50 AND LIFETIME_SUCCESS_RATE >= 0.7;
```

### Key consumers
- AI adoption and segmentation analysis
- User lifecycle / churn analysis
- Cohort seeding for retention experiments

## Known Issues & Gotchas

- `TEAM_ID_CURRENT` is a point-in-time field — for historical team membership, join to `USER_AI_ASSISTANT_DAILY` or `DIM_USERS`
- For time-series retention analysis, use `USER_AI_ASSISTANT_DAILY` instead

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Created context file from Notion AI Assistant Analytics Data Models doc | Sai (via Jarvis) |
