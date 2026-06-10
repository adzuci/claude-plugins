# Shared SQL Patterns & Conventions

Canonical query patterns for the Apollo analytics team. When in doubt, follow these.

______________________________________________________________________

## HVO calls → apollo_team_id (updated 2026-05-27)

**Preferred: direct join** — `HVO_CALLS_AI_PROCESSING` now has a direct `APOLLO_TEAM_ID` column (added ~2026-04, verified via INFORMATION_SCHEMA). Use it for all new queries. The calendar event bridge below is retained as fallback for legacy records where `APOLLO_TEAM_ID` is NULL.

```sql
-- Preferred (post-2026-04)
SELECT ai.*, dt.ACCOUNT_SUB_SEGMENT, dt.ARR
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING ai
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS dt ON dt.APOLLO_TEAM_ID = ai.APOLLO_TEAM_ID
WHERE ai.APOLLO_TEAM_ID IS NOT NULL;
```

**Fallback: calendar event bridge** — use when `APOLLO_TEAM_ID` is NULL on older records:

```sql
WITH hvo_meetings AS (
    SELECT
        REPLACE(t.APOLLO_TEAM_ID, '"', '') AS APOLLO_TEAM_ID,
        f.value::string                     AS CALENDAR_EVENT_ID
    FROM ANALYTICS_DB.ANALYTICS.ONBOARDING_HIGH_VELOCITY_TEAMS t,
         LATERAL FLATTEN(input => t.CALENDAR_EVENT_IDS) f
)
SELECT
    dt.website_domain,
    dt.apollo_team_id,
    ai.date                                  AS hvo_training_date,
    ai.aha_moment,
    ai.feature_discussed,
    ai.pain_point,
    ai.customer_technical_sufficiency_score,
    ai.client_roles
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS                       dt
LEFT JOIN hvo_meetings                                               h   ON h.APOLLO_TEAM_ID    = dt.APOLLO_TEAM_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS f  ON f.CALENDAR_EVENT_ID = h.CALENDAR_EVENT_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING ai ON ai.CONVERSATION_ID  = f.CONVERSATION_ID
WHERE dt.website_domain IS NOT NULL
  AND ai.conversation_id IS NOT NULL
```

**Join chain:** `ONBOARDING_HIGH_VELOCITY_TEAMS` (flatten `CALENDAR_EVENT_IDS`) → `FCT_MONGO_CONVERSATIONS` (via `CALENDAR_EVENT_ID`) → `HVO_CALLS_AI_PROCESSING` (via `CONVERSATION_ID`) → `DIM_TEAMS` (via `APOLLO_TEAM_ID`)

**Gotcha:** `APOLLO_TEAM_ID` in `ONBOARDING_HIGH_VELOCITY_TEAMS` has extra quotes — always `REPLACE(..., '"', '')`.

**Warning — wrong tables:**

- `FCT_MONGO_CONVERSATIONS.TEAM_ID` — this is the **rep's** team, not the customer's. Do not use.
- `DIM_MONGO_CONTACTS.TEAM_ID` — resolves to only 1 distinct team (Apollo internal contacts). Not a valid substitute.

______________________________________________________________________

## GTME calls → apollo_team_id (verified, DEVELOPER_ROLE, 2026-03-20, 97.6% match)

**Different from HVO** — GTME calendar events do NOT appear in `ONBOARDING_HIGH_VELOCITY_TEAMS` (0% tested). Use participants flatten instead:

```sql
WITH gtme_participants AS (
    SELECT
        f.CONVERSATION_ID,
        p.value:contact_id."$oid"::string AS contact_id
    FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS f,
         LATERAL FLATTEN(input => f.CONVERSATION_PARTICIPANTS) p
    WHERE f.CONVERSATION_ID IN (SELECT CONVERSATION_ID FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS)
      AND p.value:contact_id."$oid"::string IS NOT NULL
)
SELECT
    g.*,
    c.APOLLO_TEAM_ID
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS g
JOIN gtme_participants p ON p.CONVERSATION_ID = g.CONVERSATION_ID
JOIN ANALYTICS_DB.ANALYTICS.INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS c
                         ON c.CONTACT_ID = p.contact_id
WHERE c.APOLLO_TEAM_ID IS NOT NULL
```

**Join chain:** `GTME_CALLS_AI_ANALYSIS` → `FCT_MONGO_CONVERSATIONS` (flatten `CONVERSATION_PARTICIPANTS`) → `INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS` → `APOLLO_TEAM_ID`

______________________________________________________________________

## Sequence engagement + deliverability by account (verified, DEVELOPER_ROLE, 2026-03-21)

`ANALYTICS_DATASCIENCE.SEQUENCES` is the canonical table for per-sequence email metrics. Pre-aggregated, has `APOLLO_TEAM_ID` for direct customer joins.

```sql
SELECT
    EMAILER_CAMPAIGN_NAME,
    EMAILER_CAMPAIGN_ID,
    EMAIL_SENT_COUNTS                                                          AS SENT,
    EMAIL_DELIVERED_COUNTS                                                     AS DELIVERED,
    EMAIL_OPENED_COUNTS,
    ROUND(EMAIL_OPENED_COUNTS        / NULLIF(EMAIL_DELIVERED_COUNTS,0)*100,1) AS OPEN_RATE_PCT,
    EMAIL_REPLY_RECEIVED_COUNTS,
    ROUND(EMAIL_REPLY_RECEIVED_COUNTS / NULLIF(EMAIL_DELIVERED_COUNTS,0)*100,1) AS REPLY_RATE_PCT,
    EMAIL_INTEREST_RECEIVED_COUNTS,  -- positive reply / interested signal
    ROUND(EMAIL_INTEREST_RECEIVED_COUNTS / NULLIF(EMAIL_DELIVERED_COUNTS,0)*100,1) AS INTEREST_RATE_PCT,
    EMAIL_BOUNCED_COUNTS,
    ROUND(EMAIL_BOUNCED_COUNTS       / NULLIF(EMAIL_SENT_COUNTS,0)*100,1)     AS BOUNCE_RATE_PCT,
    EMAIL_HARD_BOUNCED_COUNTS,
    ROUND(EMAIL_HARD_BOUNCED_COUNTS  / NULLIF(EMAIL_SENT_COUNTS,0)*100,1)     AS HARD_BOUNCE_RATE_PCT,
    LAST_SENT_AT::DATE
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.SEQUENCES
WHERE APOLLO_TEAM_ID = '<team_id>'
  AND EMAIL_SENT_COUNTS > 0
ORDER BY SENT DESC NULLS LAST
LIMIT 20;
```

**Key columns:** `EMAIL_OPENED_COUNTS`, `EMAIL_REPLY_RECEIVED_COUNTS`, `EMAIL_INTEREST_RECEIVED_COUNTS` (positive reply signal), `EMAIL_BOUNCED_COUNTS`, `EMAIL_HARD_BOUNCED_COUNTS`, `EMAIL_DELIVERED_COUNTS`, `EMAIL_SENT_COUNTS`, `LAST_SENT_AT`.

**Rate denominators:** open/reply/interested rates use `EMAIL_DELIVERED_COUNTS`; bounce rates use `EMAIL_SENT_COUNTS`.

**Note:** Meeting booked is not available per sequence — no FK from emailer messages to calendar/meeting events in Snowflake.

**Source hierarchy (sequence email analysis):**

- **Sequence-level** (open rate, reply rate, bounce rate, interested rate by sequence) → `ANALYTICS_DATASCIENCE.SEQUENCES` ✅ default
- **Message/contact-level** (per-contact open tracking, individual message status, row-level filtering) → `FCT_MONGO_EMAILER_MESSAGES`

______________________________________________________________________

## Segmentation — Default to ACCOUNT_SUBSEGMENT

When breaking out metrics by customer segment, **default to `ACCOUNT_SUBSEGMENT`** from `DIM_SALESFORCE_ACCOUNTS` or `DIM_SALESFORCE_APOLLO_TEAMS`. Do not build ad-hoc boolean combinations as a substitute for named segments.

```sql
-- CORRECT: use ACCOUNT_SUBSEGMENT
SELECT a.ACCOUNT_SUBSEGMENT, COUNT(*) AS teams
FROM analytics_db.analytics.dim_salesforce_apollo_teams sat
JOIN analytics_db.analytics.dim_salesforce_accounts a ON a.ID = sat.ACCOUNT_ID
GROUP BY 1;
```

Only fall back to the boolean Paid Core filter (`is_paid_ind = TRUE AND is_core_account_ind = TRUE AND is_free_email_domain_ind = FALSE`) when ACCOUNT_SUBSEGMENT is unavailable or the question is specifically and explicitly about Paid Core.

______________________________________________________________________

## WAT / WAU — Use DIM_TEAMS_DAILY with L7 columns

`DIM_TEAMS_DAILY` pre-computes 7-day rolling windows in `_USER_COUNTS_L7` columns. To get WAT (weekly active teams), pick **one snapshot date per week** and count distinct teams where the L7 column > 0. The L7 already covers the full 7-day window — do not group across all days in a week.

```sql
-- CORRECT: one snapshot per week (Sunday), L7 covers the full 7 days
SELECT DATE_TRUNC('week', date) AS week,
       COUNT(DISTINCT CASE WHEN active_user_counts_l7 > 0             THEN apollo_team_id END) AS wat,
       COUNT(DISTINCT CASE WHEN meeting_booked_user_counts_l7 > 0     THEN apollo_team_id END) AS meeting_booked_wat,
       COUNT(DISTINCT CASE WHEN ai_platform_user_counts_l7 > 0        THEN apollo_team_id END) AS ai_platform_wat,
       COUNT(DISTINCT CASE WHEN enrichment_api_user_counts_l7 > 0     THEN apollo_team_id END) AS enrichment_api_wat
FROM analytics_db.analytics_datascience.dim_teams_daily
WHERE DAYOFWEEK(date) = 0   -- Sunday snapshot only (canonical week anchor, aligns with Growth)
  AND date >= current_date - 63
  AND is_paid_ind = TRUE AND is_core_account_ind = TRUE AND is_free_email_domain_ind = FALSE
GROUP BY 1 ORDER BY 1 DESC;
```

