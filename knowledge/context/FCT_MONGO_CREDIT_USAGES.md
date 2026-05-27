# FCT_MONGO_CREDIT_USAGES

> Credit usage fact table from MongoDB. One row per credit usage event.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CREDIT_USAGES` |
| **Grain** | One row per credit usage event |
| **Row count** | ~757M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model). CDC config: `dags/mongo/config/ingestion_configs/cdc/credit_usages.yml` |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | CDC ingestion + dbt model. Upstream to AGG_TEAM_CREDITS. |

## Description

Raw credit usage events (19 distinct users). Feeds into AGG_TEAM_CREDITS via STG_AGG_CU staging. Contains individual credit consumption events with CHARGED_CREDIT_TYPE_CD.

## Known Issues & Gotchas

- Credit type names do NOT match LU_CREDIT_QUOTA — must use explicit CASE mapping
- ~757M rows — filter by date
- Key upstream source for AGG_TEAM_CREDITS pipeline

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
