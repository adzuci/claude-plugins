# FCT_CANCELLATION_SURVEY_RESULTS

> Cancellation survey submissions from customers downgrading or cancelling their Apollo subscription. One row per survey submission.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_CANCELLATION_SURVEY_RESULTS` |
| **Grain** | One row per survey submission |
| **Row count** | <!-- TODO: query row count --> |
| **Refresh cadence** | Daily (assumed) |
| **Trust level** | High — ANALYTICS schema |
| **Owner** | Analytics |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Captures cancellation survey responses submitted by customers (self-serve) and termination reasons recorded by Apollo employees on behalf of customers. Two distinct flows feed this table: customer-facing survey (CANCELLATION_REASON / CANCELLATION_SUBREASON) and internal termination (TERMINATION_REASON / TERMINATION_REASON_DESCRIPTION). Use for churn reason analysis, cancellation trends, and retention strategy insights.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB (assumed) | Raw survey submissions loaded via LOAD_DATE |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CANCELLATION_SURVEY_ID | TEXT | Unique identifier per survey submission | Primary key |
| APOLLO_TEAM_ID | TEXT | Team that cancelled | Join to DIM_MONGO_TEAMS |
| SURVEY_SUBMISSION_CREATED_AT_UTC | TIMESTAMP_NTZ | When the survey was submitted | Use for time-series analysis |
| SURVEY_SUBMISSION_UPDATED_AT_UTC | TIMESTAMP_NTZ | Last update to the survey data | |
| CANCELLATION_SURVEY_JSON | VARIANT | Full JSON of survey responses | May need LATERAL FLATTEN or JSON extraction for additional fields |
| CANCELLATION_MODE | TEXT | Type of cancellation: `immediate` or `with_grace_period` | Only 2 known values as of Nov 2023 |
| CANCELLATION_REASON | TEXT | Customer-selected reason from dropdown | Primary churn reason field |
| CANCELLATION_SUBREASON | TEXT | More detailed reason (second step) | Optional — not always populated |
| TERMINATION_REASON | TEXT | Reason selected by Apollo employee | Internal cancellation flow |
| TERMINATION_REASON_DESCRIPTION | TEXT | Free-text context from Apollo employee | |
| LOAD_DATE | DATE | When results were loaded into MongoDB | |

## Common Query Patterns

```sql
-- Top cancellation reasons in last 90 days
SELECT
    CANCELLATION_REASON,
    COUNT(*) AS submissions,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 3) AS pct
FROM ANALYTICS_DB.ANALYTICS.FCT_CANCELLATION_SURVEY_RESULTS
WHERE SURVEY_SUBMISSION_CREATED_AT_UTC >= CURRENT_DATE - 90
    AND CANCELLATION_REASON IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC;
```

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_MONGO_TEAMS` | Join on APOLLO_TEAM_ID for team attributes |
| `FCT_MONTHLY_REVENUE` | Join on team for revenue context of churned accounts |
| `DIM_SALESFORCE_APOLLO_TEAMS` | Join for SF account context |

## Known Issues & Gotchas

- **Two cancellation flows** — customer self-serve (CANCELLATION_REASON) vs. employee-initiated (TERMINATION_REASON). Don't conflate them; filter appropriately.
- **CANCELLATION_SUBREASON is optional** — not always populated. Don't rely on it for complete coverage.
- **CANCELLATION_SURVEY_JSON is VARIANT** — full survey payload. May contain fields not broken out into dedicated columns.
- **CANCELLATION_MODE values** — only `immediate` and `with_grace_period` known as of Nov 2023. May have expanded since.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
