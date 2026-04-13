# FCT_TEAM_CREDIT_LIMITS_DAILY

> Daily credit limits per team per credit type — normalized view of credit allocations from AGG_TEAM_CREDITS.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_LIMITS_DAILY` |
| **Grain** | One row per team + date + credit type (`team_id` + `ds` + `credit_type`) |
| **Row count** | <!-- TODO: query for row count --> |
| **Refresh cadence** | Daily (Snowflake Task: `TASK_REFRESH_FCT_TEAM_CREDIT_LIMITS_DAILY`, chained after `TASK_REFRESH_FCT_TEAM_CREDITS_DAILY`) |
| **Trust level** | Canonical (Playground) — medium trust; depends on AGG_TEAM_CREDITS Airflow DAG |
| **Owner** | Data Engineering (Brighid Meredith) |
| **DAG** | Snowflake Task `PLAYGROUND.TASK_REFRESH_FCT_TEAM_CREDIT_LIMITS_DAILY` with stored procedure `SP_REFRESH_FCT_TEAM_CREDIT_LIMITS_DAILY` |

## Description

Normalized daily credit limits table. Each row represents one credit type's total allocation for a team on a given day. This is the companion to `FCT_TEAM_CREDIT_USE_DAILY` (which has usage). Together they replace the wide-format `FCT_TEAM_CREDITS_DAILY` for analyses that need credit_type-level granularity. Sourced from `AGG_TEAM_CREDITS` limit rows (where `feature_type IS NULL` and `credit_limit IS NOT NULL`).

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.PLAYGROUND.AGG_TEAM_CREDITS` | Limit rows only (`feature_type IS NULL AND credit_limit IS NOT NULL`) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | TEXT | Apollo team ID | FK to DIM_MONGO_TEAMS.TEAM_ID |
| ds | DATE | Snapshot date | |
| credit_type | TEXT | Type of credit | See values below |
| credit_limit | NUMBER | Total allocation for this credit type | |

### credit_type values

`email_credit`, `export_credit`, `direct_dial_credit`, `unified_lead_credit`, `ai_email`, `power_up_credit`, `form_enrichment_credit`, `website_visitor_credit`, `inbound_website_visitor_credit`, `conversation_credit`, `contact_website_visitor_credit`, `web_search_record_credit`, `ai_credit`, `unspecified`

## How It's Used

### Common query patterns
- Credit limit by type for a specific team: `WHERE team_id = ? AND ds = CURRENT_DATE()`
- Compare limits across credit types for a team over time
- Join with `FCT_TEAM_CREDIT_USE_DAILY` on `(team_id, ds, credit_type)` for utilization rates

### Key consumers
- Analytics team (credit analysis)
- Metric registry (credit-related OKR metrics)

## Known Issues & Gotchas

- **NaN filtering:** Source `AGG_TEAM_CREDITS` can contain NaN values in `credit_limit`. Filtered with `credit_limit = credit_limit` (NaN != NaN in Snowflake).
- **Medium trust:** Depends on `AGG_TEAM_CREDITS` which itself reads from `ANALYTICS_DATAPLATFORM` + `LU_ENUM`. If the AGG_TEAM_CREDITS Airflow DAG (runs every 6 hours) is late, this table will also be stale.
- **Task chaining:** This task runs after `TASK_REFRESH_FCT_TEAM_CREDITS_DAILY` completes, not on a fixed schedule.
- **DQ checks:** Row count, row count regression, duplicate grain, freshness, and credit_type cardinality checks run on each refresh.

## Slack Context

<!-- TODO: search Slack for discussions -->

## Business Terms

| Term | Definition |
|---|---|
| credit_type | The category of credit (e.g., email_credit, export_credit, unified_lead_credit) |
| credit_limit | Maximum number of credits of a given type allocated to a team |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-11 | Created context file | Brighid (via Claude) |
