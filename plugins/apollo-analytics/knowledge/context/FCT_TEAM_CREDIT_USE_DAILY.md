# FCT_TEAM_CREDIT_USE_DAILY

> Daily credit usage per team per credit type and feature type — most granular credit table showing which features consumed which credits.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY` |
| **Grain** | One row per team + date + credit type + feature type (`team_id` + `ds` + `credit_type` + `feature_type`) |
| **Row count** | <!-- TODO: query for row count --> |
| **Refresh cadence** | Daily (Snowflake Task: `TASK_REFRESH_FCT_TEAM_CREDIT_USE_DAILY`, chained after `TASK_REFRESH_FCT_TEAM_CREDITS_DAILY`) |
| **Trust level** | Canonical (Playground) — medium trust; depends on AGG_TEAM_CREDITS Airflow DAG |
| **Owner** | Data Engineering (Brighid Meredith) |
| **DAG** | Snowflake Task `PLAYGROUND.TASK_REFRESH_FCT_TEAM_CREDIT_USE_DAILY` with stored procedure `SP_REFRESH_FCT_TEAM_CREDIT_USE_DAILY` |

## Description

The most granular credit usage table. Each row shows credits consumed by a specific feature within a credit type for a team on a given day. For example: team X used 50 unified_lead_credits on searcher_emails on 2026-03-01. This is the companion to `FCT_TEAM_CREDIT_LIMITS_DAILY` (which has limits). Sourced from `AGG_TEAM_CREDITS` usage rows (where `feature_type IS NOT NULL` and `credits_used IS NOT NULL`).

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.PLAYGROUND.AGG_TEAM_CREDITS` | Usage rows only (`feature_type IS NOT NULL AND credits_used IS NOT NULL`) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | TEXT | Apollo team ID | FK to DIM_MONGO_TEAMS.TEAM_ID |
| ds | DATE | Usage date | |
| credit_type | TEXT | Type of credit consumed | See verified values below |
| feature_type | TEXT | Feature that consumed the credits | e.g., searcher_emails, direct_dial, etc. |
| credits_used | NUMBER | Number of credits consumed | |
| billing_period_start | DATE | Start of billing period | **Populated ~40% of rows** |
| billing_period_end | DATE | End of billing period | **Populated ~40% of rows** |
| product_id | TEXT | Product identifier | **Populated ~40% of rows** |

## Verified `credit_type` Values (from Snowflake, 2026-03-20)

| credit_type | Weekly Volume (Mar-02 week) | Trend | Notes |
|-------------|---------------------------|-------|-------|
| `unified_lead_credit` | 107.4M | Growing | Dominant — search/enrichment. ~294–304K teams/week |
| `email_credit` | 6.5M | Growing | Email sends |
| `ai_credit` | 4.7M | Stable | AI features (Power-Up) |
| `export_credit` | 1.8M | Declining | CSV/bulk exports — down ~31% over 4 weeks |
| `direct_dial_credit` | 1.6M | Growing | Direct dial calls |
| `conversation_credit` | 700K | Stable | Conversation intelligence |
| `inbound_website_visitor_credit` | 558K | Stable | Website visitor tracking |

> Note: FY27 AOP credit targets — Waterfall/Enrichment (unified_lead): +402%, AI Power-Up (ai_credit): +151%, Email: +102%

## How It's Used

### Common query patterns
- Credit usage by feature for a team: `SELECT feature_type, SUM(credits_used) ... GROUP BY feature_type`
- Feature-level utilization: join with `FCT_TEAM_CREDIT_LIMITS_DAILY` on `(team_id, ds, credit_type)` and compare `SUM(credits_used)` to `credit_limit`
- Top credit-consuming features across all teams
- Billing period analysis (where billing_period columns are populated)

### Key consumers
- Analytics team (credit consumption analysis by feature)
- Product teams (understanding feature-level credit burn)

## Known Issues & Gotchas

- **NaN filtering:** Source can contain NaN values in `credits_used`. Filtered with `credits_used = credits_used`.
- **Sparse billing columns:** `billing_period_start`, `billing_period_end`, and `product_id` are only populated ~40% of the time. Do not rely on these for complete billing analysis.
- **Medium trust:** Same dependency chain as `FCT_TEAM_CREDIT_LIMITS_DAILY` — depends on `AGG_TEAM_CREDITS` Airflow DAG (6-hour refresh).
- **Task chaining:** Runs after `TASK_REFRESH_FCT_TEAM_CREDITS_DAILY` completes.
- **DQ checks:** Row count, row count regression, duplicate grain, freshness, and feature_type cardinality checks run on each refresh.

## Slack Context

<!-- TODO: search Slack for discussions -->

## Business Terms

| Term | Definition |
|---|---|
| feature_type | The specific product feature that consumed credits (e.g., searcher_emails, direct_dial) |
| credits_used | Number of credits consumed by a feature on a given day |
| billing_period | The billing cycle window (start to end) for credit allocation |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-11 | Created context file | Brighid (via Claude) |
