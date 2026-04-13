# FCT_MONTHLY_REVENUE

> Monthly revenue with change categories (new, churn, upgrade, downgrade). Core retention table.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE` |
| **Grain** | One row per team + month (`APOLLO_TEAM_ID` + `DATE_PERIOD`) |
| **Row count** | ~7.4M (2026-03-06) |
| **Refresh cadence** | Unknown — not found in airflow-dags repo. Likely daily or triggered after FCT_DAILY_REVENUE. |
| **Trust level** | Use with caution (ANALYTICS schema) |
| **Owner** | <!-- TODO: likely Finance / Analytics --> |
| **DAG** | Not found in airflow-dags. Likely built by dbt project or separate pipeline external to this repo. |

## Description

Monthly revenue and retention table (27 distinct users, 26K queries). Powers churn, expansion, and retention dashboards in Looker. Contains change categories that classify each team-month as new, churn, upgrade, downgrade, etc.

## Upstream Sources

**Not a rollup of FCT_DAILY_REVENUE.** Both tables are independently built from the same shared macros at different granularities — monthly revenue is computed directly from opportunities, not aggregated from daily rows.

Built by `dbt_apollo/models/marts/finance/fct_monthly_revenue.sql` using two shared macros:
- **`create_revenue_datespine('month')`** — generates the per-account monthly date spine from `int_opportunities_and_accounts`
- **`create_revenue_model_from_datespine('month', var('churn_limit_months'))`** — applies change category logic at monthly grain

| Source | Relationship | Notes |
|---|---|---|
| `int_opportunities_and_accounts` | Core datespine source | Same source as FCT_DAILY_REVENUE. Unions team-level and account-level opportunity rows. Root source of the dual-ID behavior in `SFDC_TEAM_OR_ACCOUNT_ID`. |
| `dim_salesforce_opportunities` | Won opportunities | Filtered to closed-won + open renewals with ARR > 0. Drives all ARR/MRR values. |
| `stg_salesforce__apollo_team` | Team-to-account mapping | Source of `sfdc_team_id` and `sfdc_account_id`. |
| `int_team_id_mappings` | ID bridge | Derives `implied_sfdc_account_id`. Joined in final CTE to populate `APOLLO_TEAM_ID` (only resolves for IS_PARENT_ACCOUNT=FALSE rows). |
| `fct_account_edition_changes_extended_monthly` | Edition change flags | Monthly equivalent of the daily edition changes table. |
| `fct_apollo_monthly_seat_limits` | Seat limit changes | Monthly equivalent of the daily seat limits table. |
| `util_days` | Date spine | Calendar table used to generate the monthly date range per account. |

**dbt config:** `materialized='table'`, tagged `looker`.

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| IS_PARENT_ACCOUNT | BOOLEAN | 27 | 25,465 | Parent account flag | **Most-used column.** Critical for account-level analysis. |
| DATE_PERIOD | DATE | 27 | 25,374 | Month (first of month) | |
| ARR | NUMBER | 25 | 11,747 | Current ARR | |
| SFDC_TEAM_OR_ACCOUNT_ID | TEXT | 23 | 24,692 | SF team/account ID | **FK to DIM_SALESFORCE_APOLLO_TEAMS.SFDC_TEAM_ID** |
| APOLLO_TEAM_ID | TEXT | 23 | 8,210 | Apollo team ID | **FK to DIM_MONGO_TEAMS.TEAM_ID** |
| CHANGE_CATEGORY | TEXT | 21 | 14,512 | Revenue movement | Values: new, new_reactivated, churn, downgrade, upgrade |
| ARR_CHANGE | NUMBER | 20 | 11,593 | ARR delta this period | |
| PREVIOUS_DATE_PERIOD_ARR | NUMBER | 20 | 6,412 | Starting ARR | Retention base denominator |
| FIRST_ACTIVE_DATE_PERIOD | DATE | 18 | 2,984 | First active month | Cohort assignment |
| IS_SELF_SERVE | BOOLEAN | 18 | 1,452 | Self-serve flag | Channel segmentation |
| IS_REP_DRIVEN | BOOLEAN | 18 | 1,260 | Rep-driven flag | Channel segmentation |
| ARR_SA | NUMBER | 17 | 4,956 | Sales-assisted ARR | One of 4 motion columns |
| ARR_REP | NUMBER | — | — | Rep-Led ARR | One of 4 motion columns |
| ARR_SS | NUMBER | — | — | Self-Serve ARR | One of 4 motion columns |
| arr_labs | NUMBER | — | — | Labs ARR | **Lowercase column name** — unlike all other ARR columns |
| PREVIOUS_DATE_PERIOD_ARR_REP | NUMBER | — | — | Prior month Rep-Led ARR | Used in upgrade attribution delta |
| PREVIOUS_DATE_PERIOD_ARR_SS | NUMBER | — | — | Prior month Self-Serve ARR | |
| PREVIOUS_DATE_PERIOD_ARR_SA | NUMBER | — | — | Prior month Sales-Assisted ARR | |
| previous_date_period_arr_labs | NUMBER | — | — | Prior month Labs ARR | Lowercase |
| PERIOD_UPGRADE_ARR | NUMBER | 17 | 3,136 | Upgrade ARR this period | Expansion metric |
| PERIOD_DOWNGRADE_AND_CHURN_ARR | NUMBER | 17 | 3,018 | Downgrade + churn ARR | Contraction metric |
| IS_ACTIVE | BOOLEAN | 17 | 1,996 | Active subscription flag | |
| PREVIOUS_DATE_PERIOD_IS_ACTIVE | BOOLEAN | — | — | Prior period active flag | Retention base |
| IS_FIRST_DATE_PERIOD | BOOLEAN | — | — | First month on platform | Use for cohort assignment. Equivalent to `DATE_PERIOD = FIRST_ACTIVE_DATE_PERIOD`. |
| IS_SALES_ASSISTED | BOOLEAN | — | — | Sales-assisted flag | Mirrors IS_REP_DRIVEN for hybrid motion |
| REACTIVATION_ARR_CHANGE | NUMBER | — | — | ARR from reactivated teams | Separate from expansion |
| UPGRADE_ARR_CHANGE | NUMBER | — | — | ARR from upgrades | |
| DOWNGRADE_ARR_CHANGE | NUMBER | — | — | ARR lost from downgrades | Negative value |
| CHURN_ARR_CHANGE | NUMBER | — | — | ARR lost from churn | Negative value |

## How It's Used

### Common query patterns
- **Net retention**: Sum of ARR changes by category
- Always joined with `DIM_SALESFORCE_APOLLO_TEAMS` on SFDC_TEAM_ID and `DIM_SALESFORCE_ACCOUNTS`
- Also joined with `FCT_APOLLO_MONTHLY_SEAT_LIMITS` for seat-based analysis
- Grouped by `DATE_PERIOD` month

### Key consumers
- Looker (churn, retention, expansion dashboards — dominant consumer)
- Executive reporting

## Default query behavior

**Always filter `IS_PARENT_ACCOUNT = FALSE` unless the user explicitly asks for account-level grouping.**

The same dual-ID structure applies here as in `FCT_DAILY_REVENUE` (both are built from the same `create_revenue_datespine` macro). Team-level rows (FALSE) have fully populated `APOLLO_TEAM_ID` and clean join paths. Parent account rows (TRUE) have NULL `APOLLO_TEAM_ID` and a different ID namespace in `SFDC_TEAM_OR_ACCOUNT_ID` — joining them to `DIM_SALESFORCE_APOLLO_TEAMS` via `SFDC_TEAM_ID` will silently drop most revenue except VSB-Freemail.

**Exception — North Star Looker dashboard:** Most tiles in the North Star dashboard use `IS_PARENT_ACCOUNT = TRUE` (account-level grouping). If a user references North Star numbers and asks why their ad-hoc query doesn't match, this is a likely cause — their query is probably running at the team level (FALSE) while North Star aggregates at the account level (TRUE). When debugging North Star discrepancies, switch to `IS_PARENT_ACCOUNT = TRUE` and join directly to `DIM_SALESFORCE_ACCOUNTS` on `SFDC_TEAM_OR_ACCOUNT_ID = a.ID`.

## Known Issues & Gotchas

- `IS_PARENT_ACCOUNT` in this table IS reliable as the account-level dedup — filter on it for all NNARR metrics. (Unlike `FCT_DAILY_REVENUE` where IS_PARENT_ACCOUNT is sparse and unreliable.)
- `arr_labs` and `previous_date_period_arr_labs` are **lowercase** — unlike all other ARR motion columns which are uppercase
- `CHANGE_CATEGORY`: 'new_reactivated' and 'new' are combined for "new" metrics; 'reactivation' is a separate category for churned teams coming back
- Upgrade ARR attribution is motion-aware: determines which of REP/SS/SA/Labs drove the upgrade via delta comparison. Falls back to `ARR_CHANGE` when only one motion is active. See `domain/sql_patterns.md` — NNARR section for full logic.
- The COALESCE join to DIM_SALESFORCE_ACCOUNTS (`COALESCE(sat.SFDC_ACCOUNT_ID, r.SFDC_TEAM_OR_ACCOUNT_ID)`) handles teams without SF account mappings
- The `IS_CORE_ACCOUNT` filter in standard RevOps queries is effectively a no-op — population is controlled by `ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')`
- Always exclude suspicious teams: `NOT sat.IS_SUSPICIOUS_TEAM` + `NOT sa.HAS_SUSPICIOUS_TEAM`

