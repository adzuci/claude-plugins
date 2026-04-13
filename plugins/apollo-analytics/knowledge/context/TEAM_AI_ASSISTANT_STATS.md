# TEAM_AI_ASSISTANT_STATS

> Team-level lifetime AI Assistant stats for adoption and segmentation. One row per team, all-time aggregation.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_STATS` |
| **Grain** | One row per team_id |
| **Row count** | ~339K (2026-04-02) |
| **Refresh cadence** | Daily |
| **Trust level** | Authoritative (DS-owned, part of AI platform model hierarchy) |
| **Owner** | Data Science (Sai Sarvepalli) |
| **DAG** | dbt model: `models/marts/data_science/ai_platform/team_ai_assistant_stats.sql` |

## Description

Lifetime aggregation of AI Assistant activity per team. Complements `TEAM_AI_ASSISTANT_DAILY` (the time-series table) with a single-row snapshot per team useful for account-level adoption analysis and segmentation. Use for "all teams that have ever adopted AI Assistant" queries.

## Upstream Sources

| Source | Relationship |
|---|---|
| `TEAM_AI_ASSISTANT_DAILY` | Aggregated to lifetime stats per team |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| APOLLO_TEAM_ID | TEXT (PK) | Apollo team identifier | Renamed from TEAM_ID (2026-04 drift) |
| TEAM_CREATED_DATE | DATE | Team creation date | |
| FIRST_THREAD_DATE | DATE | First date team had any AI thread | Renamed from FIRST_ACTIVE_DATE |
| LAST_THREAD_DATE | DATE | Most recent thread date | Renamed from LAST_ACTIVE_DATE |
| TOTAL_THREADS_LIFETIME | NUMBER | All threads ever by any team member | |
| TOTAL_USERS_LIFETIME | NUMBER | Distinct users who had threads | Renamed from TOTAL_ACTIVE_USERS_LIFETIME |
| TOTAL_INTERACTED_THREADS_LIFETIME | NUMBER | Threads with user interaction | |
| TOTAL_SUCCESSFUL_THREADS_LIFETIME | NUMBER | Threads classified as success | |
| TOTAL_MESSAGES_LIFETIME | NUMBER | Total messages across all threads | |
| TOTAL_USER_MESSAGES_LIFETIME | NUMBER | User messages only | |
| TOTAL_ASSISTANT_MESSAGES_LIFETIME | NUMBER | Assistant messages only | |
| TOTAL_TOOL_CALLS_LIFETIME | NUMBER | Total tool calls | |
| TOTAL_DISTINCT_TOOLS_LIFETIME | NUMBER | Distinct tools used | |
| TOTAL_ACTIVE_DAYS_COUNT | NUMBER | Days with at least one thread | |
| DAYS_TO_ACTIVATE | NUMBER | Days from team creation to first thread | |
| IS_RETAINED_WEEK1 | BOOLEAN | Active in week 1 after first use | |
| IS_RETAINED_WEEK2 | BOOLEAN | Active in week 2 | |
| IS_RETAINED_WEEK3 | BOOLEAN | Active in week 3 | |
| IS_RETAINED_WEEK4 | BOOLEAN | Active in week 4 | |
| ACTIVE_DATES_ARRAY | ARRAY | Array of active dates | VARIANT — use LATERAL FLATTEN |
| ACTIVE_DAYS_ARRAY | ARRAY | Array of active day indices | VARIANT |

## How It's Used

### Common query patterns
```sql
-- Adopted teams by segment (join to DIM_TEAMS for segment)
SELECT t.ACCOUNT_SEGMENT, COUNT(DISTINCT s.APOLLO_TEAM_ID) AS adopted_teams
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_STATS s
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t ON s.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
WHERE s.TOTAL_THREADS_LIFETIME >= 5
GROUP BY 1;

-- Teams at risk of churning AI Assistant
SELECT * FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_STATS
WHERE LAST_THREAD_DATE < CURRENT_DATE - 14
  AND TOTAL_THREADS_LIFETIME >= 10;
```

### Key consumers
- AI adoption reporting (WAT, team-level activation)
- Account health / CSM tooling
- SMB/MM/ENT segment rollups for exec reporting

## Known Issues & Gotchas

- For weekly/daily trend analysis, use `TEAM_AI_ASSISTANT_DAILY` instead
- Join to `DIM_TEAMS` on `APOLLO_TEAM_ID` for segment and revenue enrichment
- LIFETIME_SUCCESS_RATE was removed — compute from TOTAL_SUCCESSFUL_THREADS_LIFETIME / TOTAL_INTERACTED_THREADS_LIFETIME

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Created context file from Notion AI Assistant Analytics Data Models doc | Sai (via Jarvis) |
| 2026-04-10 | Schema drift fix: TEAM_ID→APOLLO_TEAM_ID, date/user renames, 15 new cols | Bridie (Beat 4) |
