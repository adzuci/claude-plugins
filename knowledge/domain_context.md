<!-- SECTION: curated -->
# Domain Context
*Auto-generated 2026-04-20 by scripts/build_domain_context.py*
*Source: domain/index.md — 135 indexed files*

---

## Critical Context

Always-on references — loaded regardless of question type.

**contribution_guidelines** — Rules and heuristics for anyone contributing to this repo: protected files, sanity checks (no personal names in shared paths, no duplicate dirs, register files on creation), where content belongs, how to sync to Jarvis, and commit conventions.

**jarvis_characters** — Character backstory and protocol reference: Henry, Shyam, Papa Curl, error logging (henry_errors.jsonl), metric-not-found messages, and the Pride & Dignity protocol.

**active_personas** — Always-on background voices that run in every session: Jarvis (personality), Pepper (infrastructure immune system + persona traffic controller), Rhodey (experimental rigor / process cop / recap spin detection), Tony (visionary, storyteller, unblocker, startup energy). Pepper has admin oversight — max 2 persona callouts per response. Also defines the Ultron rogue override list and persona interaction rules.

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
- `product_portfolio_taxonomy` — H1 = optimize (not maximize): maintain high NRR, improve COGS, drive multi-product attach *(Mar 30)*
- `theory_of_change` — Teams hitting 4+ Record Actions in F14D have 3× higher M3 NRR than those that don't *(Mar 30)*
- `activation_methodology` — Formula: COUNT(teams ≥4 RAs in F14D) / COUNT(teams activated in window) — Golden Pop only *(Mar 30)*
- `ai_sheets_user_definition` — Status: PENDING — product team (Adhiraj) needs to confirm definition before any queries can be built *(Mar 30)*
- `churn_taxonomy_draft` — ~36% of churned teams cite low engagement — largest single category *(Mar 30)*
- `aop_execution_alignment_20260324` — Growth & Acquisition rated HIGH RISK — FTP cohorts, PQL/PQA, F0-14 activation all missing from Sn... *(Mar 24)*
- `fy27_aop_rnd` — COKR3 "70% of paid on >1 automation" has no single Snowflake source today — Analytics gap *(Mar 22)*
- `fy27_aop_gtme_partnerships_support` — GTME credit tracking is unreliable — blocks Play measurement (known blocker) *(Mar 22)*
- *+10 more files*

### Org & People
- `leader_suit` — Both suits are **opt-in only** — never applied by default *(Mar 25)*
- `executive_profiles` — Matt Curl (CEO) has 14 direct reports; Leo reports directly to CEO *(Mar 24)*
- `department_profiles` — Maps each department to its analytics partner (or flags the gap where none exists) *(Mar 24)*
- `squad_profiles` — Identifies squads with no dedicated analytics support (e.g. MM Sales for COKR1) *(Mar 24)*
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
- `support_channel_context` — Primary stakeholder: Kenny Keesee (Head of Customer Care, reports to Adam Carr) *(Apr 14)*
- `gtme_managed_teams` — GTME team = non-null `gtme_name` in `dim_salesforce_accounts` + ARR > 0 + custom edition *(Apr 14)*
- `player_cards` — One card per team member with HP, ATK, DEF, SPD, SP.ATK, SP.DEF *(Apr 14)*
- `html_report_standard` — CSS variables: --bg: #0f1117, --surface: #1a1d27, --accent: #6c63ff, --teal: #00d4aa *(Apr 10)*
- `activity_tagging` — Pulse command: `python3 scripts/snowflake_query.py --pulse <action> --detail "<context>"` *(Apr 10)*
- `hex_notebooks_context` — Extracted 2026-03-20 via Threads Agent from Leo's Hex workspace *(Apr 10)*
- `support_perception_analysis_apr2026` — CSAT ~74% among Intercom respondents; G2 support-mentioning reviews lean 60/40 praise-to-complaint *(Apr 8)*
- `JANITOR_FLAGS` — Flagged dirs: `feedback/`, `team/`, `standups/`, `docs/`, `skills/` -- mostly obsolete after rece... *(Apr 6)*
- *+50 more files*

