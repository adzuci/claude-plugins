# TEAM_ACTIVATION

> Team-level rollup of activation milestone dates and boolean flags across 57+ Apollo product moments.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_ACTIVATION` |
| **Grain** | One row per team (`apollo_team_id`) — one-time snapshot, no date column |
| **Unique key** | `apollo_team_id` (dbt-tested: unique + not_null) |
| **Refresh cadence** | Daily (dbt-managed) |
| **Trust level** | High — dbt silver layer, built from dim_user_activation with explicit activation moment definitions |
| **Owner** | Data Science (Activation team) |
| **dbt model** | `dbt_apollo/models/marts/data_science/activation_moments/team_activation.sql` |
| **dbt tags** | `activation`, `product_usage`, `silver` |

## Description

For each Apollo team, records **the earliest date any user on that team performed each of 57+ activation moments** — and a boolean flag indicating whether the moment has ever occurred. The source is `dim_user_activation` (user-grain), rolled up to team grain by taking `MIN(first_active_date_<moment>)` across all users on the team. The result is a wide, team-level table: `first_active_date_<moment>` (DATE, nullable) and `has_<moment>_activated` (BOOLEAN) for each moment. Primary use cases: activation funnel analysis, multi-product adoption tracking, and cohort segmentation by which milestone a team has hit.

## Upstream Sources

| Source | Relationship |
|---|---|
| `dim_user_activation` | One row per user, with `first_active_date_*` per moment. Team activation = MIN across all users on the team. |

## Column Structure

This table is wide by design — 2 + (57+ × 2) columns. The structure is uniform:

| Column | Type | Description |
|---|---|---|
| `apollo_team_id` | TEXT | Team identifier. PK. FK to DIM_MONGO_TEAMS, DIM_SALESFORCE_APOLLO_TEAMS. |
| `team_created_date` | DATE | Team creation date (from SFDC). |
| `first_active_date_<moment>` | DATE | Earliest date any user on the team performed this moment. NULL = never. |
| `has_<moment>_activated` | BOOLEAN | `first_active_date_<moment> IS NOT NULL`. True if team has ever hit this moment. |

### Full list of activation moments

Grouped by product area:

**Sequences / Email Outreach**
- `sequence_created`, `sequence_enabled`
- `email_sent_outreach_automatic`, `email_interest_received_outreach_automatic`
- `mailbox_linked`, `mailbox_ramp_up_started`, `mailbox_ramp_up_completed`, `mailbox_warm_up_started`, `mailbox_warm_up_completed`

**Enrichment**
- `enrichment_crm_living_data_executed`
- `manual_enrichment_executed`
- `instant_enrichment_enabled`, `instant_enrichment_executed`
- `scheduled_enrichment_job_created`, `scheduled_enrichment_job_executed`
- `waterfall_enrichment_executed`
- `waterfall_enrichment_data_provider_setup_completed`, `waterfall_enrichment_validation_provider_setup_completed`

**CRM / Data**
- `team_has_crm_connected`
- `crm_field_mapping_completed`
- `data_writing_rules_configured`, `default_field_mapping_configured`
- `data_health_gap_report_viewed`
- `stage_updated`, `record_actioned`

**Prospecting / List Building**
- `finder_view_created`
- `list_building_used`
- `persona_created`
- `contacts_imported`

**Dialer / Conversations**
- `dialer_used`
- `conversation_setup_completed`, `conversation_auto_record_setup_completed`
- `conversation_viewed`, `conversation_summary_pushed_to_crm`
- `conversation_ask_apollo_used`, `conversation_follow_up_email_sent`

**Meetings**
- `meeting_link_created`, `meeting_booked_via_apollo_scheduler`
- `meeting_insights_engaged`, `meeting_viewed`

**AI / Actions**
- `ai_messaging_used`
- `actions_platform_used`
- `power_up_executed`, `contact_power_up_prompt_executed`
- `workflow_enabled`, `workflow_executed`

**Inbound / Routing**
- `inbound_router_published`

**Chrome Extension**
- `chrome_extension_installed`
- `contact_added_to_sequence_via_linked_extension`

**Notes / CRM Activity**
- `note_created`, `note_viewed`

**API**
- `api_key_created`, `oauth_application_created`
- `people_or_company_api_call_attempted`, `people_or_company_api_call_successful`

## How It's Used

### Common query patterns

```sql
-- % of teams that have hit a given activation milestone
select
    count_if(has_sequence_created_activated) as teams_with_sequence,
    count_if(has_waterfall_enrichment_executed_activated) as teams_with_waterfall,
    count(*) as total_teams
from ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_ACTIVATION;

-- Join to revenue table to segment by activation milestone
select
    ta.has_waterfall_enrichment_executed_activated,
    count(distinct r.apollo_team_id) as teams,
    sum(r.arr) as arr
from ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE r
join ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_ACTIVATION ta
    on r.apollo_team_id = ta.apollo_team_id
where r.is_parent_account = false
  and r.date_period = (select max(date_period) from ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE)
group by 1;

-- Days to first activation milestone (time-to-activate analysis)
select
    apollo_team_id,
    datediff('day', team_created_date, first_active_date_sequence_created) as days_to_first_sequence
from ANALYTICS_DB.ANALYTICS_DATASCIENCE.TEAM_ACTIVATION
where first_active_date_sequence_created is not null;
```

```sql
-- HVO adoption curve: week offset from HVO date to first activation milestone
-- Canonical pattern from Hex HVO dashboard
-- week = -1  → team completed the action BEFORE the HVO session (pre-activated)
-- week = 0+  → integer weeks after HVO date
-- week = NULL → team has never completed the action
with hvo_cohort as (
    select
        hvo.apollo_team_id,
        date(hvo.first_meeting_attended_valid_start_at_utc_essentials) as hvo_date
    from analytics_db.analytics.onboarding_high_velocity_teams hvo
    where hvo.first_meeting_attended_primary_onboarder_valid is not null
      and hvo.first_meeting_attended_valid_start_at_utc_essentials is not null
)
select
    hvo.apollo_team_id,
    hvo.hvo_date,
    case
        when ta.first_active_date_record_actioned < hvo.hvo_date then -1
        when ta.first_active_date_record_actioned is not null
            then floor(datediff('day', hvo.hvo_date, ta.first_active_date_record_actioned) / 7)
    end as week_record_actioned,
    -- ... repeat for each moment of interest
    (
        ta.first_active_date_record_actioned is not null
        and ta.first_active_date_chrome_extension_installed is not null
        and ta.first_active_date_mailbox_linked is not null
        and ta.first_active_date_sequence_created is not null
        and ta.first_active_date_finder_view_created is not null
    ) as team_has_all_five_actions
from hvo_cohort hvo
left join analytics_db.analytics_datascience.team_activation ta
    on hvo.apollo_team_id = ta.apollo_team_id;
```

**Five "golden" onboarding moments** tracked in the HVO adoption dashboard:
1. `record_actioned`
2. `chrome_extension_installed`
3. `mailbox_linked`
4. `sequence_created`
5. `finder_view_created`

`team_has_all_five_actions` is the composite completion flag used by the HVO team.

### Key consumers
- Data Science (activation funnel analysis, onboarding research)
- **Hex HVO dashboard** — HVO adoption curve, five golden moments, week-offset analysis (see query pattern above)
- `APOLLO_TEAMS` dbt model (used as the `team_activation` CTE — supplies activation flags for Account360 Looker explore)
- Product Analytics (multi-product adoption, cohort analysis)

## Known Issues & Gotchas

- **No date column — current state only.** This is a snapshot of all-time activation. There is no way to filter to "teams activated within the last 30 days" without joining to `team_created_date` and using the `first_active_date_*` columns.
- **NULL means never, not unknown.** A NULL `first_active_date_*` means no user on that team has ever hit that moment — not a data gap.
- **Team grain, not user grain.** The minimum across all users determines the team-level date. A team is "activated" on a moment if even one user has done it.
- **`new_records_saved` in yml but not in SQL.** The yml documents `first_active_date_new_records_saved` / `has_new_records_saved_activated`, but these columns are not in the SQL's activation_moments list. They may be generated by a separate source or the yml is ahead of the implementation — verify before querying.
- **Wide table.** ~116+ columns (2 + 57 moments × 2). Avoid `SELECT *` in production queries.
- **Clustered on `apollo_team_id`**, not a date column — no date-based pruning. Point lookups by team ID are fast; full scans are not.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file — dbt model + yml review, upstream tracing, activation moment inventory | Will (via Jarvis) |
