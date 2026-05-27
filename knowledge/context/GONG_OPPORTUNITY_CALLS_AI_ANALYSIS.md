# GONG_OPPORTUNITY_CALLS_AI_ANALYSIS

> Companion table to GONG_CALLS_AI_ANALYSIS — links Gong calls to Salesforce opportunities and AE ownership.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` |
| **Grain** | One row per Gong conversation (`CONVERSATION_ID`), linked to a Salesforce opportunity |
| **Row count** | <!-- TODO: run COUNT(*) --> |
| **Refresh cadence** | <!-- TODO: confirm — likely co-refreshed with GONG_CALLS_AI_ANALYSIS --> |
| **Trust level** | Use with caution — AI-generated fields |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: confirm DAG name in airflow-dags --> |

## Description

Bridges `GONG_CALLS_AI_ANALYSIS` (call-level intelligence) to Salesforce opportunity data. The key linkage is `OWNER_ID`, which maps to `DIM_SALESFORCE_USERS.ID` — i.e., the AE/rep who owns the opportunity associated with the call.

Enables answering: "Which AEs are having calls that mention competitor X?" or "What's the call pattern on deals owned by rep Y?"

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT (PK/FK) | Gong conversation identifier | Join to `GONG_CALLS_AI_ANALYSIS.CONVERSATION_ID` |
| OWNER_ID | TEXT | Salesforce user ID of opportunity owner | Join to `DIM_SALESFORCE_USERS.ID` to get name/email |
| <!-- TODO: fill remaining columns from information_schema --> | | | |

## Sample Join Pattern

```sql
WITH sfdc_users AS (
    SELECT id, name, email FROM analytics_db.analytics.dim_salesforce_users
)
SELECT
    sfdc_users.name    AS rep_name,
    sfdc_users.email   AS rep_email,
    gc.call_date,
    comp.value::STRING AS competitor
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_CALLS_AI_ANALYSIS gc
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_OPPORTUNITY_CALLS_AI_ANALYSIS gd
    ON gd.conversation_id = gc.conversation_id
LEFT JOIN sfdc_users ON sfdc_users.id = gd.owner_id
LEFT JOIN LATERAL FLATTEN(input => gc.COMPETITORS_DISCUSSED) comp
WHERE gc.call_date > '2025-06-01'
```

## Related Tables

| Table | Relationship |
|---|---|
| `GONG_CALLS_AI_ANALYSIS` | Parent — join on CONVERSATION_ID to get call-level AI analysis |
| `DIM_SALESFORCE_USERS` | Join target — OWNER_ID = DIM_SALESFORCE_USERS.ID for rep identity |
| `DIM_SALESFORCE_OPPORTUNITIES` | Related — OWNER_ID likely links here for full opportunity context |

## Known Issues & Gotchas

- **Schema not yet fully explored** — only `CONVERSATION_ID` and `OWNER_ID` confirmed from sample query. Run `check_new_tables.py` for full column list.
- **OWNER_ID = Salesforce User ID** (not Apollo team/user ID) — join to `DIM_SALESFORCE_USERS.ID`

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file from sample query | Leo (via Claude) |
