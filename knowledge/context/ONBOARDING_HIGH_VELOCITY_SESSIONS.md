# ONBOARDING_HIGH_VELOCITY_SESSIONS

> Onboarding funnel session data.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.ONBOARDING_HIGH_VELOCITY_SESSIONS` |
| **Grain** | One row per onboarding session |
| **Row count** | ~34K (2026-03-06) — small table |
| **Refresh cadence** | Unknown — not in airflow-dags. Likely dbt. |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | <!-- TODO --> |
| **DAG** | Not found in airflow-dags. |

## Description

Onboarding funnel tracking (17 distinct users, 5.8K queries). Tracks high-velocity onboarding sessions — likely users who complete onboarding quickly. Small reference table.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
