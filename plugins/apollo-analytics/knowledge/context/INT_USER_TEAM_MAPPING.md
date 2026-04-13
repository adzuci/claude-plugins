# INT_USER_TEAM_MAPPING

> User-to-team mapping bridge table from Data Science.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.INT_USER_TEAM_MAPPING` |
| **Grain** | One row per user-team mapping |
| **Row count** | ~15.3M (2026-03-06) — same as DIM_USERS |
| **Refresh cadence** | Daily (owned by Data Science) |
| **Trust level** | Use with caution (ANALYTICS_DATASCIENCE, INT prefix = intermediate) |
| **Owner** | Data Science |
| **DAG** | Not found in airflow-dags. DS dbt model. |

## Description

User-team bridge (14 distinct users). Maps users to teams — likely an intermediate dbt model. Same row count as DIM_USERS suggests 1:1 mapping (users can only be on one team).

## Known Issues & Gotchas

- INT prefix = intermediate model. Consider using DIM_USERS.APOLLO_TEAM_ID directly if you just need the team FK.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
