# DIM_MONGO_PEOPLE

> Person-level dimension from Apollo's database. Deduplicated person records across contacts.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_PEOPLE` |
| **Grain** | One row per person (`PERSON_ID`) |
| **Row count** | ~513M (2026-03-06) |
| **Refresh cadence** | Daily (dbt_models_group_1, dbt job 137019, model `people`) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1`. Also referenced in `foundational_datasets/lu_people_scd.sql`. |

## Key Columns

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| PERSON_ID | TEXT | 21 | 357 | Person ID | **PK.** FK from DIM_MONGO_CONTACTS.PERSON_ID |
| EMAIL | TEXT | 18 | 268 | Primary email | |
| PHONE_NUMBERS | ARRAY | 18 | 267 | Phone numbers | |
| CACHED_COUNTRY | TEXT | 18 | 209 | Country | |
| CURRENT_ROLES | ARRAY | 17 | 228 | Current job roles | |
| LINKEDIN_URLS | ARRAY | 17 | 219 | LinkedIn profiles | |
| FULL_NAME | TEXT | 17 | 194 | Full name | |
| PRIMARY_TITLE | TEXT | 17 | 176 | Job title | |
| CURRENT_ORGANIZATION_ID | TEXT | 17 | 159 | Current org | FK to DIM_MONGO_ORGANIZATIONS |
| IS_GDPR_REMOVED | BOOLEAN | 16 | 164 | GDPR deletion flag | |

## Known Issues & Gotchas

- ~513M rows — large table, use targeted queries
- GDPR compliance: IS_GDPR_REMOVED records should be excluded from most analyses
- Array columns (PHONE_NUMBERS, CURRENT_ROLES, LINKEDIN_URLS) need LATERAL FLATTEN

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file | Brighid (via Claude) |
