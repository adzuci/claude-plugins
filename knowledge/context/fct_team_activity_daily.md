# FCT_TEAM_ACTIVITY_DAILY

> Daily Amplitude event counts per team and event type — the broadest activity table in the foundation layer.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_ACTIVITY_DAILY` |
| **Grain** | One row per (team_id, ds, event_type_id, event_type) |
| **Grain columns** | `team_id`, `ds`, `event_type_id`, `event_type` |
| **Row count** | ~316M |
| **Refresh cadence** | Daily |
| **Coverage period** | Last 90 days (rolling) |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Aggregates Amplitude event counts at the team × day × event type grain. This is the entry point for all WAT/WAU calculations, use-case classification, feature engagement, and multi-product flags. The table deliberately contains no business logic — consumers join to `LU_AMPLITUDE_FEATURE_RULES` to classify events into features and use cases.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS` | Direct aggregation — all rows with non-null team_id and event_date |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `team_id` | VARCHAR | Apollo team identifier | Filters to non-null only |
| `ds` | DATE | Event date | Derived from `EVENT_DATE` |
| `event_type_id` | VARCHAR | Amplitude numeric event type ID | Join to `LU_AMPLITUDE_FEATURE_RULES` for feature classification |
| `event_type` | VARCHAR | Amplitude event type name string | Human-readable event label |
| `event_count` | NUMBER | Total event firings for this team/day/event | Raw count, no deduplication |
| `user_count` | NUMBER | Distinct user count for this team/day/event | `COUNT(DISTINCT USER_ID)` |

## Known Issues

- Rolling 90-day window only — no historical backfill beyond 90 days.
- Uses `FCT_AMPLITUDE_EVENTS` (dbt-built intermediate), not raw Amplitude data. Raw Amplitude lives in a separate schema.
- Feature-level breakdowns require joining to `LU_AMPLITUDE_FEATURE_RULES` — this table intentionally carries no feature classification logic itself.
- `count_of_users` (team size) and `paid_seat_limit` are not here — join to `LU_TEAM_ATTRIBUTES` or `FCT_TEAM_REVENUE_DAILY`.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
