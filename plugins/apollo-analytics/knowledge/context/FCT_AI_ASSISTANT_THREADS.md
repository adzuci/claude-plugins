# FCT_AI_ASSISTANT_THREADS

> Thread-level fact table for AI Assistant activity — the new canonical source for AI Assistant analytics. Supersedes raw `DIM_MONGO_ASSISTANT_THREADS` + `FCT_MONGO_ASSISTANT_THREAD_MESSAGES` joins.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS` |
| **Grain** | One row per AI Assistant thread (`ASSISTANT_THREAD_ID`) |
| **Row count** | ~1,455,871 |
| **Refresh cadence** | Daily |
| **Trust level** | High — new canonical table |
| **Owner** | Data Science |

## Description

Each row is one AI Assistant conversation thread, pre-joined and enriched with user/team context, outcome classification, latency metrics, LLM cost estimates, and engagement flags. Replaces the raw `DIM_MONGO_ASSISTANT_THREADS` + message-level lateral flatten pattern used in the old retention queries.

**Key definition — "active" thread:** `USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE`
This is the new-way equivalent of the old: non-proactive thread with at least one tool call.

## Key Columns

| Column | Type | Description |
|---|---|---|
| ASSISTANT_THREAD_ID | TEXT (PK) | Unique thread identifier |
| APOLLO_USER_ID | TEXT | User who owns the thread |
| APOLLO_TEAM_ID | TEXT | User's team (renamed from TEAM_ID — 2026-04 drift) |
| THREAD_DATE | DATE | Date of thread creation |
| THREAD_NUM_LIFETIME | NUMBER | User's Nth thread ever (1 = first thread) |
| THREAD_NUM_ENGAGED_LIFETIME | NUMBER | Nth engaged thread |
| DAYS_SINCE_LAST_THREAD | NUMBER | Days since user's previous thread |
| CREATION_TYPE_CD | TEXT | Thread creation type |
| IS_PROACTIVE | BOOLEAN | True if system-initiated (proactive) thread |
| USER_INTERACTION_FLAG | BOOLEAN | **True if user actively engaged** — use this as the active filter |
| HAS_TOOL_CALLS | BOOLEAN | True if thread had at least one tool call |
| DISTINCT_TOOLS_COUNT | NUMBER | Number of distinct tools called |
| TOTAL_TOOL_CALLS | NUMBER | Total tool calls in thread |
| TOOL_NAMES_LIST | TEXT | Comma-separated list of tools used |
| OUTCOME_CD | TEXT | `success`, `failure`, `non_regrettable_block`, `unclassified` (renamed from OUTCOME) |
| IS_SUCCESS | NUMBER | 1 if outcome = success |
| IS_REGRETTABLE_FAILURE | NUMBER | 1 if regrettable failure |
| FIRST_USER_MESSAGE_TEXT | TEXT | First user message (truncated to 500 chars) |
| LAST_ASSISTANT_MESSAGE_TEXT | TEXT | Last assistant message (truncated to 500 chars) |
| CONVERSATION_LENGTH_BUCKET | TEXT | Short/medium/long bucketing |
| TOTAL_MESSAGES | NUMBER | Total messages in thread |
| USER_MESSAGES | NUMBER | User message count |
| FIRST_TOKEN_LATENCY_MS | NUMBER | Time to first token |
| TOTAL_COST | FLOAT | LLM API cost estimate (renamed from LLM_ESTIMATED_COST_USD) |
| MODEL_VERSION | TEXT | Model used (renamed from LLM_MODEL_NAME) |
| TOTAL_TOKENS | NUMBER | Total tokens consumed (renamed from LLM_TOTAL_TOKENS) |
| TOTAL_PROMPT_TOKENS | NUMBER | Prompt tokens |
| TOTAL_PROMPT_COST | FLOAT | Prompt cost |
| TOTAL_COMPLETION_TOKENS | NUMBER | Completion tokens |
| TOTAL_COMPLETION_COST | FLOAT | Completion cost |
| PRIMARY_AGENT | TEXT | Primary agent involved |
| ALL_AGENTS_INVOLVED | TEXT | All agents in the thread |
| SUCCESSFUL_AGENTS | TEXT | Agents that succeeded |
| FAILED_AGENTS | TEXT | Agents that failed |
| FAILURE_REASONS | TEXT | Failure reason codes |
| FAILURE_EXPLANATION | TEXT | Human-readable failure explanation |
| FAILURE_DETAILS | TEXT | Detailed failure info |
| FORGE_ANALYZED_AT | TIMESTAMP_NTZ | When Forge analysis was applied |
| CONVERSATION_DURATION_SECONDS | NUMBER | Thread duration in seconds |
| IS_MULTI_TURN | BOOLEAN | Multi-turn conversation |
| IS_SINGLE_EXCHANGE | BOOLEAN | Single exchange only |
| IS_ZOMBIE | BOOLEAN | Zombie thread (no meaningful interaction) |
| THREAD_TYPE | TEXT | Thread classification type |
| THREAD_TITLE | TEXT | Thread title |
| THREAD_STATUS_CD | TEXT | Thread status code |
| THREAD_TAGS | TEXT | Tags applied to thread |
| IS_FIRST_THREAD_EVER | BOOLEAN | True if this is the user's first thread |
| IS_REPEAT_USER | BOOLEAN | True if user has prior threads |
| HAS_USER_FEEDBACK | BOOLEAN | User provided thumbs up/down |
| FEEDBACK_SENTIMENT | TEXT | Feedback sentiment |
| USER_TENURE_BUCKET | TEXT | User tenure grouping |
| USER_ACTIVITY_TIER | TEXT | User activity tier |
| DATA_QUALITY_SCORE | NUMBER | 0-100 quality score for the thread record |
| WEEK_START_DATE | TIMESTAMP_NTZ | Week start for weekly aggregation |
| MONTH_START_DATE | TIMESTAMP_NTZ | Month start |

## Common Query Patterns

```sql
-- New-way "active" AI Assistant users (equivalent to old tool_calls CTE)
SELECT DISTINCT APOLLO_USER_ID, THREAD_DATE
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE USER_INTERACTION_FLAG = TRUE
  AND HAS_TOOL_CALLS = TRUE;

