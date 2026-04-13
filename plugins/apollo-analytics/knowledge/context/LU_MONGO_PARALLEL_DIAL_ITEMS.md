# LU_MONGO_PARALLEL_DIAL_ITEMS

> Item-level records for parallel dialer sessions. One row per dial item (contact dialed in a parallel dial session).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_MONGO_PARALLEL_DIAL_ITEMS` |
| **Grain** | One row per parallel dial item |
| **Row count** | ~10.4M (as of 2026-03-26) |
| **Refresh cadence** | Daily (assumed — ANALYTICS_DATAPLATFORM standard) |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Lookup/fact table for individual parallel dial items. Each row represents one contact dialed within a parallel dial session. Links to users, teams, contacts, accounts, and outreach tasks. Use for parallel dialer adoption analysis, session-level metrics, and contact-level dial outcomes.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `parallel_dial_items` collection (assumed) | Raw source — replicated to Snowflake by Data Platform |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| PARALLEL_DIAL_ITEM_ID | TEXT | Unique identifier for the dial item | Primary key |
| PARALLEL_DIAL_SESSION_ID | TEXT | Reference to the parallel dial session | Join key to group items by session |
| USER_ID | TEXT | User who owns this dial item | Join to DIM_MONGO_USERS |
| TEAM_ID | TEXT | Team the user belongs to | Join to DIM_MONGO_TEAMS |
| CONTACT_ID | TEXT | Contact being dialed | Join to DIM_MONGO_CONTACTS |
| ACCOUNT_ID | TEXT | Account the contact belongs to | |
| OUTREACH_TASK_ID | TEXT | Associated outreach task | |
| QUEUED_AT | TIMESTAMP_NTZ | When the item was queued for dialing | |
| STATUS_CD | TEXT | Status code of the dial item | <!-- TODO: enumerate distinct values --> |
| PHONE_NUMBERS | VARIANT | Embedded phone numbers for this dial item | JSON/array — may need LATERAL FLATTEN |
| CREATED_AT_UTC | TIMESTAMP_NTZ | Record creation timestamp | |
| UPDATED_AT_UTC | TIMESTAMP_NTZ | Last updated timestamp | |
| LOAD_DATE | DATE | Snowflake load date | |

## How It's Used

### Common query patterns

<!-- TODO: check SNOWFLAKE_QUERY_HISTORY_ARCHIVE for usage patterns -->

### Key consumers

<!-- TODO: identify from query history -->

## Known Issues & Gotchas

- **PHONE_NUMBERS is VARIANT** — likely needs LATERAL FLATTEN or JSON extraction for individual numbers.
- **STATUS_CD values not yet enumerated** — run `SELECT DISTINCT STATUS_CD, COUNT(*) FROM ... GROUP BY 1` to discover.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
