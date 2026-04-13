# INT_USER_FIRST_ACTION_DATE

> **First-ever date a user performed each tracked platform action.** Long-format table — one row per user-team-action-event combination. The canonical source for "when did this user first do X?" questions.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.INT_USER_FIRST_ACTION_DATE` |
| **Grain** | One row per `(apollo_user_id, apollo_team_id, action, event_type_id)` |
| **Refresh cadence** | dbt full table rebuild (ad hoc datascience job + scheduled runs) |
| **Trust level** | ANALYTICS_DATASCIENCE schema — dbt-managed, high trust |
| **Owner** | Analytics team (BIA) |
| **dbt model** | `models/marts/data_science/activation_moments/int_user_first_action_date.sql` |

## Description

Tracks the earliest date each user performed ~40+ platform actions, paired with their current `apollo_team_id` from `int_user_team_mapping`. Feeds downstream activation and data science models that need to know "when did this user first unlock or use feature X?"

Two data sources are unioned:
- **`agg_user_activation_events_daily`** — for actions already tracked as activation steps (faster, pre-aggregated)
- **`fct_amplitude_events`** — for all other flagged actions, with optional per-action filters

Which source a given action uses is controlled by the `activation_steps_in_agg` list in the model. New actions not in that list automatically route to `fct_amplitude_events`.

## Upstream Sources

| Source | Role |
|---|---|
| `agg_user_activation_events_daily` | Activation step first dates (pre-aggregated) |
| `fct_amplitude_events` | Non-activation-step first dates (raw Amplitude events) |
| `int_user_team_mapping` | Resolves current `apollo_team_id` for each user |

## Adding New Actions

Controlled entirely by `macros/amplitude/amplitude_event_to_action_mapping.sql`. To add a new action, set `is_used_in_first_action_date_models: true` in the relevant mapping dict. Use the `add-to-user-first-action-date` Jarvis skill — it handles lookup, editing, dbt build, lint, commit, and PR.

## Key Columns

| Column | Type | Description |
|---|---|---|
| `apollo_user_id` | VARCHAR | Apollo user identifier |
| `apollo_team_id` | VARCHAR | User's current team at build time (from `int_user_team_mapping`) |
| `event_type_id` | NUMBER | Amplitude event type ID. NULL for activation-step rows sourced from the agg. |
| `action` | VARCHAR | Snake_case action name (e.g. `sequence_enabled`, `mailbox_linked`) |
| `first_date` | DATE | Earliest calendar date the user performed this action |

## Currently Tracked Actions (~40)

Actions with `is_used_in_first_action_date_models: true` in the mapping macro (as of 2026-04-07):

`sequence_enabled`, `inbound_router_published`, `persona_created`, `finder_view_created`, `scheduled_enrichment_job_executed_crm_living_data`, `calendar_linked`, `meeting_insights_engaged`, `conversation_setup_completed`, `conversation_viewed`, `conversation_summary_pushed_to_crm`, `conversation_follow_up_email_sent`, `conversation_auto_record_setup_completed`, `mailbox_linked`, `chrome_extension_installed`, `workflow_enabled`, `mailbox_ramp_up_completed`, `conversation_ask_apollo_used`, `meeting_link_created`, `meeting_viewed`, `meeting_booked_via_apollo_scheduler`, `note_created`, `note_viewed`, `stage_updated`, `contacts_imported`, `crm_field_mapping_completed`, `default_field_mapping_configured`, `scheduled_enrichment_job_created`, `instant_enrichment_enabled`, `data_health_gap_report_viewed`, `data_writing_rules_configured`, and ~10 more.

## Common Query Patterns

**First date a user enabled a sequence:**

    select apollo_user_id, apollo_team_id, first_date
    from analytics_db.analytics_datascience.int_user_first_action_date
    where action = 'sequence_enabled'

**All first action dates for a specific user:**

    select action, first_date
    from analytics_db.analytics_datascience.int_user_first_action_date
    where apollo_user_id = '<user_id>'
    order by first_date

**Time-to-first-action from signup (join to dim_mongo_users):**

    select
        u.created_at::date as signup_date,
        f.first_date,
        datediff('day', u.created_at::date, f.first_date) as days_to_first_action,
        f.action
    from analytics_db.analytics_datascience.int_user_first_action_date f
    join analytics_db.analytics.dim_mongo_users u
        on f.apollo_user_id = u.user_id
    where f.action = 'mailbox_linked'

## Known Gotchas

- **`apollo_team_id` reflects current team at build time**, not the team the user was on when they first performed the action. Users who have switched teams will show their current team for all historical actions.
- **`event_type_id` is NULL for activation-step rows** sourced from `agg_user_activation_events_daily` — this is expected, not a data quality issue.
- **Not a live table** — reflects the state at last full rebuild. For very recent events, check `fct_amplitude_events` directly.
- **Adding a new action requires a dbt rebuild** to backfill historical first dates. The `first_date` for a newly added action won't appear until the next table rebuild.
