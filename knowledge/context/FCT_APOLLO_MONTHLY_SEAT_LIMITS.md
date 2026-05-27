# FCT_APOLLO_MONTHLY_SEAT_LIMITS

> Monthly seat limits and team status per Apollo team. Used to count new/active paid teams for ACV and logo metrics.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_APOLLO_MONTHLY_SEAT_LIMITS` |
| **Grain** | One row per team + month (`APOLLO_TEAM_ID` + `DATE_PERIOD`) |
| **Row count** | <!-- TODO: check --> |
| **Refresh cadence** | Unknown — not found in airflow-dags |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | Analytics / Finance |
| **DAG** | Not found in airflow-dags |

## Description

Monthly snapshot of team seat limits and subscription status. Joined to `FCT_MONTHLY_REVENUE` at team level (`IS_PARENT_ACCOUNT = false`) to count distinct new paid teams — the denominator in ACV calculations. Also used for logo count metrics.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `APOLLO_TEAM_ID` | TEXT | Team ID | FK to FCT_MONTHLY_REVENUE.APOLLO_TEAM_ID |
| `DATE_PERIOD` | DATE | Month (first of month) | Join on this + APOLLO_TEAM_ID |
| `CHANGE_CATEGORY` | TEXT | Revenue movement category | Same values as FCT_MONTHLY_REVENUE: new, churn, upgrade, downgrade |
| `IS_PAID_ACTIVE` | BOOLEAN | Team is paid and active this month | **Used as filter for new team count** |

## How It's Used

### New team count for ACV denominator

```sql
-- Join to FCT_MONTHLY_REVENUE at team level (IS_PARENT_ACCOUNT = false)
LEFT JOIN ANALYTICS_DB.ANALYTICS.FCT_APOLLO_MONTHLY_SEAT_LIMITS sl
  ON mr.APOLLO_TEAM_ID = sl.APOLLO_TEAM_ID
 AND mr.DATE_PERIOD    = sl.DATE_PERIOD
 AND mr.IS_PARENT_ACCOUNT = false   -- team-level join, not parent account

-- Count new teams (denominator for ACV)
COUNT(DISTINCT CASE WHEN sl.IS_PAID_ACTIVE AND sl.CHANGE_CATEGORY = 'new'
      THEN sl.APOLLO_TEAM_ID END)   AS count_of_new_teams
```

### ACV calculation (combined with FCT_MONTHLY_REVENUE)

```sql
SELECT
    DATE_TRUNC('month', mr.DATE_PERIOD)                                     AS month,
    -- Numerator: new team ARR at team level
    SUM(CASE WHEN mr.CHANGE_CATEGORY IN ('new', 'new_reactivated')
             AND mr.IS_PARENT_ACCOUNT = false
             THEN mr.ARR_CHANGE ELSE 0 END)                                 AS new_team_arr,
    -- Denominator: distinct new paid active teams
    COUNT(DISTINCT CASE WHEN sl.IS_PAID_ACTIVE AND sl.CHANGE_CATEGORY = 'new'
          THEN sl.APOLLO_TEAM_ID END)                                        AS new_team_count,
    -- ACV
    NULLIF(SUM(CASE WHEN mr.CHANGE_CATEGORY IN ('new', 'new_reactivated')
                    AND mr.IS_PARENT_ACCOUNT = false
                    THEN mr.ARR_CHANGE ELSE 0 END), 0)
    / NULLIF(COUNT(DISTINCT CASE WHEN sl.IS_PAID_ACTIVE AND sl.CHANGE_CATEGORY = 'new'
                   THEN sl.APOLLO_TEAM_ID END), 0)                           AS acv_per_new_team
FROM ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE mr
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat
  ON mr.SFDC_TEAM_OR_ACCOUNT_ID = sat.SFDC_TEAM_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa
  ON COALESCE(sat.SFDC_ACCOUNT_ID, mr.SFDC_TEAM_OR_ACCOUNT_ID) = sa.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.FCT_APOLLO_MONTHLY_SEAT_LIMITS sl
  ON mr.APOLLO_TEAM_ID = sl.APOLLO_TEAM_ID
 AND mr.DATE_PERIOD    = sl.DATE_PERIOD
 AND mr.IS_PARENT_ACCOUNT = false
WHERE mr.DATE_PERIOD >= DATEADD('month', -36, DATE_TRUNC('month', CURRENT_DATE))
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1
ORDER BY 1 DESC;
```

## Known Issues & Gotchas

- Always join with `IS_PARENT_ACCOUNT = false` — this table is team-level, not parent account level
- `CHANGE_CATEGORY = 'new'` for logo count (strict new only); `IN ('new', 'new_reactivated')` for ARR (includes reactivations)

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created — documented from ACV query | Leo |
