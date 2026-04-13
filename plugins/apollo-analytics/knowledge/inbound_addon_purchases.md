# Inbound Add-On Purchases

**Owner:** Anvitha | **Updated:** 2026-03-27

Weekly purchase volume for the Inbound add-on, broken down by account segment and sales motion. Uses the same real-time Mongo plan extraction and SFDC opportunity matching as the churn query, but focuses on the most recent plan start per team and aggregates by week.

## Key details

- **Output:** weekly team counts by `account_segment`, `sales_motion_label`
- **Deduplication:** `dense_rank` on `start_date desc` per team — only the most recent plan per team is counted
- Includes `quarterly` billing cadence (priced at $149×12, based on evidence from team `6920f0d1eafa03001112604f`)
- Same hard-coded ARR, test team exclusions, and opportunity matching logic as [`inbound_addon_churn.md`](inbound_addon_churn.md)

## Tables used

| Table | Schema | Purpose |
|-------|--------|---------|
| `dim_salesforce_apollo_teams` | `analytics` | Team metadata, SFDC linkage |
| `dim_salesforce_accounts` | `analytics` | Core account flag, segment, tier |
| `dim_mongo_teams_rt_vw` | `analytics_dataplatform` | Real-time inbound plan data (product_infos) |
| `dim_salesforce_opportunities` | `analytics` | Closed-won opps for sales motion matching |
| `raw_fivetran_db.salesforce.opportunity` | raw | `products_sold_c` field |

## Query

