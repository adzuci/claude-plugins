# USER_INBOUND_ACTIONS_DAILY

> Daily user-level inbound feature actions. One row per user per action per event date.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_INBOUND_ACTIONS_DAILY` |
| **Grain** | One row per (user × action × event_date) |
| **Refresh cadence** | Daily |
| **Trust level** | High — ANALYTICS_DATASCIENCE schema |
| **Owner** | Data Science |

## Description

User-level daily actions for all inbound product features. Used for activation analysis, WAU/WAT computation, and funnel metrics. Pairs with `DIM_USERS_DAILY` for segment filters (paid/free, team attributes).

## Key Columns

| Column | Type | Description |
|---|---|---|
| APOLLO_USER_ID | TEXT | User identifier |
| APOLLO_TEAM_ID | TEXT | Team identifier |
| EVENT_DATE | DATE | Date the action occurred |
| ACTION | TEXT | Specific inbound action taken — see values below |

## Verified `action` Values

| Action | What it means |
|--------|---------------|
| `website_visitors_filter_applied_in_search` | User applied a website visitor filter in people search |
| `website_visitors_tracking_filter_applied_in_company_search` | User applied visitor tracking filter in company search |
| `website_visitors_on_hover_viewed` | User viewed a website visitor hover card |
| `standalone_form_enriched` | User's standalone form was enriched |
| `inbound_router_form_enriched` | Inbound router form was enriched |
| `inbound_router_published` | User published an inbound router |
| `meeting_booked_for_a_guest_via_apollo_scheduler_inbound_router` | Guest booked a meeting via Apollo scheduler/router |
| `meeting_booked_for_a_host_via_apollo_scheduler_inbound_router` | Host meeting booked via Apollo scheduler/router |

## Common Query Patterns

```sql
-- Rolling 7-day WAU/WAT by action type (paid + free)
use warehouse elt_wh_dp;

select
    date
    , date_trunc(week, date) = date_trunc(week, current_date) as is_current_week
    , case when is_paid_ind = 1 then 'Paid' when is_paid_ind = 0 then 'Free' else null end as user_type
    , count(distinct case when a.apollo_user_id is not null then u.apollo_user_id end) as overall_inbound_wau
    , count(distinct case when a.apollo_user_id is not null then u.apollo_team_id end) as overall_inbound_wat
    , count(distinct case when a.action = 'website_visitors_filter_applied_in_search' then u.apollo_user_id end) as visitor_search_wau
    , count(distinct case when a.action = 'inbound_router_published' then u.apollo_team_id end) as router_published_wat
from analytics_db.analytics_datascience.dim_users_daily u
left join analytics_db.analytics_datascience.user_inbound_actions_daily a
    on u.apollo_user_id = a.apollo_user_id
    and u.date between a.event_date and a.event_date + 6
where u.date >= current_date - 180
group by all;

-- F7D activation rate for paid teams (cohort-based)
-- See domain/sql_patterns.md — "Feature Activation Rate — Cohort-based (F7D)"
```

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_USERS_DAILY` | Join on `apollo_user_id` + rolling date window for WAU/WAT |
| `USER_DIALER_ACTIONS_DAILY` | Sibling table for dialer actions |
| `USER_SEQUENCE_ACTIONS_DAILY` | Sibling table for sequence actions |
| `USER_AI_ASSISTANT_DAILY` | Sibling table for AI assistant actions |

## Known Issues & Gotchas

- **Column is `ACTION`, not `ACTION_TYPE`** — `ACTION_TYPE` does not exist. Queries using the wrong name will error silently or fail.
- **`APOLLO_TEAM_ID` is native on this table** — no join to `DIM_USERS` or `DIM_USERS_DAILY` needed for team-level aggregations. Join only when you need paid/free or segment filters.
- **Rolling WAU join pattern**: join `dim_users_daily.date BETWEEN event_date AND event_date + 6` — do NOT join on `date = event_date` alone or you'll get daily counts, not 7-day rolling.
- **No team segment pre-joined** — join to `DIM_USERS_DAILY` (or `DIM_TEAMS_DAILY`) for paid/free and segment filters.
- **`has_in_app_onboarding_goal_inbound_solution` is on `DIM_USERS` (static)**, not `DIM_USERS_DAILY`. For F7D activation cohorts use `DIM_USERS` directly — joining the daily table inflates cohort size.

## Mar 2026 Funnel Benchmarks

As of week of Mar 9, 2026 (use as baselines):

| Metric | Value |
|---|---|
| WAT (any inbound action, week of Mar 9) | 6,257 teams — peak since launch |
| Total interest pool (DIM_USERS survey goal) | 374,301 users (355,782 free, 18,519 paid) |
| Paid F7D activation rate | 14–16% (stable) |
| Free F7D activation rate | 1.86% (recovering from 1.65% trough Mar 2; peak was 2.94% Jan 26) |

**Top actions by unique teams (last 4 weeks, Mar 2026):**

| Action | Teams |
|---|---|
| website_visitors_filter_applied_in_search | 12,580 |
| website_visitors_on_hover_viewed | 5,327 |
| standalone_form_enriched | 230 |
| meeting_booked_for_a_guest_via_apollo_scheduler_inbound_router | 148 |
| inbound_router_published | 101 |
| website_visitors_tracking_filter_applied_in_company_search | 84 |
| inbound_router_form_enriched | 53 |
| meeting_booked_for_a_host_via_apollo_scheduler_inbound_router | 33 |

**Funnel gap:** Discovery (12,580) → Form enrichment (230, 1.8%) → Router live (101, 0.8%). Big wall between viewing visitor cards and taking action.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created — all 8 verified action types, rolling WAU pattern, F7D activation pattern | Leo (via Claude, verified from queries) |
| 2026-03-21 | Added schema gotchas (ACTION not ACTION_TYPE, APOLLO_TEAM_ID native), Mar 2026 funnel benchmarks | Leo (via Claude) |
