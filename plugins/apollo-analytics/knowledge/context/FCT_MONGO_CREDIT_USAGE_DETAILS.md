# FCT_MONGO_CREDIT_USAGE_DETAILS

> Granular credit usage details from MongoDB.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CREDIT_USAGE_DETAILS` |
| **Grain** | One row per credit usage detail record |
| **Row count** | ~137M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely `dbt_models_group_1`. Source: MongoDB credit_usage_details collection. |

## Description

Granular credit usage details (18 distinct users). More detailed than FCT_MONGO_CREDIT_USAGES — contains per-action credit consumption. Used for detailed credit analysis and debugging.

## Known Issues & Gotchas

- Related to FCT_MONGO_CREDIT_USAGES (higher level) and AGG_TEAM_CREDITS (aggregated)
- Credit type mapping issues apply here too

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
