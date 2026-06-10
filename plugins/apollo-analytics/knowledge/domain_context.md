<!-- SECTION: curated -->

# Domain Context

*Auto-generated 2026-05-28 by scripts/build_domain_context.py*
*Source: domain/index.md — 240 indexed files*

______________________________________________________________________

## Critical Context

Always-on references — loaded regardless of question type.

**contribution_guidelines** — Rules and heuristics for anyone contributing to this repo: protected files, sanity checks (no personal names in shared paths, no duplicate dirs, register files on creation), where content belongs, how to sync to Jarvis, and commit conventions.

**jarvis_characters** — Character backstory and protocol reference: Henry, Shyam, Papa Curl, error logging (henry_errors.jsonl), metric-not-found messages, and the Pride & Dignity protocol.

**active_personas** — Always-on background voices that run in every session: Jarvis (personality), Pepper (infrastructure immune system + persona traffic controller), Rhodey (experimental rigor / process cop / recap spin detection), Tony (visionary, storyteller, unblocker, startup energy), Hammer (bad analytics detector — fires when a Hammer-class flaw is detected). Pepper has admin oversight — max 2 persona callouts per response. Also defines the Ultron rogue override list and persona interaction rules.

**pepper_v2_spec** — Pepper v2 architecture spec — personal quality assistant with three operating modes (enforce, educate, orchestrate), per-user STM/LTM memory, PostToolUse hook monitoring, iteration protocol with configurable rounds, cold-start protocol for new users, scheduled compaction routine, and suit dispatch via Claude main. 8 iteration rounds with Ultron. Covers: hook architecture, memory schema, artifact classification, knowledge gap detection, cross-pollination, verification metrics, build phases 1-4.

**pepper_rules** — Catalog rules enforce template completeness: grain, full path, owner, trust level, coverage period, no unfilled placeholders; Analysis rules enforce bias evaluation: all four bias types (selection, survivorship, confounding, measurement) are individually checkable; Domain rules catch protected file edits, personal names in shared paths, and missing index registrations.

**pepper_scan_prompt** — Prompt template for the Pepper scan fork (Phase 2). The subagent receives this prompt plus a structured payload from `pepper_scan.py`. Returns JSON with findings, context injections, and recommendations (array — multiple review types can fire on one artifact). Defines severity levels, dedup policy, and recommendation routing.

**pepper_routine_prompt** — Prompt template for the Pepper weekly maintenance routine (CronCreate). The routine runs as a remote Claude session: health check → compaction (STM→LTM promotion) → cross-pollination → health metrics snapshot → GCS backup → commit. Includes safety abort if compaction would drop >60% without promoting any entries.

**hammer** — The Hammer bad analytics archive — a collection of real flawed analyses used for coaching and detection. Named after Justin Hammer (Iron Man 2): analytics that looks polished but doesn't work. Defines 15 flaw classes (avg_ratio, survivorship, selection_bias, cherry_timeframe, double_count, etc.), the entry schema, detection rules, and the Hammer persona voice. Archive lives in `worklog/hammer/`. Seed entries promoted from henry_errors.jsonl.

**finance** — ARR, MRR, NRR definitions and gotchas (parent account filter, mix-shift); Two revenue motions: Self-Serve (`arr_ss`) vs. Rep-Driven (`arr_sales`) — must segment; Stripe billing is non-standard: subscriptions structural only, custom invoices for actual billing.

**finance_onboarding** — Two access systems, two channels: GitHub via `#it-help-desk`, Claude Code via `#tmp-claude-code-approvals`; `non-eng` GitHub team is the documented least-privilege path for non-engineering Leadgenie access; Public Apollo email on GitHub profile is MANDATORY — SSO fails silently otherwise.

**finance_onboarding_facilitator_runbook** — Audience: facilitator (Bridie or designate). Do NOT screen-share this file; Pre-fills the two batch tickets with the Finance team roster; Documents the four common failure modes that trip up live onboarding sessions.