**Do NOT** sample one day per week from `DIM_USERS_DAILY` with L1 columns (`_COUNTS_L1`) as a WAU proxy — this produces a single-day count (DAU), not WAU, and can misreport trends by large margins.

| Goal | Correct source |
|---|---|
| WAT (weekly active teams) | `DIM_TEAMS_DAILY` — `_USER_COUNTS_L7 > 0`, one snapshot/week |
| DAU (daily active users) | `DIM_USERS_DAILY` — `IS_ACTIVE_L1 = TRUE` on a specific date |
| Feature WAU (user-level) | `DIM_USERS_DAILY` — `_COUNTS_L7 > 0` joined to `DIM_TEAMS_DAILY` for segment filter |

______________________________________________________________________

## NRR — Cohort-Based Methodology

**Cohort entry point:** `FIRST_PAID_DATE` from `ANALYTICS_DATASCIENCE.DIM_TEAMS` (team-level). Cohort month = `DATE_TRUNC('month', FIRST_PAID_DATE)`.

**Window:** **Default to 12M** unless specifically asked for M3. Both use the same cohort logic — only the lookback window differs.

- **12M NRR:** ARR at `cohort_month + 12 months` / ARR at M0
- **M3 NRR:** ARR at `cohort_month + 3 months` / ARR at M0 (target: 90%)

**Do NOT** use point-in-time snapshot comparison (teams paying at date M vs M+12). That approach pollutes NRR with new entrants and produces nonsense results.

**⛔ CRITICAL — Do NOT use `AVG(arr_m3 / arr_m0)`** for NRR. This is the most common NRR calculation mistake. Using an arithmetic mean of per-team ratios inflates NRR dramatically because small teams with high growth (e.g., $100 → $400 = 400% ratio) dominate the average despite being tiny in dollar terms. **Always use `SUM(arr_m3) / SUM(arr_m0)`** — dollar-weighted cohort NRR. This is the only correct method. Confirmed in production: wrong formula gave 108–132%, correct formula gave 102–110% for the same dataset (2026-03-25 incident).

**⛔ CRITICAL — Do NOT use `DATE_TRUNC('month', FIRST_PAID_DATE)` as the ARR snapshot date.** Month-truncating the cohort anchor means all teams that signed up on July 3, July 15, and July 28 all get their M0 ARR measured on July 1 — before many of them even paid. Use **exact `FIRST_PAID_DATE`** per team as the M0 snapshot date, and **`DATEADD('month', N, FIRST_PAID_DATE)`** as the M_N date. For per-team NRR cohort analysis, prefer `DIM_TEAMS_DAILY` (join on `DATE = FIRST_PAID_DATE`) over `FCT_DAILY_REVENUE` for simplicity. (2026-03-25 incident)

```sql
-- Change DATEADD months to 12 for 12M NRR, 3 for M3 NRR
WITH cohort AS (
    SELECT APOLLO_TEAM_ID,
           DATE_TRUNC('month', FIRST_PAID_DATE) AS cohort_month
    FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS
    WHERE DATE_TRUNC('month', FIRST_PAID_DATE) = '<cohort_month>'  -- e.g. '2025-12-01'
),
arr_m0 AS (
    SELECT c.APOLLO_TEAM_ID, r.ARR AS arr_m0
    FROM cohort c
    JOIN ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE r
      ON r.APOLLO_TEAM_ID = c.APOLLO_TEAM_ID
     AND r.DATE_PERIOD = c.cohort_month
),
arr_at_window AS (
    SELECT c.APOLLO_TEAM_ID, r.ARR AS arr_end
    FROM cohort c
    LEFT JOIN ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE r
      ON r.APOLLO_TEAM_ID = c.APOLLO_TEAM_ID
     AND r.DATE_PERIOD = DATEADD('month', 3, c.cohort_month)  -- 3 for M3, 12 for 12M
)
SELECT COUNT(DISTINCT a0.APOLLO_TEAM_ID)                          AS cohort_teams,
       SUM(a0.arr_m0)                                             AS arr_at_m0,
       SUM(COALESCE(aw.arr_end, 0))                               AS arr_at_window,
       SUM(COALESCE(aw.arr_end, 0)) / NULLIF(SUM(a0.arr_m0), 0)  AS nrr
FROM arr_m0 a0
LEFT JOIN arr_at_window aw ON aw.APOLLO_TEAM_ID = a0.APOLLO_TEAM_ID;
```

**Key:** `DIM_TEAMS` is in `ANALYTICS_DATASCIENCE`, NOT `ANALYTICS`. Dec 2025 M3 NRR = 78.1% (target 90%).

### Dedup gotchas

- Use `QUALIFY ROW_NUMBER() OVER (PARTITION BY APOLLO_TEAM_ID ...)` on `DIM_SALESFORCE_APOLLO_TEAMS` when joining for segmentation — teams can have multiple SFDC records
- `IS_PARENT_ACCOUNT` in FCT_DAILY_REVENUE is NOT a reliable account-level dedup — only 4,790 teams on 2025-03-01 had it set vs 72K total paying teams. Group by SFDC_ACCOUNT_ID instead.

______________________________________________________________________

## Feature WAT % (penetration rate, 8-week trend)

Weekly active team penetration rates from `DIM_TEAMS_DAILY`. Sample on **Sundays** (`DAYOFWEEK(DATE) = 0`), consistent with the canonical week anchor used across all WAT/WAU patterns. Denominator = all paid teams on that date.

```sql
SELECT
    DATE_TRUNC('week', date) AS week_start,
    COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END) AS paid_teams,
    -- WAT penetration per feature:
    COUNT(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_SEQUENCE_USER_COUNTS_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS sequence_pct,
    COUNT(CASE WHEN IS_PAID_IND = true AND EMAIL_SENT_USER_COUNTS_OUTREACH_AUTOMATIC_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS auto_email_pct,
    COUNT(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_DIALER_USER_COUNTS_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS dialer_pct,
    COUNT(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_WORKFLOW_USER_COUNTS_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS workflow_pct,
    COUNT(CASE WHEN IS_PAID_IND = true AND EXTENSION_USED_USER_COUNTS_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS extension_pct,
    COUNT(CASE WHEN IS_PAID_IND = true AND USE_CASE_ENRICHMENT_ACTIVE_USER_COUNTS_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS enrichment_pct,
    COUNT(CASE WHEN IS_PAID_IND = true AND AI_PLATFORM_USER_COUNTS_L7 > 0 THEN 1 END)
        / NULLIF(COUNT(CASE WHEN IS_PAID_IND = true THEN 1 END), 0) AS ai_platform_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DAYOFWEEK(date) = 0   -- Sunday snapshot (canonical, aligns with Growth)
  AND date >= DATEADD('week', -8, CURRENT_DATE)
GROUP BY 1
ORDER BY 1;
```

**Interpretation note:** % can decline even when absolute WAT grows — check if it's denominator-driven (new teams not activating). Mar 2026: AI Platform dropped 3.1pp purely because new paid teams (paid_teams +12.1%) aren't activating AI at same rate as existing base.

______________________________________________________________________

## Org Plan (Custom Edition) Retention

Org Plan is identified by `TEAM_EDITION ILIKE '%custom%'` in `ANALYTICS_DATASCIENCE.DIM_TEAMS` — this is the canonical filter. Do NOT default to filtering by `ACCOUNT_SUBSEGMENT` when asked about Org Plan; account subsegment is a separate dimension. If a question specifically asks for MM-only Org Plan, then additionally filter via `DIM_SALESFORCE_APOLLO_TEAMS.ACCOUNT_SUBSEGMENT`.

```sql
WITH custom_teams AS (
    SELECT APOLLO_TEAM_ID, TEAM_EDITION, FIRST_PAID_DATE
    FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS
    WHERE TEAM_EDITION ILIKE '%custom%'
      AND FIRST_PAID_DATE < DATE_TRUNC('month', CURRENT_DATE)  -- first paid before this month
),
still_paying AS (
    SELECT DISTINCT ct.APOLLO_TEAM_ID
    FROM custom_teams ct
    JOIN ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE r
      ON r.APOLLO_TEAM_ID = ct.APOLLO_TEAM_ID
     AND r.DATE_PERIOD = DATEADD('day', -1, DATE_TRUNC('month', CURRENT_DATE))
     AND r.ARR > 0
)
SELECT
    COUNT(ct.APOLLO_TEAM_ID) AS total_custom_teams,
    COUNT(sp.APOLLO_TEAM_ID) AS still_paying_teams,
    COUNT(sp.APOLLO_TEAM_ID) / NULLIF(COUNT(ct.APOLLO_TEAM_ID), 0) AS retention_rate
FROM custom_teams ct
LEFT JOIN still_paying sp ON sp.APOLLO_TEAM_ID = ct.APOLLO_TEAM_ID;
```

**Mar 2026 baseline:** 6,773 custom teams → 5,447 retained = 80.4% (target: 60%).

______________________________________________________________________

## Support Tickets — Correct Filter

Raw `COUNT(*)` on `DIM_SUPPORT_CONVERSATIONS` returns 43K–69K/week (bot + email). Use `IS_CONVERSATION_SUPPORT_TEAM_HANDLED = true` for meaningful support volume (~3,100–3,850/week).

```sql
SELECT
    DATE_TRUNC('week', CONVERSATION_CREATED_AT::date) AS week_start,
    COUNT(CASE WHEN IS_CONVERSATION_SUPPORT_TEAM_HANDLED = true THEN 1 END) AS support_tickets,
    COUNT(*) AS all_conversations  -- includes bot/email, usually 43K-69K/week — do NOT use for "tickets"
FROM ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS
WHERE CONVERSATION_CREATED_AT >= DATEADD('week', -8, CURRENT_DATE)
GROUP BY 1
ORDER BY 1;
```

**Known anomaly (2026-03-02+):** `IS_CONVERSATION_TURNED_TICKET` spiked from ~3K/week to 34K–51K/week. Likely Intercom classification rule change. Do NOT use `IS_CONVERSATION_TURNED_TICKET` for trending — use `IS_CONVERSATION_SUPPORT_TEAM_HANDLED` instead. Also: `CONVERSATION_STATUS` is unreliably populated — do not use for resolution rate.

______________________________________________________________________

## Inbound ARR Attribution

**Two source tables serve different purposes:**

