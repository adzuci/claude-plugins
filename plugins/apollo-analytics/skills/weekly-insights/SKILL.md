---
name: weekly-insights
description: Surface this week's strategic signals for leadership — which registry metrics moved week over week, churn and expansion trend, automated kernel assessments and red/yellow signals, team-level signal shifts, and current business state. Use when an exec asks what to focus on, what moved, or whether we are on track.
---

# Weekly Insights

Use when an exec asks "what should I focus on?", "what moved this week?", "any insights?", or "are we on track?".

> **Runtime:** run every query through the Snowflake connector's `execute-sql` tool and append
> `/* jarvis:{"app":"jarvis","action":"weekly_insights","source":"mcp","platform":"apollo-analytics"} */`
> as the last line. Every number comes from a query run in this conversation or a dated knowledge file, cited as such.

This skill replicates in SQL what the Analytics team's scheduled pipelines do each week: the daily registry snapshot (`LU_METRIC_SNAPSHOTS`), the Monday intelligence kernels (`INTELLIGENCE_SNAPSHOTS`, `INTELLIGENCE_SIGNAL_RESULTS`), the weekly team-signal aggregation (`WEEKLY_TEAM_SIGNALS`), and the weekly business-state refresh (`knowledge/business_state.md`). The old curated table `LU_WEEKLY_INSIGHTS` was dropped 2026-10-08 — it does not exist.

## Step 0 — Is the snapshot pipeline alive?

```sql
SELECT MAX(snapshot_date) AS latest_snapshot,
       DATEDIFF('day', MAX(snapshot_date), CURRENT_DATE()) AS days_stale,
       MAX(CASE WHEN metric_name = 'saved_metrics_failing'   THEN metric_value END) AS metrics_failing,
       MAX(CASE WHEN metric_name = 'saved_metrics_producing' THEN metric_value END) AS metrics_producing
FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS
WHERE domain = 'pipeline_health'
  AND snapshot_date = (SELECT MAX(snapshot_date) FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS)
```

More than 3 days stale, or `metrics_failing > 0` → say so at the top of the answer and name the affected metrics (`metric_name LIKE 'saved_metric_ok/%' AND metric_value = 0`). Do not present week-over-week movement from a dark pipeline.

## Step 1 — What moved: registry metrics week over week

Snapshot-grain metrics only (`/daily_snapshot/` and `/latest/` variants). Trend variants store one row per period and need Step 2's treatment, not a WoW join.

```sql
WITH latest AS (SELECT MAX(snapshot_date) d FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS),
prev AS (SELECT MAX(snapshot_date) d FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS
         WHERE snapshot_date <= (SELECT DATEADD('day', -7, d) FROM latest)),
amb AS (  -- keys that are not series keys on either day: drop before ranking, or they win the sort with fake deltas
  SELECT metric_name, COALESCE(metric_dimension, '~') dim
  FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS
  WHERE snapshot_date IN ((SELECT d FROM latest), (SELECT d FROM prev))
  GROUP BY metric_name, COALESCE(metric_dimension, '~'), snapshot_date, snapshot_ts
  HAVING COUNT(*) > 1),
s AS (
  SELECT metric_name, COALESCE(metric_dimension, '~') dim, snapshot_date, metric_value
  FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS x
  WHERE domain = 'saved_metrics' AND source_proc = 'snapshot_saved_metrics.py'
    AND (metric_name LIKE '%/daily_snapshot/%' OR metric_name LIKE '%/latest/%')
    AND snapshot_date IN ((SELECT d FROM latest), (SELECT d FROM prev))
    AND NOT EXISTS (SELECT 1 FROM amb a WHERE a.metric_name = x.metric_name AND a.dim = COALESCE(x.metric_dimension, '~'))
  QUALIFY ROW_NUMBER() OVER (PARTITION BY metric_name, COALESCE(metric_dimension, '~'), snapshot_date ORDER BY snapshot_ts DESC) = 1),
p AS (
  SELECT metric_name, dim,
         MAX(CASE WHEN snapshot_date = (SELECT d FROM latest) THEN metric_value END) AS cur,
         MAX(CASE WHEN snapshot_date = (SELECT d FROM prev)   THEN metric_value END) AS prior
  FROM s GROUP BY 1, 2
  HAVING cur IS NOT NULL AND prior IS NOT NULL AND ABS(prior) > 1e-9)
SELECT metric_name, dim, prior, cur,
       ROUND((cur - prior) / NULLIF(ABS(prior), 0) * 100, 1) AS wow_pct,
       (SELECT d FROM prev) AS prior_date, (SELECT d FROM latest) AS latest_date
FROM p
WHERE ABS((cur - prior) / NULLIF(ABS(prior), 0)) * 100 >= 3
ORDER BY ABS((cur - prior) / NULLIF(ABS(prior), 0)) DESC NULLS LAST
LIMIT 25
```

