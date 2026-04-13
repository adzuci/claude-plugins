# FCT_MONGO_PHONE_CALLS

> Phone call activity from Apollo's dialer. One row per call.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PHONE_CALLS` |
| **Grain** | One row per phone call (`PHONE_CALLS_ID`) |
| **Row count** | ~106M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model, stg_mongo prefix) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `dbt_models_group_1` (dbt job 137019, model prefix `stg_mongo`). Source: MongoDB phone_calls collection. |

## Description

Dialer activity table (35 distinct users). Tracks all phone calls made through Apollo's dialer including parallel dial sessions. Contains call outcomes, duration, transcripts, and Twilio integration data.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `phone_calls` collection | Primary source |
| Twilio | Call SID, phone numbers |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| IS_INBOUND | BOOLEAN | 28 | 334 | Inbound vs outbound call | |
| TWILIO_CALL_SID | TEXT | 27 | 1,937 | Twilio call session ID | |
| STATUS | TEXT | 27 | 1,258 | Call status | |
| TO_NUMBER | TEXT | 27 | 820 | Called phone number | |
| CREATED_AT_UTC | TIMESTAMP | 25 | 1,864 | Call creation time | |
| DURATION | NUMBER | 24 | 1,559 | Call duration (seconds) | |
| PHONE_CALLS_ID | TEXT | 24 | 864 | Call ID | **Primary key** |
| TEAM_ID | TEXT | 23 | 1,290 | Owning team | FK to DIM_MONGO_TEAMS |
| USER_ID | TEXT | 22 | 828 | Caller user | FK to DIM_MONGO_USERS |
| PHONE_CALL_OUTCOME_ID | TEXT | 22 | 222 | Outcome reference | |
| IS_ANSWERED | BOOLEAN | 21 | 321 | Call answered flag | |
| PARALLEL_DIAL_ITEM_ID | TEXT | 19 | 746 | Parallel dial item | |
| CONTACT_ID | TEXT | 19 | 209 | Called contact | FK to DIM_MONGO_CONTACTS |
| TRANSCRIPT_STRING | TEXT | 18 | 123 | Call transcript | |

## How It's Used

### Common query patterns
- **Dialer activity metrics**: Call volume, connect rates, duration by team
- **Parallel dial analysis**: PARALLEL_DIAL_SESSION_ID and PARALLEL_DIAL_ITEM_ID
- **Product engagement**: Call counts feed into DIM_USERS_DAILY/DIM_TEAMS_DAILY activity metrics

### Key consumers
- Product Analytics (dialer feature usage)
- Data Science (activation/engagement funnels)

## Known Issues & Gotchas

- ~106M rows — filter by date range
- TRANSCRIPT_STRING may be null for older calls or calls without recording

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
