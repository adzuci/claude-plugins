# Theory of Change — How NRR Improves at Apollo

**Purpose:** Document the causal model driving FY27 growth strategy. Jarvis uses this to contextualize metrics and explain why we're tracking certain signals.

**Audience:** Jarvis, analytics team, exec stakeholders
**Date:** 2026-03-30
**Owner:** Bridie Meredith

---

## The Core Causal Chain

```
ACTIVATION → HABIT → VALUE RECOGNITION → RETENTION → EXPANSION → NRR
```

Each link is empirically validated (see Evidence section).

### Phase 1: Activation (Days 0-14)

**What:** New team completes first value-producing action (4+ Record Actions = F14D Habit RA Rate)

**Why:** Early action signals intent and reduces friction. Teams that don't act in first 14 days have <20% probability of ever reaching habit.

**Metric:** F14D Habit RA Rate (4+ Record Actions in first 14 days). **Target: 17%** (up from ~12% baseline). **Golden Pop only** (SMB+, AMER/EMEA, no freemail).

**Time lag to impact:** This drives M1 retention; shows in cohort NRR by M3 (12 weeks downstream).

**Current status:** Measured in Amplitude/Hex only; not yet queryable from Snowflake (Gap 7). Adhiraj owns this metric build.

> **Drill-down:** For the full metric definition, formula, and OKR context for Phase 1, see [activation_methodology.md](activation_methodology.md).

---

### Phase 2: Habit (Days 14-60)

**What:** Team develops recurring usage pattern. Operationalized as "≥26 active days per month" (credit utilization trigger).

**Why:** Habit = recurring value recognition. Teams hitting 26+ active days have 76% retention vs. <40% retention for teams with <5 active days.

**Metric:** Active Days (count of days per month with credits_used > 0). **Proxy:** `AGG_TEAM_CREDITS` daily consumption.

**Time lag to impact:** Habit formation by Week 6 post-signup; retention benefit visible in M3 cohorts.

**Current status:** Fully queryable. Used in credit soft-cap experiment (Q1 2026).

---

### Phase 3: Value Recognition (Days 60-120)

**What:** Team recognizes product value sufficient to justify continued spend. Behavior signals: multi-product activation (2+ use cases), feature expansion, seat additions.

**Metric:** Multi-product Activation = 2+ use cases (Enrichment, GenPipe Trad, GenPipe NG, Win/Close) within F28D. **Target: 35%** (stretch to 40%).

**Why:** Teams using multiple features have higher switching cost and deeper ROI realization.

**Time lag to impact:** Multi-product activation by M1-M2; drives M3 NRR retention.

**Current status:** Measured in `DIM_ACTIVE_TEAMS_DAILY` (Data Science team), but source data quality flagged as suspect. Requires validation from event level.

---

### Phase 4: Retention (Months 3-12)

**What:** Team remains active (ARR > 0) throughout renewal cycle. Measured as Net Revenue Retention (NRR).

**Why:** Retention is the primary lever for NRR improvement at Apollo (expansion growth requires stickiness first).

**Metric:**
- **M3 NRR (cohort-based):** ARR at Month 3 / ARR at Month 0, for each monthly acquisition cohort. **Target: 82-90%** depending on segment.
- **Quarterly NRR (aggregate):** Rolling 3-month revenue bridge (Starting ARR + Expansion - Churn) / Starting ARR. **Target: 130%+ for VSB/SMB**.

**Time lag to impact:** M3 NRR reflects activation + habit + value recognition in aggregate. Quarterly NRR lags 90 days behind current momentum.

**Current status:**
- Quarterly NRR available and HIGH trust (`FCT_ACCOUNT_QUARTERLY_NRR`)
- M3 cohort NRR not yet built (Gap 3: requires segment denormalization or lookup table)

**Known issue:** Cohort NRR requires team-level segment data at acquisition time. Currently we don't have historical segment snapshots (Gap 3).

