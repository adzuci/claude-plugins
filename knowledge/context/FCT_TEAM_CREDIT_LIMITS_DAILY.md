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

### credit_type values (verified 2026-04-17, last 7d)

| credit_type | Rows | Teams | Real credit? |
|---|---:|---:|---|
| `unified_lead_credit` | 20M | 2.9M | **YES — only monetized credit type** |
| `Email` | 2.4M | 386K | No — feature activity; limits are defaults (~114K/team avg) |
| `Export` | 5.5K | 957 | No — feature activity |
| `Form Enrichment` | 5.2K | 762 | No — feature activity |
| `Website Visitor` | 5.2K | 762 | No — feature activity |
| `Contact Website Visitor` | 5.0K | 735 | No — feature activity |
| `Power Up` | 1.3K | 252 | No — feature activity |
| `Ai` | 49 | 8 | No — feature activity |
| `Mobile` | 20 | 4 | No — feature activity |

**Only `unified_lead_credit` is a real monetized credit.** The other values track feature activity performance, not paid credit caps. Their `credit_limit` values are ambiguous defaults. Do NOT aggregate across types as if they represent real quota.

**Join hazard:** limits uses Title Case (`Email`, `Ai`, `Power Up`); `FCT_TEAM_CREDIT_USE_DAILY` uses lower_snake (`email_credit`, `ai_credit`, `power_up_credit`). A join on `credit_type` silently drops non-unified rows. If you need to cross-reference non-unified types, map explicitly with CASE.

## How It's Used

### Common query patterns
- Credit limit by type for a specific team: `WHERE team_id = ? AND ds = CURRENT_DATE()`
- Compare limits across credit types for a team over time
- Join with `FCT_TEAM_CREDIT_USE_DAILY` on `(team_id, ds, credit_type)` for utilization rates

### Key consumers
- Analytics team (credit analysis)
- Metric registry (credit-related OKR metrics)

## Known Issues & Gotchas

- **Only `unified_lead_credit` is a real credit.** See credit_type values table above. Other types are feature-activity tracking; their limits are not monetized caps. Any "utilization rate" computed across all types is noise.
- **Case mismatch with `FCT_TEAM_CREDIT_USE_DAILY` breaks credit_type joins** for non-unified types (Title Case here vs lower_snake there). Pipeline source: two upstream writers to `AGG_TEAM_CREDITS` use different casing (documented in `teammates/bridie_meredith/pipeline_notes.md`).
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
| 2026-04-17 | Documented ground truth: only unified_lead_credit is a real credit; others are feature-activity tracking with ambiguous/default limits. Flagged case-mismatch join hazard. | Brighid (via Jarvis) |
