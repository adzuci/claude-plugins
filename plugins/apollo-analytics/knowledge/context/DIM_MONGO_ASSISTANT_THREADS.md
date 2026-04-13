# DIM_MONGO_ASSISTANT_THREADS

> AI Assistant conversation threads from MongoDB. One row per assistant thread.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_ASSISTANT_THREADS` |
| **Grain** | One row per assistant thread |
| **Row count** | ~1.2M (2026-03-06) |
| **Refresh cadence** | Daily (dbt model). CDC config: `dags/cdc/config/assistant_threads.yml` |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | CDC ingestion via `dags/cdc/config/assistant_threads.yml`. dbt model likely in dbt_models_group_1. |

## Description

AI Assistant thread dimension. Tracks conversations with Apollo's AI Assistant product — one row per thread. Joined with `FCT_MONGO_ASSISTANT_THREAD_MESSAGES` for message-level analysis. Primary source for WAU engagement metrics.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `assistant_threads` collection | Primary source (CDC ingestion) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ASSISTANT_THREAD_ID | TEXT (PK) | Unique thread identifier | Join key to FCT_MONGO_ASSISTANT_THREAD_MESSAGES |
| USER_ID | TEXT | User who created the thread | ⚠️ NOT `apollo_user_id` — join to DIM_USERS on `du.apollo_user_id = at.user_id`; team_id not on this table |
| CREATION_TYPE_CD | TEXT | Classification of thread origin | ⚠️ NOT `thread_type`; NULL or non-'proactive' = user-initiated; 'proactive' = system-initiated |
| CREATED_AT_UTC | TIMESTAMP | When the thread was created | ⚠️ NOT `created_at`; use for date windowing |

## How It's Used

### Canonical base query (confirmed 2026-03-26)

**Actual column names** (differ from what was originally documented):
- `at.user_id` — thread owner (NOT `apollo_user_id`)
- `at.creation_type_cd` — thread type (NOT `thread_type`)
- `at.created_at_utc` — date (NOT `created_at`)
- No `team_id` on this table — get it via JOIN to `DIM_USERS.apollo_team_id`
- `DIM_USERS`, `DIM_TEAMS_DAILY`, `DIM_TEAMS` all live in `ANALYTICS_DATASCIENCE`

```sql
WITH threads AS (
    SELECT
        at.user_id                              AS apollo_user_id,
        du.apollo_team_id,
        at.creation_type_cd                     AS thread_type,
        DATE(at.created_at_utc)                 AS thread_date,
        at.assistant_thread_id,
        atm.assistant_thread_message_id,
        TRY_PARSE_JSON(atm.content)             AS message_content,
        COUNT(DISTINCT CASE WHEN atm.author_role_cd = 'user' THEN atm.seq_num ELSE NULL END)
            OVER (PARTITION BY at.assistant_thread_id) AS user_message_count
    FROM   ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_ASSISTANT_THREADS         at
    JOIN   ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_ASSISTANT_THREAD_MESSAGES atm  ON atm.assistant_thread_id = at.assistant_thread_id
    JOIN   ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS                            du   ON du.apollo_user_id = at.user_id
    JOIN   ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY                     dtd  ON dtd.apollo_team_id = du.apollo_team_id
                                                                                      AND dtd.date = DATE(at.created_at_utc)
    WHERE  du.is_apollo_employee_ind = 0
      AND  dtd.is_core_account_ind = 1 AND dtd.is_free_email_domain_ind = 0
      AND  dtd.is_paid_ind = 1
),
tool_calls AS (
    SELECT  th.*,
            con.value,
            COALESCE(con.value:data:tool_name::STRING, con.value:data:toolName::STRING) AS tool_name
    FROM    threads th,
            LATERAL FLATTEN(input => th.message_content) con
),
actives AS (
    SELECT DISTINCT apollo_user_id, apollo_team_id, thread_date
    FROM   tool_calls
    WHERE  (thread_type IS NULL OR thread_type <> 'proactive'
            OR (thread_type = 'proactive' AND user_message_count > 1))
      AND  tool_name IS NOT NULL
)
```

### Retention query pattern — all weeks W1–W12, Paid Core (confirmed 2026-03-26)

**Canonical file:** `teammates/pubudu_wariyapola/ai_assistant_retention_all_weeks.sql`

**Rules — non-negotiable:**
1. **NEVER add a date floor to find first_active_date.** Query ALL history (`thread_date < current_date()` only).
2. **NEVER use calendar-week alignment for retention.** Always compute W_N as days relative to each user's `first_active_date`, then aggregate by cohort.
3. **No date ceiling on the activity lookup.** The actives CTE has no date filter — intentional.
4. **Run with `ALTER SESSION SET WEEK_START = 7`** so `DATE_TRUNC('week', ...)` returns Sunday-start weeks.
5. **All team types flow through `ai_assistant_active`** — Paid Core filter goes in `user_week_retention`, not in `threads`. Team type is resolved at each user's first activation date.

```sql
alter session set week_start = 7;

