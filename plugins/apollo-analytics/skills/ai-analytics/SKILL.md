---
name: ai-analytics
description: "Answer quantitative metric and analysis questions about Apollo's AI capabilities — AI Assistant usage/engagement (DAU/WAU/MAU, active users, retention, W4), thread outcomes and success/regrettable-failure rates, thread latency and LLM cost, powerups (credits), messaging (email open/reply rates, sequences, genpipe), and content center. Use for any AI-product metric or analysis question. For qualitative themes (what users say/complain about), use assistant-voc instead."
---

# AI Assistant Analytics

An analyst, engineer, or stakeholder wants to answer a question about AI Assistant usage, outcomes, powerups, messaging, or content center activity. Your job is to identify the right table, apply the correct filters, run the query, and return a clear answer.

**Scope:** this skill answers **quantitative** questions (counts, rates, trends) via SQL. For **qualitative** themes — what users are saying, complaining about, or struggling with in assistant conversations — use `data:assistant-voc` (Cortex Search RAG) instead.

______________________________________________________________________

## Arguments

`$ARGUMENTS` is a free-form question. Examples:

- "how many active AI assistant users did we have last week?"
- "what's the success rate of threads this month?"
- "which teams are using powerups the most?"
- "show me email open rates by message type for last 30 days"
- "how many content center threads were created this week?"

______________________________________________________________________

## Step 0: Registry lookup (advisory)

Before writing any SQL, check if the question maps to a canonical metric. Run via the Snowflake MCP:

```sql
SELECT metric_name, variant, description, metric_sql
FROM ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS
WHERE status = 'approved'
  AND (LOWER(metric_name) LIKE '%ai%' OR LOWER(metric_name) LIKE '%assistant%'
       OR LOWER(metric_name) LIKE '%thread%' OR LOWER(metric_name) LIKE '%powerup%'
       OR LOWER(metric_name) LIKE '%credit%')
```

If a canonical metric matches the user's question, prefer its `metric_sql` over writing from scratch. If no match, proceed with inline SQL as normal.

Also check for a recent intelligence snapshot that may already answer the question. Run via the Snowflake MCP:

```sql
SELECT kernel_id, intelligence, assessed_at
FROM ANALYTICS_DB.PLAYGROUND.INTELLIGENCE_SNAPSHOTS
WHERE kernel_id IN ('ai_assistant_adoption', 'ai_platform_growth', 'ai_platform_health', 'ai_sequence_credits')
  AND assessed_at >= DATEADD('day', -3, CURRENT_TIMESTAMP())
ORDER BY assessed_at DESC
LIMIT 3
```

If a recent snapshot covers the question, use it as context or a complete answer (cite the kernel_id and assessed_at).

______________________________________________________________________

## Step 1: Classify the question

Identify the domain from `$ARGUMENTS`:

| Domain | Keywords | Go to |
|---|---|---|
| **AI Assistant engagement / DAU** | users, active, DAU, WAU, MAU, threads, engaged | Section A |
| **AI Assistant outcomes** | success, failure, regrettable, blocked, outcome, classification | Section B |
| **AI Assistant retention** | W4, retention, cohort, returning, habit | Section C |
| **AI Assistant thread detail** | latency, cost, tokens, model, tool calls, tool names, message count | Section D |
| **Powerups / credits** | powerup, credit, credit usage, feature credit, AI credit | Section E |
| **Messaging / email** | email, sequence, reply rate, open rate, bounce, outreach, genpipe | Section F |
| **Content center** | content center, content_center, AI-generated content | Section G |

If the question spans multiple domains, identify each and run them sequentially.

______________________________________________________________________

## Section A: AI Assistant Engagement

**Table hierarchy (fastest first):**

1. `ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY` — user × day grain. Use for DAU, WAU, MAU, user-level engagement.
1. `ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_DAILY` — team × day grain. Use for team-level adoption counts, active teams.
1. `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS` — thread grain. Use for thread-level detail or when daily tables don't have the column you need.

**Critical filter — "active" definition:**

```sql
-- User level
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE

-- Thread level (equivalent)
WHERE USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE
```

