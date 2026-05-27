# SALESFORCE_CUSTOMER_ENGAGEMENTS

> View aliased from `dim_salesforce_customer_engagements` — one record per rep
> call or meeting tied to a customer intervention.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_ENGAGEMENTS` |
| **dbt model** | `dim_salesforce_customer_engagements` (view) |
| **Staging model** | `stg_salesforce__customer_engagements` |
| **Source** | `raw_fivetran_db.salesforce.customer_engagement_c` |
| **Grain** | One row per Customer Engagement record (`CUSTOMER_ENGAGEMENT_ID`) |
| **Refresh cadence** | Analytics daily run, 2x per day |
| **Trust level** | Authoritative for rep-entered engagement data |
| **Owner** | Kaitlyn Maglietto (Analytics Engineering) |
| **Tags** | gold, salesforce, looker |

## Description

View aliased from `dim_salesforce_customer_engagements`, which selects from
`stg_salesforce__customer_engagements`. Soft-deleted records are filtered out
in staging — this table only contains live records. Each row represents a
single customer engagement touchpoint (call or meeting) conducted as part of a
customer intervention, capturing stage, sentiment, meeting notes, next steps,
and the parent intervention it belongs to. It is the call-level detail that
rolls up to `TOTAL_ENGAGEMENT_CALLS` in
`ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS`. Use this table when you
need per-engagement detail.

## Upstream Sources

| Source | Relationship |
|---|---|
| `stg_salesforce__customer_engagements` | Direct upstream — handles Fivetran sync + deletion filtering |
| Customer Intervention object (`SFDC_INTERVENTION_ID`) | Parent FK — each engagement belongs to one intervention |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `CUSTOMER_ENGAGEMENT_ID` | TEXT | Primary key — Salesforce record ID | 18-char SFDC ID, NOT NULL, unique |
| `CUSTOMER_ENGAGEMENT_NAME` | TEXT | Auto-generated or user-defined record name | |
| `SFDC_INTERVENTION_ID` | TEXT | FK to parent Customer Intervention | |
| `SFDC_ACCOUNT_ID` | TEXT | Salesforce Account ID | |
| `SFDC_TEAM_ID` | TEXT | Salesforce Apollo Team ID | Not the same as `APOLLO_TEAM_ID` |
| `OWNER_ID` | TEXT | Salesforce User that owns this record | |
| `CUSTOMER_ENGAGEMENT_STAGE` | TEXT | Stage of the engagement | Values: Scheduled, In Progress, Completed |
| `INTERVENTION_STATUS` | TEXT | Status of the parent intervention | Denormalized — use `INTERVENTIONS.INTERVENTION_STATUS` for canonical status |
| `INTERVENTION_TYPES` | TEXT | Type(s) of intervention applied | e.g., Health Check, QBR, Training |
| `MEETING_TYPE` | TEXT | Meeting format | e.g., Call, Video, In-Person |
| `CONVERSATION_SOURCE` | TEXT | Links to source conversation record | Gong, ZoomIQ, Chorus, etc. |
| `APOLLO_CONVERSATION_SOURCE` | TEXT | URL to the Apollo Conversation | |
| `SENTIMENT` | TEXT | Customer sentiment recorded by rep | Values: Positive, Neutral, Negative, Concerned |
| `SENTIMENT_DETAILS` | TEXT | Free-text sentiment context | Avoid in large aggregations |
| `MEETING_NOTES` | TEXT | Free-text meeting notes | Avoid in large aggregations |
| `CALL_NEXT_STEPS` | TEXT | Agreed next steps post-engagement | Avoid in large aggregations |
| `CALL_AT` | TIMESTAMP_NTZ | Scheduled/actual call datetime | |
| `COMPLETED_AT` | TIMESTAMP_NTZ | When engagement was marked complete | |
| `CUSTOMER_ENGAGEMENT_CREATED_AT` | TIMESTAMP_NTZ | Record creation timestamp in SFDC | |
| `CUSTOMER_ENGAGEMENT_LAST_MODIFIED_AT` | TIMESTAMP_NTZ | Last modified timestamp in SFDC | |
| `LAST_ACTIVITY_DATE` | DATE | Most recent activity date on this record | Most recent of: latest event due date or latest closed task due date |

## How It's Used

### Common query patterns

```sql
-- Engagement calls per intervention with sentiment breakdown
SELECT
    SFDC_INTERVENTION_ID
    , COUNT(*) AS total_engagements
    , COUNT_IF(SENTIMENT = 'Positive')  AS positive
    , COUNT_IF(SENTIMENT = 'Neutral')   AS neutral
    , COUNT_IF(SENTIMENT = 'Negative')  AS negative
    , COUNT_IF(SENTIMENT = 'Concerned') AS concerned
