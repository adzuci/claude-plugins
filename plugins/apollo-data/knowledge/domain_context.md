<!-- SECTION: curated -->
# Domain Context
*Auto-generated 2026-03-27 by scripts/build_domain_context.py*
*Source: domain/index.md — 73 indexed files*

---

## Always-On Reference

### revenue_org_structure
*Updated 2026-03-20 | Owner: Leo*

  - `FCT_MONTHLY_REVENUE` columns `ARR_SS` / `ARR_REP` / `ARR_SA` are the motion splits
  - Rep-driven segment = `ACCOUNT_SALES_DEPARTMENT_TIER` (Tier1/2 → MM, Tier3/4 → SMB), not `ACCOUNT_SEGMENT`
  - VSB deflection project (April 2026 cutover) is the active retention lever for VSB churn
  - Always validate doc-quoted numbers against Snowflake before using them
**Use when:** doing a revenue debrief, figuring out who owns a metric, or building any SS/rep-driven ARR analysis.

### hvo_activation_findings
*Updated 2026-03-25 | Owner: Leo*

  - Dialer has the highest lift (+142%) when covered on call, but only 33% of calls cover it — biggest lever
  - Covering Sequence on call drives 2–2.4x 30-day activation vs not covered, across all segments
  - HVO Activated teams: SMB avg NRR 132.8% vs 91.1% for HVO No Activation
  - Non-HVO higher logo retention = selection bias, not a ceiling
  - Join path: `ONBOARDING_HIGH_VELOCITY_TEAMS` → `FCT_MONGO_CONVERSATIONS` → `HVO_CALLS_AI_PROCESSING` (REPLACE quotes on APOLLO_TEAM_ID)
**Use when:** working on HVO program analysis, onboarding effectiveness, PS/CS coaching, or any NRR driver analysis.

### signal_sources
*Updated 2026-03-20 | Owner: Shyam SK*

  - Consolidation table: `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS` — one row per (team, week, signal_source, signal_type)
  - ~800K rows total; 8w_churn_model dominates at 745K rows
  - `SIGNAL_METADATA` is a VARIANT array — use `LATERAL FLATTEN` directly, NOT `TRY_PARSE_JSON()`
  - `support_conversations` is NOT a live signal source (not in the actual table despite appearing in dbt plans)
  - GTME coverage is sparse (~800 signals) vs ML model (~745K) — many at-risk accounts have zero GTME coverage
**Use when:** querying team health signals, understanding what churn/upsell/sentiment data is available, or building dashboards on customer engagement drops.

### mcp_analytics
*Updated 2026-03-24 | Owner: Leo Liu*

  - MCP user SoT: `DIM_USERS.FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL` (Shyam added 2026-03-23)
  - FCT_MONGO_HTTP_REQUESTS_V3_RT_VW is in ANALYTICS_DATAPLATFORM (not ANALYTICS) — filter `USER_AGENT = 'Apollo-MCP/1.0'`
  - Feb–Mar 2026 cohort: 1,816 users, 45% Day-0, 4–28× FTP lift vs peers, net-new user type (not cannibalization)
  - OAuth token caching bug: ~10+ support tickets, upgrade flow broken until re-auth
**Use when:** analyzing MCP adoption, building MCP dashboards, or adding MCP to a product debrief.

## Hot Files (last 30 days)

**deliverability** (2026-03-27)
  - Spam blocks are included in overall bounce rate — `delivery_rate + overall_bounce_rate = 100%`
  - Open rate denominator must be `open_tracking_enabled = 1 AND delivered = 1` (not all delivered)
  - Bounce thresholds: > 5% high, > 10% extremely high

**new_trial_influenced_ss_arr** (2026-03-27)
  - 14-day attribution window; most recent trial per team per purchase day
  - `trial_grouped` values: `basic`, `professional`, `custom`, `unknown` — always exclude `no_trial` when measuring trial-influenced ARR
  - Recommended warehouse: `elt_wh_dp`