## Slack Context

- **Executive debrief (Leo Liu, Jan 2026)**: Topline is off track — Dec forecast $177.1M ARR, ($0.2M) NNARR. Driven by sales underperformance (-$2.5M vs plan) and elevated churn/downgrade (-$1.5M vs plan). "We have a conversion, mix, and retention quality problem — especially in how demand translates into durable ARR."
- **DCS Weekly Scoreboard request (Rob Statsky, Feb 2026)**: Needs VSB NRR (3-month rolling), VSB GRR (3-month rolling), VSB Logo Churn %, Churn Rate vs Target (5% reduction goal), $ Saved This Month vs $60k target. This table is the primary source for these metrics.
- **NRR/GRR measurement (Glean doc: "Improving GRR + GDR measurement in Looker")**: Active effort to improve how retention metrics are calculated in Looker. Related docs: "GRR Metrics", "GRR - By CSM", "Added new GRR & NRR Measures".
- **ARR zeroing gotcha (Pubudu, analytics)**: "The daily audit report sets ARR to zero when it knows that the account will churn - but does it before it actually churns (so ignores real future revenue - between churn notice and actual churn date)". This can affect retention calculations.
- **Key concern**: Growth is skewing toward non-core customers — helps short-term ARR but hurts churn and NRR durability.

