# FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS

> Daily team audit snapshots from MongoDB. Credit limits, billing period, and plan details.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` |
| **Grain** | One row per team + date (`TEAM_ID` + snapshot date) |
| **Row count** | ~78.9M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model, stg_mongo prefix) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) but being deprecated as credit limit source |
| **Owner** | Data Platform / Brighid (credit pipeline context) |
| **DAG** | `dbt_models_group_1` (dbt job 137019). Source: MongoDB daily_team_audit_reports collection. |

## Description

Daily audit snapshot of team billing/plan state (28 distinct users). Contains credit limits by type, billing period boundaries, plan details. Previously the primary source for credit limits in AGG_TEAM_CREDITS — being replaced by LU_CREDIT_QUOTA (PR #2665).

**Coverage: ALL teams** — includes self-serve, VSB, SMB, mid-market, enterprise, and rep-driven accounts. Despite the "Mongo" name, this table is NOT limited to self-serve or Mongo-only teams. The team relies on this table as a source of truth for multiple reports across all segments. Do NOT claim this table excludes enterprise or rep-driven accounts.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `daily_team_audit_reports` collection | Primary source |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| TEAM_ID | TEXT | 27 | 5,176 | Team ID | **Part of PK.** FK to DIM_MONGO_TEAMS |
| DATE_TIME_STRING | TEXT | 27 | 5,176 | Snapshot datetime as string | Use `date(date_time_string)` to get date |
| BILLING_INTERVAL_MONTHS | NUMBER | 27 | 5,176 | Billing cycle length in months | 1=monthly, 12=annual. Used in ARR: `fee * 12 / billing_interval_months` |
| ADDITIONAL_FEE_BY_SOURCE | VARIANT | 25 | 4,100 | JSON of add-on fees by product | **3 keys: `inbound`, `dialer`, `platform_fee`** — extract as `additional_fee_by_source:"inbound"::number` |
| PRICE_PER_ADDON_UNIFIED_CREDIT | NUMBER | 25 | 3,800 | Price per unified credit | Used to compute addon credit fees |
| PRICE_PER_ADDON_LEAD_CREDIT | NUMBER | 25 | 3,800 | Price per lead credit | |
| PRICE_PER_ADDON_DIRECT_DIAL_CREDIT | NUMBER | 25 | 3,800 | Price per direct dial credit | |
| PRICE_PER_ADDON_EXPORT_CREDIT | NUMBER | 25 | 3,800 | Price per export credit | |
| UNIFIED_CREDITS_LIMITS_BY_SOURCE | VARIANT | 23 | 3,392 | Unified credit limits breakdown | JSON — extract addon credits: `:"addon_credits"::number` |
| DIRECT_DIAL_CREDIT_LIMITS_BY_SOURCE | VARIANT | 23 | 3,326 | Direct dial credit limits | Same pattern |
| EXPORT_CREDIT_LIMITS_BY_SOURCE | VARIANT | 23 | 3,322 | Export credit limits | Same pattern |
| LEAD_CREDIT_LIMITS_BY_SOURCE | VARIANT | 23 | 3,267 | Lead credit limits | Same pattern |
| CREATED_AT_UTC | TIMESTAMP | 23 | 3,113 | Audit report creation | |
| CURRENT_PLAN_SEAT_LIMIT | NUMBER | 23 | 2,630 | Plan seat limit | |
| APOLLO_EDITION | TEXT | 23 | 2,623 | Plan edition | Free/Basic/Professional/Custom |
| PRICING_VARIANT | TEXT | 23 | 2,338 | Pricing variant | |
| ACCOUNT_PAYMENT_TERM | TEXT | 23 | 1,987 | Payment term | Monthly/Annual |
| BILLING_PERIOD_END_UTC | TIMESTAMP | 22 | 4,083 | Billing period end | |
| BILLING_PERIOD_START_UTC | TIMESTAMP | 22 | 3,822 | Billing period start | |
| PRODUCT_ID | TEXT | 22 | 2,954 | Product/plan ID | |

## How It's Used

### Common query patterns

**Inbound / Dialer ARR time series** (primary CBR source for these metrics):
```sql
SELECT
    date(date_time_string) AS dd,
    team_id,
    billing_interval_months,
    additional_fee_by_source:"inbound"::number AS inbound_fee,   -- or "dialer"
    additional_fee_by_source:"platform_fee"::number AS platform_fee,
    -- addon credit fees:
    unified_credits_limits_by_source:"addon_credits"::number * price_per_addon_unified_credit AS unified_addon_credit_fee,
    12 * SUM(inbound_fee / billing_interval_months) AS annual_inbound_arr   -- ARR formula
