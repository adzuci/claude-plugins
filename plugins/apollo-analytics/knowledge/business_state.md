# Business State — Current Momentum (as of 2026-06-04)

**Purpose:** Living snapshot of current strategic momentum, experiments, and risks. Updated from meeting transcripts and weekly reviews.

**Audience:** Jarvis, exec leadership, analysis team
**Last Updated:** 2026-06-04 (weekly refresh)

______________________________________________________________________

## The NRR Challenge (🔴 Watch)

**Status:** Q2 OKR check-in started May 15. Active churn risk from credit-ceiling pattern and waterfall extraction signal. Churn model v2 watch list now delivered to GTME — response gap is the primary lever.

**Current signals (May–June 2026):**

- **Credit ceiling churn**: Leo case study (homebuildvalet.com) confirmed pattern — $145K ARR silent exit after credit frustration + data quality eval. Zero GTME touch. Three ML churn flags ignored (unassigned). Support ticket upsell signals not feeding signal pipeline.
- **Waterfall spike is churn extraction**: Top 10 waterfall spenders May 5–11 — 6/10 churning or at-risk. Organic waterfall base down ~15%.
- **Renewal infrastructure live**: Canonical renewal queries at 98% match to rep BOB. Churn model v2 delivered (see below).
- **HVO experiment cancelled**: Insufficient sample size; no good short-term NRR predictors confirmed by Andrew.
- **Churn model v2 watch list delivered (May 27):** Rep Managed AUC-ROC 0.886, captures 70.7% of churn ARR ($13.3M of $18.8M). Self-Serve AUC-ROC 0.801, captures 80.2% ($67.7M of $84.5M). GTME_Churn_Watch_List_5_18_26 delivered with team-level risk scores. `/churn-debrief` skill now available with 6-month historical backtest and drift detection (Cat Zhou, Jun 1).
- **⚠️ GTME churn response gap (May 27):** 67% of churners were flagged by model, but 27% of flagged churners saw no CSM activity increase before churning. The problem is response speed, not signal coverage.
- **⚠️ Seat utilization risk escalating (NEW Jun 1):** 16.3% of GTME-managed ARR in low-utilization (1–25%) bucket — highest Q2 reading, ~2.6pp above Q1 avg. **50K+ ARR cohort jumped to 24.0% (previously 21.5%)** for second straight week; this cohort is in renewal territory. Rep attention warranted.

**Q2 targets (from OKR tracker):**

- VSB NRR 130% (+10pt) | SMB NRR 128% — hot in discussion
- Expansion ARR $115.7M — below plan as of Q1 closeout

**Intervention pipeline (updated Jun 4):**

- **Intervention close rate:** 18% (88/489 cases; previously 16.6% / 81 cases). Median time-to-close 17 days. `bad_domain_health` is primary throughput lever (188 open cases, avg age 28.9 days).
- **⚠️ Waterfall intervention near-zero throughput (NEW Jun 4):** `waterfall_enrichment_credits_drop` has 1/35 complete — essentially zero rep-driven closure. Decision: audit waterfall auto-resolve path.
- DCS lifecycle programs: Read from May cohorts expected.
- GTME signals pipeline: 3 new signals live (seat utilization, MCP activation, upsell potential for credit-limit teams). Credit upsell signal and seat utilization rate added May 26 (Shyam).
- Support ticket → signal pipeline: Under evaluation (Shyam).

______________________________________________________________________

## Product Bet Momentum (🟡 Mixed Signals)

### Dialer Add-On

**Status:** 🟡 Churn risk emerging (Previously 🟢 On track)

- **⚠️ Last data point: Q1 ($300K ARR, 170 teams). No updated read since March 2026 — Dialer churn spike flagged (Anvitha) but no follow-up data available.**
- **Churn spike flagged (Anvitha, Mar 30):** Top of funnel healthy, but churn spike requires root cause analysis. Lifecycle marketing now targeting users who purchased add-on but haven't completed setup (high churn risk). Interviews revealed data quality and pricing as top churn complaints.
- **⚠️ M3 NRR read was due mid-April — no results surfaced. Stale.**

### Inbound Router Add-On

**Status:** 🟡 Unclear (limited data)

