# FCT_AI_EMAIL_MESSAGING

> Message-level fact table for AI email engagement. One row per outreach or extension email sent or failed, enriched with the full sequence hierarchy.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.FCT_AI_EMAIL_MESSAGING` |
| **Grain** | One row per `emailer_messages_id` |
| **Row count** | — (incremental from 2026-03-02) |
| **Refresh cadence** | Daily incremental; 4-week lookback on each run |
| **Trust level** | Authoritative (DS-owned, part of AI platform model hierarchy) |
| **Owner** | Data Science (Sai Sarvepalli) — `#proj-ai-platform` |
| **DAG** | dbt model: `models/marts/data_science/ai_platform/fct_ai_email_messaging.sql` |

## Description

Replaces Amplitude-sourced email engagement with Mongo-native signals from `fct_mongo_emailer_messages`. Joins the full sequence hierarchy at build time so any downstream aggregation (daily, weekly, by CC version, by step depth, by template) is a simple `GROUP BY` — no runtime joins needed.

**Upstream hierarchy:**
```
fct_mongo_emailer_campaigns   (sequence name, campaign CC version, creation type)
    └── dim_mongo_emailer_steps      (step_position, step_type, wait timing)
        └── dim_mongo_emailer_touches (cc_version at step level, template FK)
            └── dim_mongo_emailer_templates (template AI flags, prompt ID)
fct_mongo_emailer_messages    (message grain — all engagement signals)
```

**Downstream:** `agg_ai_email_messaging` (pre-aggregated daily dimension slices), Looker / Hex dashboards.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| AI_EMAIL_MESSAGE_KEY | TEXT | Surrogate key (hash of `emailer_messages_id`) | Stable BI-tool FK |
| EMAILER_MESSAGES_ID | TEXT | Natural PK from MongoDB | Unique per row |
| EMAILER_STEP_ID | TEXT | FK to `dim_mongo_emailer_steps` | |
| EMAILER_CAMPAIGN_ID | TEXT | FK to `fct_mongo_emailer_campaigns` | |
| EMAILER_TEMPLATE_ID | TEXT | FK to `dim_mongo_emailer_templates` via latest touch | |
| TEAM_ID | TEXT | Sender's Apollo team ID | |
| USER_ID | TEXT | Sender's Apollo user ID | |
| CONTACT_ID | TEXT | Recipient's Apollo contact ID | |
| ACCOUNT_ID | TEXT | Recipient's Apollo account ID | |
| EMAIL_SENT_AT | TIMESTAMP_NTZ | Completion timestamp (`completed_at`) | |
| EMAIL_SENT_DATE | DATE | Calendar date of send | Cluster key |
| EMAIL_SENT_WEEK | DATE | Sunday of send week (`DATE_TRUNC('week', ...)`) | |
| IS_SENT_BEFORE_LAST_WEEK | BOOLEAN | True if send week is ≥1 full week in the past | **Gate for rate math** — see gotchas |
| EMAIL_TYPE | TEXT | `outreach_automatic_email`, `outreach_manual_email`, `extension_email` | |
| EMAIL_STATUS | TEXT | `Completed` or `Failed` | |
| SURFACE | TEXT | UI surface from which email was sent | |
| NOT_SENT_REASON | TEXT | Reason code when email was not sent | |
| FAILURE_REASON | TEXT | Detail when `email_status = 'Failed'` | |
| HAS_AI_CONTENT | BOOLEAN | True if `ai_variables_used` array is non-empty | Primary AI signal |
| AI_VARIABLES_COUNT | NUMBER | Count of AI variables used (0 = no AI) | |
| HAS_PERSONALIZED_OPENER | BOOLEAN | True if personalized opening line present | |
| PERSONALIZATION_SCORE | FLOAT | Quality score of AI personalization match | |
| CC_VERSION | TEXT | `CC v3`, `Legacy CC`, or `No CC` — step-level signal (most granular) | From `dim_mongo_emailer_touches` |
| CAMPAIGN_CC_VERSION | TEXT | `CC v3`, `Legacy CC`, or `No CC` — sequence-level signal | From `fct_mongo_emailer_campaigns`; may differ from `CC_VERSION` |
| STEP_POSITION | TEXT | Position of step in sequence (e.g. `'1'` = first touch) | `'unknown'` when unresolvable |
| STEP_TYPE | TEXT | Step type: `email`, `call`, `linkedin`, etc. | `'unknown'` when unresolvable |
| STEP_WAIT_MODE | TEXT | Wait mode between steps (business days, calendar days, etc.) | |
| STEP_WAIT_TIME | NUMBER | Configured wait duration before this step | |
| SEQUENCE_NAME | TEXT | Human-readable name of the sequence | |
| SEQUENCE_CREATION_TYPE | TEXT | How the sequence was created (manual, template, AI-generated) | |
| SEQUENCE_PERMISSIONS | TEXT | Sharing permission level for the sequence | |
| SEQUENCE_AUDIENCE | TEXT | Target audience type on the sequence | |
| IS_AB_TEST_SEQUENCE | BOOLEAN | True if sequence has A/B test steps configured | |
| TEMPLATE_HAS_AI_VARIABLES | BOOLEAN | True if the email template has AI variable placeholders | False when template unresolvable |
| TEMPLATE_CREATION_TYPE | INTEGER | How the template was created | |
| PROMPT_TEMPLATE_ID | TEXT | ID of the AI prompt template used, if applicable | |
| IS_TRACKING_ENABLED | BOOLEAN | Whether open/click tracking was enabled | |
| IS_OPEN_TRACKING_ENABLED | BOOLEAN | Whether open-tracking pixel was enabled | |
| IS_CLICK_TRACKING_ENABLED | BOOLEAN | Whether link/click tracking was enabled | |
| DELIVERED | INTEGER | 1 if confirmed delivered, else 0 | Rate-safe only after `IS_SENT_BEFORE_LAST_WEEK` filter |
| OPENED | INTEGER | 1 if email was opened, else 0 | Includes bot opens — see IS_BOT_OPENED |
| REPLIED | INTEGER | 1 if recipient replied, else 0 | Rate-safe only after maturity filter |
| DEMOED | INTEGER | 1 if demo was booked from this email, else 0 | Rate-safe only after maturity filter |
| BOUNCED | INTEGER | 1 if email bounced (soft or hard), else 0 | |
| FAILED | INTEGER | 1 if send failed (`email_status = 'Failed'`), else 0 | |
| CLICKED | INTEGER | 1 if any link was clicked, else 0 | |
| UNSUBSCRIBED | INTEGER | 1 if recipient unsubscribed via this email, else 0 | |
| SPAM_BLOCKED | INTEGER | 1 if blocked by spam filters, else 0 | |
| IS_BOT_OPENED | BOOLEAN | True if open attributed to a bot | Filter `IS_BOT_OPENED = false` for human open rates |
| HARD_BOUNCED | INTEGER | 1 if permanent delivery failure, else 0 | |
| REPLY_CLASS | TEXT | Classification of reply: `willing_to_meet`, `not_interested`, `out_of_office`, etc. | NULL when no reply |
| LOADED_AT | TIMESTAMP_NTZ | Row write timestamp (UTC). Audit column. | |