- `fct_mongo_daily_team_audit_reports` — daily `inbound_fee` (from `additional_fee_by_source:"inbound"::number`), billing fields, used to compute ARR time series
- `dim_mongo_teams_rt_vw` — current plan state, `product_infos` array flattened to identify which teams are on inbound plans (for SFDC opp matching)

**ARR formula:** `12 * SUM(inbound_fee / billing_interval_months)`

**Excluded test teams:** `68e6fb07946dcf000d2e3516` (Jerry test), `620210171b9d04008e2ac0e0` (Apollo eng fraud admin)

```sql
WITH r AS (
    SELECT
        date(date_time_string)                                AS dd,
        team_id,
        team_name,
        price_per_addon_lead_credit,
        price_per_addon_direct_dial_credit,
        price_per_addon_unified_credit,
        price_per_addon_export_credit,
        billing_interval_months,
        additional_fee_by_source,
        additional_fee_by_source:"inbound"::number            AS inbound_fee,
        additional_fee_by_source:"platform_fee"::number       AS platform_fee,
        unified_credits_limits_by_source:"addon_credits"::number  AS unified_add_on_credit,
        lead_credit_limits_by_source:"addon_credits"::number      AS lead_addon_credit,
        direct_dial_credit_limits_by_source:"addon_credits"::number AS dial_addon_credit,
        export_credit_limits_by_source:"addon_credits"::number    AS export_addon_credit_limit,
        unified_credits_limits_by_source:"addon_credits"::number * price_per_addon_unified_credit        AS unified_addon_credit_fee,
        lead_credit_limits_by_source:"addon_credits"::number     * price_per_addon_lead_credit           AS addon_leads_fee,
        direct_dial_credit_limits_by_source:"addon_credits"::number * price_per_addon_direct_dial_credit AS addon_dialer_fee,
        export_credit_limits_by_source:"addon_credits"::number   * price_per_addon_export_credit         AS addon_export_fee
    FROM analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports
    WHERE date_time_string >= '2025-11-12'
      AND inbound_fee > 0
      AND team_id != '68e6fb07946dcf000d2e3516'
      AND team_id != '620210171b9d04008e2ac0e0'
),

all_teams AS (
    SELECT
        sat.apollo_team_id,
        sat.created_date::date AS team_created_date,
        sat.website_domain,
        sat.team_name,
        sa.is_core_account,
        sat.team_edition
    FROM analytics_db.analytics.dim_salesforce_apollo_teams sat
    LEFT JOIN analytics_db.analytics.dim_salesforce_accounts sa
      ON sat.sfdc_account_id = sa.id
),

-- Flatten product_infos to find inbound plan start/end dates (for SFDC opp matching)
real_time_inbound_plans AS (
    SELECT
        mt._id                                AS apollo_team_id,
        at.team_created_date,
        at.is_core_account,
        at.website_domain,
        at.team_name,
        at.team_edition,
        pf.value:"plan_id"::string            AS plan_id,
        pf.value:"start_date"::date           AS start_date,
        pf.value:"end_date"::date             AS end_date,
        pf.value:"canceled_at"::date          AS canceled_at
    FROM analytics_db.analytics_dataplatform.dim_mongo_teams_rt_vw mt
    CROSS JOIN LATERAL FLATTEN(input => mt.product_infos) AS pf
    INNER JOIN all_teams at ON mt._id = at.apollo_team_id
    WHERE pf.value:"plan_id"::string ILIKE '%inbound%'
      AND mt._id != '68e6fb07946dcf000d2e3516'
      AND mt._id != '620210171b9d04008e2ac0e0'
),

-- Match to SFDC closed-won opps within ±1 day of plan start date
closed_won_opportunities AS (
    SELECT
        so.closed_won_at::date                AS closedate,
        so.type,
        so.arr_c,
        so.sales_motion_c,
        sat.apollo_team_id,
        ro.products_sold_c
    FROM analytics_db.analytics.dim_salesforce_opportunities so
    LEFT JOIN analytics_db.analytics.dim_salesforce_apollo_teams sat
      ON so.account_id = sat.sfdc_account_id
    LEFT JOIN raw_fivetran_db.salesforce.opportunity ro
      ON so.id = ro.id
    WHERE so.is_won = true AND so.is_closed = true AND sat.apollo_team_id IS NOT NULL
),

matched_opportunities AS (
    SELECT
        cwo.apollo_team_id,
        pp.start_date                         AS inbound_start_date,
        cwo.arr_c                             AS opportunity_arr,
        cwo.products_sold_c,
        CASE WHEN cwo.sales_motion_c = 'Self-Serve' THEN 'Self-Serve' ELSE 'Rep-Led' END AS sales_motion_label,
        CASE WHEN cwo.sales_motion_c != 'Self-Serve' OR cwo.sales_motion_c IS NULL THEN 1 ELSE 2 END AS rep_led_priority,
        CASE WHEN cwo.type = 'New Business' THEN 1
             WHEN cwo.type = 'Upsell'       THEN 2
             WHEN cwo.type = 'Renewal'      THEN 3
             ELSE 4 END                       AS type_priority
    FROM closed_won_opportunities cwo
    INNER JOIN real_time_inbound_plans pp
      ON cwo.apollo_team_id = pp.apollo_team_id
     AND ABS(DATEDIFF(day, cwo.closedate, pp.start_date)) <= 1
),

-- Persist first-ever sales_motion_label per team across all plans
first_sales_motion_per_team AS (
    SELECT apollo_team_id, sales_motion_label, products_sold_c,
           ROW_NUMBER() OVER (PARTITION BY apollo_team_id ORDER BY inbound_start_date ASC) AS rn
    FROM (
        SELECT apollo_team_id, inbound_start_date, sales_motion_label, products_sold_c,
               ROW_NUMBER() OVER (PARTITION BY apollo_team_id, inbound_start_date
                                  ORDER BY rep_led_priority, type_priority, opportunity_arr DESC) AS priority_rank
        FROM matched_opportunities
    ) WHERE priority_rank = 1
),

team_sales_motion AS (
    SELECT apollo_team_id, sales_motion_label, products_sold_c
    FROM first_sales_motion_per_team WHERE rn = 1
),

r_with_sales_motion AS (
    SELECT r.*, COALESCE(tsm.sales_motion_label, 'Self-Serve') AS sales_motion_label
    FROM r
    LEFT JOIN team_sales_motion tsm ON r.team_id = tsm.apollo_team_id
)

SELECT
    dd,
    IFF(LAST_DAY(dd, 'week') = dd, 1, 0)        AS is_last_day_of_week,
    sales_motion_label,
    COUNT(DISTINCT CASE WHEN inbound_fee > 0 THEN team_id END) AS active_inbound_teams,
    12 * SUM(inbound_fee / billing_interval_months)            AS annual_inbound_arr
FROM r_with_sales_motion
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

**Key design decisions (applies to both Inbound and Dialer):**

- Fee is a semi-structured JSON extract from `additional_fee_by_source` — only 3 keys exist: `inbound`, `dialer`, `platform_fee`
- Sales motion **persistence**: first-ever Rep-Led/Self-Serve label per team sticks to all future plans (not per-plan)
- SFDC match priority: Rep-Led > Self-Serve → New Business > Upsell > Renewal > Other → highest ARR
- Teams with no matched opp default to `Self-Serve`

______________________________________________________________________

## Dialer ARR Attribution

Same structure as Inbound ARR above. Two substitutions:

- Fee field: `additional_fee_by_source:"dialer"::number`
- Plan filter: `pf.value:"plan_id"::string ILIKE '%dialer%'`

```sql
WITH r AS (
    SELECT
        date(date_time_string)                                AS dd,
        team_id,
        team_name,
        billing_interval_months,
        additional_fee_by_source:"dialer"::number             AS dialer_fee,
        direct_dial_credit_limits_by_source:"addon_credits"::number * price_per_addon_direct_dial_credit AS addon_dialer_fee
    FROM analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports
    WHERE date_time_string >= '2025-11-12'
      AND additional_fee_by_source:"dialer"::number > 0
      AND team_id != '68e6fb07946dcf000d2e3516'
      AND team_id != '620210171b9d04008e2ac0e0'
),

all_teams AS (
    SELECT sat.apollo_team_id, sa.is_core_account, sat.team_edition
    FROM analytics_db.analytics.dim_salesforce_apollo_teams sat
    LEFT JOIN analytics_db.analytics.dim_salesforce_accounts sa ON sat.sfdc_account_id = sa.id
),

real_time_dialer_plans AS (
    SELECT
        mt._id                                AS apollo_team_id,
        pf.value:"plan_id"::string            AS plan_id,
        pf.value:"start_date"::date           AS start_date
    FROM analytics_db.analytics_dataplatform.dim_mongo_teams_rt_vw mt
    CROSS JOIN LATERAL FLATTEN(input => mt.product_infos) AS pf
    INNER JOIN all_teams at ON mt._id = at.apollo_team_id
    WHERE pf.value:"plan_id"::string ILIKE '%dialer%'
      AND mt._id != '68e6fb07946dcf000d2e3516'
      AND mt._id != '620210171b9d04008e2ac0e0'
),

closed_won_opportunities AS (
    SELECT so.closed_won_at::date AS closedate, so.type, so.arr_c, so.sales_motion_c, sat.apollo_team_id
    FROM analytics_db.analytics.dim_salesforce_opportunities so
    LEFT JOIN analytics_db.analytics.dim_salesforce_apollo_teams sat ON so.account_id = sat.sfdc_account_id
    WHERE so.is_won = true AND so.is_closed = true AND sat.apollo_team_id IS NOT NULL
),

matched_opportunities AS (
    SELECT
        cwo.apollo_team_id,
        pp.start_date                         AS dialer_start_date,
        CASE WHEN cwo.sales_motion_c = 'Self-Serve' THEN 'Self-Serve' ELSE 'Rep-Led' END AS sales_motion_label,
        CASE WHEN cwo.sales_motion_c != 'Self-Serve' OR cwo.sales_motion_c IS NULL THEN 1 ELSE 2 END AS rep_led_priority,
        CASE WHEN cwo.type = 'New Business' THEN 1 WHEN cwo.type = 'Upsell' THEN 2
             WHEN cwo.type = 'Renewal'      THEN 3 ELSE 4 END AS type_priority,
        cwo.arr_c                             AS opportunity_arr
    FROM closed_won_opportunities cwo
    INNER JOIN real_time_dialer_plans pp
      ON cwo.apollo_team_id = pp.apollo_team_id
     AND ABS(DATEDIFF(day, cwo.closedate, pp.start_date)) <= 1
),

