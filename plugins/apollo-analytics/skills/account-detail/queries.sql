-- account-detail skill — named SQL blocks
-- Each block is consumed by SKILL.md steps 1–9.
-- Substitute {team_id} with the resolved team_id string before running via the Snowflake MCP.
-- Single-quote the value inline: WHERE APOLLO_TEAM_ID = '{team_id}'
-- SECURITY: {input} and {team_id} are user-supplied. Before substituting, escape any
-- single quotes (' -> '') so free-text company names / domains cannot break or inject SQL.


-- ─────────────────────────────────────────────────────────────────────────────
-- name: resolve_by_domain
-- Use when input contains a "." (looks like a domain).
-- Returns: TEAM_ID, ARR
-- ─────────────────────────────────────────────────────────────────────────────
SELECT t.APOLLO_TEAM_ID AS TEAM_ID, t.ARR
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS dt
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY t
  ON t.APOLLO_TEAM_ID = dt.APOLLO_TEAM_ID
WHERE LOWER(dt.WEBSITE_DOMAIN) = LOWER('{input}')
  AND t.DATE = (
    SELECT MAX(DATE) FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
    WHERE APOLLO_TEAM_ID = dt.APOLLO_TEAM_ID
  )
ORDER BY t.ARR DESC NULLS LAST
LIMIT 1;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: resolve_by_user_id
-- Use when input looks like a MongoDB ObjectId (24-char hex, no dots, no spaces).
-- Returns: TEAM_ID
-- ─────────────────────────────────────────────────────────────────────────────
SELECT DISTINCT TEAM_ID
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_USERS
WHERE _ID = '{input}'
LIMIT 1;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: resolve_by_team_name
-- Use when input is a free-text company / team name (fallback).
-- Returns: TEAM_ID, TEAM_NAME, WEBSITE_DOMAIN, ACCOUNT_SEGMENT, ARR (up to 5 matches)
-- If multiple rows come back, use the one with highest ARR and tell the user.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT dt.APOLLO_TEAM_ID AS TEAM_ID, dt.TEAM_NAME, dt.WEBSITE_DOMAIN,
       dt.ACCOUNT_SEGMENT, t.ARR
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS dt
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY t
  ON t.APOLLO_TEAM_ID = dt.APOLLO_TEAM_ID
WHERE (dt.TEAM_NAME ILIKE '%{input}%'
    OR dt.ACCOUNT_NAME ILIKE '%{input}%')
  AND t.DATE = (
    SELECT MAX(DATE) FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
    WHERE APOLLO_TEAM_ID = dt.APOLLO_TEAM_ID
  )
ORDER BY t.ARR DESC NULLS LAST
LIMIT 5;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: account
-- Contract key: "acct"  — exactly 1 row expected
-- No renames needed; column names match contract verbatim.
-- DATE → alias SNAPSHOT_DATE (already aliased in SELECT).
-- FIRST_TEAM_ACTIVE_DATE: coerce to "YYYY-MM-DD" string if returned as timestamp.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT td.APOLLO_TEAM_ID, dt.TEAM_NAME, dt.WEBSITE_DOMAIN, dt.ACCOUNT_NAME,
       dt.ACCOUNT_SEGMENT, dt.ACCOUNT_SUB_SEGMENT, dt.CSM_NAME, dt.ACCOUNT_OWNER_NAME,
       td.ARR, td.PAID_SEAT_LIMIT, td.COUNT_OF_USERS, td.ACTIVE_USER_COUNTS_L7,
       td.IS_PAID_IND, td.IS_CORE_ACCOUNT_IND,
       td.FIRST_TEAM_ACTIVE_DATE::DATE AS FIRST_TEAM_ACTIVE_DATE,
       td.DATE::DATE AS SNAPSHOT_DATE
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY td
LEFT JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS dt
  ON dt.APOLLO_TEAM_ID = td.APOLLO_TEAM_ID
WHERE td.APOLLO_TEAM_ID = '{team_id}'
  AND td.DATE = (
    SELECT MAX(DATE) FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
    WHERE APOLLO_TEAM_ID = '{team_id}'
  )
LIMIT 1;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: features
-- Contract key: "feat"  — exactly 1 row expected
-- Column aliases map raw DIM_TEAMS_DAILY feature columns → contract names.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    ACTIVE_USER_COUNTS_L7                           AS ACTIVE_USERS,
    GENPIPE_FEATURE_RECORD_ACTIONED_USER_COUNTS_L7  AS PROSPECTING_RECORD_ACTION,
    ENRICHMENT_API_USER_COUNTS_L7                   AS ENRICHMENT_API,
    MEETING_BOOKED_USER_COUNTS_L7                   AS MEETING_BOOKED,
    WIN_CLOSE_MEETING_ASSISTANT_USER_COUNTS_L7      AS MEETING_ASSISTANT,
    MEETING_RECORDED_USER_COUNTS_L7                 AS MEETING_RECORDED,
    AI_PLATFORM_USER_COUNTS_L7                      AS AI_PLATFORM,
    CRM_RECORD_MANAGEMENT_USER_COUNTS_L7            AS CRM_MANAGEMENT,
    WIN_CLOSE_DEALS_USER_COUNTS_L7                  AS WIN_CLOSE_DEALS
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
WHERE APOLLO_TEAM_ID = '{team_id}'
  AND DATE = (
    SELECT MAX(DATE) FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY
    WHERE APOLLO_TEAM_ID = '{team_id}'
  )
LIMIT 1;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: calls
-- Contract key: "calls"  — exactly 1 aggregate row
-- LAST_CALL comes back as a date; coerce to "YYYY-MM-DD" string.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    COUNT(*)                                                AS TOTAL,
    COUNT(CASE WHEN IS_ANSWERED THEN 1 END)                AS ANSWERED,
    ROUND(AVG(CASE WHEN IS_ANSWERED THEN DURATION END), 0) AS AVG_DUR,
    COUNT(CASE WHEN IS_INBOUND THEN 1 END)                 AS INBOUND,
    COUNT(CASE WHEN NOT IS_INBOUND THEN 1 END)             AS OUTBOUND,
    COUNT(DISTINCT USER_ID)                                AS CALLERS,
    MAX(CREATED_AT_UTC)::DATE                              AS LAST_CALL
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PHONE_CALLS
WHERE TEAM_ID = '{team_id}'
  AND CREATED_AT_UTC >= CURRENT_DATE - 90;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: support
-- Contract key: "support"  — up to 20 rows
-- CONVERSATION_CREATED_AT: renderer uses first 10 chars as date string — keep as-is.
-- APOLLO_TOPIC_DETECTION is in contract (reserved, not rendered) — include it.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    CONVERSATION_CREATED_AT,
    CONVERSATION_STATUS,
    APOLLO_TOPIC_DETECTION,
    AI_GENERATED_SUMMARY
FROM ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS
WHERE APOLLO_TEAM_ID = '{team_id}'
  AND CONVERSATION_CREATED_AT >= CURRENT_DATE - 90
ORDER BY CONVERSATION_CREATED_AT DESC
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: credits
-- Contract key: "credits"  — up to 15 rows
-- MODEL is computed inline (Unified / Legacy). LIMIT_VAL aliases LIMIT (reserved word).
-- P_START / P_END: coerce to "YYYY-MM-DD" strings.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    FEATURE_TYPE,
    IFF(LOWER(PRODUCT_ID) ILIKE '%unified%', 'Unified', 'Legacy') AS MODEL,
    SUM(CREDITS_USED)                                              AS USED,
    MAX(CREDIT_LIMIT)                                              AS LIMIT_VAL,
    MAX(BILLING_PERIOD_START)::DATE                                AS P_START,
    MAX(BILLING_PERIOD_END)::DATE                                  AS P_END
FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS
WHERE TEAM_ID = '{team_id}'
  AND DS >= CURRENT_DATE - 35
  AND FEATURE_TYPE != 'ai_email'
GROUP BY 1, 2
ORDER BY USED DESC
LIMIT 15;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: hvo
-- Contract key: "hvo"  — up to 10 rows
-- All columns match contract verbatim. DATE aliased to DATE (no rename needed).
-- DATE: coerce to "YYYY-MM-DD" string. ACTION_DATE_FINAL: same.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT DISTINCT
    h.CONVERSATION_ID,
    h.DATE::DATE                                AS DATE,
    h.MEETING_HOST_EMAIL,
    h.AHA_MOMENT,
    h.CALL_TYPE,
    h.PAIN_POINT,
    h.RECOMMENDED_NEXT_ACTION,
    h.UPSELL_OPPORTUNITY,
    h.CUSTOMER_TECHNICAL_SUFFICIENCY_SCORE,
    h.NEXT_ACTION_TYPE_FINAL,
    h.ACTION_TEAM,
    h.ACTION_DATE_FINAL::DATE                   AS ACTION_DATE_FINAL,
    h.WILL_TRY_FEATURES,
    h.HAS_UNRESOLVED_QUESTIONS,
    h.FEATURE_DISCUSSED,
    h.CUSTOMER_INTENDED_USE_CASE
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING h
JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS c
  ON c.CONVERSATION_ID = h.CONVERSATION_ID,
LATERAL FLATTEN(INPUT => PARSE_JSON(c.CONVERSATION_PARTICIPANTS)) p
JOIN ANALYTICS_DB.ANALYTICS.INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS cf
  ON cf.CONTACT_ID = p.value:contact_id['$oid']::string
WHERE p.value:is_internal_participant::boolean = false
  AND p.value:contact_id IS NOT NULL
  AND cf.APOLLO_TEAM_ID = '{team_id}'
ORDER BY 2 DESC  -- col 2 = DATE alias; raw h.DATE is invalid under SELECT DISTINCT
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: gtme
-- Contract key: "gtme"  — up to 10 rows
-- All columns match contract verbatim.
-- DATE: coerce to "YYYY-MM-DD". ACTION_DATE_RECOMMENDED: same.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT DISTINCT
    g.CONVERSATION_ID,
    g.DATE::DATE                                AS DATE,
    g.MEETING_HOST_EMAIL,
    g.AHA_MOMENT,
    g.CUSTOMER_SENTIMENT,
    g.CHURN_RISK_SCORE,
    g.PAIN_POINT,
    g.RECOMMENDED_NEXT_ACTION,
    g.UPSELL_DETECTED,
    g.DISCUSSION_SUMMARY,
    g.NEXT_ACTION_TYPE_FINAL,
    g.CHURN_RISK_REASON,
    g.UPSELL_REASON,
    g.PRODUCT_GAPS,
    g.ACTION_TEAM,
    g.ACTION_DATE_RECOMMENDED::DATE             AS ACTION_DATE_RECOMMENDED
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS g
JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CONVERSATIONS c
  ON c.CONVERSATION_ID = g.CONVERSATION_ID,
LATERAL FLATTEN(INPUT => PARSE_JSON(c.CONVERSATION_PARTICIPANTS)) p
JOIN ANALYTICS_DB.ANALYTICS.INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS cf
  ON cf.CONTACT_ID = p.value:contact_id['$oid']::string
WHERE p.value:is_internal_participant::boolean = false
  AND p.value:contact_id IS NOT NULL
  AND cf.APOLLO_TEAM_ID = '{team_id}'
ORDER BY 2 DESC  -- col 2 = DATE alias; raw g.DATE is invalid under SELECT DISTINCT
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────────────
-- name: deliverability
-- Contract key: "deliv"  — all qualifying rows (no LIMIT; ORDER BY recency)
-- LAST_SENT: SQL already casts to ::DATE — coerce to "YYYY-MM-DD" string.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    EMAILER_CAMPAIGN_NAME,
    EMAILER_CAMPAIGN_ID,
    EMAIL_SENT_COUNTS                                                         AS SENT,
    EMAIL_DELIVERED_COUNTS                                                    AS DELIVERED,
    EMAIL_OPENED_COUNTS                                                       AS OPENED,
    ROUND(EMAIL_OPENED_COUNTS        / NULLIF(EMAIL_DELIVERED_COUNTS, 0) * 100, 1) AS OPEN_RATE_PCT,
    EMAIL_REPLY_RECEIVED_COUNTS                                               AS REPLIED,
    ROUND(EMAIL_REPLY_RECEIVED_COUNTS / NULLIF(EMAIL_DELIVERED_COUNTS, 0) * 100, 1) AS REPLY_RATE_PCT,
    EMAIL_INTEREST_RECEIVED_COUNTS                                            AS INTERESTED,
    ROUND(EMAIL_INTEREST_RECEIVED_COUNTS / NULLIF(EMAIL_DELIVERED_COUNTS, 0) * 100, 1) AS INTEREST_RATE_PCT,
    EMAIL_BOUNCED_COUNTS                                                      AS BOUNCED,
    ROUND(EMAIL_BOUNCED_COUNTS       / NULLIF(EMAIL_SENT_COUNTS, 0) * 100, 1) AS BOUNCE_RATE_PCT,
    EMAIL_HARD_BOUNCED_COUNTS                                                 AS HARD_BOUNCED,
    ROUND(EMAIL_HARD_BOUNCED_COUNTS  / NULLIF(EMAIL_SENT_COUNTS, 0) * 100, 1) AS HARD_BOUNCE_RATE_PCT,
    LAST_SENT_AT::DATE                                                        AS LAST_SENT
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.SEQUENCES
WHERE APOLLO_TEAM_ID = '{team_id}'
  AND EMAIL_SENT_COUNTS > 0
ORDER BY LAST_SENT_AT DESC NULLS LAST;
