# DIM_ACTIVE_USERS_DAILY

> Daily user-level activity dimension from Data Science — 122 columns of feature usage counts, adoption flags, and user attributes per day.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_ACTIVE_USERS_DAILY` |
| **Grain** | One row per APOLLO_USER_ID x ACTIVITY_DATE |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Standard — Data Science maintained |
| **Owner** | Data Science |

## Description

Daily user-level activity dimension with 122 columns. For each user on each active day, tracks: feature-level usage counts (email, sequence, dialer, enrichment, extension, meetings, etc.), use-case flags (genpipe, win-close, enrichment), weekly activity status, login data, and user/account attributes. Used by DS team and Looker (672 queries/14d).

**Not the same as DIM_USERS_DAILY** — DIM_ACTIVE_USERS_DAILY is DS-owned, focuses on activity/usage, and lives in ANALYTICS_DATASCIENCE. DIM_USERS_DAILY is Analytics-owned and focuses on user attributes/state.

## Upstream Sources

| Source | Relationship |
|---|---|
| Amplitude events | Feature usage counts |
| MongoDB | User/account attributes |
| DIM_USERS_DAILY | Some user attributes |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| UNIQUE_ID | TEXT | Composite primary key | |
| APOLLO_USER_ID | TEXT | User ID | |
| ACTIVITY_DATE | DATE | The date of activity | |
| ACTIVITY_WEEK | DATE | Week start date | |
| APOLLO_TEAM_ID | TEXT | Team linkage | |
| IS_USER_ACTIVE | BOOLEAN | Whether user was active this day | |
| WEEKLY_STATUS | TEXT | Weekly retention status (new, retained, resurrected, churned) | |
| IS_CURRENT_WEEK_ACTIVE | BOOLEAN | Active in current week | |
| IS_PREVIOUS_WEEK_ACTIVE | BOOLEAN | Active in previous week | |
| *_COUNTS_L1 | NUMBER | Feature usage counts (last 1 day) | ~30 columns |
| HAS_*_USAGE_L1 | BOOLEAN | Feature usage boolean flags | |
| IS_USE_CASE_*_ACTIVE_L1 | NUMBER | Use case active flags | NUMBER (0/1), not BOOLEAN |
| TOTAL_ACTIVITY_COUNT | NUMBER | Sum of all activity | |
| SUBSCRIPTION | TEXT | User's subscription tier | |
| IS_PAID_IND | NUMBER | Paid user indicator | NUMBER (0/1) |
| IS_CORE_ACCOUNT_IND | NUMBER | Core account indicator | NUMBER (0/1) |

## How It's Used

### Common query patterns

- Daily/weekly active user counts by feature
- Feature adoption funnels (first usage → habit formation)
- Retention cohort analysis using WEEKLY_STATUS
- Use case penetration analysis

### Key consumers

- Data Science team (672 queries/14d)
- Looker product usage dashboards
- Activation/retention analyses

## Known Issues & Gotchas

- **122 columns** — never use SELECT *
- **_IND columns are NUMBER (0/1), not BOOLEAN** — use `= 1` not `= TRUE`
- **Distinct from DIM_USERS_DAILY** — different schema (ANALYTICS_DATASCIENCE vs ANALYTICS), different focus (activity vs attributes)
- PAGE_VIEWS_L1 is OBJECT type, FIRST_LOGIN_SOURCES is OBJECT — need special handling
- ONBOARDING_USE_CASES is VARIANT — use LATERAL FLATTEN
- PERSONAS_ARRAY is ARRAY type
- L1 suffix means "last 1 day" — activity counts for that specific date only

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
