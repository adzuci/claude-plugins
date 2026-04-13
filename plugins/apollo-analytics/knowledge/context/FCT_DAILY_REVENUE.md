# FCT_DAILY_REVENUE

> Daily revenue snapshot per team. Core financial table.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE` |
| **Grain** | One row per team + date (`APOLLO_TEAM_ID` + `DATE_PERIOD`) |
| **Row count** | ~207M (2026-03-06) |
| **Refresh cadence** | Daily (assumed — not found in airflow-dags repo) |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | <!-- TODO: likely Finance / Analytics --> |
| **DAG** | Not found in airflow-dags. Likely built by dbt project or separate pipeline external to this repo. |

## Description

Daily revenue table (27 distinct users, 33K queries). Contains MRR broken out by product line (self-serve, sales-assisted, rep, labs). Monitored by Metaplane for data quality. Used for team-level revenue lookups and onboarding analysis.

## Upstream Sources

Built by `dbt_apollo/models/marts/finance/fct_daily_revenue.sql` using two shared macros:
- **`create_revenue_datespine('day')`** — generates the per-account daily date spine from `int_opportunities_and_accounts`
- **`create_revenue_model_from_datespine('day', var('churn_limit_days'))`** — applies change category logic (new, churn, upgrade, downgrade, reactivation) on top of the datespine

| Source | Relationship | Notes |
|---|---|---|
| `int_opportunities_and_accounts` | Core datespine source | Unions team-level (`sfdc_team_id`, IS_PARENT_ACCOUNT=FALSE) and account-level (`implied_sfdc_account_id`, IS_PARENT_ACCOUNT=TRUE) opportunity rows. Root source of the dual-ID behavior in `SFDC_TEAM_OR_ACCOUNT_ID`. |
| `dim_salesforce_opportunities` | Won opportunities | Filtered to closed-won + open renewals with ARR > 0. Drives all ARR/MRR values. |
| `stg_salesforce__apollo_team` | Team-to-account mapping | Source of `sfdc_team_id` and `sfdc_account_id`. |
| `int_team_id_mappings` | ID bridge | Derives `implied_sfdc_account_id` — falls back to `sfdc_team_id` for freemail or unparented teams. Joined in final CTE to populate `APOLLO_TEAM_ID` (only resolves for IS_PARENT_ACCOUNT=FALSE rows). |
| `fct_account_edition_changes_extended` | Edition change flags | Provides `HAS_EDITION_CHANGE` and `EDITION_GROUP_CHANGE` per team per day. |
| `int_apollo_daily_seat_limits` | Seat limit changes | Provides `HAS_SEAT_LIMIT_CHANGE` and `SEAT_CHANGE_CATEGORY` per team per day. |
| `util_days` | Date spine | Calendar table used to generate the date range for each account. |

**dbt config:** `materialized='table'`, warehouse `ELT_WH_FR_DEV` (large), tagged `looker`.

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| DATE_PERIOD | DATE | 27 | 32,708 | Revenue date | **Partition key** with APOLLO_TEAM_ID |
| APOLLO_TEAM_ID | TEXT | 25 | 29,305 | Apollo team ID | **NULL for IS_PARENT_ACCOUNT = TRUE rows** (join in final CTE uses `sfdc_team_or_account_id = sfdc_team_id`, which fails for account-level rows). Only reliable for IS_PARENT_ACCOUNT = FALSE. |
| IS_PARENT_ACCOUNT | BOOLEAN | 23 | 31,931 | Parent account flag | Controls the grain AND the meaning of `SFDC_TEAM_OR_ACCOUNT_ID`. FALSE = team-level row; TRUE = account-level row. See join patterns below. |
| ARR | NUMBER | 21 | 21,608 | Annual Recurring Revenue | Core metric |
| CHANGE_CATEGORY | TEXT | 19 | 24,343 | Revenue movement type | new, churn, upgrade, downgrade |
| ARR_CHANGE | NUMBER | 19 | 7,814 | ARR delta | Net change this period |
| CONSECUTIVE_PAYMENT_PERIODS | NUMBER | 18 | 2,297 | Consecutive payments | Retention/health metric |
| SFDC_TEAM_OR_ACCOUNT_ID | TEXT | 17 | 7,940 | SF team/account ID | **Dual-purpose field — contains different ID types per row.** When IS_PARENT_ACCOUNT = FALSE: equals `sfdc_team_id`. When IS_PARENT_ACCOUNT = TRUE: equals `implied_sfdc_account_id` (SFDC account ID, or `sfdc_team_id` fallback for freemail/unparented teams). See join patterns below. |
| IS_REP_DRIVEN | BOOLEAN | 17 | 1,126 | Rep-driven flag | Sales attribution |
| IS_SELF_SERVE | BOOLEAN | 16 | 5,209 | Self-serve flag | Channel segmentation |
| HAS_SEAT_LIMIT_CHANGE | BOOLEAN | 16 | 1,259 | Seat change flag | |
| HAS_EDITION_CHANGE | BOOLEAN | 16 | 1,259 | Edition change flag | |
| IS_ACTIVE | BOOLEAN | 15 | 5,149 | Active subscription flag | |
| MRR | NUMBER | — | — | Monthly Recurring Revenue | Monitored by Metaplane (avg/stddev) |
| MRR_SS | NUMBER | — | — | MRR — Self-Serve | Metaplane monitoring |
| MRR_SA | NUMBER | — | — | MRR — Sales-Assisted | Metaplane monitoring |
| MRR_REP | NUMBER | — | — | MRR — Rep | Metaplane monitoring |
| MRR_LABS | NUMBER | — | — | MRR — Labs | Metaplane monitoring |

## How It's Used

### Join patterns — read this before joining

`SFDC_TEAM_OR_ACCOUNT_ID` contains **different ID types** depending on `IS_PARENT_ACCOUNT`. Use the correct join for each case:

**IS_PARENT_ACCOUNT = FALSE (team-level rows)**
```sql
-- Join to DIM_SALESFORCE_APOLLO_TEAMS via APOLLO_TEAM_ID (preferred — 100% match rate)
LEFT JOIN DIM_SALESFORCE_APOLLO_TEAMS t ON r.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
LEFT JOIN DIM_SALESFORCE_ACCOUNTS a ON t.SFDC_ACCOUNT_ID = a.ID
-- OR via sfdc_team_or_account_id = sfdc_team_id (also works for FALSE rows)
LEFT JOIN DIM_SALESFORCE_APOLLO_TEAMS t ON r.SFDC_TEAM_OR_ACCOUNT_ID = t.SFDC_TEAM_ID
```

**IS_PARENT_ACCOUNT = TRUE (account-level rows)**
```sql
-- SFDC_TEAM_OR_ACCOUNT_ID is an account ID here — join directly to DIM_SALESFORCE_ACCOUNTS
LEFT JOIN DIM_SALESFORCE_ACCOUNTS a ON r.SFDC_TEAM_OR_ACCOUNT_ID = a.ID
-- Do NOT join through DIM_SALESFORCE_APOLLO_TEAMS — the ID namespaces don't match.
-- Marketing attribution (LAST_TOUCH_UTM_CHANNEL_GROUP) is unavailable for TRUE rows
-- because APOLLO_TEAM_ID is NULL and there is no team-level join path.
```

**Common anti-pattern (produces silent data loss):**
```sql
-- WRONG for IS_PARENT_ACCOUNT = TRUE — only resolves for VSB-Freemail accounts
-- (freemail teams where implied_sfdc_account_id falls back to sfdc_team_id)
LEFT JOIN DIM_SALESFORCE_APOLLO_TEAMS t ON r.SFDC_TEAM_OR_ACCOUNT_ID = t.SFDC_TEAM_ID
```

### Common query patterns
- **Metaplane monitoring**: avg/stddev of each MRR variant for anomaly detection
- **Onboarding analysis**: joined with `ONBOARDING_HIGH_VELOCITY_TEAMS` on `apollo_team_id` + `date_period`
- Point-in-time ARR lookup for a specific team on a specific date
- Also queried via `STAGE_DB.ANALYTICS.FCT_DAILY_REVENUE` (Metaplane uses stage copy)

### Key consumers
- Metaplane (data quality monitoring — all MRR columns)
- Analysts (Michelle Chang — onboarding/revenue analysis)
- DA_TOOL_USER

## Default query behavior

**CRITICAL: Always filter `IS_PARENT_ACCOUNT = FALSE` and `DATE_PERIOD <= CURRENT_DATE()`.**

This table contains both team-level rows (FALSE) and parent-account rollup rows (TRUE). Querying without the filter sums BOTH, producing ~2x the real number. This caused a critical bug where Jarvis reported $415M ARR instead of the correct ~$199M.

| Use case | IS_PARENT_ACCOUNT | ARR range | Notes |
|---|---|---|---|
| **Default for all queries** | `FALSE` | ~$199M | Correct team-level ARR. Use this. |
| Account-level rollup (special cases only) | `TRUE` | ~$330–340M | Only for North Star dashboard debugging — never for answering "what is ARR?" |

Team-level rows (FALSE) have fully populated `APOLLO_TEAM_ID`, clean join paths to `DIM_SALESFORCE_APOLLO_TEAMS` and `DIM_SALESFORCE_ACCOUNTS`, and complete segment/attribution coverage. Parent account rows (TRUE) have NULL `APOLLO_TEAM_ID`, a different ID namespace in `SFDC_TEAM_OR_ACCOUNT_ID`, and no path to marketing attribution columns.

**Future-dated rows:** This table has ~34.7M rows with dates up to 2028. Always add `DATE_PERIOD <= CURRENT_DATE()` for actuals.

**Alternative for team-level daily snapshots:** `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY` (Bridie's foundation table) gives ARR directly from Mongo billing (95.1% match with FCT_DAILY_REVENUE at team level). Use for point-in-time snapshot queries where you need `APOLLO_TEAM_ID`. See `data-catalog/context/FCT_TEAM_REVENUE_DAILY.md`.

**North Star Looker dashboard discrepancies:** Most North Star tiles use `IS_PARENT_ACCOUNT = TRUE` (account-level grouping). If a user says their ad-hoc query doesn't match the dashboard, this is why — the dashboard aggregates at account level, not team level. Only switch to TRUE when explicitly debugging a North Star tile mismatch, not for answering general ARR questions.

## Known Issues & Gotchas

- Metaplane monitors the STAGE_DB copy, not the ANALYTICS_DB copy directly
- `IS_PARENT_ACCOUNT` controls both the grain AND the meaning of `SFDC_TEAM_OR_ACCOUNT_ID` — see join patterns above
- **`APOLLO_TEAM_ID` is NULL for all IS_PARENT_ACCOUNT = TRUE rows** (except freemail/unparented teams). This means marketing attribution columns from `DIM_SALESFORCE_APOLLO_TEAMS` (e.g. `LAST_TOUCH_UTM_CHANNEL_GROUP`) are only available for team-level rows.
- **Joining `SFDC_TEAM_OR_ACCOUNT_ID = DIM_SALESFORCE_APOLLO_TEAMS.SFDC_TEAM_ID` on IS_PARENT_ACCOUNT = TRUE will silently drop most revenue** — only VSB-Freemail accounts resolve because their `implied_sfdc_account_id` falls back to `sfdc_team_id`. Confirmed via lineage analysis of `int_opportunities_and_accounts` and `int_team_id_mappings` (2026-03-23).

## Slack Context

- **Executive tracking**: Daily revenue is the operational pulse. Dec 2025 exec debrief showed $12.9M gap to ARR target. Self-serve pacing at 103.5% but core SS ARR slightly under target.
- **DCS Scoreboard (Rob Statsky, Feb 2026)**: Expansion signals needed — seat growth rate (MoM), cross-product attach rate, expansion revenue influenced by DCS programs. All derived from daily revenue snapshots.
- **Metaplane monitoring**: All MRR variants (SS, SA, rep, labs) are monitored for anomalies via avg/stddev checks. Uses STAGE_DB copy.
- **Credits dashboard crossover (Brendan Walker → Brighid)**: Trying to understand free user credit consumption paths that lead to upgrades — needs FCT_DAILY_REVENUE joined with credit usage for conversion analysis.

## Sales Motion Definitions

The motion columns (`IS_REP_DRIVEN`, `IS_SALES_ASSISTED`, `IS_SELF_SERVE`, `IS_APOLLO_LABS` and corresponding `MRR_SS`, `MRR_SA`, `MRR_REP`, `MRR_LABS`) follow the definitions in [`domain/sales_motion_definitions.md`](../../domain/sales_motion_definitions.md). See that file for thresholds, edge cases, and historical changes.

## Business Terms

| Term | Definition |
|---|---|
| MRR | Monthly Recurring Revenue |
| ARR | Annual Recurring Revenue (MRR * 12) |
| Self-Serve (SS) | Revenue from self-service customers |
| Sales-Assisted (SA) | Revenue from sales-assisted customers |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Documented dual-ID behavior of SFDC_TEAM_OR_ACCOUNT_ID, correct join patterns per IS_PARENT_ACCOUNT value, APOLLO_TEAM_ID nullability, anti-pattern warning, default IS_PARENT_ACCOUNT = FALSE rule, North Star dashboard note, full upstream lineage from dbt analysis | Will (via Claude) |
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
