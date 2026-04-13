# DIM_MONGO_USERS

> Core user dimension from MongoDB. One row per Apollo user.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_USERS` |
| **Grain** | One row per user (`_ID`) |
| **Row count** | ~4.3M (2026-03-06) |
| **Refresh cadence** | Daily (dbt_models_group_1). Has RT_VW variant: `DIM_MONGO_USERS_RT_VW` |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1` (dbt job 137019 / daily_ingestion_1 job 945826, model prefix `stg_mongo`, model `users`). Config: `dags/mongo/config/dbt_model_groups/dbt_model_groups.yml` |

## Description

Core user dimension (38 distinct users querying). Contains user profile, activity, and team membership from MongoDB. Has a real-time view variant. Commonly joined with DIM_MONGO_TEAMS via TEAM_ID.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `users` collection | Primary source |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| USER_ID | TEXT | 34 | 6,411 | User ID (MongoDB ObjectId) | **Primary key.** (Note: column name is USER_ID, not _ID) |
| TEAM_ID | TEXT | 32 | 4,948 | Team membership | **FK to DIM_MONGO_TEAMS.TEAM_ID** |
| EMAIL | TEXT | 28 | 3,358 | User email | |
| CREATED_AT_UTC | TIMESTAMP | 22 | 5,243 | Account creation | High query count — cohort analysis |
| LAST_NAME | TEXT | 21 | 432 | | |
| FIRST_NAME | TEXT | 21 | 366 | | |
| DELETED | BOOLEAN | 18 | 332 | Soft-delete flag | |
| ENABLE_OPEN_TRACKING | BOOLEAN | 18 | 226 | Open tracking setting | Email deliverability |
| ENABLE_CLICK_TRACKING | BOOLEAN | 18 | 226 | Click tracking setting | Email deliverability |
| SHOULD_INCLUDE_UNSUBSCRIBE_LINK | BOOLEAN | 18 | 226 | Unsubscribe link setting | Compliance |
| LAST_LOGGED_IN | TIMESTAMP | 17 | 306 | Last login timestamp | Activity metric |
| ACCOUNT_ACTIVATED | BOOLEAN | 16 | 4,467 | Activation status | High query count — activation funnel |
| CHROME_EXTENSION_DOWNLOADED | BOOLEAN | 16 | 463 | Extension adoption | Product adoption metric |
| HAS_EVER_LINKED_CRM | BOOLEAN | 16 | 463 | CRM integration flag | Product adoption metric |
| NUM_IN_APP_PRICING_PAGE_VISITS | NUMBER | 16 | 463 | Pricing page visits | Monetization signal |

## How It's Used

### Common query patterns
- Joined with DIM_MONGO_TEAMS via TEAM_ID for team-user analysis
- Used in CTE patterns by DA_TOOL_USER with date-range filters on UPDATED_AT/CREATED_AT
- Login attempt analysis: joined with `fct_mongo_login_attempts_rt_vw`
- Notes analysis: joined with `DIM_MONGO_NOTES_RT_VW` via USER_ID

### Key consumers
- DA_TOOL_USER (automated tooling — highest volume)
- Analyst ad-hoc queries

## Known Issues & Gotchas

- RT_VW variant is sometimes used instead of the base table
- Large table — queries often use broad date filters

## Slack Context

- **Activation funnel**: ACCOUNT_ACTIVATED (16 users, 4.5K queries) is a key activation metric. Combined with CHROME_EXTENSION_DOWNLOADED and HAS_EVER_LINKED_CRM for product adoption scoring.
- **DCS Scoreboard needs**: User-level activation metrics feed the "Adoption Health" section — % of new users performing search within 7 days, connecting mailbox, launching sequences.
- **Free-to-paid conversion**: NUM_IN_APP_PRICING_PAGE_VISITS is a monetization signal used to identify users near conversion. Brendan Walker looking at free user credit consumption pathways that lead to upgrades.
- **AI Assistant usage**: User-level activity tracked via DIM_MONGO_ASSISTANT_THREADS (joined on USER_ID). Spencer Avinger adding more analytics tracking for the Assistant.

## Business Terms

| Term | Definition |
|---|---|
| Apollo User | An individual user within an Apollo team |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
