# Inbound Teams — Identification & Revenue Attribution

**Purpose:** Identify which teams have adopted Inbound add-on and track their contribution to expansion ARR.

**Audience:** Jarvis, product team, sales
**Date:** 2026-03-30
**Owner:** Bridie Meredith (Analytics), Product team (data source)
**Status:** In progress; Q1 traction validated; mapping to revenue tables TBD (Gap 6)

---

## What is Inbound Router?

**Product:** Inbound Router add-on (beta → GA path planned Q2)

**Value prop:** Automate inbound lead routing and qualification. Routes cold inbound leads to right AE/SDR based on rules + AI scoring.

**Target buyer:** SDRs, BDRs, sales ops (own inbound qualification process)

**Business model:** Per-message or per-routed-lead fee (TBD based on usage model)

---

## Current Traction (Q1 2026)

| Metric | Value | Notes |
|--------|-------|-------|
| **Teams adopted** | ~170 | Early beta; manually identified |
| **Total ARR** | $300k+ | Estimated from Mongo audit data |
| **Monthly growth** | ~60 teams/month | Based on 60-day sample |
| **Attach rate (paid teams)** | ~2.7% | 170 / 6.3M paid teams |

**Source:** `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` (Lens 3: `ADDITIONAL_FEE_BY_SOURCE`)

---

## Data Identification Approaches

### Current (Manual, Not Scalable)

**Source:** `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS`

```sql
SELECT
  team_id,
  DATE_TRUNC('MONTH', date) as month,
  ADDITIONAL_FEE_BY_SOURCE -> 'inbound_router' as inbound_router_fee,
  SUM(ADDITIONAL_FEE_BY_SOURCE -> 'inbound_router') as monthly_inbound_arr
FROM FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS
WHERE ADDITIONAL_FEE_BY_SOURCE -> 'inbound_router' > 0
GROUP BY team_id, month
ORDER BY monthly_inbound_arr DESC
```

**Limitations:**
- Only captures fee-bearing usage (ignores free tier, pilots)
- Requires nested JSON parsing (error-prone)
- Refresh lag (daily, but diagnostic only)

---

### Future (Scalable, Permanent)

**Option A: Mongo Inbound Flag**
```
Teams.inbound_router_enabled: TRUE/FALSE
Teams.inbound_router_activated_at: TIMESTAMP
Teams.inbound_router_tier: 'free' | 'paid'
```

**Advantage:** Clean; directly from product layer

**Estimate:** Product team to provide flag definition (1-2 hours) + DE to sync (2-3 hours)

**Option B: Revenue Table Flag**
```
FCT_DAILY_REVENUE
  - INBOUND_ROUTER_ARR column (denormalized)
  - INBOUND_ROUTER_IND (T/F flag)
```

**Advantage:** Single join, no Mongo round-trip

**Estimate:** 1-2 days for DE schema update + backfill

**Option C: Lookup Table**
```
DIM_INBOUND_TEAMS:
  - team_id (PK)
  - inbound_activated_at
  - inbound_tier
  - current_inbound_arr
```

**Advantage:** Lightweight; join once to all revenue queries

**Estimate:** 1-2 days (requires source flag from option A)

---

## ARR Attribution

**Current method (Q1):** `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` fees

**Limitations:**
- Doesn't tie to `FCT_DAILY_REVENUE` (revenue table of record)
- Can't blend with other revenue metrics (churn, expansion, etc.)
- Inbound usage may be misclassified as other features

**Future method (Goal):**
```
V_INBOUND_ARR_BY_SEGMENT:
  SELECT
    s.ACCOUNT_SEGMENT as segment,
    SUM(f.INBOUND_ROUTER_ARR) as inbound_arr,
    COUNT(DISTINCT f.TEAM_ID) as teams_with_inbound,
    ROUND(SUM(f.INBOUND_ROUTER_ARR) / COUNT(DISTINCT f.TEAM_ID), 0) as avg_arr_per_team,
    ROUND(100.0 * SUM(f.INBOUND_ROUTER_ARR) / SUM(SUM(f.INBOUND_ROUTER_ARR)) OVER (), 1) as pct_of_total_inbound_arr
  FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE f
  LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT s
    ON f.TEAM_ID = s.APOLLO_TEAM_ID
  WHERE f.DATE_UTC = CURRENT_DATE() - 1
    AND f.INBOUND_ROUTER_ARR > 0
  GROUP BY s.ACCOUNT_SEGMENT
  ORDER BY inbound_arr DESC
```

---

## Retention & Expansion Analysis

**Key metrics (once data is available):**

| Metric | Calculation | Rationale |
|--------|-------------|-----------|
| **Inbound M3 NRR** | ARR at M3 / ARR at M0 for Inbound adopters | Product health; graduation criterion for H2 bet |
| **Inbound churn rate** | Count(churned_inbound_teams) / Count(inbound_teams) | Understanding product stickiness |
| **Inbound expansion ARR** | Sum of ACV increases in inbound cohorts | Secondary growth within product |
| **Competitive overlap** | % of Inbound teams also using Dialer | Cannibalization check |

---

## Known Questions (Product Clarification Needed)

1. **Is Inbound independent or bundled?** (affects pricing model + ARR counting)
2. **Free tier vs. paid?** (affects TAM calculation + attach rate)
3. **Primary user persona?** (SDR vs. sales ops vs. marketing — affects GTM targeting)
4. **Seasonal adoption pattern?** (is Q1 traction representative?)

---

## Data Table Requirements

Once product provides source flag, Analytics will build:

```
DIM_INBOUND_ADOPTION:
  - team_id (PK)
  - first_inbound_use_date
  - inbound_activated_at (paid tier)
  - current_inbound_tier ('free' | 'paid')
  - is_currently_active (boolean)

Grain: One row per team
Refresh: Daily
Source: Mongo DIM_MONGO_TEAMS.inbound_router_enabled flag
```

---

## Timeline

| Milestone | Owner | ETA | Status |
|-----------|-------|-----|--------|
| **Product defines inbound flag in Mongo** | Product (Inbound PM) | This week | Pending |
| **Sync to ANALYTICS_DATAPLATFORM** | DE | 2-3 hours after flag defined | Pending #1 |
| **Build DIM_INBOUND_ADOPTION** | Bridie (Analytics) | 1-2 hours after #2 | Pending #2 |
| **Add to FCT_DAILY_REVENUE** | DE | 2-3 hours | Pending #1 |
| **Jarvis queries enabled** | Jarvis team | 1 day | Pending #3, #4 |

**Estimate total:** 3-5 days if product provides flag immediately

---

## How Jarvis Uses This

**Current (before live):**
> "Inbound add-on revenue isn't yet flagged in our warehouse. From Mongo we can see ~170 teams adopted it in Q1 (early beta), generating $300k+ ARR. But I can't query 'inbound ARR by segment' or track cohort NRR yet. Product team is providing the data source — should have this live by end of Q1."

**Future (after implementation):**
> "Inbound Router ARR: $300k (Q1 data). SMB adoption: 60%, Mid-Market: 30%, Enterprise: 10%. Attach rate is 2.7% of paid teams (170 teams), which is light for early GA. Cohort NRR data coming next week; that read will determine if this is product-market fit or pricing issue."

---

## Related Files

- `pending_definitions.md` — Gap 6 (full context)
- `product_portfolio_taxonomy.md` — Inbound as H2 bet
- `annual_targets.md` — $6.4M FY27 target
- `business_state.md` — Current inbound momentum
