# DIM_SALESFORCE_OPPORTUNITIES

> Salesforce opportunities dimension. One row per opportunity. 413 columns total.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_OPPORTUNITIES` |
| **Grain** | One row per Salesforce Opportunity (`ID`) |
| **Row count** | ~3.0M (2026-03-06) |
| **Refresh cadence** | Unknown — not built in airflow-dags repo. Referenced downstream by `gong_opportunity_calls_ai_analysis` DAG. |
| **Coverage period** | Ongoing (live Fivetran sync) |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | Analytics / Sales Ops |
| **DAG** | Not found in airflow-dags. Built by Salesforce Fivetran integration + dbt external to this repo. |

## Description

Core sales pipeline table (32 distinct users, 46K queries). Powers S1→S2 CVR funnel, closed-won ARR by motion/segment, SQO tracking, and fiscal quarter analysis in Looker. 413 columns — most are custom SFDC fields.

## Upstream Sources

| Source | Relationship |
|---|---|
| RAW_FIVETRAN_DB.SALESFORCE.OPPORTUNITY | Raw Fivetran sync (14 distinct users query raw directly) |

## Key Columns

### Identity & Core

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| ID | TEXT | 29 | 35,961 | Opportunity ID | **Primary key** |
| NAME | TEXT | 24 | 2,062 | Opportunity name | |
| TYPE | TEXT | 27 | 39,049 | Opportunity type | Values: New Business, Upsell, Renewal, Refund, Existing Business, Freemium, Downgrade |
| OWNER_ID | TEXT | 25 | 33,695 | Opportunity owner | **FK to DIM_SALESFORCE_USERS.ID** |
| ACCOUNT_ID | TEXT | 25 | 28,981 | Parent SF account | **FK to DIM_SALESFORCE_ACCOUNTS.ID** |
| APOLLO_TEAM_ID | TEXT | 25 | 14,080 | Apollo team mapping | **FK to DIM_MONGO_TEAMS.TEAM_ID** |

### Pipeline Status

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| STAGE_NAME | TEXT | 25 | 6,309 | Current pipeline stage | Values: Discovery, Solution Evaluation, Pricing Negotiation, Out for Signature, Closed Won/Lost |
| IS_WON | BOOLEAN | 24 | 28,238 | Won flag | Closed-won filter |
| IS_CLOSED | BOOLEAN | 23 | 6,530 | Closed flag (won or lost) | |
| IS_SQO | BOOLEAN | — | — | SQO flag | **Stage 2 indicator**; used in all funnel queries |
| FORECAST_CATEGORY | TEXT | — | — | Forecast category | |
| UNQUALIFIED_REASON_C | TEXT | — | — | Disqualification reason | Filter: `<> 'Duplicate'` |
| LOSS_REASON_C | TEXT | — | — | Loss reason | Filter: `<> 'Duplicate'` |

### Stage Dates

| Column | Type | Description | Notes |
|---|---|---|---|
| CREATED_AT | TIMESTAMP_NTZ | Opp creation date | **Stage 1 date anchor** — use for funnel entry counts. Use `::DATE` cast for date-only comparisons (e.g. `CREATED_AT::DATE >= '2025-01-01'`) |
| DISCOVERY_STAGE_DATE | DATE | Date opp entered Discovery stage | Stage-entry date, not the standard anchor |
| SQO_DATE_C | DATE | SQO date | Use when you need Stage 2 date as anchor |
| QUALIFICATION_STAGE_DATE | DATE | Qualification date | Fiscal quarter pipeline analysis |
| SOLUTION_EVALUATION_STAGE_DATE | DATE | Solution Evaluation entry date | |
| INITIAL_MEETING_DATE_C | DATE | First meeting date | Custom field |
| CLOSED_AT | TIMESTAMP_NTZ | Close date | **Anchor for closed-won ARR**. Use `::DATE` cast for date-only comparisons (e.g. `CLOSED_AT::DATE >= '2025-01-01'`) |
| CLOSED_WON_AT | DATE | Closed-won date | |

### ARR / Revenue Measures

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| NEW_ANNUALIZED_DELTA_ARR | NUMBER | 21 | 17,158 | Net new annualized ARR delta | **Use for rep-driven closed-won ARR reporting** |
| NEW_ARR | NUMBER | — | — | Pre-computed new ARR | Use over `ARR_C` for won deal ARR in Looker |
| ARR_C | NUMBER | 24 | 9,283 | Opportunity ARR | Custom field |
| RENEWED_ARR | NUMBER | — | — | Renewed ARR portion | |
| UPGRADE_ARR | NUMBER | — | — | Upgrade ARR | |
| DOWNGRADE_ARR | NUMBER | — | — | Downgrade ARR | |
| CANCELLED_ARR | NUMBER | — | — | Cancelled ARR | |
| MID_TERM_UPSELL_ARR | NUMBER | — | — | Mid-term upsell ARR | |
| CONTRACT_ARR | NUMBER | — | — | Contract ARR | |

### Segmentation & Channel

| Column | Type | Description | Notes |
|---|---|---|---|
| LEAD_SOURCE_BUCKET | TEXT | Channel/lead source bucket | **Primary channel dimension.** Values: System (PLG/self-serve, dominant), Demo Request (MQL-A), Customer Advocate (CAQL), Product Feature Gate (PQL-A), Partner (ChQL), Outbound BDR (SQL-B), Outbound AE (SQL-A), Growth (PQL-A), PLSM (PQL-B), Webinar & Marketing Content (MQL-B), Referral/Network (SQL-C), Customer Success (CSQL), Other |
| LEAD_SOURCE | TEXT | Raw lead source | Used to compute LEAD_SOURCE_BUCKET |
| TO_F_SALES_BUCKET | TEXT | TOF sales bucket | 6 values: Marketing, Outbound BDR, Outbound AE/AM, Partner, Customer Success, Other. Filter: `<> 'Other'` in some views |
| INBOUND_OUTBOUND | TEXT | Inbound vs outbound flag | Computed field |
| SALES_MOTION_C | TEXT | Sales motion | Custom field |
| TEAM_SALES_TYPE | TEXT | Team sales type | |
| SMB_SEGMENT_C | TEXT | SMB sub-segment | |
| SQO_SEGMENT_C | TEXT | Segment at SQO time | |
| OPPORTUNITY_SIZE_C | TEXT | Deal size bucket | |
| USE_CASE_C | TEXT | Use case | |
| PERSONA_C | TEXT | Buyer persona | |
| PARTNER_TYPE | TEXT | Partner type | |
| SDR_CAMPAIGN_C | TEXT | SDR campaign | |
| OUTBOUND_SALES_MATURITY_C | TEXT | Outbound sales maturity | |
| UTM_SOURCE_C | TEXT | UTM source at opp create | Last-touch attribution |
| UTM_MEDIUM_C | TEXT | UTM medium | |
| UTM_CAMPAIGN_C | TEXT | UTM campaign | |
| UTM_CONTENT_C | TEXT | UTM content | |
| UTM_TERM_C | TEXT | UTM term | |

### Package & Contract

| Column | Type | Description | Notes |
|---|---|---|---|
| PACKAGE_TYPE_C | TEXT | Package type | |
| CONTRACT_TERM_C | TEXT | Contract term | |
| PRICING_VERSION_C | TEXT | Pricing version | |
| PAYMENT_METHOD_C | TEXT | Payment method | |
| PAYMENT_SCHEDULE_C | TEXT | Payment schedule | |
| NEW_PRICING_CONTRACT_TERM_C | TEXT | New pricing contract term | |
| ZP_OPPORTUNITY_SEAT_TYPE_C | TEXT | Seat type | |
| ZP_OPPORTUNITY_EDITION_V_2_C | TEXT | Edition at SQO | |
| HIGHEST_TEAM_PLAN_ON_CREATE_C | TEXT | Highest plan at opp create | |

### Owner Hierarchy (Point-in-Time at Close)

| Column | Type | Description |
|---|---|---|
| CLOSED_WON_OWNER_NAME | TEXT | AE name at close |
| CLOSED_WON_OWNER_POSITION | TEXT | AE position at close |
| CLOSED_WON_OWNER_MANAGER_NAME | TEXT | AE manager at close |
| CLOSED_WON_OWNER_L2_MANAGER_NAME | TEXT | L2 manager at close |
| GOAL_OPPORTUNITY_OWNER_POSITION_NAME | TEXT | Owner position at opp create |
| GOAL_OPPORTUNITY_ACCOUNT_SEGMENT | TEXT | Account segment at opp create (ENT/MM/SMB) |
| GOAL_OPPORTUNITY_TYPE | TEXT | Type at opp create |
| GOAL_OPPORTUNITY_LEAD_SOURCE_INBOUND_OR_OUTBOUND | TEXT | Inbound/outbound at create |
| GOAL_OPPORTUNITY_LEAD_TOF_SALES_BUCKET | TEXT | TOF bucket at create |
| GOAL_OPPORTUNITY_ACCOUNT_ORG_OR_NON_ORG_ON_OPPORTUNITY_CREATE | TEXT | Org/Non-Org at create |

### Renewal / NRR Experiment Fields

| Column | Type | Description |
|---|---|---|
| RENEWAL_OUTCOME | TEXT | Renewal result |
| REVENUE_CATEGORIZATION_OVERRIDE | TEXT | Override for revenue categorization |
| NRR_EXPERIMENT_DISQUALIFICATION_DATE | DATE | Disqualification date for NRR experiment |
| NRR_EXPERIMENT_ONBOARDING_ELIGIBILITY | TEXT | NRR experiment eligibility flag |
| IS_OM_EXPERIMENT_ELIGIBILITY_MET | BOOLEAN | OM experiment eligibility |

## How It's Used

### Sales Funnel — New Business Pipeline (S1 → S2 CVR)

Primary funnel query anchored on `CREATED_AT`. **Stage 1 → Stage 2 CVR** (total created → SQO) is the key exec metric. Channel cut uses `LEAD_SOURCE_BUCKET`.

```sql
SELECT
    DATE_TRUNC('quarter', o.CREATED_AT)               AS created_quarter,
    COUNT(DISTINCT o.ID)                               AS total_stage1_opps,
    COUNT(DISTINCT CASE WHEN o.IS_SQO THEN o.ID END)  AS sqo_count,
    -- S1→S2 CVR
    ROUND(COUNT(DISTINCT CASE WHEN o.IS_SQO THEN o.ID END)
          / NULLIF(COUNT(DISTINCT o.ID), 0) * 100, 1) AS s1_to_s2_cvr_pct,
    COUNT(DISTINCT CASE WHEN o.IS_WON THEN o.ID END)  AS won_count
