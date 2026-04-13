# Sales Motion (Rep-Driven vs. Self-Serve) — Definition Inventory

**Owner:** Will Masket
**Date:** 2026-03-20
**Purpose:** Inventory of how sales motion is defined across the analytics stack, as a foundation for stakeholder alignment.

> **Status:** This document is part of an in-progress effort to establish a single canonical definition for customer acquisition motion attribution — a unified, single-value field that answers "how did this customer come to us?" for any team or account. The inventory below captures the current state: multiple overlapping definitions at different grains, with no existing field or model that resolves them into one authoritative value. Alignment on that definition is the goal.
>
> **What we do have:** Working definitions for attributing ARR to a sales motion at the individual transaction (opportunity) level, implemented in the revenue models (`int_opportunities_and_accounts` → `fct_monthly_revenue`). These are well-defined and in production. The gap is in translating transaction-level motion attribution into a single customer-level acquisition label.

---

## Summary

Apollo classifies revenue into **four sales motions**: Self-Serve (SS), Sales-Assisted (SA), Rep-Driven (Rep), and Apollo Labs. These are **not mutually exclusive labels on a customer or account** — they are allocations applied at the **individual opportunity (transaction) level**, then rolled up into period-level flags on teams and accounts.

A single account can simultaneously carry ARR in more than one motion bucket if it has multiple active opportunities with different owners. The "is this customer rep-driven?" question is answered differently depending on which grain you're querying.

---

## The Four Sales Motions

| Motion | Short Name | Plain-English Definition |
|--------|-----------|--------------------------|
| Self-Serve | SS | Customer transacted without a sales rep involved — owned end-to-end by Marketo (our automated renewal system) |
| Sales-Assisted | SA | A Customer Advocate (CA) or Product Advocate was involved in the transaction |
| Rep-Driven | Rep | Everything else — any opportunity with a human AE/AM as the owner that isn't SA |
| Apollo Labs | Labs | Internal/experimental opportunities explicitly flagged as Labs in Salesforce |

> **Key point:** Rep-Driven is a **residual** — it is not directly detected. It is calculated as `ARR − ARR_SS − ARR_SA − ARR_Labs`. An opportunity that doesn't match SS, SA, or Labs is Rep-Driven by default.

---

## Where the Classification Lives

### Primary Source: Opportunity Level

**Model:** `int_opportunities_and_accounts.sql`
**Grain:** One row per Salesforce opportunity
**Columns produced:** `mrr_ss`, `arr_ss`, `mrr_sa`, `arr_sa`, `mrr_labs`, `arr_labs`, `mrr_rep`, `arr_rep`

This is the single authoritative place where the classification is made. All downstream aggregations (monthly, daily, team-level) flow from here.

> **Important scope limitation:** Not all Salesforce opportunities pass through this model. An opportunity is included only if it satisfies one of two conditions:
>
> **Condition 1 — Closed-won:** `is_won = true` AND `arr > 0` AND both `start_date` and `end_date` are non-null AND `type != 'Refund'` AND not a first-ever New Business opp on a Suspended-due-to-Non-Payment account AND term length is either >0 months or ends on the last day of the month.
>
> **Condition 2 — Open pending renewal:** `is_closed = false` AND `arr > 0` AND both dates non-null AND `early_termination_date` is null AND `type = 'Renewal'` AND term starts in the current month or later.
>
> The practical consequence: **mid-term rep-driven upsells that were not closed-won are excluded** (e.g., an open or lost upsell). Because rep-driven is a residual, this silently understates `arr_rep` for teams where upsells did not progress to closed-won status.

### Downstream: Period-Level Revenue Tables

| Model | Grain | Motion Columns |
|-------|-------|----------------|
| `fct_monthly_revenue` | Team × Month | `ARR_SS`, `ARR_SA`, `ARR_REP`, `arr_labs`, `IS_SELF_SERVE`, `IS_SALES_ASSISTED`, `IS_REP_DRIVEN` |
| `fct_daily_revenue` | Team × Day | Same as monthly |

The boolean flags (`IS_REP_DRIVEN`, `IS_SELF_SERVE`, `IS_SALES_ASSISTED`) are derived simply as `true` if the corresponding ARR bucket is > 0 for that team-period.

