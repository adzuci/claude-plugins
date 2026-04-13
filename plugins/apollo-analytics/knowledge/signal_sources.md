# Signals Pipeline — Source Reference

> **Last verified:** 2026-03-20 (Leo, via live Snowflake queries on WEEKLY_TEAM_SIGNALS)

## TL;DR

Weekly team-level health signals aggregated from 5 source types into `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS`.
One row per (team, week, signal_source, signal_type). Metadata and next steps stored as JSON arrays in VARIANT columns.

**Critical gotcha:** `SIGNAL_METADATA` is already a VARIANT array — use `LATERAL FLATTEN(input => s.SIGNAL_METADATA)` directly. Do NOT wrap in `TRY_PARSE_JSON()` — will error with "Invalid argument types (ARRAY)".

---

## Consolidation Table

**Full path:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS`

| Column | Type | Description |
|---|---|---|
| `APOLLO_TEAM_ID` | TEXT | Team identifier. Joins to `DIM_MONGO_TEAMS`, `DIM_SALESFORCE_APOLLO_TEAMS`. |
| `SIGNAL_WEEK` | DATE | Monday of the signal week. |
| `SIGNAL_SOURCE` | TEXT | Which feeder produced the signal (see table below). |
| `SIGNAL_TYPE` | TEXT | The specific signal within that source. |
| `SIGNAL_METADATA` | VARIANT (ARRAY) | JSON array — one object per event. Schema varies by (signal_source, signal_type). Use `LATERAL FLATTEN`. |
| `NEXT_STEPS` | VARIANT (ARRAY) | Recommended actions array. Same access pattern. |
| `TEAM_WEEK_SIGNAL_TYPE_KEY` | TEXT | Dedup key on (apollo_team_id, signal_week, signal_source, signal_type). |

---

## Signal Sources & Types (verified volumes as of 2026-03-20, ~800K rows total)

### ML model signals

| Signal Source | Signal Type | Volume | Metadata Fields |
|---|---|---|---|
| `8w_churn_model` | `churn_score` | ~745K | `score_raw` (0–1), `score_percentile` (0–1), `priority` (P1–P3), `date` |

### Feature & credit anomaly signals (robust z-score based)

| Signal Source | Signal Type | Volume | Notes |
|---|---|---|---|
| `feature_usage` | `overall_wau_drop` | ~19K | Significant WAU decrease |
| `feature_usage` | `ai_emails_sent_drop` | ~11K | AI messaging volume drop |
| `credit_usage` | `inbound_website_visitor_credits_drop` | ~11K | Inbound credit consumption drop |
| `credit_usage` | `api_enrichment_credits_drop` | ~4.6K | API enrichment drop |
| `credit_usage` | `waterfall_enrichment_credits_drop` | ~3.3K | Waterfall enrichment drop |
| `credit_usage` | `power_up_credits_drop` | ~1.7K | Power-up credit drop |
| `credit_usage` | `crm_enrichment_credits_drop` | ~335 | CRM enrichment drop |
| `credit_usage` | `csv_enrichment_credits_drop` | ~64 | CSV enrichment drop |

### Conversation-based signals

| Signal Source | Signal Type | Volume | Metadata Fields |
|---|---|---|---|
| `hvo_calls` | `feature_reactions` | ~19.5K | `pain_point`, `aha_moment` |
| `hvo_calls` | `training_needs` | ~12.8K | Training gap from HVO call |
| `hvo_calls` | `upsell_potential` | ~7.4K | Expansion opportunity |
| `gtme_calls` | `product_feedback` | ~1.5K | `pain_point`, `product_gaps`, `discussion_summary` |
| `gtme_calls` | `churn_risk` | ~426 | `churn_risk_score`, `churn_risk_reason`, `pain_point`, `customer_sentiment` |
| `gtme_calls` | `customer_sentiment` | ~387 | Negative/mixed sentiment |
| `gtme_calls` | `upsell_potential` | ~175 | Expansion opportunity |

**Note:** `support_conversations` is NOT a signal source in this table (it appears in the dbt model plans but is not present in the live table). Do not query for it.

---

## Anomaly Detection Method

All anomaly signals (credit usage, feature usage) use the same statistical approach:
- **Benchmark window:** 12 weeks (t-16 to t-5) — median + MAD (Median Absolute Deviation)
- **Evaluation window:** 4 weeks (t-4 to t-1) — average
- **Robust z-score:** `(evaluation_avg - benchmark_median) / (1.4826 * benchmark_mad)`
- **Severity:** high (z <= -3), medium (z <= -2), low (z <= -1)
- **Eligibility:** minimum 8 benchmark weeks with activity, MAD > 0

---

## Priority Matrix (churn_score signals)

| Priority | Condition |
|---|---|
| P1 - Critical | High churn probability, immediate outreach |
| P2 - High Priority | Elevated risk, schedule within 2 weeks |
| P3 - Monitor | Watch list |

---

## Query Patterns

```sql
-- ML churn scores
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

-- HVO pain points
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

---

## Gotchas

- **LATERAL FLATTEN only** — `SIGNAL_METADATA` and `NEXT_STEPS` are already VARIANT arrays. `TRY_PARSE_JSON()` will error: "Invalid argument types (ARRAY)".
- **Correct schema is `ANALYTICS_DATASCIENCE`** — not `ANALYTICS`. The table `ANALYTICS_DB.ANALYTICS.WEEKLY_TEAM_SIGNALS` does not exist.
- **GTME coverage is sparse** — only 426 churn_risk + 387 sentiment signals total vs 745K ML signals. Many at-risk accounts have zero GTME coverage.
- **Double LATERAL JOIN causes internal error** — using two `JOIN LATERAL FLATTEN` in the same query hits Snowflake internal error 300002. Flatten one column per CTE or subquery.
- **Different from WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS** — that older table has a wide sparse column schema. Use this table instead.

---

## dbt Models (in `dbt_apollo`)

| Model | Location |
|---|---|
| `weekly_team_signals` | `models/marts/data_science/signals/weekly_team_signals.sql` |
| `weekly_team_signals_from_gtme_calls` | `models/marts/data_science/signals/gtme_calls/` |
| `weekly_team_signals_from_hvo_calls` | `models/marts/data_science/signals/hvo_calls/` |
| `weekly_team_signals_from_8week_churn_model` | `models/marts/data_science/signals/8week_churn_model/` |
| `weekly_team_signals_from_wau_anomaly` | `models/marts/data_science/signals/feature_usage/` |
| `weekly_team_signals_from_ai_emails_sent_anomaly` | `models/marts/data_science/signals/feature_usage/` |
| 6x credit anomaly models | `models/marts/data_science/signals/credit_usage/` |
