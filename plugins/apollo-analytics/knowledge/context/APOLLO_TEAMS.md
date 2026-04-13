# APOLLO_TEAMS

> **Looker-only surface layer for the Account360 initiative. Do not use for ad-hoc Snowflake analysis — query the upstream source tables directly instead. Only reference this table if the user is explicitly asking about the Account360 Looker explore.**

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.APOLLO_TEAMS` / `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.APOLLO_TEAMS` |
| **Grain** | One row per team (`apollo_team_id`) — current state snapshot, no date column |
| **Unique key** | `apollo_team_id` (dbt-tested: unique + not_null) |
| **Refresh cadence** | dbt-managed (`dual_schema` tag — materializes in both schemas daily) |
| **Trust level** | High for Looker use; **do not query directly for analytics** |
| **Owner** | Analytics (dbt `apollo_core_entities` mart) |
| **dbt model** | `dbt_apollo/models/marts/apollo_core_entities/apollo_teams.sql` |
| **dbt tags** | `apollo_teams`, `core_entities`, `gold`, `looker`, `dual_schema` |

## What this table is

A pre-joined wide team profile built specifically for the Account360 Looker explore. It combines 9 upstream sources into a single table to avoid expensive in-explore joins. All metrics are **current-state only** — there is no date column and no historical data. It is refreshed daily by dbt.

The analytics team does not query this table directly in Snowflake. For any analytical question, use the upstream source tables listed below.

## Account360 Looker Explore

**Explore file:** `looker_centralized/explores/revops/account_360_teams.explore.lkml`

**Join structure:**
```
salesforce_accounts (base, 1:many on sfdc_account_id)
  └── apollo_teams (left_outer, 1:many)
        └── apollo_users (left_outer, 1:many on apollo_team_id)
```

The Looker view resolves the table via `{{_user_attributes['dbt_schema']}}` — reads from whichever dbt schema the Looker user is pointed at (prod vs. dev). This is why the table exists in both schemas (`dual_schema` tag).

**Primary use case:** RevOps and GTME account management — viewing teams under a Salesforce account, their plan/health/activity status, and user roster. Includes pre-built quick-start queries (e.g. "Core Accounts owned by GTME").

## Upstream Sources & What to Use Instead

| What you need | Use this table directly |
|---|---|
| Team identity, UTMs, personas, integrations | `DIM_SALESFORCE_APOLLO_TEAMS` |
| Current ARR, GTM motion, churn/start dates | `FCT_MONTHLY_REVENUE` |
| Current seat limits | `FCT_APOLLO_MONTHLY_SEAT_LIMITS` |
| Current plan / edition / trial status | `INT_TEAM_PRODUCT_INFO_CLEANED` |
| Active user counts (L1/L7/L28) | `DIM_USERS_DAILY` |
| HVO attended/booked flags | `ONBOARDING_HIGH_VELOCITY_TEAMS` |
| Support ticket counts | `DIM_SUPPORT_CONVERSATIONS` |
| Activation milestone dates + flags | `TEAM_ACTIVATION` |
| All-time feature activity counts | `TEAM_ACTIVITY_ALL_TIME` |
| Team health score / rating / color | `FCT_ML_PREDICTIONS_PAID_CHURN_12W` (see derived fields section in that file) |

## Key Gotchas

- **Point-in-time snapshot only.** Revenue, seat limits, and product info are current-month. No date column. For trends or history, use the upstream tables.
- **Health score nulls are intentional.** `team_health_score/rating/color` are null for any team where `is_paying = false`.
- **Revenue filter.** `FCT_MONTHLY_REVENUE` is joined with `is_parent_account = false` — child accounts only. Parent-level ARR is excluded.
- **`dual_schema`.** Table exists in both `ANALYTICS` and `ANALYTICS_DATAPLATFORM`. Schema is resolved at query time via Looker user attributes. For direct Snowflake use, prefer `ANALYTICS_DATAPLATFORM`.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial — incorrectly labeled as legacy) | Brighid (via Claude) |
| 2026-03-24 | Rewrote — documented Looker-only purpose, Account360 explore structure, upstream source map, gotchas | Will (via Jarvis) |