with threads as (
    select      at.user_id                                      as apollo_user_id
                , du.apollo_team_id
                , case
                    when dtd.is_core_account_ind = 1 and dtd.is_free_email_domain_ind = 0 and dtd.is_paid_ind = 1 then 'Paid Core'
                    when dtd.is_core_account_ind = 1 and dtd.is_free_email_domain_ind = 0 and dtd.is_paid_ind = 0 then 'Free Core'
                    when (dtd.is_core_account_ind = 0 or dtd.is_free_email_domain_ind = 1) and dtd.is_paid_ind = 1 then 'Paid Non-Core'
                    else 'Free Non-Core'
                  end                                           as team_type
                , at.creation_type_cd                           as thread_type
                , at.assistant_thread_id
                , date(at.created_at_utc)                       as thread_date
                , try_parse_json(atm.content)                   as message_content
                , count(distinct case when atm.author_role_cd = 'user' then atm.seq_num else null end)
                    over (partition by at.assistant_thread_id)  as user_message_count
    from        analytics_db.analytics_dataplatform.dim_mongo_assistant_threads         at
    join        analytics_db.analytics_dataplatform.fct_mongo_assistant_thread_messages atm on atm.assistant_thread_id = at.assistant_thread_id
    join        analytics_db.analytics_datascience.dim_users                            du  on du.apollo_user_id = at.user_id
    join        analytics_db.analytics_datascience.dim_teams_daily                     dtd on dtd.apollo_team_id = du.apollo_team_id
                                                                                          and dtd.date = date(at.created_at_utc)
    where       du.is_apollo_employee_ind = 0
    and         at.created_at_utc < date_trunc(week, current_date())
),
tool_calls as (
    select th.*, con.value
                , coalesce(con.value:data:tool_name::string, con.value:data:toolName::string) as tool_name
    from   threads th, lateral flatten(input => th.message_content) con
),
ai_assistant_active as (
    select distinct apollo_user_id, apollo_team_id, team_type, thread_date
    from   tool_calls
    where  (thread_type is null or thread_type <> 'proactive' or (thread_type = 'proactive' and user_message_count > 1))
    and    tool_name is not null
),
first_active_date_user as (
    select apollo_user_id, min(thread_date) as first_active_date_user
    from   ai_assistant_active
    where  thread_date < current_date()
    group by 1
),
first_active_date_user_type as (
    select fau.apollo_user_id, fau.first_active_date_user, act.team_type
    from   first_active_date_user fau
    join   ai_assistant_active act on act.apollo_user_id = fau.apollo_user_id
                                  and act.thread_date    = fau.first_active_date_user
),
week_offsets as (
    select (row_number() over (order by seq4())) as week_offset
    from   table(generator(rowcount => 12))
),
user_week_retention as (
    select      faut.apollo_user_id
                , date_trunc(week, faut.first_active_date_user)                   as first_active_week
                , wo.week_offset
                , max(case when act.apollo_user_id is not null then 1 else 0 end) as retained
    from        first_active_date_user_type faut
    cross join  week_offsets wo
    left join   ai_assistant_active act
                    on  act.apollo_user_id = faut.apollo_user_id
                    and act.thread_date    >  faut.first_active_date_user + ((wo.week_offset - 1) * 7)
                    and act.thread_date    <= faut.first_active_date_user + (wo.week_offset * 7)
    where       faut.team_type = 'Paid Core'
    and         date_trunc(week, faut.first_active_date_user) + (6 + wo.week_offset * 7) < current_date()
    group by    1, 2, 3
)
select      first_active_week
            , week_offset
            , count(distinct apollo_user_id)                                                as cohort_size
            , sum(retained)                                                                  as retained_users
            , round(div0(sum(retained), count(distinct apollo_user_id)) * 100, 1)          as retention_pct
