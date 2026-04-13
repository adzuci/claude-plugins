# FCT_MONGO_DIALER_EVENTS

> Raw dialer event log from MongoDB — call sessions, statuses, and event metadata.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_DIALER_EVENTS` |
| **Grain** | One row per DIALER_EVENT_ID |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Source — raw MongoDB extract |
| **Owner** | Data Platform |

## Description

Raw event-level table capturing dialer (phone call) events from MongoDB. Each row is a single event in a dialer session — includes parallel dial sessions, call statuses, event types/subtypes, and a VARIANT DATA column with additional metadata. Used by Pratheek and dialer analytics (171 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB dialer_events collection | Direct extract |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DIALER_EVENT_ID | TEXT | Primary key | |
| PARALLEL_DIAL_SESSION_ID | TEXT | Groups events within a parallel dial session | |
| PARALLEL_DIAL_ITEM_ID | TEXT | Individual dial item within a session | |
| PHONE_CALL_ID | TEXT | Links to the phone call record | |
| IDENTIFIER | TEXT | Event identifier | |
| TYPE | TEXT | Event type (e.g., call_started, call_ended) | |
| SUB_TYPE | TEXT | Event sub-type for finer classification | |
| STATUS | TEXT | Event status | |
| MESSAGE | TEXT | Event message/description | |
| DATA | VARIANT | Additional event metadata (JSON) | Use LATERAL FLATTEN or DATA:key syntax |
| CREATED_AT_UTC | TIMESTAMP_NTZ | When the event occurred | |
| LOAD_DATE | DATE | When this row was loaded into Snowflake | |

## How It's Used

### Common query patterns

- Analyze dialer call outcomes by TYPE/SUB_TYPE/STATUS
- Track parallel dial session metrics
- Extract metadata from DATA variant column

### Key consumers

- Pratheek (dialer analytics — 171 queries/14d)
- Product analytics (dialer feature usage)

## Known Issues & Gotchas

- DATA column is VARIANT (JSON) — use `DATA:key::type` syntax or LATERAL FLATTEN
- Raw source table — no aggregation or deduplication applied
- No team/user ID directly — need to join via PHONE_CALL_ID or DATA contents

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
