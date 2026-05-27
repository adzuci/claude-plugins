# STG_MONGO__WATERFALL_WATERFALL_ENRICHMENT_REQUEST_STATS

> One row per waterfall enrichment request stat record — tracks credit usage, enrichment success, and entity type per request.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.STG_MONGO__WATERFALL_WATERFALL_ENRICHMENT_REQUEST_STATS` |
| **Grain** | One row per `WATERFALL_ENRICHMENT_REQUEST_STATS_ID` |
| **Row count** | ~70M (as of 2026-04-15) |
| **Refresh cadence** | Continuous / near-real-time (covers up to today) |
| **Coverage period** | 2025-02-05 to ongoing |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Enrichment — Mounica Sonikar |
| **DAG** | <!-- TODO: confirm DAG name --> |

## Description

Staging table for waterfall enrichment request statistics from MongoDB. Each row represents a single enrichment request attempt, capturing credit consumption, enrichment/verification success counts, entity type, and the requesting team and user. This is the canonical source for enrichment job volume and credit usage analytics.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `waterfall_enrichment_request_stats` collection | Direct staging (1:1) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `WATERFALL_ENRICHMENT_REQUEST_STATS_ID` | TEXT | PK | |
| `WATERFALL_ENRICHMENT_REQUEST_ID` | TEXT | Parent request ID | Use to group stats by job |
| `TEAM_ID` | TEXT | Team that initiated the request | |
| `USER_ID` | TEXT | User that initiated the request | |
| `ENTITY_TYPE_CD` | TEXT | Entity being enriched (e.g. contacts, organizations) | |
| `TARGET_FIELD` | TEXT | Specific field targeted for enrichment | |
| `NUM_CREDITS_USED` | NUMBER | Total credits consumed | Primary credit metric |
| `NUM_APOLLO_CREDITS_USED` | NUMBER | Apollo-owned credits consumed | |
| `NUM_DATA_PROVIDER_CREDITS_USED` | NUMBER | Data provider credits consumed | |
| `NUM_VALIDATOR_CREDITS_USED` | NUMBER | Validation credits consumed | |
| `NUM_ENRICHMENT_SUCCESSFUL` | NUMBER | Count of successful enrichment ops | |
| `ENTITY_ENRICHMENT_ATTEMPTED` | NUMBER | Enrichment attempts | |
| `ENTITY_ENRICHMENT_SUCCESSFUL` | NUMBER | Successful enrichments | |
| `ENTITY_VERIFICATION_ATTEMPTED` | NUMBER | Verification attempts | |
| `ENTITY_VERIFICATION_SUCCESSFUL` | NUMBER | Successful verifications | |
| `WATERFALL_DATA_PROVIDER_STATS` | VARIANT | Per-provider breakdown | |
| `WATERFALL_VALIDATOR_STATS` | VARIANT | Per-validator breakdown | |
| `CREATED_AT_UTC` | TIMESTAMP_NTZ | Request creation time | Use for time-based filtering |

## How It's Used

### Common query patterns

```sql
-- Enrichment jobs per team per day (n_jobs = COUNT(*) at request_stats grain)
SELECT
    team_id,
    CAST(created_at_utc AS DATE) AS date,
    SUM(num_credits_used)        AS total_credits,
    COUNT(DISTINCT user_id)      AS n_users,
    AVG(num_credits_used)        AS avg_credits_per_job,
    COUNT(*)                     AS n_jobs
FROM analytics_db.analytics_dataplatform.stg_mongo__waterfall_waterfall_enrichment_request_stats
WHERE created_at_utc >= '2025-11-01'
GROUP BY 1, 2
```

### Key consumers
- Enrichment analytics (Mounica Sonikar)

## Known Issues & Gotchas

- **Grain is per stat record, not per enrichment job.** A single waterfall enrichment request (`WATERFALL_ENRICHMENT_REQUEST_ID`) can produce multiple stat rows (one per target field or provider attempt). `COUNT(*)` counts stat records, not jobs. Use `COUNT(DISTINCT WATERFALL_ENRICHMENT_REQUEST_ID)` to count distinct jobs.
- **Coverage starts 2025-02-05** — no data before that date.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-15 | Created context file | Mounica Sonikar |
