# FCT_TEAM_FEATURE_USERS_DAILY

> Daily distinct user counts per feature, per team — pre-aggregated from FCT_TEAM_EVENT_ACTIVITY.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_FEATURE_USERS_DAILY` |
| **Grain** | One row per `(team_id, ds)` |
| **Row count** | ~272K (as of 2026-03-18) |
| **Refresh cadence** | Daily (6 AM PT via PLAYGROUND_DAILY_REFRESH task DAG) |
| **Trust level** | Medium — new table, not yet validated at scale |
| **Owner** | Analytics (Brighid) |
| **DAG** | `PLAYGROUND_DAILY_REFRESH` → `TASK_REFRESH_FCT_TEAM_FEATURE_USERS_DAILY` (Tier 1) |

## Description

Pre-aggregation of `FCT_TEAM_EVENT_ACTIVITY` (~20B event-level rows) down to team + day grain with COUNT(DISTINCT user_id) for each feature flag. This is the intermediate table that feeds `DIM_TEAMS_DAILY_V2`.

**Active-teams-only:** Only teams with at least one Amplitude event on a given day appear (243K distinct teams). Teams with zero activity have no row. DIM_TEAMS_DAILY has 13.6M teams because it includes a row for every team on every day.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EVENT_ACTIVITY` | Aggregated from event-level rows using feature boolean flags |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | VARCHAR | Team identifier | Join key to other PLAYGROUND tables |
| ds | DATE | Activity date | Partition date from FCT_TEAM_EVENT_ACTIVITY |
| active_user_count | NUMBER | Distinct users with any event | Equivalent to ACTIVE_USER_COUNTS_L1 in DIM_TEAMS_DAILY |
| enrichment_api_user_count | NUMBER | Distinct users with IS_ENRICHMENT_API_ACTIVATION = TRUE | |
| meetings_user_count | NUMBER | Distinct users with IS_MEETINGS_INTEREST = TRUE | |
| crm_record_management_user_count | NUMBER | Distinct users with IS_RECORD_MANAGEMENT = TRUE | |
| win_close_user_count | NUMBER | Distinct users with IS_DIALER OR IS_CONVERSATIONS_INTEREST | Combines two feature flags |
| ai_platform_user_count | NUMBER | Distinct users with IS_AI_PLATFORM = TRUE | |
| extension_user_count | NUMBER | Distinct users with IS_EXTENSION = TRUE | |
| sequences_user_count | NUMBER | Distinct users with IS_SEQUENCES = TRUE | |
| email_user_count | NUMBER | Distinct users with IS_EMAIL = TRUE | |
| list_building_user_count | NUMBER | Distinct users with IS_LIST_BUILDING = TRUE | |
| workflows_user_count | NUMBER | Distinct users with IS_WORKFLOWS = TRUE | |
| signals_user_count | NUMBER | Distinct users with IS_SIGNALS = TRUE | |

## How It's Used

### Common query patterns
- Direct source for `DIM_TEAMS_DAILY_V2` rolling window calculations
- Quick feature adoption counts by team without scanning 20B event rows

### Key consumers
- `DIM_TEAMS_DAILY_V2` (downstream join)
- Analytics team ad-hoc feature usage analysis

## Known Issues & Gotchas

- **Daily distinct only:** Each count is distinct users for that single day. Rolling L7/L28 windows built on top will SUM these daily counts, which overcounts users active on multiple days. True multi-day distinct requires event-level rescanning.
- **Date range:** Only covers dates present in FCT_TEAM_EVENT_ACTIVITY (2025-11-10 onward), not full historical like DIM_TEAMS_DAILY.
- **Incremental refresh:** Deletes and reinserts last 3 days only. Historical data is static after initial load.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-18 | Initial creation from FCT_TEAM_EVENT_ACTIVITY | Brighid |