**revenue_org_structure** — `FCT_MONTHLY_REVENUE` columns `ARR_SS` / `ARR_REP` / `ARR_SA` are the motion splits; Rep-driven segment = `ACCOUNT_SALES_DEPARTMENT_TIER` (Tier1/2 → MM, Tier3/4 → SMB), not `ACCOUNT_SEGMENT`; VSB deflection project (April 2026 cutover) is the active retention lever for VSB churn.

**hvo_activation_findings** — Dialer has the highest lift (+142%) when covered on call, but only 33% of calls cover it — biggest lever; Covering Sequence on call drives 2–2.4x 30-day activation vs not covered, across all segments; HVO Activated teams: SMB avg NRR 132.8% vs 91.1% for HVO No Activation.

**signal_sources** — Consolidation table: `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS` — one row per (team, week, signal_source, signal_type); ~800K rows total; 8w_churn_model dominates at 745K rows; `SIGNAL_METADATA` is a VARIANT array — use `LATERAL FLATTEN` directly, NOT `TRY_PARSE_JSON()`.

**mcp_analytics** — MCP user SoT: `DIM_USERS.FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL` (Shyam added 2026-03-23); FCT_MONGO_HTTP_REQUESTS_V3_RT_VW is in ANALYTICS_DATAPLATFORM (not ANALYTICS) — filter `USER_AGENT = 'Apollo-MCP/1.0'`; Feb–Mar 2026 cohort: 1,816 users, 45% Day-0, 4–28× FTP lift vs peers, net-new user type (not cannibalization).

**action_tracker** — Durable ledger of cross-team action items (from reviews, debriefs, insights sessions). Bench delivers + expires; this persists for "what did we say we'd do, and is it done?" weeks/months later. Each row pairs the action with its load-bearing assumption, the source meeting/doc, and the bench ID if delivered via bench.

**biweekly_insights_findings_2026-05-06** — MCP NRR not stat-sig at 2-month window (new + existing customer cohorts); 48% VSB conversion surge depresses uncontrolled aggregate NRR; MCP traffic is headless (no tracking params); Dialer: >$1M ARR, paid WAU flat, activation declining across all segments, **5 connected calls in month 1 = retention inflection**, mid-market causation not yet isolated; Credits: VSB FreeMail month-0 attach 11–14% (~2x other segments); later-month attach climbing since May 2025; auto-consumption (e.g., Waterfall auto-on) drains Basic-tier disproportionately.

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

