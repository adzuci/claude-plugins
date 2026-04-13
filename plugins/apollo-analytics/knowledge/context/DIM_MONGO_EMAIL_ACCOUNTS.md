# DIM_MONGO_EMAIL_ACCOUNTS

> Email account dimension from MongoDB. Connected email accounts for sending.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_EMAIL_ACCOUNTS` |
| **Grain** | One row per email account |
| **Row count** | ~13.8M (2026-03-06) |
| **Refresh cadence** | Daily (dbt daily_ingestion_1, dbt job 945826, model `email_accounts`) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_daily_ingestion_1`. Config: `dags/mongo/config/dbt_model_groups/dbt_model_groups.yml` |

## Description

Email account dimension (14 distinct users). Tracks connected email accounts used for Apollo email sending. Important for deliverability analysis.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
