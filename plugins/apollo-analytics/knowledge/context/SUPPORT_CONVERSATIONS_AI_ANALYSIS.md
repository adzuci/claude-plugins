# SUPPORT_CONVERSATIONS_AI_ANALYSIS

> AI-extracted insights from support conversations — sentiment, churn signals, upsell opportunities, action recommendations, and issue categorization.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.SUPPORT_CONVERSATIONS_AI_ANALYSIS` |
| **Grain** | One row per conversation (CONVERSATION_ID) |
| **Refresh cadence** | Daily (batch AI processing) |
| **Coverage period** | Ongoing |
| **Trust level** | Use with caution — AI-generated fields, accuracy varies by column |
| **Owner** | Data Platform (Marie Ballenger primary consumer) |

## Description

AI analysis layer on top of support conversations. Each row represents one support conversation with AI-extracted fields including: aha moments, pain points, upsell opportunities, churn signals, sentiment, technical sufficiency scores, competitor mentions, and recommended next actions. Used by the Support analytics team and the AI Transformation Squad to understand support quality, identify at-risk accounts, and prioritize follow-ups.

Joins to `DIM_SUPPORT_CONVERSATIONS` on `CONVERSATION_ID` for conversation metadata (team, dates, channel).

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_SUPPORT_CONVERSATIONS | Parent conversation metadata (join on CONVERSATION_ID) |
| AI/LLM pipeline (DAPI) | Generates the analysis fields from conversation transcripts |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT | Primary key — links to DIM_SUPPORT_CONVERSATIONS | NOT NULL |
| APOLLO_TEAM_ID | TEXT | Team ID for joins to DIM_TEAMS_DAILY / LU_TEAM_ATTRIBUTES | |
| SENTIMENT | TEXT | AI-classified sentiment of the conversation | |
| HAS_CHURN_POTENTIAL | BOOLEAN | AI flag: does this conversation signal churn risk? | |
| CHURN_REASON | TEXT | AI explanation of why churn was flagged | |
| UPSELL_OPPORTUNITY | BOOLEAN | AI flag: upsell potential detected | |
| AHA_MOMENT | TEXT | Key "aha" moment the customer experienced | |
| PAIN_POINT | TEXT | Primary pain point identified | |
| IS_CREDITS_RELATED | TEXT | Whether the conversation involves credit issues | Text field, not boolean |
| IS_BILLING_RELATED | TEXT | Whether the conversation involves billing | Text field, not boolean |
| CUSTOMER_TECHNICAL_SUFFICIENCY_SCORE | NUMBER | AI score (0-10?) of customer's technical capability | |
| COMPETITOR_USERS_USED_BEFORE | VARIANT | Array of competitor products mentioned | |
| NEXT_ACTION_TYPE_FINAL | TEXT | Recommended action type (resolved vs needs follow-up) | |
| ACTION_TEAM | TEXT | Which team should take the next action | |
| HAS_ADOPTION_BLOCKERS | BOOLEAN | AI flag: customer has adoption blockers | |
| ISSUES_SOLVED | BOOLEAN | Whether the conversation resolved the customer's issues | |
| ISSUES_UNRESOLVED | VARIANT | Array of unresolved issues | |
| MODEL_VERSION | TEXT | Which AI model version generated this analysis | |

## How It's Used

### Common query patterns

- Join to DIM_SUPPORT_CONVERSATIONS + DIM_TEAMS_DAILY for segment-level support quality analysis
- Filter on HAS_CHURN_POTENTIAL = TRUE for churn signal pipeline
- Aggregate SENTIMENT by segment/time for support quality trends
- Filter IS_CREDITS_RELATED for credit-related support volume

### Key consumers

- Marie Ballenger (Support analytics — 158 queries in 14 days)
- AI Transformation Squad (Ashutosh Singh — Data Gap Track)
- Looker dashboards (252 queries via LOOKER_USER on DIM_SUPPORT_CONVERSATIONS)

## Known Issues & Gotchas

- IS_CREDITS_RELATED and IS_BILLING_RELATED are TEXT fields, not BOOLEAN — check actual values before filtering
- AI-generated fields have varying accuracy — use for directional analysis, not precise counts
- COMPETITOR_USERS_USED_BEFORE, AHA_FEATURES, CLIENT_ROLES, KEY_SENTIMENT_PHRASES, ISSUE_PERCENT_OF_TIME, ISSUES_UNRESOLVED, ISSUE_RESPONSIBILITY, ISSUE_BUCKET_PERCENT_OF_TIME are VARIANT (JSON arrays) — use LATERAL FLATTEN to query
- TRANSCRIPT column contains full conversation text — large column, exclude from SELECT * queries
- PROMPT column contains the AI prompt used — useful for auditing but large

## Slack Context

- 2026-04-08: AI Transformation Squad scoping "minimum read-only account state surfaces" — this table is a key dependency
- 2026-04-08: Ashutosh Singh identified ~17% of Fin escalations due to missing account state, driving urgency for this table's availability

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
