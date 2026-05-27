# INT_INTERCOM_CONVERSATIONS_TURNED_TICKETS

> One row per Intercom conversation that was escalated (converted to a ticket). Used for escalation rate calculation.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS_TURNED_TICKETS` |
| **Grain** | One row per `CONVERSATION_ID` (escalated only) |
| **Row count** | Subset of INT_INTERCOM_CONVERSATIONS |
| **Refresh cadence** | Daily |
| **Trust level** | Canonical |
| **Owner** | Analytics Engineering (BIA) |

## Description

Contains only conversations that were escalated (turned into tickets). LEFT JOIN from `INT_INTERCOM_CONVERSATIONS` to compute escalation rate — conversations missing from this table were not escalated.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT | Join key to INT_INTERCOM_CONVERSATIONS | |
| IS_CONVERSATION_TURNED_TICKET | BOOLEAN | Always TRUE in this table | Exists for explicit flag usage in joins |

## Known Issues & Gotchas

- **Always LEFT JOIN** from `INT_INTERCOM_CONVERSATIONS` — do not inner join or you will lose non-escalated conversations from the denominator.
- All rows in this table have `IS_CONVERSATION_TURNED_TICKET = TRUE`.

## How It's Used

### Escalation Rate
```sql
LEFT JOIN INT_INTERCOM_CONVERSATIONS_TURNED_TICKETS tt
    ON c.CONVERSATION_ID = tt.CONVERSATION_ID
-- Escalation rate = conversations where tt.IS_CONVERSATION_TURNED_TICKET = TRUE / total AI-touched
```

## Related Tables

| Table | Relationship |
|---|---|
| `INT_INTERCOM_CONVERSATIONS` | Parent — all conversations; left-join here for escalation flag |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Created context file for support-metrics skill catalog registration | Marie (via Claude) |
