# STG_SALESFORCE_EVENTS

> Salesforce Event objects — meetings, demos, and scheduled activities logged by reps.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.STG_SALESFORCE_EVENTS` |
| **Grain** | One row per Salesforce Event (ID) |
| **Row count** | ~TBD |
| **Refresh cadence** | Daily (Fivetran sync) |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative |
| **Owner** | Data Platform / Salesforce integration |
| **DAG** | Fivetran (not in Airflow) |

## Description

Salesforce Event objects representing scheduled activities — meetings, demos, calls with calendar entries. Unlike Tasks (which are to-dos and logged activities), Events have start/end times and duration. Each event has an OWNER_ID (the rep) and rich scheduling metadata.

## Upstream Sources

| Source | Relationship |
|---|---|
| Salesforce Event object | Direct Fivetran sync |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ID | TEXT | Primary key — Salesforce Event ID | |
| OWNER_ID | TEXT | Salesforce User ID of the event owner | Joins to DIM_SALESFORCE_USERS.ID |
| SUBJECT | TEXT | Event subject line | Contains meeting/demo descriptions |
| DURATION_IN_MINUTES | NUMBER | Event duration in minutes | |
| EVENT_SUBTYPE | TEXT | Event type classification | |
| ACTIVITY_AT | TIMESTAMP_NTZ | When the activity occurred | **Primary date filter** |
| STARTED_AT | TIMESTAMP_NTZ | Event start time | |
| ENDED_AT | TIMESTAMP_NTZ | Event end time | |
| CREATED_AT | TIMESTAMP_NTZ | When the event was created | |
| IS_DELETED | BOOLEAN | Soft-delete flag | Filter with IS_DELETED = FALSE |
| ACCOUNT_ID | TEXT | Related Salesforce Account ID | |

## How It's Used

### Common query patterns

- Meeting volume by rep/day/week (COUNT grouped by OWNER_ID + date)
- Meeting duration analysis (SUM/AVG DURATION_IN_MINUTES)
- Join to DIM_SALESFORCE_USERS for rep name/email

### Key consumers

- Org health scanner (person_activity_scan.py)
- Sales activity dashboards

## Known Issues & Gotchas

- Always filter `IS_DELETED = FALSE` — deleted events remain in the table
- `OWNER_ID` joins to `DIM_SALESFORCE_USERS.ID`, not to Mongo or Darwinbox user IDs
- `STG_` prefix is unusual — this is in `ANALYTICS_DB.ANALYTICS`, not a staging DB
- Exists in both ANALYTICS and ANALYTICS_DATAPLATFORM schemas (duplicated). Use ANALYTICS for consistency with other SFDC tables.
- Use `ACTIVITY_AT` for date filtering (when the event happened), not `CREATED_AT`
- Fivetran-synced — no Airflow DAG

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-06 | Created context file for scanner integration | Bridie Meredith |