**inbound_addon_churn** (2026-03-27)
  - Uses `dim_mongo_teams_rt_vw.product_infos` flattened for `%inbound%` plans
  - ARR hard-coded: monthly $149×12, yearly $119×12 (no discount scaling)
  - Sales motion persisted from first matched closed-won opp per team (±1 day match window)

**inbound_addon_purchases** (2026-03-27)
  - Adds `account_segment` and `tier` from `dim_salesforce_accounts`
  - Includes `quarterly` billing cadence (priced at $149×12)
  - Dedup: `dense_rank` on `start_date desc` per team — only latest plan counted

**dialer_addon_churn** (2026-03-27)
  - Uses `dim_mongo_teams_rt_vw.product_infos` flattened for `%dialer%` plans
  - ARR hard-coded: monthly $149×12, yearly $119×12
  - Extra output: `num_days_used_dialer_add_on` — days between plan start and last active date

**dialer_addon_purchases** (2026-03-27)
  - Adds `account_segment` and `tier` from `dim_salesforce_accounts`
  - Includes `quarterly` billing cadence (priced at $149×12)
  - Output includes `arr` (summed annualized ARR) in addition to team count

**fy27_aop_rnd** (2026-03-22)
  - COKR3 "70% of paid on >1 automation" has no single Snowflake source today — Analytics gap
  - AI/Signal credit type mapping in FCT_TEAM_CREDITS_DAILY is undocumented — Analytics gap
  - Deals/CI goal: replace Gong for CI + forecasting; dogfood internally first

**fy27_aop_gtme_partnerships_support** (2026-03-22)
  - GTME credit tracking is unreliable — blocks Play measurement (known blocker)
  - Support CSAT/FCR/AHT/escalation metrics live in Intercom, NOT in Snowflake (DIM_SUPPORT_CONVERSATIONS)
  - Partnership ARR attribution (partner-sourced vs influenced) has no confirmed Snowflake source

**fy27_aop_analytics** (2026-03-22)
  - Tenet: "Partnership not request-fulfillment" — Analytics is a strategic partner, not a ticket shop
  - Analytics Asset WAU target: 200 (was 17 in FY26, reached 151)
  - Credit-to-revenue translation is the biggest unsolved measurement problem

**fy27_aop_growth_acquisition** (2026-03-22)
  - W2 FTP target: 4.0% → 4.5%; F0–14 activation currently inconsistent/non-existent
  - Non-brand SEO collapsed -78.9% (147K → 31K clicks); pivoting to product-led + LLM citation
  - Golden population = Core/NA/Sales dept>3, 1–2 seat teams; PLSM = product signals → Stage 1 opps

**fy27_aop_org_map** (2026-03-22)
  - NRR 71% → 100% is the company north star; every org's goals feed it
  - Golden population = Core/NA/Sales dept>3, 1–2 seat teams — highest expand potential
  - GTME covers all custom/org plan accounts in FY27 (was subset in FY26); 60% CSQL win rate benchmark

**aop_fy27_strategic_priorities** (2026-03-20)
  - Top churn reason: "not using it enough" — product complexity is a first-order problem
  - Rep-driven new ARR target +79% YoY, rep-driven upsell +134% YoY — upmarket is the growth bet
  - Credits: 2,066M total target (+142%), Waterfall/Enrichment +402%, AI Power-Up +151%

**aop_execution_alignment_20260324** (2026-03-24)
  - Growth & Acquisition rated HIGH RISK — FTP cohorts, PQL/PQA, F0-14 activation all missing from Snowflake
  - Partnerships rated CRITICAL — $7.2M target with zero dedicated analytics
  - GTME metrics dashboard (Q2 deadline) has zero visible build progress

