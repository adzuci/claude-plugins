# Business State — Current Momentum (as of 2026-03-31)

**Purpose:** Living snapshot of current strategic momentum, experiments, and risks. Updated from meeting transcripts and weekly reviews.

**Audience:** Jarvis, exec leadership, analysis team
**Last Updated:** 2026-03-31 (weekly refresh cycle)

---

## The NRR Challenge (🔴 At Risk)

**Status:** VSB/SMB NRR is 2-6 points below target across recent cohorts.

**What we're seeing:**
- Jan-Feb 2026 cohorts averaging 118-122% NRR (targets: see [annual_targets.md](annual_targets.md))
- Retention is **not** the primary issue (M3 retention looking solid)
- Expansion ARR is tracking 8-10% below plan (targets: see [annual_targets.md](annual_targets.md))
- **Cohort quality risk:** New cohorts trending $50-100 MRR vs. $200-300 historical mean

**Leading indicators:**
- F14D Habit RA Rate: **11%** (target 17%, so we're 6 points behind) — this is THE canary. Now under active investigation (Jeffrey + Andrew); new Amplitude tracking events launched 3/31 for validation. Alternative metric being explored: 3+ RA Days within 7 days (could reduce experiment runtime ~25%).
- Multi-product adoption (F28D): **~31%** (target 35%, marginal)
- Month-1 churn for new cohorts: Elevated; analysis in progress

**What's being done:**
- FUX team launching onboarding redesign (ETA: mid-April) to lift activation
- **Champion Onboarding experiment launched 3/26** — replaces 20+ screen wizard with direct prospecting page with AI-generated filters pre-filled from user's website. Targets filter knowledge gap causing poor activation. Key watch metrics: record action rate and day-7 activation. Completion target: 4/24.
- DCS piloting lifecycle email sequences for VSB/SMB (early reads due mid-May)
- Product prioritizing enrichment + core email quality improvements

**Risk assessment:**
- **Low probability (10%), high impact:** Cohort quality continues degrading (mix shift to lower-MRR customers). If true, even 130% NRR targets won't hit expansion plan.
- **Medium probability (40%), medium impact:** Activation improvements flat (FUX redesign doesn't move needle like prior attempts). Need 3-4pp lift; historical launches moved 1pp.
- **Threshold:** If Q1 new cohort avg NRR is <118%, recommend replan expansion mix or adjust growth targets.

---

## Product Bet Momentum (🟡 Mixed Signals)

### Dialer Add-On

**Status:** 🟡 Churn risk emerging (Previously 🟢 On track)
- **Q1 traction:** 170 teams, ~$300k ARR (vs. plan to ramp to $4.1M FY27)
- **Key signal:** Parallel dial feature launching in April (expected 20-30% adoption lift)
- **NEW — Churn spike flagged (Anvitha, Mar 30):** Top of funnel healthy, but churn spike requires root cause analysis. Lifecycle marketing now targeting users who purchased add-on but haven't completed setup (high churn risk). Interviews revealed data quality and pricing as top churn complaints.
- **Next milestone:** M3 cohort retention read (due mid-April). Need 90%+ M3 NRR to signal repeatability.

### Inbound Router Add-On

**Status:** 🟡 Unclear (limited data)
- **Q1 traction:** ~$300k ARR, 170+ teams
- **Key question:** Is this cannibalization from Dialer or incremental expansion?
- **NEW — Churn spike also flagged for Inbound (Anvitha, Mar 30):** Same investigation as Dialer; top of funnel healthy but churn needs root cause.
- **Risk:** GTM Engineer persona adoption not yet measurable (Gap 2). Can't segment to understand who's buying.
- **Next milestone:** Product team to define GTM Engineer cohort by Q2. Until then, treating as experimental.

### AI Assistant / AI Sheets / Agentic Workflows

**Status:** 🔴 Retention declining (Previously 🟡 Experimental)

**AI Assistant (new this week):**
- **Paid Core actives:** 9,110 — second straight week of decline since GA spike (Previously 9,522 → now 9,110, -4.3% WoW)
- **W4 retention:** 10.5% (Previously 11.7% LW → now 10.5%; well below Q1 baseline of 13.4%)
- **W1 retention:** 22.5% — also dropped second straight week
- **Root cause (Pubudu analysis):** Getting D1=1 message users to D1=4-9 messages roughly doubles retention. First response needs to deliver immediate value.
- **Sequence Builder AI experiment rolled back 3/26** — flat on success metric, stat-sig decline in sequence creation
- **AI Default Fields Exp 3.2 (Active Opt-In)** launched 3/23, ramped to 100% — showing expected stat-sig decline in power up credit teams (consent-first design). W4 retention at 16.5% (lowest since Dec 7, below 21% baseline).

**AI Power Up Credits:**
- Weekly credit use: 11.2M (recovered from 10.0M LW, back to Q1 baseline but 1.2M below Q1 goal of 12.4M)

**AI Sheets / Agentic Workflows:**
- **Constraint:** Persona definition still in progress (Adhiraj + AI PM)
- **Data gap:** No metric yet for "AI Sheets power user" — can only measure "general AI WAU"
- **Q1 AI WAU:** ~8K (target 15K by year-end)
- **Q1 AI credit consumption:** ~3M credits/month (target 27M by year-end)
- **Risk:** If persona definition delays past Q2, can't target GTM Engineer motion; entire AI Sheets bet may need reprior.

### CRM

**Status:** 🟢 Strong
- **CRM actives at all-time high: 6,237 users** (new signal this week)

---

## Activation Initiatives (🟡 In Flight — Investigation Active)

**Current read:**
- F14D Habit RA Rate stuck at **11%** for past 6 weeks (target: 17%). Now confirmed declining over last two months (Jeffrey + Andrew investigation active).
- **New Amplitude tracking events for Habit RA launched 3/31** — will require validation against existing SoT
- **Alternative metric being explored:** 3+ RA Days within 7 days (could reduce experiment runtime ~25%)
- **Champion Onboarding experiment launched 3/26** (completion target 4/24) — key intervention replacing the multi-step wizard with AI-generated prospecting page
- **Hypothesis:** FUX friction is the blocker; multi-step onboarding causing drop-off
- **Intervention:** Redesigned flow launching mid-April (5-step → 2-step, faster time-to-first-action)
- **Success criteria:** 2-3pp lift in 2 weeks post-launch (i.e., 13-14% by early May)

**If activation doesn't move:** Recommend investigating product quality (is early value actually there?) vs. UX friction.

---

## Retention Experiments (🟡 Mixed)

**Credit Soft-Cap Experiment (Daily Limit):**
- **Hypothesis:** Artificial daily limit forces habit-forming checkpoints and increases engagement
- **Current read:** **Flat to slightly negative** (no engagement lift; some churn complaints)
- **Status:** Deprioritized; not being promoted wider
- **Lesson:** Engagement is driven by perceived value, not artificial constraints

**DCS Lifecycle Programs (Email + In-App):**
- **Status:** Piloting with 2K VSB teams (start: March 1)
- **Early signals:** Email open rate 35% (decent), but click-through low (~8%)
- **Next phase:** Content iteration based on click data; measure retention lift in May cohorts

**Deliverability Enforcement Experiment (new this week):**
- **Status:** Rolled out to 50% after no significant guardrail drops
- **Support tickets:** Tracking as expected
- **Concern:** ~40 Apollo internal mailboxes have >10% bounce rate; some metrics not trending right — needs revisiting
- **Next:** Catch-all domain blocking feature planned this quarter

---

## Expansion Tracking (🟡 Below Plan)

**Organic Expansion (Seats + Credits):**
- **Current:** $95M ARR (plan: $70M organic, $45.7M from products = $115.7M total)
- **Miss:** -$10M vs. plan (organic slightly above, but products lagging)
- **Drivers:**
  - Seats per team: Flat at 1.2 avg (no strong seasonality in Q1)
  - Credit utilization: Steady; soft-cap experiment didn't increase

**New Product Expansion:**
- **Dialer:** $300k (early, but churn spike now flagged — previously tracking well)
- **Inbound:** $300k (data unclear if incremental or cannibalistic; churn also flagged)
- **AI Sheets:** $0 (product not yet launched in volume)
- **Total:** $600k (plan: $45.7M by year-end) → **massive gap; too early to call it risk yet**

**Growth Initiatives (new this week):**
- **Free plan restrict mobile numbers:** 10-day alert period launched 3/24 → already generated **$60K net new ARR**. Enforcement period starts after alert window.
- **Free to Paid Upgrade Modal:** +6.4% relative lift on new purchases, but CI crosses 0 — needs more sample, running through early April
- **One Seat Org Plan analysis:** Estimated -$1.5M downgrade risk from removing 3-seat minimum; routed to experimentation

---

## Data Quality & Gaps Impacting Strategy

**Critical blockers:**

1. **Gap 3 (Segment denormalization): RESOLVED** — LU_TEAM_SEGMENT lookup table complete (Bridie, 2026-03-30). Cohort NRR by segment views now unblocked; build by early April.

2. **Gap 7 (Activation in Snowflake):** F14D Habit RA Rate is Amplitude-only; can't validate from warehouse events.
   - **Impact:** Over-reliant on DS team; can't build Jarvis automation
   - **Update:** New Amplitude tracking events launched 3/31; validation against existing SoT required
   - **ETA:** Adhiraj building DIM_ACTIVATION table (mid-April estimated)

3. **Gap 2 (AI Sheets persona):** No data definition for "AI Sheets power user" or "GTM Engineer" cohort.
   - **Impact:** Can't measure AI Sheets attach rate, can't target motions
   - **ETA:** Adhiraj + AI PM (end of Q2 estimated)

**New data milestones:**
- **Paid WAT inbound usage added** to all 4 dim tables (backfilled from 2025-01-01). Inbound NOT included in WAU logic yet — currently counts page lands only. API usage also added to dim_users/dim_teams.
- **Data Duels (Salesforce) data now in Snowflake via Fivetran** (Mounica) — still being QA'd; unblocks vendor evaluation sample work
- **Jarvis eval system bootstrapped (Mar 31):** First scorecard run — 23.1% pass rate (3/13), mean score 57.5. Six root cause fixes committed.

---

## What's Working ✅

- **Cohort quality for premium segment:** MM+Ent cohorts are tracking 140%+ NRR (strong organic base)
- **Dialer early traction:** 170 teams in 60 days signals product-market interest (though churn spike now under investigation)
- **Multi-product adoption:** 31% of new cohorts activating 2+ features (approaching target)
- **CRM at all-time high:** 6,237 actives (new signal)
- **Free plan mobile restrict:** $60K ARR in first 10 days of alert period (new signal)
- **AI Power Up credits recovering:** 11.2M (back to Q1 baseline from 10.0M low)

---

## What's Flat / Concerning 🟡

- **Activation rate:** Stuck at 11% for 6+ weeks (target 17%; -6pp). Now confirmed declining over 2 months.
- **Expansion ARR:** $108M actual vs. $115.7M plan (-8%)
- **Cohort MRR trend:** Declining 12% vs. FY26 average (structural risk)
- **AI Assistant retention declining:** W4 at 10.5% (Previously 13.4% Q1 baseline → now 10.5%), actives down 4.3% WoW to 9,110
- **Dialer + Inbound churn spike:** Flagged by Anvitha; root cause investigation needed
- **AI Default Fields W4 retention:** 16.5% (lowest since Dec 7, below 21% baseline)

---

## Immediate Priorities (Next 4 weeks)

1. **Champion Onboarding experiment read** (launched 3/26, completion 4/24) — key activation intervention
2. **Activation redesign launch** (mid-April) + 2-week read
3. **Cohort NRR by segment** (LU_TEAM_SEGMENT now live; build cohort views by early April)
4. **Dialer + Inbound churn root cause** (Anvitha investigation; lifecycle marketing targeting setup-incomplete users)
5. **Dialer M3 retention read** (mid-April; go/no-go for scale)
6. **AI Assistant retention diagnosis** — D1 engagement strategy; first-response value delivery
7. **Bulk Record Action experiment results** (available 4/7)
8. **DCS program iteration** (iterate content based on Week 2-3 engagement data)
9. **Validate new Habit RA Amplitude events** (launched 3/31) against existing SoT

---

## Escalation Thresholds

| Signal | Threshold | Action |
|--------|-----------|--------|
| **Activation rate drops below 10%** | <10% | Emergency FUX review; consider UX A/B test redesign |
| **Dialer M3 NRR drops below 85%** | <85% | Product review; may pause scaling |
| **Cohort NRR misses Q1 by >4pp** | <126% for new cohorts | Escalate to leadership; replan expansion targets |
| **Expansion ARR drops below $100M** | <$100M | Trigger product review + sales motion audit |

---

## How Jarvis Uses This

When an exec asks "How are we doing?" Jarvis should reference this file to provide context:

**Example response:**
> "We're tracking 124% VSB NRR (target 130%). Behind plan by 6 points. The issue is _not_ churn (retention is solid) but _expansion ARR is 8% below plan_. Activation rate is our canary — stuck at 11% (target 17%). We're launching FUX redesign in mid-April that should move this by 2-3 points. Cohort quality is a structural risk (new cohorts 12% lighter MRR than FY26). Once Bridie's segment lookup is live, we can see if this is a mix issue or a retention issue per segment."

---

## Last Updated

- **2026-03-30:** Initial write. Activation flat (11%), Dialer at $300k (early), DCS piloting, NRR below plan, cohort quality risk flagged.
- **2026-03-31:** Weekly refresh. AI Assistant retention declining (W4 10.5%, was 13.4% baseline; actives 9,110 -4.3% WoW). Dialer + Inbound churn spike flagged (Anvitha). Champion Onboarding experiment launched 3/26. Free plan mobile restrict generating $60K ARR. CRM at ATH (6,237). Gap 3 (LU_TEAM_SEGMENT) resolved. New Habit RA Amplitude events launched. Deliverability enforcement at 50%. AI Power Up credits recovered to 11.2M.
