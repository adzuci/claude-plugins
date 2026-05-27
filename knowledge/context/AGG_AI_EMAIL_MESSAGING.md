# AGG_AI_EMAIL_MESSAGING

> Daily aggregate of AI email activity sliced by all key dimensions. Pre-computed counts that power team/user engagement and retention queries without scanning the message-level fact.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.AGG_AI_EMAIL_MESSAGING` |
| **Grain** | `(apollo_team_id, apollo_user_id, email_sent_date, emailer_campaign_id, emailer_step_id, emailer_template_id, email_type, has_ai_content)` |
| **Row count** | — (incremental from 2026-03-02) |
| **Refresh cadence** | Daily incremental; 28-day lookback on each run |
| **Trust level** | Authoritative (DS-owned, part of AI platform model hierarchy) |
| **Owner** | Data Science (Sai Sarvepalli) — `#proj-ai-platform` |
| **DAG** | dbt model: `models/marts/data_science/ai_platform/agg_ai_email_messaging.sql` |

## Description

Built on top of `fct_ai_email_messaging`. Groups the message-level fact to a daily dimension slice and pre-computes engagement counts and rates. Designed so team/user-level engagement, retention, and AI impact analysis require no further joins or heavy scans.

`cc_version`, `campaign_cc_version`, `sequence_name`, `step_position`, and `step_type` are functionally dependent on the grain keys — they're included in the SELECT but do not affect uniqueness.

**Data flow:**
```
fct_ai_email_messaging (message grain)
    ↓ GROUP BY dimension slice
agg_ai_email_messaging (THIS TABLE — daily dimension slice aggregate)
    ↓
Looker / Hex dashboards — weekly/daily retention, engagement rates, AI vs non-AI comparison
```

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| AGG_AI_EMAIL_MESSAGING_KEY | TEXT | Surrogate key (hash of grain columns) | Unique per row |
| APOLLO_TEAM_ID | TEXT | Sender's Apollo team ID | NULL rows excluded from this table |
| APOLLO_USER_ID | TEXT | Sender's Apollo user ID | NULL rows excluded from this table |
| EMAIL_SENT_DATE | DATE | Calendar date of send | Cluster key; primary temporal grain |
| EMAILER_CAMPAIGN_ID | TEXT | FK to `fct_mongo_emailer_campaigns` | NULL when no associated campaign |
| EMAILER_STEP_ID | TEXT | FK to `dim_mongo_emailer_steps` | NULL when no associated step |
| EMAILER_TEMPLATE_ID | TEXT | FK to `dim_mongo_emailer_templates` | NULL when no touch record for step |
| EMAIL_TYPE | TEXT | `outreach_automatic_email`, `outreach_manual_email`, `extension_email` | Part of grain |
| CC_VERSION | TEXT | `CC v3`, `Legacy CC`, `No CC` — step-level (most granular) | Functionally dependent on `emailer_step_id` |
| CAMPAIGN_CC_VERSION | TEXT | `CC v3`, `Legacy CC`, `No CC` — sequence-level | NULL when campaign unresolvable |
| SEQUENCE_NAME | TEXT | Human-readable sequence name | Functionally dependent on `emailer_campaign_id` |
| STEP_POSITION | TEXT | Step position within the sequence | Functionally dependent on `emailer_step_id` |
| STEP_TYPE | TEXT | Step type: `email`, `call`, `linkedin`, etc. | Functionally dependent on `emailer_step_id` |
| HAS_AI_CONTENT | BOOLEAN | True if emails in this slice used AI variables | **Part of grain** — compare `true` vs `false` for AI lift |
| IS_SENT_BEFORE_LAST_WEEK | BOOLEAN | True when `email_sent_date` is ≥1 full calendar week in the past | Coalesced to `false` (never NULL). **Gate for rate math** |
| EMAIL_COUNT | INTEGER | Distinct email count for this dimension slice | |
| EMAIL_COUNT_DELIVERED | INTEGER | Count of delivered emails | Raw — not pre-filtered by maturity |
| EMAIL_COUNT_OPENED | INTEGER | Count of opened emails (includes bot opens) | For human-only opens, join back to `fct_ai_email_messaging` |
| EMAIL_COUNT_REPLIED | INTEGER | Count of replied emails | Numerator for `reply_rate` |
| EMAIL_COUNT_DEMOED | INTEGER | Count of emails resulting in a demo booking | Numerator for `demo_rate` |
| WILLING_TO_MEET_COUNT | INTEGER | Count of `willing_to_meet` reply classifications | Highest-quality reply signal |
| DELIVERY_RATE | FLOAT | `email_count_delivered / email_count` (DIV0) | Only meaningful when `IS_SENT_BEFORE_LAST_WEEK = true` |
| REPLY_RATE | FLOAT | `email_count_replied / email_count_delivered` (DIV0) | Only meaningful when `IS_SENT_BEFORE_LAST_WEEK = true` |
| DEMO_RATE | FLOAT | `email_count_demoed / email_count_delivered` (DIV0) | Only meaningful when `IS_SENT_BEFORE_LAST_WEEK = true` |
| LOADED_AT | TIMESTAMP_NTZ | Row write timestamp (UTC). Audit column. | |

