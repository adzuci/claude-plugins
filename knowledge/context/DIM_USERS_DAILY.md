# DIM_USERS_DAILY

> Daily snapshot of user-level metrics. One row per user per day.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS_DAILY` |
| **Grain** | One row per user + date (`APOLLO_USER_ID` + `DATE`) |
| **Row count** | ~10.2B (2026-03-06) — extremely large table, always filter by DATE |
| **Refresh cadence** | Daily incremental (owned by Data Science) |
| **Trust level** | Use with caution (ANALYTICS_DATASCIENCE — DS-maintained) |
| **Owner** | Data Science (Shyam SK) |
| **DAG** | Not found in airflow-dags. Likely a dbt model in DS project. |

## Description

Daily user snapshot (32 distinct users). User-level equivalent of DIM_TEAMS_DAILY — contains per-user feature engagement counts at L1/L7/L28 windows. Used for user activation, retention analysis, and feature adoption tracking.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_USERS | User attributes |
| Activity/event tables | Daily feature usage rollups |
| DIM_TEAMS_DAILY | Team-level context |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| DATE | DATE | 32 | 21,292 | Snapshot date | **Part of PK.** Always filter. |
| APOLLO_USER_ID | TEXT | 30 | 15,412 | User ID | **Part of PK.** FK to DIM_USERS |
| APOLLO_TEAM_ID | TEXT | 28 | 12,427 | Team ID | FK to DIM_TEAMS |
| IS_ACTIVE_L1 | BOOLEAN | 25 | 4,209 | Active in last 1 day | |
| ENRICHMENT_WATERFALL_COUNTS_L1 | NUMBER | 24 | 3,763 | Waterfall enrichment count (1d) | |
| MEETING_BOOKED_COUNTS_L1 | NUMBER | 23 | 3,248 | Meetings booked (1d) | |
| ENRICHMENT_CRM_LIVING_DATA_COUNTS_L1 | NUMBER | 23 | 2,692 | CRM enrichment (1d) | |
| ENRICHMENT_WATERFALL_COUNTS_L7 | NUMBER | 23 | 2,593 | Waterfall enrichment (7d) | |
| ENRICHMENT_CSV_COUNTS_L1 | NUMBER | 23 | 2,182 | CSV enrichment (1d) | |
| ENRICHMENT_API_COUNTS_L1 | NUMBER | 23 | 2,128 | API enrichment (1d) | |
| IS_PAID_IND | BOOLEAN | 22 | 15,583 | Paid user flag | |
| WIN_CLOSE_MEETING_ASSISTANT_COUNTS_L1 | NUMBER | 22 | 2,834 | Meeting assistant (1d) | |
| GENPIPE_NEXTGEN_DIY_COUNTS_L1 | NUMBER | 22 | 2,467 | GenPipe nextgen DIY (1d) | |
| GENPIPE_TRADITIONAL_COUNTS_L1 | NUMBER | 22 | 2,111 | GenPipe traditional (1d) | |
| EMAIL_SENT_COUNTS_OUTREACH_AUTOMATIC_L1 | NUMBER | 21 | 3,566 | Auto outreach emails (1d) | |
| IS_APOLLO_EMPLOYEE_IND | BOOLEAN | 21 | 3,255 | Employee filter | Always exclude for external metrics |

## How It's Used

### Common query patterns
- **User activation tracking**: Feature-level engagement by user over time
- **Retention cohorts**: Daily activity patterns, L7/L28 lookback
- **Feature adoption**: Per-feature counts (enrichment, meetings, email, genpipe)

### Key consumers
- Data Science (primary)
- Product Analytics
- Looker dashboards

## Known Issues & Gotchas

- **Extremely large** (~10.2B rows) — ALWAYS filter by DATE
- Same genpipe interest bug as DIM_TEAMS_DAILY (15% under-reporting traditional, 34% nextgen)
- Incremental build — schema changes require backfill
- Filter `IS_APOLLO_EMPLOYEE_IND = FALSE` for external-facing metrics

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