**measurement_gap_tracker** (2026-03-24)
  - 12 gaps tracked; 4 are S-complexity quick wins (segment on team tables, churn taxonomy, FTP cohorts, AI deflection rate)
  - Partnerships ($7.2M target) has zero dedicated analytics — CRITICAL gap
  - GTME dashboard (Q2 deadline) has zero build progress — highest individual risk

**sales_motion_definitions** (2026-03-20)
  - Four motions: Self-Serve (SS), Sales-Assisted (SA), Rep-Driven (Rep), Apollo Labs — NOT mutually exclusive at the account level
  - A single account can carry ARR in multiple motion buckets simultaneously (multiple opps with different owners)
  - Transaction-level attribution is well-defined and in production; customer-level single-label attribution is the open gap

**product_debrief_template** (2026-03-20)
  - BAT pain points should be mapped to open Jira issues where possible
  - `GENERAL_CONVERSATION_TOPIC` is the populated column in `DIM_SUPPORT_CONVERSATIONS` (not `CONVERSATION_MAIN_CATEGORY`)
  - `ARRAY_CONTAINS` on BAT VARIANT columns may not match — use `SEQUENCE_CREATED`, `MAILBOX_LINKED`, and LIKE on `PAIN_POINT` instead

**copilot_roi** (2026-03-20)
  - Built in 15 days from first commit
  - Covers asset inventory, build velocity, and what the copilot replaced

**sql_patterns** (2026-03-21)
  - **Two ARR cuts:** RevOps = `FCT_MONTHLY_REVENUE` at parent account level; Analytics = team level. Numbers differ — don't mix.
  - WAT weekly snapshot: Sunday (`DAYOFWEEK(date) = 0`) is canonical
  - NRR: cohort-based via `DIM_TEAMS.FIRST_PAID_DATE`; default 12M window

**cbr_data_sources** (2026-03-20)
  - Mar 2026 (prelim): $199.1M ARR (+3.2% MoM); NNARR net = +$7.2M
  - M3 NRR Dec 2025 cohort: 78.1% (target 90%, gap -11.9pp)
  - Org Plan retention: 80.4% (above 60% target) on 6,773 custom edition teams

**hex_cbr_notebooks** (2026-03-20)
  - KR targets: $1.1M Inbound ARR, 2x enrichment credits (90M/mo), $1.7M Dialer ARR, 27M AI credits/mo, 10K AI Assistant paid core WAUs with 25% W4 retention
  - `product_metrics_daily` (ANALYTICS_DATASCIENCE) is the canonical table for DAU/WAU/MAU, conversion, NRR by segment, feature retention, participation
  - AI Assistant "active" = ≥1 tool call (excludes proactive system-only threads); W4 retention window = days 22-28

**analyze-experiment** (2026-03-25)
  - Exposure source: `DIM_MONGO_EXPERIMENT_EXPOSURES` (never `FCT_AMPLITUDE_EVENTS`) — now catalogued in `data-catalog/context/`
  - Always team-level; always excludes variant-hoppers; always uses first exposure datetime
  - Additional metrics available on request after the standard report

**mongo_collection_check** (2026-03-20)
  - Invoke with `/mongo-collection-check <collection_name> [timeframe]`
  - Requires leadgenie repo cloned locally
  - Searches model fields, workers, migrations, bulk scripts, feature flags

**source_catalog** (2026-03-20)
  - Invoke with `/source-catalog <amplitude|mongo|sfdc> <object-name> [field-name]`
  - Reads leadgenie + SFDCgearset codebases to produce a reference card
  - SFDC has two modes: object overview (TL;DR) or field deep-dive (full metadata)

**skill_registry** (2026-03-24)
  - 12 skills tracked (7 user-invocable, 5 agent-only)
  - Validation script: `python3 scripts/validate_new_skill.py --all`
  - Each skill is checked for: frontmatter, table catalog compliance, execution guidance, hallucination patterns

**table_registration_checklist** (2026-03-24)
  - 3 locations required: `data-catalog/context/`, `table_inventory.md`, `lu_data_catalog.sql`
  - Validation script: `python3 scripts/validate_new_table.py <TABLE_NAME>`
  - Trust tiers: canonical > preferred > reference > avoid

