# FY27 Annual Targets — Jarvis Reference

**Purpose:** Single source of truth for AOP commitments that Jarvis should reference without being told.
**Audience:** Jarvis, analysts answering exec questions
**Updated:** 2026-03-30
**Source:** AOP (reviewed in aop_fy27_strategic_priorities.md, fy27_aop_analytics.md)

---

## NRR Targets (Highest Priority)

| Segment | FY26 Baseline | FY27 Target | Improvement | Notes |
|---------|---------------|------------|-------------|-------|
| **VSB** | ~120% | 130% | +10 points | Primary focus; home to 88.7% of teams |
| **SMB** | ~118% | 128% | +10 points | Secondary focus; 6.2% of teams |
| **MM+Ent** | 145%+ | Maintain | Sustain | Lower risk, higher inherent retention |

**Why this matters:** NRR is the #1 exec OKR for FY27. The VSB/SMB +10 point lift drives $115.7M expansion ARR target. If not achieved, entire growth plan at risk.

---

## Activation (Leading Indicator for NRR)

| Metric | FY26 Baseline | FY27 Target | Segment | Notes |
|--------|---------------|------------|---------|-------|
| **F14D Habit RA Rate** | ~12% | 17% | Golden Pop (SMB+, AMER/EMEA) | 4+ Record Actions in first 14 days post-signup. Key leading indicator. |

**Why this matters:** Activation drives early engagement → habit → retention. This metric is the canary for whether the NRR +10pt improvement plan is working.

**Current status:** Measured in Amplitude/Hex only; not yet in Snowflake (Gap 7).

---

## Expansion ARR Target

| Category | FY27 Target | Notes |
|----------|------------|-------|
| **Total Expansion ARR** | $115.7M | Net new ARR from existing customers (seats, credits, plans) |
| **Seats + Credits** | ~$70M | Organic feature adoption + credit limit increases |
| **New Products** | ~$45.7M | Dialer ($4.1M), Inbound ($6.4M), AI Sheets for GTM (TBD) |

**Why this matters:** Expansion is the biggest lever for growth when new customer acquisition is steady. Depends on retention + adoption.

---

## Product Bet Targets (H2 — Strategic Bets)

| Product | ARR Target (FY27) | Intended Buyer | Status | Notes |
|---------|------------------|-----------------|--------|-------|
| **Dialer Add-on** | $4.1M | AE-led motion; field teams | Beta→Paid | Parallel dial, IVR. Early product-market signals. |
| **Inbound Add-on** | $6.4M | Self-serve; SDR/BDR teams | Beta→Paid | Lead routing. Early traction: $300k+ Q1, 170 teams. |
| **AI Sheets (Agentic)** | TBD (stretch) | GTM Engineer (RevOps, ops roles) | Experimental | Workflow automation. Persona definition pending (Gap 2). |

**Why this matters:** These products deliver the $45.7M new-product expansion. Each bet has graduation criteria (ARR threshold, NRR floor, attach rate).

---

## AI Adoption Target (FY27)

| Metric | FY27 Target | Current (as of Q1) | Notes |
|--------|------------|------------------|-------|
| **AI Assistant WAU** | 15K | TBD (growth phase) | Weekly active users on AI Assistant threads. |
| **AI W4 Retention** | 20% | TBD | Week-4 retention for AI feature users. |
| **AI Credit Consumption** | 27M credits/month | TBD | Monthly credit burn; signals feature adoption. |

**Why this matters:** AI is the strategic priority ("AI Native GTM operating system"). These metrics track whether the bet is working.

---

## Revenue Per Employee (Operating Metric)

| Metric | FY27 Target | Current | Notes |
|--------|------------|---------|-------|
| **$ARR / Headcount** | $300k per employee | TBD | Operating efficiency metric. ARR is known; headcount source TBD (Gap 14). |

**Source of truth:** Finance owns headcount; Analytics owns ARR. Requires coordination.

---

## Pipeline Health (Sales Motion)

| Metric | FY27 Target | Notes |
|--------|------------|-------|
| **MM+Ent New Logos** | 680 | Sourced from S1→S2 conversion, deal size, velocity. |
| **S1→S2 Conversion Rate** | TBD | Stage-to-stage funnel health. SFDC-sourced. |
| **Average Contract Value (ACV)** | $50k+ (stretch) | Enterprise deals trending higher. |

---

## Credit Targets

| Credit Type | FY27 Target | Notes |
|-------------|------------|-------|
| **Total Unified Credits** | Migrate 40%+ of customer base | Unified credit system replacing per-feature credits. |
| **Email Credits** | ~2.5B annually | Foundational; highest volume. |
| **Direct Dial Credits** | Grow 25% YoY | Dialer adoption driving this. |
| **AI Credits** | Grow 40% YoY | AI feature adoption; part of AI Native bet. |

---

## CSM / Digital Customer Success Targets (VSB/SMB)

| Metric | FY27 Target | Notes |
|--------|------------|-------|
| **DCS Churn Reduction** | -5 percentage points | Digital-only playbooks for self-serve segments. |
| **Automated Lifecycle Program Adoption** | 60% of new VSB/SMB | Email/in-app success motion. |

---

## Risk Thresholds (Triggers for Escalation)

| Risk | Threshold | Implication |
|------|-----------|------------|
| **NRR miss (VSB/SMB)** | Falls below 122% | Plan at risk; replan expansion mix |
| **Activation miss** | F14D < 14% | Leading indicator failure; product issues likely |
| **Bet graduation miss** | Dialer ARR < $2M by Q2 | May be unfixable; consider resource reallocation |
| **Cohort churn (new)** | >30% Month-1 churn | Onboarding broken; emergency product review |

---

## How Jarvis Uses This

When an exec asks "Are we on track?" Jarvis should:
1. Look up the relevant target(s) from this file
2. Query the actual value from Snowflake
3. Show the delta
4. Flag if it's at risk (crossing threshold)

**Example:** "VSB NRR target is 130%. Current: 124% (Q1 read). Delta: -6 points (at risk). Need cohort analysis to understand if it's a mix shift or retention problem."

---

## Known Gaps / Caveats

- **Headcount source:** Finance owns this; path to Snowflake TBD (Gap 14)
- **AI Sheets ARR target:** Still a stretch goal; product persona definition pending (Gap 2)
- **Partner ARR:** PartnerStack pipeline not yet in Snowflake (Gap 4)
- **F14D activation in Snowflake:** Amplitude-only for now; warehouse version in progress (Gap 7)

See `pending_definitions.md` for full gap list.