Reading the result:

- `metric_name` is `<registry metric>/<variant>/<measure>`; `dim` is the segment (`channel=…`, `account_segment=…`) or `daily_snapshot` for the total.
- A dimension that embeds a measure (`unique_callers=1364`) is not a series — skip those rows.
- Small denominators produce large percentages; weight by `prior` and lead with movers on company-scale metrics (ARR, paid teams, active-L7 teams, feature WAT, credits).
- The runner changed its series-key format on 2026-09-10. If `prior_date` is before that, the comparison is invalid — say so and skip Step 1.

## Step 2 — Churn, downgrade, expansion: the monthly trend

```sql
SELECT metric_name, metric_dimension AS month, metric_value
FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS
WHERE domain = 'saved_metrics'
  AND metric_name LIKE 'Churn and Retention by Month/monthly_trend/%'
  AND snapshot_date = (SELECT MAX(snapshot_date) FROM ANALYTICS_DB.JARVIS.LU_METRIC_SNAPSHOTS)
QUALIFY ROW_NUMBER() OVER (PARTITION BY metric_name, metric_dimension ORDER BY snapshot_ts DESC) = 1
ORDER BY month DESC, metric_name
LIMIT 42
```

Read the **rate** (`churn_rate_pct`), not the count: the paying base grows, so `churned_teams` rises even when the rate is flat. Report the last three closed months of rate, churned ARR, downgrade ARR, expansion ARR. The current month is partial — label it.

## Step 3 — Automated assessments and signal statuses

```sql
-- Signals a kernel judged red or yellow in the last 8 days (latest verdict per signal)
SELECT kernel_id, signal_name, status, LEFT(detail, 200) AS detail, metric_value, assessed_at::DATE AS assessed
FROM ANALYTICS_DB.JARVIS.INTELLIGENCE_SIGNAL_RESULTS
WHERE assessed_at >= CURRENT_TIMESTAMP() - INTERVAL '8 days' AND status IN ('red', 'yellow')
QUALIFY ROW_NUMBER() OVER (PARTITION BY kernel_id, signal_name ORDER BY assessed_at DESC) = 1
ORDER BY CASE status WHEN 'red' THEN 0 ELSE 1 END, kernel_id
LIMIT 30
```

`status = 'unknown'` means the kernel could not compute the signal (missing metric) — pipeline noise, not a business signal; never report it as one.

```sql
-- Written assessments for the strategic kernels (latest per kernel, last 8 days)
SELECT kernel_id, assessed_at::DATE AS assessed, intelligence
FROM ANALYTICS_DB.JARVIS.INTELLIGENCE_SNAPSHOTS
WHERE model <> 'mistral-large2'
  AND assessed_at >= CURRENT_TIMESTAMP() - INTERVAL '8 days'
  AND kernel_id IN ('growth_arr_trajectory', 'nrr_segment_weekly', 'apollo_product_health', 'product_engagement_health',
                    'credits_consumption_health', 'credit_utilization_monitoring', 'ai_assistant_adoption', 'ai_platform_growth',
                    'email_deliverability_health', 'aop_ss_funnel', 'conversion_okr_tracking', 'onboarding_hvo_health', 'gtme_enterprise_health')
QUALIFY ROW_NUMBER() OVER (PARTITION BY kernel_id ORDER BY assessed_at DESC) = 1
ORDER BY kernel_id
```

