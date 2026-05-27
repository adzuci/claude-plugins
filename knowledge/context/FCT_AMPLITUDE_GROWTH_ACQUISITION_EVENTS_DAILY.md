# FCT_AMPLITUDE_GROWTH_ACQUISITION_EVENTS_DAILY

> Pre-aggregated daily Amplitude events for Growth & Acquisition product areas, including Feature Gate Shown events.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_GROWTH_ACQUISITION_EVENTS_DAILY` |
| **Grain** | One row per (team, event_type, event_properties, event_date) — daily pre-aggregation |
| **Refresh cadence** | Daily |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | Growth Analytics / Data Platform |

## Description

Daily-grain pre-aggregated Amplitude events filtered to Growth & Acquisition product areas. Primary source for `Feature Gate Shown` events used in feature gate attribution analysis. Each row represents one team's interactions with a specific event type on a given day, with `event_count` for volume and `min_event_at` for the earliest occurrence.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| EVENT_DATE | DATE | Date of the event batch | |
| APOLLO_TEAM_ID | VARCHAR | Team identifier | Joins directly to `dim_salesforce_apollo_teams.apollo_team_id` |
| EVENT_TYPE | VARCHAR | Amplitude event name | Filter on `'Feature Gate Shown'` for gate analysis |
| EVENT_PROPERTIES | VARIANT | Semi-structured event properties | Use `:"type"` to extract the gate identifier |
| MIN_EVENT_AT | TIMESTAMP | Earliest event timestamp in that day's batch | Used for first/last touch ordering in attribution |
| EVENT_COUNT | NUMBER | Number of events in the daily batch | |

## How It's Used

### Common query patterns

```sql
-- Feature gate views for attribution analysis
SELECT
    event_date,
    apollo_team_id,
    event_properties:"type"::varchar AS feature_gate,
    min_event_at,
    event_count
FROM analytics_db.analytics.fct_amplitude_growth_acquisition_events_daily
WHERE event_type = 'Feature Gate Shown'
```

### Known feature gates (as of 2026-04)

| Gate | Population reach | Baseline CVR |
|---|---|---|
| `bulk_select` | ~36% of free teams | ~4.5% |
| `advanced_filters` | ~59% of free teams | ~1.5% |
| `csv_enrichment_disabled` | ~4% of free teams | ~4.5% |

### Key consumers

- Feature gate first/last touch attribution (`teammates/andrew_green/sql_patterns.md`)
- Free-to-paid upgrade modal experiment analysis
- CBR Hex notebooks (2-day lookback attribution window)

## Known Issues & Gotchas

- No data catalog entry existed prior to 2026-04-10 — schema inferred from usage in analysis files
- `EVENT_PROPERTIES` is VARIANT — always cast extracted fields (e.g. `:"type"::varchar`)
- Daily grain means intra-day ordering uses `min_event_at` (earliest event), not exact event timestamps
- Coverage of `Feature Gate Shown` events may not extend before ~Sep 2025 — verify with `SELECT MIN(event_date)` before using older date ranges

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file from usage patterns in existing analyses | Andrew Green |
