# DIM_SALESFORCE_USERS

> Salesforce internal user dimension. One row per SF user (Apollo employees/reps).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_USERS` |
| **Grain** | One row per Salesforce User (`ID`) |
| **Row count** | ~820 (2026-03-06) — tiny reference table |
| **Refresh cadence** | Unknown — not in airflow-dags. Likely Salesforce integration. |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | Sales Ops / Analytics |
| **DAG** | Not found in airflow-dags. Likely Salesforce integration or dbt. |

## Key Columns

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| ID | TEXT | 22 | 35,449 | SF User ID | **PK.** FK from DIM_SALESFORCE_ACCOUNTS.OWNER_ID, OPPORTUNITIES.OWNER_ID |
| NAME | TEXT | 21 | 34,003 | User full name | Rep/GTME name for dashboards |
| EMAIL | TEXT | 13 | 646 | | |
| POSITION_C | TEXT | 11 | 4,526 | Custom position field | |
| MANAGER_ID | TEXT | 8 | 9,643 | Manager hierarchy | FK to self (DIM_SALESFORCE_USERS.ID) |
| USER_ROLE_NAME | TEXT | 8 | 1,028 | SF role | |
| IS_ACTIVE | BOOLEAN | 6 | 4,141 | Active user flag | |

## Known Issues & Gotchas

- Only ~820 rows (internal Apollo employees in SF)
- ID and NAME dominate usage — this is primarily a lookup for account/opportunity owner names
- High query count (35K) despite low user count — dashboard-driven joins

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file | Brighid (via Claude) |
