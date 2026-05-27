---
name: product-debrief
description: Generate product area performance summaries covering adoption, retention, and key metrics
---

# Product Debrief

Use this skill when a user asks about a product area's performance — AI Assistant, Sequences, Dialer, Inbound, Credits, or email activity.

## Product Area Routing

### AI Assistant

Use Sai's canonical data model — NOT `DIM_TEAMS_DAILY` for AI analytics.

**DAU (last 30 days):**
```sql
SELECT ACTIVITY_DATE, COUNT(DISTINCT APOLLO_USER_ID) AS dau
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_AI_ASSISTANT_DAILY
WHERE HAS_INTERACTIVE_THREADS_WITH_TOOL_CALLS = TRUE
  AND ACTIVITY_DATE >= CURRENT_DATE - 30
GROUP BY 1 ORDER BY 1
```

**Success rate by week:**
```sql
SELECT WEEK_START_DATE,
       ROUND(SUM(IS_SUCCESS) * 100.0 / COUNT(*), 1) AS success_rate_pct,
       COUNT(*) AS active_threads
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_ASSISTANT_THREADS
WHERE USER_INTERACTION_FLAG = TRUE AND HAS_TOOL_CALLS = TRUE
  AND THREAD_DATE >= CURRENT_DATE - 90
GROUP BY 1 ORDER BY 1 DESC LIMIT 13
```

**KR targets:** 10K paid core WAUs, 25% W4 retention (days 22-28).

### Sequences & Email

```sql
SELECT ds,
       ROUND(SUM(opened_count) * 100.0 / NULLIF(SUM(delivered_count), 0), 1) AS open_rate_pct,
       ROUND(SUM(replied_count) * 100.0 / NULLIF(SUM(delivered_count), 0), 1) AS reply_rate_pct
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EMAILER_MESSAGES_DAILY
WHERE message_type IN ('outreach_automatic_email', 'outreach_manual_email')
  AND ds >= CURRENT_DATE - 30 AND ds <= CURRENT_DATE()
GROUP BY 1 ORDER BY 1 DESC
```

**Gotcha:** `downloaded_email` = 84% of rows. Always filter to specific `message_type`.

### Feature Adoption (WAT)

```sql
SELECT ds, feature_name, COUNT(DISTINCT team_id) AS active_teams
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_FEATURE_USERS_DAILY
WHERE ds >= CURRENT_DATE - 30
GROUP BY 1, 2 ORDER BY 1 DESC, active_teams DESC
LIMIT 100
```

For DIM_TEAMS_DAILY feature columns (8.6B rows — always filter to single date):
```sql
SELECT DATE,
       COUNT(DISTINCT CASE WHEN SEQUENCE_USER_COUNTS_L7 > 0 THEN TEAM_ID END) AS sequence_wat,
       COUNT(DISTINCT CASE WHEN DIALER_USER_COUNTS_L7 > 0 THEN TEAM_ID END) AS dialer_wat,
       COUNT(DISTINCT CASE WHEN WORKFLOW_USER_COUNTS_L7 > 0 THEN TEAM_ID END) AS workflow_wat
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE IS_PAID_IND = TRUE AND DATE = CURRENT_DATE() - 1
GROUP BY 1
```

### Inbound (Website Visitors)

- **Current ARR:** $902K portfolio, 20x growth in 4 months
- **Problem:** 96% search visitors, only 3% publish a router, 1% book a meeting
- **Churn pattern:** 74% used it 30+ days before churning — value never clicked, not trial bounces

### Dialer

- **Churned team median tenure:** 23 days on add-on
- **ARR target:** $4.1M (H2 product)

## Strategic Insights to Surface

When relevant to the product area being discussed:

1. **Active days > credit utilization** for retention prediction (26+ days/month = 76% retention)
2. **Churn model works, intervention doesn't** — 89.5% correctly flagged, zero GTME coverage
3. **Inbound router is the activation wall** — 97% of churned teams never published one
4. **Credit-to-revenue translation is unsolved** — biggest measurement gap
