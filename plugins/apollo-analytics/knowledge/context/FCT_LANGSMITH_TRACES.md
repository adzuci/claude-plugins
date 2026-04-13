# FCT_LANGSMITH_TRACES

> Individual LLM trace metrics from LangSmith — the source of truth for AI Assistant latency, token usage, cost, and tool execution performance.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LANGSMITH_TRACES` |
| **Grain** | One row per LLM trace/run (trace_id) |
| **Row count** | ~141M (2026-04-01) |
| **Refresh cadence** | Daily (24h lag — GCS export → Snowflake via Airflow DAG owned by AI Infra / Sunny Kumar) |
| **Trust level** | Authoritative for LLM performance telemetry |
| **Owner** | AI Infrastructure (Sunny Kumar) / Data Platform |
| **DAG** | Airflow DAG — LangSmith API → GCS export → Snowflake load. "zeus" project. |

## Description

Captures production LLM execution traces from LangSmith's "zeus" project. Each row is one trace — an LLM call, tool execution, or chain step — with full latency, token, and error data. Traces are linked back to AI Assistant threads via `thread_id` in trace metadata. Aggregated upward into `FCT_LANGSMITH_THREADS` (thread grain) and then joined into `FCT_AI_ASSISTANT_THREADS` for enriched latency/cost analytics.

LangSmith coverage depends on which code paths are instrumented — not all requests may be traced.

## Upstream Sources

| Source | Relationship |
|---|---|
| LangSmith "zeus" project (production) | Source — traces exported to GCS daily |
| GCS bucket | Intermediate storage before Snowflake load |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| TRACE_ID | TEXT (PK) | Unique trace identifier | |
| THREAD_ID | TEXT | FK to FCT_AI_ASSISTANT_THREADS | Populated from LangSmith trace metadata — may be null for non-thread traces |
| RUN_TYPE | TEXT | `llm`, `tool`, `chain` | Filter to `llm` for model call metrics |
| MODEL_NAME | TEXT | LLM model used (e.g., claude-3-5-sonnet) | |
| START_TIME | TIMESTAMP | Trace start time | |
| END_TIME | TIMESTAMP | Trace end time | |
| FIRST_TOKEN_TIME | TIMESTAMP | Time to first token | Use for P50/P90/P95 latency |
| PROMPT_TOKENS | NUMBER | Input token count | |
| COMPLETION_TOKENS | NUMBER | Output token count | |
| LATENCY_MS | NUMBER | Total duration in ms | Note: duration_seconds field lacks ms precision — fix pending |
| ERROR | TEXT | Error message if trace failed | NULL if successful |
| IS_ROOT | BOOLEAN | True if root-level trace (thread entrypoint) | Use `WHERE IS_ROOT = TRUE` for thread-level aggregation |

## How It's Used

### Common query patterns
```sql
-- P50/P90/P95 first-token latency for a model
SELECT
  MODEL_NAME,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF('ms', START_TIME, FIRST_TOKEN_TIME)) AS p50_ms,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY DATEDIFF('ms', START_TIME, FIRST_TOKEN_TIME)) AS p90_ms
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LANGSMITH_TRACES
WHERE RUN_TYPE = 'llm' AND FIRST_TOKEN_TIME IS NOT NULL
GROUP BY 1;

-- Thread-level cost estimate (before FCT_LANGSMITH_THREADS is used)
SELECT THREAD_ID, SUM(PROMPT_TOKENS + COMPLETION_TOKENS) AS total_tokens
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LANGSMITH_TRACES
WHERE RUN_TYPE = 'llm'
GROUP BY 1;
```

### Key consumers
- FCT_LANGSMITH_THREADS (aggregated from this table)
- FCT_AI_ASSISTANT_THREADS (joined via FCT_LANGSMITH_THREADS)
- AI quality / cost monitoring

## Known Issues & Gotchas

- `LATENCY_MS` derived from `duration_seconds` lacks millisecond precision — use `DATEDIFF('ms', START_TIME, END_TIME)` instead
- `THREAD_ID` may be null for traces that aren't linked to an AI Assistant thread
- Coverage gap: only instrumented code paths appear — not a complete log of all AI requests
- 24h lag — yesterday's traces are available today
- Table is large (~141M rows) — always filter by date range and/or RUN_TYPE

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Created context file from Notion AI Assistant Analytics Data Models doc | Sai (via Jarvis) |
