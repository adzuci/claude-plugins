# Measurement Gap Tracker

**Purpose:** Standing tracker for executive measurement gaps. Reviewed weekly in analytics team syncs.
**Owner:** Bridie Meredith (tracker maintenance); individual gap owners listed below.
**Created:** 2026-03-24
**Sources:** `domain/executive_measurement_requirements.md`, `domain/aop_execution_alignment_20260324.md`

---

## Gap Status Legend

| Status | Meaning |
|--------|---------|
| NOT STARTED | No work has begun |
| IN PROGRESS | Actively being built |
| BLOCKED | Work started but waiting on external dependency |
| PARTIAL | Some data exists but not in trusted/complete form |
| DONE | Landed in a trusted table and validated |

## Complexity Legend

| Size | Meaning |
|------|---------|
| S | < 1 week. Single table, clear logic, data already exists |
| M | 1-3 weeks. Multiple source joins, business logic decisions needed, or pipeline work |
| L | 3+ weeks. New data pipeline, cross-team alignment, or architectural decision required |

---

## Gap Tracker

| # | Gap | Blocks | Who Could Build | Existing Data | Complexity | Status | Notes |
|---|-----|--------|-----------------|---------------|------------|--------|-------|
| 1 | **M3 Cohort NRR** | Analytics (NRR Intelligence Engine OKR: 82% to 90%), Leadership (board reporting) | Rahul (Analytics), Andrew | `FCT_DAILY_REVENUE` has TEAM_CREATED_DATE + ARR + DATE_PERIOD. `FCT_MONTHLY_REVENUE` has IS_FIRST_DATE_PERIOD. Cohort assignment possible from existing data. | M | PARTIAL | Metric intake file at `metrics/m3_cohort_nrr.md` — awaiting Rahul's business logic input. `FCT_ACCOUNT_QUARTERLY_NRR` exists but implements aggregate quarterly NRR, not M3 cohort methodology. |
| 2 | **F14D Habit RA Activation Rate** | Growth & Acquisition (FTP 4.0% to 4.5%), Onboarding (CBR #8: 12.2% to 17%) | **Jeffrey** (metric owner), **Tara** (DIM_ACTIVATION build), Andrew Green (covering) | `DIM_ACTIVE_TEAMS_DAILY` has `GENPIPE_FEATURE_RECORD_ACTIONED_USER_COUNTS_L1` but that is L1 (yesterday), not cumulative F14D. Raw events in Amplitude (`FCT_AMPLITUDE_EVENTS`). | M | BLOCKED | Adhiraj departed 2026-04-06. Jeffrey owns metric; Tara + Jeffrey building DIM_ACTIVATION table; Andrew Green covering interim. Definition: 4 Record Actions within 14 days of signup. Currently Amplitude/Hex only. |
| 3 | **FTP Cohort Definitions** | Growth & Acquisition (Dan Cronyn's top ask — W2 FTP 4.0% to 4.5%) | **Jeffrey**, Anvitha, Andrew Green | `DIM_ACTIVE_TEAMS_DAILY` has `FIRST_PAID_DATE`. `FCT_DAILY_REVENUE` has `TEAM_CREATED_DATE`. Week-2 cohort measurement possible from existing data. | S | NOT STARTED | No dedicated analyst assigned to FTP cohorts. Growth's highest-priority gap per AOP alignment analysis. |
| 4 | **PQL/PQA Scoring** | Growth & Acquisition (pipeline generation — PQL/PQA dashboards) | Kirk (DS), Shyam | Signal pipeline (`WEEKLY_TEAM_SIGNALS`) has churn/usage signals. `DIM_ACTIVE_TEAMS_DAILY` has feature adoption flags. No scoring model exists. | L | NOT STARTED | Zero evidence of dashboard development. Requires DS team to define scoring model + Engineering to operationalize. |
| 5 | **Multi-Product Attach Rate** | R&D (COKR3: avg use cases per Paid WAT 1.18 to 1.33) | Pubudu, **Jeffrey** (successor to Adhiraj) | `DIM_ACTIVE_TEAMS_DAILY` has `USE_CASE_*` flags + `HAS_*_TEAM_USAGE` columns. `TEAM_DAILY_SOLUTION_USAGE` has richer multi-product data. Both are DS-quality. | M | PARTIAL | DS tables have the taxonomy but are not trusted. Need to rebuild use case flags from trusted Amplitude/Mongo sources. F28D Paid Multi-Product Attach Rate (activation variant) baseline ~31.5-35%. |
| 6 | **Churn Reason Taxonomy** | Leadership (exec asks "why are teams churning?"), GTME (Eric Quanstrom) | Marie, Tighe, Martin | `CANCELLATION_SURVEYS` in RAW_MONGO_DB (not promoted). `FCT_ZENDESK_CHURN_TICKETS` (101K rows) has unstructured signal. | S | NOT STARTED | Quick win: request Mongo mirror promotion for `CANCELLATION_SURVEYS`, map survey responses to a taxonomy, join to churn events in `FCT_DAILY_REVENUE`. |
| 7 | **Inbound Revenue Attribution** | Growth & Acquisition ($4M/$10M inbound target), Marketing Analytics | Andrew, Anvitha | `DIM_MONGO_TEAMS_RT_VW` has `PRODUCT_INFOS` (can identify inbound add-on). `INT_TEAM_PRODUCT_INFO_CLEANED` has plan details. No inbound-specific revenue flag on `FCT_DAILY_REVENUE`. | M | NOT STARTED | Metric intake file at `metrics/inbound_revenue_attribution.md`. Andrew's MARKETING_CONTACTS investigation (35 queries) may be related. Needs flag on revenue tables indicating inbound add-on contribution. |
| 8 | **GTME Intervention-to-ARR Attribution** | GTME (Eric Quanstrom — prove Plays work: WAU, credits, GRR, NRR), Q2 dashboard deadline | Will, Shyam, Kaitlyn | `GTME_CALLS_AI_ANALYSIS` (2,362 rows). `WEEKLY_TEAM_SIGNALS_FROM_GTME_CALLS`. `WEEKLY_TEAM_SIGNALS` has signal_source='gtme_calls'. No intervention-to-revenue join exists. | L | NOT STARTED | GTME metrics dashboard (Q2 deadline) has zero visible build progress. Will is the nominal GTME partner but has been focused on plugin testing and Stripe billing. Highest individual-level risk from AOP alignment. |
| 9 | **Partner-Sourced ARR Tracking** | Partnerships (Jennifer Rhima — $7.2M FY27, growing to $30M FY28) | Martin | Martin's 13 PartnerStack queries are the ONLY analytics touch. No dedicated partner revenue table. No partner attribution on `FCT_DAILY_REVENUE`. | L | NOT STARTED | Partnerships is the most under-measured department at Apollo. CRITICAL risk per AOP alignment. Even basic tracking (partner-sourced teams, ARR, conversion) does not exist. |
| 10 | **AI Deflection Resolution Rate** | Support (Kenny Keesee — 80% AI deflection target) | Marie, Tighe | `FCT_TEAM_SUPPORT_DAILY` has `AI_AGENT_PARTICIPATED`, `AI_ONLY_PARTICIPATED`, `AI_RESOLUTION_STATE`. `DIM_SUPPORT_CONVERSATIONS` has conversation-level detail. 24.5% team coverage (Intercom bridge reality). | S | PARTIAL | Foundation table (`FCT_TEAM_SUPPORT_DAILY`) already captures AI participation flags. Need to define "resolution" criteria and build the rate metric. Intercom coverage gap (24.5%) limits completeness. |
| 11 | **Segment on Team-Level Tables** | ALL departments (every executive metric needs segment slicing) | Bridie, Rahul | `DIM_SALESFORCE_ACCOUNTS.ACCOUNT_SEGMENT` exists. Join path: `DIM_MONGO_TEAMS.SFDC_ACCOUNT_ID -> DIM_SALESFORCE_ACCOUNTS.ID`. `LU_TEAM_ATTRIBUTES` (PLAYGROUND) already denormalizes segment. | S | PARTIAL | `LU_TEAM_ATTRIBUTES` in PLAYGROUND has segment. Core revenue tables (`FCT_DAILY_REVENUE`, `AGG_TEAM_CREDITS`) still require the SFDC join. Options: (a) denormalize onto key tables, (b) build lightweight `DIM_TEAM_SEGMENT` lookup, (c) accept join pattern and document it. |
| 12 | **CSAT / FCR / AHT from Intercom** | Support (Kenny Keesee — CSAT 90% target, save motion 90% coverage) | Marie, Tighe | `DIM_SUPPORT_CONVERSATIONS` has conversation data but topics/subtopics mostly null. CSAT lives in Intercom, not Snowflake. FCR (First Contact Resolution) and AHT (Average Handle Time) not available. | L | BLOCKED | Intercom data pipeline quality is the blocker. Topics/subtopics are mostly null. CSAT scores not synced to Snowflake. Requires Intercom pipeline improvements (Data Engineering dependency). |

---

## Priority Order (Recommended Build Sequence)

Based on executive question frequency, OKR dependency, and data availability:

1. **Gap 11 (Segment on team tables)** — S complexity, unblocks every segmented metric
2. **Gap 1 (M3 Cohort NRR)** — M complexity, #1 retention OKR, data exists
3. **Gap 6 (Churn Reason Taxonomy)** — S complexity, quick win, high exec visibility
4. **Gap 3 (FTP Cohort Definitions)** — S complexity, Growth's top ask
5. **Gap 10 (AI Deflection Rate)** — S complexity, foundation table already exists
6. **Gap 5 (Multi-Product Attach Rate)** — M complexity, R&D COKR3 measurement
7. **Gap 2 (F14D Activation Rate)** — M complexity, awaiting AE input
8. **Gap 7 (Inbound Revenue Attribution)** — M complexity, awaiting definition
9. **Gap 8 (GTME Intervention-to-ARR)** — L complexity, Q2 deadline approaching
10. **Gap 9 (Partner-Sourced ARR)** — L complexity, CRITICAL department gap
11. **Gap 4 (PQL/PQA Scoring)** — L complexity, requires DS model
12. **Gap 12 (CSAT/FCR/AHT)** — L complexity, blocked on Intercom pipeline

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-24 | Created tracker from AOP alignment analysis + executive measurement requirements | Bridie (via Jarvis) |