-- W4 AI Assistant retention (new way — Paid Core)
-- See team/leo/ai_assistant_retention_comparison.py for full query

-- Outcome breakdown by week
SELECT WEEK_START_DATE, OUTCOME_CD, COUNT(*) AS threads
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE USER_INTERACTION_FLAG = TRUE
GROUP BY 1, 2 ORDER BY 1 DESC;

-- LLM cost by model
SELECT MODEL_VERSION, SUM(TOTAL_COST) AS total_cost, COUNT(*) AS threads
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE THREAD_DATE >= CURRENT_DATE - 30
GROUP BY 1 ORDER BY 2 DESC;
```

## New vs Old Way — Retention Comparison (2026-03-19)

Validated against old `DIM_MONGO_ASSISTANT_THREADS` lateral flatten approach. Results are very close (~1-2pt differences) — new way picks up ~5-10% more activated users per week (broader coverage), with marginally lower W4 login rate but slightly higher W4 AI retention rate.

| Week | Old Activated | New Activated | Old W4 AI Retention | New W4 AI Retention |
|---|---|---|---|---|
| 2026-02-09 | 1,759 | 1,905 | 10.8% | 11.5% |
| 2026-02-02 | 1,927 | 2,087 | 10.9% | 11.1% |
| 2026-01-26 | 1,544 | 1,585 | 10.4% | 10.6% |
| 2026-01-19 | 1,293 | 1,335 | 11.8% | 12.4% |
| 2026-01-12 | 1,292 | 1,326 | 12.6% | 13.2% |
| 2026-01-05 | 1,260 | 1,263 | 13.4% | 14.3% |

New way runs significantly faster (no lateral flatten + JSON parse).

## Related Tables

| Table | Relationship |
|---|---|
| `TEAM_AI_ASSISTANT_DAILY` | Downstream daily team-level aggregation |
| `USER_AI_ASSISTANT_DAILY` | Downstream daily user-level aggregation |
| `DIM_MONGO_ASSISTANT_THREADS` | Source (raw) — use FCT table instead |
| `FCT_MONGO_ASSISTANT_THREAD_MESSAGES` | Source (raw) — use FCT table instead |

## Known Issues & Gotchas

- **Use `USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE`** as the "active" filter — equivalent to old non-proactive + tool_call definition
- **`DATA_QUALITY_SCORE`** — records with score = 0 may have incomplete data; consider filtering `DATA_QUALITY_SCORE > 0` for analysis
- **Paid Core filter** — this table has no team_type pre-joined; join to `DIM_USERS` + `DIM_TEAMS_DAILY` for segment filtering

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file | Leo (via Claude) |
| 2026-04-10 | Schema drift fix: TEAM_ID→APOLLO_TEAM_ID, OUTCOME→OUTCOME_CD, LLM cols renamed, 40+ new cols | Bridie (Beat 4) |