team_sales_motion AS (
    SELECT apollo_team_id, sales_motion_label
    FROM (
        SELECT apollo_team_id, sales_motion_label,
               ROW_NUMBER() OVER (PARTITION BY apollo_team_id ORDER BY dialer_start_date ASC) AS rn
        FROM (
            SELECT apollo_team_id, dialer_start_date, sales_motion_label,
                   ROW_NUMBER() OVER (PARTITION BY apollo_team_id, dialer_start_date
                                      ORDER BY rep_led_priority, type_priority, opportunity_arr DESC) AS priority_rank
            FROM matched_opportunities
        ) WHERE priority_rank = 1
    ) WHERE rn = 1
),

r_with_sales_motion AS (
    SELECT r.*, COALESCE(tsm.sales_motion_label, 'Self-Serve') AS sales_motion_label
    FROM r LEFT JOIN team_sales_motion tsm ON r.team_id = tsm.apollo_team_id
)

SELECT
    dd,
    IFF(LAST_DAY(dd, 'week') = dd, 1, 0)       AS is_last_day_of_week,
    sales_motion_label,
    COUNT(DISTINCT team_id)                      AS active_dialer_teams,
    12 * SUM(dialer_fee / billing_interval_months) AS annual_dialer_arr
FROM r_with_sales_motion
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

______________________________________________________________________

## NNARR / Revenue Waterfall (RevOps)

**Two ARR cuts exist — do not mix them:**
| Cut | Source | Grain | Used by |
|-----|--------|-------|---------|
| RevOps | `FCT_MONTHLY_REVENUE` + `IS_PARENT_ACCOUNT = true` | Parent SF account | Finance, exec, board metrics, NNARR waterfall |
| Analytics | `FCT_DAILY_REVENUE` or `FCT_MONTHLY_REVENUE` (no parent filter) | Team | Cohort NRR, product analytics, feature attribution |

Numbers differ between the two cuts. When someone asks about ARR without context, default to RevOps cut (parent account). For cohort/segment/retention work, use the analytics cut.

**Source:** `FCT_MONTHLY_REVENUE` — not `FCT_DAILY_REVENUE`. Monthly grain, parent account level.

**4 ARR motions** tracked separately (each has a `PREVIOUS_DATE_PERIOD_*` counterpart):
| Column | Motion |
|--------|--------|
| `ARR_REP` | Rep-Led |
| `ARR_SS` | Self-Serve |
| `ARR_SA` | Sales-Assisted |
| `arr_labs` | Labs |

**CHANGE_CATEGORY values:** `new`, `new_reactivated`, `upgrade`, `downgrade`, `churn`, `reactivation`

**Standard joins + filters:**

```sql
FROM ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE AS r
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS AS sat
  ON r.SFDC_TEAM_OR_ACCOUNT_ID = sat.SFDC_TEAM_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS AS sa
  ON COALESCE(sat.SFDC_ACCOUNT_ID, r.SFDC_TEAM_OR_ACCOUNT_ID) = sa.ID
WHERE r.DATE_PERIOD >= <start>
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND r.IS_PARENT_ACCOUNT   -- parent account dedup (reliable in FCT_MONTHLY_REVENUE)
```

**New / Reactivation ARR** — simple delta:

```sql
-- New ARR (REP motion example)
SUM(CASE WHEN CHANGE_CATEGORY IN ('new', 'new_reactivated') AND IS_PARENT_ACCOUNT
    THEN ARR_REP - PREVIOUS_DATE_PERIOD_ARR_REP ELSE 0 END)

-- Reactivation ARR
SUM(CASE WHEN CHANGE_CATEGORY = 'reactivation' AND IS_PARENT_ACCOUNT
    THEN ARR_CHANGE ELSE 0 END)
```

**Upgrade ARR attribution** — motion-aware, falls back to `ARR_CHANGE` when only one motion is active:

```sql
-- Upgrade ARR attributed to REP motion:
CASE
  WHEN CHANGE_CATEGORY = 'upgrade' AND ARR_SS = 0 AND ARR_SA = 0 AND arr_labs = 0
    THEN ARR_CHANGE                                          -- only REP → use total change
  WHEN CHANGE_CATEGORY = 'upgrade' AND ARR_REP > 0 AND ARR_REP <> PREVIOUS_DATE_PERIOD_ARR_REP
    THEN ARR_REP - PREVIOUS_DATE_PERIOD_ARR_REP             -- REP changed
  WHEN CHANGE_CATEGORY = 'upgrade' AND ARR_REP = 0 AND ARR_SS > 0 AND ARR_SA > 0
    THEN ARR_REP - PREVIOUS_DATE_PERIOD_ARR_REP             -- mixed motion, REP portion
  ELSE 0
END
-- Same pattern repeated for SS, SA, Labs — substitute the relevant motion columns
```

**Churn / Downgrade:**

```sql
SUM(CASE WHEN CHANGE_CATEGORY = 'churn'     AND IS_PARENT_ACCOUNT THEN ARR_CHANGE ELSE 0 END)
SUM(CASE WHEN CHANGE_CATEGORY = 'downgrade' AND IS_PARENT_ACCOUNT THEN ARR_CHANGE ELSE 0 END)
```

**`IS_PARENT_ACCOUNT` — two different cuts of FCT_MONTHLY_REVENUE:**
| Filter | Use for |
|--------|---------|
| `IS_PARENT_ACCOUNT = true` | NNARR waterfall, exec ARR reporting — parent account rollup |
| `IS_PARENT_ACCOUNT = false` | New team ACV, logo counts — team-level, joined to `FCT_APOLLO_MONTHLY_SEAT_LIMITS` |

**New team ACV** = `SUM(ARR_CHANGE WHERE CHANGE_CATEGORY IN ('new','new_reactivated') AND IS_PARENT_ACCOUNT = false)` / `COUNT(DISTINCT APOLLO_TEAM_ID WHERE IS_PAID_ACTIVE AND CHANGE_CATEGORY = 'new')` from `FCT_APOLLO_MONTHLY_SEAT_LIMITS`.

**Key notes:**

- `IS_PARENT_ACCOUNT` in `FCT_MONTHLY_REVENUE` IS reliable as the account-level dedup (unlike `FCT_DAILY_REVENUE`)
- `IS_CORE_ACCOUNT` filter is a no-op — population controlled by `ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')`
- `arr_labs` is lowercase (unlike the uppercase convention for other ARR columns)

**Gotchas — Henry-logged:**

- **ARR vs ARR_CHANGE:** For upgrade/downgrade/reactivation deltas, ALWAYS use `ARR_CHANGE` (the incremental delta). `ARR` is the TOTAL ARR at that account — using it for expansion overstates by 3-4×. Only use `ARR` for new/churn categories where delta = full value.
- **Reactivation predecessor lookup:** Never `LAG()` over reactivation-only rows to find the prior churn event — LAG returns the *previous reactivation*, not the preceding churn. Correct pattern: separate `churn_rows` CTE joined to reactivation rows by `APOLLO_TEAM_ID WHERE churn_month < reactivation_month`.
- **Org Plan edition filter:** `ZP_OPPORTUNITY_EDITION_V_2_C` has 16+ variants (`custom_unified_v2/v3/v4`, `custom_EC_W/X/Y/Z`, etc.). Use `ILIKE '%custom%'`, never `= 'Custom'` — literal match misses 90% of Org Plan deals.

______________________________________________________________________

## Darwinbox (LU_DARWINBOX_POSITIONS)

**Lookup key:** Always search by `WORK_EMAIL`, never `FULL_NAME`. Darwinbox stores legal names (e.g., "Xuze Liu"), not display names ("Leo Liu"). FULL_NAME matches are unreliable and can return stale records from earlier months.

```sql
SELECT DESIGNATION, DEPARTMENT, FULL_NAME, DATE_OF_JOINING
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS
WHERE WORK_EMAIL = 'user@apollo.io'
QUALIFY ROW_NUMBER() OVER (ORDER BY EFFECTIVE_FROM DESC) = 1
```

______________________________________________________________________

## Weekly Signups by UTM Channel (Growth)

**Source:** `DIM_SALESFORCE_CONTACTS` — Growth tracks signups via SFDC contacts, not product events.

**Signup dedup key:** `COUNT(DISTINCT CASE WHEN ZP_USER_ID_C != '' THEN ZP_USER_ID_C END)` — empty string means no valid signup, not NULL.

**Week anchor:** Sunday-based — `DATEADD('day', (0 - EXTRACT(DOW FROM date)::integer), date)`. In Snowflake, `EXTRACT(DOW)` returns 0=Sunday, so this truncates to the most recent Sunday. **Consistent with product WAT/WAU canonical anchor.**

```sql
SELECT
    DATEADD('day', (0 - EXTRACT(DOW FROM sc.APOLLO_USER_CREATE_DATE_C)::integer),
            sc.APOLLO_USER_CREATE_DATE_C)::date       AS signup_week,
    sc.LAST_TOUCH_UTM_CHANNEL_GROUP                   AS channel,
    COUNT(DISTINCT CASE WHEN sc.ZP_USER_ID_C != ''
          THEN sc.ZP_USER_ID_C END)                   AS total_signups
FROM ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_CONTACTS sc
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa
  ON sc.ACCOUNT_ID = sa.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat
  ON sc.SFDC_TEAM_ID = sat.SFDC_TEAM_ID
WHERE sc.APOLLO_USER_CREATE_DATE_C >= DATEADD('day', -721, CURRENT_DATE)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1, 2
ORDER BY 1 DESC;
```

**Key notes:**

- `IS_CORE_ACCOUNT` filter in Growth Looker queries is a no-op — same pattern as RevOps
- This is SFDC contacts, not `DIM_MONGO_CONTACTS` (Apollo-native) or `DIM_USERS` (product)
- Channel is last-touch attribution at signup time

______________________________________________________________________

## Credit Consumption — Standard Exclusions

