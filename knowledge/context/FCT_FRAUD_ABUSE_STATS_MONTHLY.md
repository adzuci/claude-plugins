# FCT_FRAUD_ABUSE_STATS_MONTHLY

> Monthly fraud and abuse statistics by team cohort — fraud chargebacks, abuse value, and abuse percentages.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_FRAUD.FCT_FRAUD_ABUSE_STATS_MONTHLY` |
| **Grain** | One row per IS_CORE_ACCOUNT x IS_PAYING x TEAM_CREATED_MONTH x METRIC |
| **Refresh cadence** | Monthly |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative for fraud metrics |
| **Owner** | Fraud Analytics |

## Description

Monthly aggregated fraud and abuse statistics. Pivoted by metric type — each row represents one metric for a cohort defined by core/paying status and team creation month. Tracks fraud chargeback values, abuse values, non-abuse values, totals, and abuse percentages. Used by Fraud analytics (715 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| Fraud detection pipeline | Computed from transaction and behavior data |
| Billing/Stripe | Chargeback data |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| IS_CORE_ACCOUNT | BOOLEAN | Whether this cohort is core accounts | |
| IS_PAYING | BOOLEAN | Whether this cohort is paying teams | |
| TEAM_CREATED_MONTH | DATE | Cohort month (team creation) | |
| TEAM_CREATED_DATE | DATE | Specific team creation date | |
| METRIC | TEXT | Which metric this row represents | Pivoted — each metric is a separate row |
| FRAUD_CHARGEBACK_VALUE | FLOAT | Dollar value of fraud chargebacks | |
| ABUSE_VALUE | FLOAT | Dollar value of abusive behavior | |
| NON_ABUSE_VALUE | FLOAT | Dollar value of non-abusive behavior | |
| TOTAL_VALUE | FLOAT | Total value (abuse + non-abuse) | |
| PCT_FRAUD_ABUSE | FLOAT | Percentage: abuse / total | |

## How It's Used

### Common query patterns

- Monthly fraud/abuse trend analysis
- Compare fraud rates across core vs non-core, paying vs free
- Cohort-level abuse rate tracking

### Key consumers

- Fraud Looker dashboards (715 queries/14d)
- Fraud analytics team

## Known Issues & Gotchas

- **Pivoted structure**: METRIC column determines what the row measures — filter on METRIC before aggregating
- FLOAT types on all value columns — watch for precision
- TEAM_CREATED_DATE alongside TEAM_CREATED_MONTH is ambiguous — clarify which grain you're using
- Monthly cadence means data may lag up to 30 days

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
