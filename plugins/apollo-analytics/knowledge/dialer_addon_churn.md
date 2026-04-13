# Dialer Add-On Churn Tracker

**Owner:** Anvitha | **Updated:** 2026-03-27

Identifies teams that have churned from the Dialer add-on product. Same daily-snapshot methodology as [`inbound_addon_churn.md`](inbound_addon_churn.md) but filters for `%dialer%` plans. Also calculates `num_days_used_dialer_add_on` (days between plan start and last active date) for each churned team.

## Key details

- **Churn definition:** last active date > 2 days before `CURRENT_DATE` (buffer for data lag / table refresh)
- **Extra output column:** `num_days_used_dialer_add_on` — tenure on the dialer add-on before churn
- **ARR:** hard-coded monthly $149×12, yearly $119×12 (no quarterly cadence in this query)
- Same test team exclusions and opportunity matching logic as the inbound queries

## Tables used

| Table | Schema | Purpose |
|-------|--------|---------|
| `dim_salesforce_apollo_teams` | `analytics` | Team metadata, SFDC linkage |
| `dim_salesforce_accounts` | `analytics` | Core account flag |
| `dim_mongo_teams_rt_vw` | `analytics_dataplatform` | Real-time dialer plan data (product_infos) |
| `dim_salesforce_opportunities` | `analytics` | Closed-won opps for sales motion matching |
| `raw_fivetran_db.salesforce.opportunity` | raw | `products_sold_c` field |

## Query

```sql
with params as (
  select
    to_date('2025-10-01') as start_on,
    current_date() as end_on
),

all_teams as (
    select
        sat.apollo_team_id,
        sat.created_date::date as team_created_date,
        sat.website_domain,
        sat.team_name,
        sa.is_core_account,
        sat.team_edition
    from analytics_db.analytics.dim_salesforce_apollo_teams sat
    left join analytics_db.analytics.dim_salesforce_accounts sa
      on sat.sfdc_account_id = sa.id
),
real_time_inbound_plans as (
    select
        mt._id as apollo_team_id,
        team_created_date,
        at.is_core_account,
        at.website_domain,
        at.team_name,
        at.team_edition,
        pf.value:"plan_id"::string as plan_id,
        pf.value:"start_date"::date as start_date,
        pf.value:"end_date"::date as end_date,
        pf.value:"canceled_at"::date as canceled_at
    from analytics_db.analytics_dataplatform.dim_mongo_teams_rt_vw mt
    cross join lateral flatten(input => mt.product_infos) as pf
    inner join all_teams at
      on mt._id = at.apollo_team_id
    where pf.value:"plan_id"::string ilike '%dialer%'
    and mt._id != '68e6fb07946dcf000d2e3516' -- jerry test team
    and mt._id != '620210171b9d04008e2ac0e0' -- Apollo eng fraud admin
),

date_spine_params as (
  select
    start_on,
    end_on,
    datediff('day', start_on, end_on) + 1 as num_days
  from params
),
date_spine as (
  select
    dateadd(day, seq4(), dsp.start_on) as as_of_date
  from date_spine_params dsp,
       table(generator(rowcount => 10000))
  where seq4() < dsp.num_days
),

plan_normalized as (
  select
    r.*,
    case
      when plan_id ilike '%monthly%' then 'monthly'
      when plan_id ilike '%yearly%'  then 'yearly'
      else 'unknown'
    end as billing_cadence,
  from real_time_inbound_plans r
),

plan_priced as (
  select
    pn.*,
    case
      when billing_cadence='monthly' then 149*12 --hard code price will not scale with discounts
      when billing_cadence='yearly' then 119*12 -- hard code price will not scale with discounts
      else null
    end as annualized_arr
  from plan_normalized pn
),

closed_won_opportunities as (
    select
        so.closed_won_at::date as closedate,
        so.type,
        so.arr_c,
        so.sales_motion_c,
        sat.apollo_team_id,
        ro.products_sold_c
    from analytics_db.analytics.dim_salesforce_opportunities so
    left join analytics_db.analytics.dim_salesforce_apollo_teams sat
        on so.account_id = sat.sfdc_account_id
    left join raw_fivetran_db.salesforce.opportunity ro
        on so.id = ro.id
    where so.is_won = true
        and so.is_closed = true
        and sat.apollo_team_id is not null
),

matched_opportunities as (
    select
        cwo.apollo_team_id,
        pp.start_date as inbound_start_date,
        cwo.arr_c as opportunity_arr,
        cwo.products_sold_c,
        case when cwo.sales_motion_c = 'Self-Serve' then 'Self-Serve' else 'Rep-Led' end as sales_motion_label,
        case when cwo.sales_motion_c != 'Self-Serve' or cwo.sales_motion_c is null then 1 else 2 end as rep_led_priority,
        case
            when cwo.type = 'New Business' then 1
            when cwo.type = 'Upsell' then 2
            when cwo.type = 'Renewal' then 3
            else 4
        end as type_priority
    from closed_won_opportunities cwo
    inner join plan_priced pp
        on cwo.apollo_team_id = pp.apollo_team_id
        and abs(datediff(day, cwo.closedate, pp.start_date)) <= 1
),

ranked_opportunities as (
    select
        *,
        row_number() over (
            partition by apollo_team_id, inbound_start_date
            order by rep_led_priority asc, type_priority asc, opportunity_arr desc
        ) as priority_rank
    from matched_opportunities
),

top_opportunity_per_plan as (
    select
        apollo_team_id,
        inbound_start_date,
        sales_motion_label,
        products_sold_c
    from ranked_opportunities
    where priority_rank = 1
),

first_sales_motion_per_team as (
    select
        apollo_team_id,
        sales_motion_label,
        products_sold_c,
        row_number() over (
            partition by apollo_team_id
            order by inbound_start_date asc
        ) as rn
    from top_opportunity_per_plan
),
team_persisted_sales_motion as (
    select
        apollo_team_id,
        sales_motion_label,
        products_sold_c
    from first_sales_motion_per_team
    where rn = 1
),

plans_with_sales_motion as (
    select
        pp.*,
        coalesce(tpsm.sales_motion_label, 'Self-Serve') as sales_motion_label,
        tpsm.products_sold_c
    from plan_priced pp
    left join team_persisted_sales_motion tpsm
        on pp.apollo_team_id = tpsm.apollo_team_id
),

daily_snapshot as (
  select
    d.as_of_date,
    p.apollo_team_id,
    p.team_name,
    p.website_domain,
    p.is_core_account,
    p.team_created_date,
    p.team_edition,
    p.plan_id,
    p.billing_cadence,
    p.start_date,
    p.end_date,
    p.canceled_at,
    case
      when p.start_date <= d.as_of_date
       and coalesce(p.canceled_at, p.end_date, '9999-12-31') > d.as_of_date
      then 1 else 0 end as is_active,
    p.annualized_arr,
    p.sales_motion_label,
    p.products_sold_c
  from date_spine d
  join plans_with_sales_motion p
    on p.start_date <= d.as_of_date
    and coalesce(p.canceled_at, p.end_date, '9999-12-31') > d.as_of_date
),

adding_last_active_date as (
  select
    apollo_team_id,
    team_name,
    start_date,
    sales_motion_label,
    max(annualized_arr) as arr,
    max(as_of_date) as max_date_active
  from daily_snapshot
  group by all
)

select
    *,
    datediff('day', start_date, max_date_active) as num_days_used_dialer_add_on
from adding_last_active_date
where 1=1
    and max_date_active < current_date - 2 -- Churn logic - Adding 2 day buffer in case of data lag/table refresh
```
