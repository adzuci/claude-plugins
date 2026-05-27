# GONG_CALLS_AI_ANALYSIS

> LLM-extracted structured intelligence from Gong sales call recordings — the sales/AE equivalent of HVO_CALLS_AI_PROCESSING.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_CALLS_AI_ANALYSIS` |
| **Grain** | One row per Gong conversation (`CONVERSATION_ID`) |
| **Row count** | <!-- TODO: run COUNT(*) --> |
| **Refresh cadence** | <!-- TODO: confirm — likely daily via DAPI or Airflow --> |
| **Trust level** | Use with caution — AI-generated fields |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: confirm DAG name in airflow-dags --> |

## Description

Each row represents one Gong-recorded sales call, processed by an LLM to extract structured intelligence from the transcript. Fields include competitor mentions, call outcome signals, and other LLM-analyzed dimensions.

This is the sales call counterpart to `HVO_CALLS_AI_PROCESSING` (onboarding calls) and `GTME_CALLS_AI_ANALYSIS` (CSM/GTME calls). Covers AE sales calls recorded in Gong.

A companion table `GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` joins on `CONVERSATION_ID` and links each call to a Salesforce opportunity via `OWNER_ID`.

## Upstream Sources

| Source | Relationship |
|---|---|
| Gong (sales call recording platform) | Raw call recordings + transcripts |
| DAPI (internal AI batch processing API) | LLM inference — extracts structured fields from transcripts |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT (PK) | Unique Gong conversation identifier | Join key — links to `GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` |
| CALL_DATE | DATE | Date of the call | Filter: `WHERE call_date > '2025-06-01'` is typical |
| COMPETITORS_DISCUSSED | VARIANT | Array of competitor names mentioned on the call | Flatten with `LATERAL FLATTEN(input => gc.COMPETITORS_DISCUSSED)` |
| <!-- TODO: fill remaining columns from information_schema --> | | | |

## Sample Query

```sql
-- Gong calls with competitor signals, joined to opportunity owner
WITH sfdc_users AS (
    SELECT id, name, email FROM analytics_db.analytics.dim_salesforce_users
)
SELECT DISTINCT
    sfdc_users.name,
    sfdc_users.email,
    gc.*,
    gd.*,
    comp.value::STRING AS competitor_discussed_single
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_CALLS_AI_ANALYSIS gc
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_OPPORTUNITY_CALLS_AI_ANALYSIS gd
    ON gd.conversation_id = gc.conversation_id
LEFT JOIN sfdc_users ON sfdc_users.id = gd.owner_id
LEFT JOIN LATERAL FLATTEN(input => gc.COMPETITORS_DISCUSSED) comp
WHERE gc.call_date > '2025-06-01'
```

## How It's Used

### Common query patterns
- **Competitor analysis** — unnest `COMPETITORS_DISCUSSED` to track displacement opportunities (e.g., ZoomInfo, Outreach, Salesloft takeouts)
- **Sales rep performance** — join to `GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` for opportunity context, then to `DIM_SALESFORCE_USERS` for rep identity
- **Win/loss analysis** — combine competitor signals with opportunity outcomes

### Key consumers
- Sales leadership / RevOps — competitor displacement tracking
- Outbound Huddle tracking: competitive takeout vs $200K goal
- <!-- TODO: confirm if Hex dashboards exist -->

## Related Tables

| Table | Relationship |
|---|---|
| `GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` | Companion — links this call to a Salesforce opportunity via owner_id |
| `DIM_SALESFORCE_USERS` | Join target — `gd.owner_id = sfdc_users.id` to get rep name/email |
| `DIM_SALESFORCE_OPPORTUNITIES` | Indirect — opportunity context for sales calls |
| `HVO_CALLS_AI_PROCESSING` | Sister table — same LLM pipeline pattern, covers onboarding calls |
| `GTME_CALLS_AI_ANALYSIS` | Sister table — covers GTME/CSM calls |

## Known Issues & Gotchas

- **`SELECT *` caution** — likely has TRANSCRIPT / PROMPT columns (large text). Specify columns.
- **`COMPETITORS_DISCUSSED` is a VARIANT array** — must use `LATERAL FLATTEN` to get one row per competitor
- **Schema not yet fully explored** — run `check_new_tables.py` against this table to get full column list

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file from sample query | Leo (via Claude) |
