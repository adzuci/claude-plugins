---
name: support-metrics
description: "PA Live Support metrics snapshot — Chat SLA, AI Resolution Rate, Escalation Rate, Channel Mix (chat + email) from Snowflake, with N months of history vs AOP targets and a trend narrative. Use when someone asks for support metrics, chat SLA, AI resolution rate, escalation rate, channel mix, support metrics trend, or PA Live Support performance vs AOP targets. Accepts an optional [--months N] argument (default 6)."
---

# PA Live Support Metrics Snapshot

Runs 4 validated Snowflake queries for PA Live Support and produces a monthly trend table + narrative for each metric.

**AOP targets (FY27):**

- Chat SLA: 90% within 2 min
- AI Resolution Rate: 80%
- Escalation Rate: \<10%
- Channel Mix: no AOP target (directional only)

**Not included (requires Intercom API or is unreliable):**

- Handle Time Chat/Video — Snowflake runs 5-15 min too high; requires the Intercom API
- Video SLA — `IS_A_CALL_CONVERSATION` undercounts video by 5-15%
- Email SLA — formula not confirmed, up to 10% gap
- Chat FCR — `IS_CONVERSATION_FIRST_CONTACT_RESOLUTION` is broken in FY26

______________________________________________________________________

## Step 1 — Parse arguments

Parse `$ARGUMENTS` for `--months N`. Default to `6` if not provided.

Compute:

```
lookback_months = N (default 6)
```

The SQL queries use `DATEADD('month', -{{lookback_months}}, DATE_TRUNC('month', CURRENT_DATE()))` as the dynamic start date, so no date math is needed outside Snowflake.

**Before running:** replace every `{{lookback_months}}` placeholder in the queries below with the integer value (e.g. `6`). It is a literal placeholder, not a Jinja/template variable the Snowflake MCP will expand.

______________________________________________________________________

## Step 1.5a — Registry lookup (advisory)

Check `LU_SAVED_METRICS` for canonical support metric definitions. Run via the Snowflake MCP:

```sql
SELECT metric_name, variant, metric_sql
FROM ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS
WHERE status = 'approved'
  AND (LOWER(metric_name) LIKE '%support%' OR LOWER(metric_name) LIKE '%chat%'
       OR LOWER(metric_name) LIKE '%sla%' OR LOWER(metric_name) LIKE '%escalation%'
       OR LOWER(metric_name) LIKE '%resolution%')
```

If canonical definitions exist, prefer their SQL over inline queries. If AOP targets are stored in a metric's description or a separate LU table, use those rather than the hardcoded FY figures below.

______________________________________________________________________

## Step 1.5b — Intelligence Kernel Check (before running queries)

Before running the metric queries, check for a recent intelligence snapshot. Run via the Snowflake MCP:

```sql
SELECT intelligence, assessed_at
FROM ANALYTICS_DB.PLAYGROUND.INTELLIGENCE_SNAPSHOTS
WHERE kernel_id = 'support_intelligence_weekly'
ORDER BY assessed_at DESC
LIMIT 1
```

If a snapshot exists from the last 3 days, use it as pre-computed context alongside the queries below. Cite as "From intelligence snapshot (support_intelligence_weekly, assessed <date>)."

______________________________________________________________________

## Step 2 — Run all 4 queries in parallel

Run each via the Snowflake MCP. All 4 are independent and can be fired simultaneously.

### Query 1: Chat SLA

```sql
SELECT
    TO_CHAR(DATE_TRUNC('month', c.CONVERSATION_CREATED_AT), 'YYYY-MM') AS month,
    COUNT(DISTINCT c.CONVERSATION_ID)                                    AS total,
    COUNT(DISTINCT CASE
        WHEN r.CONVERSATION_TEAM_RESPONSE_TIME_MINUTES <= 2
        THEN c.CONVERSATION_ID END)                                      AS sla_hit,
    ROUND(100.0 * COUNT(DISTINCT CASE
        WHEN r.CONVERSATION_TEAM_RESPONSE_TIME_MINUTES <= 2
        THEN c.CONVERSATION_ID END)
        / NULLIF(COUNT(DISTINCT c.CONVERSATION_ID), 0), 1)              AS sla_pct
FROM ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS c
JOIN ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATION_TEAM_RESPONSE_TIME r
    ON c.CONVERSATION_ID = r.CONVERSATION_ID
WHERE c.CONVERSATION_CREATED_AT >= DATEADD('month', -{{lookback_months}}, DATE_TRUNC('month', CURRENT_DATE()))
  AND c.CONVERSATION_FIRST_HANDLED_TEAM_NAME LIKE 'PA Live Support%'
  AND c.IS_AI_ONLY_PARTICIPATED = FALSE
  AND r.NUMBERED_TEAM_CONVERSATION_RESPONSES = 1
  AND r.IS_TEAM_ASSIGNMENT_DURING_NON_WORKING_HOURS = FALSE
GROUP BY 1
ORDER BY 1
```