**persistent_claude_session** (2026-03-20)
  - How to keep a Claude Code session running permanently using tmux. Covers starting, detaching, reattaching, and Codespace-specific notes (idle timeout, heartbeat).

**compact_plugin_context** (2026-03-23)
  - Phase 1: Gather raw context from repo, Slack, Notion, Docs, Jira, Snowflake, dbt, Cursor/MCP
  - Phase 2: Update teammate profiles with fresh stats
  - Frequency: Weekly Monday or pre-export

**pokemon_compendium** (2026-03-23)
  - Covers executives, analytics leadership, analytics engineering, data science, data engineering, and business analytics
  - Includes game rules and battle mechanics for inter-team battles
  - Canon status: Official

**leader_suit** (2026-03-25)
  - Both suits are **opt-in only** — never applied by default
  - Analyst suit: activate when asked to "run analysis as Leo" or "put on the analyst suit"
  - Leader suit: activate only when someone asks "what would Leo tell me?" or "how would Leo see this?"

**project_dim_teams_daily_rebuild** (2026-03-20)
  - Current DIM_TEAMS_DAILY: 8.7B rows, 207 columns, dbt-owned, fragile
  - 14 foundation tables live and stable in PLAYGROUND for 2 weeks; DQ checks passing
  - Major open design question: all-teams spine (8.7B row parity vs. active-only 288K)

**dim_teams_daily_v2_gap_analysis** (2026-03-24)
  - V2 has 30 of 207 columns — covers core IDs, active user counts (L1/L7/L28), 11 feature user counts (L7 only), and 8 credit columns
  - HIGH PRIORITY missing: ARR motion splits (3 columns), segment/edition columns, revenue change columns
  - Row count gap: 303K (active only) vs 8.7B (all teams x all days) — spine needs fix

**credit_types** (2026-03-22)
  - **Waterfall Enrichment** uses waterfall trial credits first, then falls back to unified (≈1 credit/record) — this is why it doesn't show in standard unified credit queries
  - **Direct Dial** = 3–10 unified credits per number (region-based); support tickets report 9–35 — delta likely from waterfall-via-phone multi-vendor attempts
  - **AI Email** draws from Apollo's AI pool (3B credits), NOT customer-billed — exclude from customer credit consumption metrics

**churn_analysis_leo_2026-03-20** (2026-03-20)
  - Two analyses: (1) General churn — 89.5% of churned accounts correctly flagged by 8-week model but zero GTME coverage and no automated intervention. (2) Inbound churn — 200 churned teams analyzed; 97% never published a router, 0% booked meetings, 74% used product 30+ days before churning silently.

**jarvis-plugin-it-20260323** (2026-03-23)
  - Plugin deployment architecture: corporate GitHub repo (cloud-plugins), Okta auth via MCP relay, GCP-hosted servers replacing ngrok. Skills-first approach over hooks. Cost optimization: shrink Looker/Hex licenses. Action items: Bridie test locally, Patrick add repo access, Rama complete Snowflake MCP by Wednesday.

**leo-bridie-20260323** (2026-03-23)
  - Launch prep: guardrails implemented (64 approved tables), two skills for V1 (Account Detail + Product Debrief). Blockers: Rev Org alignment gap, DQ verification incomplete, teams in reactive mode. GCP server approved for daemon. Leo on PTO next week — launch must happen before.

**seal-team-20260323** (2026-03-23)
  - Launch scope: Account Detail + Product Debrief to Seal Team by EOD pending Patrick IT approval. DS teams assigned to QA product debriefs by EOW. Governance: protected branches, conflict detection, two-tier repo (copilot → Jarvis). Leo recording video walkthrough for DS setup. Bridie + Rahul designing skills governance with Deepak.

