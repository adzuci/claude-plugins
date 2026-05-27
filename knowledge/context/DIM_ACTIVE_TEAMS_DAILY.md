# DIM_ACTIVE_TEAMS_DAILY

> Filtered + enriched daily snapshot of teams with usage. The canonical source for feature WAT (Weekly Active Teams) across all product areas.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_ACTIVE_TEAMS_DAILY` |
| **Grain** | One row per (apollo_team_id, activity_date) — active teams only |
| **Refresh cadence** | Daily (dbt model, downstream of DIM_TEAMS_DAILY) |
| **Trust level** | High — canonical SoT for WAT metrics |
| **Owner** | Data Science (Shyam SK) |
| **dbt model** | `dbt_apollo/models/marts/data_science/dim_active_teams_daily.sql` |

## Relationship to DIM_TEAMS_DAILY

```
DIM_TEAMS_DAILY (all teams × all dates, ~8.5B rows)
  → DIM_ACTIVE_TEAMS_DAILY (filtered to teams with usage — much smaller)
```

DIM_ACTIVE_TEAMS_DAILY adds:
- Full **L1/L7/L28** rolling windows for every feature sub-type (DIM_TEAMS_DAILY only has L1)
- **INTEREST** variants (`*_INTEREST_USER_COUNTS_*`) — users who showed interest but may not have activated
- Boolean flags: `has_*_team_usage_l1` converted from counts
- `boolor_agg()` window "ever" flags
- `min(iff(...))` for first usage dates

## WAT Definition — This is the SoT

**Metrics DB → DIM_ACTIVE_TEAMS_DAILY is the canonical source for all feature WAT.** Never use credit tables (AGG_TEAM_CREDITS, FCT_TEAM_CREDIT_USE_DAILY) to define WAT — those are transactional tables for deeper dives, not usage metrics.

```sql
-- Waterfall WAT on a given week
SELECT
    DATE_TRUNC('week', activity_date) AS week,
    COUNT(DISTINCT apollo_team_id) AS waterfall_wat
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_ACTIVE_TEAMS_DAILY
WHERE activity_date >= DATEADD('week', -13, CURRENT_DATE)
  AND ENRICHMENT_WATERFALL_USER_COUNTS_L7 > 0
GROUP BY 1
ORDER BY 1;
```

## Enrichment Sub-Type Columns

Four enrichment sub-types are tracked. Each has L1, L7, L28 + INTEREST variants:

| Sub-type | L7 Column | Description |
|---|---|---|
| **Waterfall** | `ENRICHMENT_WATERFALL_USER_COUNTS_L7` | Users using waterfall enrichment — **Waterfall WAT source** |
| API | `ENRICHMENT_API_USER_COUNTS_L7` | Users using enrichment API |
| CSV | `ENRICHMENT_CSV_USER_COUNTS_L7` | Users using CSV enrichment |
| CRM Living Data | `ENRICHMENT_CRM_LIVING_DATA_USER_COUNTS_L7` | Users using CRM living data enrichment |

Also available: `USE_CASE_ENRICHMENT_ACTIVE_USER_COUNTS_L1/L7/L28` — total enrichment (all sub-types combined).

## Interest vs Active

Each sub-type has two variants:
- `ENRICHMENT_WATERFALL_USER_COUNTS_L7` — users who **actively used** waterfall
- `ENRICHMENT_WATERFALL_INTEREST_USER_COUNTS_L7` — users who **showed interest** (viewed/clicked) but may not have run enrichment

Use active count for WAT. Use interest count for funnel/activation analysis.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-22 | Created — schema verified from INFORMATION_SCHEMA.COLUMNS, relationship to DIM_TEAMS_DAILY documented, WAT definition established as SoT | Leo (via Jarvis) |
