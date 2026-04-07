---
name: weekly-insights
description: Surface weekly strategic insights and recommendations for leadership
---

# Weekly Insights

Use this skill when an exec asks "what should I focus on?", "what are the top recommendations?", "any insights?", "what should we do this week?", or similar strategic-direction questions.

## Query

```sql
SELECT HEADLINE, DETAIL, OWNER, PRIORITY, EFFORT, EXPECTED_IMPACT
FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS
WHERE WEEK_OF = DATE_TRUNC('WEEK', CURRENT_DATE())
ORDER BY PRIORITY, EFFORT
```

If no results for the current week, fall back to the most recent available week:

```sql
SELECT HEADLINE, DETAIL, OWNER, PRIORITY, EFFORT, EXPECTED_IMPACT
FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS
WHERE WEEK_OF = (SELECT MAX(WEEK_OF) FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS)
ORDER BY PRIORITY, EFFORT
```

**Important:** If the most recent `WEEK_OF` is more than 14 days old, warn the user that insights are stale and may not reflect current priorities.

## Output Format

Present as a numbered list with priority tags:

> **Weekly Insights (week of YYYY-MM-DD)**
>
> 1. **[P1]** _Headline_ -- Detail (Owner: X, Effort: Y, Impact: Z)
> 1. **[P2]** _Headline_ -- Detail (Owner: X, Effort: Y, Impact: Z)
>    ...

## Context

The insights table is refreshed weekly by the Analytics team (primarily Leo). Each row contains:

- **HEADLINE:** One-line summary of the insight
- **DETAIL:** Supporting explanation with data references
- **OWNER:** Who should act on it
- **PRIORITY:** P1 (critical) through P3 (nice-to-have)
- **EFFORT:** Low / Medium / High
- **EXPECTED_IMPACT:** What changes if this is acted on

If the user wants to drill into a specific insight, offer to run the underlying metric or data query that supports it.
