# FCT_TEAM_REVENUE_DAILY

> DE-owned daily revenue snapshot per team. Part of Bridie's PLAYGROUND foundation tables.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY` |
| **Grain** | One row per team + date (`team_id` + `ds`) |
| **Row count** | ~72.7M (2026-03-06) |
| **Refresh cadence** | Daily via `PLAYGROUND_DAILY_REFRESH` task DAG (Tier 2, after FCT_TEAM_FEATURE_USERS_DAILY) |
| **Trust level** | High (direct Mongo billing source, 95.1% match with FCT_DAILY_REVENUE) |
| **Owner** | Bridie Meredith (Analytics) |
| **DAG** | `PLAYGROUND_DAILY_REFRESH` → `TASK_REFRESH_FCT_TEAM_REVENUE_DAILY` |

## Description

Foundation table for daily team-level ARR snapshots. Sourced directly from `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` (Mongo billing system audit logs). ARR is `cached_current_arr` from leadgenie — formula: `billing_cycle_price * 12 / billing_interval_months`. Reconciles at 95.1% with dbt-built `FCT_DAILY_REVENUE` at the team level.

Upstream for `DIM_TEAMS_DAILY_V2` and other PLAYGROUND foundation tables.

**Why it exists:** FCT_DAILY_REVENUE (dbt/SFDC-based) uses SFDC opportunity data and has IS_PARENT_ACCOUNT duality that makes team-level queries complex. FCT_TEAM_REVENUE_DAILY is simpler — one row per team per day, ARR from billing system, clean TEAM_ID key.

## Upstream Sources

| Source | Relationship | Notes |
|---|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` | Primary | Daily Mongo billing snapshot (~79M rows). Deduplicated by GROUP BY team_id + date to handle occasional duplicate runs by AuditReportGenerationWorker. |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `team_id` | TEXT | Apollo team ID | FK to DIM_MONGO_TEAMS._ID |
| `ds` | DATE | Snapshot date | Date column (not DATE_PERIOD) |
| `arr` | NUMBER | Annual Recurring Revenue | Direct from billing system. Formula: billing_cycle_price * 12 / billing_interval_months |
| `apollo_edition` | TEXT | Plan/edition name | Basic, Professional, Organization, Custom, etc. |
| `product_id` | TEXT | Stripe/billing product ID | For plan-level analysis |
| `seat_limit` | NUMBER | Seat limit on the team's plan | |
| `payment_term` | TEXT | Billing frequency | month-to-month, annual, etc. |
| `billing_period_start` | TIMESTAMP | Current billing period start | |
| `billing_period_end` | TIMESTAMP | Current billing period end | |

## How It's Used

### Point-in-time paid team snapshot

```sql
-- Paid team count and total ARR as of a specific date (team-level)
SELECT
    COUNT(DISTINCT team_id)   AS paid_teams,
    SUM(arr)                  AS total_arr,
    AVG(arr)                  AS avg_arr_per_team
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY
WHERE ds = '2025-09-30'
  AND arr > 0;
```

### Plan distribution

```sql
SELECT
    apollo_edition,
    COUNT(DISTINCT team_id)   AS teams,
    SUM(arr)                  AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY
WHERE ds = '2025-09-30'
  AND arr > 0
GROUP BY 1
ORDER BY 2 DESC;
```

### Segment join (via LU_TEAM_ATTRIBUTES)

```sql
SELECT
    lu.account_segment,
    COUNT(DISTINCT r.team_id)   AS paid_teams,
    SUM(r.arr)                  AS total_arr
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES lu
  ON r.team_id = lu.team_id
WHERE r.ds = CURRENT_DATE - 4  -- table lags ~4 days
  AND r.arr > 0
GROUP BY 1
ORDER BY 3 DESC;
```

## Relationship to FCT_DAILY_REVENUE

| Dimension | FCT_TEAM_REVENUE_DAILY (PLAYGROUND) | FCT_DAILY_REVENUE (ANALYTICS) |
|---|---|---|
| ARR source | Mongo billing (leadgenie) | Salesforce opportunities (dbt) |
| Match rate | 95.1% at team level | n/a |
| ARR range (team-level) | ~$165–175M (late 2025) | ~$165–175M (IS_PARENT=FALSE) |
| Exec aggregate ARR | Not available (no IS_PARENT_ACCOUNT) | ~$330–340M (IS_PARENT=TRUE) |
| Motion flags (IS_REP_DRIVEN etc.) | Not available | Available |
| Date column | `ds` | `DATE_PERIOD` |
| Team ID column | `team_id` | `APOLLO_TEAM_ID` |

**Use FCT_TEAM_REVENUE_DAILY for:** point-in-time plan/edition distribution, paid team counts by segment, simple ARR lookups.
**Use FCT_DAILY_REVENUE for:** rep-driven ARR, SFDC attribution, executive topline ARR (IS_PARENT_ACCOUNT = TRUE), change categories, motion breakdown (SS/SA/REP/LABS).

## Known Issues & Gotchas

- Table date column is `ds` (not `DATE_PERIOD` like FCT_DAILY_REVENUE) — column name confusion is a common bug
- Table lags approximately 4 days behind current date
- KNOWN ISSUE: Source has duplicate rows on specific dates (2025-11-21, 2023-03-19) — these are deduplicated via GROUP BY in the build SQL
- Coverage starts 2025-11-10 for full historical data — pre-2025-11-10 data may be incomplete
- No IS_PARENT_ACCOUNT or parent-account aggregation — this is team-level only. For executive aggregate totals matching North Star, use FCT_DAILY_REVENUE IS_PARENT_ACCOUNT = TRUE.
- No MRR motion breakdown (SS/SA/REP/LABS) — only total ARR

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-31 | Created context file — documented as canonical foundation table for team-level daily ARR | Brighid (via Claude) |
