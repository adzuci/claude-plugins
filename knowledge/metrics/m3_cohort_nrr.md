# M3 Cohort NRR

> **Owner:** Rahul (Analytics)
> **OKR Target:** N/A
> **Status:** APPROVED

## What this metric measures

Net Revenue Retention measured at Month 3 post-acquisition for a monthly cohort.

## What we already have

- `FCT_TEAM_REVENUE_DAILY` — daily ARR per team
- `LU_TEAM_ATTRIBUTES` — team metadata (segment, edition, created date)
- Stub SQL that identifies cohort by first `ds` with `arr > 0`

## What we need from you

Fill in each section below. Plain language is fine — Claude will convert to SQL.

### 1. Cohort definition

How do you define which teams belong to a cohort?

- First paid date = first `ds` where `arr > 0`? Or something else (e.g., contract start date)?
- Any filters? (e.g., only core accounts, exclude free trials, minimum ARR threshold?)

```
YOUR ANSWER:
- **Source table:** `analytics_db.analytics.fct_monthly_revenue` (not `FCT_TEAM_REVENUE_DAILY`).
- **First paid date:** Use `first_active_date_period` on `fct_monthly_revenue`.
- **Cohort grouping:** Monthly cohorts by the anchor date (e.g. all teams whose `first_active_date_period` falls in January 2026 = "January 2026 Cohort").
- **Exclusions:**
  - The user must choose to measure at either **parent account** level (`is_parent_account = true`) or **team** level (`is_parent_account = false`). These are **mutually exclusive** — never mix both in the same query.
- **`is_parent_account`** is a column on `fct_monthly_revenue` — no join needed to determine grain.
```

### 2. M3 measurement window

What does "Month 3" mean exactly?

- Calendar month + 3? (e.g., Jan cohort measured on Apr 1)
- Exactly 90 days after first paid date?
- End of the 3rd full calendar month?

```
YOUR ANSWER:
- **Calendar month offset:** M0 = the `date_period` month in which the team first paid (the cohort anchor month). M1 = the next calendar month, M2 = the month after that, M3 = three calendar months after M0.
  - Example: Team first pays in January 2026 → M0 = Jan 2026, M1 = Feb 2026, M2 = Mar 2026, M3 = Apr 2026.
- **M0 definition:** The cohort anchor month itself — the `date_period` where `change_category = 'new'` and `arr > 0`.
- **Incomplete cohorts:** Only report cohorts where M3 has fully elapsed. E.g. if today is March 2026, the latest reportable cohort is December 2025 (whose M3 = March 2026).
```

### 3. NRR calculation

How should NRR be calculated?

- `SUM(arr_m3) / SUM(arr_m0)` at the cohort level? Or per-team then averaged?
- Include reactivations (teams that churned and came back within the window)?
- How to handle teams that expand then contract (or vice versa)?

```
YOUR ANSWER:
- **Aggregation:** Cohort-level. `SUM(ARR at M3) / SUM(ARR at M0)`.
- **Churned teams at M3:**
  - Teams that churned in M1 or M2 may have no record at M3 in `fct_monthly_revenue` — treat their M3 ARR as $0.
  - Teams that churn in M3 itself may still have a record with `change_category = 'churn'` — use their ARR value from that record.
- **Reactivations:** Included. Teams that churn after M0 and reactivate before or at M3 remain in the cohort with their M3 ARR as-is. `change_category = 'reactivation'` or `'new reactivated'` records are valid.
- **Expansion / contraction:** No special handling. Natural ARR changes flow through — expansion increases M3 ARR, contraction decreases it.
- **Formula:** `M3 Cohort NRR = SUM(cohort ARR at M3) / SUM(cohort ARR at M0) × 100%`
  - \> 100% = net expansion
  - < 100% = net contraction / churn
```

### 4. Segments / filters

Any breakdowns or filters we should bake in?

- By account segment? Edition? Region?
- Exclude any team types? (internal, test, partner?)

```
YOUR ANSWER:
- **Breakdowns (optional filters — user selects as needed):**
  - `account_segment` — on `fct_monthly_revenue` or joinable from `analytics_db.analytics.dim_salesforce_accounts`.
  - `region` — from `dim_salesforce_accounts`.
  - `account_sub_segment` — from `analytics_db.analytics.dim_salesforce_accounts`. Important filter.
  - `team_edition` — current edition, from `analytics_db.analytics.dim_salesforce_apollo_teams`.
  - `starting_apollo_edition_grouped` — the first valid closed-won opportunity's Apollo edition, from `analytics_db.analytics.dim_salesforce_apollo_teams`.
- **`is_parent_account`:** Not a breakdown. It is a grain toggle — always set to either `true` or `false`, never both in the same query.
- **Hard exclusions:** None beyond what `fct_monthly_revenue` already handles.
- **Other filters:** Many other filters may apply. The metric should be flexible enough that the user can filter as needed.
```

### 5. Anything else

Anything we're missing or getting wrong?

```
YOUR ANSWER:
- **Join keys:**
  - `fct_monthly_revenue.apollo_team_id` → `dim_salesforce_apollo_teams.apollo_team_id`
  - `dim_salesforce_apollo_teams.sfdc_account_id` → `dim_salesforce_accounts.id`
- **Additional optional filters (from reference SQL):**
  - `is_self_serve` (on `fct_monthly_revenue`) — can filter to self-serve teams.
- **Months-from-paid calculation:** `DATEDIFF(month, first_revenue_date_period, date_period)` gives the month offset (M0, M1, M2, M3).
- **Incomplete month guard:** Filter `date_period < DATE_TRUNC(month, CURRENT_DATE())` to exclude the current incomplete month.
- **Historical backfill:** Cohorts go as far back as `fct_monthly_revenue` has data, but bias toward the past 2–3 years for relevance.
```
