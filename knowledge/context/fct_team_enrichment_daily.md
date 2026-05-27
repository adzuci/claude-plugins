# FCT_TEAM_ENRICHMENT_DAILY

> Daily enrichment activity per team and source (API, CSV, CRM, waterfall).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_ENRICHMENT_DAILY` |
| **Grain** | One row per (team_id, ds, enrichment_source) |
| **Grain columns** | `team_id`, `ds`, `enrichment_source` |
| **Row count** | ~1.9M |
| **Refresh cadence** | Daily |
| **Coverage period** | Last 90 days (rolling) |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Aggregates enrichment activity per team per day, broken out by enrichment source. The waterfall portion (Mongo-sourced) is live. The Amplitude portion covering API, CSV, and CRM enrichment events is blocked on `LU_ENUM` event mappings and not yet populated. Consumers derive rolling windows, use-case flags, and enrichment interest signals from this table.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_TYPED_CUSTOM_FIELD_AUTO_GENERATE_WORKFLOW_REQUESTS` | Waterfall enrichment requests — live |
| Amplitude via `FCT_AMPLITUDE_EVENTS` + `LU_ENUM` | API/CSV/CRM enrichment events — blocked, not yet populated |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `team_id` | VARCHAR | Apollo team identifier | |
| `ds` | DATE | Activity date | Cast from `CREATED_AT_UTC` for waterfall source |
| `enrichment_source` | VARCHAR | Source type: `waterfall`, `api`, `csv`, `crm` | Currently only `waterfall` is populated |
| `request_count` | NUMBER | Total enrichment requests for this team/day/source | Raw count |
| `user_count` | NUMBER | Distinct users performing enrichment | `COUNT(DISTINCT USER_ID)` |

## Known Issues

- Amplitude enrichment portion (API/CSV/CRM event types) is **blocked on `LU_ENUM`** — those rows do not exist yet. Only `enrichment_source = 'waterfall'` is currently populated.
- Rolling 90-day window only.
- `enrichment_source` enum will expand when the Amplitude portion is unblocked — downstream queries filtering on this column will get new values.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
