# FCT_ML_PREDICTIONS_PAID_CHURN_12W

> ML model predictions for paid team churn within 12 weeks.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_ML_PREDICTIONS_PAID_CHURN_12W` |
| **Grain** | One row per team-prediction |
| **Row count** | ~6.4M (2026-03-06) |
| **Refresh cadence** | Unknown — likely batch ML inference pipeline. |
| **Trust level** | Use with caution (ANALYTICS schema, ML predictions) |
| **Owner** | Data Science |
| **DAG** | Likely `ml_training` pipeline. Config: `dags/ml_training/config/ml_configs/free_to_paid_hazard_inference.yml` (related). |

## Description

12-week churn predictions for paid teams (15 distinct users). ML model output used for proactive retention (DCS team). Powers the churn risk scoring that feeds customer success workflows.

## Derived Fields (rating + color)

The raw table only has `team_health_score` (a float between 0 and 1). The dbt model `team_health_scoring_12w` derives two additional fields that appear in Looker and in `APOLLO_TEAMS`:

| Derived field | Type | Logic |
|---|---|---|
| `team_health_rating` | integer 0–3 | `score * 100 < 25` → 0, `< 50` → 1, `< 75` → 2, `≥ 75` → 3 |
| `team_health_color` | string | 0 → `'Red'`, 1 → `'Orange'`, 2 → `'Yellow'`, 3 → `'Green'` |

To reproduce these when querying the raw table directly:

```sql
case
    when (team_health_score * 100) < 25 then 'Red'
    when (team_health_score * 100) < 50 then 'Orange'
    when (team_health_score * 100) < 75 then 'Yellow'
    else 'Green'
end as team_health_color
```

**Getting the current snapshot:** The table is historical (one row per team per prediction run). To get the latest score per team, filter to `MAX(prediction_date)`:

```sql
select *
from ANALYTICS_DB.ANALYTICS.FCT_ML_PREDICTIONS_PAID_CHURN_12W
where prediction_date = (select max(prediction_date) from ANALYTICS_DB.ANALYTICS.FCT_ML_PREDICTIONS_PAID_CHURN_12W)
```

This is exactly what the dbt view `team_health_scoring_12w_latest` does.

**Note:** Health score is only meaningful for paid teams.

## Slack Context

- DCS Weekly Scoreboard requested by Rob Statsky — churn predictions feed VSB/SMB retention targeting

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
