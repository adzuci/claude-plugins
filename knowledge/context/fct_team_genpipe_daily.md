# FCT_TEAM_GENPIPE_DAILY

> **WARNING: THIS TABLE DOES NOT EXIST YET.** Planned daily pipeline generation activity combining sequences + nextgen pipeline — blocked on LU_ENUM Amplitude event mappings.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_GENPIPE_DAILY` (planned) |
| **Grain** | One row per (team_id, ds, campaign_id, message_type, status) |
| **Grain columns** | `team_id`, `ds`, `campaign_id`, `message_type`, `status` |
| **Row count** | N/A (not yet built) |
| **Refresh cadence** | Daily (planned) |
| **Coverage period** | TBD |
| **Trust level** | Development (not yet built) |
| **Owner** | Analytics (Bridie Meredith) |

## Description

**NOT YET BUILT.** This table is in design, blocked on `LU_ENUM` Amplitude event mappings. When built, it will aggregate daily pipeline generation activity per team, combining Apollo Sequences data with nextgen pipeline activity. Intended consumers: use-case classification (pipeline gen), WAT breakdowns by go-to-market motion, campaign-level funnel metrics.

## Upstream Sources

| Source | Relationship |
|---|---|
| Amplitude via `FCT_AMPLITUDE_EVENTS` + `LU_ENUM` | Sequence/nextgen pipeline events — blocked |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES` | Email message sends — planned |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_RULE_ACTIONS` | Sequence rule firings — planned |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `team_id` | VARCHAR | Apollo team identifier | Planned |
| `ds` | DATE | Activity date | Planned |
| `campaign_id` | VARCHAR | Sequence/campaign identifier | Planned |
| `message_type` | VARCHAR | Email, LinkedIn, call, etc. | Planned — exact enum TBD |
| `status` | VARCHAR | Sent, bounced, opened, replied, etc. | Planned — exact enum TBD |

## Known Issues

- **Table does not exist** — do not query. Any reference to this table in SQL will fail.
- Blocked on `LU_ENUM` Amplitude event_type_id → feature_name mappings being complete.
- Grain and column names are provisional — subject to change before build.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file as planned-table stub | Pepper (auto) |
