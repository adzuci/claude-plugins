# HVO_CALLS_AI_PROCESSING

> LLM-extracted structured intelligence from HVO (High Value Onboarding) call transcripts — aka "Project BAT."

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING` |
| **Grain** | One row per conversation (CONVERSATION_ID) |
| **Row count** | ~26k (as of 2026-03-18) |
| **Refresh cadence** | Daily via Airflow DAG |
| **Trust level** | Use with caution — AI-generated fields, quality depends on model version and prompt |
| **Owner** | Rahul Gautam (Data Platform) / Leo Liu (Product Analytics, "Project BAT" stakeholder) |
| **DAG** | `hvo_calls_ai_processing` (apolloio/airflow-dags) |

## Description

Each row represents one HVO onboarding call, processed by an LLM (via DAPI) to extract ~55 structured fields from the call transcript. Fields include call classification, customer technical readiness, feature adoption signals, competitor mentions, upsell opportunities, aha moments, pain points, and recommended next actions. This is the core "Project BAT" intelligence table used by Product (Growth Conversion team), PS, and Analytics for understanding onboarding quality and customer signals.

A "decision engine" post-processes some AI outputs — `NEXT_ACTION_TYPE_FINAL` and `ACTION_DATE_FINAL` are computed from the raw AI outputs plus SLA rules.

## Upstream Sources

| Source | Relationship |
|---|---|
| HVO call transcripts (from meeting platform) | Raw transcripts ingested and normalized |
| DAPI (internal AI batch processing API) | LLM inference — extracts structured JSON from transcripts |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT (PK) | Unique conversation identifier | NOT NULL, join key across HVO tables |
| DATE | DATE | Call date | Extracted from start_time |
| MEETING_HOST_EMAIL | TEXT | Apollo rep's email | |
| CALL_TYPE | TEXT | Session type | `training`, `sales_exploration_evaluation`, `pricing_procurement`, `closing`, `technical_support`, `ongoing_account_management` |
| CALL_CATEGORY | TEXT | Session outcome category | Recently added (Rahul PR #2580). 32 predefined categories covering productive sessions, technical issues, no-shows, cancellations |
| CLIENT_ROLES | VARIANT | Array of attendee roles | `Admin`, `RevOps`, `AE`, `SDR`, `Founder`, `Sales Manager`, `Marketing`, `CSM`, `Operations`, `Other` |
| CUSTOMER_INTENDED_USE_CASE | TEXT | What customer wants Apollo for | e.g. sales prospecting, recruiting, lead generation |
| CUSTOMER_TECHNICAL_SUFFICIENCY_SCORE | NUMBER | Customer tech readiness (0-5) | Lower = needs more help |
| APOLLO_REPRESENTATIVE_TECHNICAL_SUFFICIENCY_SCORE | NUMBER | Rep proficiency (0-5) | |
| AHA_MOMENT | TEXT | Key realization during call | <=30 words |
| AHA_FEATURES | VARIANT | Array of features that resonated | From predefined list: Mailbox Linked, Chrome Extension, Sequences, etc. |
| FEATURE_DISCUSSED | VARIANT | Array of features discussed | |
| PAIN_POINT | TEXT | Primary pain point | |
| COMPETITOR_USERS_USED_BEFORE | VARIANT | Array of competitor tools | Normalized names (ZoomInfo, Salesforce, Outreach, etc.) |
| UPSELL_OPPORTUNITY | BOOLEAN | Expansion opportunity exists | |
| UPSELL_REASON | TEXT | Why upsell was flagged | |
| NEED_ANOTHER_TRAINING_SESSION | BOOLEAN | Customer needs more onboarding | |
| NEXT_ACTION_TYPE_FINAL | TEXT | Post-decision-engine action type | `training`, `config`, `data_fix`, `escalation`, `follow_up_meeting`, `sales_outreach`, `no_action`, `unknown` |
| ACTION_TEAM | TEXT | Team to handle next action | `support`, `product`, `training`, `sales`, `customer_success`, `marketing` |
| ACTION_DATE_FINAL | DATE | When action should happen | Prioritizes transcript date over SLA |
| IS_INBOUND_DISCUSSED | BOOLEAN | Inbound product discussed | |
| IS_DIALER_DISCUSSED | BOOLEAN | Dialer product discussed | |
| IS_AI_REFERRED | BOOLEAN | AI features mentioned | |
| TRANSCRIPT | TEXT | Full normalized transcript | Large text field — avoid SELECT * |
| PROMPT | TEXT | Full LLM prompt sent | For reproducibility — also large |
| MODEL_VERSION | TEXT | AI model version | |
| INGESTED_AT | TIMESTAMP_NTZ | When analysis completed | |

### Event flag columns (BOOLEAN)

These track whether specific onboarding milestones happened during the call:

MAILBOX_LINKED, CONFIG_BY_DEFAULT, VIEWS_SET_UP_SEARCH_SAVED, FILTERS_BY_DEFAULT, BUYING_INTENT_BY_DEFAULT, RECORD_ACTIONED, CREDITS_BY_DEFAULT, EXTENSION_USED, SEQUENCE_CREATED

### Decision engine flag columns (BOOLEAN)

Inputs to the post-processing decision engine:

TRAINING_OFF_TO_GOOD_START, HAS_UNRESOLVED_QUESTIONS, WILL_TRY_FEATURES, TECHNICAL_ISSUE_UNRESOLVED

## How It's Used

### Common query patterns

- **Onboarding quality dashboards** — aggregate by week/month, slice by CLIENT_ROLES, CALL_TYPE, CUSTOMER_TECHNICAL_SUFFICIENCY_SCORE
- **Feature adoption signals** — which features produce aha moments, competitor displacement patterns
- **Upsell pipeline** — filter UPSELL_OPPORTUNITY = TRUE, join to Salesforce for account context
- **Growth Conversion research** — Product team (Matt Woods) uses this as a qualitative signal source via "Feedback River" Slack channel
- **PS performance** — rep sufficiency scores, training completion rates

### Key consumers

- **Leo Liu** — Project BAT owner, exec reporting, Hex dashboards
- **Growth Conversion team** (Matt Woods, Manuela) — qualitative research for feature gates & upgrade flow optimization
- **WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS** — downstream aggregation table (ANALYTICS_DATASCIENCE)

## Joining to apollo_team_id

`HVO_CALLS_AI_PROCESSING` has no `apollo_team_id` column. Use the calendar event path via `ONBOARDING_HIGH_VELOCITY_TEAMS` — **verified working under DEVELOPER_ROLE (2026-03-20)**:

```sql
WITH hvo_meetings AS (
    SELECT
        REPLACE(t.APOLLO_TEAM_ID, '"', '') AS APOLLO_TEAM_ID,
        f.value::string                     AS CALENDAR_EVENT_ID
    FROM ANALYTICS_DB.ANALYTICS.ONBOARDING_HIGH_VELOCITY_TEAMS t,
         LATERAL FLATTEN(input => t.CALENDAR_EVENT_IDS) f
)
SELECT
    dt.website_domain,
    dt.apollo_team_id,
    ai.date                                  AS hvo_training_date,
    ai.aha_moment,
    ai.feature_discussed,
    ai.pain_point,
    ai.aligned_action_users_will_take,
    ai.competitor_users_used_before,
    ai.customer_intended_use_case,
    ai.customer_technical_sufficiency_score,
    ai.client_roles
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS                      dt
LEFT JOIN hvo_meetings                                              h   ON h.APOLLO_TEAM_ID    = dt.APOLLO_TEAM_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS f ON f.CALENDAR_EVENT_ID = h.CALENDAR_EVENT_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING ai ON ai.CONVERSATION_ID = f.CONVERSATION_ID
WHERE dt.website_domain IS NOT NULL
  AND ai.conversation_id IS NOT NULL
