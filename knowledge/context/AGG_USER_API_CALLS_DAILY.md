# AGG_USER_API_CALLS_DAILY

> Daily aggregated API call counts per user. **As of 2026-03-23, prefer DIM_USERS / DIM_TEAMS for MCP-segmented API analytics — Shyam landed those columns directly there.**

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.AGG_USER_API_CALLS_DAILY` |
| **Grain** | One row per user × day |
| **Row count** | <!-- TODO: run COUNT(*) once access confirmed --> |
| **Refresh cadence** | Daily |
| **Trust level** | Use with caution — MCP segmentation now available in DIM_USERS/DIM_TEAMS (as of 2026-03-23); this table's `NUMBER_OF_APOLLO_MCP_CALLS` column may be superseded |
| **Owner** | Data Science (Shyam) |
| **DAG** | <!-- TODO: confirm Airflow DAG name --> |

> **Schema note:** Schema not yet confirmed from live query. `ANALYTICS_DB.ANALYTICS` is inferred from table naming convention (AGG_ prefix, similar to AGG_TEAM_CREDITS). Confirm before querying.

## Description

Daily aggregated API call counts at the user level. Tracks volume of API calls made by individual Apollo users. Used in the API product debrief as the primary source for total API call counts and teams-using-API trends. The `NUMBER_OF_APOLLO_MCP_CALLS` column for MCP-specific attribution is being actively built by Shyam and was not yet deployed as of March 2026.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| USER_ID | TEXT | Apollo user identifier | Join to DIM_USERS |
| TEAM_ID | TEXT | Apollo team identifier | Join to DIM_TEAMS |
| DS | DATE | Activity date | |
| NUMBER_OF_API_CALLS | NUMBER | Total API calls by this user on this day | Used for API product debrief volume |
| NUMBER_OF_APOLLO_MCP_CALLS | NUMBER | MCP-specific API calls | **In progress** — Shyam building as of 2026-03-21. Do not rely on until confirmed deployed. |

<!-- TODO: Run INFORMATION_SCHEMA.COLUMNS to get full schema once access is confirmed. Ping Shyam. -->

## How It's Used

### Weekly API teams/volume trend (API product debrief)
```sql
SELECT
    DATE_TRUNC('week', DS) AS week,
    COUNT(DISTINCT TEAM_ID) AS teams_using_api,
    SUM(NUMBER_OF_API_CALLS) AS total_api_calls
FROM ANALYTICS_DB.ANALYTICS.AGG_USER_API_CALLS_DAILY
WHERE DS >= CURRENT_DATE - 60
GROUP BY 1
ORDER BY 1 DESC
LIMIT 20;
```

### MCP calls (once NUMBER_OF_APOLLO_MCP_CALLS is deployed)
```sql
-- DO NOT USE UNTIL SHYAM CONFIRMS COLUMN IS LIVE
SELECT
    DATE_TRUNC('week', DS) AS week,
    COUNT(DISTINCT TEAM_ID) AS mcp_teams,
    SUM(NUMBER_OF_APOLLO_MCP_CALLS) AS mcp_calls
FROM ANALYTICS_DB.ANALYTICS.AGG_USER_API_CALLS_DAILY
WHERE DS >= CURRENT_DATE - 60
  AND NUMBER_OF_APOLLO_MCP_CALLS > 0
GROUP BY 1
ORDER BY 1 DESC
LIMIT 20;
```

### Key consumers
- **Analytics / Leo** — API product debrief (weekly WAT, call volume)
- **Shyam** — actively building MCP column

## Known Issues & Gotchas

- **Prefer DIM_USERS / DIM_TEAMS for MCP analytics** — as of 2026-03-23 Shyam landed `first/last_active_date_api_calls`, `active_days_api_calls`, `active_counts_api_calls` with 3-segment breakdown (overall API, Apollo-MCP, partner) directly in those tables.
- **`NUMBER_OF_APOLLO_MCP_CALLS` status unclear** — may be superseded by the DIM_USERS/DIM_TEAMS approach. Confirm with Shyam.
- **Schema unconfirmed** — inferred as `ANALYTICS_DB.ANALYTICS` from naming convention. Validate before querying.
- **User vs team grain** — this is user × day. Use `COUNT(DISTINCT TEAM_ID)` for team-level counts.

## Business Terms

| Term | Definition |
|---|---|
| API WAT | Weekly Active Teams using the Apollo REST/API surface (via `AGG_USER_API_CALLS_DAILY` or `DIM_ACTIVE_TEAMS_DAILY`) |
| MCP API Call | API call routed through the Apollo MCP connector, identifiable by `user_agent = 'Apollo-MCP/1.0'` in HTTP logs or via the forthcoming `NUMBER_OF_APOLLO_MCP_CALLS` column |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Created context file — API call volume source, MCP column in-progress caveat | Jarvis |
| 2026-03-23 | Updated — MCP segmentation now live in DIM_USERS/DIM_TEAMS per Shyam Slack message | Jarvis |
