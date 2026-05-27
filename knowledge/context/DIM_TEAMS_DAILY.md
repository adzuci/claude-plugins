# DIM_TEAMS_DAILY

> Daily snapshot of team-level metrics. One row per team per day.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY` |
| **Grain** | One row per team + date (`APOLLO_TEAM_ID` + `DATE`) |
| **Row count** | ~8.5B (2026-03-06) — very large table, use date filters |
| **Refresh cadence** | Daily incremental (owned by Data Science). Has view variant: `DIM_TEAMS_DAILY_VW` |
| **Trust level** | Use with caution (ANALYTICS_DATASCIENCE — DS-maintained) |
| **Owner** | Data Science (Shyam SK) |
| **DAG** | Not found in airflow-dags. Likely a dbt model in DS project. Built incrementally. |

## Description

Daily team snapshot (47 distinct users). Contains daily ARR, user activity counts (L1/L7/L28), feature-level engagement metrics, and activation flags. The primary table for time-series team-level product analytics. Extremely large — always filter by DATE.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_TEAMS | Team attributes (one-time fields, 400+ cols) |
| Amplitude/Mongo event tables | Daily activity rollups per team (feature counts by L1/L7/L28 windows) |

## dbt Model Details (from dbt_apollo)

DIM_TEAMS_DAILY is upstream of DIM_ACTIVE_TEAMS_DAILY. The relationship:

```
DIM_TEAMS_DAILY (all teams × all dates, 8.5B rows)
  → DIM_ACTIVE_TEAMS_DAILY (filtered to teams with usage, adds boolean flags + window "ever" aggregates)
