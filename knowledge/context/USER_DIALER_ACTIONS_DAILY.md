# USER_DIALER_ACTIONS_DAILY

> Daily user-level dialer actions. One row per user per action per event date.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_DIALER_ACTIONS_DAILY` |
| **Grain** | One row per (user × action × event_date) |
| **Refresh cadence** | Daily |
| **Trust level** | High — ANALYTICS_DATASCIENCE schema |
| **Owner** | Data Science |

## Description

User-level daily actions for dialer features (parallel dialer, one-off dialer). Sibling to `USER_INBOUND_ACTIONS_DAILY`, `USER_SEQUENCE_ACTIONS_DAILY`, `USER_WORKFLOW_ACTIONS_DAILY`. Used for dialer WAU/WAT, activation analysis, and the FY27 R&D Performance Dashboard.

## Key Columns

| Column | Type | Description |
|---|---|---|
| APOLLO_USER_ID | TEXT | User identifier |
| APOLLO_TEAM_ID | TEXT | Team identifier |
| EVENT_DATE | DATE | Date the action occurred |
| ACTION | TEXT | Specific dialer action — see below |

## Verified `action` Values (from Snowflake, 2026-03-20)

| Action | Count | Description |
|--------|-------|-------------|
| `call_dialed_via_one_off_dialer` | 1,019,358 | Standard one-off dialer call placed |
| `call_dialed_via_parallel_dialer` | 65,469 | Parallel dialer call placed |
| `dialed_csat_great_rating_received` | 4,286 | Post-call CSAT — great rating |
| `dialed_csat_poor_rating_received` | 3,636 | Post-call CSAT — poor rating |
| `dialed_csat_average_rating_received` | 2,215 | Post-call CSAT — average rating |
| `call_joined` | 962 | User joined a call (conference/warm transfer) |

One-off dialer dominates (~94% of volume). Parallel dialer is ~6% — consistent with it being an add-on.

## Common Query Patterns

```sql
-- Rolling 7-day dialer WAU/WAT (paid teams)
use warehouse elt_wh_dp;

select
    date
    , count(distinct case when a.apollo_user_id is not null then u.apollo_user_id end) as dialer_wau
    , count(distinct case when a.apollo_user_id is not null then u.apollo_team_id end) as dialer_wat
from analytics_db.analytics_datascience.dim_users_daily u
left join analytics_db.analytics_datascience.user_dialer_actions_daily a
    on u.apollo_user_id = a.apollo_user_id
    and u.date between a.event_date and a.event_date + 6
where u.date >= current_date - 90
    and u.is_paid_ind = 1
group by 1
order by 1;
```

**Note:** Use the same rolling join pattern as `USER_INBOUND_ACTIONS_DAILY` — `dim_users_daily.date BETWEEN event_date AND event_date + 6`.

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_USERS_DAILY` | Join on `apollo_user_id` + rolling date window for WAU/WAT |
| `USER_INBOUND_ACTIONS_DAILY` | Sibling — inbound actions |
| `USER_SEQUENCE_ACTIONS_DAILY` | Sibling — sequence actions |
| `USER_WORKFLOW_ACTIONS_DAILY` | Sibling — workflow actions |
| `USER_DISCOVERY_ACTIONS_DAILY` | Sibling — discovery/recommendations actions |
| `FCT_TEAM_PHONE_CALLS_DAILY` | Team-level daily call aggregation (complement) |
| `FCT_MONGO_PHONE_CALLS` | Source — call-level, used for connect rate (twilio_call_sid present) |

## Known Issues & Gotchas

- **Rolling WAU join pattern**: join `dim_users_daily.date BETWEEN event_date AND event_date + 6` — same pattern as all `user_*_actions_daily` siblings.
- **Action values not yet enumerated** — add them when discovered.
- Table available from 2025-05-01 based on FY27 R&D dashboard query scope.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created — all 6 verified action values from Snowflake, volume context | Leo (via Claude) |