FROM ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_ENGAGEMENTS
WHERE 1 = 1
  AND CUSTOMER_ENGAGEMENT_STAGE = 'Completed'
GROUP BY 1;

-- Join engagements to intervention pipeline for full context of sentiment on actionable interventions
SELECT
    INTERVENTIONS.APOLLO_TEAM_ID
    , INTERVENTIONS.INTERVENTION_NAME
    , INTERVENTIONS.INTERVENTION_PILLAR
    , INTERVENTIONS.TOTAL_ENGAGEMENT_CALLS
    , ARRAY_AGG(SALESFORCE_CUSTOMER_ENGAGEMENTS.SENTIMENT) OVER (ORDER BY SALESFORCE_CUSTOMER_ENGAGEMENTS.CALL_AT) AS SENTIMENT_HISTORY
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS
JOIN ANALYTICS_DB.ANALYTICS.MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS
    ON INTERVENTIONS.SFDC_INTERVENTION_ID = MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS.SFDC_INTERVENTION_ID
JOIN ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_ENGAGEMENTS
    ON MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS.CUSTOMER_ENGAGEMENT_ID = SALESFORCE_CUSTOMER_ENGAGEMENTS.CUSTOMER_ENGAGEMENT_ID
WHERE INTERVENTIONS.IS_ACTIONABLE = TRUE;
```

### Key consumers

- `ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS` —
  `TOTAL_ENGAGEMENT_CALLS` aggregates from this table via the SFDC Customer
  Engagement Intervention junction object. This should be accessed via
  `MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS` table.
- Intervention coverage reporting, rep engagement rate analysis

## Known Issues & Gotchas

- **No deletion flags** — soft-delete filtering (`IS_DELETED`, `_FIVETRAN_DELETED`)
  is applied in `stg_salesforce__customer_engagements`. Do not add these filters
  when querying this table — the columns are not present.
- **Joining to INTERVENTIONS fans out** — use
  `MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS` as the bridge, and always
  aggregate engagement data (sentiment, call counts) before or after the join.
  Do not use `COUNT(*)` on the joined result for intervention-level metrics.
  One intervention can have many engagements.
- **`SFDC_TEAM_ID` ≠ `APOLLO_TEAM_ID`** — to join to Apollo team tables, go
  through `INTERVENTIONS` or `DIM_SALESFORCE_APOLLO_TEAMS`.
- **No direct `APOLLO_TEAM_ID`** — route joins through the intervention pipeline
  or Salesforce dimension tables.
- **Free-text fields** — `MEETING_NOTES`, `SENTIMENT_DETAILS`, and
  `CALL_NEXT_STEPS` are large. Don't scan in aggregations.
- **`SENTIMENT` has 4 values** — Positive, Neutral, Negative, and Concerned.
  Concerned is a separate escalation signal, distinct from Negative.
- **`INTERVENTION_STATUS` is denormalized** — reflects parent status at last
  sync. Use `INTERVENTIONS.INTERVENTION_STATUS` for canonical state.

## Business Terms

| Term | Definition |
|---|---|
| Customer Engagement | A single rep call or meeting conducted as part of a customer intervention. Child object of Customer Intervention in Salesforce. |
| Engagement Stage | Lifecycle state of the engagement: Scheduled → In Progress → Completed |
| Intervention Types | Category of activity in the engagement (Health Check, QBR, Training, etc.) |
| Concerned | Sentiment value indicating a customer expressing worry or dissatisfaction — distinct from Negative |

## Related Tables

| Table | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS` | Parent intervention pipeline — `TOTAL_ENGAGEMENT_CALLS` rolls up from here |
| `stg_salesforce__customer_engagements` | Direct upstream staging model |
| `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS` | Bridge to get `APOLLO_TEAM_ID` from `SFDC_TEAM_ID` |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-06 | Created context file | Kaitlyn Maglietto |