Do NOT use raw thread counts as "active" — this includes proactive/system threads.

**Segment join (for Paid Core filter):**

```sql
-- Join user table to get paid core
JOIN ANALYTICS_DB.ANALYTICS.DIM_USERS u ON u.USER_ID = uad.APOLLO_USER_ID
JOIN ANALYTICS_DB.ANALYTICS.DIM_TEAMS_DAILY dtd
  ON dtd.TEAM_ID = u.TEAM_ID AND dtd.DS = uad.ACTIVITY_DATE
WHERE dtd.IS_PAID_IND = TRUE
  AND dtd.IS_CORE_ACCOUNT_IND = TRUE
  AND dtd.IS_FREE_EMAIL_DOMAIN_IND = FALSE
```

**Common patterns:**

```sql
-- DAU (last 90 days)
SELECT ACTIVITY_DATE, COUNT(DISTINCT APOLLO_USER_ID) AS dau
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
  AND ACTIVITY_DATE >= CURRENT_DATE - 90
GROUP BY 1 ORDER BY 1;

-- Active teams (L30)
SELECT COUNT(DISTINCT APOLLO_TEAM_ID) AS active_teams
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_AI_ASSISTANT_DAILY
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
  AND ACTIVITY_DATE >= CURRENT_DATE - 30;

-- Power users (active 5+ days in last 30d)
SELECT APOLLO_USER_ID, COUNT(*) AS active_days
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
  AND ACTIVITY_DATE >= CURRENT_DATE - 30
GROUP BY 1 HAVING active_days >= 5
ORDER BY 2 DESC LIMIT 20;
```

______________________________________________________________________

## Section B: AI Assistant Outcomes

**Table:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS`

**Outcome values:**

| Value | Meaning |
|---|---|
| `success` | Thread completed successfully |
| `failure` | Regrettable failure — something went wrong that hurt the user |
| `non_regrettable_block` | Assistant blocked — intended behavior (e.g., policy, out-of-scope) |
| `unclassified` | Not yet classified |

**Key columns:**

- `OUTCOME` — coarse: success / failure / non_regrettable_block / unclassified
- `OUTCOME_CLASSIFICATION` — detailed version
- `IS_SUCCESS` — 1/0 flag
- `IS_REGRETTABLE_FAILURE` — 1/0 flag

**Common patterns:**

```sql
-- Outcome breakdown by week
SELECT WEEK_START_DATE, OUTCOME, COUNT(*) AS threads,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY WEEK_START_DATE), 1) AS pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE USER_INTERACTION_FLAG = TRUE
  AND THREAD_DATE >= CURRENT_DATE - 90
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC LIMIT 100;

-- Success rate trend
SELECT WEEK_START_DATE,
       SUM(IS_SUCCESS) AS successes,
       COUNT(*) AS total_active,
       ROUND(SUM(IS_SUCCESS) * 100.0 / COUNT(*), 1) AS success_rate_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE
GROUP BY 1 ORDER BY 1 DESC LIMIT 20;
```

______________________________________________________________________

## Section C: AI Assistant Retention

**Table:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS`

Key columns for retention:

- `IS_FIRST_THREAD_EVER` — boolean, true if this is the user's first thread
- `THREAD_NUM_LIFETIME` — user's Nth thread ever (1 = first)
- `THREAD_NUM_ENGAGED_LIFETIME` — Nth engaged thread
- `DAYS_SINCE_LAST_THREAD` — days since prior thread
- `IS_REPEAT_USER` — boolean

**W4 retention pattern (cohort-based):**