FROM ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_OPPORTUNITIES o
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_USERS u    ON o.OWNER_ID = u.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa ON o.ACCOUNT_ID = sa.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat ON o.APOLLO_TEAM_ID = sat.SFDC_TEAM_ID
WHERE o.TYPE = 'New Business'
  AND o.CREATED_AT >= DATEADD('day', -721, CURRENT_DATE)
  AND (u.NAME <> 'Marketo Sync' OR u.NAME IS NULL)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1 ORDER BY 1 DESC;
```

**Stage mapping:**

| Stage | Column/Flag |
|-------|-------------|
| Stage 1 — Created | `CREATED_AT` (date anchor) |
| Stage 2 — SQO | `IS_SQO = true` |
| Stage 3 — Solution Evaluation | `STAGE_NAME = 'Solution Evaluation'` |
| Stage 4 — Pricing Negotiation | `STAGE_NAME = 'Pricing Negotiation'` |
| Stage 5 — Out for Signature | `STAGE_NAME = 'Out for Signature'` |
| Stage 6 — Won | `IS_WON = true` |

### Closed Won ARR by Motion × Segment (Rep-Driven)

Anchors on `CLOSED_AT`. Motion = `TYPE` (New Business vs Upsell). Segment derived from `DIM_SALESFORCE_ACCOUNTS.ACCOUNT_SALES_DEPARTMENT_TIER` (not `ACCOUNT_SEGMENT`).

```sql
SELECT
    DATE_TRUNC('month', o.CLOSED_AT)               AS closed_month,
    o.TYPE                                          AS motion,              -- 'New Business' | 'Upsell'
    CASE
        WHEN sa.ACCOUNT_SALES_DEPARTMENT_TIER IN ('Tier 1', 'Tier 2') THEN 'MM'
        WHEN sa.ACCOUNT_SALES_DEPARTMENT_TIER IN ('Tier 3', 'Tier 4') THEN 'SMB'
        ELSE sa.ACCOUNT_SALES_DEPARTMENT_TIER
    END                                             AS segment,
    COALESCE(SUM(o.NEW_ANNUALIZED_DELTA_ARR), 0)   AS total_new_annualized_delta_arr
