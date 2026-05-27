# DIM_MONGO_RULE_ACTIONS

> Workflow/rule action execution fact from MongoDB. One row per workflow action run.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_RULE_ACTIONS` |
| **Grain** | One row per rule action execution |
| **Row count** | <!-- TODO: verify --> |
| **Refresh cadence** | Daily (dbt model, ANALYTICS_DATAPLATFORM) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |

## Description

Records each execution of a workflow action in Apollo. Used to determine whether a workflow (defined in `DIM_MONGO_RULE_CONFIGS`) was ever run. In AI Assistant outcome analysis, a workflow is considered "activated" when it has at least one action row in this table.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `rule_actions` collection | Primary source (CDC ingestion) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| RULE_CONFIG_ID | TEXT | Workflow this action belongs to | FK to DIM_MONGO_RULE_CONFIGS — join key |
| CREATED_AT_UTC | TIMESTAMP | When the workflow action was executed | Use to determine if workflow ran within F7D window |

<!-- TODO: Verify full column list — RULE_CONFIG_ID and CREATED_AT_UTC confirmed from query usage 2026-03-26 -->

## How It's Used

### Join pattern with DIM_MONGO_RULE_CONFIGS

Always LEFT JOIN from `DIM_MONGO_RULE_CONFIGS` — a workflow may exist but never have been run. Use `MIN(ra.created_at_utc)` to get the first time a workflow ran.

```sql
-- AI-Assistant-created workflow that was run
workflows as (
    select      distinct rc.user_id as apollo_user_id
                , rc.created_at_utc as workflow_created_datetime
                , ra.created_at_utc as workflow_activated_datetime
    from        analytics_db.analytics_dataplatform.dim_mongo_rule_configs  rc
    left join   analytics_db.analytics_dataplatform.dim_mongo_rule_actions  ra on ra.rule_config_id = rc.rule_config_id
    where       rc.rule_config_source_cd = 'ai_assistant'
    and         rc.type_cd = 'workflow'
    and         rc.created_at_utc > '2025-01-01'
),
```

### Key consumers
- AI product debrief — F7D high-value action rate
- AI Assistant outcome analysis (`ai_assistant_engagement_queries.sql`, query 13)

## Known Issues & Gotchas

- **Always LEFT JOIN from DIM_MONGO_RULE_CONFIGS** — not every workflow has been run.
- `CREATED_AT_UTC` is the execution timestamp — use this for the F7D activation check.

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_MONGO_RULE_CONFIGS` | Parent — workflow definition; join on `rule_config_id` |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file — confirmed columns from AI Assistant F7D outcome query | Pubudu (via Jarvis) |
