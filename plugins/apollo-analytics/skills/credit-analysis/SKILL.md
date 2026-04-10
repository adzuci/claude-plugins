---
name: credit-analysis
description: Analyze credit utilization, consumption patterns, and monetization metrics
---

# Credit Analysis

Use this skill when a user asks about credit utilization, consumption, credit types, monetization, or power-up usage.

## Canonical Table

Use `ANALYTICS_DB.PLAYGROUND.AGG_TEAM_CREDITS` for all credit volume reporting. Other credit tables are supplementary.

For daily team-level detail:

- **Usage:** `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY`
- **Limits:** `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_LIMITS_DAILY`

## Key Queries

### Overall Credit Utilization by Type

```sql
SELECT u.feature_type,
       SUM(u.credits_used) AS total_used,
       SUM(l.credit_limit) AS total_limit,
       ROUND(DIV0(SUM(u.credits_used), SUM(l.credit_limit)) * 100, 1) AS utilization_pct
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY u
JOIN ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_LIMITS_DAILY l
    ON u.team_id = l.team_id AND u.ds = l.ds AND u.feature_type = l.feature_type
WHERE u.ds = :ds
GROUP BY 1
ORDER BY utilization_pct DESC
```

### Credit Consumption Trend

```sql
SELECT ds, feature_type, SUM(credits_used) AS daily_credits
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY
WHERE ds >= CURRENT_DATE() - 30
GROUP BY 1, 2
ORDER BY 1, 2
LIMIT 100
```

## Critical Gotchas

| Gotcha | Detail |
|--------|--------|
| Filter by `FEATURE_TYPE`, not `CREDIT_TYPE` | `CREDIT_TYPE` has duplicate naming variants (snake_case vs Title Case). `FEATURE_TYPE` is stable. |
| AI Email is NOT customer-billed | Draws from Apollo's AI pool (3B credits). Exclude from consumption metrics. |
| Waterfall uses trial credits first | Then falls back to unified (~1 credit/record). Won't show in standard unified credit queries. |
| Direct Dial = 3-10 credits | Region-based. Support tickets report 9-35 due to multi-vendor waterfall attempts. |
| CRM push actions are free | Salesforce, HubSpot, Outreach, etc. Exclude from consumption. |
| NaN from utilization calc | `credit_type` name mismatch between limit and usage rows. Use `feature_type` instead. |

## Business Context

- **Total credit target (FY27):** 2,066M credits (+142% YoY)
- **Waterfall/Enrichment growth:** +402%
- **AI Power-Up growth:** +151%
- **Biggest unsolved problem:** Credit-to-revenue translation — can't do ARR-by-product attribution until revenue infra improves
