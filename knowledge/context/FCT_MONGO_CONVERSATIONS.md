# FCT_MONGO_CONVERSATIONS

> Conversation/messaging activity facts from MongoDB.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS` |
| **Grain** | One row per conversation |
| **Row count** | ~6.8M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely `dbt_models_group_1`. |

## Description

Conversation/messaging facts (15 distinct users). Tracks messaging interactions within Apollo.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