```

DIM_ACTIVE_TEAMS_DAILY (`dbt_apollo/models/marts/data_science/dim_active_teams_daily.sql`):
- Materialized: TABLE, unique key `unique_id` (activity_date + apollo_team_id)
- Clustered by: `activity_date`
- Warehouse: `dbt_large_warehouse`, tagged `looker`
- Joins: `dim_teams_daily` + `stg_salesforce__apollo_team` (for team_created_date)
- Transforms counts into boolean flags: `count > 0 → has_*_team_usage_l1`
- Window functions: `boolor_agg()` for "ever" flags, `min(iff(...))` for first usage dates

## Query History Insight (2026-03-09)

**DIM_TEAMS_DAILY (40K queries, 59 users) massively outperforms DIM_ACTIVE_TEAMS_DAILY (1.3K queries, 20 users).**

People prefer DIM_TEAMS_DAILY because it has pre-computed boolean indicators (`is_core_account_ind`, `is_paid_ind`, `is_free_email_domain_ind`) that eliminate the 3-table SFDC join. The Paid Core / Free Core / Paid Non-Core / Free Non-Core CASE statement is repeated in nearly every query.

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| DATE | DATE | 47 | 17,203 | Snapshot date | **Part of PK.** Always filter on this. |
| APOLLO_TEAM_ID | TEXT | 47 | 17,191 | Team ID | **Part of PK.** FK to DIM_TEAMS, DIM_MONGO_TEAMS |
| ARR | NUMBER | 38 | 6,385 | ARR as of that date | Daily snapshot of revenue |
| IS_PAID_IND | BOOLEAN | 31 | 8,021 | Paid team flag | |
| ACTIVE_USER_COUNTS_L1 | NUMBER | 31 | 4,803 | Active users last 1 day | |
| PAID_SEAT_LIMIT | NUMBER | 31 | 4,007 | Seat limit | |
| ACTIVE_USER_COUNTS_L7 | NUMBER | 29 | 6,485 | Active users last 7 days | Key engagement metric |
| ACTIVE_USER_COUNTS_L28 | NUMBER | 29 | 3,939 | Active users last 28 days | |
| COUNT_OF_USERS | NUMBER | 29 | 3,542 | Total users on team | |
| ENRICHMENT_API_USER_COUNTS_L7 | NUMBER | 28 | 4,681 | Enrichment API active users (7d) | Feature-level engagement |
| ENRICHMENT_WATERFALL_USER_COUNTS_L1 | NUMBER | — | — | Waterfall enrichment active users (1d) | L1 only in DIM_TEAMS_DAILY; use DIM_ACTIVE_TEAMS_DAILY for L7/L28 |
| HAS_ENRICHMENT_WATERFALL_TEAM_USAGE_L1 | BOOLEAN | — | — | Team has 1+ users with waterfall usage today | Boolean flag |
| ENRICHMENT_CSV_USER_COUNTS_L1 | NUMBER | — | — | CSV enrichment active users (1d) | |
| ENRICHMENT_CRM_LIVING_DATA_USER_COUNTS_L1 | NUMBER | — | — | CRM living data enrichment active users (1d) | |
| MEETING_BOOKED_USER_COUNTS_L7 | NUMBER | 28 | 3,366 | Meeting feature users (7d) | |
| FIRST_TEAM_ACTIVE_DATE | DATE | 27 | 5,619 | First activity date | |
| CRM_RECORD_MANAGEMENT_USER_COUNTS_L7 | NUMBER | 27 | 4,584 | CRM feature users (7d) | |
| WIN_CLOSE_DEALS_USER_COUNTS_L7 | NUMBER | 27 | 4,523 | Win/Close feature users (7d) | |
| IS_CORE_ACCOUNT_IND | BOOLEAN | 26 | 7,174 | Core account flag | |
| IS_FREE_EMAIL_DOMAIN_IND | BOOLEAN | 26 | 5,732 | Free email domain flag | |
| AI_PLATFORM_USER_COUNTS_L7 | NUMBER | 26 | 3,865 | AI platform active users (7d) | |

## How It's Used

### Common query patterns
- **Time-series team metrics**: ARR trends, activation curves, retention cohorts
- **Feature engagement tracking**: L1/L7/L28 activity counts by feature (enrichment, CRM, meetings, AI)
- **Cortex Analyst / Databot**: Being used with DIM_TEAMS to train Snowflake Databot

### Key consumers
- Data Science team (primary)
- Product Analytics (feature adoption tracking)
- Looker dashboards (via DIM_TEAMS_DAILY_VW)

## Known Issues & Gotchas

- **Coverage vs FCT_DAILY_REVENUE**: DIM_TEAMS_DAILY covers ~111K teams ($207M ARR) vs ~217K teams ($415M ARR) in FCT_DAILY_REVENUE. The gap is SFDC-billed enterprise and rep-driven accounts not tracked in Mongo. **However**, FCT_DAILY_REVENUE requires `IS_PARENT_ACCOUNT = FALSE` for correct ARR sums — without that filter it double-counts via parent-account rollup rows. The coverage gap is real but the magnitude depends on proper filtering of FCT_DAILY_REVENUE. Do not present this as a blanket indictment of DIM_TEAMS_DAILY without noting the filter requirement on the alternative.
- **Extremely large** (~8.5B rows) — ALWAYS filter by DATE range
- **Bug found**: Interest columns for genpipe nextgen & genpipe traditional were underreported (15% for traditional, 34% for nextgen). Fix was deployed by Shyam SK (#rnd-all)
- **Refresh fragility**: Pubudu reported the table not refreshing (stale at Jan 11 date) — monitor for freshness
- **Incremental build**: Backfill required if schema changes need to apply to historical records (per Karun Kumar)
- Some columns are aggregates of other columns (per Kirk Hlavka) — be careful double-counting

## Slack Context

- **Genpipe interest bug**: 15% under-reporting for traditional, 34% for nextgen — fix deployed (Shyam SK, #rnd-all)
- **Refresh outage**: Max date stuck at Jan 11 flagged by Pubudu (#dept-analytics)
- **Cortex Analyst training**: Shyam collecting sample queries from team for Databot (#product-analytics-team)
- **Schema changes require backfill**: Confirmed by Karun Kumar — incremental build means changes don't apply retroactively (#dataplatform-analytics-dev)

## WAT Definition — Source of Truth

**DIM_TEAMS_DAILY and DIM_ACTIVE_TEAMS_DAILY are the canonical SoT for WAT and all standard usage reporting.** They are the Snowflake translation of the metrics DB. Always use them for feature WAT; never proxy WAT from credit or transactional tables.

- **DIM_TEAMS_DAILY**: has L1 (daily) enrichment sub-type columns + boolean flags. Use for daily snapshots.
- **DIM_ACTIVE_TEAMS_DAILY**: has full L1/L7/L28 rolling windows + INTEREST variants. **Use this for WAT (L7).**

**Waterfall WAT** = `COUNT(DISTINCT apollo_team_id) WHERE ENRICHMENT_WATERFALL_USER_COUNTS_L7 > 0` from `DIM_ACTIVE_TEAMS_DAILY`

Four enrichment sub-types tracked:
- `ENRICHMENT_API` — API enrichment
- `ENRICHMENT_WATERFALL` — Waterfall enrichment ← canonical Waterfall WAT source
- `ENRICHMENT_CSV` — CSV enrichment
- `ENRICHMENT_CRM_LIVING_DATA` — CRM living data enrichment

If the debrief or any analysis uses credit tables (AGG_TEAM_CREDITS, FCT_TEAM_CREDIT_USE_DAILY) to count waterfall teams — that is a **proxy**, not WAT. Flag it as such.

## Business Terms

| Term | Definition |
|---|---|
| WAT | Weekly Active Teams — canonical source is DIM_ACTIVE_TEAMS_DAILY (*_USER_COUNTS_L7 > 0) |
| Waterfall WAT | Teams with ENRICHMENT_WATERFALL_USER_COUNTS_L7 > 0 in DIM_ACTIVE_TEAMS_DAILY |
| L1/L7/L28 | Lookback windows: 1 day, 7 days, 28 days |
| Multi-product Activation | Team using 2+ Apollo product features |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history + Slack research | Brighid (via Claude) |
| 2026-03-09 | Added dbt model details, DIM_ACTIVE_TEAMS_DAILY relationship, query history insight (40K vs 1.3K queries) | Brighid (via Claude) |
