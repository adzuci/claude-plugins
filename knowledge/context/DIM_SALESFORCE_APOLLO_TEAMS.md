# DIM_SALESFORCE_APOLLO_TEAMS

> Salesforce-Apollo team mapping. Bridges SF accounts to Apollo teams.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS` |
| **Grain** | One row per SF-Apollo team mapping (`SFDC_TEAM_ID`) |
| **Row count** | ~10.8M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model in `dbt_apollo`, `dbt_medium_warehouse`) |
| **Trust level** | High for bridge/attribution (ANALYTICS schema, Fivetran-sourced, mature dbt model) |
| **Owner** | Analytics Engineering (dbt_apollo) |
| **DAG** | dbt model: `dbt_apollo/models/marts/salesforce/dim_salesforce_apollo_teams.sql`. Tagged `looker`. |

## Description

Highest query count of any table (103K queries in 90 days, 57 distinct users). The primary bridge between Salesforce CRM data and Apollo product data. Nearly every Looker revenue dashboard joins through this table.

## Upstream Sources

| Source | Relationship |
|---|---|
| `stg_salesforce__apollo_team` | Base SFDC team fields (190+ columns) |
| `DIM_SALESFORCE_ACCOUNTS` | Joined via `SFDC_ACCOUNT_ID` = accounts.`ID` |
| 16 intermediate tables | See dbt model details below |

## dbt Model Details (from dbt_apollo)

**Path:** `dbt_apollo/models/marts/salesforce/dim_salesforce_apollo_teams.sql`
**Warehouse:** `dbt_medium_warehouse`
**Tags:** `looker`

**Joins 16 intermediate tables — the most heavily enriched DIM in the warehouse:**

| Intermediate Table | What It Adds |
|---|---|
| `int_team_edition_summary` | current/starting edition, contract term, sales type |
| `int_team_revenue_metrics` | is_paying, ARR, seat limits, churn dates |
| `int_team_arr_expansion` | first_active_date, starting_arr, day_30/60/90_arr |
| `int_team_first_created_user` | first_contact_id, initial UTM attribution |
| `int_team_crm_linked_summary` | CRM integration flags (SFDC, HubSpot, Pipedrive) |
| `int_team_persona_counts_and_flags` | persona distributions |
| `int_team_meetings_booked_summary` | first/last meeting booked, total, days_to_book |
| `int_team_first_deal` | team_first_deal_created_at |
| `int_salesforce_apollo_teams_partnerships_additions` | partner attribution |
| `int_team_activation_milestones_ever` | 40+ activation boolean flags |
| `int_features_and_use_cases_combined` | is_team_active_ever, first_product_active_date |
| `int_team_seat_summary` | first_paid_month_seat_limit |
| `fct_mongo_promos_teams_overview` | promo flags (redeemed, qualified, counts) |
| `team_health_scoring_12w_latest` | team_health_score/rating/color (paying only) |
| `apollo_team_fraud_abuse_flags` | fraud_abuse_flags, has_fraud_abuse_flag |
| `onboarding_high_velocity_teams` | HVO attendance/booking flags |

**Row logic gotcha:** Only `is_deleted = false` in `stg_salesforce__apollo_team` removes rows. All other joins are LEFT JOINs — teams always appear even with NULL revenue/metrics/persona data.

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| APOLLO_TEAM_ID | TEXT | 55 | 64,208 | Apollo team ID | **Primary key.** Join to all Apollo tables. |
| SFDC_ACCOUNT_ID | TEXT | 38 | 79,767 | Salesforce Account ID | **FK to DIM_SALESFORCE_ACCOUNTS.ID.** Highest query count. |
| TEAM_CREATED_DATE | DATE | 35 | 14,998 | Team creation date | Cohort analysis |
| CURRENT_APOLLO_EDITION_GROUPED | TEXT | 35 | 1,558 | Current plan tier (grouped) | Segmentation |
| SFDC_TEAM_ID | TEXT | 34 | 41,529 | SF-mapped team ID | Join key from FCT_MONTHLY_REVENUE |
| IS_SUSPICIOUS_TEAM | BOOLEAN | 34 | 40,204 | Suspicious team flag | Standard filter exclusion |
| TEAM_NAME | TEXT | 34 | 9,532 | Team name | |
| FIRST_ACTIVE_DATE | DATE | 34 | 8,667 | First activity date | |
| ARR | NUMBER | 34 | 4,366 | Current ARR | |
| WEBSITE_DOMAIN | TEXT | 32 | 7,218 | Team website | |
| TEAM_EDITION | TEXT | 32 | 6,091 | Detailed plan edition | |
| STATUS | TEXT | 32 | 1,032 | Team status | |
| LAST_TOUCH_UTM_CHANNEL_GROUP | TEXT | 31 | 8,398 | Attribution channel | Marketing attribution |
| IS_PAYING | BOOLEAN | 31 | 3,281 | Paying team flag | Core filter for paid analysis |
| MASTER_CONTRACT_TERM | TEXT | 31 | 2,532 | Contract term | |
| IS_REP_DRIVEN_FIRST_PAID_MONTH | BOOLEAN | 31 | 1,312 | Rep-driven acquisition flag | Sales vs self-serve attribution |
| CS_ELIGIBILITY_TYPE | TEXT | 30 | 921 | CS tier eligibility | |
| HAS_ANY_CRM_INTEGRATION | BOOLEAN | 29 | 1,479 | CRM connected flag | |
| HAS_SFDC_INTEGRATION | BOOLEAN | 29 | 1,456 | Salesforce connected | |
| HAS_HUBSPOT_INTEGRATION | BOOLEAN | 29 | 1,456 | HubSpot connected | |
| TOTAL_ENABLED_USERS | NUMBER | 29 | 1,225 | Active user count | |

## How It's Used

### Common query patterns
- **Revenue dashboards**: `FCT_MONTHLY_REVENUE` JOIN on `SFDC_TEAM_OR_ACCOUNT_ID` = `SFDC_TEAM_ID`
- **Account 360**: `DIM_SALESFORCE_ACCOUNTS` JOIN on `ID` = `SFDC_ACCOUNT_ID`
- Looker uses it in nearly every revenue/retention explore
- Filtered by `TEAM_CREATED_DATE` for cohort analysis
- Churn/downgrade analysis: combined with `FCT_MONTHLY_REVENUE.CHANGE_CATEGORY`

### Key consumers
- Looker (dominant consumer — revenue, churn, retention dashboards)
- Analyst ad-hoc queries

## Fraud & Abuse Columns

These columns are sourced from `apollo_team_fraud_abuse_flags` (silver mart), which aggregates MongoDB's `fraud_labels` collection. See `DIM_MONGO_FRAUD_LABELS.md` for full lineage and fraud type taxonomy.

| Column | Type | Description | Notes |
|---|---|---|---|
| `HAS_FRAUD_ABUSE_FLAG` | BOOLEAN | TRUE if team has any active **non-ATO** fraud label | ATO types (ato_suspected, ato_confirmed, ato_confirmed_with_unauthorized_charge) are intentionally excluded — they indicate compromised accounts, not intentional abuse. NULLs coalesce to false. |
| `FRAUD_ABUSE_FLAGS` | OBJECT | Key-value map of `type_cd → fraud_type` for all labels | |
| `FRAUD_ABUSE_FLAG_NAMES` | ARRAY | Sorted array of all `fraud_type` strings on this team | |
| `FIRST_FRAUD_ABUSE_FLAG_AT` | TIMESTAMP | When the team received their first non-ATO fraud label | |
| `IS_SUSPICIOUS_OR_FRAUD_ABUSE_FLAG` | BOOLEAN | TRUE if `HAS_FRAUD_ABUSE_FLAG = true` OR `IS_SUSPICIOUS_TEAM = true` | Combines MongoDB fraud labels with Salesforce suspicion flag |
| `IS_SUSPICIOUS_TEAM` | BOOLEAN | Salesforce-sourced suspicion flag | Separate from MongoDB fraud labels — set by CS/Sales Ops in Salesforce |

**Standard exclusion filter:**
```sql
where coalesce(has_fraud_abuse_flag, false) = false
  and coalesce(is_suspicious_team, false) = false