## How It's Used

### Common query patterns
- AI vs non-AI performance — filter `HAS_AI_CONTENT = true/false`, compare `reply_rate` and `demo_rate`
- CC version adoption impact — slice by `CC_VERSION = 'CC v3'` vs others
- Step-depth analysis — group by `STEP_POSITION` to see engagement drop-off across sequence steps
- Weekly reply/demo rates — aggregate by `EMAIL_SENT_WEEK` where `IS_SENT_BEFORE_LAST_WEEK = true`

### Key consumers
- `agg_ai_email_messaging` (immediate downstream — pre-aggregated daily slice table)
- Looker / Hex dashboards for AI email engagement reporting

## Known Issues & Gotchas

- **Maturity gate is mandatory for rates.** Reply and demo signals accumulate for several days post-send. Always filter `WHERE IS_SENT_BEFORE_LAST_WEEK = true` before computing `delivery_rate`, `reply_rate`, or `demo_rate`. Do NOT null out immature data — leave it visible so consumers control the gate.
- **Bot opens inflate OPENED.** Filter `IS_BOT_OPENED = false` when computing human open rates.
- **Two CC version columns.** `CC_VERSION` (step-level, from `dim_mongo_emailer_touches`) is the most granular signal. `CAMPAIGN_CC_VERSION` (sequence-level) may differ when individual steps have been reconfigured independently. Use `CC_VERSION` for step-level analysis.
- **Start date is 2026-03-02.** No data before this date — queries spanning earlier periods will return nothing.
- **4-week incremental lookback.** Reply/demo signals can arrive weeks after send. The 4-week window ensures late-arriving signals are reprocessed on each run.
- **`STEP_POSITION` and `STEP_TYPE` default to `'unknown'`** (not NULL) when the step cannot be resolved. Filter accordingly.

## Business Terms

| Term | Definition |
|---|---|
| HAS_AI_CONTENT | True if any AI-generated variable was used in the email body |
| CC_VERSION | Which Content Center product version configured the email step |
| IS_SENT_BEFORE_LAST_WEEK | Maturity flag — send week is ≥1 full calendar week in the past; safe for rate computation |
| REPLY_CLASS | AI-classified reply intent: `willing_to_meet`, `not_interested`, `out_of_office`, etc. |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from dbt SQL + YML + MD docs | Sai (via Jarvis) |
