# DIM_MONGO_RULE_CONFIGS

> Workflow/rule configuration dimension from MongoDB. One row per rule config (workflow definition).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_RULE_CONFIGS` |
| **Grain** | One row per rule config (workflow) |
| **Row count** | <!-- TODO: verify --> |
| **Refresh cadence** | Daily (dbt model, ANALYTICS_DATAPLATFORM) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |

## Description

Tracks workflow/automation rule configurations created in Apollo. Used for workflow-level analytics including creation volume, type, and source. Key for AI Assistant outcome analysis — `rule_config_source_cd = 'ai_assistant'` identifies workflows created through the AI Assistant. Paired with `DIM_MONGO_RULE_ACTIONS` to determine if the workflow was ever run.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `rule_configs` collection | Primary source (CDC ingestion) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| RULE_CONFIG_ID | TEXT (PK) | Unique workflow identifier | Join key to DIM_MONGO_RULE_ACTIONS |
| USER_ID | TEXT | User who created the workflow | FK to DIM_USERS |
| CREATED_AT_UTC | TIMESTAMP | When the workflow was created | Use for date filtering |
| RULE_CONFIG_SOURCE_CD | TEXT | How the workflow was created | `'ai_assistant'` = created via AI Assistant |
| TYPE_CD | TEXT | Type of rule config | `'workflow'` = workflow automation |

## How It's Used

### AI Assistant — workflows created and activated (F7D)

Workflows created via AI Assistant (`rule_config_source_cd = 'ai_assistant'`, `type_cd = 'workflow'`) that were run (at least one action executed) within 7 days of the user's first AI Assistant activation. Paired with `DIM_MONGO_RULE_ACTIONS` to confirm the workflow ran.

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

**F7D join condition** (join to `assistant_activated` CTE):
```sql
left join workflows wf on  wf.apollo_user_id = aa.apollo_user_id
                        and date(wf.workflow_created_datetime) >= aa.first_active_date
                        and date(wf.workflow_created_datetime) <= aa.first_active_date + 7
                        and date(wf.workflow_activated_datetime) <= aa.first_active_date + 7
```

### Key consumers
- AI product debrief — F7D high-value action rate
- AI Assistant outcome analysis (`ai_assistant_engagement_queries.sql`, query 13)

## Known Issues & Gotchas

- `RULE_CONFIG_SOURCE_CD = 'ai_assistant'` is the canonical flag for AI-created workflows.
- Always filter `TYPE_CD = 'workflow'` alongside `RULE_CONFIG_SOURCE_CD` — there may be other rule config types.
- A workflow can be created but never run — use LEFT JOIN to `DIM_MONGO_RULE_ACTIONS` and check if `ra.created_at_utc` is not null to confirm execution.

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_MONGO_RULE_ACTIONS` | Child — one row per workflow run/action; join on `rule_config_id` |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file — confirmed columns from AI Assistant F7D outcome query | Pubudu (via Jarvis) |