- **⚠️ Last data point: Q1 (~$300K ARR, 170+ teams). No updated read since March 2026.**
- **Key question:** Is this cannibalization from Dialer or incremental expansion?
- **Churn spike also flagged for Inbound (Anvitha, Mar 30):** Same investigation as Dialer; top of funnel healthy but churn needs root cause.
- **Risk:** GTM Engineer persona adoption not yet measurable (Gap 2). Can't segment to understand who's buying.
- **⚠️ GTM Engineer cohort definition was due by Q2 — no update surfaced. Stale.**

### AI Assistant / Context Center / MCP

**Status:** 🔴 Actives declining, retention collapsing, Cerberus experiment null — no near-term retention lever identified

**AI Assistant (week of May 31):**

- **⚠️ Paid Core actives: 11,510** (previously 12,807 → now 11,510; -10.1% WoW). Third consecutive weekly decline. Recovery arc from March lows is definitively broken.
- **⚠️ W4 retention: 10.9%** (previously 12.7% → now 10.9%; -1.8pp WoW). Now well below Q1 13.4% baseline and trending worse every week.
- **W1 retention:** 23.8% (flat, previously 24.2%)
- **AI Power Up weekly credits:** 9.1M (previously 10.1M → now 9.1M; -9.9% WoW). Expected decline after active opt-in rollout.
- **Default Fields W4 retention:** 14.3% (↑ slight from 13.6% — one bright spot)
- **Behavioral insight:** Returning W1–W4 users are more active than avg Paid Core but do same things. No differentiated early behavior that separates high-retention users.
- **AI credit surface attribution fix shipped (NEW Jun 4):** PR #91986 merged. Surface credits now at ~100% parity with DAPI. The 35–56% unattributed gap is closed.

**AI Sequence Builder v3 (rolled back May 25):**

- **⚠️ First hard AI experiment rollback this quarter.** Was at 20% ramp, pulled due to stat-sig decline in sequences enabled. This is a regression, not a null result.

**Cerberus (Assisted AI Email):**

- **Status:** ❌ Concluded flat (Jun 4). Ran 4 weeks from 100% 50/50 ramp (since May 7). All metrics flat after Bonferroni correction. Pubudu writing experiment review and recommendations. **Implication: no near-term AI retention lever from this experiment. AI Assistant retention OKR has no positive experiment results to point to.**

**Context Center v3:**

- **Adoption:** 229.9K cumulative teams (previously 213.6K → now 229.9K; +16.3K WoW). **Paid Core crossed 50% milestone: 50.49%** (previously 47.81% → now 50.49%; +2.7pp WoW). AI Messaging 74.0%, AI Assistant 51.9%, Power Ups 51.5%.
- **Email reply rate delta holding:** CC v3 0.485% vs Legacy 0.401% vs No CC 0.324%.
- **⚠️ Quality alert — record spike then recovery:** Generation failure rate spiked to **26.83% on May 24 (record high)**, NO_DATA_FOUND driven. Trended back to **~17.8% by May 28** — meaningful improvement from the ~24% plateau, but spike shows fragility.
- CC Agent 100% rollout May 14 (async race condition fixed).

**MCP:**

- April: 4.4M platform-wide credits. GTME: 198.9K credits, 281 teams (27.6% activation).
- Claude drives virtually all activity (267/281 GTME teams).
- **Key finding:** MCP credits volume NOT a predictor of upgrade ARR (r=0.04). Look-alike modeling in progress for upsell targeting.
- **MCP fct_apollo_mcp_requests pipeline live (May 27):** PR #2496 merged. Per-request credit attribution blocked on http_request_id (0% populated) — INCIDENT-29528 created.
- **MCP data governance shipped (NEW Jun 4):** Server-side DDL/DML gate for MCP execute-sql tool deployed. `snowflake_query.py` now also enforces data catalog access check. Snowflake egress CDC pipeline deployed.
- **MCP credits positive rebound (Jun 1):** Search→save→enrich funnel shows meaningful drop-off between discovery and enrichment; notable paid vs free differences. PSM causal NRR analysis extended to T+61.

### CRM

**Status:** 🟢 Strong

- **CRM actives at all-time high: 6,237 users** (signal from May 18)

______________________________________________________________________

## Activation Initiatives (🟡 In Flight — Investigation Active)

**Current read:**