- `inbound_debrief_template` — HTML template for the Inbound product debrief. Dark-mode layout with 4 Chart.js charts (ARR spark... *(May 22)*
- `ai_native` — Three sub-areas: AI Assistant (conversational agent), Power Ups (AI enrichment), AI Messaging (AI... *(May 20)*
- `rep_execution` — Canonical task data: Mongo `outreach_tasks` collection — not Snowflake. `created_from_cd` separat... *(May 18)*
- `inbound` — "Inbound" almost always means website visitor tracking — form enrichment and router usage are min... *(May 13)*
- `sequences` — "Sequences" almost always means email outreach — phone/LinkedIn/task steps are secondary *(May 13)*
- `prospecting` — Prospecting is a composite product spanning multiple sub-features — always show feature-level bre... *(May 13)*
- `dialer` — Pre-Jan 2026: dialer = pro/custom only, all features included; **no add-on existed** *(Apr 29)*
- `inbound_team_identification` — Inbound Router is a per-message/per-routed-lead add-on (pricing TBD); target buyer is SDR/BDR/sal... *(Mar 30)*
- *+4 more files*

### Product & Credits

- `bridie_credits_explainer` — Refresh spec for `bridie_credits_explainer` — the investigation-format dashboard explaining what'... *(May 14)*
- `credits` — PoC view: `ANALYTICS_DB.JARVIS.V_TEAM_CREDIT_UTILIZATION_DAILY` (90 days, one row per team-day) *(Apr 28)*
- `credit_types` — **Waterfall Enrichment** uses waterfall trial credits first, then falls back to unified (≈1 credi... *(Mar 22)*

### Strategy & Targets

- `rbr_metrics_and_methods` — LTV:CPA cohort conversion matures at week 12; week 4 is reliable proxy (weeks 0-3 directional only) *(May 27)*
- `partnerships` — `oauth_client_id IS NOT NULL` = partner/OAuth traffic; `IS NULL` = direct API key or in-app *(May 4)*
- `partnerships_identification` — HubSpot Breeze partner_id: `69c168f6ec87470015f21f4f` *(May 4)*
- `cbr_weekly_context` — April ARR forecast: $219.6–221.4M (+51% YoY). Downmarket massively over plan (+$14.4M NNARR). Upm... *(Apr 29)*
- `product_portfolio_taxonomy` — H1 = optimize (not maximize): maintain high NRR, improve COGS, drive multi-product attach *(Mar 30)*
- `theory_of_change` — Teams hitting 4+ Record Actions in F14D have 3× higher M3 NRR than those that don't *(Mar 30)*
- `activation_methodology` — Formula: COUNT(teams ≥4 RAs in F14D) / COUNT(teams activated in window) — Golden Pop only *(Mar 30)*
- `ai_sheets_user_definition` — Status: PENDING — product team (Adhiraj) needs to confirm definition before any queries can be built *(Mar 30)*
- *+14 more files*

### Org & People

- `kenny_keesee` — Kenny's domain: CE org (~16K-17K interactions/month, 4 squads, 3 QA frameworks) *(May 27)*
- `cx_signal_engine_next_session` — Shipped: `cx_qa_scorer.py`, cost tracker wired to Snowflake, two-tier tone prompts in pipeline *(May 27)*
- `analyst_suit` — Trigger names: "Anvitha", "Stealth" *(Apr 22)*
- `leader_suit` — Both suits are **opt-in only** — never applied by default *(Mar 25)*
- `executive_profiles` — Matt Curl (CEO) has 14 direct reports; Leo reports directly to CEO *(Mar 24)*
- `department_profiles` — Maps each department to its analytics partner (or flags the gap where none exists) *(Mar 24)*
- `squad_profiles` — Identifies squads with no dedicated analytics support (e.g. MM Sales for COKR1) *(Mar 24)*
- `pokemon_compendium` — Covers executives, analytics leadership, analytics engineering, data science, data engineering, a... *(Mar 23)*
- *+1 more files*

### Reports & Analysis

- `jarvis_baseline_measurement` — ~12 data questions/month in public channels (20/month combined with ask-henry), 23 unique askers *(May 18)*
- `dim_teams_daily_v2_gap_analysis` — V2 has 30 of 207 columns — covers core IDs, active user counts (L1/L7/L28), 11 feature user count... *(Mar 24)*
- `copilot_roi` — Built in 15 days from first commit *(Mar 20)*
- `project_dim_teams_daily_rebuild` — Current DIM_TEAMS_DAILY: 8.7B rows, 207 columns, dbt-owned, fragile *(Mar 20)*
- `ask_henry_plugin_test_report` — 30/60 questions fully answerable today *(Mar 19)*
- `ask_henry_query_guide` — **#1 bug:** `FCT_DAILY_REVENUE` contains parent-account rollup rows that double total ARR if not ... *(Mar 19)*
- `analytics_report_2026_03_19` — Total ARR $196.5M, aggregate NRR 96.3% (Mar), M3 NRR 62-71% vs 82% OKR *(Mar 19)*

### Infrastructure & Ops

- `cx_intelligence_platform` — ~16,000–17,000 human-led interactions/month across voice, chat, email *(May 27)*
- `cx_platform_kenny_context` — 4 squads: Product Advocates, Technical Support, Account Advocates, Customer Advocates (Tania Garcia) *(May 27)*
- `cx_coach_routing` — Maps squads → frameworks: Product Advocates/Technical Support/Account Advocates → non_voice_qa; C... *(May 27)*
- `template_registry` — **Source of truth** for what templates exist and what they need — supersedes REPORT_TEMPLATE_REGI... *(May 14)*
- `m0_credit_attach_signal` — M0 attach: 7,556 teams, 39% M3 logo retention, $1,488 median start ARR (higher = bought more at s... *(May 14)*
- `REPORT_TEMPLATE_REGISTRY` — Human-readable narrative companion to `template_registry.json`. Design rules, "templates needed" ... *(May 13)*
- `domain_compact` — 127 domain files compressed into a single reference (~97K chars) *(May 12)*
- `handoff_template` — Track A vs Track C decision rule: if "who is this blocked on" has one answer → Track A; if it pro... *(May 5)*
- *+73 more files*

### Meetings

- `analytics_insight_review_20260325` — Jarvis alpha launch: Friday deploy to all Claude users via IT cloud enterprise *(Mar 25)*
- `daily_seal_team_standup_20260325` — Leo to demo Jarvis at insight review: product debrief, MCP onboarding analysis, HBO effectiveness *(Mar 25)*
- `battle_skill_release_notes_20260324` — Ghost typing = low signal source count → stat penalties; teams >50% Ghost = Ghost fusion *(Mar 24)*
- `gdrive_digest_20260324` — Three key docs: Data Leads Weekly agenda (Mar 17), CBR FY27Q1 (CC v3 at 29.48% Paid Core AI WAT, ... *(Mar 24)*
- `jira_digest_20260324` — 80+ legacy tables dropped (ABSM, Vitally, product taxonomy, NRR) — avoid referencing them *(Mar 24)*
- *+11 more files*

### Recent Updates

- `cx_signal_engine_handoff_package` — Links to all 6 prompt files, 6 scripts, 5 Snowflake tables, and the steady-state runbook *(May 27)*
- `cx_signal_engine_steady_state` — Three-stage daily flow: BUILD INPUT → FLAG EVAL (Cortex) → FINALIZE FLAGS *(May 27)*
- `identity_eval` — 54 labeled pairs, 4 edge types *(May 27)*
- `cx_haiku_v2.1` — CX Signal Engine Haiku prompt v2.1 — builds on v2 with decision trees for the 5 flags that underp... *(May 27)*
- `cx_haiku_v3` — CX Signal Engine Haiku prompt v3 — latest iteration. Incorporates Round 4 tuning feedback. Full 8... *(May 27)*
- `cx_sonnet_hard5_v1` — CX Signal Engine Sonnet prompt for 5 hard flags — extends `cx_sonnet_hard4_v1.txt` by adding \`pro... *(May 27)*
- `cx_eval_tuning_session_prompt` — Round 4 eval tuning session prompt. Documents Phase 0 results (80 stratified conversations, 3 ite... *(May 27)*
- `jon_ferrari_recon` — Files: `slack.md`, `notion_glean.md`, `gmail_calendar_github.md`, `snowflake_code.md`, \`IDENTITY\_... *(May 27)*
- *+43 more files*

## Recent Findings

| Date | Source | Key Finding |
|------|--------|-------------|
| 2026-05-27 | rbr metrics and methods | LTV:CPA cohort conversion matures at week 12; week 4 is reliable proxy (weeks 0-3 directional only) |
| 2026-05-27 | cx haiku v2.1 | CX Signal Engine Haiku prompt v2.1 — builds on v2 with decision trees for the 5 flags that underperformed in Phase 0 ... |
| 2026-05-27 | lu ea null reduction 2026 05 27 | LU_EMPLOYEE_ACTIVITY NULL reduction analysis supporting KRs B-O1 4.3 (NULL reduction ≥ 50%) and B-O1 4.4 (token cover... |
| 2026-05-26 | extension context | Extension is available to all users (including free); some features are paid-only — always specify which use case |
| 2026-05-21 | dedup service harvest | Service-account / dedup pipeline audit scaffold for the identity-graph project. Documents current per-source anchor s... |
| 2026-05-20 | ai native | Three sub-areas: AI Assistant (conversational agent), Power Ups (AI enrichment), AI Messaging (AI-generated sequence ... |

<!-- /SECTION: curated -->

<!-- SECTION: weekly-sweep -->

______________________________________________________________________

## Weekly Sweep — 2026-06-04

*Auto-replaced each run. Do not edit manually.*

| Date | Source | Key Finding or Decision |
|------|--------|------------------------|
| 2026-06-03 | glossary entries | Business term definitions with SQL predicates where applicable. Maps to `LU_BUSINESS_GLOSSARY` in Snowflake. |
| 2026-05-29 | 2026 05 29 | **Period:** 2026-05-22 → 2026-05-29 |
| 2026-05-28 | reference tables | Lazy-loaded from CLAUDE.md. Read this file when you need a specific lookup — not at startup. |
| 2026-05-29 | shared strategic context | *Team-wide orientation. Loaded for every session, every user. Updated weekly via `/weekly-context-refresh`.* |
| 2026-06-01 | content center debrief template | **Owner:** Sai Sarvepalli | **Updated:** 2026-06-01 | **Status:** Canonical — use for all Content Center debri... |
| 2026-05-29 | resource directory | *What's available in this repo. Loaded for every session, every user.* |
| 2026-05-29 | QA FULL AUDIT 2026 05 29 | **Scope:** All context surfaces except teammate benches. Domain (885 files), data-catalog (221 files), scripts... |
| 2026-05-29 | PRODUCT METRICS DAILY | **Schema:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE` |
| 2026-05-29 | QA AUDIT 2026 05 29 | **Scope:** All 43 standalone intelligence kernels in `domain/intelligence/`. |
| 2026-05-29 | QA AUDIT 2026 05 29 | **Scope:** 15 questions sampled from 60 active test cases, run through Haiku subagents with fresh analytics-co... |
| 2026-06-03 | lu saved metrics snapshot | -- LU_SAVED_METRICS snapshot — 2026-05-29 |
| 2026-05-31 | gtme call effectiveness | **Owner:** Leo Liu | **Updated:** 2026-05-31 |
| 2026-05-29 | FCT MONTHLY REVENUE | > Monthly revenue with change categories (new, churn, upgrade, downgrade). Core retention table. |
| 2026-06-02 | DIM TEAMS | > Data Science team dimension. Enriched team-level attributes for product analytics. |
| 2026-05-29 | DIM USER ACTIVATION | > Data Science dimension: first calendar date each user hit tracked activation steps (PLG / product milestones... |
| 2026-06-03 | lu team segment | **Location:** `ANALYTICS_DB.JARVIS.LU_TEAM_SEGMENT` |
| 2026-05-29 | site integrity plan | audience: build-system |
| 2026-05-29 | cx intelligence platform | **Owner:** Kenny Keesee (Head of Customer Care) |
| 2026-06-03 | employee activity refresh | You are running a scheduled weekly refresh of `ANALYTICS_DB.JARVIS.LU_EMPLOYEE_ACTIVITY`. |
| 2026-06-01 | cx ai audit dashboard | audience: kenny_keesee_team |
| 2026-05-29 | domain audit 2026 05 29 | The `domain/` directory has 887 files across 27 subdirectories (~75K lines). It grew organically with no audie... |
| 2026-06-03 | worklog pubudu | - **Synthetic Twin User-Skill Rebuild + 21-Use-Case Run — 2026-06-01 → WIP** |
| 2026-06-01 | strategic context | - FY27 Growth & Acquisition AOP: signup volume, conversion rates, CAC efficiency |
| 2026-05-29 | repo audit 2026 05 29 | | Total files (excl .git, .venv) | ~3,900 | |
| 2026-05-29 | readout | **Analyst:** Andrew Green · **Date:** 2026-05-28 · **Flag:** `top-nav-credit-widget-followup` · \[Amplitude\](ht... |
| 2026-06-03 | ultron stm | Compact distillation of recent patterns. Three-tier flow: |
| 2026-06-02 | jarvis spine consolidation plan 2026 06 02 | > **Origin:** Bridie's session 2026-06-02. Five workstreams surfaced; this doc holds them with explicit forks ... |
| 2026-06-01 | chrome extension 07 user journeys 20260529 | > **Author:** Valery | **Date:** 2026-05-29 | **Data as of:** 2026-05-27 |
| 2026-05-29 | skill audit 2026 05 29 | Evidence sources (strongest → weakest): |
| 2026-06-03 | ultron distilled | Curated by Ultron from `ultron_recent.jsonl`. Updated when the rolling buffer fills, or when a clear pattern e... |
| 2026-06-02 | signal sizing queries 2026 06 01 | > **Date:** 2026-06-01 |
| 2026-06-01 | chrome extension 08 monetization 20260529 | > **Author:** Valery | **Date:** 2026-05-29 | **Data as of:** 2026-05-27 |
| 2026-05-29 | ops cheat sheet | What writes what, when, and how. Reference for debugging staleness or understanding why a file changed. |
| 2026-05-29 | full audit compilation 2026 05 29 | | # | Audit | Time | Location | Key Result | |
| 2026-05-29 | skill audit 2026 05 29 draft | Status: Draft — initial pass from Bridie's usage log + git history. Needs cross-bench evidence scan. |
| 2026-06-02 | aa test features team level | -- Team-Level Feature Extraction for Python Matching |
| 2026-06-02 | aa user revenue bias decomposition | -- Decompose user revenue bias by ARR bucket and team size bucket |
| 2026-06-01 | chrome extension 04 retained paid users 20260528 | > **Author:** Valery | **Date:** 2026-05-28 | **Data as of:** 2026-05-27 |
| 2026-06-01 | mcp hex canonical queries | Source: \[v0 — MCP Product Operating Metrics & Health\](https://app.hex.tech/apollo/hex/v0-MCP-Product-Operating... |
| 2026-05-29 | okr alignment | description: Map company-wide employee activity to Apollo's OKR hierarchy. Surfaces alignment gaps, under-inve... |
| 2026-06-03 | analytics engineer suit | > **Usage:** Activate this suit when the task involves building or modifying data infrastructure — dbt models,... |
| 2026-06-02 | aa allperiod team retention | -- Synthetic Twin A/A Test — Team-Level Retention (All-Period Sampling) |
| 2026-06-02 | aa allperiod user retention | -- Synthetic Twin A/A Test — User-Level Retention (All-Period Sampling) |
| 2026-06-02 | aa baseline team retention 10k | -- Synthetic Twin A/A Test — Baseline Team-Level Retention |
| 2026-06-02 | aa baseline team retention 1k | -- Synthetic Twin A/A Test — Baseline Team-Level Retention |
| 2026-06-02 | aa baseline user retention 10k | -- Synthetic Twin A/A Test — Baseline User-Level Retention |
| 2026-06-02 | aa baseline user retention 1k | -- Synthetic Twin A/A Test — Baseline User-Level Retention |
| 2026-06-02 | aa bootstrap team pairs | -- Synthetic Twin A/A -- Team-Level Bootstrap Pairs |
| 2026-06-02 | aa bootstrap team pairs 9dim 2m segment | -- Synthetic Twin A/A -- Team-Level Bootstrap Pairs (9-dim with segment replacing tier) |
| 2026-06-02 | aa bootstrap team pairs 9dim segment | -- Synthetic Twin A/A -- Team-Level Bootstrap Pairs (9-dim with segment replacing tier) |
| 2026-06-02 | aa bootstrap user pairs | -- Synthetic Twin A/A -- User-Level Bootstrap Pairs |
| 2026-06-02 | aa bootstrap user pairs 9dim 2m segment | -- Synthetic Twin A/A -- User-Level Bootstrap Pairs (9-dim with segment replacing tier) |
| 2026-06-02 | aa bootstrap user pairs 9dim segment | -- Synthetic Twin A/A -- User-Level Bootstrap Pairs (9-dim with segment replacing tier) |
| 2026-06-02 | aa bootstrap user pairs admin | -- Synthetic Twin A/A -- User-Level Bootstrap Pairs (12-dim: base 11 + has_admin_permissions_ind) |
| 2026-06-02 | aa bootstrap user pairs industry | -- Synthetic Twin A/A -- User-Level Bootstrap Pairs (12-dim: base 11 + industry_bucket) |
| 2026-06-02 | aa team retention 10k | -- Synthetic Twin A/A Test — Team-Level Retention |
| 2026-06-02 | aa team retention 1k | -- Synthetic Twin A/A Test — Team-Level Retention |
| 2026-06-02 | aa teamsize team retention 10k | -- Synthetic Twin A/A Test — Team-Level Retention |
| 2026-06-02 | aa teamsize user retention 10k | -- Synthetic Twin A/A Test — User-Level Retention |
| 2026-06-02 | aa test retention team level v1 | -- Team-Level A/A Retention Bias Test |
| 2026-06-02 | aa test revenue no inbox arr 3bin team no rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr 3bin team rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr 5bin user no rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr 5bin user rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr bucket 5bin no rm 1k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr bucket 5bin rm 1k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr bucket no rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue no inbox arr bucket rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa test revenue with inbox arr 5bin user rm 10k | -- Synthetic Twin A/A Test — ARR Impact (Limited Attributes, Required Match) |
| 2026-06-02 | aa user retention 10k | -- Synthetic Twin A/A Test — User-Level Retention |
| 2026-06-02 | aa user retention 1k | -- Synthetic Twin A/A Test — User-Level Retention |
| 2026-06-02 | aa user revenue diagnostic by period | -- Diagnostic: treatment vs control ARR per user by period |
| 2026-06-02 | aa user revenue team size diagnostic | -- Diagnostic: compare team size between treatment and matched control |
| 2026-06-02 | retention query | -- Synthetic Twin Model — Retention Query |
| 2026-06-02 | retention query | -- Synthetic Twin Model — Team-Level Retention Query (sub_segment, 9-dim) |
| 2026-06-02 | amp retention perform search | -- Synthetic Twin Model â€” User-Level Retention Query (sub_segment, 9-dim) |
| 2026-06-02 | retention query | -- Synthetic Twin Model — User-Level Retention Query (sub_segment, 9-dim) |
| 2026-06-01 | chrome extension 05 apollo everywhere 20260528 | > **Author:** Valery | **Date:** 2026-05-28 | **Data as of:** 2026-05-27 |
| 2026-06-01 | chrome extension 06 support tickets 20260529 | > **Author:** Valery | **Date:** 2026-05-29 | **Data as of:** 2026-05-28 |
| 2026-05-31 | backtest | -- ============================================================================ |
| 2026-05-29 | ai assistant credit surface 2026 05 23 | **Author:** Sai Sarvepalli |
| 2026-05-29 | daily shape | -- Daily ARR flows from FCT_DAILY_REVENUE for shape curve CDFs + current month pacing. |
| 2026-05-29 | weekly flows | -- Weekly ARR flows from FCT_DAILY_REVENUE for trailing 26-week trend view. |
| 2026-05-29 | monthly arr impact | -- GE-5110: Monthly ARR overstatement from duplicate Mid-Term Upsells |
| 2026-06-03 | lu weekly insights | -- LU_WEEKLY_INSIGHTS — Weekly strategic recommendations from analytics deep-dives |
| 2026-06-03 | lu business glossary | -- LU_BUSINESS_GLOSSARY — DE-owned business term definitions |
| 2026-06-03 | lu saved metrics | -- LU_SAVED_METRICS — AE-owned canonical metric queries |
| 2026-06-01 | mcp hex canonical queries | Source: \[v0 — MCP Product Operating Metrics & Health\](https://app.hex.tech/apollo/hex/v0-MCP-Product-Operating... |
| 2026-06-03 | dim teams daily v2 spine fix | -- DIM_TEAMS_DAILY_V2 — SPINE FIX |
| 2026-06-03 | lu team segment | -- LU_TEAM_SEGMENT — Daily refresh procedure with data quality checks |
| 2026-06-02 | sp dashboard refresh | -- Canonical SP_DASHBOARD_REFRESH — registry-driven JS proc. |

<!-- /SECTION: weekly-sweep -->
