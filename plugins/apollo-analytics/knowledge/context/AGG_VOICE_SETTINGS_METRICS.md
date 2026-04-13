# AGG_VOICE_SETTINGS_METRICS

> Daily aggregated metrics for voice settings (dialer phone numbers). One row per date.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.AGG_VOICE_SETTINGS_METRICS` |
| **Grain** | One row per date |
| **Row count** | 185 (as of 2026-03-26) |
| **Refresh cadence** | Daily (assumed — ANALYTICS_DATAPLATFORM standard) |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Daily snapshot aggregation of voice settings (dialer phone numbers) across the entire Apollo platform. Tracks total number count, active number count, and spam-flagged number count over time. Use for dialer health monitoring, spam rate trends, and capacity planning.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_MONGO_VOICE_SETTINGS | Aggregated from — daily counts of active, spam, and total voice settings |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DATE_OF_AGGREGATION | DATE | Date the metrics were captured | Primary key / grain |
| TOTAL_COUNT | NUMBER | Total number of voice settings | |
| ACTIVE_COUNT | NUMBER | Number of active voice settings | ACTIVE = true in DIM_MONGO_VOICE_SETTINGS |
| MARKED_AS_SPAM_COUNT | NUMBER | Number of voice settings marked as spam | |

## How It's Used

### Common query patterns

```sql
-- Spam rate trend over time
SELECT
    DATE_OF_AGGREGATION,
    TOTAL_COUNT,
    ACTIVE_COUNT,
    MARKED_AS_SPAM_COUNT,
    ROUND(MARKED_AS_SPAM_COUNT / NULLIF(ACTIVE_COUNT, 0), 4) AS spam_rate
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.AGG_VOICE_SETTINGS_METRICS
ORDER BY DATE_OF_AGGREGATION DESC
LIMIT 30;
```

### Key consumers

<!-- TODO: identify from query history -->

## Known Issues & Gotchas

- **Only 4 columns** — this is a platform-level daily snapshot, not team-level or user-level. For team-level breakdowns, use DIM_MONGO_VOICE_SETTINGS directly.
- **No TEAM_ID** — aggregated across all teams. Cannot filter by team without going back to the source dimension.

## Related Tables

| Table | Relationship |
|---|---|
| DIM_MONGO_VOICE_SETTINGS | Source dimension — item-level detail |
| FCT_MONGO_PHONE_CALLS | Complementary — call activity (this table is about number provisioning) |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
