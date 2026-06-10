# Measurement Gap Tracker

**Purpose:** Standing tracker for executive measurement gaps. Reviewed weekly in analytics team syncs.
**Owner:** Bridie Meredith (tracker maintenance); individual gap owners listed below.
**Created:** 2026-03-24
**Sources:** `domain/executive_measurement_requirements.md`, `domain/aop_execution_alignment_20260324.md`

______________________________________________________________________

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

______________________________________________________________________

## Gap Tracker

| # | Gap | Blocks | Who Could Build | Existing Data | Complexity | Status | Notes |
|---|-----|--------|-----------------|---------------|------------|--------|-------|
| 1 | **M3 Cohort NRR** | Analytics (NRR Intelligence Engine OKR: 82% to 90%), Leadership (board reporting) | Rahul (Analytics), Andrew | `FCT_DAILY_REVENUE` has TEAM_CREATED_DATE + ARR + DATE_PERIOD. `FCT_MONTHLY_REVENUE` has IS_FIRST_DATE_PERIOD. Cohort assignment possible from existing data. | M | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.LU_M3_COHORT_NRR` live.** 472 rows, 125 cohort months. VSB 71% NRR, MM 99.6%, Ent 92.7%. Segment is current-state (no time-travel). Catalog: `data-catalog/context/LU_M3_COHORT_NRR.md`. |
| 2 | **F14D Habit RA Activation Rate** | Growth & Acquisition (FTP 4.0% to 4.5%), Onboarding (CBR #8: 12.2% to 17%) | **Jeffrey** (metric owner), **Tara** (DIM_ACTIVATION build), Andrew Green (covering) | `DIM_ACTIVE_TEAMS_DAILY` has `GENPIPE_FEATURE_RECORD_ACTIONED_USER_COUNTS_L1` but that is L1 (yesterday), not cumulative F14D. Raw events in Amplitude (`FCT_AMPLITUDE_EVENTS`). | M | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.LU_TEAM_ACTIVATION_F14D` live.** 15.9M teams, 22.6% overall activation rate. Uses `record_actioned` from AGG_USER_ACTIVATION_EVENTS_DAILY — broader than canonical 14 RA types (~24% vs official ~12%). Directional V1; DIM_ACTIVATION from Jeffrey/Tara will provide exact RA decomposition. Golden pop filters included. Catalog: `data-catalog/context/LU_TEAM_ACTIVATION_F14D.md`. |
| 3 | **FTP Cohort Definitions** | Growth & Acquisition (Dan Cronyn's top ask — W2 FTP 4.0% to 4.5%) | **Jeffrey**, Anvitha, Andrew Green | `DIM_ACTIVE_TEAMS_DAILY` has `FIRST_PAID_DATE`. `FCT_DAILY_REVENUE` has `TEAM_CREATED_DATE`. Week-2 cohort measurement possible from existing data. | S | PARTIAL | **2026-06-04: `JARVIS.LU_FTP_COHORT_W2` live.** 1,144 rows, 88 cohort weeks (2024-09-30 → 2026-06-01). Materialized from `sql/ftp_cohort_w2.sql`. Includes maturity guard. Catalog: `data-catalog/context/LU_FTP_COHORT_W2.md`. |
| 4 | **PQL/PQA Scoring** | Growth & Acquisition (pipeline generation — PQL/PQA dashboards) | Kirk (DS), Shyam | Signal pipeline (`WEEKLY_TEAM_SIGNALS`) has churn/usage signals. `DIM_ACTIVE_TEAMS_DAILY` has feature adoption flags. No scoring model exists. | L | PARTIAL | **2026-06-04: `PLAYGROUND.V_PQA_TEAMS` live.** Heuristic: 3+ MAU (IS_ACTIVE_L28 users) = PQA. 15K PQA teams, 1.83% rate among active teams. This is the interim version — Universal Scoring Model (DS) will refine. Catalog: `data-catalog/context/V_PQA_TEAMS.md`. |
| 5 | **Multi-Product Attach Rate** | R&D (COKR3: avg use cases per Paid WAT 1.18 to 1.33) | Pubudu, **Jeffrey** (successor to Adhiraj) | `DIM_ACTIVE_TEAMS_DAILY` has `USE_CASE_*` flags + `HAS_*_TEAM_USAGE` columns. `TEAM_DAILY_SOLUTION_USAGE` has richer multi-product data. Both are DS-quality. | M | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.V_MULTI_PRODUCT_ATTACH` live.** 53.8K paid teams, 44.9% overall attach rate (2+ products). 10 product areas tracked via L1 flags. By segment: MM 60%, Ent 54%, SMB 53%, VSB 39%. Column gotcha: DIM_ACTIVE_TEAMS_DAILY uses ACTIVITY_DATE not DS. Catalog: `data-catalog/context/V_MULTI_PRODUCT_ATTACH.md`. |
| 6 | **Churn Reason Taxonomy** | Leadership (exec asks "why are teams churning?"), GTME (Eric Quanstrom) | Marie, Tighe, Martin | `CANCELLATION_SURVEYS` in RAW_MONGO_DB (not promoted). `FCT_ZENDESK_CHURN_TICKETS` (101K rows) has unstructured signal. | S | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.LU_CHURN_REASON_TAXONOMY` live.** 229K rows, 177K teams. 7 categories mapped from FCT_CANCELLATION_SURVEY_RESULTS. Low Engagement 36.7% ($93M), Other/Unknown 21.4% ($78M), Pricing 15.2% ($36M). 90.2% revenue match rate. SQL: `sql/lu_churn_reason_taxonomy.sql`. Catalog: `data-catalog/context/LU_CHURN_REASON_TAXONOMY.md`. |
| 7 | **Inbound Revenue Attribution** | Growth & Acquisition ($4M/$10M inbound target), Marketing Analytics | Andrew, Anvitha | `DIM_MONGO_TEAMS_RT_VW` has `PRODUCT_INFOS` (can identify inbound add-on). `INT_TEAM_PRODUCT_INFO_CLEANED` has plan details. No inbound-specific revenue flag on `FCT_DAILY_REVENUE`. | M | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.LU_INBOUND_TEAMS` live.** 1,392 teams with inbound add-on (PRODUCT_ID='inbound'). $12.9M total team ARR. Note: ARR is team-level total, not product-level — FCT_DAILY_REVENUE doesn't break out add-on ARR. Catalog: `data-catalog/context/LU_INBOUND_TEAMS.md`. |
| 8 | **GTME Intervention-to-ARR Attribution** | GTME (Eric Quanstrom — prove Plays work: WAU, credits, GRR, NRR), Q2 dashboard deadline | **Cat Zhou (new, 2026-04-14)**, Will, Shyam, Kaitlyn | `GTME_CALLS_AI_ANALYSIS` (2,362 rows). `WEEKLY_TEAM_SIGNALS_FROM_GTME_CALLS`. `WEEKLY_TEAM_SIGNALS` has signal_source='gtme_calls'. No intervention-to-revenue join exists. | L | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.LU_INTERVENTION_ARR_ATTRIBUTION` live.** 536 interventions, 369 teams. Uses 3-month pre/post ARR windows from FCT_MONTHLY_REVENUE. Completed interventions show +$1,189 avg delta. OBSERVATIONAL ONLY — Cat Zhou's DiD is the causal version. Catalog: `data-catalog/context/LU_INTERVENTION_ARR_ATTRIBUTION.md`. |
| 9 | **Partner-Sourced ARR Tracking** | Partnerships (Jennifer Rhima — $7.2M FY27, growing to $30M FY28) | Martin | Martin's 13 PartnerStack queries are the ONLY analytics touch. No dedicated partner revenue table. No partner attribution on `FCT_DAILY_REVENUE`. | L | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.LU_PARTNER_SOURCED_TEAMS` live.** 17.3K teams, $21.8M ARR. SFDC-sourced (IS_PARTNER_REFERRAL + opp lead source). Amplitude OAuth scan timed out — placeholder columns exist. PartnerStack referral pipeline still not in warehouse. Catalog: `data-catalog/context/LU_PARTNER_SOURCED_TEAMS.md`. |
| 10 | **AI Deflection Resolution Rate** | Support (Kenny Keesee — 80% AI deflection target) | Marie, Tighe | `FCT_TEAM_SUPPORT_DAILY` has `AI_AGENT_PARTICIPATED`, `AI_ONLY_PARTICIPATED`, `AI_RESOLUTION_STATE`. `DIM_SUPPORT_CONVERSATIONS` has conversation-level detail. 24.5% team coverage (Intercom bridge reality). | S | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.V_AI_DEFLECTION_RATE` live.** 2,441 rows (day × paid/free), 2022-07 → 2026-06. Avg 34.7% deflection rate; recent June data 48-57%. Paid/free split via ACCOUNT_ARR > 0. 24.5% Intercom coverage caveat. SQL: `sql/v_ai_deflection_rate.sql`. Catalog: `data-catalog/context/V_AI_DEFLECTION_RATE.md`. |
| 11 | **Segment on Team-Level Tables** | ALL departments (every executive metric needs segment slicing) | Bridie, Rahul | `DIM_SALESFORCE_ACCOUNTS.ACCOUNT_SEGMENT` exists. Join path: `DIM_MONGO_TEAMS.SFDC_ACCOUNT_ID -> DIM_SALESFORCE_ACCOUNTS.ID`. `LU_TEAM_ATTRIBUTES` (PLAYGROUND) already denormalizes segment. | S | PARTIAL | **2026-06-04: `JARVIS.LU_TEAM_SEGMENT` live.** 14.3M rows, 4 segments (VSB 91%, SMB 5.3%, Ent 1.8%, MM 1.8%). Replaces raw SFDC join for 99% of segment queries. Core revenue tables still require join — denormalization is future work. Catalog: `data-catalog/context/LU_TEAM_SEGMENT.md`. |
| 12 | **CSAT / FCR / AHT from Intercom** | Support (Kenny Keesee — CSAT 90% target, save motion 90% coverage) | Marie, Tighe | `INT_INTERCOM_CONVERSATIONS` has CSAT, AI resolution state, escalation flags. AHT available via Intercom API script. See `departments/support/ai_ops_metrics.md`. | M | PARTIAL | **2026-06-04: `ANALYTICS_DB.JARVIS.V_SUPPORT_CSAT` live.** 99 rows (monthly × paid/free), 2022-04 → 2026-06. Paid CSAT 77-93% recent trend. DO NOT use DURATION_HANDLE_TIME_MINUTES for AHT (it's conversation lifetime). IS_CONVERSATION_FIRST_CONTACT_RESOLUTION broken in FY26. Catalog: `data-catalog/context/V_SUPPORT_CSAT.md`. |

______________________________________________________________________

## Promotion Priority (PARTIAL → DONE)

All 12 gaps have minimum-viable coverage as of 2026-06-04. Priority order for promoting to DONE (trusted, ANALYTICS schema):

1. **Gap 11 (Segment)** — move JARVIS.LU_TEAM_SEGMENT to ANALYTICS schema via dbt model or DBTCLOUD_ROLE grant
1. **Gap 1 (M3 Cohort NRR)** — validate against Rahul's definition, promote to ANALYTICS
1. **Gap 2 (F14D Activation)** — reconcile with Jeffrey/Tara's DIM_ACTIVATION when it ships; current V1 is broader than canonical
1. **Gap 6 (Churn Taxonomy)** — get product/VoC sign-off on 7-category mapping
1. **Gap 5 (Multi-Product Attach)** — rebuild from trusted Amplitude/Mongo sources (not DS L1 flags)
1. **Gap 3 (FTP Cohorts)** — already validated against exemplar; just needs schema promotion
1. **Gap 10 (AI Deflection)** — stable; 24.5% coverage is structural, not fixable
1. **Gap 12 (CSAT)** — AHT needs Intercom API script integration; FCR is structurally broken
1. **Gap 7 (Inbound)** — needs product-level ARR decomposition on FCT_DAILY_REVENUE
1. **Gap 8 (GTME Intervention)** — observational table is complete; causal version is Cat's DiD
1. **Gap 4 (PQL/PQA)** — heuristic; awaiting Universal Scoring Model from DS
1. **Gap 9 (Partner ARR)** — needs PartnerStack pipeline + Amplitude OAuth scan

______________________________________________________________________

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-24 | Created tracker from AOP alignment analysis + executive measurement requirements | Bridie (via Jarvis) |
| 2026-04-13 | Gap 12: BLOCKED → PARTIAL. CSAT, AI resolution rate, escalation rate, AHT (chat) now validated. AHT video approximate. FCR quarterly benchmarks documented. | Marie (via Jarvis) |
| 2026-04-20 | Gap 1 (M3 Cohort NRR): PARTIAL → IN PROGRESS. Rahul-validated definition reconciled in `sql/lu_saved_metrics.sql` (commit a583ffe, Bridie, 2026-04-17). Dedicated M3 cohort table still pending. | Bridie (via Jarvis) |
| 2026-04-20 | Gap 8 (GTME Intervention-to-ARR): NOT STARTED → IN PROGRESS. Cat Zhou (Staff DS, joined GTME zone 2026-04-14) shipped DiD causal playbook + CBR weekly insights + seat utilization + account assignment + interventions status + managed teams definition + DiD cohort SQL. Attribution TABLE not yet built; methodology in place. | Jarvis (weekly alignment scan) |
| 2026-06-04 | **All 12 gaps → PARTIAL.** Bulk gap closure: built 8 tables + 4 views across PLAYGROUND/JARVIS schemas. 12 catalog entries created. Tables: LU_M3_COHORT_NRR, LU_TEAM_ACTIVATION_F14D, LU_FTP_COHORT_W2, LU_CHURN_REASON_TAXONOMY, LU_INBOUND_TEAMS, LU_INTERVENTION_ARR_ATTRIBUTION, LU_PARTNER_SOURCED_TEAMS, LU_TEAM_SEGMENT. Views: V_PQA_TEAMS, V_MULTI_PRODUCT_ATTACH, V_AI_DEFLECTION_RATE, V_SUPPORT_CSAT. All in DEVELOPER_ROLE-accessible schemas; promotion to ANALYTICS requires DBTCLOUD_ROLE. | Bridie (via Jarvis) |
