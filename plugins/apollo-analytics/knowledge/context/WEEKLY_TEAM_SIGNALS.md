# WEEKLY_TEAM_SIGNALS

> Weekly team-level upsell and churn signals aggregated from ML model, GTME calls, HVO calls, feature usage, and credit usage.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS` |
| **Grain** | One row per `(APOLLO_TEAM_ID, SIGNAL_WEEK, SIGNAL_SOURCE, SIGNAL_TYPE)` |
| **Row count** | ~800K (2026-03-20) |
| **Refresh cadence** | Weekly |
| **Trust level** | Medium — multi-source aggregation; validate against source tables for high-stakes decisions |
| **Owner** | Data Science |

## Description

Unified weekly signal table for account health, churn risk, and upsell monitoring. Aggregates signals from 5 distinct sources into a consistent schema. Each row = one signal fired for one team in one week. Metadata and next steps are stored as JSON VARIANTs — use `LATERAL FLATTEN` (not `TRY_PARSE_JSON`) to access them.

**Note:** Despite the name similarity, this is a different (cleaner) table than `WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS`, which has a wider but sparser column schema. Prefer this table.

## Key Columns

| Column | Type | Description |
|---|---|---|
| APOLLO_TEAM_ID | TEXT | Team identifier — joins directly to DIM_MONGO_TEAMS, DIM_SALESFORCE_APOLLO_TEAMS |
| SIGNAL_WEEK | DATE | Monday of the signal week |
| SIGNAL_SOURCE | TEXT | Origin system — see taxonomy below |
| SIGNAL_TYPE | TEXT | Signal category — see taxonomy below |
| SIGNAL_METADATA | VARIANT (ARRAY) | JSON array with signal details — structure varies by signal type |
| NEXT_STEPS | VARIANT (ARRAY) | JSON array with recommended actions |
| TEAM_WEEK_SIGNAL_TYPE_KEY | TEXT | Dedup key |

## Signal Taxonomy

| signal_source | signal_type | Volume | Description |
|---|---|---|---|
| `8w_churn_model` | `churn_score` | 745K | ML churn probability (8-week horizon). Metadata: `score_raw` (0–1), `score_percentile` (0–1), `priority` (P1–P3), `date` |
| `feature_usage` | `overall_wau_drop` | 19K | Significant WAU decrease detected |
| `feature_usage` | `ai_emails_sent_drop` | 11K | AI messaging volume drop |
| `credit_usage` | `inbound_website_visitor_credits_drop` | 11K | Inbound credit consumption drop |
| `credit_usage` | `api_enrichment_credits_drop` | 4.6K | API enrichment drop |
| `credit_usage` | `waterfall_enrichment_credits_drop` | 3.3K | Waterfall enrichment drop |
| `credit_usage` | `power_up_credits_drop` | 1.7K | Power-up credit drop |
| `credit_usage` | `crm_enrichment_credits_drop` | 335 | CRM enrichment drop |
| `credit_usage` | `csv_enrichment_credits_drop` | 64 | CSV enrichment drop |
| `hvo_calls` | `feature_reactions` | 19.5K | Customer reactions to inbound/dialer/AI from HVO calls. Metadata: `pain_point`, `aha_moment` |
| `hvo_calls` | `training_needs` | 12.8K | Training gap identified in HVO call |
| `hvo_calls` | `upsell_potential` | 7.4K | Expansion opportunity from HVO call |
| `gtme_calls` | `product_feedback` | 1.5K | Feature requests, gaps from GTME. Metadata: `pain_point`, `product_gaps`, `discussion_summary` |
| `gtme_calls` | `churn_risk` | 426 | Elevated churn risk from GTME call. Metadata: `churn_risk_score`, `churn_risk_reason`, `pain_point`, `customer_sentiment` |
| `gtme_calls` | `customer_sentiment` | 387 | Negative/mixed sentiment from GTME call |
| `gtme_calls` | `upsell_potential` | 175 | Expansion opportunity from GTME call |

## How to Query SIGNAL_METADATA

`SIGNAL_METADATA` is already a VARIANT array — use `LATERAL FLATTEN` directly (not `TRY_PARSE_JSON`):

```sql
-- ML churn scores with priority breakdown
SELECT
    s.APOLLO_TEAM_ID
    , s.SIGNAL_WEEK
    , f.value:score_raw::FLOAT          AS score_raw
    , f.value:score_percentile::FLOAT   AS score_percentile
    , f.value:priority::TEXT            AS priority
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS s
JOIN LATERAL FLATTEN(input => s.SIGNAL_METADATA) f
WHERE s.SIGNAL_SOURCE = '8w_churn_model'
    AND s.SIGNAL_WEEK >= CURRENT_DATE - 30;

-- GTME churn risk with pain points
SELECT
    s.APOLLO_TEAM_ID
    , s.SIGNAL_WEEK
    , f.value:churn_risk_score::TEXT    AS churn_risk_score
    , f.value:churn_risk_reason::TEXT   AS churn_risk_reason
    , f.value:pain_point::TEXT          AS pain_point
    , f.value:customer_sentiment::TEXT  AS sentiment
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS s
JOIN LATERAL FLATTEN(input => s.SIGNAL_METADATA) f
WHERE s.SIGNAL_SOURCE = 'gtme_calls'
    AND s.SIGNAL_TYPE = 'churn_risk'
    AND s.SIGNAL_WEEK >= CURRENT_DATE - 60;

-- HVO pain points for a set of team IDs
SELECT
    s.APOLLO_TEAM_ID
    , s.SIGNAL_WEEK
    , f.value:pain_point::TEXT      AS pain_point
    , f.value:aha_moment::TEXT      AS aha_moment
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS s
JOIN LATERAL FLATTEN(input => s.SIGNAL_METADATA) f
WHERE s.SIGNAL_SOURCE = 'hvo_calls'
    AND s.SIGNAL_TYPE = 'feature_reactions'
    AND f.value:pain_point::TEXT IS NOT NULL;
```

## Known Issues & Gotchas

- **LATERAL FLATTEN only** — `SIGNAL_METADATA` and `NEXT_STEPS` are already VARIANT arrays. Using `TRY_PARSE_JSON()` on them will error with "Invalid argument types (ARRAY)".
- **Different from WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS** — that table has wider sparse columns; this one uses JSON metadata. Prefer this table for signal queries.
- **GTME coverage is sparse** — only 426 churn_risk + 387 sentiment signals total vs 745K ML signals. GTME signals only exist for accounts with GTME call coverage.
- **Historical backfill**: Table created recently (2026-03-20 discovered). Row count of 800K suggests some backfill, but verify signal_week range before doing historical trend analysis.

## Related Tables

| Table | Relationship |
|---|---|
| `WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS` | Older version with wide sparse columns — use this table instead |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING` | Upstream for `hvo_calls` signals |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS` | Upstream for `gtme_calls` signals |
| `FCT_ML_PREDICTIONS_PAID_CHURN_12W` | Upstream for `8w_churn_model` signals |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created context file — schema verified, FLATTEN pattern documented, full signal taxonomy mapped | Leo (via Claude) |
