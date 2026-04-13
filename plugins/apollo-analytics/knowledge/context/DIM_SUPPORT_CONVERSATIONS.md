# DIM_SUPPORT_CONVERSATIONS

> Support/CX conversation dimension. One row per support conversation.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS` |
| **Grain** | One row per support conversation |
| **Row count** | ~4.3M (2026-03-06) |
| **Refresh cadence** | Unknown — not found in airflow-dags. Likely dbt or external integration. |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | <!-- TODO: likely CX / Support Analytics --> |
| **DAG** | Not found in airflow-dags. Likely built by external integration (Intercom/Zendesk) or dbt model. |

## Description

Support conversation tracking (26 distinct users, 9.6K queries). Used for CX analytics, support volume tracking, and customer health analysis.

## Upstream Sources

| Source | Relationship |
|---|---|
| Support platform (Intercom/Zendesk) | Primary source |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT (PK) | Unique conversation identifier | **Use this as the grain key for COUNT(DISTINCT) — not TICKET_ID which can be NULL for chat conversations** |
| CONVERSATION_CREATED_AT | TIMESTAMP | When the conversation was created | **Use this for date filtering — NOT `CREATED_AT`** |
| GENERAL_CONVERSATION_TOPIC | TEXT | AI-classified topic category | **Use this for topic filtering — `CONVERSATION_MAIN_CATEGORY` is NULL across all 4.4M rows** |
| APOLLO_TEAM_ID | TEXT | Team associated with the conversation | FK to DIM_MONGO_TEAMS |
| APOLLO_USER_ID | TEXT | User who submitted the ticket | |

**Known topic values in `GENERAL_CONVERSATION_TOPIC` (high volume):**
- `Emails` — #1 topic company-wide
- `Sequences`
- `Subscription and Usage Management`
- `Data Management`
- `CSV Enrichment`
- `People Search`
- `Companies Search`
- `Workflows`
- `Calls`
- `Chrome Extension`
- `Hubspot`, `API`

## How It's Used

### Common query patterns
```sql
-- Monthly ticket volume by topic
SELECT
    DATE_TRUNC('month', CONVERSATION_CREATED_AT) AS month,
    GENERAL_CONVERSATION_TOPIC,
    COUNT(*) AS tickets
FROM ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS
WHERE CONVERSATION_CREATED_AT >= DATEADD(month, -6, CURRENT_DATE)
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- Join to full conversation text
SELECT s.CONVERSATION_ID, s.GENERAL_CONVERSATION_TOPIC, c.SUMMARY
FROM ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS s
JOIN ANALYTICS_DB.ANALYTICS_COMMON.CONVERSATION_SUMMARY c
    ON s.CONVERSATION_ID = c.CONVERSATION_ID
WHERE s.GENERAL_CONVERSATION_TOPIC = 'Emails'
  AND s.CONVERSATION_CREATED_AT >= CURRENT_DATE - 30;
