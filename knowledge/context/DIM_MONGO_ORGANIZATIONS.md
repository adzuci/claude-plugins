# DIM_MONGO_ORGANIZATIONS

> Organization/company dimension from Apollo's database. One row per organization.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_ORGANIZATIONS` |
| **Grain** | One row per organization (`ORGANIZATION_ID`) |
| **Row count** | ~66.7M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model, stg_mongo prefix) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1` (dbt job 137019, model prefix `stg_mongo`, model `organizations`). |

## Description

Apollo's organization/company database (28 distinct users). Contains firmographic data — employee counts, industries, technologies, revenue. The foundation of Apollo's B2B data product. Low query frequency relative to user count (473 queries) suggests targeted lookups.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `organizations` collection | Primary source |
| Data enrichment pipeline | Firmographic enrichment |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| ORGANIZATION_ID | TEXT | 26 | 409 | Organization ID | **Primary key** |
| ESTIMATED_NUM_EMPLOYEES | NUMBER | 20 | 254 | Employee count estimate | |
| INDUSTRIES | ARRAY/TEXT | 20 | 223 | Industry classifications | |
| WEBSITE_URL | TEXT | 20 | 205 | Company website | |
| ORG_NAME | TEXT | 19 | 192 | Organization name | |
| SIC_CODES | ARRAY/TEXT | 19 | 147 | SIC industry codes | |
| TECHNOLOGIES | ARRAY/TEXT | 18 | 144 | Tech stack | Apollo's technographic data |
| SHORT_DESCRIPTION | TEXT | 18 | 142 | Company description | |
| ALL_DOMAINS | ARRAY/TEXT | 17 | 128 | All known domains | |
| REVENUE | NUMBER | 17 | 110 | Estimated revenue | |
| RNK_DESC | NUMBER | 16 | 99 | Ranking/dedup field | |
| HEADQUARTER_RAW_ADDRESS | TEXT | 16 | 91 | HQ address | |
| LINKEDIN_URL | TEXT | 16 | 84 | LinkedIn company page | |

## How It's Used

### Common query patterns
- **Firmographic lookups**: Employee count, industry, revenue for account analysis
- **Domain matching**: ALL_DOMAINS and WEBSITE_URL for company identification
- **Technographic analysis**: TECHNOLOGIES array for tech stack analysis

### Key consumers
- Data Science (auto-scoring models use org data)
- Product (data quality analysis)
- Sales/Marketing (account enrichment)

## Known Issues & Gotchas

- ~66.7M rows — large table, use targeted queries
- Array columns (INDUSTRIES, TECHNOLOGIES, SIC_CODES, ALL_DOMAINS) require LATERAL FLATTEN
- RNK_DESC likely used for deduplication — check before aggregating

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
