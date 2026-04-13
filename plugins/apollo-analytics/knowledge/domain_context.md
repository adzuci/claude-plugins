<!-- SECTION: curated -->
# Domain Context
*Auto-generated 2026-04-10 by scripts/build_domain_context.py*
*Source: domain/index.md — 128 indexed files*

---

## Critical Context

Always-on references — loaded regardless of question type.

**contribution_guidelines** — Rules and heuristics for anyone contributing to this repo: protected files, sanity checks (no personal names in shared paths, no duplicate dirs, register files on creation), where content belongs, how to sync to Jarvis, and commit conventions.

**jarvis_characters** — Character backstory and protocol reference: the Jarvis family, Shyam, Papa Curl, error logging, metric-not-found messages, and the Pride & Dignity protocol.

**revenue_org_structure** — `FCT_MONTHLY_REVENUE` columns `ARR_SS` / `ARR_REP` / `ARR_SA` are the motion splits; Rep-driven segment = `ACCOUNT_SALES_DEPARTMENT_TIER` (Tier1/2 → MM, Tier3/4 → SMB), not `ACCOUNT_SEGMENT`; VSB deflection project (April 2026 cutover) is the active retention lever for VSB churn.

**hvo_activation_findings** — Dialer has the highest lift (+142%) when covered on call, but only 33% of calls cover it — biggest lever; Covering Sequence on call drives 2–2.4x 30-day activation vs not covered, across all segments; HVO Activated teams: SMB avg NRR 132.8% vs 91.1% for HVO No Activation.

**signal_sources** — Consolidation table: `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS` — one row per (team, week, signal_source, signal_type); ~800K rows total; 8w_churn_model dominates at 745K rows; `SIGNAL_METADATA` is a VARIANT array — use `LATERAL FLATTEN` directly, NOT `TRY_PARSE_JSON()`.

**mcp_analytics** — MCP user SoT: `DIM_USERS.FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL` (Shyam added 2026-03-23); FCT_MONGO_HTTP_REQUESTS_V3_RT_VW is in ANALYTICS_DATAPLATFORM (not ANALYTICS) — filter `USER_AGENT = 'Apollo-MCP/1.0'`; Feb–Mar 2026 cohort: 1,816 users, 45% Day-0, 4–28× FTP lift vs peers, net-new user type (not cannibalization).

## Active State

Current business snapshot — verify against Snowflake before quoting.

- VSB/SMB NRR +10pp is the #1 exec OKR; drives $115.7M expansion ARR target
- F14D Habit RA Rate target: 17% (baseline ~12%); Golden Pop only (SMB+, AMER/EMEA, no freemail)
- AI Assistant WAU target: 10K paid core with 25% W4 retention
- 12 gaps tracked; 4 are S-complexity quick wins (segment on team tables, churn taxonomy, FTP cohorts, AI deflection rate)
- Partnerships ($7.2M target) has zero dedicated analytics — CRITICAL gap
- GTME dashboard (Q2 deadline) has zero build progress — highest individual risk
- VSB/SMB NRR at risk: expansion ARR tracking 8-10% below plan ($108M vs $115.7M)
- Champion Onboarding experiment: replaces 20+ screen wizard with AI-pre-filled prospecting page; key watch metrics = record action rate and day-7 activation
- Cohort quality risk: new cohorts trending $50-100 MRR vs $200-300 historical mean

## Topic Router

Read the file — don't guess from memory.

### Revenue & NRR
- `inbound_team_identification` — Inbound Router is a per-message/per-routed-lead add-on (pricing TBD); target buyer is SDR/BDR/sal... *(Mar 30)*
- `inbound_addon_churn` — Uses `dim_mongo_teams_rt_vw.product_infos` flattened for `%inbound%` plans *(Mar 27)*
- `inbound_addon_purchases` — Adds `account_segment` and `tier` from `dim_salesforce_accounts` *(Mar 27)*
- `dialer_addon_churn` — Uses `dim_mongo_teams_rt_vw.product_infos` flattened for `%dialer%` plans *(Mar 27)*
- `dialer_addon_purchases` — Adds `account_segment` and `tier` from `dim_salesforce_accounts` *(Mar 27)*

