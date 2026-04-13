# F14D Habit RA Rate

> **Owner:** Adhiraj (O&A)
> **OKR Target:** 12.2% -> 17%
> **Status:** APPROVED — deployed to LU_SAVED_METRICS (2026-03-18). Two variants: weekly_cohort (all teams) and golden_pop_weekly (SMB+, AMER/EMEA, non-freemail).

## What this metric measures

First-14-day Habit Record Actioned rate. Percent of Golden Population (SMB+) teams that perform Record Actions on 4 distinct dates within 14 days of signup.

## What we already have

- `FCT_TEAM_ACTIVITY_DAILY` — daily activity events per team
- `LU_TEAM_ATTRIBUTES` — team metadata (segment, market tier, created date, freemail flag)
- Stub SQL with the skeleton logic

## What we need from you

Fill in each section below. Plain language is fine — Claude will convert to SQL.

### 1. Golden Population filter

Which teams qualify as "Golden Population"?

- SMB+ meaning: `account_segment` in ('SMB', 'Mid-Market', 'Enterprise')? Or based on `market_segment_tier`?
- AMER/EMEA only? Which region column?
- Non-freemail — is this `is_freemail = false` on `LU_TEAM_ATTRIBUTES`?
- Any other filters? (e.g., minimum seats, exclude internal/test?)

```
YOUR ANSWER:
- **Golden Population (optional filter):** When filtering for Habit RA reporting, restrict to AMER/EMEA using `account_region`. Not required to measure Habit RA itself.
- **SMB+ (optional filter):** When filtering for Habit RA reporting, use `account_segment` in ('SMB', 'Mid-Market', 'Enterprise'). Not required to measure Habit RA itself.
- **Freemail (optional filter):** Can filter on non-freemail (e.g. `is_freemail = false` on LU_TEAM_ATTRIBUTES) for reporting, but not required to measure Habit RA.
- **Other exclusions:** None.
```

### 2. Record Action definition

What counts as a "Record Action"?

- Which `event_type` or `event_type_id` values in `FCT_TEAM_ACTIVITY_DAILY`?
- If there's a list of qualifying events, paste it or point us to the source doc.
- Does it matter which object was actioned (contact, account, lead)?

```
YOUR ANSWER: Need to trace this logic from @Jeffrey Alexovich's hex notebook here (effectively DIM_TEAMS_DAILY logic).

team_activation_events as (
    -- Calculate habit RA metric: sum of record_actions in first 14 days
    -- Habit RA = 1 if total_record_actions >= 4, else 0
    select
        teams_with_created_date.apollo_team_id
        , sum(coalesce(dtd.genpipe_feature_record_actioned_user_counts_l1, 0)) as total_record_action_days  -- << THIS IS IMPORTANT: Counts total days
    from teams_with_created_date
    inner join analytics_db.analytics_datascience.dim_teams_daily as dtd
        on teams_with_created_date.apollo_team_id = dtd.apollo_team_id
        and dtd.date >= teams_with_created_date.team_created_date
        and dtd.date < dateadd(day, 14, teams_with_created_date.team_created_date)
    where teams_with_created_date.apollo_team_id is not null
    group by teams_with_created_date.apollo_team_id
),
teams_with_habit_ra as (
    -- Assign habit RA flag to teams
    select
        teams_with_created_date.apollo_team_id
        , teams_with_created_date.apollo_user_id
        , teams_with_created_date.team_created_date
        , teams_with_created_date.has_full_data
        , coalesce(accounts_with_segment.company_type_simplified, 'Unknown') as company_type_simplified
        , case
            when coalesce(team_activation_events.total_record_action_days, 0) >= 4 then 1    -- << THIS IS IMPORTANT: Filter by >= 4 total days
            else 0
        end as is_habit_ra
    from teams_with_created_date
    left join team_activation_events
        on teams_with_created_date.apollo_team_id = team_activation_events.apollo_team_id
    left join accounts_with_segment
        on teams_with_created_date.sfdc_account_id = accounts_with_segment.sfdc_account_id
),


```

### 3. 14-day window

How is the 14-day window defined?

- Calendar days from `team_created_at`? Or from first login?
- Business days or calendar days?
- Include day 0 (signup day) or start counting from day 1?
- Include teams that churn within 14 days?

```
YOUR ANSWER: Calendar days, where day 0 is team create.

```

### 4. Threshold and grain

Confirming the activation threshold and reporting grain:

- 4+ Record Actions within the window = activated. Correct?
- Report as weekly cohorts? Monthly? Rolling?
- Rate = activated teams / total qualifying teams in the cohort?

```
YOUR ANSWER: 4+ distinct record action days within the window = activated.  Reporting periods must be flexible.  There's more nuance around "qualifying teams" but start with "vs created teams to start" (unless you want to open the "qualified" can of worms now -- @Jeffrey Alexovich can assist.

```

### 5. Anything else

Anything we're missing or getting wrong?

```
YOUR ANSWER:

```
