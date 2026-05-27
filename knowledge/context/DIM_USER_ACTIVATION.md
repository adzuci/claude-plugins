# DIM_USER_ACTIVATION

> Data Science dimension: first calendar date each user hit tracked activation steps (PLG / product milestones), plus team context.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USER_ACTIVATION` |
| **Grain** | One row per Apollo user (`APOLLO_USER_ID`) |
| **Row count** | ~15.9M (2026-03-27 spot check); same order of magnitude as `DIM_USERS` / all-users spine |
| **Refresh cadence** | Daily (dbt table; large warehouse in model config) |
| **Trust level** | Use with caution (`ANALYTICS_DATASCIENCE` — DS-maintained; validate definitions via upstream agg + activation sheet) |
| **Owner** | Data Science (Shyam SK / Tara Crabtree) |
| **DAG** | Not in airflow-dags. Built by dbt (`dbt_apollo`). |
| **dbt model** | `models/marts/data_science/activation_moments/dim_user_activation.sql` |

## Description

Wide user-level table: for each user, **first `event_date`** per **activation step** (50+ date columns of the form `FIRST_ACTIVE_DATE_<STEP>`), keyed off `AGG_USER_ACTIVATION_EVENTS_DAILY`. Also includes `APOLLO_USER_CREATED_DATE`, `APOLLO_TEAM_ID`, `TEAM_CREATED_DATE`, and **`FIRST_ACTIVE_DATE_TEAM_HAS_CRM_CONNECTED`** (earliest day the user’s team had any CRM integration active on the daily agg — different semantics from step columns).

**Not boolean flags:** each milestone is a **DATE or NULL** (NULL = no qualifying event in upstream daily data). Downstream models may derive booleans (e.g. `team_activation`).

Primary uses: activation funnels, time-to-first-action, cohort analyses, Hex “Activation Moments” dashboards, and selective joins into core entities (e.g. finder view → `apollo_users`).

## Upstream Sources

| Source | Relationship |
|---|---|
| `INT_ALL_USERS_UNIFIED` | User spine; `APOLLO_USER_ID`, `APOLLO_USER_CREATED_DATE` |
| `INT_USER_TEAM_MAPPING` | `APOLLO_TEAM_ID`, `TEAM_CREATED_DATE` |
| `AGG_USER_ACTIVATION_EVENTS_DAILY` | Daily user × step activity; **source of truth** for step names and golden/setup/aha/habit classification flags. Step definitions and hierarchy: [activation moments sheet](https://docs.google.com/spreadsheets/d/1K8qL6p1Ee2cNG_ajGW2eUOfKpA_cmJ_2vY3sgA34bOc/edit?gid=0#gid=0) (linked from dbt docs on the agg model). |

**Special logic:** `FIRST_ACTIVE_DATE_TEAM_HAS_CRM_CONNECTED` = min `EVENT_DATE` where `HAS_ANY_CRM_INTEGRATION = TRUE` on `AGG_USER_ACTIVATION_EVENTS_DAILY` for that user.

## Key Columns

| Column | Description | Notes |
|---|---|---|
| `APOLLO_USER_ID` | User primary key | Unique; join key |
| `APOLLO_USER_CREATED_DATE` | User creation date | From `INT_ALL_USERS_UNIFIED` |
| `APOLLO_TEAM_ID` | Team FK | From `INT_USER_TEAM_MAPPING`; may be NULL |
| `TEAM_CREATED_DATE` | Team creation date | |
| `FIRST_ACTIVE_DATE_<ACTIVATION_STEP>` | First day that step fired | Snake step name matches `ACTIVATION_STEP` on daily agg. **NULL** = never observed. |
| `FIRST_ACTIVE_DATE_NEW_RECORDS_SAVED` | First “new records saved” | Renamed from upstream step `total_new_records_saved` for clarity |
| `FIRST_ACTIVE_DATE_TEAM_HAS_CRM_CONNECTED` | First day team had CRM connected | Team-level signal rolled to user grain; not the same as other step columns |

High-traffic dimensions for segmentation (join out): `DIM_USERS`, `DIM_TEAMS`, `DIM_SALESFORCE_*`, `DIM_MONGO_*` — same patterns as other DS user tables.

### Snowflake usage (90-day landscape, internal scan)

Reference: `domain/dim_table_infrastructure.md` — ~**4.9k queries**, **~21 distinct users**, **50+ first-event-date columns**. Heavier than niche dims; lighter than `DIM_USERS` / `DIM_TEAMS_DAILY`.

## Downstream / Lineage (dbt)

| Model | Role |
|---|---|
| `team_activation` | Rolls user first dates up to team (min per team); adds `HAS_<STEP>_ACTIVATED`; filters `APOLLO_TEAM_ID IS NOT NULL` |
| `user_activation_aha_moments` | Subset of columns remapped by product pillar (enrichment / genpipe / win_close) |
| `apollo_users` | Exposes `HAS_FINDER_VIEW_CREATED` from `FIRST_ACTIVE_DATE_FINDER_VIEW_CREATED` (Salesforce / Looker-facing) |

## How It's Used

### Common query patterns

- **Time to first action:** `DATEDIFF(day, APOLLO_USER_CREATED_DATE, FIRST_ACTIVE_DATE_<STEP>)`
- **Ever activated:** `FIRST_ACTIVE_DATE_<STEP> IS NOT NULL`
- **Team-level adoption:** Prefer `TEAM_ACTIVATION` or aggregate this table with `MIN()` / `MAX()` over users on a team
- **Joins:** `APOLLO_USER_ID` → `DIM_USERS`, `DIM_MONGO_USERS`; `APOLLO_TEAM_ID` → `DIM_TEAMS` / SF team bridge

### Key consumers

- Data Science & product analytics (activation, PLG)
- **Hex:** [Activation Moments](https://app.hex.tech/apollo/app/Activation-Moments-030L9oc8iJdURBNXpKR9PP/latest), [Sai’s Activation Moments](https://app.hex.tech/apollo/app/Sais-Activation-Moments-032MPBXarcvSPcs0sn9UrP/latest); [DIM Use](https://app.hex.tech/apollo/app/DIM-Use-032UBJYBgkLTNdM4I1BF12/latest) (confirm SQL sources in-app)
- Ad hoc Snowflake (often alongside onboarding / signals tables per user profiles)
- Looker (indirect): via `APOLLO_USERS` for finder-view activation

## When to use this vs alternatives

| Need | Prefer |
|---|---|
| First time user ever did step X | `DIM_USER_ACTIVATION` |
| Activity on a specific day / daily counts | `AGG_USER_ACTIVATION_EVENTS_DAILY` (or other daily facts) |
| Team “any user did X yet?” | `TEAM_ACTIVATION` or roll up from this table |
| Long-format KPIs by day and segment | `PRODUCT_METRICS_DAILY` (different grain) |

## Known Issues & Gotchas

- **NULL on a `FIRST_ACTIVE_DATE_*` column** means no event in the upstream daily model — not “unknown” or “excluded.”
- **Team columns:** If `APOLLO_TEAM_ID` is NULL, team-scoped rollups are wrong unless you filter or left-join intentionally (`TEAM_ACTIVATION` requires non-null team).
- **CRM column semantics:** `FIRST_ACTIVE_DATE_TEAM_HAS_CRM_CONNECTED` is derived from team CRM integration flags on the daily agg, not a generic “user connected CRM” step column.
- **Schema changes:** New steps require edits to `dim_user_activation.sql` (`activation_steps` list) and consistent population in `AGG_USER_ACTIVATION_EVENTS_DAILY` plus dbt docs.
- **DE roadmap:** Internal DE docs reference **`LU_USER_ACTIVATION_MILESTONES`** as a successor pattern for some heavy `DIM_USER_ACTIVATION` consumption — verify current status before large new dependencies.

## Slack Context

- Catherine Zhou raised need for more activation columns (CSV enrichment, inbound, agentic outbound) — DS team controls schema (#dept-analytics)
- Same row count order as `DIM_USERS` / all-users spine — one row per user in universe, not “only activated users”

## Business Terms

| Term | Definition |
|---|---|
| Activation step | Named product behavior in the activation framework (setup, aha, habit, golden moments); see activation spreadsheet |
| First active date | Earliest calendar day the step recorded activity in `AGG_USER_ACTIVATION_EVENTS_DAILY` |
| Golden / setup / aha / habit | Moment categories defined on the daily agg model and spreadsheet — not separate columns on this dim |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
| 2026-03-27 | Expanded: grain, upstream/downstream, usage, Hex links, gotchas, corrected boolean misstatement; row count refresh | Tara Crabtree |