- F14D Habit RA Rate stuck at **11%** for past 6 weeks (target: 17%). Now confirmed declining over last two months (Jeffrey + Andrew investigation active).
- **New Amplitude tracking events for Habit RA launched 3/31** — will require validation against existing SoT
- **Alternative metric being explored:** 3+ RA Days within 7 days (could reduce experiment runtime ~25%)
- **⚠️ Champion Onboarding experiment target date (4/24) passed with no published results. F14D Habit RA Rate remains at 11% — no improvement observed.**
- **Tasks usage insight (May 27, Anvitha):** Email tasks 93% done in 24h; phone batched; LinkedIn treated as backlog. One-off tasks 80–90% completion vs. sequence-generated tasks (lower). Task usage concentrated in \<20-seat teams — MM OKR segments barely using tasks. High-leverage enablement gap.

______________________________________________________________________

## Retention Experiments (🟡 Mixed → 🔴 No Positive Results)

**Credit Soft-Cap Experiment:** ❌ Closed. No engagement lift; deprioritized.

**DCS Lifecycle Programs (Email + In-App):**

- **Status:** Piloting with 2K VSB teams (start: March 1)
- **Early signals:** Email open rate 35% (decent), but click-through low (~8%)
- **⚠️ Pilot started March 1 — retention lift read was expected from May cohorts but no results published.**

**Deliverability Enforcement Experiment:**

- **⚠️ Last update March 2026. Was at 50% rollout. No recent signal.**
- **Concern (March):** ~40 Apollo internal mailboxes have >10% bounce rate; some metrics not trending right — needs revisiting
- **Next:** Catch-all domain blocking feature planned this quarter

**AI Sequence Builder v3 (rolled back):**

- **Status:** Rolled back May 25 after stat-sig decline in sequences enabled at 20% ramp. First confirmed negative AI experiment outcome this quarter. Not a null result — a regression.

**Cerberus (Assisted AI Email):**

- **Status:** ❌ Concluded flat (Jun 4). 4-week read: all metrics flat after Bonferroni correction. No lift, no harm. This is a null result. No near-term AI retention lever from this experiment.

**"Powered by Apollo" free plan branding (NEW — in design):**

- **Status:** Active PRD for email branding on free users. Target: detect ≥11% relative lift on 2.91% blended baseline. Experiment audience expanded to include extension users. P1 requirements defined; blocked on dev.

**AI Voice Assistant for search→save (NEW — in design):**

- PRD for AI-guided assistant at first search. Target: lift search→save conversion for new users. Phase 1 (SDK + FF) in design; Phase 2 (in-app experiment) TBD. Jeffrey to define MDE before start.

**Finder default columns A/B (NEW — scoped):**

- People Finder + Company Finder column reorganization experiments scoped by eng. ~4–6 dev days combined. Waiting on product/design column decision before build.

______________________________________________________________________

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

**Growth Initiatives:**

- **Free plan restrict mobile numbers (⚠️ data as of 3/24):** 10-day alert period launched 3/24 → generated **$60K net new ARR**. Enforcement period started after alert window. No subsequent update.
- **Free to Paid Upgrade Modal (⚠️ data as of early April):** +6.4% relative lift on new purchases, but CI crosses 0 — was running through early April. No results published.
- **One Seat Org Plan analysis (⚠️ no update):** Estimated -$1.5M downgrade risk from removing 3-seat minimum; routed to experimentation. No follow-up.

______________________________________________________________________

## Data Quality & Gaps Impacting Strategy

**All 12 executive measurement gaps now closed (Jun 2).** `domain/measurement_gap_tracker.md` confirms minimum-viable Snowflake coverage for every gap including trial conversion, partner sourcing, churn reason taxonomy, FTP cohorts, and M3 cohort NRR. New lookup tables: LU_INBOUND_TEAMS, LU_WEEKLY_INSIGHTS, LU_PARTNER_SOURCED_TEAMS, LU_FTP_COHORT_W2, LU_M3_COHORT_NRR, LU_TEAM_ACTIVATION_F14D, LU_INTERVENTION_ARR_ATTRIBUTION, LU_CHURN_REASON_TAXONOMY, PRODUCT_METRICS_DAILY.

**Residual gaps (non-blocking):**

1. **Gap 7 (Activation in Snowflake): Partially resolved.** F14D Habit RA Rate is Amplitude-only; can't validate from warehouse events. However, `LU_TEAM_ACTIVATION_F14D` now provides lookup coverage and `dim_teams` has habit RA date column.

   - **Impact:** Reduced dependency on DS team; Jarvis automation partially unblocked.
   - **Update:** New Amplitude tracking events launched 3/31; validation against existing SoT required.
   - **ETA:** ⚠️ Adhiraj building DIM_ACTIVATION table (mid-April estimated — past due, no update)

