# DIM_SALESFORCE_ACCOUNTS

> Salesforce account dimension. One row per SF account.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS` |
| **Grain** | One row per Salesforce Account (`ID`) |
| **Row count** | ~5.9M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model in `dbt_apollo`, `dbt_medium_warehouse`) |
| **Trust level** | High for segmentation (ANALYTICS schema, Fivetran-sourced, mature dbt model) |
| **Owner** | Analytics Engineering (dbt_apollo) |
| **DAG** | dbt model: `dbt_apollo/models/marts/salesforce/dim_salesforce_accounts.sql`. Tagged `looker`. |

## Description

Second highest query count (118K queries, 46 distinct users). Core CRM account dimension. Used in nearly every Looker explore as the account-level filter/grouper. Contains GTME (Go-To-Market Engineer) ownership, account segmentation, and suspicion flags.

## Upstream Sources

| Source | Relationship |
|---|---|
| `RAW_FIVETRAN_DB.SALESFORCE_QUICKSTART.STG_SALESFORCE__ACCOUNT` | Raw Fivetran sync (5.7M rows) |
| `stg_salesforce__accounts` | dbt staging model |
| 12 intermediate tables | See dbt model details below |

## dbt Model Details (from dbt_apollo)

**Path:** `dbt_apollo/models/marts/salesforce/dim_salesforce_accounts.sql`
**Warehouse:** `dbt_medium_warehouse`
**Tags:** `looker`

**Joins 12 intermediate tables to enrich raw SFDC data:**

| Intermediate Table | What It Adds |
|---|---|
| `int_account_revenue_metrics` | count_teams_with_active_arr, total_account_arr, total_account_mrr_to_date, seat counts |
| `int_accounts_starting_tier` | account_starting_tier, tier_N_started_at (tracks SMB→MM→Ent progression) |
| `int_accounts_with_team_summary` | count_teams, count_free_teams, first_team_* |
| `int_free_email_domain_accounts` | is_free_account flags (Gmail, Yahoo, Hotmail) |
| `int_account_persona_counts_and_flags` | enabled_persona_* counts (CEO, Sales, SDR, etc.) |
| `int_sfdc_account_start_and_end` | first_active_date (first opportunity date) |
| `dim_salesforce_users` × 3 lookups | Owner, CSM, product specialist names and hierarchy |
| `dim_salesforce_user_allocation` | Current owner/manager hierarchy with allocation dates |
| `fct_account_edition_changes` | onboarding_qualified_date |
| `marketing_contacts` | Whitespace persona counts |

**ACCOUNT_SEGMENT is a native Salesforce field** (`account_segment_c`), synced via Fivetran and renamed in `stg_salesforce__accounts`. It is NOT computed in dbt — dbt passes it through unchanged. The segment assignment logic (employee count thresholds, override rules, etc.) lives entirely in Salesforce.

**Segment values:**
| Segment | Typical Employee Count |
|---|---|
| Enterprise | > 1,000 |
| Mid-Market | 201–1,000 |
| SMB | 21–200 |
| VSB | 0–20, null, or freemail |

**Companion Salesforce fields** (also available in this table):
| Column | Source Field | Description |
|---|---|---|
| ACCOUNT_SEGMENT_DEFAULT | `account_segment_default_c` | System-assigned default before any overrides |
| ACCOUNT_SEGMENT_CUTTING | `account_segment_cutting_c` | Cutting/transition segment value |
| ACCOUNT_SEGMENT_OVERRIDE | `account_segment_override_c` | Manual override applied on top of default |

**ACCOUNT_SUB_SEGMENT** is computed in dbt on top of ACCOUNT_SEGMENT. Only VSB is split further; all other segments are passed through unchanged:

```sql
case
    when account_segment = 'VSB' and is_free_account = true       then 'VSB - Freemail'
    when account_segment = 'VSB' and number_of_employees is not null then 'VSB - Enriched'
    when account_segment = 'VSB'                                   then 'VSB - Not Enriched'
    else account_segment  -- Enterprise, Mid-Market, SMB pass through as-is
