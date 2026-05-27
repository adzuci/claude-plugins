# FCT_TEAM_PHONE_CALLS_DAILY

> Daily phone call activity per team — call counts, user counts, and duration by status, outcome, and purpose.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_PHONE_CALLS_DAILY` |
| **Grain** | One row per team + date + status + outcome + purpose (`team_id` + `ds` + `status` + `call_outcome_id` + `call_purpose_id`) |
| **Row count** | ~892K (from catalog) |
| **Refresh cadence** | Daily (Snowflake Task: `TASK_REFRESH_FCT_TEAM_PHONE_CALLS_DAILY`, runs at 06:00 UTC) |
| **Trust level** | Canonical (Playground) — source is high-trust ANALYTICS_DATAPLATFORM |
| **Owner** | Data Engineering (Brighid Meredith) |
| **DAG** | Snowflake Task `PLAYGROUND.TASK_REFRESH_FCT_TEAM_PHONE_CALLS_DAILY` with stored procedure `SP_REFRESH_FCT_TEAM_PHONE_CALLS_DAILY` |

## Description

Daily aggregation of phone call activity from the Mongo phone_calls collection. Consumers derive connect rates, call duration analysis, rolling windows, dialer usage metrics, and win/close domain aggregations. This covers the dialer feature only; conversations and deals/scheduler/notes are separate sources (see notes below).

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PHONE_CALLS` | Primary source — Mongo phone_calls collection |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | TEXT | Apollo team ID | FK to DIM_MONGO_TEAMS.TEAM_ID |
| ds | DATE | Call date | Derived from `CREATED_AT_UTC::DATE` |
| status | TEXT | Call status | **NULL for 55% of source rows** — source DQ issue |
| call_outcome_id | TEXT | Outcome identifier | FK to phone call outcomes |
| call_purpose_id | TEXT | Purpose identifier | FK to phone call purposes |
| call_count | NUMBER | Number of calls | `COUNT(*)` of source rows |
| user_count | NUMBER | Distinct users making calls | `COUNT(DISTINCT USER_ID)` |
| total_call_duration | NUMBER | Sum of call durations | `SUM(DURATION)` |

## How It's Used

### Common query patterns
- **Connect rate:** Calls with connected status / total calls per team per day
- **Call volume trends:** `SELECT ds, SUM(call_count) ... GROUP BY ds`
- **Duration analysis:** `SUM(total_call_duration) / SUM(call_count)` for average call length
- **Dialer adoption:** Teams with non-zero call_count over rolling windows
- Join with `DIM_MONGO_TEAMS` for team attributes

### Key consumers
- Win/close domain analysis
- Dialer usage metrics
- Product analytics (call feature adoption)

## Known Issues & Gotchas

- **55% NULL status:** The `status` column is NULL for 55% of source rows. This is a source data quality issue in `FCT_MONGO_PHONE_CALLS`, not a bug in this table. DQ check monitors null_status_rate on each refresh.
- **Status inconsistency:** Minor casing/format issues in source: `no-answer` (8.4M rows) vs `no_answer` (255) vs `No Answer` (17) vs `"no_answer"` (9). Per design rules, normalization is a consumer concern.
- **No connect rate column** — there is no `connected_call_count` or equivalent column in this table. Closest proxy is `status = 'completed'` but this is unreliable given the 55% NULL rate. For connect rate, use `FCT_MONGO_PHONE_CALLS` directly with `twilio_call_sid` present (see FY27 R&D dashboard pattern).
- **Verified status values** (from `FCT_MONGO_PHONE_CALLS` source): `completed`, `no-answer`, `canceled`, `failed`, `busy`
- **Win/close domain is partial:** This table covers dialer activity only. For conversations, consider a separate `FCT_TEAM_CONVERSATIONS_DAILY`. For deals/scheduler/notes, those are Amplitude-sourced — use `FCT_TEAM_ACTIVITY_DAILY` with feature flags.
- **DQ checks:** Row count, row count regression, freshness, and null_status_rate checks run on each refresh.

## Slack Context

<!-- TODO: search Slack for dialer/phone call discussions -->

## Business Terms

| Term | Definition |
|---|---|
| connect rate | Percentage of calls that result in a connected/answered status |
| call_outcome_id | Identifier for the outcome of a call (e.g., interested, not interested, left voicemail) |
| call_purpose_id | Identifier for the purpose of a call (e.g., prospecting, follow-up) |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-11 | Created context file | Brighid (via Claude) |
