# FCT_ACCOUNT_EDITION_CHANGES

> Account plan/edition change events.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_ACCOUNT_EDITION_CHANGES` |
| **Grain** | One row per edition change event |
| **Row count** | ~83.7M (2026-03-06) |
| **Refresh cadence** | Unknown — not in airflow-dags. Likely dbt. |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | <!-- TODO --> |
| **DAG** | Not found in airflow-dags. |

## Description

Plan/edition change tracking (14 distinct users). Records when teams upgrade, downgrade, or change plans. Used for revenue analytics and churn analysis.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
