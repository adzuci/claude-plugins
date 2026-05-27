-- LU_SAVED_METRICS — AE-owned canonical metric queries
-- Grain: one row per (metric_name, variant)
-- Purpose: Pre-validated SQL that the plug-in executes verbatim when an exec asks a metric question.
--          AEs write the SQL, set status to 'approved', and the plug-in picks it up immediately.
--          No plug-in redeploy needed — update a row, next conversation uses it.
-- Ownership: AE-owned definitions. DE owns the table infrastructure.
-- Refresh: manual (updated when metric definitions change)
--
-- STATUS values:
--   'approved'    — Vetted by metric owner. Plug-in will use this.
--   'draft'       — Work in progress. Plug-in will NOT use this (tells user it is not ready).
--   'deprecated'  — Replaced. Plug-in will NOT use this.
--
-- VARIANT: allows multiple cuts of the same metric (e.g., NRR by segment, NRR by cohort)

CREATE OR REPLACE TABLE ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS (
    metric_name             VARCHAR(200)    NOT NULL,
    variant                 VARCHAR(200)    NOT NULL DEFAULT 'default',
    description             VARCHAR(4000)   NOT NULL,
    metric_sql              VARCHAR(16000)  NOT NULL,
    grain                   VARCHAR(200),
    parameters              VARCHAR(2000),
    default_parameters      VARCHAR(2000),
    output_columns          VARCHAR(2000),
    related_terms           VARCHAR(1000),
    owner                   VARCHAR(200)    NOT NULL,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'draft',
    okr_target              VARCHAR(500),
    notes                   VARCHAR(4000),
    created_at              TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    updated_at              TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),

    PRIMARY KEY (metric_name, variant)
);

-- =============================================================================
-- Initial load: Draft metrics with known definitions
-- These are seeded as 'draft' — AE owners must review and set to 'approved'
-- =============================================================================