Extract the headline finding and stated risk from each `intelligence` text; do not paste it. Figures inside were computed when the kernel ran — cite `assessed`, and re-query with `/apollo-analytics:metric-lookup` before presenting one as current. **Rows with `model = 'mistral-large2'` are confabulated; the filter is mandatory.** To list all kernels and their freshness, `GROUP BY kernel_id` on the same table.

## Step 4 — Team-level signal shifts

```sql
WITH w AS (
  SELECT signal_week, signal_source, signal_type, COUNT(DISTINCT apollo_team_id) AS teams
  FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS
  WHERE signal_week >= DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '3 weeks'
  GROUP BY 1, 2, 3),
r AS (
  SELECT signal_source, signal_type, signal_week, teams,
         LAG(teams) OVER (PARTITION BY signal_source, signal_type ORDER BY signal_week) AS prior_teams
  FROM w)
SELECT signal_week, signal_source, signal_type, prior_teams, teams,
       ROUND((teams - prior_teams) / NULLIF(prior_teams, 0) * 100, 1) AS wow_pct
FROM r
WHERE signal_week = (SELECT MAX(signal_week) FROM w) AND prior_teams IS NOT NULL
ORDER BY ABS((teams - prior_teams) / NULLIF(prior_teams, 0)) DESC
LIMIT 20
```

Signal types include churn scores, credit drops, WAU drops, seat utilization, support churn-risk and upsell flags, HVO and GTME call themes. `signal_metadata` is already a VARIANT array — `LATERAL FLATTEN(input => signal_metadata)` directly if you need detail; never wrap it in `TRY_PARSE_JSON`. Weeks are Monday-anchored; if the latest week is more than 10 days old, say the aggregation is behind.

## Step 5 — Business state

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/business_state.md` — header, *Immediate Priorities*, *Risks*, and *Escalation Thresholds*. It is the Analytics team's weekly synthesis, dated in its header. Targets: `${CLAUDE_PLUGIN_ROOT}/knowledge/annual_targets.md`. Quote both with their dates.

## Output

> **Weekly Insights — snapshot {latest_date}, vs {prior_date}**
>
> **Top movers (registry metrics, WoW)** — ranked table, ≤ 8 rows: metric, segment, prior → current, %.
>
> **Churn & expansion (last 3 closed months)** — rate, churned ARR, downgrade ARR, expansion ARR.
>
> **Red / yellow signals (kernels, assessed {date})** — one line each: kernel, signal, detail.
>
> **Team signal shifts (week of {date})** — the three or four largest moves and what they usually precede.
>
> **Context (business state as of {date})** — two lines on where ARR / NRR / activation stand against FY27 targets.
>
> **Data notes** — snapshot freshness, any skipped step and why.

Rank, don't list: name the top two items that deserve attention and why. Cap at ten items total. Judge each mover against the thresholds in `${CLAUDE_PLUGIN_ROOT}/knowledge/heuristics.md` (deep-dive vs emergency) and say which row applied.

**Bias & limitations** — one line before the critic hand-off, naming the risk that most threatens the week's read and how it is bounded: selection (only metrics in the registry are in the snapshot — a silent area is unmeasured, not flat), survivorship (teams that churned mid-window leave the denominator and flatter every rate), mix-shift (segment composition moved, not behaviour), or measurement (a snapshot records that the job ran, not that the data advanced). Definitions: `${CLAUDE_PLUGIN_ROOT}/knowledge/analysis_standards.md`.

Before presenting, hand the draft (answer, SQL, result rows, original question) to the `critic` agent when this runtime can run agents, and act on its flags. Where agents are unavailable, apply the checklist in `${CLAUDE_PLUGIN_ROOT}/agents/critic.md` yourself. Offer to drill into any item with `/apollo-analytics:metric-movement` (why it moved) or `/apollo-analytics:product-debrief` (the area).