```

### Ticket classification — canonical approach (established 2026-04-02)

**Always use LLM classification, not regex, to confirm tickets belong to a feature area.**

Steps:
1. Pull the full concatenated `search_text` using the query below with an appropriate keyword pre-filter (e.g. `LIKE '%qualify account%'`)
2. Send each ticket's `search_text` to Claude for binary classification (confirmed / false positive)
3. Use only LLM-confirmed tickets in the analysis

The exception is when you have no reasonable initial keyword query — in that case pull a broader sample and rely entirely on LLM classification.

The canonical script for Default Fields tickets: `teammates/pubudu_wariyapola/Analyses/Default_Fields_Ticket_Investigation_2026_03_30/Python/classify_df_tickets.py`

Apply the same pattern for other feature areas — swap the keyword pre-filter and update the classification prompt.

---

### AI Assistant support ticket search (confirmed 2026-03-26)

Full-text search across all ticket fields. Combines `DIM_SUPPORT_CONVERSATIONS` metadata with `DIM_INTERCOM_CUSTOMER_CHAT_LOGS` body text, concatenates into a single `search_text` column, then filters by keyword.

**Confirmed additional columns (from query):** `ticket_id`, `ticket_title`, `conversation_subject`, `ticket_description`, `conversation_body`, `ai_generated_summary`, `conversation_ai_generated_tags`, `conversation_live_tag_names`, `account_arr`, `ticket_status`, `conversation_request_type`, `ticket_category`

**Join key to DIM_INTERCOM_CUSTOMER_CHAT_LOGS:** `cl.ticket_or_conversation_id = con.conversation_id` — note: the join key on the chat logs table is `ticket_or_conversation_id`, NOT `conversation_id`.

**Multiple chat log rows per conversation** — use `listagg(cl.body)` to aggregate.

**`GROUP BY ALL` pattern — IMPORTANT:** For this query to work with `GROUP BY ALL`, all columns referenced in `search_text` must also be selected as individual columns directly in the SELECT list. `GROUP BY ALL` only picks up columns that appear directly as SELECT expressions — columns embedded only inside a complex expression are not automatically included. The working pattern is below (confirmed working 2026-04-02).

```sql
with conversations as (
    select      dt.apollo_team_id
                , dt.account_name
                , coalesce(con.account_arr, dt.arr, 0) as arr
                , con.conversation_created_at
                , con.ticket_id
                , con.conversation_id
                , con.ticket_title
                , con.conversation_subject
                , con.ticket_description
                , con.conversation_body as conversation_body_part_1
                , listagg(cl.body) within group (order by cl.created_at) as conversation_body_part_2
                , con.ticket_category
                , con.ai_generated_summary
                , con.conversation_ai_generated_tags
                , con.conversation_live_tag_names
                , lower(coalesce(con.ticket_title, '')                                          || ' ' ||
                        coalesce(con.conversation_subject, '')                                  || ' ' ||
                        coalesce(con.ticket_description, '')                                    || ' ' ||
                        coalesce(con.conversation_body, '')                                     || ' ' ||
                        coalesce(listagg(cl.body) within group (order by cl.created_at), '')   || ' ' ||
                        coalesce(con.ai_generated_summary, '')                                  || ' ' ||
                        coalesce(con.conversation_ai_generated_tags, '')                        || ' ' ||
                        coalesce(con.conversation_live_tag_names, '')) as search_text
    from        analytics_db.analytics.dim_support_conversations            con
    left join   analytics_db.analytics.dim_intercom_customer_chat_logs     cl  on cl.ticket_or_conversation_id = con.conversation_id
    left join   analytics_db.analytics_datascience.dim_teams               dt  on dt.apollo_team_id = con.apollo_team_id
    where       (con.conversation_main_category is null or con.conversation_main_category != 'Invalid/Spam')
    group by    all
)
select * from conversations where search_text like any ('%qualify account%', '%qualify contact%');
```

### AI debrief — weekly ticket classification (keyword scoring)

No dedicated topic label for AI — must classify by content. Pull body text from `DIM_INTERCOM_CUSTOMER_CHAT_LOGS` (join on CONVERSATION_ID), score in Python across signal lists, classify to highest-scoring category. Use 10-week window snapped to completed Sundays.

```sql
-- Base query: AI-relevant support conversations with body text
SELECT
    s.CONVERSATION_ID,
    DATE_TRUNC('week', s.CONVERSATION_CREATED_AT) AS week_starting_sun,
    s.AI_GENERATED_SUMMARY,
    s.AI_ISSUE_SUMMARY,
    c.BODY
FROM ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS s
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_INTERCOM_CUSTOMER_CHAT_LOGS c
    ON s.CONVERSATION_ID = c.CONVERSATION_ID
WHERE s.CONVERSATION_CREATED_AT >= {START_DATE}
  AND s.CONVERSATION_CREATED_AT < {END_DATE}
  AND (
    s.AI_GENERATED_SUMMARY ILIKE '%ai%'
    OR s.AI_ISSUE_SUMMARY ILIKE '%ai%'
    OR s.AI_GENERATED_SUMMARY ILIKE '%assistant%'
    OR s.AI_GENERATED_SUMMARY ILIKE '%enrich%'
  )
ORDER BY s.CONVERSATION_CREATED_AT;
```

Python classification: score each row by counting keyword hits in AI_GENERATED_SUMMARY + AI_ISSUE_SUMMARY + BODY across three lists (AI Assistant, Power Ups, AI Messaging). Classify to highest-score category. Produce weekly count table.

### Key consumers
- CX/Support team
- Customer Success
- Product analytics — support volume signal in debriefs (AI debrief: weekly 10-week view)

## Known Issues & Gotchas

- **`CONVERSATION_MAIN_CATEGORY` is NULL** across all 4.4M rows — do not use. Use `GENERAL_CONVERSATION_TOPIC` instead.
- **`CREATED_AT` does not exist** as a column — use `CONVERSATION_CREATED_AT` for date filtering.
- Row count: ~4.4M (verified 2026-03-20)
- In ANALYTICS schema (mixed trust) — verify refresh timing before relying on recency.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial — column usage pending) | Brighid (via Claude) |
| 2026-03-20 | Added columns, topic values, query patterns, gotchas (CONVERSATION_MAIN_CATEGORY=NULL, CONVERSATION_CREATED_AT anchor) | Leo (verified via Snowflake) |
| 2026-03-24 | Added AI debrief weekly classification query pattern; noted DIM_INTERCOM_CUSTOMER_CHAT_LOGS join for body text | Pubudu (via Claude) |