1. **Gap 2 (AI Sheets persona):** No data definition for "AI Sheets power user" or "GTM Engineer" cohort.

   - **Impact:** Can't measure AI Sheets attach rate, can't target motions
   - **ETA:** ⚠️ Adhiraj + AI PM (end of Q2 estimated — Q2 closes soon, no update)

**Schema migration:**

- **PLAYGROUND → JARVIS migration complete (Jun 2–4):** All tables moved from `ANALYTICS_DB.PLAYGROUND` to `ANALYTICS_DB.JARVIS`. 116 files repointed. Shim views left in place for backward compatibility.

**New data milestones:**

- **All 12 measurement gaps closed (NEW Jun 2):** See above.
- **Churn debrief skill with drift detection (NEW Jun 1):** `/churn-debrief` runs 6-month historical backtest of Rep-Managed v2 predictions vs actuals. Leading indicator: weekly HIGH_RISK flag rate; lagging: hit rate vs actuals.
- **Extension debrief skill (NEW Jun 3):** Valery's `/extension-debrief` with 13 canonical SQL queries (Q0–Q12). First live debrief shipped.
- **MCP data governance shipped (NEW Jun 4):** Server-side DDL/DML gate deployed. Python connector path now enforces catalog access check.
- **Switchboard PreToolUse gate shipped (NEW Jun 4):** `scripts/switchboard_gate.py` blocks Snowflake queries when context routing hasn't fired.
- **Intelligence snapshots committed (May 22):** growth_revenue_health, mcp_platform_health, product_engagement_health, meeting_booked_weekly, gtme_enterprise_health, operations_trust_health.
- **Data catalog updates (May 21–27):** INTERVENTIONS.md (grain, suppression logic, IS_ACTIONABLE resolved), HVO_CALLS_AI_PROCESSING.md, DIM_INTERCOM_CUSTOMER_CHAT_LOGS.md, DIM_USERS.md updated. METRIC_SPECS.md added. Glossary now 47 terms; 26 approved / 3 draft saved metrics.
- **Employee activity scaffold (May 27):** LU_EMPLOYEE_ACTIVITY pipeline instrumented; Gong source live (67 employees), Jira/Slack pending CI secrets.
- **dim_teams enriched (May 27):** SIC industry classification fields added; habit RA date column added.
- **⚠️ Jarvis pulse data stale (35 days as of Jun 4):** FCT_JARVIS_PULSE_DAILY was stale — root cause: all 3 Jarvis pulse tasks (TASK_JARVIS_PULSE_DAILY, \_HEALTH, \_RETENTION) were suspended. Resumed Jun 4. **Any Jarvis usage metrics are unreliable until pulse backfills (~2–3 days).** Do not cite Jarvis adoption numbers until pulse data is current.

______________________________________________________________________

## What's Working ✅

- **CC v3 Paid Core crossed 50% milestone:** 229.9K teams (previously 213.6K), **50.49% Paid Core** (previously 47.81%); +16.3K teams WoW. Email reply rate delta holding (0.485% vs 0.324% No CC). AI Messaging 74.0%, AI Assistant 51.9%, Power Ups 51.5%.
- **CC v3 failure rate improving:** Generation failure rate trended down to ~17.8% (from ~24% plateau), though spiked to 26.83% on May 24 before recovering.
- **AI credit attribution gap closed:** PR #91986 shipped. Surface credits now at ~100% parity with DAPI. The 35–56% unattributed gap from WaterfallEnrichmentExecutionWorker overwrite is resolved.
- **All 12 measurement gaps closed:** Every exec-visible gap now has minimum-viable Snowflake coverage.
- **Churn model v2 delivered + debrief skill live:** Both Rep Managed (AUC-ROC 0.886) and Self-Serve (AUC-ROC 0.801) models live with watch list in GTME hands. `/churn-debrief` now provides 6-month backtest with drift detection.
- **MCP momentum + governance:** GTME +142% MoM, Claude dominates (267/281 teams). Platform-wide 4.4M credits/month. Server-side DDL/DML gate and catalog access check deployed.
- **Intervention pipeline operational:** 489 cases, 18% close rate (previously 16.6%). `bad_domain_health` backlog identified as primary lever.
- **PLAYGROUND → JARVIS migration complete:** 116 files repointed, shim views in place.
- **Deliverability infrastructure:** Q2 OKR features instrumented, enforcement-v2 in flight
- **Signals pipeline expanding:** Credit upsell signal, seat utilization rate, MCP activation status added (Shyam, May 26). Revenue backfills on dims for rows from 2025 onward.
- **GTME calls reconciliation:** 90% captured, 10% gap closure in progress
- **Renewal infrastructure:** Canonical queries live at 98% match; churn model v2 now delivered

