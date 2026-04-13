# DIM_MONGO_TEAMS_PRODUCT_INFO

> Team-level product/plan details from MongoDB.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TEAMS_PRODUCT_INFO` |
| **Grain** | One row per team-product mapping |
| **Row count** | ~6.7M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely `dbt_models_group_1`. |

## Description

Raw team product info (16 distinct users). Upstream of INT_TEAM_PRODUCT_INFO_CLEANED. Contains plan details, product IDs per team.

## Known Issues & Gotchas

- INT_TEAM_PRODUCT_INFO_CLEANED is the cleaned downstream version — prefer that for analysis

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