### Meetings
- `analytics_insight_review_20260325` — Jarvis alpha launch: Friday deploy to all Claude users via IT cloud enterprise *(Mar 25)*
- `daily_seal_team_standup_20260325` — Leo to demo Jarvis at insight review: product debrief, MCP onboarding analysis, HBO effectiveness *(Mar 25)*
- `battle_skill_release_notes_20260324` — Ghost typing = low signal source count → stat penalties; teams >50% Ghost = Ghost fusion *(Mar 24)*
- `gdrive_digest_20260324` — Three key docs: Data Leads Weekly agenda (Mar 17), CBR FY27Q1 (CC v3 at 29.48% Paid Core AI WAT, ... *(Mar 24)*
- `jira_digest_20260324` — 80+ legacy tables dropped (ABSM, Vitally, product taxonomy, NRR) — avoid referencing them *(Mar 24)*
- *+11 more files*

### Recent Updates
- `personal_action_board` — Exemplar: `teammates/bridie_meredith/next_up.md` *(Apr 16)*
- `conversion_team_q2_fy27_okr` — KR1: W2 Free-to-Paid Conversion Rate ≥ 1.33% (joint with Lifecycle) *(Apr 9)*
- `zone_assignments` — 17 analysts across DS, AE, GTME/Sales Analytics, and Data Platform Engineering *(Apr 7)*
- `offboarding_protocol` — 7-step checklist: triage → ownership decisions → knowledge extraction → repo updates → archive → ... *(Apr 6)*
- `rnd_okr_structure` — 5 objectives: Meet the Moment, Improve NRR (H1), Upmarket Readiness (H1), New Product Revenue (H2... *(Apr 2)*
- `fiscal_calendar` — Apollo's fiscal year and quarter boundaries. FY27 = Feb 2026–Jan 2027. Feb-start fiscal quarters ... *(Apr 2)*
- `mcp_tool_guidelines` — Token-efficient usage guidelines for MCP tools (Glean, Notion, Gmail, Snowflake). References from... *(Mar 27)*
- `deliverability` — Spam blocks are included in overall bounce rate — `delivery_rate + overall_bounce_rate = 100%` *(Mar 27)*
- *+1 more files*

## Recent Findings

| Date | Source | Key Finding |
|------|--------|-------------|
| 2026-04-14 | support channel context | Primary stakeholder: Kenny Keesee (Head of Customer Care, reports to Adam Carr) |
| 2026-04-09 | conversion team q2 fy27 okr | KR1: W2 Free-to-Paid Conversion Rate ≥ 1.33% (joint with Lifecycle) |
| 2026-04-08 | support perception analysis apr2026 | CSAT ~74% among Intercom respondents; G2 support-mentioning reviews lean 60/40 praise-to-complaint |
| 2026-04-06 | offboarding protocol | 7-step checklist: triage → ownership decisions → knowledge extraction → repo updates → archive → comms → Jarvis memory |
| 2026-04-02 | authoring guide | Rule 1–6: domain files — Read-if precision, mutual exclusivity, primary ownership, Key facts that distinguish, stalen... |
| 2026-04-02 | jarvis schema drift | 3 tables correctly documented as PLAYGROUND |
<!-- /SECTION: curated -->

<!-- SECTION: strategic-context -->
## Strategic Context (as of 2026-04-20)

*Auto-injected by scripts/compact_plugin_context.md. Sources: `aop_execution_alignment_20260420.md`, `measurement_gap_tracker.md`, `worklog/briefings/leo_weekly_20260420.md`, `pokemon_compendium.md`.*

### AOP Alignment Status

| Department | Alignment | Risk | Change vs 03-24 |
|-----------|-----------|------|-----------------|
| Analytics (Leo) | HIGH | MEDIUM | ↑ Scout MVP, janitor, Pepper gate, synthetic-twin shipped |
| Growth & Acquisition (Dan Cronyn) | LOW-MEDIUM | HIGH | ↑ slight — Andrew solo with 4 experiment readouts |
| GTME (Eric Quanstrom) | MEDIUM | HIGH → MEDIUM | ↑↑ Cat Zhou joined, shipped DiD causal playbook |
| R&D / Product | MEDIUM | HIGH | → stable (Pubudu/Mounica/Sai on COKRs) |
| Support (Kenny Keesee) | HIGH | LOW-MEDIUM | ↑↑ Marie promoted to Rescue, 22 commits |
| Partnerships (Jennifer Rhima) | NONE | **CRITICAL** | → no change, Martin inactive, $7.2M target unmeasured |

**Critical finding:** Partnerships remains the single biggest unfilled analytics gap at Apollo. GTME risk partially de-risked by Cat Zhou's DiD methodology — attribution TABLE itself still not built.

### Known Measurement Gaps (what we CAN'T answer yet)

| # | Gap | Status | Owner |
|---|-----|--------|-------|
| 1 | M3 Cohort NRR | IN PROGRESS | Rahul / Bridie reconciled 04-17, table pending |
| 3 | FTP Cohort Definitions (W2 FTP 4.0%→4.5%) | NOT STARTED | Jeffrey named, no commits |
| 6 | Churn Reason Taxonomy | NOT STARTED | Marie/Tighe/Martin — quick win |
| 8 | GTME Intervention-to-ARR | IN PROGRESS | Cat Zhou — methodology done, table pending |
| 9 | Partner-Sourced ARR Tracking | NOT STARTED | Martin — CRITICAL, zero infrastructure |
| 11 | Segment on team-level tables | PARTIAL | Bridie/Rahul — unblocks every sliced metric |
| 12 | CSAT/FCR/AHT from Intercom | PARTIAL | Marie — CSAT/AI/escalation validated; FCR/AHT-video approximate |

If a question hits a NOT STARTED gap, say "we don't track that yet" — don't hallucinate.

### Department Priorities

- **Growth & Acquisition (Dan Cronyn):** W2 FTP 4.0→4.5%, PQL/PQA pipeline, F0-14 activation. Covered (interim) by Andrew Green.
- **GTME (Eric Quanstrom):** Pod model to $46M ARR; prove Plays (WAU, credits, GRR, NRR); Q2 dashboard. Covered by Cat Zhou (de facto); Will Masket nominal owner.
- **R&D / Product (Bela Stepanova):** COKR1 Win Account/MM ($100M), COKR2 Multi-Solution ($85M), COKR3 Onboarding→Agentic, COKR4 AI Native ($70M). Pubudu + Mounica + Sai.
- **Support (Kenny Keesee):** Voice+screenshare default (CSAT 90%), save motion (90% coverage), AI deflection (80%). Marie Ballenger (sole analyst — over-capacity).
- **Partnerships (Jennifer Rhima):** $7.2M FY27 → $30M FY28, international expansion. Martin Ekaputra (inactive this week — CRITICAL gap).
- **Analytics (Leo Liu):** NRR Intelligence Engine (P1), AI measurement (P2), Unified Intelligence (P3), Platform (P4), Reliability (P5).

### Analytics Team Roster (quick "who owns X?" reference)

| Name | Role / Suit | Owns |
|------|-------------|------|
| Leo Liu | Head of Analytics / Mark L + Friday | Strategy, NRR vision, function-debrief skill |
| Bridie Meredith | Data Engineer / Pepper | Foundation tables, copilot, Scout/janitor/critic infrastructure |
| Pubudu Wariyapola | Analyst / War Machine + Iron Patriot | AI experiments, retention, synthetic-twin causal inference |
| Marie Ballenger | Support Scientist / Rescue + Red Snapper | Support analytics, FCR/CSAT, Intercom AI taxonomy |
| Mounica Sonikar | Analyst / Hydro | Waterfall enrichment, ARR attribution, fill-rate comp |
| Sai Sarvepalli | DS / Gemini | AI Assistant VoC, Cortex Search, AI data layer |
| Andrew Green | Analyst / Jarvis Protocol | Metric definitions, Growth experiments, lifecycle |
| Cat Zhou (NEW) | Staff DS / *suit TBD* | GTME Analytics, DiD causal playbook, CBR weekly insights |
| Shyam SK | Analyst / Veronica | Signals pipeline, churn risk, cross-domain detective |
| Rahul Gautam | Data Platform Eng / Legion-08 | Foundation tables, Jarvis Snowflake schema |
| Kirk Hlavka | DS Lead / Legion-01 | DS team, AI product |
| Anvitha Ananth | Legion-02 | Inbound / Growth (interim) |
| Will Masket | Legion-05 | GTME/Sales (nominal — actual coverage: Cat) |
| Kaitlyn Maglietto | Legion-06 | HVO signals, fraud |
| Tara Crabtree | Legion-07 (DEPARTING) | WAT metrics, credits — zone going Iron Monger |
| Deepak Kumar | Data Platform Eng | Reliability CI, scope-guard, catalog coverage |
| Martin Ekaputra | — | Partnerships (sole — CRITICAL gap) |

### Current Leadership Focus (Leo's open decisions)

- **Formalize Cat Zhou's GTME role** (by 04-24) — Named Suit + decide Will vs Cat on AOP GTME-dashboard ownership.
- **Escalate Partnerships gap** (by off-site 04-21) — $7.2M target with zero infrastructure is a structural risk.
- **Tara handoff** (by 04-24) — document credit zone coverage; hand to Shyam/Cy or mark Iron Monger.
- **Growth staffing** — Andrew alone on Growth experimentation; Jeffrey named on FTP but no commits.
- **Marie over-capacity** — flag to Kenny Keesee that Support analytics runs on one contributor.
<!-- /SECTION: strategic-context -->

<!-- SECTION: weekly-sweep -->
---

## Weekly Sweep — 2026-04-20
*Auto-replaced each run. Do not edit manually.*

| Date | Source | Key Finding or Decision |
|------|--------|------------------------|
| 2026-04-20 | aop execution alignment 20260420 | **Author:** Jarvis (on behalf of Bridie) |
| 2026-04-14 | lu business glossary | > Canonical business term definitions with SQL predicates used by the Jarvis plugin to translate exec language... |
| 2026-04-14 | lu saved metrics | > Canonical metric definitions with pre-validated SQL. The Jarvis plugin executes approved metrics verbatim wh... |
| 2026-04-14 | 2026 04 10 140000 | **Questions tested:** 1 (targeted — GA integration discipline test) |
| 2026-04-15 | SUPPORT CONVERSATIONS AI ANALYSIS | > AI-enriched support conversation analysis table. **Paid teams only.** |
| 2026-04-14 | fct team genpipe daily | > **WARNING: THIS TABLE DOES NOT EXIST YET.** Planned daily pipeline generation activity combining sequences +... |
| 2026-04-14 | DIM CUSTOMER IO PEOPLE | > Bridge table mapping Customer.io person IDs to Apollo team IDs. The join key for lifecycle email analysis. |
| 2026-04-17 | AGG MONGO HTTP REQUESTS DAILY | > Daily aggregation of HTTP requests to Apollo's backend, broken out by team, user, user agent, controller/act... |
| 2026-04-17 | FCT TEAM CREDIT USE DAILY | > Daily credit usage per team per credit type and feature type — most granular credit table showing which feat... |
| 2026-04-17 | FCT MONGO EMAIL VERIFY REQUESTS | > Fact table for every email enrichment request — the source of truth for email reveals across all non-waterfa... |
| 2026-04-16 | AGG USER GENPIPE ACTIVATION EVENTS DAILY | > Daily per-user event counts for Genpipe (prospecting/RA) activation steps. |
| 2026-04-16 | SEQUENCES | > ✅ **Canonical source for sequence-level email analysis.** Default to this table for open rate, reply rate, b... |
| 2026-04-15 | STG MONGO  WATERFALL WATERFALL ENRICHMENT REQUEST STATS | > One row per waterfall enrichment request stat record — tracks credit usage, enrichment success, and entity t... |
| 2026-04-15 | AGG AI EMAIL MESSAGING | > Daily aggregate of AI email activity sliced by all key dimensions. Pre-computed counts that power team/user ... |
| 2026-04-14 | lu team attributes | > Team-level attribute lookup: segment, region, SFDC fields, MFA status, subscription lifecycle. Current state... |
| 2026-04-14 | LU TEAM SEGMENT | > Denormalization bypass for segment-sliced queries. Join this instead of going through DIM_SALESFORCE_APOLLO_... |
| 2026-04-14 | matthew curl | > Scanned 2026-04-03, lookback: 14 days, dept: Executive (GC1.33010) , Snowflake user: `MATTHEW_MOORE` |
| 2026-04-13 | FCT AMPLITUDE EVENTS | > Amplitude event tracking — user-level product events. One row per event. |
| 2026-04-17 | lifecycle measurement plan | > ⚠️ **DEPRECATED — DO NOT USE.** This version is out of date. A revised plan is being iterated with cross-fun... |
| 2026-04-20 | leo weekly 20260420 | **Week of:** 2026-04-20 |
| 2026-04-17 | worklog pubudu | - **AI Assistant D1=1 Next Action analysis — 2026-04-17 → WIP, pick up next session** |
| 2026-04-20 | habit ra retention paradox 2026 04 20 | **Author:** Andrew Green (Jarvis Protocol) |
| 2026-04-17 | semantic review 2026 04 17 | **Scope:** Skills + Domain (45 skills, ~60 domain files) |
| 2026-04-16 | slack sweep 2026 04 16 | **Window:** 2026-04-09 → 2026-04-16 (past 7 days) |
| 2026-04-14 | brighid | > Standing log of what Jarvis (Claude Code) worked on with Bridie, why, the value added, and estimated ROI. Up... |
| 2026-04-17 | free plan email cap impact 2026 04 17 | **Author:** Andrew Green |
| 2026-04-14 | gre 557 top nav credit usage widget 2026 04 14 | **Experiment:** `gre-557-top-nav-credit-usage-widget` |
| 2026-04-14 | expiring credits nudge posthoc | **Experiment:** GA-315 | Flag key: `expiring-credits-nudge` |
| 2026-04-17 | pipeline notes | I own data quality of `agg_team_credits`. |
| 2026-04-16 | logging strategy | **Captured:** 2026-04-16 · **Owner:** Bridie · **For:** Leo (impact proof + efficacy monitoring) |
| 2026-04-16 | snowflake query py sweep 2026 04 16 | **Context:** MCP-only migration (commits cc68ff3, 3a28d58, c6bdd96). SKILL.md |
| 2026-04-15 | mcp connector debrief 2026 04 15 | **Date:** 2026-04-15 | **Window:** 30 days (+ full adoption since Feb 23 GA) | **Author:** Jarvis (War Machine... |
| 2026-04-15 | free plan extension restriction 2026 04 15 | **Author:** Andrew Green |
| 2026-04-14 | strategic context | | What She's Shipping | Why It Matters | |
| 2026-04-16 | 2026 04 15 18 | **Run type:** Scheduled 6 PM check (anomaly-only alerting) |
| 2026-04-16 | preset by segment | -- preset_by_segment.sql |
| 2026-04-14 | ai assistant retention analysis | **Author:** Pubudu Wariyapola |
| 2026-04-13 | gtme cbr weekly insights guide | Automates the Monday CBR workflow for GTME-managed account metrics. Fetches SQL queries from Notion, executes ... |
| 2026-04-20 | 2026 04 20 12 | | Domain | Query | Status | Notes | |
| 2026-04-20 | q mcp api ra rebaseline | -- MCP + API × Habit RA Analysis |
| 2026-04-17 | d1 retention by tool | -- d1_retention_by_tool.sql |
| 2026-04-17 | analytics engineer suit | > **Usage:** Activate this suit when the task involves building or modifying data infrastructure — dbt models,... |
| 2026-04-17 | worklog | **Analyst:** Pubudu (suit active) |
| 2026-04-17 | surface attribution trust 2026 04 17 | > Captured 2026-04-17. Report written before /clear, referenced in `next_up.md` as DO item. |
| 2026-04-16 | preset activation retention | -- preset_activation_retention.sql |
| 2026-04-16 | preset by search group | -- preset_by_search_group.sql |
| 2026-04-16 | cerberus full funnel | -- cerberus_full_funnel.sql |
| 2026-04-16 | red snapper suit | > **Usage:** Activates when someone says "use Red Snapper", "orient me", "I'm new to this", or "I don't know w... |
| 2026-04-16 | pepper manifest consistency report | **Scope:** verify `jarvis/knowledge/JARVIS_KNOWLEDGE_BASE_MANIFEST.md` correctly registers the two files calle... |
| 2026-04-16 | 2026 04 16 00 | All three monitoring checks failed to execute. Both the Snowflake MCP server and the Python fallback (`snowfla... |
| 2026-04-15 | TODO suit | Leo roasted suits in #jarvis on 2026-04-15. You said "ooofff. My suit needs work. Will edit." This is your rem... |
| 2026-04-15 | support resolution retention | -- Support Resolution Quality → 30-Day Retention Analysis |
| 2026-04-15 | retention query | -- Synthetic Twin Model — Retention Query |
| 2026-04-14 | ai assistant engagement queries | -- AI Assistant — Engagement & Retention Query Library |
| 2026-04-14 | prompt | You are the Exec Insights Agent. You run every Wednesday morning to generate the weekly E-Staff analytics deci... |
| 2026-04-14 | battle log | | Name | ELO | Wins | Losses | Streak | |
| 2026-04-17 | lu saved metrics | -- LU_SAVED_METRICS — AE-owned canonical metric queries |
| 2026-04-15 | fct team revenue daily | -- FCT_TEAM_REVENUE_DAILY — DE-owned daily revenue snapshot per team |
<!-- /SECTION: weekly-sweep -->

<!-- SECTION: metric-trends -->
## Metric Trends — 2026-04-14

*24 approved metrics | auto-generated by scripts/update_metric_trends.py*

**ARR by Geography** (variant: daily_snapshot)
  Description: ARR and paid team count by billing country and account region. Useful for US vs non-US split and regional breakdowns.
  ds | account_region | billing_country | team_count | total_arr
  2026-04-13 | AMER | None | 45013 | 95437094.0
  2026-04-13 | EMEA | None | 22276 | 36776415.0
  2026-04-13 | None | None | 20489 | 22424255.0
  2026-04-13 | AMER | United States | 2358 | 16423826.0
  2026-04-13 | APAC | United States | 13603 | 13061063.0
  2026-04-13 | APAC | None | 8178 | 12323813.0
  2026-04-13 | EMEA | UAE | 3 | 13560.0
  2026-04-13 | APAC | United Arab Emirates | 3 | 13536.0
  2026-04-13 | None | Singapore | 1 | 13500.0
  2026-04-13 | EMEA | Australia | 3 | 13208.0

**ARR by Industry** (variant: daily_snapshot)
  Description: ARR and paid team count by industry vertical. Sourced from Salesforce account industry field via LU_TEAM_ATTRIBUTES.
  ds | industry | team_count | total_arr
  2026-04-13 | Staffing and Recruiting | 573 | 1396491.0
  2026-04-13 | Higher Education | 982 | 1307817.0
  2026-04-13 | Transportation/Trucking/Railroad | 604 | 1263333.0
  2026-04-13 | Accounting | 485 | 1113884.0
  2026-04-13 | Publishing | 396 | 1092767.0
  2026-04-13 | Insurance | 569 | 1464138.0
  2026-04-13 | Real Estate | 872 | 1422642.0
  2026-04-13 | Logistics and Supply Chain | 539 | 1413841.0
  2026-04-13 | capital markets | 656 | 1407261.0
  2026-04-13 | Political Organization | 1 | 1416.0

**ARR by Segment** (variant: daily_snapshot)
  Description: Current ARR broken down by account segment. Point-in-time daily snapshot.
  ds | account_segment | team_count | total_arr
  2026-04-13 | VSB | 77059 | 92307720.0
  2026-04-13 | Mid-Market | 5219 | 26641344.0
  2026-04-13 | SMB | 27612 | 77455571.0
  2026-04-13 | Enterprise | 3619 | 12220210.0

**ARR by Segment** (variant: trend)
  Description: Daily ARR trend by account segment over a date range.
  ds | account_segment | team_count | total_arr
  2026-03-15 | VSB | 69559 | 83971093.0
  2026-03-15 | SMB | 26191 | 73423284.0
  2026-03-15 | Mid-Market | 4985 | 25931349.0
  2026-03-15 | Enterprise | 3465 | 11883693.0
  2026-03-16 | VSB | 69585 | 83993319.0
  2026-03-16 | SMB | 26184 | 73401343.0
  2026-03-16 | Mid-Market | 4985 | 25940602.0
  2026-03-31 | VSB | 74106 | 89033206.0
  2026-03-31 | SMB | 27142 | 76096805.0
  2026-03-31 | Mid-Market | 5125 | 26267212.0

**ARR by Segment Trend** (variant: monthly_share)
  Description: Monthly ARR by segment as % of total — for "are we moving upmarket?" questions. Shows share of ARR, not absolute growth.
  snap_month | account_segment | team_count | arr_m | pct_of_arr
  2025-04-01 | Mid-Market | 4202 | 20.25 | 13.9
  2025-04-01 | Enterprise | 2767 | 9.18 | 6.3
  2025-05-01 | VSB | 51888 | 60.44 | 40.0
  2025-05-01 | Mid-Market | 4284 | 20.71 | 13.7
  2026-02-01 | SMB | 26218 | 73.63 | 38.2
  2026-02-01 | Mid-Market | 4995 | 25.63 | 13.3
  2025-04-01 | SMB | 21781 | 59.21 | 40.5
  2025-04-01 | VSB | 49466 | 57.46 | 39.3
  2026-02-01 | Enterprise | 3452 | 11.65 | 6.0
  2026-03-01 | VSB | 75205 | 91.88 | 44.3

**Credit Usage by Feature** (variant: daily_trend)
  Description: Daily credit consumption by feature type. Shows which product features are consuming credits over time.
  ds | credit_type | feature_type | teams_using | total_credits_used
  2026-03-29 | unified_lead_credit | rules_engine | 13 | 44
  2026-03-29 | unified_lead_credit | blacklist_check | 7 | 35
  2026-03-29 | web_search_record_credit | web_search_record | 7 | 21
  2026-03-29 | export_credit | pipedrive_push | 2 | 4
  2026-03-30 | unified_lead_credit | searcher_emails | 50884 | 6069129
  2026-03-30 | unified_lead_credit | direct_dial | 32692 | 4746563
  2026-03-30 | unified_lead_credit | api_access | 7691 | 2514690
  2026-03-30 | unified_lead_credit | power_up | 6727 | 2320070
  2026-03-30 | unified_lead_credit | waterfall_enrichment | 15392 | 1634323
  2026-03-30 | unified_lead_credit | linkedin_emails | 38909 | 550565

**Credit Utilization by Type** (variant: daily_snapshot)
  Description: Credit usage vs limits by credit type for a given date. Shows utilization rate per credit type across all teams.
  ds | credit_type | teams_using | total_credits_used | total_credit_limit | utilization_rate
  2026-04-13 | unified_lead_credit | 99679 | 21235806 | 53907735 | 0.393929
  2026-04-13 | web_search_record_credit | 8 | 236 | None | None
  2026-04-13 | power_up_credit | 94 | 56389 | None | None
  2026-04-13 | export_credit | 527 | 223935 | None | None
  2026-04-13 | ai_credit | 3773 | 577832 | None | None
  2026-04-13 | inbound_website_visitor_credit | 6613 | 56910 | None | None
  2026-04-13 | contact_website_visitor_credit | 83 | 12133 | None | None
  2026-04-13 | conversation_credit | 1456 | 116185 | None | None
  2026-04-13 | direct_dial_credit | 850 | 830972 | None | None
  2026-04-13 | email_credit | 1269 | 495002 | None | None

**Email Activity** (variant: daily_trend)
  Description: Daily email send volume and engagement by message type. Excludes downloaded_email (bulk exports with no engagement tracking).
  ds | message_type | messages_sent | opens | replies | bounces | open_rate | reply_rate
  2026-03-20 | extension_email | 120765 | 47477 | 35626 | 2993 | 0.403126 | 0.302500
  2026-03-20 | conversation_followup_email | 12 | 0 | 0 | 0 | 0.000000 | 0.000000
  2026-03-21 | outreach_automatic_email | 537258 | 13605 | 493 | 24634 | 0.026540 | 0.000962
  2026-03-22 | extension_email | 447 | 71 | 35 | 19 | 0.165888 | 0.081776
  2026-03-22 | outreach_manual_email | 2099 | 61 | 2 | 85 | 0.030409 | 0.000997
  2026-03-15 | outreach_automatic_email | 46319 | 974 | 13 | 5553 | 0.024007 | 0.000320
  2026-03-15 | extension_email | 469 | 62 | 28 | 13 | 0.135965 | 0.061404
  2026-04-11 | outreach_automatic_email | 268723 | 20202 | 574 | 7631 | 0.077375 | 0.002198
  2026-04-11 | outreach_manual_email | 48674 | 3465 | 125 | 2823 | 0.075571 | 0.002726
  2026-04-11 | extension_email | 10769 | 2450 | 1684 | 472 | 0.237933 | 0.163543

**Enrichment Activity** (variant: daily_trend)
  Description: Daily enrichment volume by source (API, CSV, CRM, waterfall).
  ds | enrichment_source | teams_enriching | total_enrichments
  2026-03-15 | waterfall | 7538 | 284044
  2026-03-16 | waterfall | 32376 | 1517637
  2026-03-20 | waterfall | 25640 | 1066869
  2026-03-26 | waterfall | 32400 | 1517411
  2026-03-27 | waterfall | 28518 | 1209253
  2026-03-24 | waterfall | 34080 | 1591123
  2026-03-25 | waterfall | 33582 | 1563570
  2026-04-12 | waterfall | 8628 | 272369
  2026-04-13 | waterfall | 35153 | 1553856
  2026-03-17 | waterfall | 33646 | 1610647

**Enterprise Paid Team Activity** (variant: daily_snapshot)
  Description: What % of Enterprise (paid_seat_limit > 20) paid teams are active in L7/L28. Answers "are our big accounts actually using the product?"
  enterprise_paid_teams | active_l7 | pct_active_l7 | active_l28 | pct_active_l28
  499 | 492 | 98.6 | 494 | 99.0

**Extension-Only Paid Teams** (variant: daily_snapshot)
  Description: Paid teams that use ONLY the Chrome extension — no other product features (no genpipe, no enrichment, no CRM, no win-close). Answers "how many paid teams are extension-only?"
  total_paid_teams | ext_only_teams | pct_ext_only | ext_only_arr_m
  114847 | 5534 | 4.8 | 7.05

**Feature WAT Snapshot** (variant: daily_snapshot)
  Description: Paid team counts by feature activity in last 7 days. Shows how many paid teams use each feature. Source: DIM_TEAMS_DAILY.
  paid_teams | active_l7 | sequence_teams | auto_email_teams | dialer_teams | workflow_teams | record_actioned_teams | extension_teams | win_close_teams | enrichment_teams
  114847 | 72695 | 19183 | 17531 | 2176 | 11903 | 56751 | 38779 | 4399 | 47712

**Feature WAT Trend** (variant: weekly)
  Description: Weekly trend of feature WAT percentages across paid teams. Shows feature adoption rates over time. Source: DIM_TEAMS_DAILY.
  week_start | paid_teams | sequence_pct | auto_email_pct | dialer_pct | workflow_pct | record_actioned_pct | extension_pct
  2026-01-19 | 94298 | 17.8 | 16.4 | 2.2 | 12.1 | 51.7 | 35.1
  2026-04-06 | 112561 | 16.7 | 15.8 | 1.8 | 11.3 | 47.4 | 33.2
  2026-03-02 | 101974 | 17.6 | 16.7 | 2.2 | 12.2 | 52.2 | 34.9
  2026-02-02 | 97516 | 18.4 | 17.1 | 2.3 | 12.6 | 52.9 | 36.4
  2026-01-26 | 95846 | 18.2 | 16.8 | 2.2 | 12.8 | 52.5 | 35.5
  2026-03-09 | 103561 | 17.4 | 16.4 | 2.1 | 12.3 | 51.9 | 34.3
  2026-03-16 | 105491 | 17.3 | 16.4 | 2.1 | 12.3 | 51.8 | 34.2
  2026-04-13 | 114847 | 16.7 | 15.3 | 1.9 | 10.4 | 49.4 | 33.8
  2026-02-16 | 99577 | 17.9 | 17.0 | 2.2 | 12.5 | 52.0 | 35.7
  2026-03-23 | 107525 | 17.3 | 16.4 | 2.0 | 11.9 | 50.5 | 34.0

**Free-to-Paid Conversion Rate** (variant: monthly_trend)
  Description: Monthly free-to-paid conversion rate — what % of new teams convert to paid within 3 months. Uses FIRST_PAID_DATE from DIM_TEAMS_DAILY.
  first_seen_month | total_teams | converted_3mo | conversion_rate_pct
  2025-04-01 | 133929 | 1713 | 1.3
  2025-05-01 | 213749 | 2882 | 1.3
  2025-07-01 | 301536 | 3144 | 1.0
  2025-09-01 | 362452 | 3390 | 0.9
  2025-06-01 | 316082 | 2980 | 0.9
  2025-12-01 | 271773 | 3610 | 1.3
  2025-08-01 | 294250 | 3126 | 1.1
  2025-11-01 | 315944 | 3645 | 1.2
  2025-10-01 | 342755 | 3750 | 1.1
  2026-01-01 | 134054 | 2747 | 2.0

**New Paid Teams by Month** (variant: trend)
  Description: Count of new paid teams per month — teams whose first paid date falls in that month. Uses FCT_DAILY_REVENUE (full history) with IS_PARENT_ACCOUNT filter.
  cohort_month | new_paid_teams
  2025-10-01 | 6077
  2026-01-01 | 11827
  2026-03-01 | 18012
  2026-02-01 | 13041
  2025-11-01 | 9123
  2025-12-01 | 7804
  2026-04-01 | 7878

**Paid Team Counts and ARR** (variant: daily_snapshot)
  Description: Current paid team and user counts from DIM_TEAMS_DAILY. Answers "how many paid teams and users do we have?"
  paid_teams | total_arr_m | avg_arr_per_team
  114847 | 209.41 | 1823.0

**Phone Call Activity** (variant: daily_trend)
  Description: Daily phone call volume, connect rates, and duration by status.
  ds | status | total_calls | unique_callers | total_duration_seconds | connect_rate
  2026-03-15 | failed | 36 | 12 | 22 | None
  2026-03-15 | completed | 205 | 68 | 12506 | 1.000000
  2026-03-15 | busy | 11 | 6 | 0 | None
  2026-03-15 | no-answer | 1338 | 185 | 0 | None
  2026-03-15 | None | 937 | 116 | 11270 | None
  2026-03-16 | queued | 1 | 1 | None | None
  2026-03-16 | None | 136417 | 8543 | 1904489 | None
  2026-03-16 | no_answer | 3 | 1 | 11 | None
  2026-03-16 | busy | 3893 | 1412 | 254 | None
  2026-03-16 | ringing | 18 | 16 | 7 | None

**Revenue by Self-Serve vs Rep-Driven** (variant: daily_snapshot)
  Description: ARR split between self-serve and rep-driven teams. Uses FCT_DAILY_REVENUE with parent-account filter. Note: flags can overlap (some teams are both).
  channel | paid_teams | total_arr_m | pct_of_total
  Pure Self-Serve | 106874 | 146.71 | 70.1
  Both | 1538 | 18.47 | 8.8
  Neither | 1192 | 1.32 | 0.6
  Pure Rep-Driven | 5270 | 42.92 | 20.5

**Sequence Participation Trend** (variant: weekly)
  Description: Weekly trend of sequence participation rate for paid teams. Answers "how is sequence participation trending?"
  week_start | paid_teams | sequence_teams | seq_participation_pct
  2026-01-26 | 95846 | 17462 | 18.2
  2026-01-19 | 94298 | 16793 | 17.8
  2026-02-02 | 97516 | 17918 | 18.4
  2026-03-30 | 110907 | 18946 | 17.1
  2026-03-09 | 103561 | 17983 | 17.4
  2026-04-06 | 112561 | 18762 | 16.7
  2026-04-13 | 114847 | 19183 | 16.7
  2026-02-16 | 99577 | 17853 | 17.9
  2026-02-09 | 98418 | 17969 | 18.3
  2026-03-02 | 101974 | 17908 | 17.6

**Support Volume** (variant: daily_trend)
  Description: Daily support conversation volume by type and AI participation.
  ds | conversation_type | ai_agent_participated | conversations | fcr_count | avg_csat
  2026-03-15 | email | False | 3 | 0 | None
  2026-03-15 | email | True | 64 | 1 | None
  2026-03-15 | conversation | True | 175 | 0 | 2.714285714286
  2026-03-15 | conversation | False | 79 | 1 | None
  2026-03-15 | admin_initiated | False | 16 | 0 | None
  2026-03-16 | conversation | True | 950 | 13 | 3.814393939394
  2026-03-16 | email | True | 235 | 9 | 2.666666666667
  2026-03-16 | conversation | False | 412 | 16 | 4.297297297297
  2026-03-16 | admin_initiated | False | 58 | 3 | None
  2026-03-16 | email | False | 46 | 2 | 1.000000000000

**Team Count by Edition** (variant: daily_snapshot)
  Description: Count of teams by Apollo edition (plan tier) for a given date.
  ds | apollo_edition | team_count | total_arr
  2026-04-13 | Professional | 44159 | 85125124.0
  2026-04-13 | Organization | 5455 | 61509940.0
  2026-04-13 | Elite | 47 | 78138.0
  2026-04-13 | Enterprise | 5 | 57204.0
  2026-04-13 | Free | 1 | 600.0
  2026-04-13 | Basic | 63741 | 59940024.0
  2026-04-13 | Custom | 101 | 1913815.0

**Teams by Billing Term** (variant: daily_snapshot)
  Description: Count of paid teams and ARR split by billing term (monthly, annually, quarterly, semi-annually). Point-in-time snapshot.
  ds | payment_term | team_count | total_arr
  2026-04-13 | annually | 23360 | 66435969.0
  2026-04-13 | monthly | 89290 | 129750644.0
  2026-04-13 | quarterly | 630 | 8354518.0
  2026-04-13 | semi-annually | 229 | 4083714.0

**Total ARR Snapshot** (variant: daily_snapshot)
  Description: Total paid team count and ARR as of a given date. Uses FCT_DAILY_REVENUE with parent-account filter for full date history.
  paid_teams | total_arr_m | avg_arr_per_team | median_arr_per_team
  114874 | 209.42 | 1823.0 | 828.0

**Win and Close WAT Trend** (variant: weekly)
  Description: Weekly trend of Win and Close use case active teams. Answers "what is Win and Close WAU?"
  week_start | paid_teams | win_close_teams | win_close_users | win_close_pct
  2026-01-19 | 94298 | 5020 | 9240 | 5.3
  2026-03-23 | 107525 | 4963 | 9445 | 4.6
  2026-04-06 | 112561 | 4530 | 8379 | 4.0
  2026-03-30 | 110907 | 5068 | 9542 | 4.6
  2026-03-09 | 103561 | 5063 | 9689 | 4.9
  2026-03-16 | 105491 | 5009 | 9620 | 4.7
  2026-02-09 | 98418 | 5176 | 9741 | 5.3
  2026-02-16 | 99577 | 5019 | 9302 | 5.0
  2026-01-26 | 95846 | 5089 | 9436 | 5.3
  2026-04-13 | 114847 | 4399 | 8047 | 3.8
<!-- /SECTION: metric-trends -->

<!-- SECTION: slack-pulse -->
## Slack Pulse — 2026-04-14

*Last 7 days | 5 channels | auto-generated by scripts/update_from_slack.py*


### #dept-analytics-updates

0 human messages in last 7 days (narrative synthesis skipped — no API key).


### #xfn-data-analytics

0 human messages in last 7 days (narrative synthesis skipped — no API key).


### #engineering

0 human messages in last 7 days (narrative synthesis skipped — no API key).


### #rnd-all

0 human messages in last 7 days (narrative synthesis skipped — no API key).


### #dept-analytics

0 human messages in last 7 days (narrative synthesis skipped — no API key).
<!-- /SECTION: slack-pulse -->