```

**Join chain:**
`ONBOARDING_HIGH_VELOCITY_TEAMS` (flatten `CALENDAR_EVENT_IDS`)
→ `FCT_MONGO_CONVERSATIONS` (via `CALENDAR_EVENT_ID`)
→ `HVO_CALLS_AI_PROCESSING` (via `CONVERSATION_ID`)
→ `DIM_TEAMS` (via `APOLLO_TEAM_ID`)

**Note:** `APOLLO_TEAM_ID` in `ONBOARDING_HIGH_VELOCITY_TEAMS` has extra quotes — use `REPLACE(..., '"', '')` to clean.

**Do NOT use:**
- `FCT_MONGO_CONVERSATIONS.TEAM_ID` — that is the Apollo rep's team, not the customer's
- `DIM_MONGO_CONTACTS` — resolves to only 1 distinct team (Apollo internal only)

Same pattern applies to `GTME_CALLS_AI_ANALYSIS`.

## Related Tables

| Table | Relationship |
|---|---|
| `HVO_CALLS_AI_PROCESSING_V2` | Previous version — same schema minus CALL_CATEGORY. Likely deprecated once backfill completes. |
| `HVO_CALLS_CALL_CATEGORY_BACKFILL` | Staging table for CALL_CATEGORY backfill (35k rows). Temporary — join on CONVERSATION_ID. |
| `WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS` | Downstream — weekly team-level signals derived from this + other sources. |
| `ONBOARDING_HIGH_VELOCITY_SESSIONS` | Related — onboarding funnel table (P1 in inventory). |

## Known Issues & Gotchas

- **TRANSCRIPT and PROMPT columns are huge** — always specify columns, never `SELECT *`
- **AI-generated data quality varies** — CALL_CATEGORY was recently added and backfilled separately; check INGESTED_AT to distinguish original vs backfilled records
- **CALL_CATEGORY comment is NULL** in Snowflake metadata (not yet documented in DDL)
- **V2 table overlap** — 16k rows in V2 vs 26k in main table. Unclear if V2 is a subset or parallel version. Use the main table unless you have a reason not to.

## Business Terms

| Term | Definition |
|---|---|
| HVO | High Value Onboarding — structured onboarding calls for new paid customers |
| Project BAT | Leo's analytics initiative to extract structured intelligence from HVO call transcripts using LLM processing |
| DAPI | Internal AI batch processing API used for LLM inference at scale |
| Decision engine | Post-processing logic that converts raw AI outputs (NEXT_ACTION_TYPE) into final action recommendations (NEXT_ACTION_TYPE_FINAL) using SLA rules |
| Sufficiency score | 0-5 rating of technical proficiency — applies to both customer and Apollo rep |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-02-03 | CALL_CATEGORY field added (PR #2580) | Rahul Gautam |
| 2026-03-18 | Created context file | Brighid (via Claude) |
