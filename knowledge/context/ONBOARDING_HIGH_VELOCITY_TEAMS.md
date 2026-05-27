# ONBOARDING_HIGH_VELOCITY_TEAMS

> Team-level rollup of High Velocity Onboarding (HVO) sessions. One row per Apollo team.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.ONBOARDING_HIGH_VELOCITY_TEAMS` |
| **Grain** | One row per Apollo team (all HVO sessions collapsed to team grain) |
| **Row count** | ~38,482 (2026-03-19) |
| **Refresh cadence** | Daily (dbt — `models/marts/onboarding/onboarding_high_velocity_teams.sql`) |
| **Trust level** | Use with caution (ANALYTICS schema, dbt-managed) |
| **Owner** | Kaitlyn Maglietto (Analytics Engineering) |
| **DAG** | dbt mart — `models/marts/onboarding/` |

## Description

Team-level view of High Velocity Onboarding (HVO) sessions. While `ONBOARDING_HIGH_VELOCITY_SESSIONS` has one row per meeting, this table collapses all of a team's HVO activity into a single row — capturing first/last/ever metrics across each stage of the HVO funnel (booked → scheduled → held → attended → valid attended). Includes arrays of all meeting IDs, onboarders, participants, and UTMs across every session. Two key fields (`has_team_ever_attended_valid_hvo`, `has_team_ever_booked_hvo`) are promoted onto `DIM_TEAMS` for broad join access. Primary consumers: GTM analytics, onboarding team, revenue analytics joining HVO status to ARR.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS.ONBOARDING_HIGH_VELOCITY_SESSIONS` | Direct upstream — each row in TEAMS aggregates N rows from SESSIONS |
| Calendar events (Apollo Scheduler) | Meeting booking data: who, when, booking source, scheduler type |
| Conversations (Apollo Recorder) | Meeting attendance data: who attended, duration |

## Key Columns

### Identity & Arrays
| Column | Type | Description | Notes |
|---|---|---|---|
| `apollo_team_id` | VARCHAR | PK — team identifier | Joins to DIM_TEAMS, DIM_MONGO_TEAMS, FCT_DAILY_REVENUE |
| `sfdc_account_id` | VARCHAR | SFDC account ID at time of meeting | Joins to DIM_SALESFORCE_ACCOUNTS |
| `calendar_event_ids` | ARRAY | All calendar event IDs for this team's HVO sessions | |
| `primary_onboarders` | ARRAY | All Product Specialists who ran this team's sessions | |
| `apollo_contact_ids` | ARRAY | Contact IDs for all invitees | |
| `apollo_user_ids` | ARRAY | User IDs for all invitees | |

### Funnel Stage — First Occurrence
Each stage has a group of columns: `first_meeting_<stage>_at_utc`, `first_meeting_<stage>_calendar_event_id`, `is_primary_team_on_first_meeting_<stage>`, `primary_team_id_on_first_meeting_<stage>`.

| Stage | Date Column | Notes |
|---|---|---|
| **booked** | `first_meeting_booked_created_at_utc` | Calendar event creation time |
| **scheduled** | `first_meeting_scheduled_at_utc` | Meeting scheduled (booked + not yet rescheduled/cancelled) |
| **held** | `first_meeting_held_start_at_utc` | Meeting held (occurred) |
| **attended** | `first_meeting_attended_start_at_utc` | Customer was present |
| **attended_valid** | `first_meeting_attended_valid_start_at_utc` | Attended AND duration > 15 min |

### Has-Ever Booleans (promoted to DIM_TEAMS)
| Column | Description |
|---|---|
| `has_team_ever_booked_hvo` | True if team ever booked an HVO session (as primary or invited) |
| `has_team_ever_attended_hvo` | True if team ever attended an HVO session |
| `has_team_ever_attended_valid_hvo` | True if team ever had a valid HVO session (>15 min) — **the canonical completion flag** |
| `has_ever_had_cancelled_meeting` | True if any of this team's meetings were cancelled |
| `has_ever_had_rescheduled_meeting` | True if any of this team's meetings were rescheduled |

### Context Flags
| Column | Description |
|---|---|
| `is_core_account_during_meeting` | Was the team a core SFDC account at time of first meeting? |
| `is_on_free_plan_during_meeting` | Was the team on a free plan at time of first meeting? |

