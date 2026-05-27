# INT_INTERCOM_CONVERSATIONS

> One row per Intercom conversation. Canonical source for conversation-level support metrics.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS` |
| **Grain** | One row per `CONVERSATION_ID` |
| **Row count** | ~20K rated conversations per 6 months (partial); total volume higher |
| **Refresh cadence** | Daily |
| **Trust level** | Canonical |
| **Owner** | Analytics Engineering (BIA) |

## Description

Canonical conversation-level table for Intercom support metrics. Powers Chat SLA, AI Resolution Rate, Escalation Rate, and Channel Mix OKR queries. Key flags: AI participation, resolution state, first-handled team, channel type (chat vs video).

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT | Primary key | |
| CONVERSATION_CREATED_AT | TIMESTAMP | Conversation start time | Use for date filtering |
| CONVERSATION_FIRST_HANDLED_TEAM_NAME | TEXT | Team that first handled | Use LIKE 'PA Live Support%' — has sub-team suffixes |
| IS_AI_AGENT_PARTICIPATED | BOOLEAN | TRUE if AI touched the conversation | Denominator for AI Resolution Rate and Escalation Rate |
| IS_AI_ONLY_PARTICIPATED | BOOLEAN | TRUE if only AI handled (no human) | Filter to FALSE for rep-driven CSAT |
| AI_AGENT_RESOLUTION_STATE | TEXT | AI resolution outcome | Values: 'assumed_resolution', 'confirmed_resolution', others |
| IS_A_CALL_CONVERSATION | BOOLEAN | TRUE if video/voice conversation | Undercounts video by 5-15% — do not use for Video SLA OKR |

## Known Issues & Gotchas

- `IS_A_CALL_CONVERSATION` undercounts video conversations by 5-15% — do not use for Video SLA reporting.
- `IS_CONVERSATION_FIRST_CONTACT_RESOLUTION` is broken in FY26 — do not use.
- `CONVERSATION_FIRST_HANDLED_TEAM_NAME` requires a LIKE filter (e.g. `LIKE 'PA Live Support%'`) because team names include sub-team suffixes that vary.

## How It's Used

### Chat SLA
Join to `INT_INTERCOM_CONVERSATION_TEAM_RESPONSE_TIME` on `CONVERSATION_ID`. Filter: `IS_AI_ONLY_PARTICIPATED = FALSE`, team LIKE `PA Live Support%`.

### AI Resolution Rate
Filter to `IS_AI_AGENT_PARTICIPATED = TRUE`. Rate = `AI_AGENT_RESOLUTION_STATE IN ('assumed_resolution', 'confirmed_resolution')` / total.

### Channel Mix
Use `IS_A_CALL_CONVERSATION` to split video vs chat. Combine with `INT_INTERCOM_TICKETS` for email channel.

## Related Tables

| Table | Relationship |
|---|---|
| `INT_INTERCOM_CONVERSATION_TEAM_RESPONSE_TIME` | Child — one row per team response event; join on CONVERSATION_ID |
| `INT_INTERCOM_CONVERSATIONS_TURNED_TICKETS` | Child — escalated conversations only; left-join on CONVERSATION_ID |
| `INT_INTERCOM_TICKETS` | Separate — email/ticket channel; join on month for Channel Mix |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Created context file for support-metrics skill catalog registration | Marie (via Claude) |