### Product & Credits
- `credit_types` — **Waterfall Enrichment** uses waterfall trial credits first, then falls back to unified (≈1 credi... *(Mar 22)*

### Strategy & Targets
- `activation_methodology` — Formula: COUNT(teams ≥4 RAs in F14D) / COUNT(teams activated in window) — Golden Pop only *(Mar 30)*
- `ai_sheets_user_definition` — Status: PENDING — product team (Adhiraj) needs to confirm definition before any queries can be built *(Mar 30)*
- `churn_taxonomy_draft` — ~36% of churned teams cite low engagement — largest single category *(Mar 30)*
- `product_portfolio_taxonomy` — H1 = optimize (not maximize): maintain high NRR, improve COGS, drive multi-product attach *(Mar 30)*
- `theory_of_change` — Teams hitting 4+ Record Actions in F14D have 3× higher M3 NRR than those that don't *(Mar 30)*
- `aop_execution_alignment_20260324` — Growth & Acquisition rated HIGH RISK — FTP cohorts, PQL/PQA, F0-14 activation all missing from Sn... *(Mar 24)*
- `fy27_aop_rnd` — COKR3 "70% of paid on >1 automation" has no single Snowflake source today — Analytics gap *(Mar 22)*
- `fy27_aop_gtme_partnerships_support` — GTME credit tracking is unreliable — blocks Play measurement (known blocker) *(Mar 22)*
- *+10 more files*

### Org & People
- `leader_suit` — Both suits are **opt-in only** — never applied by default *(Mar 25)*
- `department_profiles` — Maps each department to its analytics partner (or flags the gap where none exists) *(Mar 24)*
- `squad_profiles` — Identifies squads with no dedicated analytics support (e.g. MM Sales for COKR1) *(Mar 24)*
- `executive_profiles` — Matt Curl (CEO) has 14 direct reports; Leo reports directly to CEO *(Mar 24)*
- `pokemon_compendium` — Covers executives, analytics leadership, analytics engineering, data science, data engineering, a... *(Mar 23)*
- `dept_assessment_2026-03-11` — State of the Analytics department as of March 2026. Covers what's working, what's not, and what c... *(Mar 11)*

### Reports & Analysis
- `dim_teams_daily_v2_gap_analysis` — V2 has 30 of 207 columns — covers core IDs, active user counts (L1/L7/L28), 11 feature user count... *(Mar 24)*
- `project_dim_teams_daily_rebuild` — Current DIM_TEAMS_DAILY: 8.7B rows, 207 columns, dbt-owned, fragile *(Mar 20)*
- `copilot_roi` — Built in 15 days from first commit *(Mar 20)*
- `ask_henry_plugin_test_report` — 30/60 questions fully answerable today *(Mar 19)*
- `ask_henry_query_guide` — **#1 bug:** `FCT_DAILY_REVENUE` contains parent-account rollup rows that double total ARR if not ... *(Mar 19)*
- `analytics_report_2026_03_19` — Total ARR $196.5M, aggregate NRR 96.3% (Mar), M3 NRR 62-71% vs 82% OKR *(Mar 19)*

### Infrastructure & Ops
- `html_report_standard` — CSS variables: --bg: #0f1117, --surface: #1a1d27, --accent: #6c63ff, --teal: #00d4aa *(Apr 10)*
- `activity_tagging` — Pulse command: `python3 scripts/snowflake_query.py --pulse <action> --detail "<context>"` *(Apr 10)*
- `hex_notebooks_context` — Extracted 2026-03-20 via Threads Agent from Leo's Hex workspace *(Apr 10)*
- `JANITOR_FLAGS` — Flagged dirs: `feedback/`, `team/`, `standups/`, `docs/`, `skills/` -- mostly obsolete after rece... *(Apr 6)*
- `PLAYGROUND_MIGRATION_MANIFEST` — Coordination with DPE (Rahul Gautam) and Infra (Deepak Kumar) required *(Apr 6)*
- `REPORT_TEMPLATE_REGISTRY` — If a template is not in the registry, Jarvis offers to build from raw queries *(Apr 6)*
- `SKILL_MANIFEST` — Plugin skills live in `plugin/claude-plugins-export/skills/` *(Apr 6)*
- `org_pulse` — Generated via `/org-pulse-scan` skill *(Apr 6)*
- *+46 more files*

### Meetings
- `analytics_insight_review_20260325` — Jarvis alpha launch: Friday deploy to all Claude users via IT cloud enterprise *(Mar 25)*
- `daily_seal_team_standup_20260325` — Leo to demo Jarvis at insight review: product debrief, MCP onboarding analysis, HBO effectiveness *(Mar 25)*
- `battle_skill_release_notes_20260324` — Ghost typing = low signal source count → stat penalties; teams >50% Ghost = Ghost fusion *(Mar 24)*
- `gdrive_digest_20260324` — Three key docs: Data Leads Weekly agenda (Mar 17), CBR FY27Q1 (CC v3 at 29.48% Paid Core AI WAT, ... *(Mar 24)*
- `jira_digest_20260324` — 80+ legacy tables dropped (ABSM, Vitally, product taxonomy, NRR) — avoid referencing them *(Mar 24)*
- *+11 more files*

### Recent Updates
- `zone_assignments` — 17 analysts across DS, AE, GTME/Sales Analytics, and Data Platform Engineering *(Apr 7)*
- `offboarding_protocol` — 7-step checklist: triage → ownership decisions → knowledge extraction → repo updates → archive → ... *(Apr 6)*
- `rnd_okr_structure` — 5 objectives: Meet the Moment, Improve NRR (H1), Upmarket Readiness (H1), New Product Revenue (H2... *(Apr 2)*
- `fiscal_calendar` — Apollo's fiscal year and quarter boundaries. FY27 = Feb 2026–Jan 2027. Feb-start fiscal quarters ... *(Apr 2)*
- `mcp_tool_guidelines` — Token-efficient usage guidelines for MCP tools (Glean, Notion, Gmail, Snowflake). References from... *(Mar 27)*
- `deliverability` — Spam blocks are included in overall bounce rate — `delivery_rate + overall_bounce_rate = 100%` *(Mar 27)*
- `new_trial_influenced_ss_arr` — 14-day attribution window; most recent trial per team per purchase day *(Mar 27)*

## Recent Findings

| Date | Source | Key Finding |
|------|--------|-------------|
| 2026-04-06 | offboarding protocol | 7-step checklist: triage → ownership decisions → knowledge extraction → repo updates → archive → comms → Jarvis memory |
| 2026-04-02 | authoring guide | Rule 1–6: domain files — Read-if precision, mutual exclusivity, primary ownership, Key facts that distinguish, stalen... |
| 2026-04-02 | jarvis schema drift | 3 tables correctly documented as PLAYGROUND |
| 2026-03-31 | business state | VSB/SMB NRR at risk: expansion ARR tracking 8-10% below plan ($108M vs $115.7M) |
| 2026-03-30 | inbound team identification | Inbound Router is a per-message/per-routed-lead add-on (pricing TBD); target buyer is SDR/BDR/sales ops |
| 2026-03-30 | annual targets | VSB/SMB NRR +10pp is the #1 exec OKR; drives $115.7M expansion ARR target |
<!-- /SECTION: curated -->

<!-- SECTION: weekly-sweep -->
---

## Weekly Sweep — 2026-04-09
*Auto-replaced each run. Do not edit manually.*

| Date | Source | Key Finding or Decision |
|------|--------|------------------------|
| 2026-04-03 |  okr alignment | > Scanned 2026-04-03, 885 employees, 219 with activity, lookback: 14 days |
| 2026-04-03 | 2026 04 03 | **Period:** 2026-03-31 → 2026-04-03 |
| 2026-04-06 | leo memo 2026 04 06 | **From:** Jarvis (Analytics Copilot) |
| 2026-04-06 | 2026 04 06 repo changelog | > Mar 30 – Apr 6, 2026 | 88 commits | 7 contributors |
| 2026-04-03 | FCT MONGO SALESFORCE OPPORTUNITIES | > Historical Mongo-sourced Salesforce opportunities. **Data through July 2024 only — do not use for current-pe... |
| 2026-04-02 | TEAM AI ASSISTANT STATS | > Team-level lifetime AI Assistant stats for adoption and segmentation. One row per team, all-time aggregation... |
| 2026-04-07 | INTERVENTIONS | > The enriched intervention pipeline table — one row per team × signal week × |
| 2026-04-03 | DIM TEAMS DAILY | > Daily snapshot of team-level metrics. One row per team per day. |
| 2026-04-03 | DIM SALESFORCE OPPORTUNITIES | > Salesforce opportunities dimension. One row per opportunity. 413 columns total. |
| 2026-04-02 | USER AI ASSISTANT STATS | > User-level lifetime AI Assistant stats for segmentation and lifecycle analysis. One row per user, all-time a... |
| 2026-04-06 | LU EMPLOYEE ACTIVITY | > **Weekly activity digest per Apollo employee.** One row per (person, week). Aggregates signals from GitHub, ... |
| 2026-04-03 | FCT MONGO DAILY TEAM AUDIT REPORTS | > Daily team audit snapshots from MongoDB. Credit limits, billing period, and plan details. |
| 2026-04-03 |  multi source okr alignment | **Generated:** 2026-04-03 |
| 2026-04-03 |  company summary | > Scanned 2026-04-03, lookback: 14 days, 284 employees matched |
| 2026-04-02 | FCT AMPLITUDE EVENTS | > Amplitude event tracking — user-level product events. One row per event. |
| 2026-04-02 | FCT LANGSMITH TRACES | > Individual LLM trace metrics from LangSmith — the source of truth for AI Assistant latency, token usage, cos... |
| 2026-04-09 | matthew curl | > Scanned 2026-04-03, lookback: 14 days, dept: Executive (GC1.33010) , Snowflake user: `MATTHEW_MOORE` |
| 2026-04-08 | usage log | > Auto-maintained by Jarvis. Each entry = one meaningful interaction. |
| 2026-04-06 | strategic steering 2026 04 03 | > **⚠ HISTORICAL SNAPSHOT — 2026-04-03.** All numbers, people references, experiment states, and ARR targets r... |
| 2026-04-03 | okr alignment first scan 2026 04 03 | > 2026-04-03 | 14-day window | 893 Darwinbox employees, 284 matched to Snowflake, 219 active |
| 2026-04-06 | jarvis issues | Post issues, questions, or feedback here. Jarvis will pick them up on the next patrol cycle. |
| 2026-04-03 | multi source okr alignment 2026 04 03 | **For Leo** | 2026-04-03 | Bridie + Jarvis |
| 2026-04-08 | free to paid upgrade modal 2026 04 07 | **Experiment:** `free-to-paid-upgrade-modal` |
| 2026-04-02 | claude roi best practices | > Draft ideas for a playbook that guarantees and demonstrates ROI when using Claude (Jarvis or Claude Code) in... |
| 2026-04-07 | bridie action items 2026 04 07 | **What:** The table `CONNECTION_REG_R3` no longer exists (or was moved). Fraud Looker dashboards are actively ... |
| 2026-04-07 | brighid | > Standing log of what Jarvis (Claude Code) worked on with Bridie, why, the value added, and estimated ROI. Up... |
| 2026-04-07 | semantic review 2026 04 07 | **Scope:** Skills + Domain (all checks) |
| 2026-04-03 | okr alignment | description: Map company-wide employee activity to Apollo's OKR hierarchy. Surfaces alignment gaps, under-inve... |
| 2026-04-08 | gtme managed teams | GTME teams are **paid teams with a `gtme_name` assigned** on a **custom plan**. |
| 2026-04-07 | ai platform active definition impact on wau | **Date:** 2026-04-07 | **Author:** Analytics |
| 2026-04-05 | analytics engineer suit | > **Usage:** Activate this suit when the task involves building or modifying data infrastructure — dbt models,... |
| 2026-04-05 | worklog pubudu | - **Default Fields Notion refresh — 2026-04-03 (IN PROGRESS)** |
| 2026-04-02 | claudathon submission | - [ ] Team name: **Seal Team** (Leo Liu + Bridie Meredith) |
| 2026-04-09 | battle log | | Name | ELO | Wins | Losses | Streak | |
<!-- /SECTION: weekly-sweep -->