from        user_week_retention
group by    1, 2
order by    1, 2;
```

### Engagement & retention query library (confirmed 2026-03-26)

**File:** `teammates/pubudu_wariyapola/ai_assistant_engagement_queries.sql`

| # | Query | Key dimension |
|---|---|---|
| 1 | W4 retention by W1 thread count | 1 / 2 / 3+ active threads in W1 |
| 2 | W4 retention by W1 tool-call count | 1 / 2-3 / 4+ tool calls in W1 |
| 3 | W4 retention by W1 tool name | which tools were called in W1 |
| 4 | W4 retention by W1 message count | user message count buckets (all threads, not just tool-call threads) |
| 5 | W4 retention — thread-start definition | alternative active: any non-proactive thread, no tool call required |
| 6 | First session conversion funnel | open → message → tool call within 30 min; uses Amplitude + thread data |
| 7 | Assistant opens by day (raw) | Amplitude event_type_id `839645913` = 'Assistant Opened' |
| 8 | Threads / messages / tool calls by thread | raw thread-level aggregation |
| 9 | Threads by user message count by week | distribution of message depth per thread |
| 10 | Tool name raw | distinct tool call per user / thread / date |
| 11 | Support tickets — AI Assistant | full-text search across ticket + chat log body for 'ai assistant' |
| 12 | User feedback — raw | `feedback_cd` + message receiving feedback (thumbs up/down) |
| 13 | F7D high-value action completion rate | sequence activated, workflow run, power up, report/dashboard within 7 days of activation |

**Additional column facts confirmed by these queries:**
- `atm.sent_at_utc` — message timestamp on `FCT_MONGO_ASSISTANT_THREAD_MESSAGES`
- `atm.author_role_cd` — `'user'` or `'assistant'`
- Apollo RevOps instance exclusion: `apollo_team_id <> '551e3ef07261695147160000'`
- `DIM_USERS_DAILY` used for point-in-time team type (join on `apollo_user_id` + `date`)
- `FCT_AMPLITUDE_EVENTS.event_type_id = 839645913` = 'Assistant Opened'

**Additional tables referenced in this query library:**
- `ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS` — support tickets (query 11)
- `ANALYTICS_DB.ANALYTICS.DIM_INTERCOM_CUSTOMER_CHAT_LOGS` — chat log bodies joined via `ticket_or_conversation_id` (query 11)
- `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_CAMPAIGNS` — sequences; `creation_type_cd = 'ai_assistant'` for AI-created (query 13)
- `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES` — email sends; `status = 'Completed'` for sent (query 13)
- `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_RULE_CONFIGS` — workflows; `rule_config_source_cd = 'ai_assistant'`, `type_cd = 'workflow'` (query 13)
- `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_RULE_ACTIONS` — workflow runs (query 13)
- `feedback_cd` — column on `DIM_MONGO_ASSISTANT_THREADS` (thumbs up/down); join to messages via `assistant_thread_id` to get the message text (query 12)

**Pattern notes:**
- Queries 1–5 and 7–10 omit `DIM_TEAMS_DAILY` (commented out) — use `DIM_USERS_DAILY` or no team filter when team segmentation isn't needed; saves significant cost
- Query 6 combines Amplitude opens + first thread datetime to get true first open (Amplitude timestamps can lag)
- Query 4 counts messages from ALL threads in W1, not just tool-call threads — different denominator from the standard active definition
- Query 13: F7D window is `first_active_date` to `first_active_date + 7`; cohorts where the F7D window hasn't elapsed are NULLed out via `CASE WHEN first_active_week < date_trunc(week, current_date() - 7)`

### Key consumers
- AI product debrief (run_ai_debrief.py — canonical WAU source)
- Data Science (WAU reporting)
- Product Analytics (AI feature team)

## Known Issues & Gotchas

- **`THREAD_TYPE` determines user interaction**: non-proactive threads are always user-initiated. Only proactive threads need the `user_message_count > 1` check. Do NOT add `user_message_count > 0` to non-proactive threads — it's redundant and was confirmed incorrect.
- **Do NOT use `TEAM_AI_ASSISTANT_DAILY` for WAU** — its `HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS` definition may include proactive threads. Use this table + FCT_MONGO_ASSISTANT_THREAD_MESSAGES for canonical WAU.
- Use `< {END_DATE}` (last completed Sunday), not `< CURRENT_DATE()` — partial current week distorts trends.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial — column usage pending) | Brighid (via Claude) |
| 2026-03-24 | Added key columns, WAU definition + full query pattern, thread_type filter logic, date window pattern | Pubudu (via Claude) |
| 2026-03-26 | Updated retention query to canonical all-weeks W1–W12 methodology; added engagement query library (10 queries) | Pubudu (via Jarvis) |
| 2026-03-31 | Fixed Key Columns table: actual column names are USER_ID (not APOLLO_USER_ID), CREATION_TYPE_CD (not THREAD_TYPE), CREATED_AT_UTC (not CREATED_AT) — confirmed across all production SQL | Pubudu (via Jarvis) |
