---
name: assistant-voc
description: Qualitative Voice of Customer insights from Apollo AI Assistant conversations. Uses Cortex Search RAG over indexed conversation chunks to surface top issues, themes, complaints, and user struggles. Ask this anything about what users are saying, struggling with, or complaining about in assistant conversations.
---

# Assistant VoC — Qualitative Conversation Insights

Surface qualitative themes, user issues, complaints, and feedback patterns from Apollo AI Assistant conversations using Cortex Search RAG.

**This skill is qualitative only.** For quantitative metrics (DAU, WAU, success rate, retention, powerups, messaging), use `data:ai-analytics`; for product/weekly rollups, use `data:product-debrief` or `data:weekly-insights`.

______________________________________________________________________

## Step 1 — Run the RAG query

> **Pre-condition:** `DBT_DEVELOPMENT_DB.DBT_SAI_DATASCIENCE.ASSISTANT_MSG_SEARCH_SVC` must exist and be
> queryable. If the search service is missing or unpopulated, the query returns `chunks_retrieved = 0`.

Run the Cortex Search + Complete query below via the Snowflake MCP.

Substitute `<SEARCH_KEYWORDS>`, `<USER_QUESTION>`, and `<DATE_FILTER>` before running.

Derive `<SEARCH_KEYWORDS>` by stripping prose down to keywords:

- "what are the top issues users face?" → `top issues errors problems users assistant`
- "what do users do most in assistant?" → `top actions tasks users do assistant`

Derive `<DATE_FILTER>` from the question's time reference.
**Important:** `SEARCH_PREVIEW` requires a constant string — compute the cutoff date as a literal ISO date (`YYYY-MM-DD`) when writing the file. Do NOT use `TO_CHAR(CURRENT_DATE - N, ...)` or any SQL expression inside the JSON string.

- "last 30 days" → `, "filter": {"@gte": {"THREAD_DATE": "<today minus 30 as YYYY-MM-DD>"}}`
- "last 7 days" / "this week" → `, "filter": {"@gte": {"THREAD_DATE": "<today minus 7 as YYYY-MM-DD>"}}`
- "last 90 days" / "this quarter" → `, "filter": {"@gte": {"THREAD_DATE": "<today minus 90 as YYYY-MM-DD>"}}`
- no time reference → leave `<DATE_FILTER>` empty (searches all-time data)

Example for "last 30 days" when today is 2026-04-16:
`, "filter": {"@gte": {"THREAD_DATE": "2026-03-17"}}`

```sql
WITH search_results AS (
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'DBT_DEVELOPMENT_DB.DBT_SAI_DATASCIENCE.ASSISTANT_MSG_SEARCH_SVC',
            '{"query": "<SEARCH_KEYWORDS>", "columns": ["chunk_for_embedding"], "limit": 100<DATE_FILTER>}'
        )
    ) AS response
),
ranked_chunks AS (
    SELECT
        f.index + 1                                                          AS rank,
        ROUND(f.value:"@scores":"cosine_similarity"::FLOAT, 4)              AS cosine_score,
        ROUND(f.value:"@scores":"reranker_score"::FLOAT, 4)                 AS reranker_score,
        REGEXP_SUBSTR(f.value:"chunk_for_embedding"::STRING,
            'Thread: ([a-f0-9]+)', 1, 1, 'e', 1)                           AS thread_id,
        f.value:"chunk_for_embedding"::STRING                               AS chunk
    FROM search_results,
         LATERAL FLATTEN(input => search_results.response['results'], OUTER => TRUE) f
),
context AS (
    SELECT
        COUNT(CASE WHEN chunk IS NOT NULL THEN 1 END)                        AS chunk_count,
        COALESCE(LISTAGG(chunk, '\n\n---\n\n') WITHIN GROUP (ORDER BY rank), '') AS chunks_text
    FROM ranked_chunks
),
top_examples AS (
    SELECT LISTAGG(
        'Rank ' || rank ||
        ' | cosine: ' || cosine_score ||
        ' | reranker: ' || reranker_score ||
        ' | thread: ' || COALESCE(thread_id, 'n/a') || CHR(10) ||
        LEFT(chunk, 400),
        '\n\n'
    ) WITHIN GROUP (ORDER BY rank) AS examples
    FROM ranked_chunks
    WHERE rank <= 5 AND chunk IS NOT NULL
),
prompt_cte AS (
    SELECT
        c.chunk_count,
        t.examples AS top_scored_examples,
        IFF(
            c.chunk_count = 0,
            'No relevant assistant conversation data found. Try broader keywords.',
            SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large2',
                'You are a senior analyst reviewing Apollo AI Assistant conversation data. ' ||
                'USER QUESTION: <USER_QUESTION> ' ||
                'Based ONLY on the excerpts below, provide a thorough, well-structured answer. ' ||
                'Use numbered lists, be specific, call out patterns or trends. ' ||
                'If the data is insufficient, say so. ' ||
                'EXCERPTS: ' || LEFT(c.chunks_text, 50000)
            )
        ) AS answer
    FROM context c, top_examples t
)
SELECT answer, top_scored_examples, chunk_count AS chunks_retrieved
FROM prompt_cte;
```

**If `chunks_retrieved = 0`:** the search service returned nothing — broaden the keywords or check that `ASSISTANT_MSG_SEARCH_SVC` is populated.

______________________________________________________________________

## Output format

1. **Top issues / themes** — numbered list, each with what the issue is and a suggested mitigation
1. **Caveats** — RAG is over a sample of conversations; results reflect indexed data only
1. **Follow-up** — suggest `data:product-debrief ai assistant` if the user wants quantitative backing

Always append:

> *Source: Cortex Search over assistant conversations (`DBT_DEVELOPMENT_DB.DBT_SAI_DATASCIENCE.ASSISTANT_MSG_SEARCH_SVC`). Qualitative signal only.*

## Tracking

- **Query tag:** Before running queries, set the session query tag via the Snowflake MCP: `ALTER SESSION SET QUERY_TAG = '{"app":"jarvis","action":"assistant_voc"}'`
- **Pulse:** After surfacing insights, log the session via the Snowflake MCP `log-jarvis-session` tool with action `assistant_voc` and a one-line detail of the themes surfaced and timeframe.
