# DIM_USERS

> Data Science user dimension. Enriched user-level attributes for product analytics.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS` |
| **Grain** | One row per Apollo user (`APOLLO_USER_ID`) |
| **Row count** | ~15.3M (2026-03-06) |
| **Refresh cadence** | Daily (owned by Data Science) |
| **Trust level** | Use with caution (ANALYTICS_DATASCIENCE — DS-maintained) |
| **Owner** | Data Science (Shyam SK) |
| **DAG** | Not found in airflow-dags. Likely a dbt model in DS project. |

## Description

DS-enriched user dimension (41 distinct users). Downstream of DIM_MONGO_USERS with additional attributes like activation flags, persona classification, and SF account linkage. Used for user-level product analytics, activation tracking, and filtering.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_MONGO_USERS | Primary source (user attributes from Mongo) |
| DIM_SALESFORCE_ACCOUNTS | SF account fields (IS_CORE_ACCOUNT_IND) |
| Amplitude | Country, activity data |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| APOLLO_USER_ID | TEXT | 39 | 18,331 | User ID | **Primary key.** FK to DIM_MONGO_USERS.USER_ID |
| APOLLO_TEAM_ID | TEXT | 33 | 14,267 | Team ID | FK to DIM_TEAMS, DIM_MONGO_TEAMS |
| EMAIL | TEXT | 31 | 3,736 | User email | |
| APOLLO_USER_CREATED_DATE | DATE | 29 | 7,076 | User signup date | |
| PRIMARY_PERSONA | TEXT | 28 | 3,504 | User persona classification | e.g. Sales, Marketing, RevOps |
| AMPLITUDE_COUNTRY | TEXT | 28 | 3,400 | Country from Amplitude | |
| IS_FREE_EMAIL_DOMAIN_IND | BOOLEAN | 26 | 7,520 | Free email domain flag | |
| FIRST_NAME | TEXT | 26 | 3,062 | | |
| LAST_NAME | TEXT | 26 | 3,061 | | |
| JOB_TITLE | TEXT | 26 | 2,920 | | |
| SFDC_ACCOUNT_ID | TEXT | 26 | 2,773 | SF account ID | |
| IS_CORE_ACCOUNT_IND | BOOLEAN | 25 | 8,281 | Core account flag | Standard exclusion filter |
| LAST_ACTIVE_DATE | DATE | 25 | 2,975 | Last activity | |
| IS_APOLLO_EMPLOYEE_IND | BOOLEAN | 24 | 7,372 | Internal employee flag | Filter out for external analysis |
| IS_USER_ENABLED_IND | BOOLEAN | 24 | 4,934 | User enabled/disabled | |
| HAS_IN_APP_ONBOARDING_GOAL_CRM | BOOLEAN | 24 | 4,909 | CRM onboarding goal set | Activation indicator |
| IS_PAID_IND | BOOLEAN | 24 | 4,387 | Paid user flag | |
| FIRST_PAID_DATE | DATE | 24 | 3,533 | First conversion date | |
| HAS_ADMIN_PERMISSIONS_IND | BOOLEAN | 24 | 3,137 | Admin permission flag | |
| WEBSITE_DOMAIN | TEXT | 24 | 3,066 | User's domain | |

## How It's Used

### Common query patterns
- **Activation analysis**: `IS_PAID_IND`, `FIRST_PAID_DATE`, onboarding goal columns
- **User segmentation**: `PRIMARY_PERSONA`, `IS_CORE_ACCOUNT_IND`, `IS_FREE_EMAIL_DOMAIN_IND`
- **Employee filtering**: `IS_APOLLO_EMPLOYEE_IND = FALSE` for external-only analysis
- **Null activity investigation**: Shyam SK queried for users with NULL `LAST_ACTIVE_DATE` and `FIRST_ACTIVE_DATE`

### Key consumers
- Data Science team (primary)
- Product Analytics
- Looker explores

## Known Issues & Gotchas

- Row count (15.3M) is ~3.6x DIM_MONGO_USERS (4.3M) — likely includes historical/deleted users or different dedup
- Owned by DS, not DE — schema changes go through DS team
- `IS_APOLLO_EMPLOYEE_IND` — always filter out for external-facing metrics
- Some users have NULL `LAST_ACTIVE_DATE` and `FIRST_ACTIVE_DATE` — never activated

## Slack Context

- **Feature activation expansion**: Catherine Zhou raised need for more activation columns (CSV enrichment, inbound, agentic outbound) — DS team controls schema (#dept-analytics)
- **Null active dates**: Shyam SK investigating users that never got activated (#dept-analytics)
- **Leo Liu weekly metrics**: Uses activation metrics from this and related tables for topline product analytics summary (#dept-analytics-updates)

## Business Terms

| Term | Definition |
|---|---|
| Primary Persona | User's self-selected role classification (Sales, Marketing, RevOps, etc.) |
| Activation | User completing key onboarding milestones (CRM, enrichment, etc.) |
| WAT | Weekly Active Teams — derived from user activity data |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history + Slack research | Brighid (via Claude) |
| 2026-03-23 | New API/MCP columns added by Shyam: `first/last_active_date_api_calls`, `active_days_api_calls`, `active_counts_api_calls` — 3 segments: overall API, Apollo-MCP, partner API calls. Now the preferred source for MCP adoption analytics at user grain. | Jarvis (via Shyam Slack) |
