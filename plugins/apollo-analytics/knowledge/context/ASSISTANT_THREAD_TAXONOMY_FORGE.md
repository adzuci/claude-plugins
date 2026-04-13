# ASSISTANT_THREAD_TAXONOMY_FORGE

> AI-generated outcome classifications for AI Assistant threads. Analyzes conversation transcripts via GPT-4o-mini to classify success, failure reasons, and agents involved.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.ASSISTANT_THREAD_TAXONOMY_FORGE` |
| **Grain** | One row per thread_id (use latest row — known duplicate issue) |
| **Row count** | ~1.2M (2026-04-02) |
| **Refresh cadence** | Daily (Airflow DAG, runs at 5 AM UTC with 2-day lookback) |
| **Trust level** | Use with caution — known duplicate rows at thread_id level; fix and prod promotion in progress |
| **Owner** | Data Platform / AI Analytics (Sai Sarvepalli) |
| **DAG** | Airflow DAG — uses OpenAI GPT-4o-mini via DAPI to analyze conversation transcripts |

## Description

Runs daily via Airflow, sending AI Assistant conversation transcripts to GPT-4o-mini for classification. Produces outcome labels (success/failure/assistant_blocked), identifies agents and failure reasons, and enriches threads with conversation metadata. Joined into `FCT_AI_ASSISTANT_THREADS` as the outcome classification source.

**Known issue:** Duplicate rows exist at the thread_id grain. Always use the latest row per thread when joining:
```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY thread_id ORDER BY <created_at_col> DESC) AS rn
  FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.ASSISTANT_THREAD_TAXONOMY_FORGE
) WHERE rn = 1
```

## Upstream Sources

| Source | Relationship |
|---|---|
| AI Assistant conversation transcripts | Sent to GPT-4o-mini via DAPI for classification |
| `FCT_MONGO_ASSISTANT_THREAD_MESSAGES` | Source of transcript content |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| THREAD_ID | TEXT | FK to FCT_AI_ASSISTANT_THREADS | **Duplicates exist — use latest row** |
| OUTCOME | TEXT | `success`, `failure`, `assistant_blocked` | Top-level outcome |
| AGENTS_INVOLVED | TEXT | Agents present in the conversation | |
| FAILED_AGENTS | TEXT | Agents that failed | |
| FAILURE_REASONS | ARRAY | Structured failure reason codes | |
| FAILURE_DETAILS | TEXT | Free-text explanation of failure | |
| CONVERSATION_LENGTH_BUCKET | TEXT | Short / medium / long | |
| SEARCH_TYPE | TEXT | Type of search performed | |
| NO_RESPONSE_CATEGORIES | TEXT | Categories when assistant gave no response | |
| HAS_CONTENT_CENTER | BOOLEAN | Whether content center was involved | |
| USER_TENURE_BUCKET | TEXT | User tenure grouping | |
| USER_ACTIVITY_TIER | TEXT | User activity tier | |

## How It's Used

### Common query patterns
- Outcome rate analysis — AVG(outcome = 'success') for success rate
- Failure root cause — GROUP BY failure_reasons to rank top failure modes
- Agent failure analysis — filter FAILED_AGENTS IS NOT NULL
- Join to FCT_AI_ASSISTANT_THREADS for enriched thread-level analysis

### Key consumers
- FCT_AI_ASSISTANT_THREADS (joined to provide outcome classification columns)
- AI quality monitoring dashboards

## Known Issues & Gotchas

- **Duplicate rows** at thread_id level — always deduplicate to latest row before joining or aggregating
- 2-day lookback means threads from the last 2 days may be reclassified on subsequent runs
- GPT-4o-mini classification quality — outcomes are AI-generated, not ground truth
- `OUTCOME` values: `success`, `failure`, `assistant_blocked` (not the same as `non_regrettable_block` used in FCT_AI_ASSISTANT_THREADS — mapping happens during join)

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Created context file from Notion AI Assistant Analytics Data Models doc | Sai (via Jarvis) |