______________________________________________________________________

## What's Flat / Concerning 🟡

- **⚠️ AI Assistant decline accelerating:** Paid Core actives 11,510 (previously 12,807 → now 11,510; -10.1% WoW). Third consecutive weekly decline — March recovery is fully erased.
- **⚠️ AI Assistant W4 retention in freefall:** 10.9% (previously 12.7% → now 10.9%; -1.8pp WoW). Now 2.5pp below Q1 13.4% baseline and worsening every week.
- **⚠️ No positive AI retention experiment results:** Cerberus flat (null), AI Sequence Builder v3 rolled back (regression). Zero experiments showing positive AI retention signal this quarter.
- **⚠️ Seat utilization risk escalating:** 50K+ ARR cohort at 24.0% low-utilization (previously 21.5%), second consecutive weekly jump. These teams are in renewal territory. Total GTME low-util ARR at 16.3% — highest Q2 reading.
- **AI Power Up weekly credits declining:** 9.1M (previously 10.1M; -9.9% WoW). Expected after active opt-in rollout but extends 3-week downtrend.
- **⚠️ AI Sequence Builder v3 rolled back:** First hard AI experiment rollback this quarter. Stat-sig decline in sequences enabled at 20% ramp. Regression, not null.
- **Waterfall spike = churn extraction:** 6/10 top spenders at-risk/churning; organic base -15%
- **Credit ceiling churn pattern:** Support tickets are last upsell signal and not wired to pipeline
- **GTME churn response gap:** 27% of model-flagged churners saw no CSM activity increase — response speed is the bottleneck, not signal coverage
- **Waterfall intervention throughput near-zero:** 1/35 waterfall_enrichment_credits_drop cases completed. Auto-resolve path audit needed.
- **Extension WAU logging gap (Jun 3):** Amplitude extension WAU underreporting due to broken logging — not a real usage drop. Eng investigating.

______________________________________________________________________

## Immediate Priorities (Q2, as of June 4)

1. **AI Assistant actives + retention in freefall:** Actives 11,510 (-10.1% WoW, third consecutive decline), W4 retention 10.9% (-1.8pp WoW). No positive experiment results (Cerberus null, Seq Builder regression). Root cause investigation is urgent — is this product regression, seasonal, opt-in rollout effect, or user quality decay?
1. **Seat utilization risk — 50K+ cohort:** 24.0% low-utilization in renewal-territory cohort, climbing for 2 consecutive weeks. Rep intervention needed before renewal window closes.
1. **Cerberus post-mortem and next steps:** Experiment concluded flat. Pubudu writing review. Key question: what's the next retention lever to test?
1. **GTME churn response gap:** 27% of flagged churners see no CSM activity increase. Response speed > signal coverage. Operationalize the watch list.
1. **Waterfall intervention audit:** Near-zero rep-driven closure on waterfall_enrichment_credits_drop (1/35). Decide: auto-resolve path or kill the signal.
1. **CC v3 failure rate fragility:** Recovered to ~17.8% but spiked to 26.83% record on May 24. NO_DATA_FOUND root cause still active — need structural fix, not trend monitoring.
1. **Intervention pipeline throughput:** 489 cases, 18% close rate. `bad_domain_health` backlog (188 open, avg age 28.9 days) is the primary lever.
1. **Jarvis pulse backfill:** 3 tasks resumed Jun 4 after 35-day suspension. Verify data is flowing within 2–3 days. Do not cite Jarvis usage metrics until confirmed current.
1. **Support tickets → signal pipeline:** homebuildvalet pattern is a known gap; Shyam evaluating
1. **Taxonomy CI/CD:** Unblock DAPI secrets access in pipeline (AI Infra discussion ongoing)

______________________________________________________________________

## Escalation Thresholds