MERGE INTO ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS tgt
USING (
    SELECT column1 AS metric_name, column2 AS variant, column3 AS description,
           column4 AS metric_sql, column5 AS grain, column6 AS parameters,
           column7 AS default_parameters, column8 AS output_columns,
           column9 AS related_terms, column10 AS owner, column11 AS status,
           column12 AS okr_target, column13 AS notes
    FROM VALUES
    -- =========================================================================
    -- REVENUE METRICS — derivable from existing tables
    -- =========================================================================
    ('ARR by Segment', 'daily_snapshot',
     'Current ARR broken down by account segment. Point-in-time daily snapshot.',
     'SELECT
    r.ds,
    t.account_segment,
    COUNT(DISTINCT r.team_id)                                AS team_count,
    SUM(r.arr)                                               AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t
    ON r.team_id = t.team_id
WHERE r.ds = :ds
    AND r.arr > 0
GROUP BY r.ds, t.account_segment
ORDER BY total_arr DESC',
     'segment', 'ds DATE',
     'ds=CURRENT_DATE()-1', 'ds, account_segment, team_count, total_arr',
     'ARR, Account Segment', 'Analytics', 'approved',
     NULL, 'Requires LU_TEAM_ATTRIBUTES for segment. Filter arr > 0 for paid teams only.'),

    ('ARR by Segment', 'trend',
     'Daily ARR trend by account segment over a date range.',
     'SELECT
    r.ds,
    t.account_segment,
    COUNT(DISTINCT r.team_id)                                AS team_count,
    SUM(r.arr)                                               AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t
    ON r.team_id = t.team_id
WHERE r.ds BETWEEN :start_date AND :end_date
    AND r.arr > 0
GROUP BY r.ds, t.account_segment
ORDER BY r.ds, total_arr DESC',
     '(ds, segment)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-30,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'ds, account_segment, team_count, total_arr',
     'ARR, Account Segment', 'Analytics', 'approved',
     NULL, NULL),

    ('Team Count by Edition', 'daily_snapshot',
     'Count of teams by Apollo edition (plan tier) for a given date.',
     'SELECT
    r.ds,
    r.apollo_edition,
    COUNT(DISTINCT r.team_id)                                AS team_count,
    SUM(r.arr)                                               AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
WHERE r.ds = :ds
    AND r.arr > 0
GROUP BY r.ds, r.apollo_edition
ORDER BY total_arr DESC',
     'edition', 'ds DATE',
     'ds=CURRENT_DATE()-1', 'ds, apollo_edition, team_count, total_arr',
     'ARR, Pricing Variant', 'Analytics', 'approved',
     NULL, NULL),

    ('Support Volume', 'daily_trend',
     'Daily support conversation volume by type and AI participation.',
     'SELECT
    s.ds,
    s.conversation_type,
    s.ai_agent_participated,
    SUM(s.conversation_count)                                AS conversations,
    SUM(s.first_contact_resolution_count)                    AS fcr_count,
    AVG(s.avg_csat_rating)                                   AS avg_csat
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_SUPPORT_DAILY s
WHERE s.ds BETWEEN :start_date AND :end_date
GROUP BY s.ds, s.conversation_type, s.ai_agent_participated
ORDER BY s.ds',
     '(ds, type, ai_flag)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-30,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'ds, conversation_type, ai_agent_participated, conversations, fcr_count, avg_csat',
     'DCS', 'Analytics', 'approved',
     NULL, '24.5% team coverage — numbers represent Intercom-bridged conversations only.'),

    ('Email Activity', 'daily_trend',
     'Daily email send volume and engagement by message type. Excludes downloaded_email (bulk exports with no engagement tracking).',
     'SELECT
    e.ds,
    e.message_type,
    SUM(e.message_count)                                     AS messages_sent,
    SUM(e.opened_count)                                      AS opens,
    SUM(e.replied_count)                                     AS replies,
    SUM(e.bounced_count)                                     AS bounces,
    DIV0(SUM(e.opened_count), NULLIF(SUM(e.delivered_count), 0)) AS open_rate,
    DIV0(SUM(e.replied_count), NULLIF(SUM(e.delivered_count), 0)) AS reply_rate
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EMAILER_MESSAGES_DAILY e
WHERE e.ds BETWEEN :start_date AND :end_date
    AND e.message_type != ''downloaded_email''
GROUP BY e.ds, e.message_type
ORDER BY e.ds',
     '(ds, message_type)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-30,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'ds, message_type, messages_sent, opens, replies, bounces, open_rate, reply_rate',
     'GenPipe', 'Analytics', 'approved',
     NULL, 'Excludes downloaded_email (bulk exports). Legacy dbt FCT_APOLLO_EMAILER_MESSAGES_METRICS only counts sequence emails (outreach_automatic + outreach_manual).'),

    -- =========================================================================
    -- CREDIT METRICS — derivable from new credit tables
    -- =========================================================================
    ('Credit Utilization by Type', 'daily_snapshot',
     'Credit usage vs limits by credit type for a given date. Shows utilization rate per credit type across all teams.',
     'SELECT
    u.ds,
    u.credit_type,
    COUNT(DISTINCT u.team_id)                                AS teams_using,
    SUM(u.credits_used)                                      AS total_credits_used,
    SUM(l.credit_limit)                                      AS total_credit_limit,
    DIV0(SUM(u.credits_used), NULLIF(SUM(l.credit_limit), 0)) AS utilization_rate
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY u
LEFT JOIN ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_LIMITS_DAILY l
    ON u.team_id = l.team_id AND u.ds = l.ds AND u.credit_type = l.credit_type
WHERE u.ds = :ds
GROUP BY u.ds, u.credit_type
ORDER BY total_credits_used DESC',
     'credit_type', 'ds DATE',
     'ds=CURRENT_DATE()-1', 'ds, credit_type, teams_using, total_credits_used, total_credit_limit, utilization_rate',
     'Unified Credits, Feature Type, Credit Type', 'Analytics', 'approved',
     NULL, 'Uses Tier 2 credit tables (AGG_TEAM_CREDITS source). For team-level wide-format credit snapshot, use FCT_TEAM_CREDITS_DAILY instead.'),

    ('Credit Usage by Feature', 'daily_trend',
     'Daily credit consumption by feature type. Shows which product features are consuming credits over time.',
     'SELECT
    u.ds,
    u.credit_type,
    u.feature_type,
    COUNT(DISTINCT u.team_id)                                AS teams_using,
    SUM(u.credits_used)                                      AS total_credits_used
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY u
WHERE u.ds BETWEEN :start_date AND :end_date
GROUP BY u.ds, u.credit_type, u.feature_type
ORDER BY u.ds, total_credits_used DESC',
     '(ds, credit_type, feature_type)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-30,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'ds, credit_type, feature_type, teams_using, total_credits_used',
     'Unified Credits, Feature Type, Active Days', 'Analytics', 'approved',
     NULL, 'Uses Tier 2 credit tables (AGG_TEAM_CREDITS source).'),

    ('Phone Call Activity', 'daily_trend',
     'Daily phone call volume, connect rates, and duration by status.',
     'SELECT
    p.ds,
    p.status,
    SUM(p.call_count)                                        AS total_calls,
    SUM(p.user_count)                                        AS unique_callers,
    SUM(p.total_call_duration)                                AS total_duration_seconds,
    DIV0(SUM(CASE WHEN p.status = ''completed'' THEN p.call_count END),
         NULLIF(SUM(p.call_count), 0))                        AS connect_rate
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_PHONE_CALLS_DAILY p
WHERE p.ds BETWEEN :start_date AND :end_date
GROUP BY p.ds, p.status
ORDER BY p.ds',
     '(ds, status)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-30,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'ds, status, total_calls, unique_callers, total_duration_seconds, connect_rate',
     'Parallel Dial', 'Analytics', 'approved',
     NULL, 'Status is NULL for 55% of source rows — filter WHERE status IS NOT NULL for connect rate analysis.'),

    ('Enrichment Activity', 'daily_trend',
     'Daily enrichment volume by source (API, CSV, CRM, waterfall).',
     'SELECT
    e.ds,
    e.enrichment_source,
    COUNT(DISTINCT e.team_id)                                AS teams_enriching,
    SUM(e.request_count)                                  AS total_enrichments
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_ENRICHMENT_DAILY e
WHERE e.ds BETWEEN :start_date AND :end_date
GROUP BY e.ds, e.enrichment_source
ORDER BY e.ds',
     '(ds, enrichment_source)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-30,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'ds, enrichment_source, teams_enriching, total_requests',
     'Waterfall, Enrichment', 'Analytics', 'approved',
     NULL, 'Waterfall portion only in v1. Amplitude-sourced enrichment events not yet included.'),

    -- =========================================================================
    -- OKR METRICS — schema only, SQL needs AE definition
    -- =========================================================================
    ('M3 Cohort NRR', 'default',
     'Net Revenue Retention at Month 3 post-acquisition for monthly cohorts of core paid teams. Cohort = first active period in FCT_MONTHLY_REVENUE for IS_CORE_ACCOUNT teams. M3 = same teams 3 calendar months later.',
     'WITH cohort AS (
    SELECT r.APOLLO_TEAM_ID,
           r.FIRST_ACTIVE_DATE_PERIOD AS cohort_month,
           r.ARR                      AS arr_m0
    FROM ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE r
    JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t
        ON r.APOLLO_TEAM_ID = t.TEAM_ID
    WHERE r.IS_FIRST_DATE_PERIOD = TRUE
      AND t.IS_CORE_ACCOUNT = TRUE
      AND r.ARR > 0
      AND r.FIRST_ACTIVE_DATE_PERIOD BETWEEN :cohort_start_month AND :cohort_end_month
),
m3 AS (
    SELECT r.APOLLO_TEAM_ID,
           DATEADD(''month'', -3, r.DATE_PERIOD) AS cohort_month,
           r.ARR                                  AS arr_m3
    FROM ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE r
    WHERE r.IS_ACTIVE = TRUE
)
SELECT
    TO_VARCHAR(c.cohort_month, ''YYYY-MM'')                            AS cohort_month,
    COUNT(DISTINCT c.APOLLO_TEAM_ID)                                    AS cohort_teams,
    SUM(c.arr_m0)                                                       AS arr_m0,
    COUNT(DISTINCT m3.APOLLO_TEAM_ID)                                   AS retained_teams,
    COALESCE(SUM(m3.arr_m3), 0)                                        AS arr_m3,
    ROUND(DIV0(COALESCE(SUM(m3.arr_m3), 0), NULLIF(SUM(c.arr_m0), 0)) * 100, 1) AS m3_nrr_pct
FROM cohort c
LEFT JOIN m3
    ON c.APOLLO_TEAM_ID = m3.APOLLO_TEAM_ID
   AND c.cohort_month   = m3.cohort_month
WHERE DATEADD(''month'', 3, c.cohort_month) < CURRENT_DATE()
GROUP BY c.cohort_month
ORDER BY c.cohort_month',
     'cohort_month', 'cohort_start_month DATE, cohort_end_month DATE',
     'DATEADD(month,-12,DATE_TRUNC(month,CURRENT_DATE())), DATEADD(month,-3,DATE_TRUNC(month,CURRENT_DATE()))',
     'cohort_month, cohort_teams, arr_m0, retained_teams, arr_m3, m3_nrr_pct',
     'NRR, ARR, Change Category, Core Account', 'Analytics', 'draft',
     '82% -> 90%',
     'BEST-GUESS definition. Assumptions: cohort=IS_FIRST_DATE_PERIOD in FCT_MONTHLY_REVENUE, M3=+3 calendar months, core filter=LU_TEAM_ATTRIBUTES.IS_CORE_ACCOUNT. Produces 62-75% range vs stated 82% OKR baseline — gap likely due to IS_CORE_ACCOUNT being broader than OKR definition. Will Masket noted a current-to-future definition transition is in progress. Needs Rahul to validate.'),

    ('F14D Habit RA Rate', 'default',
     'First-14-day Habit Record Actioned rate. Percent of Golden Population (SMB+) teams that perform 4+ Record Actions within 14 days of signup.',
     '-- TODO: AE (Adhiraj / O&A) must define canonical SQL
-- Required logic:
--   1. Identify new teams: team_created_at within reporting period (from LU_TEAM_ATTRIBUTES)
--   2. Filter to Golden Population (SMB+ in AMER/EMEA, non-freemail)
--   3. Count record_actioned events per team in first 14 days (from FCT_TEAM_ACTIVITY_DAILY)
--   4. Rate = teams with >= 4 RAs / total qualifying teams
-- Open questions for AE:
--   - Exact event_type_ids that constitute a "Record Action"?
--   - Does Golden Population filter use account_segment or market_segment_tier?
--   - Include teams that churn within 14 days?
SELECT 1 AS placeholder',
     'signup_cohort', 'start_date DATE, end_date DATE',
     NULL, 'signup_week, qualifying_teams, activated_teams, f14d_rate_pct',
     'F14D Habit RA Rate, Golden Population, Record Action', 'O&A (Adhiraj)', 'draft',
     '12.2% -> 17%', 'BLOCKED: Needs O&A-defined Record Action event list and Golden Population filter.'),

    ('Inbound Revenue Attribution', 'default',
     'Revenue attributed to inbound marketing channels. OKR: $4M of $10M target.',
     '-- TODO: Marketing Analytics must define attribution model
-- Required logic:
--   1. Identify inbound opportunities (TOF_SALES_BUCKET or similar)
--   2. Link to closed-won revenue
--   3. Attribution model: first-touch? multi-touch? time-decay?
-- Open questions:
--   - Which TOF_SALES_BUCKET values count as "inbound"?
--   - Attribution to opportunity or account level?
--   - Include partner/referral channels?
SELECT 1 AS placeholder',
     'month', 'start_date DATE, end_date DATE',
     NULL, 'month, channel, attributed_arr, opportunity_count',
     'Inbound Revenue Attribution, SQO, TOF Sales Bucket', 'Marketing Analytics', 'draft',
     '$4M / $10M', 'BLOCKED: Needs Marketing Analytics attribution model definition.'),

    -- =========================================================================
    -- METRICS FROM #ask-henry QUESTION BANK (added 2026-03-19)
    -- =========================================================================
    ('Teams by Billing Term', 'daily_snapshot',
     'Count of paid teams and ARR split by billing term (monthly, annually, quarterly, semi-annually). Point-in-time snapshot.',
     'SELECT
    r.ds,
    r.payment_term,
    COUNT(DISTINCT r.team_id)  AS team_count,
    SUM(r.arr)                 AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
WHERE r.ds = :ds
    AND r.arr > 0
GROUP BY r.ds, r.payment_term
ORDER BY total_arr DESC',
     'payment_term', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'ds, payment_term, team_count, total_arr',
     'Monthly Plan, Annual Plan, Payment Term', 'Analytics', 'approved',
     NULL, 'Sourced from FCT_TEAM_REVENUE_DAILY.PAYMENT_TERM. Verified values: monthly, annually, quarterly, semi-annually.'),

    ('ARR by Geography', 'daily_snapshot',
     'ARR and paid team count by billing country and account region. Useful for US vs non-US split and regional breakdowns.',
     'SELECT
    r.ds,
    t.account_region,
    t.billing_country,
    COUNT(DISTINCT r.team_id)  AS team_count,
    SUM(r.arr)                 AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t
    ON r.team_id = t.team_id
WHERE r.ds = :ds
    AND r.arr > 0
GROUP BY r.ds, t.account_region, t.billing_country
ORDER BY total_arr DESC',
     '(region, country)', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'ds, account_region, billing_country, team_count, total_arr',
     'ARR, Geography, US vs Non-US, AMER, EMEA, APAC', 'Analytics', 'approved',
     NULL, 'Use account_region for high-level (AMER/EMEA/APAC) or billing_country for country-level. Joins LU_TEAM_ATTRIBUTES which sources from DIM_SALESFORCE_ACCOUNTS.'),

    ('ARR by Industry', 'daily_snapshot',
     'ARR and paid team count by industry vertical. Sourced from Salesforce account industry field via LU_TEAM_ATTRIBUTES.',
     'SELECT
    r.ds,
    COALESCE(t.industry, ''Unknown'') AS industry,
    COUNT(DISTINCT r.team_id)         AS team_count,
    SUM(r.arr)                        AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t
    ON r.team_id = t.team_id
WHERE r.ds = :ds
    AND r.arr > 0
GROUP BY r.ds, t.industry
ORDER BY total_arr DESC',
     'industry', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'ds, industry, team_count, total_arr',
     'ARR, Industry', 'Analytics', 'approved',
     NULL, 'Industry sourced from DIM_SALESFORCE_ACCOUNTS via LU_TEAM_ATTRIBUTES. Teams without SFDC account show as Unknown.'),

    ('New Paid Teams by Month', 'trend',
     'Count of new paid teams per month — teams whose first paid date falls in that month. Uses FCT_DAILY_REVENUE (full history) with IS_PARENT_ACCOUNT filter.',
     'SELECT
    DATE_TRUNC(''month'', first_paid.first_paid_ds)          AS cohort_month,
    COUNT(DISTINCT first_paid.team_id)                       AS new_paid_teams
FROM (
    SELECT APOLLO_TEAM_ID AS team_id, MIN(DATE_PERIOD) AS first_paid_ds
    FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE
    WHERE ARR > 0
      AND IS_PARENT_ACCOUNT = false
    GROUP BY APOLLO_TEAM_ID
) first_paid
WHERE first_paid.first_paid_ds BETWEEN :start_date AND :end_date
GROUP BY cohort_month
ORDER BY cohort_month',
     'cohort_month', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(month,-6,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'cohort_month, new_paid_teams',
     'New Paid Teams, First Paid Date, Cohort', 'Analytics', 'approved',
     NULL, 'Uses FCT_DAILY_REVENUE (full history back to 2022) with IS_PARENT_ACCOUNT=false. Preferred over FCT_TEAM_REVENUE_DAILY for this metric since PLAYGROUND only starts Sep 2025.'),

    -- =========================================================================
    -- REVENUE SNAPSHOT — safe template for ad-hoc ARR questions
    -- =========================================================================
    ('Total ARR Snapshot', 'daily_snapshot',
     'Total paid team count and ARR as of a given date. Uses FCT_DAILY_REVENUE with parent-account filter for full date history.',
     'SELECT
    COUNT(DISTINCT f.APOLLO_TEAM_ID)                         AS paid_teams,
    ROUND(SUM(f.ARR) / 1e6, 2)                              AS total_arr_m,
    ROUND(AVG(f.ARR), 0)                                    AS avg_arr_per_team,
    ROUND(MEDIAN(f.ARR), 0)                                 AS median_arr_per_team
FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE f
WHERE f.DATE_PERIOD = :ds
    AND f.ARR > 0
    AND f.IS_PARENT_ACCOUNT = false',
     'snapshot', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'paid_teams, total_arr_m, avg_arr_per_team, median_arr_per_team',
     'ARR, Paid Teams, Revenue', 'Analytics', 'approved',
     NULL, 'CRITICAL: IS_PARENT_ACCOUNT=false prevents 2x ARR doubling. Without filter total reads ~$332M instead of correct ~$166M. Use this for any date; for Sep 2025+ can also use FCT_TEAM_REVENUE_DAILY.'),

    ('Revenue by Self-Serve vs Rep-Driven', 'daily_snapshot',
     'ARR split between self-serve and rep-driven teams. Uses FCT_DAILY_REVENUE with parent-account filter. Note: flags can overlap (some teams are both).',
     'SELECT
    CASE WHEN f.IS_SELF_SERVE = true AND f.IS_REP_DRIVEN = false THEN ''Pure Self-Serve''
         WHEN f.IS_REP_DRIVEN = true AND f.IS_SELF_SERVE = false THEN ''Pure Rep-Driven''
         WHEN f.IS_SELF_SERVE = true AND f.IS_REP_DRIVEN = true THEN ''Both''
         ELSE ''Neither'' END                                AS channel,
    COUNT(DISTINCT f.APOLLO_TEAM_ID)                         AS paid_teams,
    ROUND(SUM(f.ARR) / 1e6, 2)                              AS total_arr_m,
    ROUND(SUM(f.ARR) * 100.0 / NULLIF(SUM(SUM(f.ARR)) OVER (), 0), 1) AS pct_of_total
FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE f
WHERE f.DATE_PERIOD = :ds
    AND f.ARR > 0
    AND f.IS_PARENT_ACCOUNT = false
GROUP BY channel
ORDER BY total_arr_m DESC',
     'channel', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'channel, paid_teams, total_arr_m, pct_of_total',
     'Self-Serve, Rep-Driven, ARR', 'Analytics', 'approved',
     NULL, 'IS_SELF_SERVE and IS_REP_DRIVEN flags overlap for some teams. Use this instead of computing from separate flag sums. IS_PARENT_ACCOUNT=false applied.'),

    ('ARR by Segment Trend', 'monthly_share',
     'Monthly ARR by segment as % of total — for "are we moving upmarket?" questions. Shows share of ARR, not absolute growth.',
     'SELECT
    DATE_TRUNC(''month'', f.DATE_PERIOD)                     AS snap_month,
    t.account_segment,
    COUNT(DISTINCT f.APOLLO_TEAM_ID)                         AS team_count,
    ROUND(SUM(f.ARR) / 1e6, 2)                              AS arr_m,
    ROUND(SUM(f.ARR) * 100.0 / NULLIF(SUM(SUM(f.ARR)) OVER (PARTITION BY DATE_TRUNC(''month'', f.DATE_PERIOD)), 0), 1) AS pct_of_arr
FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE f
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t
    ON f.APOLLO_TEAM_ID = t.TEAM_ID
WHERE f.DATE_PERIOD IN (
    SELECT MAX(DATE_PERIOD) FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE
    WHERE IS_PARENT_ACCOUNT = false AND ARR > 0
    GROUP BY DATE_TRUNC(''month'', DATE_PERIOD)
    HAVING DATE_TRUNC(''month'', MAX(DATE_PERIOD)) BETWEEN :start_month AND :end_month
)
    AND f.ARR > 0
    AND f.IS_PARENT_ACCOUNT = false
GROUP BY snap_month, t.account_segment
ORDER BY snap_month, arr_m DESC',
     '(month, segment)', 'start_month DATE, end_month DATE',
     'start_month=DATEADD(month,-12,DATE_TRUNC(month,CURRENT_DATE())), end_month=CURRENT_DATE()-1',
     'snap_month, account_segment, team_count, arr_m, pct_of_arr',
     'ARR, Segment, Upmarket, Mix', 'Analytics', 'approved',
     NULL, 'For "moving upmarket" questions — shows pct_of_arr (share) not just absolute ARR. Enterprise+MM share growing from ~31% to ~34% = modest upmarket signal. IS_PARENT_ACCOUNT=false applied.'),

    -- =========================================================================
    -- PRODUCT USAGE / FEATURE WAT METRICS (DIM_TEAMS_DAILY)
    -- Addresses Henry Q20, Q22, Q23, Q25, Q26, Q27, Q29, Q35
    -- =========================================================================
    ('Feature WAT Snapshot', 'daily_snapshot',
     'Paid team counts by feature activity in last 7 days. Shows how many paid teams use each feature. Source: DIM_TEAMS_DAILY.',
     'SELECT
    SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END) AS paid_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS active_l7,
    SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_SEQUENCE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS sequence_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND EMAIL_SENT_USER_COUNTS_OUTREACH_AUTOMATIC_L7 > 0 THEN 1 ELSE 0 END) AS auto_email_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_DIALER_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS dialer_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_WORKFLOW_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS workflow_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_RECORD_ACTIONED_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS record_actioned_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND EXTENSION_USED_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS extension_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS win_close_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND USE_CASE_ENRICHMENT_ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS enrichment_teams
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE = :ds',
     'feature', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'paid_teams, active_l7, sequence_teams, auto_email_teams, dialer_teams, workflow_teams, record_actioned_teams, extension_teams, win_close_teams, enrichment_teams',
     'WAT, Feature, Extension, Workflow, Sequence, Dialer, Record Actioned, Win Close', 'Analytics', 'approved',
     NULL, 'Uses DIM_TEAMS_DAILY (ANALYTICS_DATASCIENCE). L7 user counts > 0 = feature active. Paid denominator = IS_PAID_IND. This table has 8.6B rows — query targets a single date.'),

    ('Feature WAT Trend', 'weekly',
     'Weekly trend of feature WAT percentages across paid teams. Shows feature adoption rates over time. Source: DIM_TEAMS_DAILY.',
     'SELECT
    DATE_TRUNC(''week'', DATE)                                                     AS week_start,
    SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END)                           AS paid_teams,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_SEQUENCE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS sequence_pct,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND EMAIL_SENT_USER_COUNTS_OUTREACH_AUTOMATIC_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS auto_email_pct,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_DIALER_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS dialer_pct,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_WORKFLOW_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS workflow_pct,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_RECORD_ACTIONED_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS record_actioned_pct,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND EXTENSION_USED_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS extension_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE BETWEEN :start_date AND :end_date
    AND DAYOFWEEK(DATE) = 1