```sql
-- W4 AI Assistant retention — users who were active in week W and also in week W+4
WITH first_week AS (
  SELECT APOLLO_USER_ID,
         DATE_TRUNC('week', MIN(THREAD_DATE)) AS cohort_week
  FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
  WHERE USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE
    AND IS_FIRST_THREAD_EVER = TRUE
  GROUP BY 1
),
w4_active AS (
  SELECT DISTINCT APOLLO_USER_ID, DATE_TRUNC('week', THREAD_DATE) AS active_week
  FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
  WHERE USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE
)
SELECT fw.cohort_week,
       COUNT(DISTINCT fw.APOLLO_USER_ID) AS cohort_size,
       COUNT(DISTINCT w4.APOLLO_USER_ID) AS retained_w4,
       ROUND(COUNT(DISTINCT w4.APOLLO_USER_ID) * 100.0 / COUNT(DISTINCT fw.APOLLO_USER_ID), 1) AS w4_retention_pct
FROM first_week fw
LEFT JOIN w4_active w4
  ON fw.APOLLO_USER_ID = w4.APOLLO_USER_ID
  AND w4.active_week = DATEADD('week', 4, fw.cohort_week)
WHERE fw.cohort_week BETWEEN CURRENT_DATE - 120 AND CURRENT_DATE - 28  -- need 4 weeks to mature
GROUP BY 1 ORDER BY 1 DESC LIMIT 20;
```

Validated benchmark: W4 retention is typically 10-14% for active users.

______________________________________________________________________

## Section D: AI Assistant Thread Detail (Latency, Cost, Model)

**Table:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS`

Key columns:

- `FIRST_TOKEN_LATENCY_MS` — time to first token in ms
- `LLM_ESTIMATED_COST_USD` — estimated LLM API cost
- `LLM_MODEL_NAME` — model used (e.g., claude-sonnet-4-x)
- `LLM_TOTAL_TOKENS` — total tokens
- `TOTAL_TOOL_CALLS` — tool call count
- `TOOL_NAMES_LIST` — comma-separated tool names
- `DISTINCT_TOOLS_COUNT` — number of distinct tools used
- `CONVERSATION_LENGTH_BUCKET` — short / medium / long
- `DATA_QUALITY_SCORE` — 0–100; filter `> 0` for complete records

```sql
-- Cost by model (last 30 days)
SELECT LLM_MODEL_NAME,
       COUNT(*) AS threads,
       ROUND(SUM(LLM_ESTIMATED_COST_USD), 2) AS total_cost_usd,
       ROUND(AVG(LLM_ESTIMATED_COST_USD), 4) AS avg_cost_per_thread
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE THREAD_DATE >= CURRENT_DATE - 30
  AND DATA_QUALITY_SCORE > 0
GROUP BY 1 ORDER BY 3 DESC LIMIT 20;

-- Tool usage distribution
SELECT TOOL_NAMES_LIST, COUNT(*) AS threads
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE USER_INTERACTION_FLAG = TRUE
  AND THREAD_DATE >= CURRENT_DATE - 30
GROUP BY 1 ORDER BY 2 DESC LIMIT 30;
```

______________________________________________________________________

## Section E: Powerups / Credits

Powerups consume credits. Two levels of detail:

**Aggregated (preferred for team-level):**

- `ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS` — team × credit_type grain, pre-aggregated
- `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY` — team × date × credit_type (daily)
- `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_LIMITS_DAILY` — team × date × credit_type limits

**Granular (for detailed drill-downs):**

- `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CREDIT_USAGES` — one row per credit usage event
- `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CREDIT_USAGE_DETAILS` — granular per-action credit records

**Known gotcha:** `credit_type` naming differs between limit rows and usage rows in the same table. Utilization rates can return NaN until the mapping is resolved. If this happens, note it and report raw counts instead of rates.

```sql
-- Top teams by credit usage last 30 days
SELECT team_id, credit_type, SUM(credits_used) AS total_credits
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY
WHERE ds >= CURRENT_DATE - 30
GROUP BY 1, 2
ORDER BY 3 DESC LIMIT 50;
```

______________________________________________________________________

## Section F: Messaging / Email

**Table:** `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EMAILER_MESSAGES_DAILY`

Grain: team × date × campaign_id × message_type × status

**message_type values:**

| Value | Domain |
|---|---|
| `outreach_automatic_email` | Automated sequence emails |
| `outreach_manual_email` | Manual sequence emails |
| `extension_email` | Chrome extension emails |
| `downloaded_email` | Bulk downloads — campaign_id and status are NULL |
| `conversation_followup_email` | Conversation follow-ups |

**Gotchas:**

- 84% of rows are `downloaded_email` — filter out for sequence/outreach analysis
- Filter `ds <= CURRENT_DATE()` to exclude scheduled future sends and corrupt dates

```sql
-- Open and reply rates for sequence emails (last 30 days)
SELECT ds,
       SUM(message_count) AS sent,
       ROUND(SUM(opened_count) * 100.0 / NULLIF(SUM(delivered_count), 0), 1) AS open_rate_pct,
       ROUND(SUM(replied_count) * 100.0 / NULLIF(SUM(delivered_count), 0), 1) AS reply_rate_pct,
       ROUND(SUM(bounced_count) * 100.0 / NULLIF(SUM(delivered_count) + SUM(bounced_count), 0), 1) AS bounce_rate_pct
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EMAILER_MESSAGES_DAILY
WHERE message_type IN ('outreach_automatic_email', 'outreach_manual_email')
  AND ds >= CURRENT_DATE - 30
  AND ds <= CURRENT_DATE()