**analytics_insight_review_20260325** (2026-03-25)
  - Jarvis alpha launch: Friday deploy to all Claude users via IT cloud enterprise
  - High-volume sender strategy: manual conversion required (successfully converted 2nd-largest sender)
  - AI email: 36% of AI email teams have zero sequence power-ups — power-up/AI email correlation is broken

**executive_profiles** (2026-03-24)
  - Matt Curl (CEO) has 14 direct reports; Leo reports directly to CEO
  - James Boone (Sr Dir Onboarding) is the heaviest non-Analytics Snowflake user (5,748 queries/30 days)
  - Karthik Mahadevan (Dir Pricing) runs 699 queries/30 days — very data-literate

**department_profiles** (2026-03-24)
  - Partnerships is CRITICAL risk — $7.2M target with zero analytics support
  - Growth & Acquisition is HIGH risk — FTP cohorts, PQL/PQA, F0-14 all missing
  - GTME is HIGH risk — Q2 dashboard deadline with zero build progress

**squad_profiles** (2026-03-24)
  - Lifecycle (Ben Frutos) is the largest unserved growth function — no dedicated analyst
  - Named/Managed GTME pods have no working metrics dashboard
  - 6 AI content agents deployed under SEO/AEO squad

## Recent Report-Outs & Findings

| Date | Source | Key Finding or Decision |
|------|--------|-------------------------|
| 2026-03-27 | deliverability | Spam blocks are included in overall bounce rate — `delivery_rate + overall_bounce_rate = 100%` |
| 2026-03-27 | inbound addon churn | Uses `dim_mongo_teams_rt_vw.product_infos` flattened for `%inbound%` plans |
| 2026-03-27 | inbound addon purchases | Adds `account_segment` and `tier` from `dim_salesforce_accounts` |
| 2026-03-27 | dialer addon churn | Uses `dim_mongo_teams_rt_vw.product_infos` flattened for `%dialer%` plans |
| 2026-03-27 | dialer addon purchases | Adds `account_segment` and `tier` from `dim_salesforce_accounts` |
| 2026-03-25 | analytics insight review 20260325 | Jarvis alpha launch: Friday deploy to all Claude users via IT cloud enterprise |
<!-- /SECTION: curated -->

<!-- SECTION: weekly-sweep -->
---

## Weekly Sweep — 2026-03-27
*Auto-replaced each run. Do not edit manually.*

