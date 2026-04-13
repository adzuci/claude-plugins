# AI_ASSISTANT_MESSAGES

> Message-level event table for AI Assistant tool usage and conversation flow. The lowest grain in the AI Assistant model hierarchy.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.AI_ASSISTANT_MESSAGES` |
| **Grain** | One row per assistant_thread_id + assistant_thread_message_id + tool_call_seq_in_message |
| **Row count** | ~19M (2026-04-02) |
| **Refresh cadence** | Daily (incremental, 30-day lookback) |
| **Trust level** | Authoritative (DS-owned, part of AI platform model hierarchy) |
| **Owner** | Data Science (Sai Sarvepalli) |
| **DAG** | dbt model: `models/marts/data_science/ai_platform/ai_assistant_messages.sql` |

## Description

Message-level event table that flattens tool calls out of conversation messages using LATERAL FLATTEN on message content JSON. Each row represents a single tool call within a message (or the message itself if no tool calls). Feeds upward into `FCT_AI_ASSISTANT_THREADS` as the primary aggregation source for tool usage, conversation flow, and engagement signals.

## Upstream Sources

| Source | Relationship |
|---|---|
| `DIM_MONGO_ASSISTANT_THREADS` | Base thread data from MongoDB |
| `FCT_MONGO_ASSISTANT_THREAD_MESSAGES` | Message data from MongoDB |
| LATERAL FLATTEN on message content JSON | Extracts individual tool calls per message |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ASSISTANT_THREAD_ID | TEXT | FK to FCT_AI_ASSISTANT_THREADS | |
| ASSISTANT_THREAD_MESSAGE_ID | TEXT | Message identifier | |
| TOOL_CALL_SEQ_IN_MESSAGE | NUMBER | Tool call position within message | Part of grain |
| APOLLO_USER_ID | TEXT | User who owns the thread | |
| TEAM_ID | TEXT | User's team | |
| TOOL_NAME | TEXT | Name of tool called | |
| CONTENT_TYPE | TEXT | Message content type | |
| MESSAGE_SEQ_NUM | NUMBER | Message position in conversation | |
| AUTHOR_ROLE_CD | TEXT | `user` or `assistant` | |
| USER_ENGAGEMENT_FLAG | BOOLEAN | True if user actively engaged | |
| ALL_AGENTS_INVOLVED | TEXT | Agents present in conversation | |
| FAILED_AGENTS | TEXT | Agents that failed | |

## How It's Used

### Common query patterns
- Tool call frequency analysis — COUNT by TOOL_NAME to understand what tools users invoke
- Conversation flow analysis — ORDER BY MESSAGE_SEQ_NUM to trace turn-by-turn interactions
- Failed agent debugging — filter FAILED_AGENTS IS NOT NULL for quality investigations
- Feed to FCT_AI_ASSISTANT_THREADS aggregation (has_tool_calls, distinct_tools_count, tool_names_list)

### Key consumers
- FCT_AI_ASSISTANT_THREADS (upstream dependency — aggregates this table)
- AI quality team (debugging failure modes)

## Known Issues & Gotchas

- Grain includes tool_call_seq_in_message — a single message can produce multiple rows if it has multiple tool calls. Deduplicate on (thread_id, message_id) before counting messages.
- LATERAL FLATTEN means rows without tool calls may appear once with null tool fields; rows with N tool calls appear N times.
- 30-day incremental lookback — historical data before the lookback window may not be reprocessed.

## Business Terms

| Term | Definition |
|---|---|
| USER_ENGAGEMENT_FLAG | True if user actively sent a message (vs system-initiated) |
| ALL_AGENTS_INVOLVED | Comma-separated list of agent names called during the thread |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Created context file from Notion AI Assistant Analytics Data Models doc | Sai (via Jarvis) |