**Filter by `FEATURE_TYPE`, not `CREDIT_TYPE`.** `CREDIT_TYPE` has duplicate naming variants from two pipelines (snake_case + Title Case) and is unreliable as a filter. `FEATURE_TYPE` is canonical and stable.

Always apply these exclusions when querying `AGG_TEAM_CREDITS` for customer-facing credit metrics:

```sql
WHERE FEATURE_TYPE NOT IN (
    'ai_email',            -- AI Word Credits pool, not customer-billed
    'csv_export',          -- Free — credits consumed at enrichment time
    'crm_field_enrichment',-- Free
    'hubspot_push', 'salesforce_push', 'pipedrive_push',
    'zapier_push', 'salesloft_push', 'outreach_push',  -- Free CRM integrations
    'conversation'         -- Included feature, not billed
)
AND FEATURE_TYPE IS NOT NULL  -- NULL = ~342M admin/system rows, exclude
```

**Waterfall-specific filter:**

```sql
WHERE FEATURE_TYPE IN ('waterfall_enrichment', 'waterfall_mobile_enrichment', 'api_waterfall_enrichment')
```

See `data-catalog/context/AGG_TEAM_CREDITS.md` for the full verified FEATURE_TYPE taxonomy (30 values).

These exclusions are standard across all R&D dashboards and CBR credit metrics.

______________________________________________________________________

## Sales Funnel — New Business Pipeline (Stage 1 → Stage 2 CVR)

**Source:** `DIM_SALESFORCE_OPPORTUNITIES`

**Key concept:** Stage 1 count anchors on `CREATED_AT` (opp creation date). Stage 1 → Stage 2 CVR = `SQO count / total opps created`. Channel dimension: `LEAD_SOURCE_BUCKET`.

**Standard filters (always apply):**

- `TYPE = 'New Business'` — new logo opps only
- `owner.NAME <> 'Marketo Sync'` (allow NULL — Looker uses OR IS NULL)
- Standard segment + suspicious team filters
- `IS_CORE_ACCOUNT` is a **no-op** — Looker expression `(IS_CORE_ACCOUNT OR NOT IS_CORE_ACCOUNT)` always evaluates true; omit it

```sql
SELECT
    DATE_TRUNC('month', o.CREATED_AT)                    AS created_month,
    o.LEAD_SOURCE_BUCKET                                  AS channel,
    COUNT(DISTINCT o.ID)                                  AS total_opps,           -- Stage 1
    COUNT(DISTINCT CASE WHEN o.IS_SQO THEN o.ID END)     AS sqo_count,            -- Stage 2
    COUNT(DISTINCT CASE WHEN o.IS_WON  THEN o.ID END)    AS won_count,
    COALESCE(SUM(o.NEW_ARR), 0)                           AS total_new_arr,

    -- Stage 1 → Stage 2 CVR
    ROUND(COUNT(DISTINCT CASE WHEN o.IS_SQO THEN o.ID END)
          / NULLIF(COUNT(DISTINCT o.ID), 0) * 100, 1)    AS s1_to_s2_cvr_pct

FROM ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_OPPORTUNITIES o
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_USERS u
  ON o.OWNER_ID = u.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa
  ON o.ACCOUNT_ID = sa.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat
  ON o.APOLLO_TEAM_ID = sat.SFDC_TEAM_ID
WHERE o.TYPE = 'New Business'
  AND o.CREATED_AT >= DATEADD('day', -721, CURRENT_DATE)
  AND (u.NAME <> 'Marketo Sync' OR u.NAME IS NULL)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1, 2
ORDER BY 1 DESC;
```

**Stage mapping:**

| Stage | Column/Flag | Notes |
|-------|-------------|-------|
| Stage 1 — Created | `CREATED_AT` | Date anchor; all new business opps |
| Stage 2 — SQO | `IS_SQO = true` | Sales Qualified Opportunity |
| Stage 3 — Solution Evaluation | `STAGE_NAME = 'Solution Evaluation'` | |
| Stage 4 — Pricing Negotiation | `STAGE_NAME = 'Pricing Negotiation'` | |
| Stage 5 — Out for Signature | `STAGE_NAME = 'Out for Signature'` | |
| Stage 6 — Won | `IS_WON = true` | Closed-won |

**Key notes:**

- Date anchor is `CREATED_AT` — Looker Stage 1 standard. `DISCOVERY_STAGE_DATE` exists but is a stage-entry date field, not the standard Stage 1 anchor.
- `LEAD_SOURCE_BUCKET` is the channel dimension (not `TO_F_SALES_BUCKET`)
- `NEW_ARR` is a pre-computed ARR column on the opp (use over `ARR_C` for won deals)
- `IS_CORE_ACCOUNT` is a no-op — omit from direct SQL; only Looker includes it for historical reasons
- `IS_SQO` flag drives Stage 2; `SQO_DATE_C` available if you need SQO date as the anchor instead

______________________________________________________________________

## Closed Won ARR by Motion × Segment (Rep-Driven)

**Source:** `DIM_SALESFORCE_OPPORTUNITIES` anchored on `CLOSED_AT` + `IS_WON`.

**Segment:** Derived from `DIM_SALESFORCE_ACCOUNTS.ACCOUNT_SALES_DEPARTMENT_TIER` (not `ACCOUNT_SEGMENT`):

- Tier 1 / Tier 2 → `'MM'`
- Tier 3 / Tier 4 → `'SMB'`

**Metric:** `NEW_ANNUALIZED_DELTA_ARR` — annualized ARR delta vs prior period.

```sql
SELECT
    DATE_TRUNC('month', o.CLOSED_AT)               AS closed_month,
    o.TYPE                                          AS motion,
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
  AND (u.NAME   <> 'Marketo Sync'        OR u.NAME   IS NULL)
  AND (mgr.NAME <> 'Tania Garcia Chavez' OR mgr.NAME IS NULL)  -- excludes renewals/CS team
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1, 2, 3
ORDER BY 1 DESC;
```

**Key notes:**

- Use `ACCOUNT_SALES_DEPARTMENT_TIER` (not `ACCOUNT_SEGMENT`) for rep-driven segment — it maps to MM/SMB rep coverage tiers
- Manager exclusion (`Tania Garcia Chavez`) removes a renewals/CS manager; rep-driven view is AE/BDR only
- `IS_CORE_ACCOUNT` is a no-op — omit
- For Upsell ARR reporting, same query — just include `'Upsell'` in TYPE filter

______________________________________________________________________

## Email Deliverability — Weekly Trend by Channel

Canonical deliverability query. Source: `FCT_MONGO_EMAILER_MESSAGES` joined to `DIM_MONGO_EMAIL_ACCOUNTS`.

**Key design decisions:**

- `channel` split: `SendGrid/Mailgun` vs `Direct` — based on `ea.type_cd`
- Time anchor: `COMPLETED_AT` (not sent time)
- Week boundary: `<= CURRENT_DATE - DAYOFWEEK(CURRENT_DATE) + 1` — most recent Sunday (excludes partial current week)
- Exclusions: `status IN ('Completed','Failed')` only; team_id exclusions for internal/test teams
- Bounce split: `hard_bounced_for_email_algorithm` = hard; spam_blocked=0 + hard=0 = soft; spam_blocked=1 = spam
- Open rate: filtered (bot removed) vs unfiltered; tracked-only denominator variant for accuracy
- Click rate: `bot_clicked IS NULL OR bot_clicked = FALSE` for filtered version

```sql
USE WAREHOUSE ELT_WH_DP;

SELECT
    DATE_TRUNC('week', eml.completed_at)                        AS sent_week,
    CASE
        WHEN ea.type_cd IN ('sendgrid', 'mailgun') THEN 'SendGrid/Mailgun'
        ELSE 'Direct'
    END                                                          AS channel,

    -- Volume
    COUNT(DISTINCT eml.emailer_messages_id)                                                                                 AS message_count_sent,

    -- Bounce / spam
    COUNT(DISTINCT CASE WHEN eml.spam_blocked = 1 THEN eml.emailer_messages_id END)                                        AS message_count_spam_blocked,
    DIV0(COUNT(DISTINCT CASE WHEN eml.spam_blocked = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                           AS spam_block_rate,
    COUNT(DISTINCT CASE WHEN eml.bounced = 1 THEN eml.emailer_messages_id END)                                             AS message_count_bounced,
    DIV0(COUNT(DISTINCT CASE WHEN eml.bounced = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                           AS overall_bounce_rate,

    -- Delivery
    COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END)                                           AS message_count_delivered,

    -- Opens (filtered = bot removed, tracked = tracking-enabled only)
    COUNT(DISTINCT CASE WHEN eml.opened = 1 THEN eml.emailer_messages_id END)                                              AS message_count_opened,
    COUNT(DISTINCT CASE WHEN eml.opened = 1 OR eml.bot_opened = 1 THEN eml.emailer_messages_id END)                       AS message_count_opened_unfiltered,
    DIV0(COUNT(DISTINCT CASE WHEN eml.opened = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END))                                     AS filtered_open_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.opened = 1 OR eml.bot_opened = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END))                                     AS unfiltered_open_rate,
    COUNT(DISTINCT CASE WHEN eml.enable_tracking = 1 AND eml.delivered = 1 THEN eml.emailer_messages_id END)              AS message_count_tracked_delivered,
    DIV0(COUNT(DISTINCT CASE WHEN eml.opened = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.enable_tracking = 1 AND eml.delivered = 1 THEN eml.emailer_messages_id END))        AS filtered_open_rate_tracked,
    DIV0(COUNT(DISTINCT CASE WHEN eml.opened = 1 OR eml.bot_opened = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.enable_tracking = 1 AND eml.delivered = 1 THEN eml.emailer_messages_id END))        AS unfiltered_open_rate_tracked,

    -- Replies, unsubs, clicks
    COUNT(DISTINCT CASE WHEN eml.replied = 1 THEN eml.emailer_messages_id END)                                             AS message_count_replied,
    DIV0(COUNT(DISTINCT CASE WHEN eml.replied = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END))                                     AS reply_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.unsubscribed = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END))                                     AS unsubscribe_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.clicked = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 AND eml.open_tracking_enabled THEN eml.emailer_messages_id END))       AS unfiltered_click_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.clicked = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 AND eml.open_tracking_enabled
               AND (eml.bot_clicked IS NULL OR eml.bot_clicked = FALSE) THEN eml.emailer_messages_id END))                 AS filtered_click_rate

FROM analytics_db.analytics_dataplatform.fct_mongo_emailer_messages eml
LEFT JOIN analytics_db.analytics_dataplatform.dim_mongo_email_accounts ea
    ON ea.email_account_id = eml.email_account_id
WHERE eml.status IN ('Completed', 'Failed')
  AND DATE(eml.completed_at) >= DATEADD(month, -6, CURRENT_DATE())
  AND DATE(eml.completed_at) <= CURRENT_DATE - DAYOFWEEK(CURRENT_DATE) + 1  -- most recent Sunday
  AND eml.type IN ('outreach_automatic_email', 'outreach_manual_email')
  AND eml.team_id NOT IN (
      '551e3ef07261695147160000',   -- internal
      '5b33b1e1079cc732d656a677'    -- internal
  )
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

**For full 1-year trend**, change the date filter to:

```sql
AND DATE(eml.completed_at) >= DATE_TRUNC('WEEK', DATEADD(year, -1, CURRENT_DATE()))
```

______________________________________________________________________

## Feature Activation Rate — Cohort-based (Paid Teams, F7D)

Measures % of paid teams that use a given feature within their first N days after creation, broken down by team creation week. Only weeks with complete observation windows are included.

**Key design decisions:**

- **Team creation date** = `min(apollo_user_created_date)` from `DIM_USERS_DAILY` where `is_paid_ind = 1` — not team creation timestamp
- **Activation join** = left join to `user_inbound_actions_daily` (or swap for any other feature action table) within the observation window
- **Maturity guard** = `dateadd(day, 6 + 7, team_created_week) <= current_date` — ensures 7-day observation window + 1 week data lag before including a cohort
- **Warehouse** = `elt_wh_dp` (medium)

```sql
use warehouse elt_wh_dp;

