# APOLLO_USERS

> Current-state user dimension with demographics, activity counts, onboarding goals, and feature adoption flags.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.APOLLO_USERS` |
| **Grain** | One row per APOLLO_USER_ID |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing (current snapshot) |
| **Trust level** | Standard — widely used in Looker |
| **Owner** | Analytics |

## Description

Wide user-level dimension table (140 columns) containing current-state user attributes: demographics, team linkage, persona classification, activity counts by feature, active-day counts, onboarding goal flags, and integration status. Used extensively by Looker dashboards (8,452 queries/14d). This is a current-snapshot table — no date dimension. For historical daily user state, use DIM_USERS_DAILY or DIM_ACTIVE_USERS_DAILY instead.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB user collection | Core user attributes |
| Amplitude | Activity counts (ACTIVE_COUNTS_*, ACTIVE_DAYS_*) |
| SFDC | SFDC_CONTACT_ID, SFDC_TEAM_ID, SFDC_ACCOUNT_ID |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| APOLLO_USER_ID | TEXT | Primary key | |
| APOLLO_TEAM_ID | TEXT | Team the user belongs to | Join to DIM_TEAMS_DAILY |
| SFDC_CONTACT_ID | TEXT | Salesforce contact ID | |
| SFDC_TEAM_ID | TEXT | Salesforce team/account ID | |
| EMAIL | TEXT | User email address | |
| PRIMARY_PERSONA | TEXT | User's primary persona classification | |
| SENIORITY | TEXT | Seniority level | |
| IS_ACTIVE_L1 | BOOLEAN | Active in last 1 day | |
| IS_ACTIVE_L7 | BOOLEAN | Active in last 7 days | |
| IS_ACTIVE_L28 | BOOLEAN | Active in last 28 days | |
| ACTIVE_COUNTS_* | NUMBER/FLOAT | ~40 columns of feature-level activity counts | Current rolling window |
| ACTIVE_DAYS_* | NUMBER | ~40 columns of active-day counts by feature | Current rolling window |
| HAS_IN_APP_ONBOARDING_GOAL_* | BOOLEAN | ~10 onboarding goal flags | |
| IN_APP_ONBOARDING_GOALS | ARRAY | Array of selected onboarding goals | VARIANT — use LATERAL FLATTEN |

## How It's Used

### Common query patterns

- Looker user-level dashboards (8,452 queries/14d)
- User segmentation by persona, seniority, activity level
- Feature adoption analysis (ACTIVE_COUNTS_* columns)
- Onboarding funnel analysis

### Key consumers

- Looker dashboards (primary consumer)
- Product analytics team
- Growth/activation analyses

## Known Issues & Gotchas

- **Current snapshot only** — no date dimension. Cannot do historical lookback. Use DIM_USERS_DAILY or DIM_ACTIVE_USERS_DAILY for time-series analysis.
- 140 columns — avoid SELECT *
- ACTIVE_COUNTS columns mix NUMBER and FLOAT types — watch for precision in comparisons
- IN_APP_ONBOARDING_GOALS is ARRAY type — use LATERAL FLATTEN to query individual goals
- PAGE_VIEWS columns are not present in this table (they are in DIM_ACTIVE_USERS_DAILY)

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
