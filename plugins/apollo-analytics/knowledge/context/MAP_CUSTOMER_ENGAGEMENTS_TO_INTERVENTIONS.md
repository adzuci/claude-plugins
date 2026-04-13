# MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS

> Junction table linking Customer Engagement records to Customer Interventions
> — required to join `SALESFORCE_CUSTOMER_ENGAGEMENTS` to `INTERVENTIONS`.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS` |
| **dbt model** | `map_customer_engagements_to_interventions` (view) |
| **Staging model** | `stg_salesforce__customer_engagement_interventions` |
| **Grain** | One row per Customer Engagement Intervention junction record (`CUSTOMER_ENGAGEMENT_INTERVENTION_ID`) |
| **Refresh cadence** | Analytics daily run, 2x per day |
| **Trust level** | Authoritative — direct Fivetran sync via staging model |
| **Owner** | Kaitlyn Maglietto (Analytics Engineering) |
| **Tags** | gold, salesforce, looker |

## Description

View aliased from `map_customer_engagements_to_interventions`. This is the
Salesforce junction object that links Customer Engagements to Customer
Interventions — a many-to-many bridge. One intervention can have multiple
engagement calls; one engagement can be linked to multiple interventions
and one intervention can have multiple engagements.

Joining through this table is the correct pattern, but **the join itself
produces fan-out by design**: joining `INTERVENTIONS → MAP → ENGAGEMENTS`
returns one row per engagement per intervention. It is strongly advised to
aggregate customer engagement data when making this join — e.g. use
`COUNT(DISTINCT CUSTOMER_ENGAGEMENT_ID)` or aggregate sentiment/call data.
For most intervention-level engagement counts, `TOTAL_ENGAGEMENT_CALLS` in
`INTERVENTIONS` is pre-aggregated and is the right field to use.

## Upstream Sources

| Source | Relationship |
|---|---|
| `stg_salesforce__customer_engagement_interventions` | Direct upstream — Fivetran sync of SFDC junction object |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `CUSTOMER_ENGAGEMENT_INTERVENTION_ID` | TEXT | Primary key — Salesforce junction record ID | |
| `CUSTOMER_ENGAGEMENT_INTERVENTION_NAME` | TEXT | Auto-generated name for the junction record | |
| `CUSTOMER_ENGAGEMENT_ID` | TEXT | FK to `SALESFORCE_CUSTOMER_ENGAGEMENTS` | Join key |
| `SFDC_INTERVENTION_ID` | TEXT | FK to `SALESFORCE__CUSTOMER_INTERVENTIONS` / `INTERVENTIONS` | Join key |
| `SFDC_TEAM_ID` | TEXT | Salesforce Apollo Team ID | Not the same as `APOLLO_TEAM_ID` |
| `OWNER_ID` | TEXT | Salesforce User that owns this record | |
| `SFDC_INTERVENTION_STATUS` | TEXT | Denormalized status of the parent intervention | Use `INTERVENTIONS.INTERVENTION_STATUS` for canonical status |
| `INTERVENTION_DISPOSITION_DETAILS` | TEXT | Free-text disposition detail from the parent intervention | |
| `CUSTOMER_ENGAGEMENT_INTERVENTION_CREATED_AT_UTC` | TIMESTAMP_NTZ | Record creation timestamp | |
| `CUSTOMER_ENGAGEMENT_INTERVENTION_LAST_MODIFIED_AT_UTC` | TIMESTAMP_NTZ | Last modified timestamp | |
| `LAST_ACTIVITY_DATE` | DATE | Most recent activity date on this record | |

## How It's Used

### Common query patterns

```sql
-- Correct join pattern: interventions → map → engagements, aggregates customer engagement information

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
WHERE 1 = 1
  AND INTERVENTIONS.IS_ACTIONABLE = TRUE;

-- Count positive engagements per intervention
SELECT
    INTERVENTIONS.APOLLO_TEAM_ID
    , INTERVENTIONS.INTERVENTION_NAME
    , INTERVENTIONS.INTERVENTION_PILLAR
    , INTERVENTIONS.TOTAL_ENGAGEMENT_CALLS
    , COUNT_IF(SALESFORCE_CUSTOMER_ENGAGEMENTS.SENTIMENT = 'Positive') AS POSITIVE_ENGAGEMENTS
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS
JOIN ANALYTICS_DB.ANALYTICS.MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS
    ON INTERVENTIONS.SFDC_INTERVENTION_ID = MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS.SFDC_INTERVENTION_ID
JOIN ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_ENGAGEMENTS
    ON MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS.CUSTOMER_ENGAGEMENT_ID = SALESFORCE_CUSTOMER_ENGAGEMENTS.CUSTOMER_ENGAGEMENT_ID
WHERE 1 = 1
GROUP BY 1,2,3,4;


```

### Key consumers

- Any query joining `SALESFORCE_CUSTOMER_ENGAGEMENTS` to `INTERVENTIONS`
- `TOTAL_ENGAGEMENT_CALLS` in `INTERVENTIONS` is sourced via this junction

## Known Issues & Gotchas

- **The join through this table fans out by design** — one intervention links
  to many engagements, so `INTERVENTIONS → MAP → ENGAGEMENTS` returns multiple
  rows per intervention. Always aggregate customer engagement data when making
  this join. Use `COUNT(DISTINCT CUSTOMER_ENGAGEMENT_ID)` or aggregate
  sentiment/call fields before joining. Do not use `COUNT(*)` on the joined
  result for intervention-level metrics. For most cases, use the
  pre-aggregated `TOTAL_ENGAGEMENT_CALLS` in `INTERVENTIONS` instead.
- **`SFDC_TEAM_ID` ≠ `APOLLO_TEAM_ID`** — use `INTERVENTIONS.APOLLO_TEAM_ID`
  for team-level joins.
- **`SFDC_INTERVENTION_STATUS` is denormalized** — use
  `INTERVENTIONS.INTERVENTION_STATUS` for canonical statENGAGEMENTS.

## Related Tables

| Table | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_ENGAGEMENTS` | Child side — join on `CUSTOMER_ENGAGEMENT_ID` |
| `ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS` | Parent side — join on `SFDC_INTERVENTION_ID` |
| `stg_salesforce__customer_engagement_interventions` | Direct upstream staging model |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-06 | Created context file from dbt gold_interventions branch | Kaitlyn Maglietto |