end as account_sub_segment
```

| Sub-Segment | Condition |
|---|---|
| VSB - Freemail | VSB + free email domain (Gmail, Yahoo, Hotmail, etc.) |
| VSB - Enriched | VSB + `NUMBER_OF_EMPLOYEES` is populated |
| VSB - Not Enriched | VSB + no employee count and not freemail |
| Enterprise / Mid-Market / SMB | Same as ACCOUNT_SEGMENT — no further split |

## ANALYTICS_DATAPLATFORM Availability

This table is **NOT** in ANALYTICS_DATAPLATFORM. The only SFDC-related table there is `DIM_MONGO_SALESFORCE_EQUIVALENT_ACCOUNTS` (6M rows, 12 columns) which lacks ACCOUNT_SEGMENT, IS_CORE_ACCOUNT, and ACCOUNT_REGION.

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| ID | TEXT | 43 | 115,999 | Salesforce Account ID | **Primary key.** Highest query count in warehouse. |
| ACCOUNT_SEGMENT | TEXT | 33 | 16,551 | Segmentation tier | Values: Enterprise, Mid-Market, SMB, VSB. **Raw Salesforce field** (`account_segment_c`) — assigned in Salesforce, not computed in dbt. |
| ACCOUNT_SUB_SEGMENT | TEXT | — | — | Sub-segment within ACCOUNT_SEGMENT | VSB splits into 3 values; all other segments echo ACCOUNT_SEGMENT. Computed in dbt. See logic below. |
| IS_CORE_ACCOUNT | BOOLEAN | 32 | 82,280 | Core account flag | **Being phased out.** High query count reflects legacy usage. Prefer filtering by `ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')` going forward. |
| HAS_SUSPICIOUS_TEAM | BOOLEAN | 31 | 42,561 | Has suspicious team flag | Standard exclusion filter |
| NAME | TEXT | 31 | 16,568 | Account name | |
| ACCOUNT_SALES_DEPARTMENT_TIER | TEXT | 30 | 42,129 | Sales dept tier | **Being phased out.** Values: Tier 1–4 (Tier 1/2 → MM, Tier 3/4 → SMB). Prefer `ACCOUNT_SEGMENT` / `ACCOUNT_SUB_SEGMENT` for segment-based views going forward. |
| NUMBER_OF_EMPLOYEES | NUMBER | 28 | 5,467 | Employee count | Firmographic |
| GTME_NAME | TEXT | 28 | 4,621 | Assigned GTME | Account ownership |
| SUSPICIOUS_ACCOUNT_C | BOOLEAN | 27 | 9,595 | Suspicious account flag | Filter: `NOT suspicious_account_c OR IS NULL` |
| TOTAL_ACCOUNT_ARR | NUMBER | 27 | 2,547 | Total ARR for account | Aggregated across teams |
| OWNER_ID | TEXT | 27 | 2,436 | Account owner | FK to DIM_SALESFORCE_USERS |
| BILLING_COUNTRY | TEXT | 27 | 1,795 | Billing country | Geo segmentation |
| ZP_SALES_DEPARTMENT_SIZE_C | TEXT | 27 | 1,727 | Sales dept size | Firmographic |
| INDUSTRY | TEXT | 27 | 845 | Industry classification | |
| ACCOUNT_REGION | TEXT | 26 | 5,875 | Geographic region | |
| APOLLO_INDUSTRY | TEXT | 26 | 2,484 | Apollo's industry classification | May differ from SF INDUSTRY |
| CUSTOMER_SUCCESS_MANAGER_USER_ID | TEXT | 26 | 1,309 | CSM assignment | FK to DIM_SALESFORCE_USERS |

## How It's Used

### Common query patterns
- **Account 360 Looker explore**: aliased as `account_360_teams`, joined with `apollo_teams` and `apollo_users`
- **Revenue dashboards**: joined via `DIM_SALESFORCE_APOLLO_TEAMS` using COALESCE pattern
- Almost always filtered by: `NOT suspicious_account_c` AND segment IN (Enterprise, Mid-Market, SMB, VSB)
- GTME reporting: grouped by `gtme_name`, `gtme_position_name`, `gtme_manager_name`

### Key consumers
- Looker (dominant — Account 360 explore, revenue dashboards)
- Sales/GTM reporting

## Known Issues & Gotchas

- **`IS_CORE_ACCOUNT` and `ACCOUNT_SALES_DEPARTMENT_TIER` are being phased out.** They appear frequently in existing queries due to legacy Looker usage, but new queries should use `ACCOUNT_SEGMENT` and `ACCOUNT_SUB_SEGMENT` instead. If you see these fields in a query, flag them as candidates for migration.
- Suspicious account filtering is critical — nearly every Looker query excludes them


## Slack Context

- **Account segmentation is central**: Executive metrics are always sliced by ACCOUNT_SEGMENT (Enterprise, Mid-Market, SMB, VSB). The DCS Scoreboard specifically needs VSB and SMB cohorts.
- **GTME assignment drives retention**: GTME_NAME, GTME_MANAGER_NAME used in retention/renewal analysis. Sales ops tracks 2.5x pipeline coverage per rep against accounts.
- **Suspicious account filtering is critical**: Nearly all reporting excludes suspicious accounts. The IS_CORE_ACCOUNT flag determines which accounts count toward official metrics.
- **Glean docs**: "Upmarket Readiness - AOP Objective", "SMB/VSB Segmentation Definition" — active work on how accounts are segmented and what qualifies as core.

## Business Terms

| Term | Definition |
|---|---|
| GTME | Go-To-Market Engineer — account owner/CSM equivalent |
| Core Account | An account that meets Apollo's criteria for active, legitimate customer |
| Account Segment | Tiered classification: Enterprise > Mid-Market > SMB > VSB |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Added ACCOUNT_SUB_SEGMENT column + dbt logic; corrected ACCOUNT_SEGMENT lineage — it is a raw Salesforce field (account_segment_c), not computed in dbt; added companion segment fields (default, cutting, override) | Will (via Claude) |
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
| 2026-03-09 | Added dbt model details (12 int tables), segment computation rules, ANALYTICS_DATAPLATFORM availability analysis | Brighid (via Claude) |