## Business Terms

| Term | Definition |
|---|---|
| Churn | A previously active team/account that stopped paying |
| Downgrade | A team/account that reduced their plan/spend |
| Net Retention | (Starting ARR + expansion - contraction - churn) / Starting ARR |
| Parent Account | The top-level SF account (vs individual team) |

## Sales Motion Definitions

The motion columns (`IS_REP_DRIVEN`, `IS_SALES_ASSISTED`, `IS_SELF_SERVE` and corresponding `ARR_REP`, `ARR_SA`, `ARR_SS`, `arr_labs`) follow the definitions in [`domain/sales_motion_definitions.md`](../../domain/sales_motion_definitions.md). See that file for thresholds, edge cases, and historical changes.

## M3 Cohort NRR Notes

This table is the source for M3 Cohort NRR. The key pattern:

```sql
-- Cohort = first month (IS_FIRST_DATE_PERIOD = TRUE)
-- Retention = same team active 3 months later (IS_ACTIVE = TRUE at DATE_PERIOD = cohort_month + 3 months)
-- Core filter: JOIN to LU_TEAM_ATTRIBUTES ON APOLLO_TEAM_ID = TEAM_ID WHERE IS_CORE_ACCOUNT = TRUE
```

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Added default IS_PARENT_ACCOUNT = FALSE rule, dual-ID gotcha, North Star dashboard note, full upstream lineage from dbt analysis; corrected misconception that this is a rollup of FCT_DAILY_REVENUE | Will (via Claude) |
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
| 2026-03-19 | Added newly discovered columns (IS_FIRST_DATE_PERIOD, motion flags, change components); added M3 NRR notes | Brighid (via Claude) |
| 2026-03-20 | Added 4 ARR motion columns (ARR_REP, ARR_SS, arr_labs) + PREVIOUS_DATE_PERIOD_* variants; documented upgrade attribution logic; corrected IS_PARENT_ACCOUNT reliability note; arr_labs lowercase gotcha | Leo |
