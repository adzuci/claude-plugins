# PRODUCT_METRICS_DAILY

**Schema:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE`
**Grain:** metric x use_case x topic x segment x activity_date
**Row count:** ~1,818 (as of 2026-03-04)
**Refresh:** Daily; forward-fills to end of month — always filter `ACTIVITY_DATE <= CURRENT_DATE() - 1`
**Trust level:** Canonical — this is the single source of truth for platform activity metrics

---

## Purpose

Central product metrics table powering FY27 R&D reporting. Contains DAU/WAU/MAU (users) and DAT/WAT/MAT (teams) plus conversion, NRR, retention, and feature participation metrics.

## Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `ACTIVITY_DATE` | DATE | Metric observation date |
| `METRIC` | VARCHAR | Metric name: `dat`, `wat`, `mat`, `dau`, `wau`, `mau`, `amount`, etc. |
| `USE_CASE` | VARCHAR | Metric category: `apollo_platform`, `conversion`, `nrr`, `retention`, `participation` |
| `TOPIC` | VARCHAR | Sub-category: `overall`, `paid_d7`, `paid_d14`, `workflow_d7`, `sequence_d28`, feature names, etc. |
| `SEGMENT` | VARCHAR | Compound string: `paid\|not_paid_core\|not_core_tier_N_vsb\|smb\|mid_market\|enterprise\|unknown` — parse 4th group for segment |
| `METRIC_VALUE` | NUMBER | The metric value — replaces old PAID_ONLY_COUNT/TOTAL_COUNT/COHORT_SIZE/CONVERTED_COUNT/RETAINED_COUNT columns (table restructured to long format) |
| `PRODUCT_METRICS_DAILY_SK` | NUMBER | Surrogate key |

## Canonical Query Patterns

### WAT (Weekly Active Teams) — point-in-time
```sql
SELECT ACTIVITY_DATE, METRIC_VALUE AS wat
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.PRODUCT_METRICS_DAILY
WHERE METRIC = 'wat'
  AND USE_CASE = 'apollo_platform'
  AND TOPIC = 'overall'
  AND ACTIVITY_DATE = '2026-03-15'
  AND ACTIVITY_DATE <= CURRENT_DATE() - 1
```

### WAT trend (weekly snapshots)
```sql
SELECT ACTIVITY_DATE, METRIC_VALUE AS wat
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.PRODUCT_METRICS_DAILY
WHERE METRIC = 'wat'
  AND USE_CASE = 'apollo_platform'
  AND TOPIC = 'overall'
  AND ACTIVITY_DATE <= CURRENT_DATE() - 1
  AND DAYOFWEEK(ACTIVITY_DATE) = 0  -- Sundays for weekly cadence
ORDER BY ACTIVITY_DATE DESC
LIMIT 12
```

### Feature participation (feature WAT as % of platform WAT)
```sql
SELECT ACTIVITY_DATE, TOPIC AS feature,
       METRIC_VALUE AS feature_wat,
       SUM(METRIC_VALUE) OVER (PARTITION BY ACTIVITY_DATE) AS total_wat,
       ROUND(METRIC_VALUE / NULLIF(total_wat, 0) * 100, 1) AS participation_pct
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.PRODUCT_METRICS_DAILY
WHERE METRIC = 'wat'
  AND USE_CASE = 'participation'
  AND ACTIVITY_DATE = CURRENT_DATE() - 1
ORDER BY feature_wat DESC
```

## Rolling Window Warning

WAT, WAU, MAT, MAU are **rolling window metrics** (L7, L7, L28, L28 respectively). Each day's value counts distinct teams/users active in the trailing window. **Never sum or total these across dates** — overlapping windows mean the same team/user is counted in multiple rows.

## Use Cases Covered

| use_case | What it measures | Key metrics |
|----------|-----------------|-------------|
| `apollo_platform` | Platform-wide actives | DAU, WAU, MAU, DAT, WAT, MAT |
| `conversion` | New team conversion | `paid_d7`, `paid_d14` topics; rate = converted_count / cohort_size |
| `nrr` | Net Revenue Retention | Month-end only; `nrr_starting_arr`, `nrr_upgrade_arr`, `nrr_churned_and_downgraded_arr` |
| `retention` | Feature retention | `workflow_d7`, `sequence_d28`, `overall_d90` topics; rate = retained_count / cohort_size |
| `participation` | Feature adoption | Feature-level WAT: genpipe, win_close, enrichment, ai, crm, extension |

## Related Tables

| Need | Use Instead |
|------|------------|
| Team-level detail (individual team activity) | `DIM_TEAMS_DAILY` or `DIM_TEAMS_DAILY_V2` |
| User-level daily activity | `DIM_USERS_DAILY` |
| AI Assistant specific metrics | `USER_AI_ASSISTANT_DAILY` |
| Revenue / ARR | `FCT_TEAM_REVENUE_DAILY` or `FCT_DAILY_REVENUE` |
