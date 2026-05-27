# DIM_TEAMS

> Data Science team dimension. Enriched team-level attributes for product analytics.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS` |
| **Grain** | One row per Apollo team (`APOLLO_TEAM_ID`) |
| **Row count** | ~13.2M (2026-03-06) |
| **Refresh cadence** | Daily (owned by Data Science) |
| **Trust level** | Use with caution (ANALYTICS_DATASCIENCE — DS-maintained, not DE) |
| **Owner** | Data Science (Shyam SK) |
| **DAG** | Not found in airflow-dags. Likely a dbt model in a separate DS project. |

## Description

Second most-used table by distinct users (58). The Data Science team's enriched team dimension — likely downstream of DIM_MONGO_TEAMS with additional attributes like `IS_PAID_IND`, `ACCOUNT_SALES_DEPARTMENT_TIER`, and `IS_CORE_ACCOUNT`. Used for product analytics funnels, activation metrics, and Cortex Analyst (Databot) experiments.

## Upstream Sources

| Source | Relationship |
|---|---|
| `int_user_team_mapping` | apollo_team_id, sfdc_account_id, team_created_date |
| `dim_salesforce_apollo_teams` | 40+ columns: team_name, edition, pricing_variant, UTM, owner_id |
| `dim_salesforce_accounts` | account_name, segment, region, industry, employees |
| `dim_salesforce_users` × 3 | Owner, CSM, onboarding manager names/emails |
| `fct_daily_revenue` | first_paid_date, last_paid_date, is_paid_ind, ARR, starting_arr |
| `fct_apollo_daily_seat_limits` | starting/current paid_seat_limit |
| `int_events_users_indicators` | Setup action dates (email_verified, SSO, mailbox, calendar, CI) |
| `int_user_activity_aggregates` | **180+ feature usage columns** (first/last active dates, counts per feature) |
| `int_mongo_users_history` | Mongo user attributes |
| `onboarding_high_velocity_teams` | HVO attendance/booking flags |

## dbt Model Details (from dbt_apollo)

**Path:** `dbt_apollo/models/marts/data_science/dim_teams/dim_teams.sql`
**Warehouse:** `dbt_large_warehouse`
**Tags:** `looker`
**Materialized:** TABLE, unique key `apollo_team_id`, clustered by `apollo_team_id`

**Aggregation pattern:** User-level data aggregated to team level via `GROUP BY apollo_team_id`:
- `MAX()` for boolean flags (has_admin_permissions, is_free_email_domain)
- `SUM()` for feature usage counts (active_counts_email, active_counts_enrichment)
- `MIN()` for first dates, `MAX()` for last dates across all team users

**Output: 400+ columns** including identifiers, team dimensions, SF account data, revenue, seat metrics, setup actions, 180 feature usage columns, health score.

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| APOLLO_TEAM_ID | TEXT | 57 | 21,556 | Team ID | **Primary key.** Join to DIM_MONGO_TEAMS.TEAM_ID |
| TEAM_CREATED_DATE | DATE | 41 | 6,240 | Team creation date | |
| IS_PAID_IND | BOOLEAN | 41 | 3,649 | Paid team flag | Core filter for paid-only analysis |
| ACCOUNT_SEGMENT | TEXT | — | — | Account segment | Values: Enterprise / Mid-Market / SMB / VSB. **Use this for segment analysis.** |
| ACCOUNT_SUB_SEGMENT | TEXT | — | — | Pre-computed 6-way segment | Values: Enterprise / Mid-Market / SMB / VSB - Enriched / VSB - Not Enriched / VSB - Freemail. Shortcut — avoids manual CASE logic. |
| ACCOUNT_SALES_DEPARTMENT_TIER | TEXT | 41 | 3,231 | ~~Sales tier~~ | **OBSOLETE — do not use.** Replaced by `ACCOUNT_SEGMENT`. |
| TEAM_NAME | TEXT | 39 | 2,280 | Team display name | |
| ARR | NUMBER | 38 | 6,338 | Current ARR | Snapshot value, not historical |
| SFDC_ACCOUNT_ID | TEXT | 38 | 3,709 | Salesforce account ID | FK to DIM_SALESFORCE_ACCOUNTS.ID |
| IS_CORE_ACCOUNT | BOOLEAN | 37 | 5,763 | Core account flag | Standard filter for legitimate accounts |
| WEBSITE_DOMAIN | TEXT | 36 | 4,080 | Team domain | |
| FIRST_PAID_DATE | DATE | 36 | 2,654 | First conversion date | |
| BILLING_COUNTRY | TEXT | 35 | 3,235 | Billing country | |
| NUMBER_OF_EMPLOYEES | NUMBER | 34 | 3,614 | Headcount | From SF account |
| CONTRACT_STATUS | TEXT | 33 | 3,160 | Contract status | |
| MASTER_CONTRACT_TERM | TEXT | 33 | 1,734 | Contract length | |
| TEAM_EDITION | TEXT | 32 | 2,106 | Plan/edition | e.g. Free, Basic, Professional, Custom |
| CURRENT_TEAM_SALES_TYPE | TEXT | 32 | 1,793 | Sales type | Self-serve vs sales-assisted |
| HAS_FREE_EMAIL_DOMAIN_IND | BOOLEAN | 31 | 1,733 | Free email domain flag | gmail.com, yahoo.com, etc. |
| ACCOUNT_OWNER_NAME | TEXT | 31 | 1,516 | SF account owner | |

## How It's Used

### Common query patterns
- **Product analytics funnels**: Base table for user activation and retention analysis
- **Segment filtering**: `IS_PAID_IND`, `ACCOUNT_SEGMENT`, `IS_CORE_ACCOUNT`. Use `ACCOUNT_SUB_SEGMENT` for the pre-computed 6-way VSB split. **Never use `ACCOUNT_SALES_DEPARTMENT_TIER` — it is obsolete.**
- **Cortex Analyst / Databot**: Being used to power Snowflake Databot with sample queries collected from team

### Key consumers
- Data Science team (primary owner/user)
- Product Analytics
- Cortex Analyst / Databot experiments (Shyam SK)

## Known Issues & Gotchas

- Owned by DS, not DE — changes go through DS team, not Data Platform
- Likely a denormalized view of DIM_MONGO_TEAMS + SF data — may have stale SF fields
- Row count (13.2M) is ~4x DIM_MONGO_TEAMS (3.4M) — may include historical/deleted teams or different dedup logic

## Slack Context

- **Cortex Analyst experiment**: Shyam SK collecting sample queries using DIM_TEAMS and DIM_TEAMS_DAILY to train Snowflake Databot (#product-analytics-team)
- **Owned by Data Science**: Karun Kumar confirmed this dataset is owned by DS team, not Data Platform (#dataplatform-analytics-dev)
- **Refresh issues**: Pubudu flagged DIM_TEAMS_DAILY not refreshing (Jan 2026) — may indicate fragile pipeline (#dept-analytics)

## Business Terms

| Term | Definition |
|---|---|
| IS_PAID_IND | Boolean flag for teams on a paid plan |
| ACCOUNT_SEGMENT | Enterprise / Mid-Market / SMB / VSB. Use this for segment-level analysis. |
| ACCOUNT_SUB_SEGMENT | Pre-computed 6-way split: Enterprise / Mid-Market / SMB / VSB - Enriched / VSB - Not Enriched / VSB - Freemail. Use as a shortcut instead of manual CASE logic. |
| ACCOUNT_SALES_DEPARTMENT_TIER | **Obsolete.** Do not use — replaced by ACCOUNT_SEGMENT. |
| IS_CORE_ACCOUNT | Standard filter excluding suspicious/free-email teams |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history + Slack research | Brighid (via Claude) |
| 2026-03-09 | Added dbt model details (16 joins, 400+ cols), aggregation patterns, full upstream sources | Brighid (via Claude) |
| 2026-03-23 | New API/MCP columns added by Shyam: `first/last_active_date_api_calls`, `active_days_api_calls`, `active_counts_api_calls` — 3 segments: overall API, Apollo-MCP, partner API calls. Now the preferred source for MCP adoption analytics. | Jarvis (via Shyam Slack) |
| 2026-03-31 | Confirmed `ACCOUNT_SEGMENT` (Enterprise/Mid-Market/SMB/VSB) and `ACCOUNT_SUB_SEGMENT` (6-way VSB pre-split) as the current segment columns. `ACCOUNT_SALES_DEPARTMENT_TIER` marked obsolete. | Jarvis (Pubudu session) |
