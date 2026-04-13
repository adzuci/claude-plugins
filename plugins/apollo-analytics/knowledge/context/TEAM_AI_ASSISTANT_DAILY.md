# TEAM_AI_ASSISTANT_DAILY

> Daily team-level aggregation of AI Assistant activity. Downstream of `FCT_AI_ASSISTANT_THREADS`.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_DAILY` |
| **Grain** | One row per (team × activity date) |
| **Row count** | ~596,435 |
| **Refresh cadence** | Daily |
| **Trust level** | High — new canonical table |
| **Owner** | Data Science |

## Description

Pre-aggregated daily team-level rollup of AI Assistant usage. Use this instead of aggregating `FCT_AI_ASSISTANT_THREADS` by team when you need team-day grain — it's significantly faster.

## Key Columns

| Column | Type | Description |
|---|---|---|
| APOLLO_TEAM_ID_DATE_KEY | TEXT (PK) | Surrogate key: team_id + activity_date |
| APOLLO_TEAM_ID | TEXT | Team identifier |
| TEAM_CREATED_DATE | DATE | When the team was created |
| ACTIVITY_DATE | DATE | Date of activity |
| THREADS_CREATED_COUNT | NUMBER | Total threads created on this date |
| INTERACTED_THREADS_COUNT | NUMBER | Threads where user actively engaged (`USER_INTERACTION_FLAG = TRUE`) |
| SUCCESSFUL_THREADS_COUNT | NUMBER | Threads classified as `success` |
| THREADS_WITH_TOOL_CALLS_COUNT | NUMBER | Threads that had at least one tool call |
| HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS | BOOLEAN | True if team had any "active" threads (interaction + tool call) on this date |
| ACTIVE_USERS_COUNT | NUMBER | Distinct users with active threads on this date |
| TOTAL_MESSAGES_COUNT | NUMBER | Total messages across all threads |
| USER_MESSAGES_COUNT | NUMBER | User-authored messages |
| ASSISTANT_MESSAGES_COUNT | NUMBER | Assistant-authored messages |
| DISTINCT_TOOLS_COUNT | NUMBER | Distinct tools used across all threads |
| TOTAL_TOOL_CALLS_COUNT | NUMBER | Total tool calls across all threads |

## Common Query Patterns

```sql
-- Teams using AI Assistant (active) in last 30 days
SELECT APOLLO_TEAM_ID, SUM(ACTIVE_USERS_COUNT) AS total_active_users
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_DAILY
WHERE ACTIVITY_DATE >= CURRENT_DATE - 30
  AND HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
GROUP BY 1
ORDER BY 2 DESC;

-- Daily active AI Assistant users across all teams
SELECT ACTIVITY_DATE, SUM(ACTIVE_USERS_COUNT) AS dau
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_DAILY
WHERE ACTIVITY_DATE >= CURRENT_DATE - 90
GROUP BY 1 ORDER BY 1;
```

## Related Tables

| Table | Relationship |
|---|---|
| `FCT_AI_ASSISTANT_THREADS` | Source — thread-level fact |
| `USER_AI_ASSISTANT_DAILY` | Sibling — user-day grain |
| `DIM_TEAMS_DAILY` | Join on APOLLO_TEAM_ID + ACTIVITY_DATE for team segment filters |

## Known Issues & Gotchas

- **No team segment pre-joined** — join to `DIM_TEAMS_DAILY` for Paid Core / Free / etc. filtering
- **`HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS`** is the "was this team active today" flag — equivalent to `INTERACTED_THREADS_COUNT > 0 AND THREADS_WITH_TOOL_CALLS_COUNT > 0`

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file | Leo (via Claude) |