FROM ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_OPPORTUNITIES o
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_USERS u        ON o.OWNER_ID = u.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_USERS mgr      ON u.MANAGER_ID = mgr.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa    ON o.ACCOUNT_ID = sa.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat ON o.APOLLO_TEAM_ID = sat.APOLLO_TEAM_ID
WHERE o.IS_WON
  AND o.TYPE IN ('New Business', 'Upsell')
  AND o.CLOSED_AT >= DATEADD('month', -24, DATE_TRUNC('month', CURRENT_DATE))
  AND (u.NAME   <> 'Marketo Sync' OR u.NAME IS NULL)
  AND (mgr.NAME <> 'Tania Garcia Chavez' OR mgr.NAME IS NULL)  -- excludes renewals/CS team
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1, 2, 3
ORDER BY 1 DESC;
```

**Key notes:**
- `NEW_ANNUALIZED_DELTA_ARR` — annualized ARR delta (net change vs prior period); use for rep-driven ARR reporting
- `ACCOUNT_SALES_DEPARTMENT_TIER` is the rep-driven segment (not `ACCOUNT_SEGMENT`); Tier 1/2 = MM, Tier 3/4 = SMB
- Manager exclusion (`Tania Garcia Chavez`) removes a renewals/CS manager from rep-driven view
- `IS_CORE_ACCOUNT` is a no-op (always-true Looker expression) — omit from direct SQL

### Available Segmentation Cuts

| Dimension | Column | Notes |
|-----------|--------|-------|
| Motion / deal type | `TYPE` | New Business, Upsell, Renewal, Refund |
| Rep-driven segment | `ACCOUNT_SALES_DEPARTMENT_TIER` (on accounts) | Tier 1/2 → MM, Tier 3/4 → SMB |
| Account segment | `ACCOUNT_SEGMENT` (on accounts) | Enterprise, Mid-Market, SMB, VSB — standard filter |
| Channel | `LEAD_SOURCE_BUCKET` | System, Demo Request (MQL-A), Customer Advocate (CAQL), etc. (17 values) |
| TOF sales bucket | `TO_F_SALES_BUCKET` | Marketing, Outbound BDR, Outbound AE/AM, Partner, Customer Success, Other |
| Inbound/Outbound | `INBOUND_OUTBOUND` | Computed field |
| Sales motion | `SALES_MOTION_C` | Custom field |
| UTM attribution | `UTM_SOURCE_C`, `UTM_MEDIUM_C`, `UTM_CAMPAIGN_C` | Last-touch at opp create |
| Owner hierarchy | `CLOSED_WON_OWNER_NAME`, `CLOSED_WON_OWNER_POSITION` | Point-in-time at close |
| Package / contract | `PACKAGE_TYPE_C`, `CONTRACT_TERM_C`, `PRICING_VERSION_C` | |
| Edition (at SQO) | `ZP_OPPORTUNITY_EDITION_V_2_C` | |

### Other common patterns
- **SQO counts by week**: `COUNT(DISTINCT CASE WHEN is_sqo THEN ID END)` grouped by `SQO_DATE_C` week
- **Fiscal quarter pipeline**: grouped by `QUALIFICATION_STAGE_DATE` fiscal quarter (Feb fiscal year)
- Always joined with `DIM_SALESFORCE_USERS` as `opportunity_owner` on `OWNER_ID`
- Standard filters: `TYPE IN ('New Business', 'Upsell')`, `UNQUALIFIED_REASON_C <> 'Duplicate'`, `TO_F_SALES_BUCKET <> 'Other'`, owner `<> 'Marketo Sync'`

### Key consumers
- Looker (sales pipeline dashboards)
- Sales ops reporting

## Known Issues & Gotchas

- Fiscal year starts in February (11-month offset in Looker date math)
- `IS_CORE_ACCOUNT` is a **no-op** in Looker (evaluates to always-true) — omit it in direct SQL
- `ACCOUNT_SALES_DEPARTMENT_TIER` (rep-driven segment) ≠ `ACCOUNT_SEGMENT` (standard filter) — use the right one for the right report
- Standard exclusions to always apply: `TYPE IN ('New Business', 'Upsell')`, owner `<> 'Marketo Sync'`, `LOSS_REASON_C/UNQUALIFIED_REASON_C <> 'Duplicate'`
- Rep-driven closed-won views also exclude manager `Tania Garcia Chavez` (renewals/CS team)
- "System" lead source bucket (~40% of opps) = self-serve / PLG; can dominate channel cuts if not filtered
- 413 columns total — don't `SELECT *`; pull specific columns

## Slack Context

- **SQO pipeline tracking**: Sales ops tracks SQO counts by week and fiscal quarter. Pipeline dashboards filter by TYPE (New Business, Upsell) and exclude Marketo Sync owner and Duplicate unqualified reason.
- **Dialer monetization (Alex Beckham)**: Using "Jobs to be done" field to filter opps where parallel/power dialing contributed. Building pipeline reports for dialer specifically.
- **Opportunity data discrepancies (Tina Zhang)**: Found discrepancies in Pipeline Created (S2 Reached) section in Looker. Active investigation.
- **Sales ops hygiene (Helene Rojas)**: Questions about whether upsell opps should show full deal amount vs quota-relevant amount (60%). Impacts forecasting accuracy.
- **Ramp metrics (ext-fullcast-apollo)**: Need time to first Stage 2 opp, S2 pipeline by ramp month 2, % of wins at/above ACV target by ramp month 4. Pipeline replenishment rate after first win.
- **Glean docs**: "Resolve SFDC Opportunity Issues caused by monetization logic", "2 → 1 Opportunity Migration" — active cleanup of opp data quality.

## Business Terms

| Term | Definition |
|---|---|
| SQO | Sales Qualified Opportunity — an opportunity that has met qualification criteria (Stage 2) |
| S1→S2 CVR | Stage 1 to Stage 2 conversion rate — primary pipeline efficiency metric (SQO count / total opps created) |
| TOF Sales Bucket | Top-of-funnel lead source classification — 6 buckets: Marketing, Outbound BDR, Outbound AE/AM, Partner, CS, Other |
| New Business | Motion type for new logo deals (first-time customer) |
| Upsell | Motion type for expanding an existing customer |
| Rep-Driven ARR | Closed-won ARR from AE/BDR activity — segmented by ACCOUNT_SALES_DEPARTMENT_TIER (Tier 1/2 = MM, Tier 3/4 = SMB) |
| NEW_ANNUALIZED_DELTA_ARR | Annualized ARR change for a won opp (net delta vs prior period); the canonical rep performance metric |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
| 2026-03-20 | Added sales funnel pattern (S1→S2 CVR), closed-won ARR by motion×segment, full column expansion (413 cols), all segmentation cuts, stage dates, ARR measures, owner hierarchy, NRR experiment fields | Leo |
| 2026-04-02 | Schema drift fix: CLOSED_AT and CREATED_AT corrected from DATE to TIMESTAMP_NTZ; added ::DATE cast guidance | Bridie (schema drift detection) |
