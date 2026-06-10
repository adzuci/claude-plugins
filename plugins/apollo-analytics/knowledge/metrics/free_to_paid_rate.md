# Self-Serve Free-to-Paid Conversion Rate

> **Owner:** Andrew Green (Analytics) / Conversion PM
> **OKR Target:** Average 1.33% W2 free-to-paid conversion rate for all teams
> **Status:** DRAFT

## What this metric measures

Of all self-serve teams that signed up in a given week, what percentage converted to a paying customer by each week after signup? Tracked as a cohort curve from week 0 through week 12.

## What we already have

- `analytics_db.analytics.dim_salesforce_apollo_teams` — signup population, team metadata
- `analytics_db.analytics.dim_salesforce_accounts` — segmentation dimensions (`account_segment`, `is_core_account`, region)
- `analytics_db.analytics.fct_daily_revenue` — first payment detection

## What we need from you

Fill in each section below. Plain language is fine — Claude will convert to SQL.

### 1. Free and paid definition

What qualifies a team as "free", and what counts as their first payment?

- Is "free" any team with no ARR? Does it include teams on free trials?
- What revenue event marks the conversion to paid?
- Any grain considerations (parent vs. child accounts)?

```
YOUR ANSWER:
- **Free:** Any team that has signed up (exists in dim_salesforce_apollo_teams) but has not yet made a payment. Includes free trials.
- **Paid:** First occurrence in fct_daily_revenue where change_category = 'new', is_self_serve = true, and is_parent_account = false — deduplicated to the earliest date per team.
- **is_parent_account scope:** The is_parent_account = false filter applies only within fct_daily_revenue (revenue grain). The signup population is NOT filtered by is_parent_account.

SQL for first_purchase CTE:
, first_purchase as (
    select
        dr.apollo_team_id,
        dr.date_period,
        dr.arr,
        dr.arr_change,
        dr.change_category,
    from analytics_db.analytics.fct_daily_revenue dr
    where
        dr.change_category = 'new'
        and dr.is_self_serve = true
        and dr.is_parent_account = false
    qualify row_number() over (partition by dr.apollo_team_id order by dr.date_period asc) = 1
)
```

### 2. Cohort structure and time window

How are cohorts defined and how long is the conversion window?

- Cohort by signup week? Month?
- How many weeks to track conversion after signup?
- How to handle weeks that haven't fully elapsed yet?

```
YOUR ANSWER:
- **Cohort grain:** Weekly (date_trunc('week', team_created_date)).
- **Window:** 13 weeks (weeks 0–12 since signup).
- **Incomplete weeks:** Only populate conversion metrics when week_end_date <= current_date(). Future weeks show NULL.
- **Start date:** Default 2024-10-01, parameterisable.
```

### 3. Segmentation

What dimensions should this be sliceable by?

- Which columns and tables?
- Any hard filters vs. optional breakdowns?

```
YOUR ANSWER:
- **Segmentation is flexible.** Key dimension: account_segment from analytics_db.analytics.dim_salesforce_accounts.
- **Join path:** dim_salesforce_apollo_teams.sfdc_account_id → dim_salesforce_accounts.id
- Other dimensions (region, is_core_account, etc.) can be added as optional filters as needed.
- is_core_account is available but NOT applied by default — it's an optional filter.
```

### 4. Exclusions

What teams should be excluded from the signup population?

```
YOUR ANSWER:
- **is_suspicious_team = false** — hard filter on dim_salesforce_apollo_teams.
- **has_fraud_abuse_flag = false** — hard filter on dim_salesforce_apollo_teams. ALWAYS exclude fraud/abuse-flagged teams from the FTP denominator. Without this filter, fraudulent signups inflate the denominator and suppress the conversion rate. This is a mandatory filter for the Conversion team's FTP KR — never omit it.
```

### 5. Full reference SQL

```
YOUR ANSWER:
with signups as (
    select
        st.apollo_team_id,
        st.team_created_date,
        st.is_team_verified,
        st.is_suspicious_team,
        sa.is_core_account,
        sa.account_segment,
    from analytics_db.analytics.dim_salesforce_apollo_teams st
    left join analytics_db.analytics.dim_salesforce_accounts sa
        on st.sfdc_account_id = sa.id
    where
        st.team_created_date >= '2024-10-01'
        and st.is_suspicious_team = false
        and st.has_fraud_abuse_flag = false
        -- optional: and sa.is_core_account = true
        -- optional: and sa.account_segment = :segment
)

, first_purchase as (
    select
        dr.apollo_team_id,
        dr.date_period,
        dr.arr,
        dr.arr_change,
        dr.change_category,
    from analytics_db.analytics.fct_daily_revenue dr
    where
        dr.change_category = 'new'
        and dr.is_self_serve = true
        and dr.is_parent_account = false
    qualify row_number() over (partition by dr.apollo_team_id order by dr.date_period asc) = 1
)

, base as (
    select
        s.apollo_team_id,
        s.team_created_date,
        s.account_segment,
        date_trunc('week', s.team_created_date) as cohort_week,
        s.is_team_verified,
        s.is_suspicious_team,
        s.is_core_account,
        fp.date_period as first_purchase_date,
        fp.arr,
        case
            when fp.date_period is not null
            then datediff('week', s.team_created_date, fp.date_period)
            else null
        end as weeks_until_purchase
    from signups s
    left join first_purchase fp
        on s.apollo_team_id = fp.apollo_team_id
)

, week_numbers as (
    select row_number() over (order by seq4()) - 1 as weeks_since_signup
    from table(generator(rowcount => 13))
)

, team_weeks as (
    select
        b.apollo_team_id,
        b.team_created_date,
        b.cohort_week,
        b.account_segment,
        b.is_team_verified,
        b.is_suspicious_team,
        b.is_core_account,
        b.first_purchase_date,
        b.weeks_until_purchase,
        b.arr,
        wn.weeks_since_signup,
        dateadd('week', wn.weeks_since_signup, b.cohort_week) as week_end_date,
        case
            when b.first_purchase_date is not null
                 and b.weeks_until_purchase <= wn.weeks_since_signup
            then 1
            else 0
        end as has_converted_by_week,
        case
            when b.first_purchase_date is not null
                 and b.weeks_until_purchase <= wn.weeks_since_signup
            then b.arr
            else null
        end as arr_converted_by_week
    from base b
    cross join week_numbers wn
    where wn.weeks_since_signup <= 13
)

, cohort_conversion as (
    select
        cohort_week,
        weeks_since_signup,
        max(week_end_date) as week_end_date,
        count(distinct apollo_team_id) as total_teams_in_cohort,
        case
            when max(week_end_date) <= current_date()
            then sum(has_converted_by_week)
            else null
        end as teams_converted_by_week,
        case
            when max(week_end_date) <= current_date()
            then round((sum(has_converted_by_week)::float / count(distinct apollo_team_id)) * 100, 2)
            else null
        end as conversion_rate_pct,
        case
            when max(week_end_date) <= current_date()
            then sum(arr_converted_by_week)
            else null
        end as total_arr_converted_by_week,
        case
            when max(week_end_date) <= current_date()
                 and sum(has_converted_by_week) > 0
            then round(sum(arr_converted_by_week)::float / sum(has_converted_by_week), 2)
            else null
        end as avg_arr_per_converting_team
    from team_weeks
    group by cohort_week, weeks_since_signup
)

select
    cohort_week,
    weeks_since_signup,
    total_teams_in_cohort,
    teams_converted_by_week,
    conversion_rate_pct,
    total_arr_converted_by_week,
    avg_arr_per_converting_team
from cohort_conversion
order by cohort_week, weeks_since_signup
```