---

### Phase 5: Expansion (Months 3+)

**What:** Retained teams increase spend through seats (more users), credits (higher usage), or product add-ons (Dialer, Inbound, AI).

**Why:** Expansion is the secondary growth lever. High-NRR cohorts that don't expand still stall growth.

**Metric:** Net New ARR from existing customers. Segmented by:
- **Organic expansion:** Seat adds, credit limit increases, plan upgrades (source: `FCT_DAILY_REVENUE` with CHANGE_CATEGORY='upgrade')
- **Product expansion:** Dialer ARR, Inbound ARR, AI Sheets ARR (source: `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS`)

**Target:** $115.7M total expansion ARR (FY27), split ~60% organic, ~40% new products.

**Time lag to impact:** Expansion measured monthly; contributes to quarterly NRR.

**Current status:** Fully queryable for organic expansion. New product ARR requires product-level flags (partially available for Dialer, Inbound; AI Sheets persona TBD per Gap 2).

---

## Lever 1: Improve Activation (F14D Habit RA Rate)

**What we're doing:**
- Redesigning onboarding UX to reduce friction
- Earlier value delivery in first-run experience
- Activation scoring + targeted education campaigns

**How it drives NRR:**
- Activation rate 12% → 17% = ~5pp lift
- Estimated impact on M3 retention: ~2-3pp lift in NRR
- Estimated impact on expansion: 15-20% more teams eligible for product upsell

**Data signals to track:**
- F14D Habit RA Rate (leading indicator)
- Multi-product activation within F28D (secondary)
- Cohort Month-1 churn (0-30 day survival, should trend up)

**Risks:**
- FUX changes don't convert to behavior change (past risk: email sequence overhaul had <1pp impact)
- Targeting only Golden Pop masks degradation in SMB-minus segment

---

## Lever 2: Improve Retention (Habit → Month-12)

**What we're doing:**
- Credit soft-cap experiment (daily engagement limit) → test habit stickiness
- DCS lifecycle programs for VSB/SMB (email sequences, success campaigns)
- Product-led improvement to core features (email, dialer, enrichment quality)

**How it drives NRR:**
- Retention improvement: 120% → 130% NRR for VSB/SMB = +10pp
- Estimated impact: ~$60M incremental expansion ARR (expansion only possible if retention foundation is strong)

**Data signals to track:**
- Quarterly NRR by segment (`FCT_ACCOUNT_QUARTERLY_NRR`)
- M3 cohort NRR by segment (under construction, Gap 3)
- Active days per month (early warning for churn, 30-day lookback)
- Churn rate by segment + primary reason (requires churn taxonomy, Gap 5)

**Risks:**
- Churn is exogenous (economy, buyer role change, competitive loss) and not product-fixable
- Credit soft-cap experiment flat so far; may not move engagement
- Low-MRR cohort growth eroding cohort quality (smaller teams = lower NRR naturally)

---

## Lever 3: Expand via Products (New Bets)

**What we're doing:**
- Dialer add-on: Field sales motion + free trial path
- Inbound Router add-on: Self-serve + GTM targeting
- AI Sheets agentic workflows: Premium GTM engineer tool (persona TBD)

**How it drives NRR (via expansion ARR):**
- Each product targets different buyer persona → less cannibalization
- Product attach rate 20-30% of core customers = $45.7M incremental ARR
- Expansion + retention together hit $115.7M target

**Data signals to track:**
- Dialer ARR ($4.1M target) vs. progress
- Inbound Router ARR ($6.4M target) vs. progress
- AI Sheets adoption by GTM engineer cohort (persona definition pending)
- Attach rate (% of teams using each add-on)
- Cohort NRR for add-on users vs. non-users