FROM analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports
WHERE date_time_string >= '2025-11-12'
  AND additional_fee_by_source:"inbound"::number > 0
  AND team_id NOT IN ('68e6fb07946dcf000d2e3516', '620210171b9d04008e2ac0e0')
```

- **Credit limit analysis**: `*_LIMITS_BY_SOURCE` variant columns for credit allocation breakdown
- **Billing period boundaries**: `BILLING_PERIOD_START_UTC` / `BILLING_PERIOD_END_UTC`
- **Plan/edition analysis**: `APOLLO_EDITION`, `PRICING_VARIANT`, `PRODUCT_ID`

### Key consumers
- **CBR dashboard** — Inbound ARR, Dialer ARR (primary source)
- AGG_TEAM_CREDITS DAG (upstream source for credit limits, being deprecated)
- Credit pipeline analysis (Brighid)
- Monetization team

## Known Issues & Gotchas

- **Being deprecated as credit limit source** — PR #2665 removed this as the source for AGG_TEAM_CREDITS credit limits, replacing with LU_CREDIT_QUOTA which is more accurate
- **Billing period anchor problem**: Teams can remain anchored to expired billing periods, missing current grants
- **`*_LIMITS_BY_SOURCE` and `ADDITIONAL_FEE_BY_SOURCE` are VARIANT columns** — use `:"key"::type` syntax to extract, not dot notation
- **`ADDITIONAL_FEE_BY_SOURCE` only has 3 keys**: `inbound`, `dialer`, `platform_fee` (verified 2026-03-20). Two key-set shapes exist: `["dialer","inbound","platform_fee"]` (majority) and `["inbound","platform_fee"]`.
- **Date column is a string**: use `date(date_time_string)` not `date_time_string::date` — both work but the former is more common in existing queries. **`DS` is NOT a valid column name here** — this is a common mistake when joining with other tables.
- **`APOLLO_TEAM_ID` is NOT a column here** — the team ID column is `TEAM_ID`. Do not use `APOLLO_TEAM_ID`.
- ~78.9M rows — always filter by `date_time_string >=`
- **Inbound/Dialer ARE populated (verified 2026-03-23)**: Last 90 days — inbound > 0 in 32,170 rows (~0.19%), dialer > 0 in 16,513 rows, platform_fee > 0 in 73,850 rows. Values cluster at $149, $447, $894, $1,428 (multiples of $149 — seat-based pricing tiers). If you see 0% for these addons, check column names first.

## Slack Context

- PR #2665 removed dependency on this table for credit limits in AGG_TEAM_CREDITS
- Known data integrity issues with credit limit reporting from this source

## Business Terms

| Term | Definition |
|---|---|
| Billing Period | The current subscription cycle dates for a team |
| Credit Limits By Source | JSON breakdown of credit allocations by source (plan, promo, addon) |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
| 2026-03-20 | Added ADDITIONAL_FEE_BY_SOURCE, DATE_TIME_STRING, BILLING_INTERVAL_MONTHS, PRICE_PER_ADDON_* columns; added Inbound/Dialer ARR usage pattern; confirmed 3 keys in ADDITIONAL_FEE_BY_SOURCE | Leo |
| 2026-03-23 | Confirmed inbound/dialer ARE populated (32K and 16K non-zero rows last 90d). Added column name gotchas: date col = DATE_TIME_STRING (not DS), team col = TEAM_ID (not APOLLO_TEAM_ID). | Leo |
