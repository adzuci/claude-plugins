# DIM_MONGO_ACCOUNTS

> Account dimension from MongoDB. One row per Apollo account record.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_ACCOUNTS` |
| **Grain** | One row per account |
| **Row count** | ~9.8B (2026-03-06) — extremely large |
| **Refresh cadence** | Daily (dbt_models_group_1, dbt job 137019, model `accounts`). Clone DB copy with 7-day timetravel. |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1`. Config: `dags/mongo/config/dbt_model_groups/dbt_model_groups.yml` |

## Key Columns

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| ORGANIZATION_ID | TEXT | 21 | 348 | Org reference | FK to DIM_MONGO_ORGANIZATIONS |
| ACCOUNT_ID | TEXT | 18 | 359 | Account ID | **PK** |
| TEAM_ID | TEXT | 17 | 352 | Owning team | FK to DIM_MONGO_TEAMS |
| CREATED_AT_UTC | TIMESTAMP | 16 | 316 | Creation date | |
| WEB_DOMAIN | TEXT | 14 | 288 | Account domain | |
| ACCOUNT_NAME | TEXT | 14 | 250 | Account name | |
| SALESFORCE_ID | TEXT | 10 | 37 | SF account ID | FK to DIM_SALESFORCE_ACCOUNTS |
| CRM_ACCOUNTS | VARIANT | 9 | 52 | CRM account data | Semi-structured |

## Known Issues & Gotchas

- **~9.8B rows** — extremely large, always use targeted queries with filters
- RNK_DESC field exists for deduplication — check before aggregating
- CRM_ACCOUNTS and MERGED_CRM_IDS are semi-structured (VARIANT)

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file | Brighid (via Claude) |