```

**How fraud labels flow into this table:**
```
mongo.fraud_labels (MongoDB) → stg_mongo__fraud_labels → dim_mongo_fraud_labels
  → apollo_team_fraud_abuse_flags (aggregated per team)
      → dim_salesforce_apollo_teams (LEFT JOIN on apollo_team_id)
```

The app enforces blocks from MongoDB directly at request time — Snowflake is an analytics mirror, not the enforcement layer.

## Known Issues & Gotchas

- Lives in ANALYTICS schema (mixed trust level) — verify lineage if precision matters
- The COALESCE pattern `coalesce(SFDC_ACCOUNT_ID, SFDC_TEAM_OR_ACCOUNT_ID)` appears in Looker queries, suggesting some teams don't have SF account mappings
- **Only one filter removes rows:** `is_deleted = false` in `stg_salesforce__apollo_team`. All other joins in the main model are LEFT JOINs — teams always appear even with NULL revenue/metrics/persona data. Filters like `IS_PAYING`, `IS_SUSPICIOUS_TEAM`, edition, etc. are query-time filters, not table-level exclusions. (Kirk, 2026-03-09)
- `HAS_FRAUD_ABUSE_FLAG` does **not** include ATO-type labels — query `DIM_MONGO_FRAUD_LABELS` directly if you need ATO events

## Slack Context

- **Bridge table for all revenue reporting**: Every Looker revenue dashboard joins through this table. The exec debrief showing $177.1M ARR and churn breakdowns relies on this join.
- **NRR/GRR by segment**: The IS_PAYING, CURRENT_APOLLO_EDITION_GROUPED, IS_SUSPICIOUS_TEAM columns are the filters that define the denominator for retention metrics. Getting these wrong cascades into all retention reporting.
- **DCS Scoreboard needs**: VSB/SMB team-level metrics (search adoption, mailbox connection, sequence activity) all require this table to map Apollo teams to SF accounts for segment filtering.
- **Attribution tracking**: LAST_TOUCH_UTM_CHANNEL_GROUP, IS_REP_DRIVEN_FIRST_PAID_MONTH, IS_SELF_SERVE_FIRST_PAID_MONTH power the acquisition channel attribution that feeds marketing AOP planning.
- **Glean docs**: "FY27 Macro Funnel: Growth & Acquisition", "North Star 2.5" — this table is foundational to funnel and growth metrics.

## Business Terms

| Term | Definition |
|---|---|
| SFDC Team | An Apollo team that has been mapped to a Salesforce account |
| Parent Account | A Salesforce account that owns one or more Apollo teams |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
| 2026-03-09 | Added dbt model details (16 int tables), row logic gotcha, upstream sources | Brighid (via Claude) |
| 2026-03-17 | Added fraud & abuse columns section with full lineage notes | Kirk (via Claude) |
