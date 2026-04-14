---
name: pr-metrics
description: Use when someone asks for PR lead time, velocity, cycle time, or PR health metrics for any engineering team. Pulls data from Snowflake and applies Apollo engineering health thresholds.
---

# PR Metrics

Pulls PR lead time and velocity data for any Apollo engineering team from Snowflake.

## Data Source

- **Table:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LEADGENIE_GITHUB_COMMIT_DATA`
- **CLI:** `snow sql --connection apollo --query "..."`

## Steps

### 1. Discover available teams

Run this query to show the user which team names exist in the table:

```sql
SELECT DISTINCT team
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LEADGENIE_GITHUB_COMMIT_DATA
WHERE team IS NOT NULL
ORDER BY team;
```

Present the list and ask: **"Which team would you like metrics for?"**

If the user specifies a team that maps to multiple names (e.g. a rename), ask them to confirm all relevant names to include.

### 2. Get the date range

Ask the user for the time range in natural language (e.g. "last 2 weeks", "Apr 1–14", "ending Apr 4").

Convert to:

- `<START>` — start date (YYYY-MM-DD, inclusive)
- `<END>` — end date (YYYY-MM-DD, inclusive)
- `<ROLLING_START>` — 4 weeks before `<END>` (YYYY-MM-DD)

### 3. Run the query

Replace `<TEAM>`, `<START>`, `<END>`, and `<ROLLING_START>` with actual values. If multiple team names apply, expand the `IN` clause accordingly.

```sql
WITH pr_metrics AS (
  SELECT
    pr_id,
    merged_ts,
    DATEDIFF('hour', opened_ts, merged_ts)        AS lead_time_hrs,
    DATEDIFF('hour', opened_ts, pr_approved_ts)   AS time_to_approval_hrs,
    pr_comments_count
  FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_LEADGENIE_GITHUB_COMMIT_DATA
  WHERE team IN ('<TEAM>')
    AND pr_id IS NOT NULL
    AND merged_ts IS NOT NULL
    AND opened_ts IS NOT NULL
),
current_period AS (
  SELECT
    'Selected period (<START> – <END>)' AS period,
    COUNT(DISTINCT pr_id)                                                        AS pr_velocity,
    ROUND(MEDIAN(lead_time_hrs), 1)                                              AS median_lead_time_hrs,
    ROUND(AVG(lead_time_hrs), 1)                                                 AS avg_lead_time_hrs,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY lead_time_hrs), 1)        AS p75_lead_time_hrs,
    ROUND(MEDIAN(time_to_approval_hrs), 1)                                       AS median_time_to_approval_hrs,
    ROUND(AVG(pr_comments_count), 1)                                             AS avg_comments_per_pr
  FROM pr_metrics
  -- DATEADD ensures PRs merged on <END> itself are included (timestamp < midnight of next day)
  WHERE merged_ts >= '<START>'::DATE AND merged_ts < DATEADD('day', 1, '<END>'::DATE)
),
rolling AS (
  SELECT
    'Rolling 4 weeks (<ROLLING_START> – <END>)' AS period,
    COUNT(DISTINCT pr_id)                                                        AS pr_velocity,
    ROUND(MEDIAN(lead_time_hrs), 1)                                              AS median_lead_time_hrs,
    ROUND(AVG(lead_time_hrs), 1)                                                 AS avg_lead_time_hrs,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY lead_time_hrs), 1)        AS p75_lead_time_hrs,
    ROUND(MEDIAN(time_to_approval_hrs), 1)                                       AS median_time_to_approval_hrs,
    ROUND(AVG(pr_comments_count), 1)                                             AS avg_comments_per_pr
  FROM pr_metrics
  WHERE merged_ts >= '<ROLLING_START>'::DATE AND merged_ts < DATEADD('day', 1, '<END>'::DATE)
)
SELECT * FROM current_period
UNION ALL
SELECT * FROM rolling;
```

### 4. Present results

Present as a markdown table with a health rating column for the selected period:

| Metric | Selected period | Rolling (4w) | Health |
|--------|-------------|--------------|--------|
| PR Velocity | N PRs | N PRs | (ask headcount or skip) |
| Median Lead Time | Nh | Nh | 🟢/🔴 |
| P75 Lead Time | Nh | Nh | 🟢/🔴 |
| Median Time to Approval | Nh | Nh | 🟢/🔴 |
| Avg Comments / PR | N | N | 🟢/🔴 |

Then add a brief **observations** section noting:

- Health rating for each metric with the threshold that applies
- Whether the selected period is above/below the 4-week baseline (trending better or worse)
- Any significant gap between median and P75 (long-tail outliers)

## Health Thresholds (Apollo Engineering)

Apply these to the **selected period** values. Use 🟢/🔴 labels.

| Metric | 🟢 GREEN | 🔴 NOT HEALTHY |
|--------|----------|----------------|
| Median Lead Time (P50) | < 48h | ≥ 48h |
| P75 Lead Time | < 72h | ≥ 72h (company goal is < 48h) |
| Median Time to Approval (P50) | < 24h | ≥ 24h |
| Avg Comments / PR | < 10 | ≥ 10 |

**PR Velocity** is measured per engineer per month. To rate it, ask for team headcount then compute: `(period PRs / team size) * (30 / days_in_period)` for a monthly estimate.

| Level | PRs / engineer / month |
|-------|------------------------|
| 🟢 Excellent | ≥ 15 |
| 🟡 Satisfactory | ≥ 10 |
| 🔴 Not Healthy | < 5 |

Target: **12+ PRs / engineer / month**. Company TP-75 goal: **< 48h**.

## Known Limitations

**Comments per PR**

- `pr_comments_count` includes GitHub automated messages (bots, CI checks, Dependabot, etc.), which inflates the count
- Until fixed: treat the 🔴 threshold with a grain of salt; flag it but note the caveat

**PR Velocity**

- Reported as raw PR count unless headcount is provided
- Does not account for PTO — note any known PTO weeks when presenting velocity