```sql
with params as (
    select
        to_date('2025-10-01') as start_on
        , current_date()      as end_on
)

, all_teams as (
    select
        sat.apollo_team_id
        , sat.created_date::date           as team_created_date
        , sat.website_domain
        , sat.team_name
        , sa.is_core_account
        , sat.team_edition
        , sa.account_segment
        , sa.account_sales_department_tier as tier
    from analytics_db.analytics.dim_salesforce_apollo_teams as sat
    left join analytics_db.analytics.dim_salesforce_accounts as sa
        on sat.sfdc_account_id = sa.id
)

, real_time_inbound_plans as (
    select
        mt._id                         as apollo_team_id
        , team_created_date
        , at.is_core_account
        , at.website_domain
        , at.team_name
        , at.team_edition
        , at.account_segment
        , at.tier
        , pf.value:"plan_id"::string   as plan_id
        , pf.value:"start_date"::date  as start_date
        , pf.value:"end_date"::date    as end_date
        , pf.value:"canceled_at"::date as canceled_at
    from analytics_db.analytics_dataplatform.dim_mongo_teams_rt_vw as mt
    cross join lateral flatten(input => mt.product_infos) as pf
    inner join all_teams as at
        on mt._id = at.apollo_team_id
    where pf.value:"plan_id"::string ilike '%inbound%'
        and mt._id != '68e6fb07946dcf000d2e3516' -- jerry test team
        and mt._id != '620210171b9d04008e2ac0e0' -- Apollo eng fraud admin
)

, date_spine_params as (
    select
        start_on
        , end_on
        , datediff('day', start_on, end_on) + 1 as num_days
    from params
)

, date_spine as (
    select dateadd(day, seq4(), dsp.start_on) as as_of_date
    from date_spine_params as dsp
    , table(generator(rowcount => 10000))
    where seq4() < dsp.num_days
)

, plan_normalized as (
    select
        r.*
        , case
            when r.plan_id ilike '%monthly%' then 'monthly'
            when r.plan_id ilike '%yearly%' then 'yearly'
            when r.plan_id ilike '%quarterly%' then 'quarterly'
            else 'unknown'
        end as billing_cadence
    from real_time_inbound_plans as r
)

, plan_priced as (
    select
        pn.*
        , case
            when pn.billing_cadence = 'monthly' then 149 * 12 --hard code price will not scale with discounts
            when pn.billing_cadence = 'yearly' then 119 * 12 -- hard code price will not scale with discounts
            when pn.billing_cadence = 'quarterly' then 149 * 12 -- evidence from 447 inbound fee at billing interval of 3 months from team: On Location (6920f0d1eafa03001112604f)
        end as annualized_arr
    from plan_normalized as pn
)

, closed_won_opportunities as (
    select
        so.closed_won_at::date as closedate
        , so.type
        , so.arr_c
        , so.sales_motion_c
        , sat.apollo_team_id
        , ro.products_sold_c
    from analytics_db.analytics.dim_salesforce_opportunities as so
    left join analytics_db.analytics.dim_salesforce_apollo_teams as sat
        on so.account_id = sat.sfdc_account_id
    left join raw_fivetran_db.salesforce.opportunity as ro
        on so.id = ro.id
    where so.is_won = true
        and so.is_closed = true
        and sat.apollo_team_id is not null
)

, matched_opportunities as (
    select
        cwo.apollo_team_id
        , pp.start_date                                                                                as inbound_start_date
        , cwo.arr_c                                                                                    as opportunity_arr
        , cwo.products_sold_c
        -- Sales motion label
        , case when cwo.sales_motion_c = 'Self-Serve' then 'Self-Serve' else 'Rep-Led' end             as sales_motion_label
        -- Prioritization logic
        , case when cwo.sales_motion_c != 'Self-Serve' or cwo.sales_motion_c is null then 1 else 2 end as rep_led_priority
        , case
            when cwo.type = 'New Business' then 1
            when cwo.type = 'Upsell' then 2
            when cwo.type = 'Renewal' then 3
            else 4
        end                                                                                            as type_priority
    from closed_won_opportunities as cwo
    inner join plan_priced as pp
        on cwo.apollo_team_id = pp.apollo_team_id
        and abs(datediff(day, cwo.closedate, pp.start_date)) <= 1
)

, ranked_opportunities as (
    select
        *
        , row_number() over (
            partition by apollo_team_id, inbound_start_date
            order by rep_led_priority asc, type_priority asc, opportunity_arr desc
        ) as priority_rank
    from matched_opportunities
)

--   1. Prioritize rep-led over self-serve (based on sales_motion_c)
--   2. Prioritize by type: New Business > Upsell > Renewal > Others
--   3. Within same type, choose largest ARR

, top_opportunity_per_plan as (
    select
        apollo_team_id
        , inbound_start_date
        , sales_motion_label
        , products_sold_c
    from ranked_opportunities
    where priority_rank = 1
)

-- OPTIONAL: Persist first sales_motion_label per team across all time
-- Comment out this CTE and uncomment the alternative logic in plans_with_sales_motion below
-- to revert to per-plan sales_motion_label logic
, first_sales_motion_per_team as (
    select
        apollo_team_id
        , sales_motion_label
        , products_sold_c
        , row_number() over (
            partition by apollo_team_id
            order by inbound_start_date asc
        ) as rn
    from top_opportunity_per_plan
)

, team_persisted_sales_motion as (
    select
        apollo_team_id
        , sales_motion_label
        , products_sold_c
    from first_sales_motion_per_team
    where rn = 1
)

, plans_with_sales_motion as (
    select
        pp.*
        -- OPTION 1: Use persisted first sales_motion_label per team (current)
        , coalesce(tpsm.sales_motion_label, 'Self-Serve') as sales_motion_label
        , tpsm.products_sold_c
        -- OPTION 2: Use per-plan sales_motion_label (original logic - uncomment to revert)
        -- coalesce(top.sales_motion_label, 'Self-Serve') as sales_motion_label,
        -- top.products_sold_c
    from plan_priced as pp
    -- OPTION 1: Join to persisted team-level sales motion
    left join team_persisted_sales_motion as tpsm
        on pp.apollo_team_id = tpsm.apollo_team_id
    -- OPTION 2: Join to per-plan sales motion (original logic - uncomment to revert)
    -- left join top_opportunity_per_plan top
    --     on pp.apollo_team_id = top.apollo_team_id
    --     and pp.start_date = top.inbound_start_date
)

, adding_rank as (
    select
        *
        , dense_rank() over (partition by apollo_team_id order by start_date desc) as start_date_rank
    from plans_with_sales_motion
)

select
    date_trunc('week', start_date) as start_week
    , account_segment
    , sales_motion_label
    , count(distinct apollo_team_id) as team_count
from adding_rank
where 1=1
    and start_date_rank = 1
group by all
```