with team_creation_dates as (
    select
        apollo_team_id
        , min(apollo_user_created_date) as apollo_team_created_date
    from "ANALYTICS_DB"."ANALYTICS_DATASCIENCE"."DIM_USERS_DAILY"
    where is_paid_ind = 1
        and apollo_team_id is not null
        and apollo_user_created_date between current_date - 195 and current_date - 8
    group by 1
),

first_7_days_activity as (
    select
        tcd.apollo_team_id
        , tcd.apollo_team_created_date
        , max(case when user_inbound_actions_daily.apollo_user_id is not null then true else false end) as is_activated

    from team_creation_dates tcd

    left join "ANALYTICS_DB"."ANALYTICS_DATASCIENCE"."DIM_USERS_DAILY" dim_users_daily
        on tcd.apollo_team_id = dim_users_daily.apollo_team_id
        and dim_users_daily.date between tcd.apollo_team_created_date and tcd.apollo_team_created_date + 6

    left join analytics_db.analytics_datascience.user_inbound_actions_daily
        on dim_users_daily.apollo_user_id = user_inbound_actions_daily.apollo_user_id
        and dim_users_daily.date = user_inbound_actions_daily.event_date
        and user_inbound_actions_daily.event_date between tcd.apollo_team_created_date and tcd.apollo_team_created_date + 6
        and dim_users_daily.is_paid_ind = 1

    group by 1, 2
)

select
    date_trunc(week, apollo_team_created_date) as team_created_week
    , count(apollo_team_id) as starting_cohort
    , count(case when is_activated = true then apollo_team_id end) / starting_cohort as conversion_rate

from first_7_days_activity

where team_created_week >= current_date - 180           -- trailing 6 months
    and dateadd(day, 6 + 7, team_created_week) <= current_date  -- complete observation window only

group by 1
order by 1;
```

**To change the feature:** swap `user_inbound_actions_daily` for any other action table in `ANALYTICS_DATASCIENCE` (e.g. `user_dialer_actions_daily`, `user_sequence_actions_daily`).

**To change the window (F14D, F28D):** change `+ 6` → `+ 13` or `+ 27`, and update the maturity guard `6 + 7` → `13 + 7` or `27 + 7`.

______________________________________________________________________

## W2 FTP Rate — Cohort Maturity Guard {#W2-FTP-Maturity}

**Why this is different from day-based maturity guards:** Snowflake `DATEDIFF('week', signup_date, payment_date)` counts *Sunday calendar boundaries crossed*, not elapsed days. A team that signed up on a Sunday needs the *next* Sunday (+7d) to cross 1 week boundary and the Sunday after that (+14d) to cross 2. This means the maturity requirement for W2 is not simply `signup_date + 14 <= today` — it depends on the day of the week of signup.

**The safe formula:** A cohort week (Monday-start) is fully mature for W2 analysis when its last day (Sunday = week_start + 6) has had 2 Sunday boundaries pass. That means:

```
last_day_of_cohort (Sunday) <= last_sunday - 14 days
⟹ week_start <= last_sunday - 20 days
⟹ DATE_TRUNC('week', week_start) <= DATE_TRUNC('week', DATEADD('day', -14, last_sunday))
```

**Canonical SQL filter — use this in every W2 FTP and W2 Trial CVR query:**

```sql
-- Drop immature cohorts (W2 window not yet closed for all teams in the week)
AND DATE_TRUNC('week', team_created_date) <=
    DATE_TRUNC('week',
        DATEADD('day', -14,
            DATEADD('day', -DAYOFWEEK(CURRENT_DATE()), CURRENT_DATE())
        )
    )
```

**Worked example (today = Mon Apr 20, 2026):**

- `DAYOFWEEK(Apr 20)` = 1 (Monday)
- Last Sunday = `DATEADD(-1, Apr 20)` = Apr 19
- `last_sunday - 14` = Apr 5
- `DATE_TRUNC('week', Apr 5)` = **Mar 30** ← last mature cohort week start
- Apr 6 cohort: last day = Apr 12 → DATEDIFF('week', Apr 12, Apr 20) = 1 → **immature, exclude**
- Mar 30 cohort: last day = Apr 5 → DATEDIFF('week', Apr 5, Apr 20) = 2 → **mature, include**

**Additional anomaly guardrail:** after applying the maturity filter, check if any included week's signup count is >1.5× the rolling 8-week average. Flag those weeks as unreliable (bot/spam spike, not caught by `is_suspicious_team = false`). Do not use anomalous weeks in OKR reporting.

______________________________________________________________________

## Inbound WAU/WAT — Daily Rolling 7-Day, by Action Type

Daily rolling WAU/WAT for all inbound actions, broken down by action type and paid/free. Canonical list of action types in `user_inbound_actions_daily`.

**Join pattern:** `dim_users_daily.date BETWEEN event_date AND event_date + 6` — for each calendar day, counts distinct users/teams active in the 7-day window ending that day (rolling WAU).

**Known action types in `user_inbound_actions_daily`:**

- `website_visitors_filter_applied_in_search` — visitor search filter used
- `website_visitors_tracking_filter_applied_in_company_search` — visitor tracking filter in company search
- `website_visitors_on_hover_viewed` — visitor hover card viewed
- `standalone_form_enriched` — standalone form enriched
- `inbound_router_form_enriched` — inbound router form enriched
- `inbound_router_published` — inbound router published
- `meeting_booked_for_a_guest_via_apollo_scheduler_inbound_router` — guest meeting booked via router
- `meeting_booked_for_a_host_via_apollo_scheduler_inbound_router` — host meeting booked via router

```sql
use warehouse elt_wh_dp;

select
    date
    , date_trunc(week, date) = date_trunc(week, current_date) as is_current_week
    , case when dim_users_daily.is_paid_ind = 1 then 'Paid'
           when dim_users_daily.is_paid_ind = 0 then 'Free'
           else null end as user_type
    -- overall inbound
    , count(distinct case when user_inbound_actions_daily.apollo_user_id is not null then dim_users_daily.apollo_user_id end) as overall_inbound_wau
    , count(distinct case when user_inbound_actions_daily.apollo_user_id is not null then dim_users_daily.apollo_team_id end) as overall_inbound_wat
    -- by action
    , count(distinct case when action = 'website_visitors_filter_applied_in_search' then dim_users_daily.apollo_user_id end) as website_visitors_filter_applied_in_search_wau
    , count(distinct case when action = 'website_visitors_filter_applied_in_search' then dim_users_daily.apollo_team_id end) as website_visitors_filter_applied_in_search_wat
    , count(distinct case when action = 'standalone_form_enriched' then dim_users_daily.apollo_user_id end) as standalone_form_enriched_wau
    , count(distinct case when action = 'standalone_form_enriched' then dim_users_daily.apollo_team_id end) as standalone_form_enriched_wat
    , count(distinct case when action = 'website_visitors_tracking_filter_applied_in_company_search' then dim_users_daily.apollo_user_id end) as website_visitors_tracking_filter_applied_in_company_search_wau
    , count(distinct case when action = 'website_visitors_tracking_filter_applied_in_company_search' then dim_users_daily.apollo_team_id end) as website_visitors_tracking_filter_applied_in_company_search_wat
    , count(distinct case when action = 'website_visitors_on_hover_viewed' then dim_users_daily.apollo_user_id end) as website_visitors_on_hover_viewed_wau
    , count(distinct case when action = 'website_visitors_on_hover_viewed' then dim_users_daily.apollo_team_id end) as website_visitors_on_hover_viewed_wat
    , count(distinct case when action = 'inbound_router_form_enriched' then dim_users_daily.apollo_user_id end) as inbound_router_form_enriched_wau
    , count(distinct case when action = 'inbound_router_form_enriched' then dim_users_daily.apollo_team_id end) as inbound_router_form_enriched_wat
    , count(distinct case when action = 'inbound_router_published' then dim_users_daily.apollo_user_id end) as inbound_router_published_wau
    , count(distinct case when action = 'inbound_router_published' then dim_users_daily.apollo_team_id end) as inbound_router_published_wat
    , count(distinct case when action = 'meeting_booked_for_a_guest_via_apollo_scheduler_inbound_router' then dim_users_daily.apollo_user_id end) as meeting_booked_guest_wau
    , count(distinct case when action = 'meeting_booked_for_a_guest_via_apollo_scheduler_inbound_router' then dim_users_daily.apollo_team_id end) as meeting_booked_guest_wat
    , count(distinct case when action = 'meeting_booked_for_a_host_via_apollo_scheduler_inbound_router' then dim_users_daily.apollo_user_id end) as meeting_booked_host_wau
    , count(distinct case when action = 'meeting_booked_for_a_host_via_apollo_scheduler_inbound_router' then dim_users_daily.apollo_team_id end) as meeting_booked_host_wat

