# DIM_MONGO_CONTACTS

> Contact dimension from MongoDB. One row per contact record.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_CONTACTS` |
| **Grain** | One row per contact (`CONTACT_ID`) |
| **Row count** | ~40.2B (2026-03-06) — extremely large table |
| **Refresh cadence** | Daily (dbt_models_group_1). Clone DB copy has 7-day timetravel retention. |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1` (dbt job 137019, model prefix `stg_mongo`, model `contacts`). Config: `dags/mongo/config/dbt_model_groups/dbt_model_groups.yml` |

## Description

Contact dimension (41 distinct users despite only 615 queries — wide reach, low frequency). Used for contact-level analysis, waterfall/enrichment analysis, and reverse ETL via Census.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `contacts` collection | Primary source |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| CONTACT_ID | TEXT | 37 | 427 | Contact ID | **Primary key.** Join to FCT_MONGO_EMAILER_MESSAGES, waterfall tables |
| CREATED_AT_UTC | TIMESTAMP | 29 | 201 | Contact creation | |
| TEAM_ID | TEXT | 28 | 267 | Owning team | **FK to DIM_MONGO_TEAMS.TEAM_ID** |
| UPDATED_AT_UTC | TIMESTAMP | 25 | 129 | Last update | |
| PERSON_ID | TEXT | 23 | 207 | Person reference | FK to DIM_MONGO_PEOPLE |
| EMAIL | TEXT | 23 | 159 | Contact email | |
| FIRST_NAME | TEXT | 22 | 131 | | |
| LAST_NAME | TEXT | 22 | 131 | | |
| LINKEDIN_URL | TEXT | 22 | 131 | LinkedIn profile | Enrichment data |
| ORIGINAL_SOURCE_CD | TEXT | 21 | 154 | How contact was created | Source attribution |
| LINKEDIN_UID | TEXT | 21 | 138 | LinkedIn user ID | |
| ENRICHED_BY_APOLLO | BOOLEAN | 21 | 100 | Apollo enrichment flag | |
| PROSPECT_IMPORT_IDS | ARRAY/TEXT | 20 | 150 | Import batch IDs | |
| CSV_EXPORT_IDS | ARRAY/TEXT | 20 | 127 | Export batch IDs | |
| ACCOUNT_ID | TEXT | 20 | 124 | Account reference | FK to DIM_MONGO_ACCOUNTS |

## How It's Used

### Common query patterns
- **Waterfall analysis**: joined with `DIM_MONGO_WATERFALL_STEP_RESULTS` on `CONTACT_ID` for enrichment/validation credit analysis
- **Census reverse ETL**: Census queries INFORMATION_SCHEMA for column metadata
- Joined with `DIM_TEAMS` for team-level attribution (filtering by ARR > 100K)

### Key consumers
- Census (reverse ETL — schema introspection)
- Jon Jenkins (waterfall/credit analysis)
- Analysts

## Known Issues & Gotchas

- Very large table — use targeted queries with LIMIT
- Low query count (615) relative to user count (41) suggests mostly metadata lookups and targeted queries, not full scans
- A DBT_DEVELOPMENT_DB copy exists and is sometimes used in joins

## Slack Context

- **Waterfall/enrichment analysis**: Jon Jenkins uses this table to analyze credit consumption per contact enrichment — joining with DIM_MONGO_WATERFALL_STEP_RESULTS to understand data_credit_used, validation_credit_used per contact.
- **Census reverse ETL**: CENSUS_USER queries this table for schema introspection — contacts are synced out to external systems.
- **Contact quality matters for deliverability**: ENRICHED_BY_APOLLO and ORIGINAL_SOURCE_CD help assess contact data quality. Low-quality contacts drive bounces and hurt email reputation.
- **PERSON_ID linkage**: Connects to DIM_MONGO_PEOPLE for deduplicated person-level analysis across teams.

## Business Terms

| Term | Definition |
|---|---|
| Contact | A person record in Apollo's database |
| Waterfall | Apollo's data enrichment pipeline that tries multiple providers |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