GROUP BY 1 ORDER BY 1 DESC LIMIT 30;
```

______________________________________________________________________

## Section G: Content Center

Content center is a product area within AI Assistant. Threads related to content center are identified via a dimension on `FCT_AI_ASSISTANT_THREADS` (currently being enriched — branch `feature/fct-threads-team-id-content-center` in dbt_apollo).

**Current state:** The `CONTENT_CENTER` or equivalent dimension may not yet be fully populated in production. Check `FCT_AI_ASSISTANT_THREADS` columns first:

```sql
-- Check if content_center column exists and what values it has
SELECT CONTENT_CENTER_FLAG, COUNT(*) AS threads
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE THREAD_DATE >= CURRENT_DATE - 30
GROUP BY 1;
```

If the column doesn't exist yet or is largely NULL, note this and fall back to filtering on `TOOL_NAMES_LIST` or `FIRST_USER_MESSAGE_TEXT` for content-related threads as a proxy. Flag the limitation in your response.

For feature-level user counts (including AI platform / content center):

```sql
-- AI platform daily users by team
SELECT team_id, ds, ai_platform_user_count
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_FEATURE_USERS_DAILY
WHERE ds >= CURRENT_DATE - 30 AND ai_platform_user_count > 0
ORDER BY ds DESC, ai_platform_user_count DESC LIMIT 50;
```

______________________________________________________________________

## Executing queries

Use the Snowflake MCP to run queries. Always:

- `LIMIT 100` or less for exploratory queries
- Use aggregations before pulling row-level data
- Default to last 30 days unless the question specifies otherwise

If the Snowflake MCP is not available, write the SQL and tell the user to run it manually.

______________________________________________________________________

## Output format

Always include:

1. **Answer** — the direct answer to the question in plain English
1. **Data** — a formatted table of results
1. **Caveats** — any filters applied, known data quality issues, or limitations
1. **Follow-up** — 1-2 logical next questions if useful

______________________________________________________________________

## Error handling

- **Column not found:** Check `FCT_AI_ASSISTANT_THREADS` schema by querying `INFORMATION_SCHEMA.COLUMNS` or the data catalog entry for `FCT_AI_ASSISTANT_THREADS`. The content center column may not be live yet.
- **Metric is NULL or NaN:** For credit utilization, this is a known issue with credit_type mapping. Report raw usage counts instead.
- **Question spans products I don't have tables for:** Say so clearly and point to who to ask (Sai for AI assistant data model, Brighid for foundation tables, #xfn-data-platform for ownership questions).
- **Question about experiments or A/B tests:** Do not answer with observational data. Say: "I can't answer experiment questions with observational data — this needs proper statistical analysis. Ask Andrew Green or check `DIM_MONGO_EXPERIMENT_ASSIGNMENTS`."

## Tracking

- **Query tag:** Before running queries, set the session query tag via the Snowflake MCP: `ALTER SESSION SET QUERY_TAG = '{"app":"jarvis","action":"ai_analytics"}'`
- **Pulse:** After successful completion, log the session via the Snowflake MCP `log-jarvis-session` tool with action `ai_analytics` and a one-line detail (the question summary).