### Totals
| Column | Description |
|---|---|
| `count_hvo_meetings` | Total HVO meetings booked/attended by this team |
| `count_apollo_contacts` | Count of unique contacts invited |
| `count_apollo_users` | Count of unique users invited |
| `longest_conversation_duration_minutes` | Duration of the longest attended meeting |

### UTMs & Booking Survey (first meeting)
| Column | Description |
|---|---|
| `first_meeting_utm_campaign/content/medium/source` | UTMs captured from the booking link |
| `first_meeting_utm_onboarding_manager` | Onboarding manager from UTM |
| `first_meeting_response_review_topics` | Customer's stated review topics from booking form |
| `first_meeting_has_selected_*` | Boolean flags for booking form topic selections (link mailbox, contact list, sequences, etc.) |

### Session-Type Sub-Columns
All major funnel columns are duplicated with `_essentials` and `_inbound` suffixes, allowing analysis sliced to specific HVO session types without additional joins.

## How It's Used

### Common query patterns

**Team funnel counts by week** (from Notion example):
```sql
-- Count teams by funnel stage per week
select
    date_trunc(week, first_meeting_booked_created_at_utc) as activity_week,
    count(distinct apollo_team_id) as count_teams_booked,
    count(distinct case when first_meeting_scheduled_at_utc is not null then apollo_team_id end) as count_teams_scheduled,
    count(distinct case when first_meeting_held_start_at_utc is not null then apollo_team_id end) as count_teams_held,
    count(distinct case when first_meeting_attended_valid_start_at_utc is not null then apollo_team_id end) as count_teams_attended_valid
from analytics_db.analytics.onboarding_high_velocity_teams
where activity_week >= '2025-09-01'
group by 1
```

**Join to ARR** (most common pattern per Notion):
```sql
select
    t.apollo_team_id,
    t.has_team_ever_attended_valid_hvo,
    t.first_meeting_attended_valid_start_at_utc,
    d.arr_end_of_current_month
from analytics_db.analytics.onboarding_high_velocity_teams t
left join analytics_db.analytics_datascience.dim_teams d
    on t.apollo_team_id = d.apollo_team_id
```

**Filter to primary teams only** (exclude invited teams from booking counts):
```sql
where is_primary_team_on_first_meeting_booked = true
```

**Join to DIM_SALESFORCE_USERS for rep management chain:**
`first_meeting_attended_primary_onboarder_valid` uses `@apollomail.io` domain and has two known name spelling mismatches vs. SFDC. Use this pattern to resolve:
```sql
from analytics_db.analytics.onboarding_high_velocity_teams hvo
    left join analytics_db.analytics.dim_salesforce_users sfdc
        on lower(sfdc.email) = case
            -- ana.ballesteros@apollomail.io is stored as ana.b@apollo.io in SFDC
            when split_part(lower(hvo.first_meeting_attended_primary_onboarder_valid), '@', 1) = 'ana.ballesteros'
                then 'ana.b@apollo.io'
            -- mauricio.velazquez (HVO) vs mauricio.velasquez (SFDC) - spelling variation
            when split_part(lower(hvo.first_meeting_attended_primary_onboarder_valid), '@', 1) = 'mauricio.velazquez'
                then 'mauricio.velasquez@apollo.io'
            else replace(lower(hvo.first_meeting_attended_primary_onboarder_valid), '@apollomail.io', '@apollo.io')
        end
    left join analytics_db.analytics.dim_salesforce_users mgr
        on mgr.id = sfdc.manager_id
```
`sfdc.*` gives rep-level SFDC fields (name, title, etc.). `mgr.*` gives the rep's manager. Chain further joins on `mgr.manager_id` for skip-level.

**Detecting new apollomail ↔ apollo.io mismatches:**
Run this when the SFDC join produces unexpected NULLs — it surfaces onboarders in HVO that don't resolve to any SFDC user after the standard domain swap:
```sql
select distinct
    hvo.first_meeting_attended_primary_onboarder_valid as hvo_email,
    replace(lower(hvo.first_meeting_attended_primary_onboarder_valid), '@apollomail.io', '@apollo.io') as normalized_email,
    sfdc.id as sfdc_id
from analytics_db.analytics.onboarding_high_velocity_teams hvo
left join analytics_db.analytics.dim_salesforce_users sfdc
    on lower(sfdc.email) = replace(lower(hvo.first_meeting_attended_primary_onboarder_valid), '@apollomail.io', '@apollo.io')
where hvo.first_meeting_attended_primary_onboarder_valid is not null
  and sfdc.id is null
order by 1
```
Any row returned is either a new name mismatch (add a `when` branch to the join above) or a deactivated SFDC user (verify before adding).

