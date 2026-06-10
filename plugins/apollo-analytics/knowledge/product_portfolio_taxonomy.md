# Product Portfolio Taxonomy — Horizon Framework

**Purpose:** Classify Apollo's product surface into strategic horizons and investment tiers. Jarvis uses this to answer "Is this bet on track?"

**Audience:** Jarvis, exec leadership, product management
**Date:** 2026-03-30
**Owner:** Bridie Meredith, Leo Liu (strategy)

______________________________________________________________________

## Horizon Framework

Apollo operates on a three-horizon framework:

### **Horizon 1 (H1) — Core, Revenue-Sustaining**

Products that define Apollo's core value prop. Mature, high volume, essential to retention.

| Product | Description | Key Metric | FY27 Target |
|---------|-------------|-----------|------------|
| **Email (Outreach)** | Multi-touch email sequences, templates, deliverability | Email volume, DAU | Grow 15% |
| **Enrichment (Contact + Company)** | B2B data and skill matching | Enrichment credits, success rate | 2.5B email credits, 10% quality lift |
| **GenPipe Traditional** | Manual lead generation pipeline | Leads created, cost per lead | Improve 20% COGS |
| **CRM Management** | CRM record mgmt, field data capture | Active teams, seat utilization | Grow 12% |
| **Dialer (Core)** | Click-to-call, recordings, voicemail drops | Call volume, conversion | 5% adoption lift |

**Investment approach:** Optimize (not maximize). Maintain high NRR, improve COGS, drive attach through multi-product.

______________________________________________________________________

### **Horizon 2 (H2) — Strategic Bets**

Products proving repeatable business model, in scale-up phase. Each has ARR target in AOP.

| Product | ARR Target (FY27) | Intended Buyer | Launch Status | Bet Graduation Criteria |
|---------|------------|-----------------|----------------|--------------------------|
| **Dialer Add-on** | $4.1M | Field reps, AEs | GA (soft launch) | M3 NRR 90%+, attach 20%+ |
| **Inbound Add-on** (website visitor tracking + router; see `domain/inbound.md`) | $6.4M | SDRs, BDRs | Beta→GA (Q2) | M3 NRR 90%+, attach 15%+ |
| **AI Sheets / Agentic Workflows** | Stretch (TBD) | GTM Engineer (RevOps) | Pilot (Persona TBD) | Persona definition Q2; then 10K WAU by Q4 |

**Investment approach:** Scale. Feature launch, GTM motion, sales enablement, product iteration based on early signals.

**Graduation criteria** (when a bet becomes H1):

- ARR achievement: Dialer $4.1M, Inbound $6.4M (both by EOY)
- Retention: Cohort NRR ≥ 90% at M3 (indicates repeatable unit economics)
- Attach rate: 20%+ of core customers using feature (indicates scalable motion)
- Churn risk: \<10% of product attach churned due to product quality (indicates sustainable)

**Demotion criteria** (when a bet should be slowed or cut):

- By end of Q2, if Dialer M3 NRR < 85% → consider slowdown
- By end of Q2, if Inbound attach rate < 10% → reconsider GTM
- If AI Sheets persona not defined by Q2 → deprioritize

______________________________________________________________________

### **Horizon 3 (H3) — Experiments**

Early-stage ideas, limited cohorts, not yet in AOP.

| Product | Status | Next Gate | Notes |
|---------|--------|-----------|-------|
| **GenPipe NextGen (AI-native)** | Experimental | Product-market fit (Q3) | Testing smarter pipeline generation. |
| **Win/Close** | Early (limited beta) | Attach rate validation (Q3) | Closing deal tracking + notes. |
| **Parallel Dial** | Experimental (within Dialer) | Feature adoption in H2 Dialer (Q2) | Simultaneous multi-call feature. |
| **Conversation Intelligence** | Platform capability (not packaged) | GTM motion TBD | Call/email analysis; not yet monetized. |

**Investment approach:** Explore. Small team, customer feedback loops, learn-fast mindset.

**Graduation criteria:** Product-market fit signals (cohort NRR 110%+ OR attach rate 25%+), then move to H2.

______________________________________________________________________

## How to Use This Framework

### For Jarvis answering "Is this bet on track?"

1. **Identify the product** in the table above (is it H1, H2, or H3?)
1. **Find its target** (ARR, attach rate, NRR, etc.)
1. **Query current performance**
1. **Evaluate vs. graduation criteria**

**Example:**

> **Exec:** "Is Dialer add-on on track?"
>
> **Jarvis:** "Dialer is an H2 bet with $4.1M FY27 ARR target. Current: $300k (60 days in). Graduation criteria: M3 NRR ≥ 90%, attach ≥ 20%. Early data shows ~170 teams (2.7% of potential market), suggesting attach may undershoot. M3 cohort retention due mid-April — that read will determine whether to accelerate, maintain, or slow. Currently tracking as "on plan but early."

### For Exec decision-making

When a product reaches the end of a quarter without hitting its H2 metrics:

| Scenario | Decision |
|----------|----------|
| ARR on track, M3 NRR ≥ 90%, attach ≥ 15% | **Accelerate:** More sales/marketing investment |
| ARR behind but M3 NRR 85-90%, attach 10-15% | **Maintain:** Fix go-to-market, iterate product |
| M3 NRR < 85% or attach < 10% | **Slow or cut:** Product-market fit unproven; redeploy resources |

______________________________________________________________________

## Mapping to Data Tables

| Horizon | Data Source | Grain | Refresh |
|---------|------------|-------|---------|
| **H1 Core** | `FCT_DAILY_REVENUE` (primary), `AGG_TEAM_CREDITS` (feature), `TEAM_DAILY_SOLUTION_USAGE` | Team × Day | Daily |
| **H2 Bets** | `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` (add-ons by source), `TEAM_AI_ASSISTANT_DAILY` (AI metrics) | Team × Day | Daily |
| **H3 Experiments** | Product-owned dashboards (not yet synced; Hex/Amplitude) | TBD | Ad-hoc |

______________________________________________________________________

## Known Gaps / Caveats

- **AI Sheets:** Persona definition (GTM Engineer) still in progress (Gap 2). Until defined, can't segment attach rate to target buyer.
- **Dialer:** M3 retention due mid-April; only 60 days of data so far. Early signals are positive but not yet decisive.
- **Inbound:** Unclear if $300k attach is incremental or cannibalization from Dialer. Next phase: product team to clarify positioning.

______________________________________________________________________

## Related Files

- `annual_targets.md` — FY27 targets
- `theory_of_change.md` — How each product layer drives NRR
- `business_state.md` — Current momentum on each bet
