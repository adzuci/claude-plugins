# DIM_MONGO_TEAMS

> Core team dimension table from MongoDB. One row per Apollo team.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TEAMS` |
| **Grain** | One row per Apollo team (`_ID`) |
| **Row count** | ~3.4M (2026-03-06) |
| **Refresh cadence** | Daily (dbt_models_group_1). Has a real-time view variant: `DIM_MONGO_TEAMS_RT_VW` |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1` (dbt job 137019, model prefix `stg_mongo`, model `teams`). Config: `dags/mongo/config/dbt_model_groups/dbt_model_groups.yml` |

## Description

The most-queried table in the warehouse by distinct users (77 in 90 days). Contains team-level attributes from MongoDB. Used as the foundational team dimension across nearly all analytics. A real-time view (`DIM_MONGO_TEAMS_RT_VW`) exists for fresher data.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `teams` collection | Primary source via Mongo CDC/ingestion |

## dbt Model Details (from dbt_apollo)

**Path:** `dbt_apollo/models/marts/mongo/dim_mongo_teams.sql`

Simple dedup passthrough:
```sql
-- ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY updated_at_utc DESC)
-- Picks the most recent snapshot per team_id from stg_mongo__teams
```

**Tags:** `mongo`, `dataplatform`, `base`
**Warehouse:** `ELT_WH_DEV` (xsmall)

## Downstream Dependencies

| Downstream Table | Schema | How It Uses DIM_MONGO_TEAMS |
|---|---|---|
| `DIM_TEAMS` (DS) | ANALYTICS_DATASCIENCE | Via `int_user_team_mapping` — aggregates user-level data to team |
| `DIM_MONGO_TEAMS_PRODUCT_INFO` | ANALYTICS_DATAPLATFORM | Direct ref — extracts product info fields |
| `DIM_SALESFORCE_APOLLO_TEAMS` | ANALYTICS | Indirect — via `stg_salesforce__apollo_team` matching on team_id |
| Fraud investigation queries | Ad-hoc | Joined to `FCT_MONGO_STRIPE_WEBHOOK_EVENTS` via `stripe_customer_id` |
| Privacy/Transcend workflows | Automated | RT_VW variant joined to `DIM_MONGO_USERS_RT_VW` and `DIM_MONGO_CSV_EXPORTS_RT_VW` |
| Pricing variant analysis | Automated (DA_TOOL_USER) | Joined to `fct_pricing_variant_changes` then through SFDC bridge for segment |

## The Canonical 3-Table Segmentation Join

DIM_MONGO_TEAMS has **NO segment column**. To slice any team metric by segment:

```sql
DIM_MONGO_TEAMS.SFDC_ACCOUNT_ID
  → DIM_SALESFORCE_APOLLO_TEAMS.APOLLO_TEAM_ID (bridge)
    → DIM_SALESFORCE_ACCOUNTS.ID (ACCOUNT_SEGMENT, IS_CORE_ACCOUNT, ACCOUNT_REGION)
```

This 3-table join appears in nearly every segmented analysis. DIM_TEAM_ATTRIBUTES (planned) will eliminate it.

## Key Columns

Ranked by actual usage from `SNOWFLAKE_ACCESS_HISTORY_ARCHIVE` (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| TEAM_ID | TEXT | 74 | 28,450 | Team ID (MongoDB ObjectId) | **Primary key.** Universal join key. |
| CREATED_AT_UTC | TIMESTAMP | 42 | 27,086 | Team creation timestamp | Cohort analysis |
| CACHED_CURRENT_ARR | NUMBER | 42 | 811 | Cached ARR snapshot | Quick ARR lookup without joining revenue tables |
| WEB_DOMAIN | TEXT | 40 | 5,295 | Team's web domain | |
| CONTACT_NAME | TEXT | 37 | 428 | Primary contact name | |
| PRICING_VARIANT | TEXT | 35 | 19,096 | Pricing plan variant | Very high query count — key segmentation column |
| DELETED | BOOLEAN | 34 | 3,248 | Soft-delete flag | Filter: `deleted = false` |
| LAST_ACTIVE_AT_UTC | TIMESTAMP | 31 | 2,846 | Last activity timestamp | Active team filtering |
| IS_ON_ANNUAL_CONTRACT | BOOLEAN | 30 | 485 | Annual vs monthly billing | |
| ROOT_DOMAIN | TEXT | 30 | 321 | Team's root domain | |
| STATUS_CD | TEXT | 30 | 284 | Team status code | |
| RNK_DESC | NUMBER | 30 | 280 | Ranking column | Used for dedup/ordering |
| STRIPE_CUSTOMER_ID | TEXT | 30 | 278 | Stripe customer reference | Links to payment data |
| MASTER_TEAM_ID | TEXT | 30 | 274 | Parent/master team | Hierarchy/consolidation |
| DATA_DELETED_AT_UTC | TIMESTAMP | 29 | 2,813 | Data deletion timestamp | GDPR/compliance |
| HAS_BEEN_MIGRATED_TO_UNIFIED_CREDIT_VARIANT | BOOLEAN | 29 | 429 | Unified credit migration flag | Credit system migration tracking |
| ZP_PARENT_ACCOUNT_ID | TEXT | 29 | 335 | Parent account ID | FK to SF accounts |
| PRODUCT_INFOS | VARIANT | 28 | 2,819 | Semi-structured product info | High query count, semi-structured |

## How It's Used

### Common query patterns
- Joined with `DIM_MONGO_USERS` via `TEAM_ID` for user-team analysis
- Joined with `DIM_MONGO_CSV_EXPORTS` for export activity analysis
- DA_TOOL_USER queries it heavily (automated tooling / AI agent queries)
- Filtered by `LAST_ACTIVE_AT` and `CREATED_AT` date ranges

### Key consumers
- DA_TOOL_USER (automated analytics tool — highest query volume)
- Looker dashboards (via downstream tables like DIM_SALESFORCE_APOLLO_TEAMS)
- Ad-hoc analyst queries

## Known Issues & Gotchas

- The RT_VW variant (`DIM_MONGO_TEAMS_RT_VW`) is sometimes used interchangeably — check which one your upstream uses
- Many queries use broad date filters (`>= '2022-01-01'`) suggesting the table is large

## Slack Context

- **Universal join key**: Nearly every analytics query touches this table. TEAM_ID is the atomic unit of Apollo's business — billing, usage, product, and CRM all converge here.
- **Pricing variant tracking**: PRICING_VARIANT (35 users, 19K queries) is critical for unified credit migration analysis. HAS_BEEN_MIGRATED_TO_UNIFIED_CREDIT_VARIANT tracks migration status.
- **Non-core vs core customer mix**: Executive concern that growth is skewing toward non-core customers. DELETED and STATUS_CD columns used to separate active/legitimate teams.
- **CACHED_CURRENT_ARR**: Quick ARR lookup (42 users) avoids joining to revenue tables for simple team-level ARR checks.
- **Key for DCS Scoreboard**: Team-level adoption metrics (search within 7 days, mailbox connection, sequences launched) all join through TEAM_ID.

## Business Terms

| Term | Definition |
|---|---|
| Team | An Apollo workspace/account unit. Multiple users belong to one team. |
| Root Domain | The primary domain associated with a team |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
| 2026-03-09 | Added dbt model details, downstream dependencies, canonical 3-table join pattern | Brighid (via Claude) |
