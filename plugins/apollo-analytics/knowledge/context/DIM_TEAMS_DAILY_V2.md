# DIM_TEAMS_DAILY_V2

> Temporary replacement for DIM_TEAMS_DAILY built from DE-owned foundation tables in PLAYGROUND.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.DIM_TEAMS_DAILY_V2` |
| **Grain** | One row per `(team_id, ds)` |
| **Row count** | ~272K (as of 2026-03-18) |
| **Refresh cadence** | Daily (6 AM PT via PLAYGROUND_DAILY_REFRESH task DAG) |
| **Trust level** | Medium — new table, intended as proof-of-concept replacement for DIM_TEAMS_DAILY |
| **Owner** | Analytics (Brighid) |
| **DAG** | `PLAYGROUND_DAILY_REFRESH` → `TASK_REFRESH_DIM_TEAMS_DAILY_V2` (Tier 2, after feature users + revenue + credits) |

## Description

Joins daily feature user counts, revenue, credits, and team attributes into a single wide table with rolling L7/L28 windows. Designed to prove we can fulfill existing `DIM_TEAMS_DAILY` use cases from DE-owned foundation tables, reducing dependence on the DS dbt pipeline.

**Active-teams-only (243K teams):** Unlike DIM_TEAMS_DAILY (13.6M teams), this table only has rows for teams with at least one Amplitude event on a given day. Teams with zero activity have no row. Most analytical queries filter to active or paid teams anyway.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_FEATURE_USERS_DAILY` | Daily distinct user counts per feature (spine) |
| `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY` | ARR, seat_limit, apollo_edition |
| `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDITS_DAILY` | Credit limits and daily usage |
| `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS` | IS_CORE_ACCOUNT, HAS_FREE_EMAIL_DOMAIN_IND (point-in-time) |

## Key Columns

| Column | Type | Description | DIM_TEAMS_DAILY Equivalent |
|---|---|---|---|
| team_id | VARCHAR | Team identifier | APOLLO_TEAM_ID |
| ds | DATE | Calendar date | DATE |
| arr | FLOAT | Annual recurring revenue | ARR |
| is_paid | BOOLEAN | Derived: ARR > 0 | IS_PAID_IND |
| seat_limit | NUMBER | Paid seat limit | PAID_SEAT_LIMIT |
| apollo_edition | VARCHAR | Plan tier | (not in DTD but useful) |
| is_core_account | NUMBER | Core account flag (point-in-time) | IS_CORE_ACCOUNT_IND |
| has_free_email_domain | NUMBER | Free email domain flag (point-in-time) | IS_FREE_EMAIL_DOMAIN_IND |
| active_user_count_l1 | NUMBER | Distinct active users that day | ACTIVE_USER_COUNTS_L1 |
| active_user_count_l7 | NUMBER | Rolling 7-day SUM of daily distinct counts | ACTIVE_USER_COUNTS_L7 |
| active_user_count_l28 | NUMBER | Rolling 28-day SUM of daily distinct counts | ACTIVE_USER_COUNTS_L28 |
| enrichment_api_user_count_l7 | NUMBER | Rolling 7-day enrichment API users | ENRICHMENT_API_USER_COUNTS_L7 |
| meetings_user_count_l7 | NUMBER | Rolling 7-day meetings users | MEETING_BOOKED_USER_COUNTS_L7 |
| crm_record_management_user_count_l7 | NUMBER | Rolling 7-day CRM record mgmt users | CRM_RECORD_MANAGEMENT_USER_COUNTS_L7 |
| win_close_user_count_l7 | NUMBER | Rolling 7-day dialer+conversations users | WIN_CLOSE_DEALS_USER_COUNTS_L7 |
| ai_platform_user_count_l7 | NUMBER | Rolling 7-day AI platform users | AI_PLATFORM_USER_COUNTS_L7 |
| extension_user_count_l7 | NUMBER | Rolling 7-day extension users | (feature-level) |
| sequences_user_count_l7 | NUMBER | Rolling 7-day sequences users | (feature-level) |
| email_user_count_l7 | NUMBER | Rolling 7-day email users | (feature-level) |
| list_building_user_count_l7 | NUMBER | Rolling 7-day list building users | (feature-level) |
| workflows_user_count_l7 | NUMBER | Rolling 7-day workflows users | (feature-level) |
| signals_user_count_l7 | NUMBER | Rolling 7-day signals users | (feature-level) |
| email_credit_limit | NUMBER | Email credit limit for the day | (credit cols) |
| email_credits_used_today | NUMBER | Email credits consumed that day | (credit cols) |
| export_credit_limit | NUMBER | Export credit limit | (credit cols) |
| export_credits_used_today | NUMBER | Export credits consumed that day | (credit cols) |
| mobile_credit_limit | NUMBER | Mobile credit limit | (credit cols) |
| mobile_credits_used_today | NUMBER | Mobile credits consumed that day | (credit cols) |
| unified_credit_limit | NUMBER | Unified credit limit | (credit cols) |
| unified_credits_used_today | NUMBER | Unified credits consumed that day | (credit cols) |

## How It's Used

### Common query patterns
- Drop-in replacement for DIM_TEAMS_DAILY queries that filter to active/paid teams
- Feature adoption trend analysis with rolling windows
- Revenue + usage correlation analysis

### Key consumers
- Analytics team (migration testing from DIM_TEAMS_DAILY)
- Potential future plugin registry source

## Known Issues & Gotchas

- **Active-teams-only:** 243K teams vs DIM_TEAMS_DAILY's 13.6M. Queries that count inactive teams will undercount.
- **L7/L28 overcounting:** Rolling counts SUM daily distinct counts. A user active on 3 of 7 days counts as 3, not 1. This matches what many downstream queries already do.
- **IS_CORE_ACCOUNT / HAS_FREE_EMAIL_DOMAIN:** Point-in-time from DIM_TEAMS, not daily-varying. Stable enough for a temp table but could drift for teams that change status.
- **Validation (2026-03-18):** ARR matches DIM_TEAMS_DAILY exactly for 4/5 sample teams. One team showed $300 ARR difference (likely snapshot timing). Active user counts tend to be equal or higher than DTD due to broader event capture.
- **Not yet included:** COUNT_OF_USERS, FIRST_TEAM_ACTIVE_DATE.
- **Incremental refresh:** Rebuilds last 31 days (to handle L28 lookback). Historical data beyond 31 days is static after initial load.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-18 | Initial creation as DIM_TEAMS_DAILY replacement proof-of-concept | Brighid |
