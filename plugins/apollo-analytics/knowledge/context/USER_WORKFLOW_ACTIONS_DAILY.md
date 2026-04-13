# USER_WORKFLOW_ACTIONS_DAILY

> Daily user-level workflow actions. One row per user per action per event date.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_WORKFLOW_ACTIONS_DAILY` |
| **Grain** | One row per (user × action × event_date) |
| **Row count** | <!-- TODO: query row count --> |
| **Refresh cadence** | Daily |
| **Trust level** | High — ANALYTICS_DATASCIENCE schema |
| **Owner** | Data Science |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

User-level daily actions for workflow (Plays) features. Sibling to `USER_INBOUND_ACTIONS_DAILY`, `USER_DIALER_ACTIONS_DAILY`, `USER_SEQUENCE_ACTIONS_DAILY`. Used for workflow WAU/WAT, activation analysis, and funnel metrics. Simpler schema than the sequence sibling — no boolean category flags, just the core action column.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| APOLLO_USER_ID | TEXT | User identifier (ZP User ID) | |
| APOLLO_TEAM_ID | TEXT | Team identifier (ZP Team ID) | |
| EVENT_DATE | DATE | Date the action occurred | Amplitude-adjusted UTC timestamp |
| ACTION | TEXT | Specific workflow action taken | <!-- TODO: enumerate distinct values --> |
| EVENT_COUNTS | NUMBER | Count of events for this user × date × action | Pre-aggregated |
| USER_EVENT_DATE_ACTION_KEY | TEXT | Surrogate unique key (user + date + action) | Can use as primary key |

## Common Query Patterns

```sql
-- Rolling 7-day workflow WAU/WAT (paid teams)
SELECT
    date,
    COUNT(DISTINCT CASE WHEN a.apollo_user_id IS NOT NULL THEN u.apollo_user_id END) AS workflow_wau,
    COUNT(DISTINCT CASE WHEN a.apollo_user_id IS NOT NULL THEN u.apollo_team_id END) AS workflow_wat
FROM analytics_db.analytics_datascience.dim_users_daily u
LEFT JOIN analytics_db.analytics_datascience.user_workflow_actions_daily a
    ON u.apollo_user_id = a.apollo_user_id
    AND u.date BETWEEN a.event_date AND a.event_date + 6
WHERE u.date >= CURRENT_DATE - 90
    AND u.is_paid_ind = 1
GROUP BY 1
ORDER BY 1;
```

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_USERS_DAILY` | Join on `apollo_user_id` + rolling date window for WAU/WAT |
| `USER_INBOUND_ACTIONS_DAILY` | Sibling — inbound actions |
| `USER_DIALER_ACTIONS_DAILY` | Sibling — dialer actions |
| `USER_SEQUENCE_ACTIONS_DAILY` | Sibling — sequence actions |

## Known Issues & Gotchas

- **Rolling WAU join pattern**: join `dim_users_daily.date BETWEEN event_date AND event_date + 6` — same as all `user_*_actions_daily` siblings.
- **No boolean category flags** — unlike `USER_SEQUENCE_ACTIONS_DAILY`, this table has no IS_*_ACTION columns. Filter on ACTION text values directly.
- **ACTION values not yet enumerated** — run `SELECT DISTINCT ACTION, COUNT(*) FROM ... GROUP BY 1 ORDER BY 2 DESC` to discover.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
