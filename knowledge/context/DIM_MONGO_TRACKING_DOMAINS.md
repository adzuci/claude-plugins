# DIM_MONGO_TRACKING_DOMAINS

> Tracking domain configuration for email deliverability. One row per tracking domain.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TRACKING_DOMAINS` |
| **Grain** | One row per tracking domain |
| **Row count** | ~109K (as of 2026-03-26) |
| **Refresh cadence** | Daily (assumed — ANALYTICS_DATAPLATFORM standard) |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Dimension table for custom tracking domains used in email link tracking and click tracking. Each row represents a tracking domain configured by a team, with metadata on status, health, spam flags, email volume, and HTTPS configuration. Use for deliverability analysis, tracking domain health monitoring, and spam rate reporting.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `tracking_domains` collection (assumed) | Raw source — replicated to Snowflake by Data Platform |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| TRACKING_DOMAIN_ID | TEXT | Unique identifier | Primary key |
| DOMAIN | TEXT | The tracking domain name | |
| TEAM_ID | TEXT | Team that owns this domain | Join to DIM_MONGO_TEAMS |
| STATUS_CD | TEXT | Domain status | <!-- TODO: enumerate values --> |
| HOST_CD | TEXT | Hosting provider code | |
| TYPE_CD | TEXT | Domain type | |
| ALLOW_CLICK_TRACKING | BOOLEAN | Whether click tracking is enabled | |
| IS_DEFAULT | BOOLEAN | Whether this is the team's default tracking domain | |
| USE_HTTPS | BOOLEAN | Whether HTTPS is enabled for tracking links | |
| MARKED_AS_MAYBE_UNHEALTHY | BOOLEAN | Domain flagged as potentially unhealthy | |
| MARKED_AS_SPAM | BOOLEAN | Domain flagged as spam | Key for spam rate analysis |
| NUM_EMAILS_SENT | FLOAT | Total emails sent through this domain | |
| ROUTING_DOMAIN_ID | TEXT | Associated routing domain | |
| TAG_CD | TEXT | Domain tag | |
| EXPIRED_AT_UTC | TIMESTAMP_NTZ | When the domain expired | NULL if still active |
| CACHED_FIRST_EMAIL_SENT_AT_UTC | TIMESTAMP_NTZ | First email sent through this domain | |
| NUM_EMAILS_SENT_LAST_UPDATED_UTC | TIMESTAMP_NTZ | When email count was last refreshed | |
| CREATED_AT_UTC | TIMESTAMP_NTZ | Record creation timestamp | |
| UPDATED_AT_UTC | TIMESTAMP_NTZ | Last updated timestamp | |
| LOAD_DATE | DATE | Snowflake load date | |

## Known Issues & Gotchas

- **Column comments mostly empty** — schema is lightly documented at source. Column names are self-descriptive but enum values for STATUS_CD, HOST_CD, TYPE_CD need discovery.
- **NUM_EMAILS_SENT is FLOAT** — not INTEGER. May contain fractional values or NULLs.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