**Risks:**
- Inbound Router: GTM Engineer adoption is new motion; attach rate uncertain
- Dialer: Parallel dial feature not yet launched; Q1 traction (170 teams, $300k) is above plan but retention unknown
- AI Sheets: Persona definition still pending (Gap 2); can't target until defined
- Product quality risk: If dialer has high churn, expansion ARR can be negative

---

## Lever 4: Expand via Seats (Organic)

**What we're doing:**
- Customer success initiatives for MM+Ent (dedicated CSM attach)
- Success playbooks for VSB/SMB (automated email sequences, in-app guidance)
- Integration partnerships (Zapier, native CRM integrations)

**How it drives NRR:**
- Seat expansion: Average 1.2 seats per team → target 1.5 seats = +25% user base
- Each seat = higher credit consumption + lower churn risk
- Estimated impact: $70M organic expansion ARR

**Data signals to track:**
- Seats per team (by segment, by cohort)
- Seat utilization (% of active users over total seats purchased)
- Team multi-use-case adoption (correlates with seat expansion)

**Risks:**
- Seat purchases are economically sensitive (budget cuts during downturn)
- VSB teams are unlikely to expand seats (mean team size ~2 users)

---

## Cohort Risk: Low-MRR Mix Shift

**What's happening:** New customer cohorts are trending smaller MRR (~$50-100/mo) vs. historical mean ($200-300/mo).

**Why it matters:** Smaller-MRR cohorts have inherently lower NRR (lower absolute dollar expansion possible) and higher churn (lower switching cost).

**Data signal:** Cohort NRR for Jan-Feb 2026 new cohorts showing signs of being 3-5pp lower than FY26 average.

**Implication:** Even if activation, retention, and expansion improve, overall NRR may flat-line if cohort quality degrades faster.

**Threshold for escalation:** If Q1 new cohort average MRR is <15% vs. FY26 average, plan is structurally at risk.

**Mitigation:** Focus acquisition on SMB+ segment (higher MRR, higher baseline NRR).

---

## Time Lag Summary

| Signal | When it Starts | When it Shows in NRR |
|--------|----------------|---------------------|
| **Activation change** | Week 1 of campaign | Month 3 (cohort NRR) |
| **Habit formation** | Week 6 post-signup | Month 3 (cohort NRR) |
| **Churn signal** | Days 30-60 post-signup | Month 1-3 (early churn, quarterly NRR lag 90 days) |
| **Seat expansion** | Month 1-3 | Month 3+ (quarterly NRR captures in current period) |
| **Product add-on** | Month 1+ | Month 3+ (captures in quarterly NRR as expansion ARR) |

**Implication:** Most strategic initiatives take 90-120 days to manifest in quarterly NRR. This is why we're over-reliant on leading indicators (activation, habit, multi-product adoption).

---

## How Jarvis Uses This

When an exec asks "Why is NRR at X?" Jarvis should:

1. **Identify the relevant levers:** Is this about retention? Expansion? Cohort quality?
2. **Pull the leading indicator:** F14D activation for retention bets, expansion ARR for product bets, cohort MRR for mix concerns
3. **Provide context:** "NRR is 124% (target 130%). Retention is strong (M3 cohorts 126%), but expansion ARR is 8% below plan ($108M vs. $115.7M target). New product attach is [X]%, driven by [Dialer/Inbound/AI]. Cohort MRR trend is [up/flat/down], which is [risk/tailwind]."

**Example:** "VSB NRR is 120% (target 130%). Cohort NRR for Jan-Feb is 118% (vs. FY26 avg 125%). The miss is driven by: (1) smaller cohort MRR (-12%), (2) lower activation rate (11% vs. target 17%), (3) flat expansion ARR. Activation improvements should drive M3 reads by mid-May. Cohort quality is the bigger structural risk."

---

## See Also

- `annual_targets.md` — FY27 targets and thresholds
- `pending_definitions.md` — Data gaps blocking this analysis (Gaps 2, 3, 5, 7)
- `domain/segment_join_canonical.md` — How to slice metrics by segment
