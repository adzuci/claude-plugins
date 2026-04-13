---
name: weekly-insights
description: Surface weekly strategic insights and recommendations for leadership
trigger-conditions:
  - "what should I focus on"
  - "top priorities this week"
  - "top recommendations"
  - "what should we do this week"
  - "P1 actions"
  - "strategic priorities"
  - "what are the priorities"
  - "weekly priorities"
  - "any strategic recs"
not-for:
  - "[area] performance" → use product-debrief
  - "[area] debrief" → use product-debrief
  - "how is [area] doing" → use product-debrief
  - "[area] summary" → use product-debrief
---

# Weekly Insights

Use this skill when an exec asks about **strategic direction** — "what should I focus on?", "top priorities?", "strategic recommendations?", or "what actions should we take this week?"

**Do NOT use this skill for product-area performance questions.** If the user asks "how is AI doing?", "sequences update?", or "[area] performance?", use `product-debrief` instead — it pulls live Snowflake data. This skill surfaces pre-curated P1–P3 recommendations from the weekly insights table.

## Query

```sql
SELECT HEADLINE, DETAIL, OWNER, PRIORITY, EFFORT, EXPECTED_IMPACT
FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS
WHERE WEEK_OF = DATE_TRUNC('WEEK', CURRENT_DATE())
ORDER BY PRIORITY, EFFORT
```

If no results for the current week, fall back to the previous week:

```sql
SELECT HEADLINE, DETAIL, OWNER, PRIORITY, EFFORT, EXPECTED_IMPACT
FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS
WHERE WEEK_OF = DATE_TRUNC('WEEK', DATEADD('WEEK', -1, CURRENT_DATE()))
ORDER BY PRIORITY, EFFORT
```

## Output Format

Present as a numbered list with priority tags:

> **Weekly Insights (week of YYYY-MM-DD)**
>
> 1. **[P1]** _Headline_ -- Detail (Owner: X, Effort: Y, Impact: Z)
> 2. **[P2]** _Headline_ -- Detail (Owner: X, Effort: Y, Impact: Z)
> ...

## Context

The insights table is refreshed weekly by the Analytics team (primarily Leo). Each row contains:
- **HEADLINE:** One-line summary of the insight
- **DETAIL:** Supporting explanation with data references
- **OWNER:** Who should act on it
- **PRIORITY:** P1 (critical) through P3 (nice-to-have)
- **EFFORT:** Low / Medium / High
- **EXPECTED_IMPACT:** What changes if this is acted on

If the user wants to drill into a specific insight, offer to run the underlying metric or data query that supports it.

## Tracking

- **Query tag:** Pass `--context weekly_insights` when running queries via `snowflake_query.py`
- **Pulse:** After surfacing insights, fire: `python3 scripts/snowflake_query.py --pulse weekly_insights --detail "<N> insights surfaced for <user>, week of <date>"`