| Date | Source | Key Finding or Decision |
|------|--------|------------------------|
| 2026-03-22 | glossary entries | Business term definitions with SQL predicates where applicable. Maps to `LU_BUSINESS_GLOSSARY` in Snowflake. |
| 2026-03-24 | leo alignment briefing 20260324 | **From:** Jarvis + Bridie |
| 2026-03-24 | gdrive digest 20260324 | | # | Title | Owner | Updated By | Date | URL | |
| 2026-03-24 | slack digest 20260324 | - **Leo** flagged a DIM_SUPPORT_CONVERSATIONS anomaly in #xfn-data-analytics (Mar 20): 10x spike in IS_CONVERS... |
| 2026-03-24 | leo decisions 20260324 | **Date:** 2026-03-24 (Data Leads Weekly) |
| 2026-03-27 | lu saved metrics snapshot | -- LU_SAVED_METRICS snapshot — 2026-03-27 |
| 2026-03-24 | FCT DAILY REVENUE | > Daily revenue snapshot per team. Core financial table. |
| 2026-03-24 | weekly data leads 20260324 | The Jarvis plugin is in testing after resolving Snowflake connection issues using a Python workaround; a PR is... |
| 2026-03-24 | FCT MONTHLY REVENUE | > Monthly revenue with change categories (new, churn, upgrade, downgrade). Core retention table. |
| 2026-03-24 | jira digest 20260324 | | Ticket | Title | Assignee | Status | Priority | |
| 2026-03-24 | notion digest 20260324 | 1. **Master PRD: Analytics Co-Pilot Agent** (updated Mar 19) |
| 2026-03-20 | GTME CALLS AI ANALYSIS | > LLM-extracted structured intelligence from GTME (Go-To-Market Engineer) / CSM call transcripts — the GTME eq... |
| 2026-03-20 | USER DIALER ACTIONS DAILY | > Daily user-level dialer actions. One row per user per action per event date. |
| 2026-03-27 | DIM USER ACTIVATION | > Data Science dimension: first calendar date each user hit tracked activation steps (PLG / product milestones... |
| 2026-03-26 | FCT CANCELLATION SURVEY RESULTS | > Cancellation survey submissions from customers downgrading or cancelling their Apollo subscription. One row ... |
| 2026-03-23 | DIM TEAMS | > Data Science team dimension. Enriched team-level attributes for product analytics. |
| 2026-03-20 | free to paid rate | > **Owner:** Andrew Green (Analytics) / Conversion PM |
| 2026-03-26 | USER SEQUENCE ACTIONS DAILY | > Daily user-level sequence actions. One row per user per action per event date. |
| 2026-03-26 | USER WORKFLOW ACTIONS DAILY | > Daily user-level workflow actions. One row per user per action per event date. |
| 2026-03-24 | battle skill release notes 20260324 | **Skill:** `/apollo-data:battle` |
| 2026-03-23 | FCT MONGO HTTP REQUESTS V3 RT VW | > Real-time view of Apollo HTTP API requests — raw source for MCP usage. **As of 2026-03-23, prefer DIM_USERS ... |
| 2026-03-23 | FCT MONGO DAILY TEAM AUDIT REPORTS | > Daily team audit snapshots from MongoDB. Credit limits, billing period, and plan details. |
| 2026-03-22 | DIM TEAMS DAILY | > Daily snapshot of team-level metrics. One row per team per day. |
| 2026-03-21 | USER INBOUND ACTIONS DAILY | > Daily user-level inbound feature actions. One row per user per action per event date. |
| 2026-03-20 | INT TEAM PRODUCT INFO CLEANED | > Cleaned team-level product/plan information. Intermediate table. |
| 2026-03-20 | FCT TEAM PHONE CALLS DAILY | > Daily phone call activity per team — call counts, user counts, and duration by status, outcome, and purpose. |
| 2026-03-26 | DIM MONGO DOMAIN DIAGNOSES | > Domain authentication and health diagnosis records. One row per domain diagnosis. |
| 2026-03-26 | DIM MONGO VOICE SETTINGS | > Dimension table for voice/dialer phone number settings. One row per voice setting (phone number) per user. |
| 2026-03-26 | DIM INTERCOM CUSTOMER CHAT LOGS | > Full text of Intercom customer support chat logs. Multiple rows per conversation (one per message or log ent... |
| 2026-03-25 | DIM MONGO SSO CONFIGS | > One row per SSO configuration per team. Tracks which teams have set up SSO (OAuth or SAML), which identity p... |
| 2026-03-25 | daily seal team standup 20260325 | Leo will demo Jarvis output capabilities at the insight review, showcasing product debriefs with trend graphs ... |
| 2026-03-24 | CLAUDE | Read this file at the start of every session that involves the data catalog. It tells you what's done, what's ... |
| 2026-03-24 | FCT AMPLITUDE EVENTS | > Amplitude event tracking — user-level product events. One row per event. |
| 2026-03-23 | AGG USER API CALLS DAILY | > Daily aggregated API call counts per user. **As of 2026-03-23, prefer DIM_USERS / DIM_TEAMS for MCP-segmente... |
| 2026-03-23 | DIM USERS | > Data Science user dimension. Enriched user-level attributes for product analytics. |
| 2026-03-24 | CUSTOMERS METADATA | > Stripe customers metadata table (external data share). Key-value metadata on Stripe customers — the bridge b... |
| 2026-03-24 | FCT MONGO TEAM PLAN UPDATE ATTEMPTS | > Every billing event at Apollo — plan changes, upgrades, new customers. The primary bridge between Apollo tea... |
| 2026-03-24 | INVOICES | > Stripe invoices table (external data share). Contains all invoices across both Apollo billing flows — plan c... |
| 2026-03-23 | DIM MONGO EXPERIMENT EXPOSURES | > Canonical source for user-level experiment exposure events from MongoDB. Records when a user was assigned to... |
| 2026-03-23 | DIM SALESFORCE ACCOUNTS | > Salesforce account dimension. One row per SF account. |
| 2026-03-22 | AGG TEAM CREDITS | > **Canonical SoT for customer-billed credit consumption.** Use `FEATURE_TYPE` (not `CREDIT_TYPE`) as the prim... |
| 2026-03-21 | SEQUENCES | > ✅ **Canonical source for sequence-level email analysis.** Default to this table for open rate, reply rate, b... |
| 2026-03-20 | HVO CALLS AI PROCESSING | > LLM-extracted structured intelligence from HVO (High Value Onboarding) call transcripts — aka "Project BAT." |
| 2026-03-20 | FCT TEAM CREDIT USE DAILY | > Daily credit usage per team per credit type and feature type — most granular credit table showing which feat... |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-27 | brighid | - [ ] **Next up** — TBD |
| 2026-03-24 | 2026 03 24 brighid seal team | **Date:** 2026-03-24 (Monday) |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | hvo nrr correlation 2026 03 19 | **Author:** Brighid Meredith (via Jarvis) |
| 2026-03-20 | estaff decisions 2026 03 19 | > **From:** Analytics (Brighid/Jarvis) | **For:** E-Staff & KR Owners | **Data as of:** 2026-03-19 |
| 2026-03-20 | weekly signals | - **Focus:** Analytics Copilot v1 milestone — shipped plugin, 14 foundation tables, full registry |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | tomorrow 2026 03 20 | 1. **Built 4 autonomous agents** — all committed, pushed, and installed via launchd: |
| 2026-03-27 | journal | Daily log of work on the analytics data layer. Newest entries at top. |
| 2026-03-23 | apollo product debrief 2026 03 23 | **Owner:** Leo Liu | **Window:** 30 days (Feb 22 – Mar 22, 2026) | **Scope:** All product areas |
| 2026-03-22 | growth debrief 2026 03 22 | **Area:** Apollo Growth (ARR waterfall · team acquisition · self-serve / PLG · onboarding + activation · free-... |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What He's Shipping | Why It Matters | |
| 2026-03-20 | credit monetization analysis 2026 03 19 | **Author:** Brighid (via Jarvis) |
| 2026-03-25 | inbound debrief 2026 03 25 | **Date:** March 25, 2026 (rerun) |
| 2026-03-25 | pubudu | - **AI Assistant retention investigation** (2026-03-25) — full segmentation suite built and published to Notio... |
| 2026-03-23 | kenny keesee debrief 2026 03 23 | **Date:** 2026-03-23 | **Owner:** Leo Liu | **Audience:** Leo / Kenny sync prep |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What She's Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What He's Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What He's Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What He's Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | README | Welcome to the team directory. Each person has a `context.md` profile — a rich "player card" with their role, ... |
| 2026-03-20 | estaff weekly brief 2026 03 19 | **Week of March 17, 2026** | Prepared by Analytics (Jarvis) | Data as of 2026-03-18 |
| 2026-03-20 | hex notebooks context | Extracted 2026-03-20 from 4 Hex notebooks via Threads Agent. Covers SQL table sources, metric definitions, sec... |
| 2026-03-26 | free plan search limit gate exploratory 2026 03 26 | **Branch:** `exploratory-free-plan-search-limit-gate` |
| 2026-03-25 | one seat org plan analysis 2026 03 25 | **Branch:** `one-seat-org-plan-pricing-packaging-research` |
| 2026-03-23 | strategic context | | What She's Shipping | Why It Matters | |
| 2026-03-22 | pipeline notes | I own data quality of `agg_team_credits`. |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What She's Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | ai assistant debrief 2026 03 20 | **Date:** 2026-03-20 | **Author:** Jarvis (via Leo Liu) |
| 2026-03-20 | pipeline notes | AI Assistant data pipeline behavior, refresh timing, and failure modes. |
| 2026-03-20 | stakeholders | Who owns what in the AI Assistant / data platform space. |
| 2026-03-20 | refresh prompt | You are refreshing the weekly context profiles for the Analytics team's teammates. |
| 2026-03-26 | sai | - **fct_ai_assistant_threads enrichment** — Adding team_id and content_center columns (branch: `feature/fct-th... |
| 2026-03-25 | outbound debrief 2026 03 25 | **Area:** Outbound / Sequences / Email Deliverability |
| 2026-03-25 | hvo activation analysis | **Author:** Jarvis (via Leo's request) |
| 2026-03-24 | ai assistant debrief 2026 03 24 | **Area:** AI Assistant (scoped — excludes Power Ups and AI Messaging) |
| 2026-03-24 | prompt | This document tells Jarvis how to handle questions from support stakeholders in `#jarvis-support-qs`. Read thi... |
| 2026-03-22 | waterfall debrief 2026 03 22 | **Date:** 2026-03-22 | **Window:** 30 days | **Author:** Jarvis |
| 2026-03-21 | inbound debrief 2026 03 21 | **Area:** Inbound (website visitor tracking, workflows, forms, inbound router) |
| 2026-03-20 | strategic context | | What She's Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | ai assistant retention deepdive 2026 03 19 | **Prepared for:** Tyler Phillips & E-Staff |
| 2026-03-20 | alignment meeting 2026 03 10 | **Date:** 2026-03-10 | **Duration:** 30 min | **Attendees:** Rahul, KT, Brighid |
| 2026-03-20 | hvo insights review 2026 03 19 | > **Format:** Insights review (actionable findings + recommendations) | **Audience:** Leo Liu, Growth Conversi... |
| 2026-03-24 | ai platform debrief 2026 03 24 | **Date:** March 24, 2026 |
| 2026-03-23 | ai debrief 2026 03 23 | **Prepared by:** Jarvis (run by Pubudu Wariyapola) |
| 2026-03-21 | api debrief 2026 03 21 | **Area:** Enrichment API + broader API (MCP, REST) |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | outbound vs inbound pipeline 2026 03 19 | **Author:** Brighid Meredith (via Jarvis) |
| 2026-03-20 | conversation intelligence debrief 2026 03 20 | **Date:** 2026-03-20 | **Author:** Jarvis (via Leo Liu) |
| 2026-03-20 | inbound debrief 2026 03 20 | **Date:** 2026-03-20 | **Author:** Jarvis (via Leo Liu) |
| 2026-03-20 | outbound debrief 2026 03 20 | **Date:** 2026-03-20 | **Author:** Jarvis (via Leo Liu) |
| 2026-03-26 | ai assistant engagement queries | -- AI Assistant — Engagement & Retention Query Library |
| 2026-03-24 | ai debrief 2026 03 24 | **Prepared by:** Jarvis (run by Pubudu Wariyapola) |
| 2026-03-20 | strategic context | | What They're Shipping | Why It Matters | |
| 2026-03-20 | stakeholders | | Domain | Owner | Notes | |
| 2026-03-20 | enrichment debrief 2026 03 20 | **Date:** 2026-03-20 | **Author:** Jarvis (via Leo Liu) |
| 2026-03-25 | lu saved metrics | -- LU_SAVED_METRICS — AE-owned canonical metric queries |
| 2026-03-24 | dim teams daily v2 spine fix | -- DIM_TEAMS_DAILY_V2 — SPINE FIX |
<!-- /SECTION: weekly-sweep -->
