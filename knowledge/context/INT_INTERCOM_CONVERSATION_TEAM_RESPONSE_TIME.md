# INT_INTERCOM_CONVERSATION_TEAM_RESPONSE_TIME

> One row per team response event per conversation. Used for Chat SLA calculation.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATION_TEAM_RESPONSE_TIME` |
| **Grain** | One row per (CONVERSATION_ID, NUMBERED_TEAM_CONVERSATION_RESPONSES) |
| **Row count** | Multiple rows per conversation |
| **Refresh cadence** | Daily |
| **Trust level** | Canonical |
| **Owner** | Analytics Engineering (BIA) |

## Description

Tracks each team response event for a conversation, with response time in minutes. Used to calculate Chat SLA (% of conversations where first team response was within 2 minutes, excluding non-working hours).

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT | Join key to INT_INTERCOM_CONVERSATIONS | |
| NUMBERED_TEAM_CONVERSATION_RESPONSES | NUMBER | Response sequence number (1 = first response) | Filter to = 1 for first-response SLA |
| CONVERSATION_TEAM_RESPONSE_TIME_MINUTES | NUMBER | Minutes from assignment to response | Used for SLA threshold check (≤ 2 min) |
| IS_TEAM_ASSIGNMENT_DURING_NON_WORKING_HOURS | BOOLEAN | TRUE if assignment was outside working hours | Filter to FALSE for AOP-aligned SLA |

## Known Issues & Gotchas

- **Multiple rows per conversation** — do not count rows as conversations; join and filter to `NUMBERED_TEAM_CONVERSATION_RESPONSES = 1`.
- **Exclude non-working hours** (`IS_TEAM_ASSIGNMENT_DURING_NON_WORKING_HOURS = FALSE`) to match AOP target methodology.

## How It's Used

### Chat SLA
```sql
JOIN INT_INTERCOM_CONVERSATION_TEAM_RESPONSE_TIME r
    ON c.CONVERSATION_ID = r.CONVERSATION_ID
WHERE r.NUMBERED_TEAM_CONVERSATION_RESPONSES = 1
  AND r.IS_TEAM_ASSIGNMENT_DURING_NON_WORKING_HOURS = FALSE
-- SLA hit = r.CONVERSATION_TEAM_RESPONSE_TIME_MINUTES <= 2
```

## Related Tables

| Table | Relationship |
|---|---|
| `INT_INTERCOM_CONVERSATIONS` | Parent — join on CONVERSATION_ID |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Created context file for support-metrics skill catalog registration | Marie (via Claude) |
