# GTME_CALLS_AI_ANALYSIS

> LLM-extracted structured intelligence from GTME (Go-To-Market Engineer) / CSM call transcripts — the GTME equivalent of HVO_CALLS_AI_PROCESSING.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS` |
| **Grain** | One row per conversation (`CONVERSATION_ID`) |
| **Row count** | ~2,362 (2026-03-19) |
| **Refresh cadence** | Daily via DAPI batch (assumed — same pipeline as HVO) |
| **Trust level** | Use with caution — AI-generated fields; quality depends on model version and prompt |
| **Owner** | Data Platform (same pipeline owner as HVO_CALLS_AI_PROCESSING) |
| **DAG** | <!-- TODO: confirm DAG name in airflow-dags — likely parallel to hvo_calls_ai_processing --> |

## Description

Each row represents one GTME/CSM customer call, processed by an LLM (via DAPI) to extract ~38 structured fields from the transcript. Fields cover customer sentiment, churn risk scoring, upsell detection, pain points, feature requests, product gaps, competitor mentions, and recommended next actions with SLA-driven dates.

This is the GTME-focused counterpart to `HVO_CALLS_AI_PROCESSING` (which covers onboarding calls). Where HVO focuses on new customer activation, GTME_CALLS_AI_ANALYSIS focuses on ongoing account health, retention signals, and expansion opportunities for existing customers managed by GTMEs/CSMs.

A decision engine post-processes AI outputs — `NEXT_ACTION_TYPE_FINAL` and `ACTION_DATE_FINAL` are computed from raw AI outputs plus SLA rules, same pattern as HVO.

## Upstream Sources

| Source | Relationship |
|---|---|
| GTME/CSM call transcripts (meeting platform) | Raw transcripts ingested and normalized |
| DAPI (internal AI batch processing API) | LLM inference — extracts structured JSON from transcripts |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT (PK) | Unique conversation identifier | Join key |
| DATE | DATE | Call date | Extracted from transcript start_time |
| MEETING_HOST_EMAIL | TEXT | Email of the GTME/CSM host | |
| DISCUSSION_SUMMARY | TEXT | 1-2 sentence summary of what was discussed | ≤30 words |
| AHA_MOMENT | TEXT | Biggest realization or moment from the call | ≤30 words |
| TOPICS_DISCUSSED | VARIANT | Array of topics (e.g. Inbound, Dialer, Seats, Credits, Integrations) | |
| WHAT_APOLLO_IS_TRYING_TO_DRIVE | TEXT | What Apollo is pushing the customer toward | ≤30 words |
| CUSTOMER_SENTIMENT | TEXT | `positive`, `neutral`, `negative`, `mixed`, `unknown` | |
| SENTIMENT_REASON | TEXT | Reasoning for sentiment classification | ≤30 words |
| CHURN_RISK_SCORE | NUMBER | 0–5: 0=unknown, 1=very low, 5=very high | Key retention signal |
| CHURN_RISK_REASON | TEXT | Reasoning for churn risk score | ≤30 words |
| UPSELL_DETECTED | BOOLEAN | Expansion opportunity detected | Strictly: seat expansion, addon credits, Inbound/Dialer add, monthly→annual |
| UPSELL_REASON | TEXT | Why upsell was flagged | ≤30 words |
| PAIN_POINT | TEXT | Main customer problems or friction | ≤30 words |
| FEATURE_REQUESTS | VARIANT | Array of customer asks for new capabilities | |
| PRODUCT_GAPS | TEXT | Missing capabilities or limitations mentioned | ≤30 words |
| COMPETITOR_USERS_USED_BEFORE | VARIANT | Array of competitor tools mentioned | e.g. ZoomInfo, Outreach, Salesloft, Clay |
| IS_AI_REFERRED | BOOLEAN | Whether AI features were mentioned | |
| COMMENTS_ON_AI | TEXT | Customer comments on AI features | ≤30 words |
| RECOMMENDED_NEXT_ACTION | TEXT | What GTME/CSM should do next | ≤30 words |
| NEXT_ACTION_TYPE | TEXT | Raw AI action type | `sales_outreach`, `csm_followup`, `support_ticket`, `product_feedback`, `no_action`, `unknown` |
| NEXT_ACTION_TYPE_FINAL | TEXT | Post-decision-engine action type | Same values — overrides raw type |
| ACTION_TEAM | TEXT | Team to handle action | `support`, `product`, `customer_success`, `sales`, or empty |
| ACTION_SLA_DAYS | NUMBER | SLA days for the action | NULL if no action |
| ACTION_DATE_RECOMMENDED | DATE | Recommended action date based on SLA | |
| ACTION_DATE_FROM_TRANSCRIPT | DATE | Action date parsed from transcript text | |
| ACTION_DATE_FINAL | DATE | Final action date | Prioritizes transcript date over SLA |
| CRM_TASK_TITLE | TEXT | Auto-generated CRM task title | Includes action type, team, date, and conversation ID |
| CLIENT_ROLES | VARIANT | Array of client roles on the call | Admin, RevOps, AE, SDR, Founder, CMO, Sales Manager, etc. |
| LANGUAGE_SPOKEN | TEXT | Language(s) spoken | e.g. English, Spanish, English+Spanish |
| INTERVENTIONS_DISCUSSED | VARIANT | Array of interventions discussed during the call | |
| TRANSCRIPT | TEXT | Full normalized transcript | Large — avoid `SELECT *` |
| PROMPT | TEXT | Full LLM prompt sent | For reproducibility — also large |
| MODEL_VERSION | TEXT | AI model version used | |
| TRANSCRIPT_CHECKSUM | TEXT | SHA256 of normalized transcript | For dedup/verification |
| DAPI_BATCH_ID | TEXT | DAPI batch request identifier | For tracking/debugging |
| DAPI_REQUEST_TIME | TIMESTAMP_NTZ | When the analysis request was made | |
| INGESTED_AT | TIMESTAMP_NTZ | When analysis completed and ingested | |

## How It's Used

### Common query patterns
- **Churn risk monitoring** — filter `CHURN_RISK_SCORE >= 3`, join to `DIM_SALESFORCE_APOLLO_TEAMS` for account context and ARR at risk
- **Upsell pipeline** — filter `UPSELL_DETECTED = TRUE`, group by segment/GTME
- **Sentiment trends** — aggregate `CUSTOMER_SENTIMENT` by week/month/GTME
- **Product feedback synthesis** — unnest `FEATURE_REQUESTS` and `TOPICS_DISCUSSED` for product teams
- **Competitor displacement signals** — unnest `COMPETITOR_USERS_USED_BEFORE`

### Key consumers
- GTME / CSM team — action routing and account health
- `WEEKLY_TEAM_SIGNALS_FROM_GTME_CALLS` — downstream aggregation table (ANALYTICS_DATASCIENCE, 2,908 rows)
- <!-- TODO: confirm if Hex dashboards or other consumers exist -->

## Joining to apollo_team_id

`GTME_CALLS_AI_ANALYSIS` has no `apollo_team_id` column. **Verified pattern (2026-03-20, DEVELOPER_ROLE, 97.6% match rate on 500-call sample):**

```sql
WITH gtme_participants AS (
    SELECT
        f.CONVERSATION_ID,
        p.value:contact_id."$oid"::string AS contact_id
    FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS f,
         LATERAL FLATTEN(input => f.CONVERSATION_PARTICIPANTS) p
    WHERE f.CONVERSATION_ID IN (SELECT CONVERSATION_ID FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS)
      AND p.value:contact_id."$oid"::string IS NOT NULL
)
SELECT
    g.*,
    c.APOLLO_TEAM_ID
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS g
JOIN gtme_participants p   ON p.CONVERSATION_ID = g.CONVERSATION_ID
JOIN ANALYTICS_DB.ANALYTICS.INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS c
                           ON c.CONTACT_ID = p.contact_id
