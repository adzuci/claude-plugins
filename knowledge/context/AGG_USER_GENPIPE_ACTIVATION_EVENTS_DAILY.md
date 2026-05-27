# AGG_USER_GENPIPE_ACTIVATION_EVENTS_DAILY

> Daily per-user event counts for Genpipe (prospecting/RA) activation steps.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.AGG_USER_GENPIPE_ACTIVATION_EVENTS_DAILY` |
| **Grain** | One row per user × event_date × activation_step |
| **Row count** | ~10M+ rows |
| **Refresh cadence** | Daily |
| **Coverage period** | ongoing |
| **Trust level** | Authoritative |
| **Owner** | Analytics DS (Adhiraj → Andrew Green interim) |
| **DAG** | unknown |

## Description

Aggregated daily event counts per user for Genpipe activation steps. Primary source for computing F14D Habit RA Rate — join to DIM_USER_ACTIVATION on APOLLO_USER_ID to get team context, then filter events within TEAM_CREATED_DATE + 14 days and count distinct days with `record_actioned` events.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `APOLLO_USER_ID` | TEXT | User identifier | Join key to DIM_USER_ACTIVATION |
| `EVENT_DATE` | DATE | Date of activity | |
| `ACTIVATION_STEP` | TEXT | Step name | Key values: `record_actioned`, `total_new_records_saved` |
| `EVENT_COUNTS` | FLOAT | Number of events on that day | |

## How It's Used

### Official F14D Habit RA Rate computation

```sql
-- Teams with 4+ distinct days of record_actioned in first 14 days
WITH events AS (
  SELECT a.APOLLO_TEAM_ID, g.EVENT_DATE
  FROM AGG_USER_GENPIPE_ACTIVATION_EVENTS_DAILY g
  JOIN DIM_USER_ACTIVATION a ON g.APOLLO_USER_ID = a.APOLLO_USER_ID
  WHERE g.ACTIVATION_STEP = 'record_actioned'
    AND g.EVENT_DATE BETWEEN a.TEAM_CREATED_DATE AND a.TEAM_CREATED_DATE + 14
    AND g.EVENT_COUNTS > 0
)
SELECT APOLLO_TEAM_ID,
       COUNT(DISTINCT EVENT_DATE) AS ra_days,
       ra_days >= 4 AS is_habit_ra
FROM events
GROUP BY 1
```

## Known Issues & Gotchas

- AI Assistant RA actions do NOT fire the underlying Amplitude event — undercounts true RA for AI-active teams (fix pending as of Apr 2026)
- MCP record actions have no downstream tracking — also excluded
