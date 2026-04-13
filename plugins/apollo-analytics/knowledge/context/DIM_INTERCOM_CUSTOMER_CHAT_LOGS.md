# DIM_INTERCOM_CUSTOMER_CHAT_LOGS

> Full text of Intercom customer support chat logs. Multiple rows per conversation (one per message or log entry).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_INTERCOM_CUSTOMER_CHAT_LOGS` |
| **Grain** | Multiple rows per conversation — one per chat log entry |
| **Row count** | <!-- TODO: verify --> |
| **Refresh cadence** | <!-- TODO: verify — likely daily from Intercom integration --> |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | <!-- TODO: CX / Support Analytics --> |
| **DAG** | <!-- TODO: not yet verified in airflow-dags --> |

## Description

Full body text of Intercom customer support conversations. Paired with `DIM_SUPPORT_CONVERSATIONS` (which has AI-classified metadata) for content-based ticket analysis. Primary use case is keyword classification when no dedicated topic label exists in `DIM_SUPPORT_CONVERSATIONS.GENERAL_CONVERSATION_TOPIC`.

## Upstream Sources

| Source | Relationship |
|---|---|
| Intercom (support platform) | Primary source — conversation transcript data |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| TICKET_OR_CONVERSATION_ID | TEXT | Join key to DIM_SUPPORT_CONVERSATIONS.CONVERSATION_ID | **NOT** `CONVERSATION_ID` — confirmed from query usage 2026-03-26 |
| BODY | TEXT | Text of one chat log entry | Multiple rows per conversation — use `listagg(body)` to reconstruct full thread |
| CREATED_AT | TIMESTAMP | Timestamp of the log entry | Use for ordering in listagg |

<!-- TODO: Verify full column list — TICKET_OR_CONVERSATION_ID, BODY, CREATED_AT confirmed from query usage -->

## How It's Used

### Join pattern with DIM_SUPPORT_CONVERSATIONS

**Correct join key is `ticket_or_conversation_id`** — the column on DIM_INTERCOM_CUSTOMER_CHAT_LOGS, joined to `conversation_id` on DIM_SUPPORT_CONVERSATIONS. Always LEFT JOIN and always `listagg(body)` since there are multiple rows per conversation.

```sql
SELECT
    s.CONVERSATION_ID,
    DATE_TRUNC('week', s.CONVERSATION_CREATED_AT)              AS week_starting_sun,
    s.AI_GENERATED_SUMMARY,
    s.AI_ISSUE_SUMMARY,
    listagg(cl.body) within group (order by cl.created_at)     AS full_conversation_body
FROM ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS          s
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_INTERCOM_CUSTOMER_CHAT_LOGS cl
    ON cl.ticket_or_conversation_id = s.conversation_id        -- NOT cl.conversation_id
WHERE s.CONVERSATION_CREATED_AT >= {START_DATE}
  AND s.CONVERSATION_CREATED_AT <  {END_DATE}
GROUP BY 1, 2, 3, 4;
```

### AI debrief keyword classification

Pull BODY + AI_GENERATED_SUMMARY + AI_ISSUE_SUMMARY, then score in Python across signal keyword lists (AI Assistant, Power Ups, AI Messaging). Classify to highest-scoring category. Produces weekly ticket volume breakdown where no topic label exists.

### Key consumers
- AI product debrief (`run_ai_debrief.py`) — keyword classification when GENERAL_CONVERSATION_TOPIC has no AI category
- Ad-hoc support analysis requiring full ticket text

## Known Issues & Gotchas

- **Join key is `ticket_or_conversation_id`** — NOT `conversation_id`. Using `conversation_id` will silently return no rows.
- **Multiple rows per conversation** — always `listagg(body)` to reconstruct full thread text; never assume one row.
- **Always join LEFT** — not every conversation in DIM_SUPPORT_CONVERSATIONS has a corresponding log row.
- **Use `DIM_SUPPORT_CONVERSATIONS.CONVERSATION_CREATED_AT` for date filtering** — do not filter on a date column in this table.
- `TICKET_OR_CONVERSATION_ID`, `BODY`, `CREATED_AT` confirmed from query usage 2026-03-26.

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_SUPPORT_CONVERSATIONS` | Parent — conversation metadata, topic classification, team/user IDs |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file — discovered via AI debrief support ticket classification query | Pubudu (via Claude) |
