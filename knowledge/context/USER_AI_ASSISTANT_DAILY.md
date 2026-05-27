# USER_AI_ASSISTANT_DAILY

> Daily user-level aggregation of AI Assistant activity. Downstream of `FCT_AI_ASSISTANT_THREADS`.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY` |
| **Grain** | One row per (user × activity date) |
| **Row count** | ~675,381 |
| **Refresh cadence** | Daily |
| **Trust level** | High — new canonical table |
| **Owner** | Data Science |

## Description

Pre-aggregated daily user-level rollup of AI Assistant usage. Use this for per-user engagement metrics, DAU calculations, or retention cohort analysis when you don't need thread-level detail. Faster than aggregating `FCT_AI_ASSISTANT_THREADS` by user.

## Key Columns

| Column | Type | Description |
|---|---|---|
| APOLLO_USER_ID | TEXT | User identifier |
| USER_CREATED_DATE | DATE | When the user account was created |
| ACTIVITY_DATE | DATE | Date of activity |
| THREADS_CREATED_COUNT | NUMBER | Total threads created on this date |
| INTERACTED_THREADS_COUNT | NUMBER | Threads where user actively engaged (`USER_INTERACTION_FLAG = TRUE`) |
| SUCCESSFUL_THREADS_COUNT | NUMBER | Threads classified as `success` |
| THREADS_WITH_TOOL_CALLS_COUNT | NUMBER | Threads that had at least one tool call |
| HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS | BOOLEAN | True if user had any "active" threads (interaction + tool call) on this date — use as the DAU flag |
| TOTAL_MESSAGES_COUNT | NUMBER | Total messages across all threads |
| USER_MESSAGES_COUNT | NUMBER | User-authored messages |
| ASSISTANT_MESSAGES_COUNT | NUMBER | Assistant-authored messages |
| DISTINCT_TOOLS_COUNT | NUMBER | Distinct tools used across all threads |
| TOTAL_TOOL_CALLS_COUNT | NUMBER | Total tool calls across all threads |

## Common Query Patterns

```sql
-- Daily Active Users (AI Assistant) — last 90 days
SELECT ACTIVITY_DATE, COUNT(DISTINCT APOLLO_USER_ID) AS dau
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
  AND ACTIVITY_DATE >= CURRENT_DATE - 90
GROUP BY 1 ORDER BY 1;

-- Power users: users active 5+ days in last 30d
SELECT APOLLO_USER_ID, COUNT(*) AS active_days
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
  AND ACTIVITY_DATE >= CURRENT_DATE - 30
GROUP BY 1
HAVING active_days >= 5
ORDER BY 2 DESC;

-- W4 retention check (new way, user-day grain)
-- See FCT_AI_ASSISTANT_THREADS for full cohort retention query
SELECT uad.APOLLO_USER_ID, uad.ACTIVITY_DATE
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY uad
WHERE uad.HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE;
```

## Related Tables

| Table | Relationship |
|---|---|
| `FCT_AI_ASSISTANT_THREADS` | Source — thread-level fact |
| `TEAM_AI_ASSISTANT_DAILY` | Sibling — team-day grain |
| `DIM_USERS` | Join on APOLLO_USER_ID for user attributes |
| `DIM_USERS_DAILY` | Join on APOLLO_USER_ID + ACTIVITY_DATE for login activity |

## Known Issues & Gotchas

- **No team or segment pre-joined** — join to `DIM_USERS` + `DIM_TEAMS_DAILY` for Paid Core filtering
- **`HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS`** is the canonical "user was active today" flag — equivalent to `INTERACTED_THREADS_COUNT > 0 AND THREADS_WITH_TOOL_CALLS_COUNT > 0`
- **For cohort retention** — use `FCT_AI_ASSISTANT_THREADS` directly (has `IS_FIRST_THREAD_EVER`, `THREAD_NUM_LIFETIME`, etc.) or this table + `DIM_USERS_DAILY` for the login denominator

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file | Leo (via Claude) |
