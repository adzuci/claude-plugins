# FCT_LANGSMITH_THREADS

> Thread-level LLM performance metrics aggregated from FCT_LANGSMITH_TRACES. The canonical source for per-thread latency, token, and cost data.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_LANGSMITH_THREADS` |
| **Grain** | One row per thread_id |
| **Row count** | ~2M (2026-04-02) |
| **Refresh cadence** | Daily |
| **Trust level** | Authoritative for thread-level LLM performance metrics |
| **Owner** | Data Science (Sai Sarvepalli) |
| **DAG** | dbt model — aggregated from `FCT_LANGSMITH_TRACES` using `IS_ROOT = TRUE` or `THREAD_ID` grouping |

## Description

Aggregates individual LangSmith traces (from `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LANGSMITH_TRACES`) to the thread grain. Each row represents one AI Assistant conversation thread with rolled-up latency, token usage, cost estimates, and tool execution metrics. Joined into `FCT_AI_ASSISTANT_THREADS` as the LangSmith enrichment layer.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LANGSMITH_TRACES` | Aggregated by thread_id — sum tokens, avg/min latency, count LLM calls |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| THREAD_ID | TEXT (PK) | FK to FCT_AI_ASSISTANT_THREADS | |
| NUM_LLM_CALLS | NUMBER | Total LLM calls in thread | |
| FIRST_TOKEN_LATENCY_MS | NUMBER | Time to first token (ms) | From root/first trace |
| AVG_LLM_LATENCY_MS | NUMBER | Average LLM call latency | |
| TOTAL_PROMPT_TOKENS | NUMBER | Sum of prompt tokens across all LLM calls | |
| TOTAL_COMPLETION_TOKENS | NUMBER | Sum of completion tokens | |
| TOTAL_TOKENS | NUMBER | Total tokens consumed | |
| ESTIMATED_COST_USD | NUMBER | Estimated LLM API cost | Model-based pricing estimate |
| PRIMARY_MODEL_NAME | TEXT | Most frequently used model in thread | |
| TOOL_EXECUTION_TIME_MS | NUMBER | Total time spent in tool calls | |
| NUM_TOOL_CALLS | NUMBER | Total tool call traces | |

## How It's Used

### Common query patterns
```sql
-- Average cost per thread by model
SELECT PRIMARY_MODEL_NAME, AVG(ESTIMATED_COST_USD) AS avg_cost, COUNT(*) AS threads
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_LANGSMITH_THREADS
GROUP BY 1 ORDER BY 2 DESC;

-- P90 first-token latency trend by week
SELECT DATE_TRUNC('week', t.THREAD_DATE) AS week,
       PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY l.FIRST_TOKEN_LATENCY_MS) AS p90_latency
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_LANGSMITH_THREADS l
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS t ON l.THREAD_ID = t.ASSISTANT_THREAD_ID
GROUP BY 1 ORDER BY 1 DESC;
```

### Key consumers
- FCT_AI_ASSISTANT_THREADS (joined for LLM latency + cost columns)
- AI product analytics (cost monitoring, latency dashboards)

## Known Issues & Gotchas

- Coverage limited to threads with LangSmith traces — threads not instrumented will be absent. Join as LEFT JOIN to FCT_AI_ASSISTANT_THREADS.
- `FIRST_TOKEN_LATENCY_MS` may be null if no first-token timestamp was captured in traces
- Cost estimates are model-based approximations, not actual billed amounts

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Created context file — confirmed implemented (~2M rows, updated 2026-04-02) | Sai (via Jarvis) |