GROUP BY week_start
ORDER BY week_start',
     '(week)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-90,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'week_start, paid_teams, sequence_pct, auto_email_pct, dialer_pct, workflow_pct, record_actioned_pct, extension_pct',
     'WAT, Feature Trend, WoW', 'Analytics', 'approved',
     NULL, 'Samples Mondays (DAYOFWEEK=1) for weekly snapshots from DIM_TEAMS_DAILY. Uses L7 user counts > 0 as feature-active definition.'),

    ('Extension-Only Paid Teams', 'daily_snapshot',
     'Paid teams that use ONLY the Chrome extension — no other product features (no genpipe, no enrichment, no CRM, no win-close). Answers "how many paid teams are extension-only?"',
     'SELECT
    SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END) AS total_paid_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND EXTENSION_USED_USER_COUNTS_L7 > 0
        AND COALESCE(GENPIPE_FEATURES_USER_COUNTS_L7, 0) = 0
        AND COALESCE(USE_CASE_ENRICHMENT_ACTIVE_USER_COUNTS_L7, 0) = 0
        AND COALESCE(CRM_RECORD_MANAGEMENT_USER_COUNTS_L7, 0) = 0
        AND COALESCE(USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7, 0) = 0
        THEN 1 ELSE 0 END) AS ext_only_teams,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND EXTENSION_USED_USER_COUNTS_L7 > 0
        AND COALESCE(GENPIPE_FEATURES_USER_COUNTS_L7, 0) = 0
        AND COALESCE(USE_CASE_ENRICHMENT_ACTIVE_USER_COUNTS_L7, 0) = 0
        AND COALESCE(CRM_RECORD_MANAGEMENT_USER_COUNTS_L7, 0) = 0
        AND COALESCE(USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7, 0) = 0
        THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1) AS pct_ext_only,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND EXTENSION_USED_USER_COUNTS_L7 > 0
        AND COALESCE(GENPIPE_FEATURES_USER_COUNTS_L7, 0) = 0
        AND COALESCE(USE_CASE_ENRICHMENT_ACTIVE_USER_COUNTS_L7, 0) = 0
        AND COALESCE(CRM_RECORD_MANAGEMENT_USER_COUNTS_L7, 0) = 0
        AND COALESCE(USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7, 0) = 0
        THEN ARR ELSE 0 END) / 1e6, 2) AS ext_only_arr_m
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE = :ds',
     'snapshot', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'total_paid_teams, ext_only_teams, pct_ext_only, ext_only_arr_m',
     'Extension Only, Chrome Extension', 'Analytics', 'approved',
     NULL, 'Strict extension-only: has extension L7 but zero GENPIPE_FEATURES, enrichment, CRM, and win-close. PDF ground truth: ~2,404 teams (2.3%). Our definition yields ~4K teams (~4%) on recent dates — close but not exact match due to slightly different column exclusion lists.'),

    ('Free-to-Paid Conversion Rate', 'monthly_trend',
     'Monthly free-to-paid conversion rate — what % of new teams convert to paid within 3 months. Cohort anchored on TEAM_CREATED_DATE from DIM_TEAMS.',
     'SELECT
    DATE_TRUNC(''month'', t.TEAM_CREATED_DATE)                AS first_seen_month,
    COUNT(DISTINCT t.APOLLO_TEAM_ID)                           AS total_teams,
    SUM(CASE WHEN t.FIRST_PAID_DATE IS NOT NULL
             AND t.FIRST_PAID_DATE <= DATEADD(''month'', 3, t.TEAM_CREATED_DATE)
             THEN 1 ELSE 0 END)                                AS converted_3mo,
    ROUND(SUM(CASE WHEN t.FIRST_PAID_DATE IS NOT NULL
             AND t.FIRST_PAID_DATE <= DATEADD(''month'', 3, t.TEAM_CREATED_DATE)
             THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(DISTINCT t.APOLLO_TEAM_ID), 0), 1)     AS conversion_rate_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t
WHERE t.TEAM_CREATED_DATE BETWEEN :start_date AND :end_date
GROUP BY first_seen_month
ORDER BY first_seen_month',
     'cohort_month', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(month,-12,CURRENT_DATE()), end_date=DATEADD(month,-3,CURRENT_DATE())',
     'first_seen_month, total_teams, converted_3mo, conversion_rate_pct',
     'Conversion, Free-to-Paid, Cohort', 'Analytics', 'approved',
     NULL, 'Conversion window = 3 months from TEAM_CREATED_DATE. Cohort anchored on team creation (not first activation) so all signups are included. End date defaults to 3 months ago to allow full conversion window. Uses DIM_TEAMS directly — no dedup needed. Updated 2026-03-25: switched from FIRST_TEAM_ACTIVE_DATE/DIM_TEAMS_DAILY to TEAM_CREATED_DATE/DIM_TEAMS after finding ~35-58k teams/week were excluded by the activation filter.'),

    ('Enterprise Paid Team Activity', 'daily_snapshot',
     'What % of Enterprise (paid_seat_limit > 20) paid teams are active in L7/L28. Answers "are our big accounts actually using the product?"',
     'SELECT
    COUNT(*) AS enterprise_paid_teams,
    SUM(CASE WHEN ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS active_l7,
    ROUND(SUM(CASE WHEN ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_active_l7,
    SUM(CASE WHEN ACTIVE_USER_COUNTS_L28 > 0 THEN 1 ELSE 0 END) AS active_l28,
    ROUND(SUM(CASE WHEN ACTIVE_USER_COUNTS_L28 > 0 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_active_l28
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE = :ds
    AND IS_PAID_IND = true
    AND PAID_SEAT_LIMIT > 20',
     'snapshot', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'enterprise_paid_teams, active_l7, pct_active_l7, active_l28, pct_active_l28',
     'Enterprise, Activity, Seat Limit', 'Analytics', 'approved',
     NULL, 'Enterprise defined as PAID_SEAT_LIMIT > 20 per PDF ground truth (Q35). PDF shows ~460 teams, 98.5% active L7.'),

    ('Win and Close WAT Trend', 'weekly',
     'Weekly trend of Win and Close use case active teams. Answers "what is Win and Close WAU?"',
     'SELECT
    DATE_TRUNC(''week'', DATE)                                                     AS week_start,
    SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END)                           AS paid_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS win_close_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7 > 0 THEN COALESCE(USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7, 0) ELSE 0 END) AS win_close_users,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS win_close_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE BETWEEN :start_date AND :end_date
    AND DAYOFWEEK(DATE) = 1
GROUP BY week_start
ORDER BY week_start',
     '(week)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-90,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'week_start, paid_teams, win_close_teams, win_close_users, win_close_pct',
     'Win Close, WAT, Trend', 'Analytics', 'approved',
     NULL, 'Uses USE_CASE_WIN_CLOSE_ACTIVE_USER_COUNTS_L7 from DIM_TEAMS_DAILY. PDF shows ~8-9% of paid teams. Samples Mondays for weekly snapshots.'),

    ('Sequence Participation Trend', 'weekly',
     'Weekly trend of sequence participation rate for paid teams. Answers "how is sequence participation trending?"',
     'SELECT
    DATE_TRUNC(''week'', DATE)                                                     AS week_start,
    SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END)                           AS paid_teams,
    SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_SEQUENCE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) AS sequence_teams,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true AND GENPIPE_FEATURE_SEQUENCE_USER_COUNTS_L7 > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END), 0), 1)      AS seq_participation_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE BETWEEN :start_date AND :end_date
    AND DAYOFWEEK(DATE) = 1