### Downstream: Team Dimension

**Model:** `dim_salesforce_apollo_teams`
**Grain:** One row per Salesforce team (current state)
**Columns:**

| Column | Meaning |
|--------|---------|
| `HAS_CURRENT_REP_DRIVEN_ARR` | Team has active rep-driven ARR today |
| `HAS_CURRENT_SELF_SERVE_ARR` | Team has active self-serve ARR today |
| `HAS_CURRENT_SALES_ASSISTED_ARR` | Team has active sales-assisted ARR today |
| `IS_REP_DRIVEN_FIRST_PAID_MONTH` | Team's first-ever payment was rep-driven |
| `IS_SELF_SERVE_FIRST_PAID_MONTH` | Team's first-ever payment was self-serve |
| `IS_SALES_ASSISTED_FIRST_PAID_MONTH` | Team's first-ever payment was sales-assisted |
| `IS_REP_DRIVEN_MOST_RECENT_FIRST_PAID_MONTH` | Most recent acquisition event (post-reactivation) was rep-driven |

The "first paid month" flags capture the **acquisition motion** — how the team originally became a paying customer — and persist even if the motion changes later. The "most recent first paid month" variant resets when a team churns and reactivates after 3+ months.

---

## How Each Motion Is Determined

### Self-Serve (SS)

An opportunity is self-serve if **all** of the following are true:

1. `owner_id` = Marketo Sync user (the automated renewal bot)
   _OR_ (FY27 only) `revenue_categorization_override` contains `"self serve"` — a manual Salesforce override for edge cases
2. `has_selling_advocate = false` — no CA/PA was involved
3. `is_previous_rep_driven_logic = false` — the prior opportunity wasn't a rep-driven upsell that started in the same month as this renewal
4. `is_apollo_labs_opportunity = false`
5. (FY27 only) Owner's `position_name` is NOT `Customer Advocate` or `CA Team Manager`

**The "previous rep-driven" guard:** If a rep closed an upsell in the same month that the renewal auto-processes, the renewal inherits the rep attribution. This prevents double-counting a rep's contribution.

### Sales-Assisted (SA)

