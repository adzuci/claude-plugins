# FCT_SALESFORCE_TASKS

> Salesforce Task objects — calls, emails, meetings, and other activities logged by reps.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_SALESFORCE_TASKS` |
| **Grain** | One row per Salesforce Task (ID) |
| **Row count** | ~TBD (large — all historical tasks) |
| **Refresh cadence** | Daily (Fivetran sync) |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative |
| **Owner** | Data Platform / Salesforce integration |
| **DAG** | Fivetran (not in Airflow) |

## Description

Salesforce Task objects representing activities logged by sales reps — calls, emails, meetings, to-dos. Each task has an OWNER_ID (the rep who owns it) and timestamps for creation, completion, and last modification. Used for measuring rep activity volume and engagement patterns.

## Upstream Sources

| Source | Relationship |
|---|---|
| Salesforce Task object | Direct Fivetran sync |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ID | TEXT | Primary key — Salesforce Task ID | |
| OWNER_ID | TEXT | Salesforce User ID of the task owner | Joins to DIM_SALESFORCE_USERS.ID |
| SUBJECT | TEXT | Task subject line | Contains call/email/meeting descriptions |
| STATUS | TEXT | Task status (Open, Completed, etc.) | |
| TASK_SUBTYPE | TEXT | Task type classification (Call, Email, etc.) | Key for activity type breakdown |
| CALL_DURATION_IN_SECONDS | NUMBER | Duration of calls | NULL for non-call tasks |
| ACTIVITY_AT | TIMESTAMP_NTZ | When the activity occurred | **Primary date filter** |
| CREATED_AT | TIMESTAMP_NTZ | When the task was created | |
| COMPLETED_AT | TIMESTAMP_NTZ | When the task was completed | NULL if still open |
| IS_DELETED | BOOLEAN | Soft-delete flag | Filter with IS_DELETED = FALSE |
| ACCOUNT_ID | TEXT | Related Salesforce Account ID | |

## How It's Used

### Common query patterns

- Rep activity volume by day/week (COUNT grouped by OWNER_ID + date)
- Activity type breakdown (GROUP BY TASK_SUBTYPE)
- Call duration analysis (AVG/SUM CALL_DURATION_IN_SECONDS)
- Join to DIM_SALESFORCE_USERS for rep name/email

### Key consumers

- Org health scanner (person_activity_scan.py)
- Sales activity dashboards

## Known Issues & Gotchas

- Always filter `IS_DELETED = FALSE` — deleted tasks remain in the table
- `OWNER_ID` joins to `DIM_SALESFORCE_USERS.ID`, not to Mongo or Darwinbox user IDs
- `CALL_DURATION_IN_SECONDS` is NULL for non-call tasks — don't average without filtering TASK_SUBTYPE
- Use `ACTIVITY_AT` for date filtering, not `SYSTEM_MODSTAMP` (which reflects last metadata change, not activity date)
- Fivetran-synced — no Airflow DAG. Schema changes won't show in Airflow config.
- Filter `u.NAME <> 'Marketo Sync'` when joining to DIM_SALESFORCE_USERS to exclude system accounts

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-06 | Created context file for scanner integration | Bridie Meredith |