| Signal | Threshold | Action |
|--------|-----------|--------|
| **Activation rate drops below 10%** | \<10% | Emergency FUX review; consider UX A/B test redesign |
| **Dialer M3 NRR drops below 85%** | \<85% | Product review; may pause scaling |
| **Cohort NRR misses Q1 by >4pp** | \<126% for new cohorts | Escalate to leadership; replan expansion targets |
| **Expansion ARR drops below $100M** | \<$100M | Trigger product review + sales motion audit |

______________________________________________________________________

## How Jarvis Uses This

When an exec asks "How are we doing?" Jarvis should reference this file to provide context:

**Example response:**

> "We're tracking 124% VSB NRR (target 130%). Behind plan by 6 points. The issue is _not_ churn (retention is solid) but _expansion ARR is 8% below plan_. Activation rate is our canary — stuck at 11% (target 17%). We're launching FUX redesign in mid-April that should move this by 2-3 points. Cohort quality is a structural risk (new cohorts 12% lighter MRR than FY26). Once Bridie's segment lookup is live, we can see if this is a mix issue or a retention issue per segment."

______________________________________________________________________

## Last Updated

- **2026-03-30:** Initial write. Activation flat (11%), Dialer at $300k (early), DCS piloting, NRR below plan, cohort quality risk flagged.
- **2026-03-31:** Weekly refresh. AI Assistant retention declining (W4 10.5%, was 13.4% baseline; actives 9,110 -4.3% WoW). Dialer + Inbound churn spike flagged (Anvitha). Champion Onboarding experiment launched 3/26. Free plan mobile restrict generating $60K ARR. CRM at ATH (6,237). Gap 3 (LU_TEAM_SEGMENT) resolved. New Habit RA Amplitude events launched. Deliverability enforcement at 50%. AI Power Up credits recovered to 11.2M.
- **2026-05-18:** Weekly refresh. AI Assistant actives recovered to 13,646 (+50% from March low). CC v3 at 190K teams (43.96% Paid Core); CC Agent 100% rollout complete; failure rate spiked to 26.9% (NOT trending down — watch). MCP: GTME +142% MoM, 4.4M platform credits; credits r=0.04 with upgrade ARR. Churn pattern: credit-ceiling → silent exit (homebuildvalet case study). Waterfall spike = churn extraction (6/10 top spenders at-risk). Renewal infra live. Q2 OKRs: first check-in opened May 15. Cerberus flat/trending positive. AI credit definition gap open for investor reporting.
- **2026-05-27:** Weekly refresh. AI Assistant recovery arc broken — actives 12,807 (was 13,646), W4 retention collapsed to 12.7% (was 15.2%). AI Sequence Builder v3 rolled back (first hard AI rollback this quarter). Churn model v2 watch list delivered; 27% GTME response gap is the lever. CC v3 adoption accelerating (213.6K teams, 47.81% Paid Core) but failure rate still ~24%. Cerberus flat at 3-week read, decision window June 4. AI credit attribution gap partially closed (35–56% unattributed root-caused). MCP fct pipeline live. Intervention pipeline: 489 cases, 16.6% close rate.
- **2026-05-29:** Staleness audit. Marked Dialer/Inbound/Activation/DCS/Deliverability sections as stale (no data since March/April). Archived Credit Soft-Cap experiment. Pruned shipped milestones from Data Quality section (Jarvis eval bootstrap, Paid WAT inbound, Data Duels). Flagged overdue ETAs (DIM_ACTIVATION past mid-April, GTM Engineer cohort Q2 deadline imminent). Marked Growth Initiatives (Free mobile restrict, Upgrade Modal, One Seat analysis) with stale dates.
- **2026-06-04:** Weekly refresh. AI Assistant decline accelerating — actives 11,510 (was 12,807; -10.1% WoW), W4 retention 10.9% (was 12.7%). Cerberus experiment concluded flat (null result). CC v3 Paid Core crossed 50% (50.49%). AI credit attribution fix shipped (~100% parity). Seat utilization risk escalating (50K+ cohort at 24%). All 12 measurement gaps closed. PLAYGROUND → JARVIS migration complete. Intervention close rate 18%; waterfall throughput near-zero. Jarvis pulse tasks resumed after 35-day suspension — usage metrics unreliable until backfill completes. Three new retention experiments in pipeline (Powered by Apollo, AI Voice Assistant, Finder columns).