from analytics_db.analytics_datascience.dim_users_daily

left join analytics_db.analytics_datascience.user_inbound_actions_daily
    on dim_users_daily.apollo_user_id = user_inbound_actions_daily.apollo_user_id
    and dim_users_daily.date between user_inbound_actions_daily.event_date and user_inbound_actions_daily.event_date + 6

where dim_users_daily.date >= current_date - 180  -- trailing 6 months
    -- and dim_users_daily.is_paid_ind = 1        -- uncomment to restrict to paid only

group by all;
```

______________________________________________________________________

## Inbound — Interest to Activation Rate (F7D, by User)

Measures F7D activation rate for users who expressed interest in inbound via in-app onboarding survey, by creation week and paid/free status.

**Key design decisions:**

- **Interest signal**: `has_in_app_onboarding_goal_inbound_solution = TRUE` on `DIM_USERS` — survey-expressed intent
- **Activation**: any action in `USER_INBOUND_ACTIONS_DAILY` within 7 days of user creation
- **Join on DIM_USERS** (not DIM_USERS_DAILY) — static user creation date, not a daily snapshot
- **Maturity guard**: `apollo_user_created_date <= CURRENT_DATE - 7` — full 7-day window must have elapsed

```sql
use warehouse elt_wh_dp;

with users_expressed_interest as (
    select
        date_trunc('week', apollo_user_created_date)  as apollo_user_created_week
        , t1.is_paid_ind
        , t1.apollo_user_id
        , max(case when t2.apollo_user_id is not null then true else false end) as is_activated
    from ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS t1
    left join ANALYTICS_DB.ANALYTICS_DATASCIENCE.USER_INBOUND_ACTIONS_DAILY t2
        on t1.apollo_user_id = t2.apollo_user_id
        and t2.event_date between t1.apollo_user_created_date
                              and (t1.apollo_user_created_date + 6)  -- 7-day window
    where t1.has_in_app_onboarding_goal_inbound_solution = true  -- expressed interest
        and t1.apollo_user_created_date <= current_date - 7       -- full window elapsed
        and t1.apollo_user_created_date >= current_date - 180     -- trailing 6 months
    group by all
)

select
    apollo_user_created_week
    , is_paid_ind
    , count(distinct apollo_user_id)                                                   as cohort_size
    , count(case when is_activated = true then apollo_user_id else null end)           as activated_user_count
    , count(case when is_activated = true then apollo_user_id else null end)
      / count(distinct apollo_user_id)                                                 as activation_rate
from users_expressed_interest
group by all;
```

**Note:** `has_in_app_onboarding_goal_inbound_solution` is on `DIM_USERS` (static snapshot), not `DIM_USERS_DAILY`. Use `DIM_USERS` here — joining daily would inflate the cohort.

______________________________________________________________________

## Inbound Churn Analysis — Feature Setup + Days Used

Analyzes which inbound features churned teams set up before churning, and how long they used the add-on. Requires upstream CTEs `sku_purchased` (teams that bought inbound) and `churned_teams` (with `max_date_active` = last active date before churn).

**Three setup signals tracked:**

1. `standalone_form_setup_event` — first `standalone_form_enriched` from `user_inbound_actions_daily`
1. `inbound_router_setup_event` — first `inbound_router_published` from `user_inbound_actions_daily`
1. `website_visitor_set_up_event` — first `Website Visitor Company Identified` from `FCT_AMPLITUDE_EVENTS` (reliable from 2025-11-06 only — data issues prior)

**Key metrics:**

- `days_used_inbound_add_on` = `datediff('day', inbound_start_date, max_date_active)` — how long from purchase to churn
- `website_visitor_inbound_set_up` = boolean — did the team actually set up visitor tracking?

```sql
website_visitor as (
    select
        apollo_team_id
        , min(event_date) as website_visitor_set_up_event
    from ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS
    where event_type = 'Website Visitor Company Identified'
        and event_date >= '2025-11-06'  -- data issues before this date
    group by all
),

adding_set_up_dates as (
    select
        t1.apollo_team_id
        , t1.team_name
        , t1.sales_motion_label
        , t1.inbound_start_date
        , min(case when action = 'standalone_form_enriched' then event_date else null end) as standalone_form_setup_event
        , min(case when action = 'inbound_router_published' then event_date else null end) as inbound_router_setup_event
        , t3.website_visitor_set_up_event
    from sku_purchased t1
    left join analytics_db.analytics_datascience.user_inbound_actions_daily t2
        on t1.apollo_team_id = t2.apollo_team_id
    left join website_visitor t3
        on t1.apollo_team_id = t3.apollo_team_id
    group by all
)

select
    t1.apollo_team_id
    , t1.team_name
    , t1.sales_motion_label
    , t1.inbound_start_date
    , t1.standalone_form_setup_event
    , t1.inbound_router_setup_event
    , t1.website_visitor_set_up_event
    , t2.max_date_active                                                        as inbound_churn_initiated_date
    , datediff('day', t1.inbound_start_date, t2.max_date_active)               as days_used_inbound_add_on
    , case when t1.website_visitor_set_up_event is not null then true else false end as website_visitor_inbound_set_up
from adding_set_up_dates t1
join churned_teams t2
    on t1.apollo_team_id = t2.apollo_team_id;
```

**Upstream CTEs needed (not shown — build from FCT_MONTHLY_REVENUE / DIM_SALESFORCE_APOLLO_TEAMS):**

- `sku_purchased` — teams that have an active inbound add-on; columns: `apollo_team_id`, `team_name`, `sales_motion_label`, `inbound_start_date`
- `churned_teams` — teams that have churned off inbound; columns: `apollo_team_id`, `max_date_active`

**Gotcha:** `FCT_AMPLITUDE_EVENTS.Website Visitor Company Identified` has data issues before 2025-11-06 — always filter `event_date >= '2025-11-06'` for this event type.

______________________________________________________________________

## ARR Lookup — Use DIM_TEAMS (Don't Over-Engineer)

For any question about current ARR — top customers, ARR for a specific account, sorting by revenue — go straight to `DIM_TEAMS`. Do NOT reach for `FCT_MONTHLY_REVENUE` with IS_PARENT_ACCOUNT joins and date filters for a simple lookup.

```sql
-- Top customers by ARR
SELECT TEAM_NAME, ACCOUNT_SEGMENT, ARR
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS
WHERE ARR > 0
ORDER BY ARR DESC
LIMIT 10;

-- ARR for a specific domain
SELECT TEAM_NAME, ACCOUNT_SEGMENT, ARR, WEBSITE_DOMAIN
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS
WHERE WEBSITE_DOMAIN = 'rippling.com'
  AND ARR > 0;
```

**When to use each:**

| Use case | Table |
|----------|-------|
| Top customers by ARR | **DIM_TEAMS** |
| Current ARR for an account | **DIM_TEAMS** |
| Revenue waterfall (new/churn/expansion) | FCT_MONTHLY_REVENUE |
| NRR / cohort retention analysis | FCT_MONTHLY_REVENUE |
| Parent account rollup (RevOps view) | FCT_MONTHLY_REVENUE + IS_PARENT_ACCOUNT=true |

______________________________________________________________________

## MCP User Cohort Analysis (verified 2026-03-24)

### Who counts as an MCP user

Use `DIM_USERS` (ANALYTICS_DATASCIENCE). Shyam added MCP-specific columns 2026-03-23:

- `FIRST_ACTIVE_DATE_MCP_API_CALLS` — first day user made an MCP API call
- `ACTIVE_DAYS_MCP_API_CALLS` — total days active via MCP
- `ACTIVE_COUNTS_MCP_API_CALLS` — total MCP API call count

MCP user = `FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL`. Do NOT use FCT_MONGO_HTTP_REQUESTS_V3_RT_VW for this — DIM_USERS is the preferred source for standard MCP analytics.

### Fixed observation window cohort (prevents cohort age bias)

```sql
-- MCP user analysis — 14-day fixed window
-- Cohort: signed up Feb 23 onward (MCP launch), restricted to users with ≥14 days tenure
WITH cohort AS (
    SELECT
        u.APOLLO_USER_ID,
        u.APOLLO_TEAM_ID,
        u.EMAIL,
        u.FIRST_NAME,
        u.LAST_NAME,
        u.JOB_TITLE,
        u.WEBSITE_DOMAIN,
        u.PRIMARY_PERSONA,
        t.ACCOUNT_SUB_SEGMENT,
        u.IS_PAID_IND,
        u.FIRST_PAID_DATE,
        u.APOLLO_USER_CREATED_DATE                                      AS signup_date,
        -- MCP flag: first MCP use within 14-day window
        CASE WHEN u.FIRST_ACTIVE_DATE_MCP_API_CALLS
                  <= u.APOLLO_USER_CREATED_DATE + 14 THEN 1 ELSE 0 END AS is_mcp_user,
        -- Activation flags within 14-day window
        CASE WHEN u.FIRST_ACTIVE_DATE_EMAIL
                  <= u.APOLLO_USER_CREATED_DATE + 14 THEN 1 ELSE 0 END AS activated_email_14d,
        CASE WHEN u.FIRST_ACTIVE_DATE_SEQUENCE
                  <= u.APOLLO_USER_CREATED_DATE + 14 THEN 1 ELSE 0 END AS activated_seq_14d
    FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS u
    LEFT JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t
        ON u.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
    WHERE u.IS_APOLLO_EMPLOYEE_IND = FALSE
      AND u.APOLLO_USER_CREATED_DATE >= '2026-02-23'        -- MCP launch date
      AND u.APOLLO_USER_CREATED_DATE <= CURRENT_DATE - 14   -- ≥14 days of observable history
)
SELECT
    is_mcp_user,
    ACCOUNT_SUB_SEGMENT,
    IS_PAID_IND,
    COUNT(DISTINCT APOLLO_USER_ID)                          AS n_users,
    AVG(activated_email_14d)                                AS email_activation_rate,
    AVG(activated_seq_14d)                                  AS seq_activation_rate
