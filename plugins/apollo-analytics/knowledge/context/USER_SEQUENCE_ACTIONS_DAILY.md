# USER_SEQUENCE_ACTIONS_DAILY

> Daily user-level sequence actions. One row per user per action per event date.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_SEQUENCE_ACTIONS_DAILY` |
| **Grain** | One row per (user × action × event_date) |
| **Row count** | <!-- TODO: query row count --> |
| **Refresh cadence** | Daily |
| **Trust level** | High — ANALYTICS_DATASCIENCE schema |
| **Owner** | Data Science |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

User-level daily actions for all sequence features — creation, step management, email sending, contact enrollment, AI usage, deliverability, and tab views. Sibling to `USER_INBOUND_ACTIONS_DAILY`, `USER_DIALER_ACTIONS_DAILY`, `USER_WORKFLOW_ACTIONS_DAILY`. Used for sequence WAU/WAT, activation analysis, and funnel metrics. Includes boolean flags for action categories to simplify filtering.

Reference: [Sequences Data Assets (Notion)](https://www.notion.so/apolloio/Sequences-Data-Assets-1e9ab2b3b49680ae80f6d5d724e2ecd0)

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| APOLLO_USER_ID | TEXT | User identifier (ZP User ID) | |
| APOLLO_TEAM_ID | TEXT | Team identifier (ZP Team ID) | |
| EVENT_DATE | DATE | Date the action occurred | Amplitude-adjusted UTC timestamp |
| ACTION | TEXT | Specific sequence action taken | See Notion doc for full list |
| EVENT_COUNTS | NUMBER | Count of events for this user × date × action | |
| USER_EVENT_DATE_ACTION_KEY | TEXT | Surrogate unique key (user + date + action) | Can use as primary key |
| IS_EMAIL_SENT_ACTION | BOOLEAN | outreach_automatic_email_sent or outreach_manual_email_sent | |
| IS_CONTACT_ADDED_TO_SEQUENCE_ACTION | BOOLEAN | Contact added to a sequence (source agnostic) | |
| IS_AI_ACTION | BOOLEAN | AI-powered actions: power_up_field/signal inserted, dynamic_variable inserted | |
| IS_SEQUENCE_CREATION_ACTION | BOOLEAN | Sequence created (by user or during onboarding) or creation modal viewed | |
| IS_SEQUENCE_STEP_RELATED_ACTION | BOOLEAN | Step CRUD: email/dialer/LinkedIn/task steps created, updated, viewed, deleted | |
| IS_SEQUENCE_TAB_VIEWED_ACTION | BOOLEAN | Activity, analytics, reports, or settings tab viewed | |
| IS_DELIVERABILITY_ACTION | BOOLEAN | Email deliverability-related actions | |

## Common Query Patterns

```sql
-- Rolling 7-day sequence WAU/WAT (paid teams)
SELECT
    date,
    COUNT(DISTINCT CASE WHEN a.apollo_user_id IS NOT NULL THEN u.apollo_user_id END) AS sequence_wau,
    COUNT(DISTINCT CASE WHEN a.apollo_user_id IS NOT NULL THEN u.apollo_team_id END) AS sequence_wat
FROM analytics_db.analytics_datascience.dim_users_daily u
LEFT JOIN analytics_db.analytics_datascience.user_sequence_actions_daily a
    ON u.apollo_user_id = a.apollo_user_id
    AND u.date BETWEEN a.event_date AND a.event_date + 6
WHERE u.date >= CURRENT_DATE - 90
    AND u.is_paid_ind = 1
GROUP BY 1
ORDER BY 1;

-- AI action adoption within sequences
SELECT
    EVENT_DATE,
    COUNT(DISTINCT APOLLO_USER_ID) AS ai_sequence_users,
    SUM(EVENT_COUNTS) AS ai_events
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_SEQUENCE_ACTIONS_DAILY
WHERE IS_AI_ACTION = TRUE
    AND EVENT_DATE >= CURRENT_DATE - 30
GROUP BY 1
ORDER BY 1;
```

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_USERS_DAILY` | Join on `apollo_user_id` + rolling date window for WAU/WAT |
| `SEQUENCES` | Sequence-level email metrics (sent, delivered, opened, replied) |
| `FCT_MONGO_EMAILER_MESSAGES` | Message-level email activity |
| `USER_INBOUND_ACTIONS_DAILY` | Sibling — inbound actions |
| `USER_DIALER_ACTIONS_DAILY` | Sibling — dialer actions |
| `USER_WORKFLOW_ACTIONS_DAILY` | Sibling — workflow actions |

## Known Issues & Gotchas

- **Rolling WAU join pattern**: join `dim_users_daily.date BETWEEN event_date AND event_date + 6` — same as all `user_*_actions_daily` siblings. Do NOT join on `date = event_date` alone.
- **EVENT_COUNTS is pre-aggregated** — already a unique count per user × date × action. Use SUM(EVENT_COUNTS) for total events, COUNT(DISTINCT APOLLO_USER_ID) for unique users.
- **Boolean flags are additive** — an action can match multiple flags (e.g., an AI email send could be both IS_AI_ACTION and IS_EMAIL_SENT_ACTION). Don't assume mutual exclusivity.
- **EVENT_DATE is Amplitude-adjusted UTC** — not raw client time. See column comment for formula.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
