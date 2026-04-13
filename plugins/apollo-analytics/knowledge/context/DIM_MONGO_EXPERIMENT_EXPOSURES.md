# DIM_MONGO_EXPERIMENT_EXPOSURES

> Canonical source for user-level experiment exposure events from MongoDB. Records when a user was assigned to an experiment variant.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_EXPERIMENT_EXPOSURES` |
| **Grain** | One row per user × experiment flag × exposure event (multiple exposures per user possible) |
| **Row count** | <!-- TODO: check live --> |
| **Refresh cadence** | Daily (ANALYTICS_DATAPLATFORM pipeline) |
| **Trust level** | Authoritative — use this, not FCT_AMPLITUDE_EVENTS, for experiment exposure |
| **Owner** | Pubudu Wariyapola (Data Science — AI Product Analytics) |
| **DAG** | <!-- TODO: confirm Airflow DAG name --> |

## Description

Tracks every instance of a user being exposed to an A/B experiment variant. The source is MongoDB experiment assignment records. Because exposure is recorded at the user level, all analysis must be aggregated to team level via `DIM_USERS`. Variant-hopping (teams exposed to both control and treatment) is a known data quality issue and must always be excluded. The canonical pattern is to find each team's first exposure datetime and use that as the start of the post-exposure outcome window.

Primary consumers: Data Science (Pubudu, Andrew Green), the `analyze-experiment` skill.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB experiment assignment events | Raw source — records written when Statsig/Amplitude assigns a user to a variant |
| `ANALYTICS_DATASCIENCE.DIM_USERS` | Required join to translate `user_id` → `apollo_team_id` |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `flag_key` | VARCHAR | Experiment identifier | e.g. `ai-default-fields-with-auto-enrichment-second-iteration`. Case-sensitive. |
| `user_id` | VARCHAR | Apollo user ID at exposure time | Joins to `DIM_USERS.apollo_user_id` — do NOT join directly to team tables |
| `exposure_variant` | VARCHAR | Variant assigned to this user | Typically `control` / `treatment`; multi-arm experiments may have others |
| `created_at_utc` | TIMESTAMP | When the exposure was recorded | Multiple rows per user are possible — always use `MIN()` for first exposure |

## How It's Used

### Standard query pattern — team-level, variant-hopper excluded

All experiment analysis must follow this pattern. Do not deviate.

```sql
with exposed_teams as (
    select      du.apollo_team_id
                , count(distinct exp.exposure_variant) as variant_count
    from        analytics_db.analytics_dataplatform.dim_mongo_experiment_exposures exp
    join        analytics_db.analytics_datascience.dim_users du
                    on du.apollo_user_id = exp.user_id
    where       exp.flag_key = '<flag_key>'
      and       du.apollo_team_id != '551e3ef07261695147160000'  -- exclude Apollo internal
    group by    1
    having      variant_count = 1   -- exclude variant-hoppers
),
first_exposure as (
    select      et.apollo_team_id
                , exp.exposure_variant
                , min(exp.created_at_utc) as first_exposure_datetime
    from        exposed_teams et
    join        analytics_db.analytics_datascience.dim_users du
                    on du.apollo_team_id = et.apollo_team_id
    join        analytics_db.analytics_dataplatform.dim_mongo_experiment_exposures exp
                    on exp.user_id = du.apollo_user_id
                    and exp.flag_key = '<flag_key>'
    group by    1, 2
)
```

### Key consumers

- `analyze-experiment` skill — uses this as the exposure source for all standard experiment read-outs
- Pubudu Wariyapola — AI product A/B experiments (AI Assistant, AI Messaging, AI Qualification)
- Andrew Green — general product experimentation

## Known Issues & Gotchas

- **Variant-hoppers must always be excluded** — teams whose users were exposed to multiple variants produce contaminated results. Always apply `HAVING COUNT(DISTINCT exposure_variant) = 1` at the team level.
- **Grain is user-level, not team-level** — you must join to `DIM_USERS` to get `apollo_team_id`. Do not assume `user_id` maps directly to a team.
- **Multiple exposures per user** — a user may have many rows for the same `flag_key`. Always use `MIN(created_at_utc)` as `first_exposure_datetime`.
- **Case-sensitive flag_key** — experiment identifiers are exact strings. A wrong flag_key returns zero rows silently.
- **Never use FCT_AMPLITUDE_EVENTS for exposure** — Amplitude experiment assignment events exist there too, but `DIM_MONGO_EXPERIMENT_EXPOSURES` is the canonical source for Snowflake-based analysis.
- **Apollo internal team must be excluded** — always filter out `apollo_team_id = '551e3ef07261695147160000'` and `website_domain = 'apollo.io'`.

## Slack Context

- Pubudu has consistently flagged that FCT_AMPLITUDE_EVENTS should not be used for exposure — always use this table instead.

## Business Terms

| Term | Definition |
|---|---|
| `flag_key` | The experiment identifier string, sourced from Statsig/Amplitude. Identifies a unique A/B test. |
| `exposure_variant` | The arm of the experiment a user was assigned to (e.g. `control`, `treatment`). |
| Variant-hopper | A team whose users were exposed to more than one variant — excluded from all analysis to prevent contamination. |
| First exposure datetime | `MIN(created_at_utc)` at team level — used as day 0 for all post-exposure outcome windows. |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Created context file — schema from Pubudu's data_sources.md + analyze-experiment skill | Jarvis |