FROM cohort
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2, 3;
```

### Lookalike matching (stratified comparison)

Only compare MCP users to non-MCP peers from the same strata (signup_week × paid × segment). Prevents enterprise-vs-VSB comparisons from polluting lift calculations.

```sql
WITH strata_with_mcp AS (
    -- Find strata that contain at least one MCP user
    SELECT
        DATE_TRUNC('week', APOLLO_USER_CREATED_DATE) AS signup_week,
        IS_PAID_IND,
        t.ACCOUNT_SUB_SEGMENT,
        MAX(CASE WHEN u.FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL THEN 1 ELSE 0 END) AS has_mcp_user
    FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS u
    LEFT JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t ON u.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
    WHERE u.IS_APOLLO_EMPLOYEE_IND = FALSE
      AND u.APOLLO_USER_CREATED_DATE BETWEEN '2026-02-23' AND CURRENT_DATE - 14
    GROUP BY 1, 2, 3
    HAVING MAX(CASE WHEN u.FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL THEN 1 ELSE 0 END) = 1
)
-- Join back to cohort, filter to matched strata only
SELECT ...
FROM cohort c
JOIN strata_with_mcp s
    ON DATE_TRUNC('week', c.signup_date) = s.signup_week
    AND c.IS_PAID_IND = s.IS_PAID_IND
    AND c.ACCOUNT_SUB_SEGMENT = s.ACCOUNT_SUB_SEGMENT;
```

### MCP controller/action breakdown (raw request-level)

For understanding WHAT MCP users are doing (not just that they're using it), use FCT_MONGO_HTTP_REQUESTS_V3_RT_VW. Requires DEVELOPER_ROLE or higher.

```sql
-- MCP action breakdown by controller category
-- Schema: ANALYTICS_DB.ANALYTICS_DATAPLATFORM (NOT ANALYTICS)
SELECT
    r.CONTROLLER,
    r.ACTION,
    CASE
        WHEN r.CONTROLLER ILIKE '%people%' AND r.ACTION ILIKE '%search%' THEN 'Prospecting'
        WHEN r.CONTROLLER ILIKE '%people%' AND r.ACTION ILIKE '%match%'  THEN 'Person Enrichment'
        WHEN r.CONTROLLER ILIKE '%organizations%'                         THEN 'Org Enrichment'
        WHEN r.CONTROLLER ILIKE '%contacts%' OR r.CONTROLLER ILIKE '%accounts%' THEN 'CRM Management'
        WHEN r.CONTROLLER ILIKE '%emailer%'                               THEN 'Sequence'
        ELSE 'Other'
    END                                         AS category,
    COUNT(DISTINCT r.USER_ID)                   AS distinct_users,
    COUNT(DISTINCT r.TEAM_ID)                   AS distinct_teams,
    COUNT(*)                                    AS total_requests
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_HTTP_REQUESTS_V3_RT_VW r
WHERE r.USER_AGENT = 'Apollo-MCP/1.0'
  AND r.REQUEST_TIMESTAMP >= '2026-02-23'
GROUP BY 1, 2, 3
ORDER BY total_requests DESC
LIMIT 50;
```

**Key finding (Mar 2026 cohort):** Top MCP controllers by volume:

- `people/search` — Prospecting (781 web users, MCP heavily used)
- `contacts/create` — CRM write (MCP-dominant)
- `people/match` — Person Enrichment (MCP-dominant: 838 MCP vs 89 web users)
- `emailer_campaigns/add_contact_ids` — 111 MCP users added contacts to existing sequences (MCP CAN interact with sequences; just can't CREATE them)

### FTP (Free-to-Paid) rate for MCP users

```sql
SELECT
    is_mcp_user,
    t.ACCOUNT_SUB_SEGMENT,
    COUNT(DISTINCT u.APOLLO_USER_ID)                                    AS n_free_users,
    COUNT(DISTINCT CASE WHEN u.FIRST_PAID_DATE > u.APOLLO_USER_CREATED_DATE
                        THEN u.APOLLO_USER_ID END)                      AS converted,
    COUNT(DISTINCT CASE WHEN u.FIRST_PAID_DATE > u.APOLLO_USER_CREATED_DATE
                        THEN u.APOLLO_USER_ID END)
        / NULLIF(COUNT(DISTINCT u.APOLLO_USER_ID), 0)                   AS ftp_rate,
    MEDIAN(DATEDIFF('day', u.FIRST_ACTIVE_DATE_MCP_API_CALLS,
                           u.FIRST_PAID_DATE))                          AS median_days_mcp_to_paid
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS u
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t ON u.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
WHERE u.IS_APOLLO_EMPLOYEE_IND = FALSE
  AND u.IS_PAID_IND = FALSE     -- free at signup
  AND u.APOLLO_USER_CREATED_DATE >= '2026-02-23'
  AND u.APOLLO_USER_CREATED_DATE <= CURRENT_DATE - 14
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

______________________________________________________________________

## Rep-Driven (Sales) ARR — Recognized Revenue

**Use this for: "How much ARR did the sales team close last month?" or "What is rep-driven ARR?"**

Two different questions, two different tables:

| Question | Source | Filter |
|---|---|---|
| Recognized rep-driven ARR (finance/revenue) | `FCT_MONTHLY_REVENUE` | `IS_REP_DRIVEN = TRUE` |
| SFDC closed-won ARR by AE (pipeline/booking) | `DIM_SALESFORCE_OPPORTUNITIES` | `IS_WON = TRUE, TYPE IN ('New Business', 'Upsell')` |

**FCT_MONTHLY_REVENUE IS_REP_DRIVEN pattern (recognized revenue):**

```sql
SELECT
    DATE_PERIOD                                                     AS month,
    SUM(CASE WHEN CHANGE_CATEGORY IN ('new','new_reactivated')
             THEN ARR_REP END)                                      AS new_rep_arr,
    SUM(CASE WHEN CHANGE_CATEGORY = 'upgrade'
             THEN ARR_REP - PREVIOUS_DATE_PERIOD_ARR_REP END)       AS expansion_rep_arr,
    SUM(CASE WHEN CHANGE_CATEGORY IN ('new','new_reactivated','upgrade')
             THEN ARR_REP END)                                      AS total_new_and_expansion_rep_arr
FROM ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE
WHERE DATE_PERIOD = DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE))
  AND IS_PARENT_ACCOUNT = FALSE
  AND IS_REP_DRIVEN = TRUE
GROUP BY 1
ORDER BY 1 DESC;
```

**Key notes:**

- `IS_REP_DRIVEN` and `ARR_REP` are the columns for rep-driven ARR in both FCT_MONTHLY_REVENUE and FCT_DAILY_REVENUE
- `CHANGE_CATEGORY IN ('new','new_reactivated')` = new logos; `'upgrade'` = expansion
- Always separate new ARR from expansion — execs want to see both
- `ARR_REP` column = the subset of ARR attributed to rep motion; always use this not `ARR` when filtering IS_REP_DRIVEN
- This gives recognized revenue (what billing recorded); DIM_SALESFORCE_OPPORTUNITIES gives booking/pipeline ARR

______________________________________________________________________

## Total User and Team Counts (Org-wide)

**Use this for: "How many users/teams do we have?" — canonical source is DIM_MONGO.**

```sql
-- Total teams (all plans)
SELECT COUNT(DISTINCT _ID) AS total_teams
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TEAMS;

-- Total users (all plans)
SELECT COUNT(DISTINCT _ID) AS total_users
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_USERS;
```

| Metric | Table | Notes |
|---|---|---|
| Total teams (all plans) | `DIM_MONGO_TEAMS` | ~3.4M rows, authoritative Mongo source |
| Total users (all plans) | `DIM_MONGO_USERS` | ~4.3M rows, authoritative Mongo source |
| Paid teams | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY` | Filter `arr > 0` on latest date |
| Paid team user count | `ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES` | `user_count` column (static snapshot) |

**Key notes:**

- DIM_MONGO_TEAMS and DIM_MONGO_USERS are the canonical sources for **total org-wide counts** — do not use revenue tables for this
- Always clarify the as-of date when reporting totals
- Do NOT present paid-team user counts as "total users" — the org has ~4.3M total users across 3.4M teams

______________________________________________________________________

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created — segmentation default + WAT/WAU pattern | Leo |
| 2026-03-19 | Added NRR cohort methodology | Leo |
| 2026-03-20 | Added M3 Cohort NRR, Feature WAT %, Org Plan retention, support ticket filter, credit exclusions | Leo (verified via Snowflake) |
| 2026-03-20 | Added Inbound + Dialer ARR attribution — real query from CBR dashboard; dialer fee key confirmed via Snowflake sample | Leo |
| 2026-03-20 | Added Sales Funnel — New Business Pipeline (S1→S2 CVR); corrected to CREATED_AT anchor, LEAD_SOURCE_BUCKET channel | Leo |
| 2026-03-20 | Added Closed Won ARR by Motion × Segment; ACCOUNT_SALES_DEPARTMENT_TIER tier mapping, Tania Garcia Chavez manager exclusion | Leo |
| 2026-03-20 | Added Email Deliverability — Weekly Trend by Channel; canonical query with bounce/spam/open/reply/click rates, bot filtering, SendGrid vs Direct channel split | Leo |
| 2026-03-20 | Added Feature Activation Rate — Cohort-based (F7D); maturity guard pattern, team creation date via min(user_created), swap-friendly for any feature action table | Leo |
| 2026-03-20 | Added Inbound WAU/WAT by action type; rolling 7-day join pattern, canonical action type list for user_inbound_actions_daily | Leo |
| 2026-03-20 | Added Inbound Interest-to-Activation (F7D); DIM_USERS survey goal flag, user-level cohort | Leo |
| 2026-03-20 | Added Inbound Churn Analysis; feature setup dates, days used, FCT_AMPLITUDE_EVENTS data issue before 2025-11-06 | Leo |
| 2026-04-20 | Added W2 FTP Cohort Maturity Guard — canonical formula, worked example, anomaly guardrail note | Andrew |
| 2026-03-24 | Added MCP user cohort analysis — fixed window, lookalike matching, controller breakdown, FTP pattern | Leo |
| 2026-03-22 | Added ARR Lookup pattern — DIM_TEAMS for current ARR, not FCT_MONTHLY_REVENUE | Leo |
