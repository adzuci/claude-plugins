# DIM_SALESFORCE_CONTACTS

> Salesforce contact dimension. One row per SF contact record.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_CONTACTS` |
| **Grain** | One row per Salesforce Contact |
| **Row count** | ~9.6M (2026-03-06) |
| **Refresh cadence** | Unknown — not in airflow-dags. Likely Salesforce integration or dbt. |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | Sales Ops / Analytics |
| **DAG** | Not found in airflow-dags. |

## Description

SF contact dimension (19 distinct users, 18K queries). Salesforce CRM contact records — separate from Apollo's DIM_MONGO_CONTACTS which tracks Apollo-native contacts. Primary use case for Growth team: tracking weekly signups by UTM channel using `APOLLO_USER_CREATE_DATE_C` and `ZP_USER_ID_C` as the dedup key.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `APOLLO_USER_CREATE_DATE_C` | DATE | Date user was created in Apollo | Used for signup week bucketing |
| `ZP_USER_ID_C` | TEXT | Unique user identifier | **Signup dedup key** — `COUNT(DISTINCT ZP_USER_ID_C) WHERE ZP_USER_ID_C != ''`. Empty string = no valid signup. |
| `LAST_TOUCH_UTM_CHANNEL_GROUP` | TEXT | Last-touch UTM channel group attribution | Growth channel dimension — e.g. Paid, Organic, Direct |
| `ACCOUNT_ID` | TEXT | FK to `DIM_SALESFORCE_ACCOUNTS.ID` | |
| `SFDC_TEAM_ID` | TEXT | FK to `DIM_SALESFORCE_APOLLO_TEAMS.SFDC_TEAM_ID` | |

## How It's Used

### Weekly signups by UTM channel (Growth)

```sql
SELECT
    -- Sunday-based week (Growth convention for this metric)
    DATEADD('day', (0 - EXTRACT(DOW FROM APOLLO_USER_CREATE_DATE_C)::integer),
            APOLLO_USER_CREATE_DATE_C)::date          AS signup_week,
    LAST_TOUCH_UTM_CHANNEL_GROUP                      AS channel,
    COUNT(DISTINCT CASE WHEN ZP_USER_ID_C != ''
          THEN ZP_USER_ID_C END)                      AS total_signups
FROM ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_CONTACTS sc
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa
  ON sc.ACCOUNT_ID = sa.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat
  ON sc.SFDC_TEAM_ID = sat.SFDC_TEAM_ID
WHERE APOLLO_USER_CREATE_DATE_C >= DATEADD('day', -721, CURRENT_DATE)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1, 2
ORDER BY 1 DESC;
```

**Note on week anchor:** Sunday-based weeks (`EXTRACT(DOW)` where 0=Sunday) — consistent with product WAT/WAU canonical anchor in `DIM_TEAMS_DAILY`.

## Known Issues & Gotchas

- Different from `DIM_MONGO_CONTACTS` — this is CRM contacts from Salesforce, not Apollo-native contacts
- `ZP_USER_ID_C` can be empty string (not NULL) for contacts without a valid signup — always filter `!= ''`
- `IS_CORE_ACCOUNT` filter in Growth Looker queries is a no-op (includes all) — population is controlled by `ACCOUNT_SEGMENT`
- Week anchor is Sunday-based — consistent with product WAT/WAU canonical anchor

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
| 2026-03-20 | Added key columns, signup dedup pattern, weekly signups by UTM channel query | Leo |
