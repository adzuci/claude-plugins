# WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS

> Weekly team-level signals aggregated from HVO calls, GTME calls, ML churn models, and product/credit usage data.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS` |
| **Grain** | One row per team (APOLLO_TEAM_ID) x signal_week x signal_type x signal_source. For HVO-sourced signals, also per CONVERSATION_ID. |
| **Row count** | ~40k (as of 2026-03-18) |
| **Refresh cadence** | Weekly |
| **Trust level** | Use with caution — multi-source aggregation, signal definitions vary by source |
| **Owner** | Data Science team |
| **DAG** | <!-- TODO: identify DAG --> |

## Description

A unified signal table that aggregates customer health indicators from multiple sources into a single weekly cadence. Despite the name referencing "HVO calls," this table pulls from 5 distinct signal sources: HVO call analysis, GTME call analysis, 8-week ML churn model, product usage metrics, and credit consumption metrics. Each row represents one signal detected for one team in one week. The table is designed to feed downstream alerting, account health dashboards, and CS/sales action workflows.

## Upstream Sources

| Source | Relationship |
|---|---|
| HVO_CALLS_AI_PROCESSING | HVO call signals: upsell_potential, training_needs, feature_reactions |
| GTME call transcripts | GTME call signals: churn_risk, upsell_potential, customer_sentiment, product_feedback |
| FCT_ML_PREDICTIONS_PAID_CHURN_12W | 8-week churn model: churn_score |
| Product usage metrics | WAU anomaly detection: overall_wau_drop |
| Feature usage metrics | AI messaging anomaly: ai_emails_sent_drop |
| Credit usage metrics | Credit consumption anomalies across 6 credit types |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| APOLLO_TEAM_ID | TEXT | Team ID (ZP Team ID) | Join key to DIM_MONGO_TEAMS, DIM_SALESFORCE_APOLLO_TEAMS |
| SIGNAL_WEEK | DATE | Monday of the signal week | ISO week, always a Monday |
| SIGNAL_TYPE | TEXT | Category of signal detected | See signal type taxonomy below |
| SIGNAL_SOURCE | TEXT | Origin system | `hvo_calls`, `gtme_calls`, `8w_churn_model`, `feature_usage`, `credit_usage` |
| ACTION_TEAM | TEXT | Team responsible for acting | |
| RECOMMENDED_NEXT_ACTION | TEXT | Suggested action | |
| ACTION_DATE_FINAL | DATE | When to act | |
| CONVERSATION_ID | TEXT | HVO/GTME conversation ID | NULL for non-call signal sources |
| DATE | DATE | Call date | Only populated for call-sourced signals |

### Signal type taxonomy

**From HVO calls (`signal_source = 'hvo_calls'`):**
- `upsell_potential` — expansion opportunity identified
- `training_needs` — additional training required, unresolved questions, or low sufficiency score (<=3)
- `feature_reactions` — customer reactions to inbound, dialer, AI; aha moments; pain points

**From GTME calls (`signal_source = 'gtme_calls'`):**
- `churn_risk` — elevated churn risk (score >= 3)
- `upsell_potential` — expansion opportunity
- `customer_sentiment` — mixed or negative sentiment
- `product_feedback` — feature requests, product gaps, aha moments

**From ML model (`signal_source = '8w_churn_model'`):**
- `churn_score` — ML-predicted churn probability

**From product usage (`signal_source = 'feature_usage'`):**
- `overall_wau_drop` — significant WAU decrease
- `ai_emails_sent_drop` — AI messaging volume decrease

**From credit usage (`signal_source = 'credit_usage'`):**
- `waterfall_enrichment_credits_drop`, `api_enrichment_credits_drop`, `crm_enrichment_credits_drop`, `csv_enrichment_credits_drop`, `power_up_credits_drop`, `inbound_website_visitor_credits_drop`

### Conditional columns (populated based on signal_type)

| Column | Present when | Description |
|---|---|---|
| UPSELL_REASON | signal_type = upsell_potential | Why upsell was flagged |
| NEED_ANOTHER_TRAINING_SESSION | signal_type = training_needs | Boolean |
| CUSTOMER_TECHNICAL_SUFFICIENCY_SCORE | signal_type = training_needs | 1-5, lower = needs more help |
| CUSTOMER_TECHNICAL_SUFFICIENCY_REASON | signal_type = training_needs | Explanation |
| HAS_UNRESOLVED_QUESTIONS | signal_type = training_needs | Boolean |
| FOLLOW_UP | signal_type = training_needs | Follow-up notes |
| IS_INBOUND_DISCUSSED | signal_type = feature_reactions | Boolean |
| IS_DIALER_DISCUSSED | signal_type = feature_reactions | Boolean |
| IS_AI_REFERRED | signal_type = feature_reactions | Boolean |
| INBOUND_REACTION | signal_type = feature_reactions | Customer comments on Inbound |
| DIALER_REACTION | signal_type = feature_reactions | Customer comments on Dialer |
| COMMENTS_ON_AI | signal_type = feature_reactions | Customer comments on AI |
| AHA_MOMENT | signal_type = feature_reactions | Value discovery moment |
| PAIN_POINT | signal_type = feature_reactions | Customer pain point |

## How It's Used

### Common query patterns

- **Weekly account health review** — filter by SIGNAL_WEEK, join to DIM_SALESFORCE_APOLLO_TEAMS for account context, group by SIGNAL_TYPE
- **CS action lists** — filter to recent week + specific signal types (churn_risk, training_needs), order by ACTION_DATE_FINAL
- **Feature adoption tracking** — filter signal_type = feature_reactions, aggregate IS_INBOUND_DISCUSSED / IS_DIALER_DISCUSSED / IS_AI_REFERRED

### Key consumers

- CS/Sales teams (action routing)
- Leo Liu / Product Analytics (Project BAT dashboards)
- Data Science (model monitoring — churn score distribution over time)

## Known Issues & Gotchas

- **Table name is misleading** — contains signals from 5 sources, not just HVO calls. Filter on SIGNAL_SOURCE if you only want call data.
- **Sparse columns** — most columns are NULL for any given row because they're conditional on signal_type. Don't count NULLs as data quality issues.
- **Created very recently** (2026-03-18) — still being validated. Row count (40k) seems high for a weekly table; may include historical backfill.

## Business Terms

| Term | Definition |
|---|---|
| GTME | Go-To-Market Engineering — another call analysis pipeline similar to HVO but for different call types |
| Signal | A detected customer health indicator from any source, normalized to team-week grain |
| WAU | Weekly Active Users — product engagement metric |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-18 | Table created in ANALYTICS_DATASCIENCE | Data Science team |
| 2026-03-18 | Created context file | Brighid (via Claude) |