### Query 2: AI Resolution Rate

```sql
SELECT
    TO_CHAR(DATE_TRUNC('month', c.CONVERSATION_CREATED_AT), 'YYYY-MM') AS month,
    COUNT(DISTINCT c.CONVERSATION_ID)                                    AS ai_touched,
    COUNT(DISTINCT CASE
        WHEN c.AI_AGENT_RESOLUTION_STATE IN ('assumed_resolution', 'confirmed_resolution')
        THEN c.CONVERSATION_ID END)                                      AS ai_resolved,
    ROUND(100.0 * COUNT(DISTINCT CASE
        WHEN c.AI_AGENT_RESOLUTION_STATE IN ('assumed_resolution', 'confirmed_resolution')
        THEN c.CONVERSATION_ID END)
        / NULLIF(COUNT(DISTINCT c.CONVERSATION_ID), 0), 1)              AS ai_resolution_pct
FROM ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS c
WHERE c.CONVERSATION_CREATED_AT >= DATEADD('month', -{{lookback_months}}, DATE_TRUNC('month', CURRENT_DATE()))
  AND c.IS_AI_AGENT_PARTICIPATED = TRUE
GROUP BY 1
ORDER BY 1
```

### Query 3: Escalation Rate

> **Scope note:** Covers all AI-touched conversations company-wide (not PA Live Support only). This matches the validated Intercom formula — do not add a PA Live Support team filter.

```sql
SELECT
    TO_CHAR(DATE_TRUNC('month', c.CONVERSATION_CREATED_AT), 'YYYY-MM') AS month,
    COUNT(DISTINCT c.CONVERSATION_ID)                                    AS ai_touched,
    COUNT(DISTINCT CASE
        WHEN tt.IS_CONVERSATION_TURNED_TICKET = TRUE
        THEN c.CONVERSATION_ID END)                                      AS escalated,
    ROUND(100.0 * COUNT(DISTINCT CASE
        WHEN tt.IS_CONVERSATION_TURNED_TICKET = TRUE
        THEN c.CONVERSATION_ID END)
        / NULLIF(COUNT(DISTINCT c.CONVERSATION_ID), 0), 1)              AS escalation_pct
FROM ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS c
LEFT JOIN ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS_TURNED_TICKETS tt
    ON c.CONVERSATION_ID = tt.CONVERSATION_ID
WHERE c.CONVERSATION_CREATED_AT >= DATEADD('month', -{{lookback_months}}, DATE_TRUNC('month', CURRENT_DATE()))
  AND c.IS_AI_AGENT_PARTICIPATED = TRUE
GROUP BY 1
ORDER BY 1
```

### Query 4: Channel Mix (Chat + Email)

