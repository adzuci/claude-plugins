# FCT_MONGO_ASSISTANT_THREAD_MESSAGES

> AI Assistant message-level data. One row per message in an assistant thread.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_ASSISTANT_THREAD_MESSAGES` |
| **Grain** | One row per assistant message |
| **Row count** | ~12M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely `dbt_models_group_1`. Related CDC config exists. |

## Description

Message-level AI Assistant data. Joined with `DIM_MONGO_ASSISTANT_THREADS` for thread-level context. Key table for WAU engagement analysis — tool calls are stored in the `content` VARIANT column and extracted via LATERAL FLATTEN.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `assistant_thread_messages` collection | Primary source (CDC ingestion) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ASSISTANT_THREAD_MESSAGE_ID | TEXT (PK) | Unique message identifier | |
| ASSISTANT_THREAD_ID | TEXT (FK) | Thread this message belongs to | Join to DIM_MONGO_ASSISTANT_THREADS |
| AUTHOR_ROLE_CD | TEXT | Who authored the message | `'user'` or `'assistant'` |
| SEQ_NUM | NUMBER | Message sequence within the thread | Used to count distinct user messages |
| CONTENT | VARIANT/ARRAY | Message content blocks | Contains tool_use blocks for tool calls |

## How It's Used

### Tool call extraction (LATERAL FLATTEN on content)

Tool calls are stored as content blocks. The content is a VARIANT that must be parsed with `TRY_PARSE_JSON`. Two tool name paths exist depending on message format — always use COALESCE:

```sql
-- Step 1: parse content in threads CTE
TRY_PARSE_JSON(atm.content) AS message_content

-- Step 2: flatten + extract tool name in a separate CTE
FROM threads th, LATERAL FLATTEN(input => th.message_content) con
COALESCE(con.value:data:tool_name::STRING, con.value:data:toolName::STRING) AS tool_name
-- :data:tool_name = standard path; :data:toolName = camelCase variant (both appear in practice)
-- Presence of a non-NULL tool_name indicates a tool call occurred
```

Note: some older documentation shows `f.value:name::string` or `f.value:type::string = 'tool_use'` — this does **not** match the confirmed format in production queries. Use `:data:tool_name` / `:data:toolName` with COALESCE.

### user_message_count window function

Count distinct user messages per thread (used to classify proactive thread interaction):

```sql
COUNT(DISTINCT CASE WHEN atm.author_role_cd = 'user' THEN atm.seq_num ELSE NULL END)
    OVER (PARTITION BY atm.assistant_thread_id) AS user_message_count
```

### Full WAU engagement query

See `DIM_MONGO_ASSISTANT_THREADS.md` for the complete WAU query — this table is always joined to that one. The pattern:
1. Join threads → messages in a CTE to compute `user_message_count` per thread
2. Re-join messages and LATERAL FLATTEN to extract tool calls
3. Apply interactive thread filter + Paid Core filter
4. Aggregate by week

### Key consumers
- AI product debrief (`run_ai_debrief.py`)
- Data Science WAU reporting
- Product Analytics (AI engagement)

## Known Issues & Gotchas

- **`content` is a VARIANT array** — must use LATERAL FLATTEN to access tool_use blocks. Cannot filter content directly.
- **`author_role_cd = 'user'` + `seq_num`** is the reliable way to count user turns — not message count alone (assistant may generate multiple messages in one turn).
- Table is rapidly growing — always use a date filter on the joined thread's `created_at`, not on a timestamp in this table (which may not exist).

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
| 2026-03-24 | Added key columns, tool call extraction pattern (LATERAL FLATTEN), user_message_count window function, WAU engagement query notes | Pubudu (via Claude) |
| 2026-03-31 | Corrected tool call extraction path: confirmed format is `con.value:data:tool_name` / `con.value:data:toolName` (COALESCE both); old `f.value:name::string` path does not match production data | Pubudu (via Jarvis) |
