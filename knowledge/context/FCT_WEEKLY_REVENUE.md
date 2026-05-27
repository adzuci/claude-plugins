# FCT_WEEKLY_REVENUE

> Weekly-grain revenue table with ARR by sales motion, churn tracking, and retention metrics per team.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_WEEKLY_REVENUE` |
| **Grain** | One row per APOLLO_TEAM_ID x DATE_PERIOD (weekly) |
| **Refresh cadence** | Weekly |
| **Coverage period** | Historical (ongoing) |
| **Trust level** | Standard — Looker revenue dashboards |
| **Owner** | Analytics / Finance |

## Description

Weekly-grain revenue table structurally similar to FCT_DAILY_REVENUE but at weekly granularity. Tracks ARR/MRR broken out by sales motion (self-serve, sales-assisted, rep-driven, labs), churn dates, retention metrics, and period-over-period changes. Used by Looker (882 queries/14d).

**IMPORTANT:** Same parent-account filter gotcha as FCT_DAILY_REVENUE — must filter `IS_PARENT_ACCOUNT = FALSE` for correct team-level ARR sums.

## Upstream Sources

| Source | Relationship |
|---|---|
| FCT_DAILY_REVENUE | Weekly aggregation of daily revenue data |
| Billing / Stripe | Ultimate revenue source |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DATE_PERIOD | DATE | Weekly period date | |
| APOLLO_TEAM_ID | TEXT | Team ID | Join to DIM_TEAMS_DAILY |
| SFDC_TEAM_OR_ACCOUNT_ID | TEXT | SFDC account linkage | |
| IS_PARENT_ACCOUNT | BOOLEAN | Parent account flag | **MUST filter FALSE for team-level sums** |
| ARR | FLOAT | Total ARR | |
| ARR_SS | FLOAT | Self-serve ARR | |
| ARR_SA | FLOAT | Sales-assisted ARR | |
| ARR_REP | FLOAT | Rep-driven ARR | |
| ARR_LABS | FLOAT | Labs ARR | |
| MRR / MRR_SS / MRR_SA / MRR_REP / MRR_LABS | FLOAT | Monthly recurring revenue by motion | |
| CHANGE_CATEGORY | TEXT | Week-over-week change type | new, expansion, contraction, churn, etc. |
| ARR_CHANGE | FLOAT | ARR delta from previous period | |
| IS_ACTIVE | BOOLEAN | Whether the team has active revenue | |
| SUBSCRIPTION_PERIOD | TEXT | Current subscription billing period | |

## How It's Used

### Common query patterns

- Weekly revenue trends by segment/motion
- Cohort retention analysis at weekly grain
- Churn tracking (MOST_RECENT_CHURN_DATE, TOTAL_TIMES_CHURNED_*)
- Period-over-period ARR change analysis

### Key consumers

- Looker dashboards (882 queries in 14 days)
- Finance / RevOps weekly reporting

## Known Issues & Gotchas

- **IS_PARENT_ACCOUNT = FALSE is mandatory** for team-level ARR sums — same as FCT_DAILY_REVENUE
- FLOAT type on all revenue columns — watch for precision
- For daily grain, use FCT_DAILY_REVENUE or FCT_TEAM_REVENUE_DAILY (Sep 2025+ preferred)
- DATE_PERIOD is weekly — do not try to use for daily-level analysis

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