## How It's Used

### Common query patterns

**AI vs non-AI engagement comparison:**
```sql
SELECT
    has_ai_content
    , SUM(email_count_replied) / NULLIF(SUM(email_count_delivered), 0) AS reply_rate
FROM agg_ai_email_messaging
WHERE is_sent_before_last_week
GROUP BY 1
```

**Weekly email volume by CC version:**
```sql
SELECT
    DATE_TRUNC('week', email_sent_date) AS week
    , cc_version
    , SUM(email_count) AS total_emails
FROM agg_ai_email_messaging
WHERE is_sent_before_last_week
GROUP BY 1, 2
ORDER BY 1
```

**W1/W4 user retention (self-join pattern):**
```sql
SELECT
    DATE_TRUNC('week', w0.email_sent_date) AS cohort_week
    , COUNT(DISTINCT w0.apollo_user_id)    AS users_week_0
    , COUNT(DISTINCT w1.apollo_user_id)    AS retained_week_1
    , COUNT(DISTINCT w4.apollo_user_id)    AS retained_week_4
FROM agg_ai_email_messaging AS w0
LEFT JOIN agg_ai_email_messaging AS w1
    ON  w1.apollo_user_id = w0.apollo_user_id
    AND w1.email_sent_date BETWEEN DATEADD('day', 7, w0.email_sent_date)
                               AND DATEADD('day', 13, w0.email_sent_date)
LEFT JOIN agg_ai_email_messaging AS w4
    ON  w4.apollo_user_id = w0.apollo_user_id
    AND w4.email_sent_date BETWEEN DATEADD('day', 28, w0.email_sent_date)
                               AND DATEADD('day', 34, w0.email_sent_date)
WHERE w0.is_sent_before_last_week
GROUP BY 1
```

### Key consumers
- Looker / Hex dashboards for AI email engagement and retention reporting
- Ad-hoc team/user retention analyses

## Upstream Sources

| Source | Relationship |
|---|---|
| `FCT_AI_EMAIL_MESSAGING` | Only upstream — all columns sourced from here |

## Known Issues & Gotchas

- **Maturity gate is mandatory for rates.** `DELIVERY_RATE`, `REPLY_RATE`, and `DEMO_RATE` are pre-computed but only valid when `IS_SENT_BEFORE_LAST_WEEK = true`. The column is never NULL (coalesced to false), so a bare `WHERE IS_SENT_BEFORE_LAST_WEEK` is safe.
- **Opened counts include bot opens.** `EMAIL_COUNT_OPENED` includes bot-attributed opens. For human-only open analysis, join back to `fct_ai_email_messaging` and filter `is_bot_opened = false`.
- **NULL team/user rows are excluded.** `fct_ai_email_messaging` rows where `team_id` or `user_id` is NULL are dropped before aggregation.
- **28-day incremental lookback.** Reply/demo signals arrive late — the 28-day window ensures re-aggregation on each run as signals mature.
- **Functionally dependent columns don't affect uniqueness.** `cc_version`, `campaign_cc_version`, `sequence_name`, `step_position`, `step_type` are included for convenience but are derived from grain keys. Do not GROUP BY them when they conflict with the main grain.
- **Start date is 2026-03-02.** Inherits the start date of `fct_ai_email_messaging`.

## Business Terms

| Term | Definition |
|---|---|
| HAS_AI_CONTENT | True if any AI-generated variable was used in emails in this slice |
| IS_SENT_BEFORE_LAST_WEEK | Maturity flag — send date is ≥1 full calendar week in the past; safe for rate computation |
| WILLING_TO_MEET_COUNT | Count of replies classified as highest-quality intent (`willing_to_meet`) |
| CC_VERSION | Which Content Center product version configured the email step |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from dbt SQL + YML + MD docs | Sai (via Jarvis) |