An opportunity is sales-assisted if **any** of the following are true (and it's not Labs):

- `has_selling_advocate = true` (Salesforce checkbox stamped during the opp)
- `closed_won_owner_position` = `Customer Advocate` or `CA Team Manager` (stamped at close time)
- (FY27 only) Owner's current `position_name` in User Allocation = `Customer Advocate` or `CA Team Manager`

**Pre-FY27 caveat:** The legacy logic also excluded opps where the owner had an AE/AM role (`owner_role_name` contained "Account Management", "Account Executive", or "Account Manager"). This guard was removed in FY27 in favor of position-name detection.

**Note from the code (Oct 2026 comment):** `has_selling_advocate` stopped being populated reliably at some point in FY27 — the `closed_won_owner_position` and `user_allocation.position_name` signals became the primary detection path.

### Rep-Driven (Rep)

No direct detection. Calculated as:

```sql
arr_rep = arr - arr_ss - arr_sa - arr_labs
```

Any opportunity with a human AE or AM owner that isn't SA or Labs will fall here.

### Apollo Labs

An opportunity is Labs if `is_apollo_labs_opportunity = true` (a checkbox in Salesforce). Labs ARR is excluded from all SS/SA/Rep calculations.

> **Note:** Apollo Labs is no longer an active program. The Labs bucket exists in the data for historical purposes but should not be generating new ARR.

---

## FY27 Methodology Change (Effective 2026-02-01)

The logic is **date-split** at `closed_at = 2026-02-01`. Opportunities closed before this date use legacy logic; opportunities closed on or after use FY27 logic.

| Change | Legacy (pre-FY27) | FY27 (2026-02-01+) |
|--------|-------------------|---------------------|
| SA detection | `has_selling_advocate` OR `closed_won_owner_position = 'Customer Advocate'`, with AE/AM exclusion | Same OR `user_allocation.position_name` in ('Customer Advocate', 'CA Team Manager'); AE/AM exclusion removed |
| SS detection | Owner must be Marketo Sync | Owner can be Marketo Sync OR non-Marketo with `revenue_categorization_override ilike '%self serve%'` |
| CA role scope | `Customer Advocate` only | `Customer Advocate` AND `CA Team Manager` |

---

## Key Fields Reference

| Salesforce / Model Field | Source | Role in Classification |
|--------------------------|--------|------------------------|
| `owner_id` | Salesforce Opportunity | Primary self-serve signal (must = Marketo Sync user) |
| `has_selling_advocate` | Salesforce Opportunity (checkbox) | SA signal; reliability degraded in FY27 |
| `closed_won_owner_position` | Stamped at close from User Allocation | SA signal; more reliable than has_selling_advocate |
| `user_allocation.position_name` | User Allocation dim (FY27) | SA signal for current-position detection |
| `revenue_categorization_override` | Salesforce Opportunity (text) | Manual SS override; FY27 only |
| `is_apollo_labs_opportunity` | Salesforce Opportunity (checkbox) | Labs exclusion |
| `is_previous_rep_driven_logic` | Calculated in model | Prevents SS classification for same-month renewal after rep upsell |

---

## Data Analysis: Acquisition Motion Attribution (March 2026)

This analysis uses `IS_X_FIRST_PAID_MONTH` flags from `DIM_SALESFORCE_APOLLO_TEAMS` joined to March 2026 ARR from `FCT_MONTHLY_REVENUE` (active paying teams, team-level grain). It is intended to inform business rules for a consolidated single-value acquisition attribution.

### All flag combinations

| SS | SA | Rep | Teams | ARR ($M) | Notes |
|----|----|----|-------|----------|-------|
| ✓ |  |  | 95,266 | $137.1M | Pure self-serve — dominant bucket |
|  |  | ✓ | 8,909 | $54.2M | Pure rep-driven |
| ✓ |  | ✓ | 692 | $3.8M | Mixed SS + Rep — see tiebreaker analysis below |
|  | ✓ |  | 2,476 | $3.7M | Pure sales-assisted |
| ✓ | ✓ |  | 412 | $1.3M | Mixed SS + SA |
|  | ✓ | ✓ | 24 | $0.15M | Mixed SA + Rep |
| ✓ | ✓ | ✓ | 4 | $0.02M | All three — noise |

**~93% of teams land cleanly in a single bucket.** The pure SS, Rep, and SA rows account for ~$195M of ~$200M total ARR. The ambiguous cases total ~$5M, of which the SS+Rep overlap ($3.8M) is the most meaningful.

### Tiebreaker deep dive: mixed SS + Rep teams (692 teams, $3.8M)

For the 692 teams where both `IS_SELF_SERVE_FIRST_PAID_MONTH` and `IS_REP_DRIVEN_FIRST_PAID_MONTH` are true, we compared the term start dates of SS-attributed vs. Rep-attributed opportunities in `INT_OPPORTUNITIES_AND_ACCOUNTS` within the team's first paid month:

| Which came first | Teams | ARR ($M) | Share of mixed ARR |
|-----------------|-------|----------|--------------------|
| Rep first | 376 | $2.21M | 58% |
| Same day | 234 | $1.12M | 30% |
| SS first | 82 | $0.45M | 12% |

The dominant case is a rep-closed opportunity (New Business or Upsell) followed by a Marketo-owned renewal landing in the same first month. The "same day" bucket (234 teams, $1.12M) is the scenario the `is_previous_rep_driven_logic` guard in the dbt model was designed for — a rep upsell and an auto-renewal closing on the same date.

**Implication for business rules:** If "first transaction wins" is adopted as the tiebreaker, 58% of the mixed ARR ($2.21M) would flip from ambiguous to Rep-Driven, and 12% ($0.45M) to Self-Serve. The same-day cases (30%, $1.12M) would require a secondary rule.

---

## Open Questions / Alignment Gaps

These are areas where the current implementation may not match business intent — or where different stakeholders may have different mental models:

1. **"Is this customer self-serve?"** is ambiguous. An account can have both SS and Rep-Driven ARR simultaneously (e.g., a self-serve renewal alongside a rep-closed upsell). `HAS_CURRENT_SELF_SERVE_ARR` and `IS_REP_DRIVEN` are not mutually exclusive.

2. **Acquisition motion vs. current motion:** `IS_SELF_SERVE_FIRST_PAID_MONTH` (how you acquired) can differ from `HAS_CURRENT_SELF_SERVE_ARR` (what you are today). Which one should segment-level reporting use?

3. **Rep-Driven is residual:** There is no explicit signal that makes an opportunity rep-driven. If any classification logic is wrong (e.g., a CA-assisted opp that isn't flagged), that ARR silently falls into the Rep bucket. The "residual" approach makes the Rep total sensitive to errors in SS/SA logic.

4. **`has_selling_advocate` reliability:** The code includes a comment that this field stopped being populated at some point in FY27. It's unclear when exactly, or how much historical SA data is affected.

5. **SA vs. Rep boundary for AE-owned opps:** Under FY27 logic, an AE can own an opp and it still classifies as SA if a CA is attached via `position_name`. Pre-FY27, that same opp would have been Rep-Driven. This means SA increased mechanically at the FY27 cutoff.

6. **`revenue_categorization_override`:** There's no documented governance around who sets this field, when, or why. Its use creates a manual escape hatch from the automated classification.

---

## Salesforce-Native Motion Fields

Two picklist fields exist directly on the Salesforce Opportunity object with "Self-Serve" / "Rep-Driven" values. These are **separate from the dbt ARR classification** and are not used in any current revenue models. Their population source is unconfirmed — no automation was found in the SFDCgearset deployment repo or the leadgenie CRM push codebase. High fill rates suggest they are set by Salesforce automation (Flow or Process Builder) that exists in the org but is not tracked in Gearset. **Needs investigation.**

### Fill rates by opportunity type (closed-won, last 3 months as of 2026-03-20)

#### `Sales_Motion__c`

| Value | New Business | Upsell | Renewal | Total |
|-------|-------------|--------|---------|-------|
| Self-Serve | 40,564 | 28,858 | 199,317 | 268,739 |
| Rep-Driven | 0 | 0 | 0 | 0 |
| NULL | 2,279 | 1,871 | 7 | 4,157 |
| **Fill rate** | 95% | 94% | ~100% | **98.5%** |

- Restricted picklist (only "Self-Serve" and "Rep-Driven" are valid values)
- "Rep-Driven" has **never been populated** — zero records across all time in the last 3 months
- Near-100% fill on Renewals; NULLs concentrated in New Business and Upsell
- Used in `Opportunity_Before_Save_Populate_fields` flow as a **read-only condition** to derive a pipeline category label — not written by that flow
- Field description: *(none)*

#### `Plan_changed_by_motion__c`

| Value | New Business | Upsell | Renewal | Total |
|-------|-------------|--------|---------|-------|
| Self-Serve | 41,600 | 28,512 | 3,960 | 74,072 |
| Rep-Driven | 1,087 | 1,147 | 303 | 2,537 |
| NULL | 156 | 1,070 | 195,061 | 196,287 |
| **Fill rate** | ~95% | ~97% | ~2% | **28%** |

- Non-restricted picklist (same two values, but not restricted)
- Both values are genuinely populated — "Rep-Driven" appears on ~3% of filled records
- Renewals are almost entirely NULL (195K of 199K) — this field appears scoped to plan-change transactions (NB and Upsell)
- Not referenced anywhere in dbt models or Looker
- Field description: *"Whether the plan was changed via sales assist or self-serve"*

### Open question

The population mechanism for both fields is unknown. No Salesforce Flow, Apex trigger, or API-based sync (leadgenie) was found that writes to either field. Given the high and consistent fill rates on applicable opp types, automated population via an untracked Salesforce Flow or Process Builder is the likely explanation. **Someone with Salesforce Setup access should check Process Automation → Flows for active flows on the Opportunity object that write to these fields.**

---

## Data Lineage Summary

```
Salesforce Opportunity
    → int_opportunities_and_accounts   [CLASSIFICATION HAPPENS HERE]
         → arr_ss, arr_sa, arr_rep, arr_labs per opportunity
    → fct_daily_revenue / fct_monthly_revenue
         → is_self_serve, is_rep_driven, is_sales_assisted per team-period
    → int_team_revenue_metrics
         → has_current_*_arr, is_*_first_paid_month per team
    → dim_salesforce_apollo_teams
         → team-level current-state flags and historical acquisition motion
```
