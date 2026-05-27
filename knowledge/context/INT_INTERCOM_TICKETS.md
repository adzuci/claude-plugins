# INT_INTERCOM_TICKETS

> One row per Intercom ticket (email channel). Used for email volume in Channel Mix metric.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.INT_INTERCOM_TICKETS` |
| **Grain** | One row per `TICKET_ID` |
| **Row count** | Unknown |
| **Refresh cadence** | Daily |
| **Trust level** | Canonical |
| **Owner** | Analytics Engineering (BIA) |

## Description

Intercom tickets represent the email support channel. Used in Channel Mix reporting to count email volume alongside chat and video from `INT_INTERCOM_CONVERSATIONS`. Filter to `IS_TICKET_SUPPORT_TEAM_HANDLED = TRUE` and `TICKET_CATEGORY = 'Customer'` for PA Live Support scope.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| TICKET_ID | TEXT | Primary key | |
| TICKET_CONVERSION_AT | TIMESTAMP | When the ticket was created/converted | Use for date filtering |
| IS_TICKET_SUPPORT_TEAM_HANDLED | BOOLEAN | TRUE if handled by a support team | Filter to TRUE for PA Live Support scope |
| TICKET_CATEGORY | TEXT | Ticket category | Filter to 'Customer' for end-customer tickets |

## How It's Used

### Channel Mix (email volume)
```sql
FROM INT_INTERCOM_TICKETS
WHERE TICKET_CONVERSION_AT >= ...
  AND IS_TICKET_SUPPORT_TEAM_HANDLED = TRUE
  AND TICKET_CATEGORY = 'Customer'
```
LEFT JOIN result to `INT_INTERCOM_CONVERSATIONS` monthly rollup — months with zero email tickets still appear (COALESCE to 0).

## Related Tables

| Table | Relationship |
|---|---|
| `INT_INTERCOM_CONVERSATIONS` | Parallel — chat channel; join on month for Channel Mix rollup |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Created context file for support-metrics skill catalog registration | Marie (via Claude) |