GROUP BY week_start
ORDER BY week_start',
     '(week)', 'start_date DATE, end_date DATE',
     'start_date=DATEADD(day,-90,CURRENT_DATE()), end_date=CURRENT_DATE()-1',
     'week_start, paid_teams, sequence_teams, seq_participation_pct',
     'Sequence, Participation, WAT, Trend', 'Analytics', 'approved',
     NULL, 'Uses GENPIPE_FEATURE_SEQUENCE_USER_COUNTS_L7 from DIM_TEAMS_DAILY. PDF shows core+paid teams; this uses all paid. Samples Mondays.'),

    ('Paid Team Counts and ARR', 'daily_snapshot',
     'Current paid team and user counts from DIM_TEAMS_DAILY. Answers "how many paid teams and users do we have?"',
     'SELECT
    SUM(CASE WHEN IS_PAID_IND = true THEN 1 ELSE 0 END) AS paid_teams,
    ROUND(SUM(CASE WHEN IS_PAID_IND = true THEN ARR ELSE 0 END) / 1e6, 2) AS total_arr_m,
    ROUND(AVG(CASE WHEN IS_PAID_IND = true THEN ARR END), 0) AS avg_arr_per_team
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE DATE = :ds',
     'snapshot', 'ds DATE',
     'ds=CURRENT_DATE()-1',
     'paid_teams, total_arr_m, avg_arr_per_team',
     'Paid Teams, Users, ARR', 'Analytics', 'approved',
     NULL, 'Uses DIM_TEAMS_DAILY for team/user counts. For revenue precision, prefer Total ARR Snapshot metric (FCT_DAILY_REVENUE). This is useful when you need counts and basic ARR in a single query.')
) src
ON tgt.metric_name = src.metric_name AND tgt.variant = src.variant
WHEN MATCHED THEN UPDATE SET
    description = src.description,
    metric_sql = src.metric_sql,
    grain = src.grain,
    parameters = src.parameters,
    default_parameters = src.default_parameters,
    output_columns = src.output_columns,
    related_terms = src.related_terms,
    owner = src.owner,
    status = src.status,
    okr_target = src.okr_target,
    notes = src.notes,
    updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
    metric_name, variant, description, metric_sql, grain, parameters,
    default_parameters, output_columns, related_terms, owner, status, okr_target, notes
) VALUES (
    src.metric_name, src.variant, src.description, src.metric_sql, src.grain, src.parameters,
    src.default_parameters, src.output_columns, src.related_terms, src.owner, src.status, src.okr_target, src.notes
);