### Key consumers
- `DA_TOOL_USER` — automated tool (likely Hex dashboards) drives the bulk of query volume
- GTM Analytics (#gtm-analytics) — onboarding funnel tracking
- Onboarding team (#xfn-high-velocity-onboarding) — operational reporting
- Revenue/OKR analytics — HVO completion joined to ARR cohorts
- DIM_TEAMS — `has_team_ever_attended_valid_hvo` and `has_team_ever_booked_hvo` promoted here

## Known Issues & Gotchas

- **Primary vs. invited teams:** Every team associated with a meeting (not just the booking team) appears in this table. To count only the team that booked the meeting, filter `is_primary_team_on_first_meeting_<stage> = true`. Counting all rows double-counts invited teams.
- **Valid attendance threshold:** "Valid" = customer attended AND meeting duration > 15 minutes. Short attended meetings (customer joined then rescheduled, or PS called a no-show) are excluded. This is the canonical HVO completion definition.
- **Multiple meetings per team:** Teams can reschedule, creating new calendar event IDs. This table collapses all of them — `first_*` columns tell you the earliest occurrence of each funnel stage.
- **Missing from this table:** Teams that were offered HVO but never booked. For top-of-funnel offer data, check with Kaitlyn — additional datasets were planned.
- **ANALYTICS schema trust:** dbt-managed, not ANALYTICS_DATAPLATFORM. Use with normal ANALYTICS schema caution.
- **`first_meeting_attended_primary_onboarder_valid` uses `@apollomail.io` domain**, not `@apollo.io`. When joining to `DIM_SALESFORCE_USERS` on email, normalize with `replace(lower(...), '@apollomail.io', '@apollo.io')`. Two known name spelling mismatches also require special-casing: `ana.ballesteros@apollomail.io` → `ana.b@apollo.io` and `mauricio.velazquez` → `mauricio.velasquez`.
- **Rescheduling creates new IDs:** Rescheduled meetings generate a new calendar event ID; the original meeting is marked `is_meeting_rescheduled = true` in SESSIONS.

## Slack Context

- **Oct 2025:** Kaitlyn announced the HVO dataset in #xfn-data-analytics. Two flags (`has_team_ever_attended_valid_hvo`, `has_team_ever_booked_hvo`) promoted to DIM_TEAMS at the same time.
- **Oct 2025 (#gtm-analytics):** Catherine Zhou asked about the grain — specifically why a team might have multiple meeting IDs (rescheduling creates new IDs, teams can reinvite each other). Kaitlyn confirmed.
- **Nov 2025 (#xfn-high-velocity-onboarding):** Marie Ballenger noted that a lookup by `apollo_team_id` returned no results — the team had attended HTC (High-Touch, not HVO). Teams in HTC won't appear here.
- **Reference:** [Notion conceptual doc](https://www.notion.so/apolloio/High-Velocity-Onboarding-28dab2b3b49680d39a74efb9c02eccdc)

## Business Terms

| Term | Definition |
|---|---|
| HVO (High Velocity Onboarding) | Scalable, group-style live onboarding sessions run by Apollo Product Specialists. Distinct from High-Touch Onboarding (HTC) which is 1:1. |
| Valid Attendance | A meeting where the customer attended AND the session lasted longer than 15 minutes. Sub-15 min sessions are excluded (typically no-shows or immediate reschedules). |
| Primary Team | The team that booked the HVO session via the Apollo Scheduler link. Distinguishes the booking team from teams they invited. |
| Invited Team | Any team associated with an HVO meeting that did not do the booking. |
| HVO Funnel Stages | Booked → Scheduled → Held → Attended → Valid Attended. Each represents a progressively stricter filter on the meeting progressing. |
| Essentials (session type) | A specific HVO session sub-type. Columns with `_essentials` suffix filter to this type only. |
| Inbound (session type) | A specific HVO session sub-type. Columns with `_inbound` suffix filter to this type only. |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file (dbt YAML + Notion doc + Slack) | Will (via Claude) |
