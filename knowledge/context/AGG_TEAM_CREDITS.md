# AGG_TEAM_CREDITS

> **Canonical SoT for customer-billed credit consumption.** Use `FEATURE_TYPE` (not `CREDIT_TYPE`) as the primary filter — CREDIT_TYPE has duplicate naming variants and is inconsistently populated.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS` |
| **Grain** | One row per team + date + product + feature type |
| **Row count** | ~1.06B (2026-03-06) |
| **Refresh cadence** | Every 6 hours (`15 */6 * * *`) |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | Brighid (data quality), Analytics team |
| **DAG** | `analytics_agg_team_credits`. Config: `dags/analytics/config/agg_team_credits.yml`. SQL: `dags/analytics/dag_imports/sql_files/agg_team_credits_dag.sql`. Creates intermediate STG_AGG_CU and STG_CREDIT_SOURCES. |

## Description

Credit usage aggregation table (32 distinct users, ~9K queries). Used for tracking unified vs non-unified credit consumption per team. Monitored by Metaplane for data quality. A playground copy exists at `ANALYTICS_DB.PLAYGROUND.AGG_TEAM_CREDITS` (23 users).

## Upstream Sources

| Source | Relationship |
|---|---|
| FCT_MONGO_CREDIT_USAGES | Likely upstream credit facts |
| FCT_MONGO_CREDIT_USAGE_DETAILS | Granular credit details |
| <!-- TODO: verify via DAG lineage --> | |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| DS | DATE | 32 | 7,580 | Date dimension | Often aliased as `date` in queries |
| CREDITS_USED | NUMBER | 32 | 7,394 | Credits consumed — **the billing metric** | NULL for some feature types (e.g. form_enrichment); check before SUM |
| TEAM_ID | TEXT | 31 | 6,901 | Apollo team ID | **FK to DIM_MONGO_TEAMS.TEAM_ID** — note: NOT `apollo_team_id` |
| FEATURE_TYPE | TEXT | 31 | 6,575 | **Primary filter column** — canonical feature category | Use this, not CREDIT_TYPE. See full value list below. |
| CREDIT_TYPE | TEXT | 27 | 3,713 | Credit currency type (e.g. `unified_lead_credit`, `email_credit`) | **Do not use as feature filter** — has duplicates (snake_case + Title Case variants from two pipelines) |
| PRODUCT_ID | TEXT | 24 | 3,074 | Product/plan identifier | `%unified%` = unified credits plan; legacy plans have different IDs |
| CREDIT_LIMIT | NUMBER | 24 | 2,398 | Team's credit allocation for billing period | Unreliable — doesn't capture all allocation sources (see Known Issues) |
| BILLING_PERIOD_START | DATE | 23 | 1,324 | Billing period start date | Use with BILLING_PERIOD_END to scope to active billing window |
| BILLING_PERIOD_END | DATE | 23 | 1,104 | Billing period end date | |
| CREDIT_SOURCES | VARIANT | 22 | 288 | Breakdown of credit source (trial vs unified vs other) | Semi-structured — recently changed (PR #2665). Use for deep-dives, not standard queries. |

## FEATURE_TYPE Values — Full Taxonomy (verified 2026-03-22, last 3 months)

| FEATURE_TYPE | What it represents | Billed? |
|---|---|---|
| `searcher_emails` | Revealing emails via Searcher/prospecting | Yes |
| `direct_dial` | Phone number lookups | Yes (3–10 credits, region-based) |
| `waterfall_enrichment` | Email enrichment via vendor waterfall cascade | Yes |
| `power_up` | AI Power Ups (research, opener, etc.) | Yes |
| `api_access` | API credit consumption | Yes |
| `ai_email` | AI-written emails — draws from AI Word pool | **No** — not customer-billed, exclude from totals |
| `csv_export` | CSV export | **No** — free, credits consumed at enrichment time |
| `csv_enrichment_email` | CSV upload enrichment | Yes |
| `waterfall_mobile_enrichment` | Phone number enrichment via vendor waterfall | Yes |
| `linkedin_emails` | LinkedIn extension email pulls | Yes |
| `conversation` | Conversation intelligence | **No** — included feature |
| `hubspot_push` | HubSpot sync | **No** — free integration action |
| `auto_enrich_contact` | Auto-enrich when saving contact | Yes |
| `phone_call` | Dialer call credits | Separate $ pool |
| `reverify_emails` | Email re-verification | Yes |
| `change_job` | Job change enrichment | Yes |
| `salesforce_push` | Salesforce sync | **No** — free |
| `crm_field_enrichment` | CRM field sync | **No** — free (consumed at enrichment time) |
| `mailwarming_unified` | Mailbox warmup | Yes |
| `person_enrichment` | Email reveal in prospecting | Yes |
| `domain_and_mailbox_purchase_unified` | Domain/inbox purchasing | Yes |
| `inbound_website_visitor` | Inbound website visitor identification | Yes |
| `dialer_phone_number` | Dialer phone number credit | Yes |
| `rules_engine` | Rules engine automation | Yes |
| `api_waterfall_enrichment` | API-triggered waterfall enrichment | Yes |
| `pipedrive_push` | Pipedrive sync | **No** — free |
| `zapier_push` | Zapier sync | **No** — free |
| `salesloft_push` | Salesloft sync | **No** — free |
| `outreach_push` | Outreach sync | **No** — free |
| NULL | Catch-all / system rows (342M rows) | Unknown — likely admin/overhead |

**Standard exclusions:** `ai_email`, `csv_export`, `crm_field_enrichment`, `hubspot_push`, `salesforce_push`, `pipedrive_push`, `zapier_push`, `salesloft_push`, `outreach_push`, `conversation`

## How It's Used

### Standard credit consumption query
```sql
SELECT
    DATE_TRUNC('week', DS) AS week_start,
    FEATURE_TYPE,
    COUNT(DISTINCT TEAM_ID) AS teams,
    SUM(CREDITS_USED) AS total_credits
FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS
WHERE DS >= DATEADD('week', -8, CURRENT_DATE())
  AND FEATURE_TYPE NOT IN ('ai_email','csv_export','crm_field_enrichment',
                            'hubspot_push','salesforce_push','pipedrive_push',
                            'zapier_push','salesloft_push','outreach_push','conversation')
  AND FEATURE_TYPE IS NOT NULL
GROUP BY 1, 2
ORDER BY 1 DESC, 4 DESC;
```

### Waterfall credit query
```sql
-- Filter: FEATURE_TYPE IN ('waterfall_enrichment','waterfall_mobile_enrichment','api_waterfall_enrichment')
-- Note: CREDITS_USED is NULL for some rows — always check SUM returns non-null
```

### Other common patterns
- Split by unified vs non-unified: `IFF(LOWER(product_id) ILIKE '%unified%', credits_used, 0)`
- Filtered by team and date range: `ds > current_date - 90 AND team_id = ?`
- `feature_type NOT IN ('ai_email')` is the minimum exclusion for customer-facing metrics
- Metaplane monitors `PRODUCT_ID` and `FEATURE_TYPE` distributions

### Key consumers
- DA_TOOL_USER (team health dashboards / AI agent)
- Metaplane (data quality monitoring)
- Analysts (credit analysis, team health)

## Known Issues & Gotchas

- Recent PR #2665 removed audit report dependency from STG_CREDIT_SOURCES — lineage may have changed
- Playground copy (`ANALYTICS_DB.PLAYGROUND.AGG_TEAM_CREDITS`) is actively queried — may have diverged from production
- `ai_email` feature_type is commonly excluded from credit totals

## Slack Context

- **Data integrity problem (Brighid → Monetization, Jan 2026)**: Credits can be added from multiple sources but we only log some — analytics regularly sees more credits consumed than assigned. Breaks utilization metrics that feed upsell decisions and core business reporting. Need daily snapshot of actual credit limits from all sources.
- **Unified credit migration bugs (Brandon Renfrow)**: Teams migrated to unified credits saw historical usage data change, making it look like they exceeded limits when they may not have. Migration timing matters for accuracy.
- **CSV limit confusion (Zobaida, Monetization)**: High-ARR customers hitting CSV export limits on unified credit model. Manual admin adjustments possible but unclear if safe.
- **Glean docs**: "Daily audit team report shows credit overages vs limits (Monetization data bug)", "Ongoing Challenges in Daily Audit Team Reports Table and Data Collection", "Credit Utilization Metric Discrepancies" — multiple open issues around credit data accuracy.
- **Free-to-paid strategy (Brendan Walker)**: Wants to increase free user credit consumption to drive feature gates → upgrades. Needs credit usage data joined with conversion outcomes.
- **Key concern**: CREDIT_SOURCES column recently changed (PR #2665). The utilization metric (credits_used / credit_limit) is unreliable because credit_limit doesn't capture all allocation sources.

## Business Terms

| Term | Definition |
|---|---|
| Unified Credits | Apollo's consolidated credit system (vs legacy per-feature credits) |
| Feature Type | Category of Apollo feature that consumed credits |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
| 2026-03-22 | Added canonical SoT note, full FEATURE_TYPE taxonomy (verified from INFORMATION_SCHEMA + live queries), CREDIT_TYPE warning, standard query patterns | Leo (via Jarvis) |