```sql
SELECT
    conv.month,
    conv.video_n,
    conv.chat_n,
    tick.email_n,
    conv.video_n + conv.chat_n + COALESCE(tick.email_n, 0)                                              AS total,
    ROUND(100.0 * conv.video_n / NULLIF(conv.video_n + conv.chat_n + COALESCE(tick.email_n, 0), 0), 1) AS video_pct,
    ROUND(100.0 * conv.chat_n  / NULLIF(conv.video_n + conv.chat_n + COALESCE(tick.email_n, 0), 0), 1) AS chat_pct,
    ROUND(100.0 * COALESCE(tick.email_n, 0) / NULLIF(conv.video_n + conv.chat_n + COALESCE(tick.email_n, 0), 0), 1) AS email_pct
FROM (
    SELECT
        TO_CHAR(DATE_TRUNC('month', CONVERSATION_CREATED_AT), 'YYYY-MM')                              AS month,
        COUNT(DISTINCT CASE WHEN IS_A_CALL_CONVERSATION = TRUE  THEN CONVERSATION_ID END)             AS video_n,
        COUNT(DISTINCT CASE WHEN IS_A_CALL_CONVERSATION = FALSE THEN CONVERSATION_ID END)             AS chat_n
    FROM ANALYTICS_DB.ANALYTICS.INT_INTERCOM_CONVERSATIONS
    WHERE CONVERSATION_CREATED_AT >= DATEADD('month', -{{lookback_months}}, DATE_TRUNC('month', CURRENT_DATE()))
      AND CONVERSATION_FIRST_HANDLED_TEAM_NAME LIKE 'PA Live Support%'
    GROUP BY 1
) conv
LEFT JOIN (
    SELECT
        TO_CHAR(DATE_TRUNC('month', TICKET_CONVERSION_AT), 'YYYY-MM')                                 AS month,
        COUNT(DISTINCT TICKET_ID)                                                                       AS email_n
    FROM ANALYTICS_DB.ANALYTICS.INT_INTERCOM_TICKETS
    WHERE TICKET_CONVERSION_AT >= DATEADD('month', -{{lookback_months}}, DATE_TRUNC('month', CURRENT_DATE()))
      AND IS_TICKET_SUPPORT_TEAM_HANDLED = TRUE
      AND TICKET_CATEGORY = 'Customer'
    GROUP BY 1
) tick ON conv.month = tick.month
-- LEFT JOIN so months with zero email tickets still appear (email_n coalesced to 0 above)
ORDER BY 1
```

______________________________________________________________________

## Step 3 — Format the report

Present each metric as a section with:

1. A monthly table showing raw counts and the rate, plus a MoM delta column
1. A one-line status vs AOP target for the most recent completed month
1. A 1-2 sentence trend call (improving / declining / flat, and anything notable)

**Template for each metric section:**

```
### [Metric Name]  [status emoji vs AOP target]
AOP target: [target] | Latest ([YYYY-MM]): [value]  ([+/-]Xpp MoM)

| Month  | [numerator label] | [denominator label] | Rate   | MoM Δ |
|--------|-------------------|---------------------|--------|-------|
| 2026-03 | ...              | ...                 | XX.X%  | +X.Xpp |
...

[Trend narrative — 1-2 sentences. Call out: trend direction, worst/best month, any anomalies to watch.]
```

**Status emoji rules:**

- Chat SLA: ✅ if ≥90%, ⚠️ if 80-89%, 🔴 if \<80%
- AI Resolution Rate: ✅ if ≥80%, ⚠️ if 70-79%, 🔴 if \<70%
- Escalation Rate: ✅ if \<10%, ⚠️ if 10-15%, 🔴 if >15%
- Channel Mix: no target — omit emoji, note if video share jumped significantly (use ⚠️ if video >10% since it affects AHT and capacity planning)

**Data caveats to append at the bottom of the report:**

```
---
**Data notes (~1% error unless noted):**
- Chat SLA: ~1% error vs Intercom dashboard. Excludes off-hours assignments.
- AI Resolution Rate: ~1% error. Do NOT filter by IS_CONVERSATION_SUPPORT_TEAM_HANDLED.
- Escalation Rate: ~1% error Jun 2025+; ~6% gap in data before Jun 2025 — treat pre-Jun 2025 months as approximate. **Scope: all AI-touched conversations company-wide, not PA Live Support only** — this matches the validated Intercom formula but is broader than the other 3 metrics.
- Channel Mix: video undercounted by ~5-15% (IS_A_CALL_CONVERSATION field incomplete); those conversations are miscounted as chat, inflating chat % and deflating video %. Email ~0.5-5pp error.
- Handle Time (chat/video), Email SLA, and FCR are not included — require Intercom API or have no validated formula.
```

______________________________________________________________________

## Step 4 — Surface any alerts

After the per-metric sections, add a short **Alerts** block if any of the following are true for the most recent completed month:

- Chat SLA < 80%
- AI Resolution Rate < 70%
- Escalation Rate > 15%
- Video share > 10% (capacity signal — see voice ramp context in domain files)
- Any metric moved more than 5pp MoM in either direction

Format:

```
### ⚠️ Alerts
- [metric]: [value] — [one-line explanation of why this is notable]
```

If no alerts, omit the section entirely.

______________________________________________________________________

## Tracking

- **Query tag:** Before running queries, set the session query tag via the Snowflake MCP: `ALTER SESSION SET QUERY_TAG = '{"app":"jarvis","action":"support_metrics"}'`
- **Pulse:** After producing the snapshot, log the session via the Snowflake MCP `log-jarvis-session` tool with action `support_metrics` and a one-line detail (months covered + any alerts).