WHERE c.APOLLO_TEAM_ID IS NOT NULL
```

**Join chain:** `GTME_CALLS_AI_ANALYSIS` → `FCT_MONGO_CONVERSATIONS` (flatten `CONVERSATION_PARTICIPANTS`) → `INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS` (via `contact_id`) → `APOLLO_TEAM_ID`

**Note:** This is DIFFERENT from the HVO pattern. HVO uses `ONBOARDING_HIGH_VELOCITY_TEAMS.CALENDAR_EVENT_IDS` as the bridge. GTME calendar events do NOT appear in that table (0% match tested). GTME must go through participants.

**Do NOT use:**
- `FCT_MONGO_CONVERSATIONS.TEAM_ID` — this is the Apollo rep's team, not the customer's
- `ONBOARDING_HIGH_VELOCITY_TEAMS` as bridge for GTME — 0% match, HVO-specific table only

## Related Tables

| Table | Relationship |
|---|---|
| `HVO_CALLS_AI_PROCESSING` | Sister table — same pipeline, covers onboarding calls instead of GTME calls |
| `WEEKLY_TEAM_SIGNALS_FROM_GTME_CALLS` | Downstream — weekly team-level signals derived from this table |
| `WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS` | Downstream — parallel HVO signals table |

## Known Issues & Gotchas

- **TRANSCRIPT and PROMPT columns are large** — always specify columns, never `SELECT *`
- **AI-generated data quality varies** — cross-check high-stakes outputs (CHURN_RISK_SCORE, UPSELL_DETECTED) with quantitative signals before acting
- **Row count is small (~2,362)** compared to HVO (~26K) — GTME call volume is naturally lower; this is expected
- **INTERVENTIONS_DISCUSSED has no column comment** — meaning TBD

## Business Terms

| Term | Definition |
|---|---|
| GTME | Go-To-Market Engineer — Apollo's account ownership role (equivalent to CSM) |
| DAPI | Internal AI batch processing API used for LLM inference at scale |
| Decision engine | Post-processing logic that converts raw AI outputs into final action recommendations using SLA rules |
| Churn risk score | 0–5 LLM-assigned score: 0=unknown, 1=very low, 5=very high churn risk |
| Upsell detected | Strictly defined: seat expansion, addon credits, Inbound add, Dialer add, or monthly→annual upgrade only |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file | Leo (via Claude) |
