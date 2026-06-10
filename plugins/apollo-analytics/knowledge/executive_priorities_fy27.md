# Executive Priorities FY27 — What Needs to Be Measured

Source: FY27 AOP, CKO: Ignite to Win sessions, FY27 Goals Repository (CBRs #8–#11), Matt Curl comms, Slack channels (#internal-communications, #product-ship-room, #xfn-ai-assistant, #proj-context-graph, #growth-conversion-pd, #proj-ai-content-center). Compiled 2026-03-06, updated with OKR targets.

## Company Snapshot

- **ARR target:** ~$300M (FY27 plan)
- **Historical trajectory:** $6M → $130M over 5 years (~70% CAGR)
- **Revenue per employee target:** $300k
- **Operating model shift:** PLG point solution → multi-solution platform via hybrid motion (PLG + human-led sales)
- **Framework:** Horizons (H1 core / H2 emerging / H3 exploratory), teams locked per quarter

______________________________________________________________________

## Strategic Pillar 1: NRR & Retention

**Why it matters:** T4 customers = 52% of ARR but 75% of total churn. Retention is the single most impactful lever.

### What needs to be measured

| Metric | Current | Target | Cadence |
|---|---|---|---|
| NRR by segment (T1/T2/T3/T4) | ? | Improve | Monthly |
| M3 NRR for new core cohorts | 82% | 90% (CBR #10) | Monthly cohort |
| Churn rate by segment | T4 dominates | Reduce | Monthly |
| Churn reason decomposition | Not granular | Granular tracking | Per-event |
| MM Org Plan retention | 55% | 60% (5pt lift) | Quarterly |
| Active days per month (daily habit) | Varies | 26+ days | Daily grain |
| Avg use cases per Paid WAT | 1.18 | 1.33 (CBR #10) | Monthly |
| Credit utilization rate | Varies | Track distribution | Daily grain |
| Seat expansion (1-2 seat → 3+) | 94% start at 1 seat | Increase multi-seat | Monthly |
| Month-to-annual upgrade rate | ? | Increase | Monthly |

**OKR detail (CBR #10 — Multi-Product & Retention):**

- "Multi-product" = teams using 2+ Apollo use cases (sequences + enrichment, etc.)
- M3 NRR measures retention 3 months after acquisition — cohort-based, not aggregate
- Growth accounting framework: need "NRR annualized actual" metric for tracking real vs modeled retention

### Data Sparring insight (2026-03-06)

Daily active days is the #1 retention signal — 26+ days = 76% retention vs \<40% at 1-5 days. Proposed soft-cap daily credit limit experiment to drive daily engagement. See `domain/credit_utilization_and_retention.md`.

### Relevant tables

- `AGG_TEAM_CREDITS` — Source for credit metrics (usage and limits by type/feature)
- `LU_TEAMS` — Team metadata, segment, plan
- `FCT_EVENTS` / Amplitude — Product engagement events, active days

______________________________________________________________________

## Strategic Pillar 2: AI-Native GTM

**Why it matters:** Matt Curl: "The clearest expression of what Apollo is supposed to do." AI Assistant moved to GA. This is Apollo's differentiation bet.

### Key product areas

**AI Assistant (GA)**

- SDR workflow: 1 hour → 10-15 minutes for sequence building
- OKR targets (CBR #9): 15K WAUs at 20% W4 retention
- Tracking: AI WAT (weekly active teams), multi-tool call rates, first-time use conversion
- First-time tool call improving but multi-tool call lagging — "people are still not engaging deeper"
- AI credit consumption recalibration needed — behavioral baseline not established yet

**Context Center 3.0**

- ~1-4% adoption of AI WAT teams so far (early stage)
- 644 teams approved but show zero AI WAT activity (setup without use)
- Scrape failure rate improved: 37% (v2) → 26% (v3)
- 24hr review-to-approval conversion: 51.8%

**Context Graph (POC)**

- Goal: AI "next best action" recommendations using historical sales precedents
- Signal prioritization: Bombora intent, website visitors, job changes, funding events, news events
- OKR: CC 3.0 to 100% by 3/4, Context Graph baseline delivered
- Missing data in Snowflake: funding events (partial), news events (missing)

**Claude/MCP Connector**

- GA launch with Anthropic partnership
- Customer-facing Apollo MCP server
- MCP usage trackable via `FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` filtered by `user_agent = 'Apollo-MCP/1.0'`

### What needs to be measured

| Metric | Notes |
|---|---|
| AI WAT (weekly active teams) | By segment, paid vs free |
| AI Assistant multi-tool call rate | % of sessions using 2+ tools |
| CC v3 adoption rate | By segment (paid core/non-core, free) |
| CC v3 scrape failure rate | 26% baseline, track improvement |
| CC v3 review-to-approval conversion | 51.8% baseline |
| Context Graph signal coverage | Which signals have Snowflake data |
| MCP connector active teams | Via HTTP request logs |
| AI credit consumption | AI credits excluded from unified pool |

### Relevant tables

- `FCT_EVENTS` / Amplitude — AI feature events
- `FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` — MCP usage
- `AGG_TEAM_CREDITS` — AI credit types (ai_email, ai_credit)
- Context Graph signals: Bombora, website visitors, job changes (various raw tables)

______________________________________________________________________

## Strategic Pillar 3: Inbound Product

**Why it matters:** New revenue line. $4M base / $10M stretch target. 3-year opportunity: $45M ARR. Funded with 7-8 engineers + tiger team.

### Financial model

| Metric | Value |
|---|---|
| Current pricing | $149/team/mo ($119 annual) |
| H2 pricing (after maturity) | $499/team/mo ($399 annual) |
| Self-serve target | $2.4M ARR from 666 teams (0.6% adoption) |
| Rep-driven target | $1.7M ARR from 612 teams (4.6% adoption) |
| Q1 revenue target | >$1.5M inbound add-on revenue |
| Early traction | $300k+ in first quarter, 170 teams (88% SMB/VSMB, 12% MM+) |
| Exit ARPT | $3.3k |

### Product themes & ARR targets

1. Supercharged add-on — $1.5M
1. Simple onboarding — $500k
1. Inbound+Outbound orchestration — $500k
1. Replace Chili Piper for MM — $1M
1. Foray into MAP (marketing automation) — $500k (incubate Q3, launch Q4)

### What needs to be measured

| Metric | Current | Target |
|---|---|---|
| Inbound add-on adoption rate | ? | 0.6% self-serve, 4.6% rep-driven |
| Q1 inbound add-on revenue pacing | ~$1.2M | $1.5M (CBR #11) |
| New user inbound activation | 19% | 25% |
| Website visitor WATs (forms) | ? | 50+ |
| Website visitor WATs (contact-level) | ? | 250+ |
| Workflows launched from website visitors | 0.9% | 2% |
| Inbound pipeline attribution | ? | Meetings booked, SLA health |
| ARPT trend | $3.3k exit | Track as pricing increases |
| Contact-level website visitor GA | Pre-GA | GA target April 8 (CBR #11) |

**OKR detail (CBR #11 — Inbound):**

- Q1 pacing ~$1.2M vs $1.5M OKR goal — tracking behind, may need acceleration
- Contact-level website visitors (not just form submissions) is the key unlock for volume
- Website visitor WATs (contact-level) target 250+ is aggressive; forms-only target 50+ is conservative

### Relevant tables

- Website visitor events (needs identification)
- Inbound form submission data
- Workflow execution tables
- Revenue / billing tables for ARPT

______________________________________________________________________

## Strategic Pillar 4: Upmarket Readiness

**Why it matters:** MM+Ent rep-driven ARR growing 64% YoY ($13.5M → $21.8M). New logo targets: 488 → 680 teams (+39%).

### What needs to be measured

| Metric | Current | Target |
|---|---|---|
| MM+Ent rep-driven ARR | $13.5M | $21.8M (+64%) |
| MM+Ent new logos | 488 | 680 teams (+39%) |
| ACV at acquisition | $9k | $11k (+23%) |
| S1 → S2 conversion | 20% | Optimize |
| MM Org Plan retention | 55% | 60% |
| PQL/PQA volume and conversion to S1 | ? | Track |
| Sales coverage model | ? | By segment |

### Relevant tables

- SFDC opportunity data
- `LU_TEAMS` — segment, plan type
- Pipeline / stage change events
- PQL/PQA scoring tables

______________________________________________________________________

## Strategic Pillar 5: Pricing & Packaging

**Why it matters:** P&P delivered $16M+ incremental ARR in FY26. FY27 continuing with $10M+ from existing initiatives + new experiments.

### Active experiments and initiatives

- **AB59 higher price variant** — Testing price sensitivity on basic plan
- **Expiring credits nudge** — Meaningful gains for free users during trials
- **Trial preview badges** — Paid feature previews to drive engagement
- **Seat upgrade fraud fix** — $1 exploit for 1000 seats discovered, being patched
- **Soft-cap daily credit limit** — Proposed (Data Sparring), Karthik owns A/B test

### What needs to be measured

| Metric | Notes |
|---|---|
| FTP conversion at Week 2 | 4.0% current, 4.5% target |
| Direct-to-annual plan share | % starting on annual vs monthly |
| Price experiment lift (AB59) | Conversion and revenue impact |
| Credit limit hit rate | % of teams hitting limits (price-insensitive signal) |
| Seat discount ROI | 9-10% retention lift, but unit economics matter |
| Feature gate reach and conversion | Which gates drive upgrades |

### Relevant tables

- `AGG_TEAM_CREDITS` — Credit usage and limits
- Amplitude experiment data
- Billing / subscription tables
- `FCT_EVENTS` — Feature gate impressions

______________________________________________________________________

## Strategic Pillar 6: Waterfall Enrichment & Data Quality

**Why it matters:** Apollo positioning as "data provider to intelligence engine." Data quality is table stakes for upmarket.

### What needs to be measured

| Metric | Notes |
|---|---|
| Waterfall enrichment hit rates | Email and phone, by provider |
| 3P enrichment coverage | % of contacts with 3P data |
| Data freshness / accuracy | Bounce rates, invalid numbers |
| Enrichment by channel | CSV, API, in-app, AI Sheets |

### Relevant tables

- Waterfall enrichment event tables
- Contact/People enrichment results
- `FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` — API enrichment calls

______________________________________________________________________

## Onboarding & Activation (Cross-Cutting Theme)

**Why it matters:** Onboarding is a prerequisite for multi-product adoption and retention. CBR #8 tracks activation specifically.

| Metric | Current | Target |
|---|---|---|
| SMB+ Habit "Record Actioned" in first 14 days | 12% | 17% (CBR #8) |
| FTP conversion at Week 2 | 4.0% | 4.5% |
| First-time AI tool call conversion | Improving | Track by segment |

**Data need:** "Record Actioned" definition needs clarification — what events constitute actioning a record? Likely combination of email send, call, task completion on a contact/lead.

______________________________________________________________________

## Key Data & Analytics Gaps (from OKR Review)

These are measurement gaps surfaced by the Goals Repository that Analytics needs to address:

| Gap | Context | Priority |
|---|---|---|
| R&D retention metric definition | Engineering uses different retention definition than GTM — need alignment | High |
| NRR annualized "actual" for growth accounting | Currently modeled, not measured from real cohort data | High |
| Cohort-based vs aggregate retention | Executive reporting uses aggregate; OKRs use cohort-based (M3 NRR). Need both. | High |
| AI credit consumption behavioral baseline | No baseline for what "normal" AI credit usage looks like — needed before recalibration | Medium |
| "Record Actioned" event definition | Onboarding OKR depends on this; unclear what events qualify | Medium |
| Inbound pipeline attribution end-to-end | Meeting booked → opportunity → revenue attribution for inbound channel | Medium |

______________________________________________________________________

## What's Being Defunded / Descoped

| Area | Status |
|---|---|
| VSB from comp plan | Deflecting to Customer Advocacy |
| Field Marketing | Wound down in FY26 |
| Heavy international GTM | Deferred; lightweight R&D only |
| Legacy onboarding team | Reduced, being rebuilt |
| Non-brand SEO | Declining due to AI Overviews — strategic pivot needed |

______________________________________________________________________

## People & Operations Metrics

| Metric | Target |
|---|---|
| Employee engagement score | 80% by end of FY27 |
| Regrettable attrition | \<8% |
| Overall attrition | \<25% by end of FY27 |
| Cost of hire | $9k/hire |
| People team cost as % of ARR | 3.2% |

______________________________________________________________________

## Comprehensive Data Availability Mapping (Updated 2026-03-06)

Source: Snowflake schema exploration + leadgenie monorepo model analysis.

**IMPORTANT — Trust hierarchy for this analysis:**

1. **ANALYTICS_DATAPLATFORM** — Raw Mongo mirrors. Trustworthy as source-of-record.
1. **RAW_MONGO_DB.RAW_COLLECTIONS** — Raw Mongo exports. Trustworthy.
1. **Stripe / Salesforce staging tables** — Fivetran-synced. Trustworthy for billing/CRM.
1. **ANALYTICS schema** — Mixed quality. Some tables authoritative, others legacy. Verify before depending.
1. **ANALYTICS_DATASCIENCE** — Data science team's derived tables. **Data quality is suspect.** Useful as a *reference for what should be measured* and what event types exist, but we must trace upstream to raw sources for anything we depend on. Do NOT treat these as final data assets.

### Pillar 1: NRR & Retention

**What needs to be measured:** NRR by segment (T1-T4), M3 NRR for cohorts, churn rate and reason decomposition, expansion/contraction revenue, active days, multi-product usage, time-to-value.

**Trusted raw data available:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| Revenue (daily/weekly/monthly) | `FCT_DAILY_REVENUE` (207M), `FCT_WEEKLY_REVENUE` (30M), `FCT_MONTHLY_REVENUE` (7.4M) | ANALYTICS | Core revenue tables, likely Stripe-sourced |
| Revenue from Mongo | `FCT_MONGO_DAILY_REVENUE` (32M), `FCT_MONGO_MONTHLY_REVENUE` (1.2M) | ANALYTICS | Alternative source, verify consistency with above |
| NRR (quarterly, by account) | `FCT_ACCOUNT_QUARTERLY_NRR` (983K) | ANALYTICS | Verify methodology — is this actual or modeled? |
| NRR (parent account, weekly) | `FCT_PARENT_ACCOUNT_NRR` (153K), `FCT_WEEKLY_PARENT_ACCOUNT_NRR` (644K) | ANALYTICS | Verify vs cohort-based M3 NRR OKR definition |
| Expansion revenue | `INT_TEAM_ARR_EXPANSION` (313K) | ANALYTICS | Needs audit — how are expansion/contraction defined? |
| MRR by opportunity | `FCT_MRR_BY_OPPORTUNITY_AND_ACCOUNT_DAILY` (2.8M) | ANALYTICS | Links Mongo to Salesforce revenue |
| Stripe subscriptions | `STG_STRIPE__SUBSCRIPTION` (997K) | ANALYTICS | Raw Stripe data, trustworthy |
| Stripe payments | `STG_STRIPE__PAYMENT_INTENT` (3.3M) | ANALYTICS | Raw Stripe data, trustworthy |
| Billing periods | `INT_TEAM_BILLING_PERIODS` (20M) | ANALYTICS | Verify construction methodology |
| Churn accounts (SFDC) | `FCT_SALESFORCE_CHURN_ACCOUNTS` (108K) | ANALYTICS | Salesforce-sourced, verify churn definition |
| Churn tickets (Zendesk) | `FCT_ZENDESK_CHURN_TICKETS` (101K) | ANALYTICS | Good for churn *reason* signal |
| Churn prediction models | `FCT_ML_PREDICTIONS_PAID_CHURN_12W` (6.4M), `FCT_ML_PREDICTIONS_PAID_CHURN_8W` (6.5M) | ANALYTICS | ML output — treat as features, not ground truth |
| Team metadata | `DIM_MONGO_TEAMS` | ANALYTICS_DATAPLATFORM | Raw Mongo, includes segment, plan, created_at |
| User metadata | `DIM_MONGO_USERS` | ANALYTICS_DATAPLATFORM | Raw Mongo |
| Credit usage (raw events) | `FCT_MONGO_CREDIT_USAGES`, `FCT_MONGO_CREDIT_USAGE_DETAILS` | ANALYTICS_DATAPLATFORM | Raw Mongo, trustworthy |
| Credit aggregation | `AGG_TEAM_CREDITS` | ANALYTICS | We own this, verified |
| Plan edition changes | `FCT_ACCOUNT_EDITION_CHANGES` | ANALYTICS | Verify: is this Stripe-sourced or derived? |

**DS reference tables (quality suspect, use for metric definitions only):**
`PRODUCT_METRICS_NRR`, `PRODUCT_METRICS_ARR`, `PRODUCT_METRICS_CONVERSION`, `PRODUCT_METRICS_ACQUISITION`, `DIM_ACTIVE_TEAMS_DAILY`, `FEATURE_RETENTION_TEAM_COHORTS_WEEKLY`, `TEAM_DAILY_SOLUTION_USAGE`, `WEEKLY_TEAM_SIGNALS`. These tell us *what the DS team thought was important to measure* and can guide our own pipeline design.

**Gaps:**

- Churn *reason* taxonomy — Zendesk tickets provide some signal, and `CANCELLATION_SURVEYS` exists in RAW_MONGO_DB (leadgenie `packs/billing/app/models/cancellation_survey.rb` captures structured churn reasons). Needs investigation: what fields are captured, how complete is coverage, and is it synced to ANALYTICS_DATAPLATFORM?
- "Record Actioned" event definition — undefined, critical for onboarding OKR
- R&D vs GTM retention definition alignment — still unresolved
- Cohort-based M3 NRR — verify if `FCT_ACCOUNT_QUARTERLY_NRR` implements this or a different methodology

______________________________________________________________________

### Pillar 2: AI-Native GTM

**What needs to be measured:** AI WAT (weekly active teams), AI assistant multi-tool call rate, CC v3 adoption/scrape failure rate, AI-generated content attribution, AI → outcome correlation, MCP connector usage.

**Trusted raw data available:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| AI Assistant threads | `DIM_MONGO_ASSISTANT_THREADS` | ANALYTICS_DATAPLATFORM | Raw Mongo mirror — thread-level |
| AI Assistant messages | `FCT_MONGO_ASSISTANT_THREAD_MESSAGES` | ANALYTICS_DATAPLATFORM | Raw Mongo mirror — message-level |
| AI credit usage | `FCT_MONGO_CREDIT_USAGES` filtered by credit type | ANALYTICS_DATAPLATFORM | Filter to ai_email, ai_credit types |
| MCP connector usage | `FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` filtered by `user_agent = 'Apollo-MCP/1.0'` | ANALYTICS_DATAPLATFORM | Real-time view |

**DS reference tables (quality suspect, but show what event types exist):**
`TEAM_AI_PLATFORM_DAILY` tracks 8 AI feature categories (filtering, scoring, recommendations, power_ups, messaging, conversational_insights, support, assistant) with L7/L14/L28 windows. `USER_AI_PLATFORM_ACTIONS_DAILY` has 23 distinct AI action types including granular email AI content attribution (auto vs manual, by content component: subject_line, snippet_opener, ps_line, full_email). `AI_ASSISTANT_MESSAGES` (12.8M) provides message-level data. These tables show the *types of AI measurement* the DS team built — we'd need to trace each back to its Amplitude/Mongo source events to build trusted versions.

**Raw source for AI events:** Likely Amplitude events flowing through `INT_AMPLITUDE_EVENTS_DAILY` (127M, ANALYTICS_DATASCIENCE). Need to identify the specific Amplitude event names that correspond to each AI action type, then build from those raw events.

**Gaps:**

- AI → outcome correlation — no join between AI-generated emails and reply/meeting rates. Would need to tag emails in `FCT_MONGO_EMAILER_MESSAGES` with AI generation source, then join to email outcome events.
- Context Center v3 scrape failure rate — likely in Amplitude, not yet surfaced
- Context Graph signal coverage — funding events (partial), news events (DIM_MONGO_ORGANIZATION_INTENT_NEWS exists with 609M rows)
- AI credit consumption behavioral baseline — needs to be established from `FCT_MONGO_CREDIT_USAGES`

______________________________________________________________________

### Pillar 3: Inbound Product

**What needs to be measured:** Inbound add-on adoption, website visitor WATs (forms + contact-level), activation rate, conversion funnel, inbound revenue attribution, ARPT.

**Trusted raw data available:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| Inbound router config | `LU_MONGO_MEETINGS_INBOUND_ROUTER_ROUTING_FORM_SETTINGS` (97K) | ANALYTICS_DATAPLATFORM | Raw Mongo — who has inbound router configured |
| Intent events | `DIM_MONGO_INTENT_EVENTS` (8.5B) | ANALYTICS_DATAPLATFORM | Raw Mongo — 1P intent signals |
| Intent signal accounts | `FCT_MONGO_INTENT_SIGNAL_ACCOUNTS` (149M) | ANALYTICS_DATAPLATFORM | Account-level intent signals |
| Intent daily aggregates | `FCT_MONGO_ORGANIZATION_TEAM_INTENT_DAILY_AGGREGATES` (429M) | ANALYTICS_DATAPLATFORM | Team × org daily intent |
| Intent news | `DIM_MONGO_ORGANIZATION_INTENT_NEWS` (609M) | ANALYTICS_DATAPLATFORM | News-based intent |
| HubSpot form submissions | `DIM_HUBSPOT_FORM_SUBMISSIONS` (1.2M) | ANALYTICS | Apollo's own inbound (marketing) |

**DS reference tables (quality suspect, but show what's tracked):**
`USER_INBOUND_ACTIONS_DAILY` (585K) tracks: website_visitors_filter_applied_in_search, website_visitors_on_hover_viewed, inbound_router_form_enriched, standalone_form_enriched, meeting_booked_via_apollo_scheduler. Categories: inbound_website_visitors, inbound_form_enrichment, inbound_router. Small volume (585K total) confirms product is early-stage.

**Leadgenie models (upstream source tracing for inbound):**

- `packs/1p_intent/app/models/website_visits/website_visitor.rb` — Has `new_reveal` (boolean), `total_visits`, `unique_sessions` fields. This is the contact-level identification model.
- `packs/1p_intent/app/models/website_visits/intent_event.rb` — Raw events with `contact_identified` and `deanonymised` boolean fields. These are the signals that power contact-level website visitor identification.
- `packs/plays/app/models/form_enrichment_daily_stat.rb` — Daily stats for inbound form enrichment conversion funnel.
- `INTENT_EVENTS` collection exists in RAW_MONGO_DB — raw intent event data is flowing to Snowflake.

**Gaps (SIGNIFICANT — this is the weakest pillar):**

1. **Contact-level website visitor identification** — Product feature targeting GA April 8 (CBR #11). Leadgenie models exist (`website_visitor.rb` with `new_reveal`, `intent_event.rb` with `contact_identified`/`deanonymised`). `INTENT_EVENTS` exists in RAW_MONGO_DB but need to verify if contact-level identification fields are populated pre-GA. `DIM_MONGO_INTENT_EVENTS` (8.5B rows) in ANALYTICS_DATAPLATFORM may already have these fields — needs column-level investigation.
1. **Inbound conversion funnel** — No visitor → identified → engaged → meeting → opportunity → revenue pipeline. `FormEnrichmentDailyStat` model in leadgenie tracks daily form enrichment stats — check if this surfaces in Snowflake.
1. **Inbound revenue attribution** — Cannot tie inbound to revenue end-to-end
1. **Inbound ARPT tracking** — Need join of inbound feature usage to Stripe billing
1. **Contact-level website visitor WATs target (250+)** — Need a table to track this metric against OKR

______________________________________________________________________

### Pillar 4: Upmarket Readiness

**What needs to be measured:** MM+Ent rep-driven ARR, new logos, ACV at acquisition, S1→S2 conversion, MM Org Plan retention, PQL/PQA volume, SSO/SCIM adoption, RBAC usage.

**Trusted raw data available:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| RBAC/Permission sets | `DIM_MONGO_PERMISSION_SETS` (13.6M) | ANALYTICS_DATAPLATFORM | Raw Mongo — 40+ permission booleans, TYPE_CD, per team |
| Enterprise deals/ACV | `DIM_SALESFORCE_OPPORTUNITIES` | ANALYTICS | SFDC-sourced |
| Account metadata | `DIM_SALESFORCE_ACCOUNTS` | ANALYTICS | SFDC-sourced, includes segment |
| Team segment/plan | `DIM_MONGO_TEAMS` | ANALYTICS_DATAPLATFORM | Raw Mongo — plan, created_at |
| IP-org association | `DIM_IP_ORG_ASSOCIATION` (69M) | ANALYTICS_DATAPLATFORM | Enterprise identification |

**Permission set fields available (40+):** CAN_ACCESS_BILLING, CAN_ACCESS_CREDIT_USAGE, CAN_INVITE_USER, CAN_MANAGE_PERMISSION_SETS, CAN_MANAGE_GROUPS, CAN_MANAGE_INBOUND_ROUTER, CAN_EDIT_OR_DELETE_USER, IS_SUPERUSER, TYPE_CD, CAN_ADD_SEQUENCES, CAN_ADD_PLAYBOOKS, CAN_EDIT_SALESFORCE_SETTINGS, CAN_MANAGE_TABLE_LAYOUTS, etc.

**Additional enterprise readiness data:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| MFA adoption | `DIM_MONGO_MFA_CONFIGS` (31K rows) | ANALYTICS_DATAPLATFORM | Raw Mongo — which teams have MFA enabled |
| Security config (real-time) | `DIM_MONGO_SECURITY_CONFIGS_RT_VW` | ANALYTICS_DATAPLATFORM | Real-time security settings view |

**Gaps:**

1. **SSO/SCIM adoption** — **CONFIRMED GAP.** Leadgenie `packs/iam/app/models/sso_config.rb` exists with `active` boolean, `idp` enum (gmail, ms_exchange, okta, entra_id), and `scim_api_key` field. However, `SSO_CONFIGS` is NOT synced to any Snowflake table — no `DIM_MONGO_SSO_CONFIGS` exists. **Action needed:** Request ANALYTICS_DATAPLATFORM team add this collection to the Mongo mirror pipeline. Until then, MFA adoption via `DIM_MONGO_MFA_CONFIGS` (31K rows) is the closest enterprise security adoption signal.
1. **PQL/PQA scoring** — No dedicated table found. May live in Salesforce or an external system (e.g., MadKudu). Check with GTM analytics.
1. **Enterprise feature usage aggregation** — Raw permission data exists but no "enterprise readiness score" or adoption aggregate. MFA (31K teams) + permission sets (13.6M) could be combined into a composite signal.

______________________________________________________________________

### Pillar 5: Pricing & Packaging

**What needs to be measured:** Credit utilization by plan/type, overage events, plan upgrade/downgrade, FTP conversion, experiment results, seat dynamics.

**Trusted raw data available:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| Credit usage (raw events) | `FCT_MONGO_CREDIT_USAGES`, `FCT_MONGO_CREDIT_USAGE_DETAILS` | ANALYTICS_DATAPLATFORM | Raw Mongo — event-level |
| Credit aggregation | `AGG_TEAM_CREDITS` | ANALYTICS | We own this, verified. (GOLD_TEAM_CREDITS deprecated 2026-04-15) |
| Credit limits | `LU_CREDIT_QUOTA` → `STG_CREDIT_QUOTA` | ANALYTICS_DATAPLATFORM | Raw Mongo |
| Plan edition changes | `FCT_ACCOUNT_EDITION_CHANGES` | ANALYTICS | Upgrade/downgrade events |
| Stripe subscriptions | `STG_STRIPE__SUBSCRIPTION` (997K) | ANALYTICS | Raw Stripe, trustworthy |
| Stripe payments | `STG_STRIPE__PAYMENT_INTENT` (3.3M) | ANALYTICS | Raw Stripe, trustworthy |
| Team product info | `DIM_MONGO_TEAMS_PRODUCT_INFO`, `INT_TEAM_PRODUCT_INFO_CLEANED` | ANALYTICS_DATAPLATFORM / ANALYTICS | Plan tier, features |
| Credit enum mappings | `LU_ENUM` | ANALYTICS_DATAPLATFORM | Credit type/source/status enums |

**DS reference tables:** `PRODUCT_METRICS_CONVERSION` (FTP conversion metrics), `INT_TEAM_CONTROL_AND_TREATMENT` (experiment allocations — team-level, 4 columns). These define the measurement patterns but need upstream verification.

> **Experiment platform (2026-03-19):** Statsig is **deprecated**. Current platform is **Amplitude**. `DIM_USER_SPLIT_TEST_ALLOCATIONS` and `EXPORT_TEAMS_DAILY_STATSIG` are both deprecated. Use `INT_TEAM_CONTROL_AND_TREATMENT` for Snowflake-side experiment joins. For full results, go to Amplitude directly. User-level assignment table TBC — ask Andrew Green or Pubudu.

**This pillar is well-covered by trusted sources.** Our own AGG_TEAM_CREDITS work directly supports it.

______________________________________________________________________

### Pillar 6: Data Quality & Waterfall Enrichment

**What needs to be measured:** Waterfall hit rates by provider/field, enrichment match rates, bounce rates, phone connect rates, data freshness, deliverability.

**Trusted raw data available:**

| Measurement | Trusted Source Table(s) | Schema | Notes |
|---|---|---|---|
| Waterfall step results | `DIM_MONGO_WATERFALL_STEP_RESULTS` (658M) | ANALYTICS_DATAPLATFORM | Raw Mongo — per provider, per field, status, validation_status, credit usage |
| Field enrichment statuses | `DIM_MONGO_FIELD_ENRICHMENT_STATUSES` (27.4B) | ANALYTICS_DATAPLATFORM | Raw Mongo — enriched boolean, source, old/new values, internal_field |
| Waterfall request stats | `DIM_MONGO_WATERFALL_ENRICHMENT_REQUEST_STATS` (54M) | ANALYTICS_DATAPLATFORM | Raw Mongo |
| Waterfall templates | `DIM_MONGO_WATERFALL_ENRICHMENT_TEMPLATES` (1.1M) | ANALYTICS_DATAPLATFORM | Config data |
| CSV enrichment jobs | `DIM_MONGO_CSV_ENRICHMENT_JOBS` (2.6M) | ANALYTICS_DATAPLATFORM | Raw Mongo |
| Email bounce events | `DIM_MONGO_BOUNCE_EMAIL_ADDRESS_EVENTS` (21.7M) | ANALYTICS_DATAPLATFORM | Raw Mongo |
| Email bounce data | `INT_MONGO_EMAIL_BOUNCE_DATA` (2.1B) | ANALYTICS_DATAPLATFORM | Intermediate, verify source |
| Bounce rate aggregates | `AGG_EMAILER_CAMPAIGN_BOUNCE_RATE_MONTHLY` (2.9M), `AGG_EMAIL_BOUNCE_RATE_BY_ACC_TYPE_MONTHLY` | ANALYTICS_DATAPLATFORM | Pre-built aggregates, verify methodology |
| Deliverability scores | `DIM_MONGO_DELIVERABILITY_SCORES_RT_VW` | ANALYTICS_DATAPLATFORM | Real-time view |
| DNC information | `DIM_MONGO_DNC_INFORMATIONS` (20M) | ANALYTICS_DATAPLATFORM | Raw Mongo |

**This pillar has the deepest raw data coverage.** 27.4B field enrichment status rows give field-level enrichment tracking. 658M waterfall step results give per-provider hit rates. All in ANALYTICS_DATAPLATFORM (trusted).

______________________________________________________________________

## Revised Gap Analysis (Post-Investigation)

### Previously identified gaps — status update:

| # | Original Gap | Status | Notes |
|---|---|---|---|
| 1 | No unified AI feature usage tracking | **RAW DATA EXISTS** — `DIM_MONGO_ASSISTANT_THREADS` + Amplitude events. DS team built derived tables (`TEAM_AI_PLATFORM_DAILY`) showing 23 action types. We need to build from raw sources. |
| 2 | No enrichment quality metrics | **RAW DATA EXISTS** — `DIM_MONGO_WATERFALL_STEP_RESULTS` (658M) + `DIM_MONGO_FIELD_ENRICHMENT_STATUSES` (27B) in ANALYTICS_DATAPLATFORM. Fully trustworthy. |
| 3 | No expansion/contraction revenue split | **PARTIALLY EXISTS** — `INT_TEAM_ARR_EXPANSION` (313K) in ANALYTICS schema. Need to verify methodology and trace to Stripe/SFDC sources. |
| 4 | No AI-generated content attribution | **RAW EVENTS EXIST** — DS tables show the Amplitude event types exist. Need to trace to raw Amplitude/Mongo sources. |

### TRUE remaining gaps:

| # | Gap | Pillar | Severity | What We Need | Upstream Source to Investigate |
|---|---|---|---|---|---|
| 1 | **Contact-level website visitor identification** | Inbound | HIGH | Product GA April 8. No analytics table yet. | leadgenie `packs/1p_intent/` models — what Mongo collection will store identified visitors? |
| 2 | **Inbound conversion funnel** | Inbound | HIGH | visitor → identified → engaged → meeting → revenue | Need to join: intent events → router form settings → meetings → SFDC opportunities |
| 3 | **SSO/SCIM adoption tracking** | Upmarket | MEDIUM | Which teams have SSO/SCIM enabled | **CONFIRMED:** `sso_config.rb` exists in leadgenie (active, idp enum, scim_api_key) but NOT synced to Snowflake. Need to request Mongo mirror. MFA available via `DIM_MONGO_MFA_CONFIGS` (31K rows) as interim signal. |
| 4 | **AI → outcome correlation** | AI-Native GTM | MEDIUM | AI-generated email → reply/meeting rates | Need to join Amplitude AI attribution events to `FCT_MONGO_EMAILER_MESSAGES` outcome fields |
| 5 | **Churn reason decomposition** | NRR & Retention | MEDIUM | Structured churn reason codes | `FCT_ZENDESK_CHURN_TICKETS` (101K) + **NEW:** `CANCELLATION_SURVEYS` in RAW_MONGO_DB (from `cancellation_survey.rb`). Investigate survey fields and coverage. |
| 6 | **PQL/PQA scoring** | Upmarket | MEDIUM | Scoring table for S1→S2 conversion | Check Salesforce fields or external scoring system |
| 7 | **Context Center v3 metrics** | AI-Native GTM | LOW | Scrape failure rate, review-to-approval | Likely in Amplitude events |
| 8 | **"Record Actioned" definition** | Onboarding | LOW | Agreed event definition for OKR | Needs cross-functional alignment, not a data problem |
| 9 | **NRR methodology verification** | NRR & Retention | MEDIUM | Verify `FCT_ACCOUNT_QUARTERLY_NRR` implements M3 cohort NRR per OKR definition | Trace upstream to Stripe subscription changes |

______________________________________________________________________

## Leadgenie Monorepo: Data Model Mapping

The leadgenie repo at `~/workspace/leadgenie` uses a packwerk architecture with models distributed across packs. Key packs by pillar:

| Pack | Path | Pillar(s) |
|---|---|---|
| `billing` | `packs/billing/app/models/` | Pricing & Packaging, NRR |
| `ai` | `packs/ai/app/models/` | AI-Native GTM |
| `enrichment` | `packs/enrichment/app/models/` | Data Quality |
| `waterfall` | `packs/waterfall/app/models/` | Data Quality |
| `data_quality` | `packs/data_quality/app/models/` | Data Quality |
| `1p_intent` | `packs/1p_intent/app/models/` | Inbound (website visitors, intent) |
| `conversations` | `packs/conversations/app/models/` | AI-Native GTM, Inbound |
| `iam` | `packs/iam/app/models/` | Upmarket (SSO, SCIM, RBAC) |
| `onboarding` | `packs/onboarding/app/models/` | NRR & Retention (activation) |
| `plays` | `packs/plays/app/models/` | AI-Native GTM (automation) |
| `recommendations` | `packs/recommendations/app/models/` | AI-Native GTM |
| `dialer` | `packs/dialer/app/models/` | Data Quality (phone connect) |
| `deliverability` | `packs/deliverability/app/models/` | Data Quality (bounce rates) |
| `email_messaging` | `packs/email_messaging/app/models/` | NRR (engagement) |
| `deals` | `packs/deals/app/models/` | Upmarket (pipeline) |
| `meetings` | `packs/meetings/app/models/` | Inbound (router) |
| `experiments` | `packs/experiments/app/models/` | Pricing & Packaging |
| `fraud` | `packs/fraud/app/models/` | Pricing (seat exploit) |
| `3p_data_tool` | `packs/3p_data_tool/app/models/` | Data Quality |
| `data_synthesis` | `packs/data_synthesis/app/models/` | Data Quality |
| `mongo` | `packs/mongo/app/models/` | Foundation (teams, users, contacts) |
| `ui` | `packs/ui/app/models/` | Foundation |

### Key Model → Mongo Collection → Snowflake Table Tracing

This maps critical leadgenie models to their Snowflake availability, highlighting where the pipeline breaks:

| Leadgenie Model | Pack | Mongo Collection | Snowflake Table | Status |
|---|---|---|---|---|
| `credit_quota.rb` | billing | credit_quotas | `LU_CREDIT_QUOTA` / `STG_CREDIT_QUOTA` | Synced, trusted |
| `credit_usage.rb` | billing | credit_usages | `FCT_MONGO_CREDIT_USAGES` | Synced, trusted |
| `credit_usage_detail.rb` | billing | credit_usage_details | `FCT_MONGO_CREDIT_USAGE_DETAILS` | Synced, trusted |
| `cancellation_survey.rb` | billing | cancellation_surveys | `CANCELLATION_SURVEYS` (RAW_MONGO_DB) | Raw only — not in ANALYTICS_DATAPLATFORM |
| `sso_config.rb` | iam | sso_configs | **NOT SYNCED** | Gap — needs Mongo mirror request |
| `permission_set.rb` | iam | permission_sets | `DIM_MONGO_PERMISSION_SETS` | Synced, trusted |
| `mfa_config.rb` | iam | mfa_configs | `DIM_MONGO_MFA_CONFIGS` | Synced (31K rows) |
| `assistant_thread.rb` | ai | assistant_threads | `DIM_MONGO_ASSISTANT_THREADS` | Synced, trusted |
| `ai_request.rb` | ai | ai_requests | Not confirmed | Needs investigation |
| `website_visitor.rb` | 1p_intent | website_visitors | `DIM_MONGO_INTENT_EVENTS` (partial) | `new_reveal`, `total_visits` fields — verify column presence |
| `intent_event.rb` | 1p_intent | intent_events | `INTENT_EVENTS` (RAW_MONGO_DB) | Raw available; verify `contact_identified`/`deanonymised` columns |
| `form_enrichment_daily_stat.rb` | plays | form_enrichment_daily_stats | Not confirmed | Needs investigation |
| `waterfall_enrichment_request_stats.rb` | waterfall | waterfall_enrichment_request_stats | `DIM_MONGO_WATERFALL_ENRICHMENT_REQUEST_STATS` | Synced (54M rows) |
| `data_quality_issue.rb` | data_quality | data_quality_issues | Not confirmed | DQ issue tracking with status workflow |
| `team.rb` | mongo | teams | `DIM_MONGO_TEAMS` | Synced, trusted — includes `market_segment_tier`, `pricing_variant` |

**Key takeaway:** Most billing, enrichment, and core entity models are well-synced. The biggest pipeline gaps are in **IAM** (SSO not synced) and **inbound** (contact-level identification pre-GA). The `CANCELLATION_SURVEYS` collection exists in RAW_MONGO but hasn't been promoted to ANALYTICS_DATAPLATFORM — this is a quick win for churn reason analysis.

______________________________________________________________________

## Key Reference Documents

| Document | Link |
|---|---|
| FY27 AOP | [Google Doc](https://docs.google.com/document/d/1O8eYOSdYk-8MQlVm6EiO5VhfaS5CcVwup4_xYhcYYRw/edit) |
| FY27 Goals Repository | [Google Sheet](https://docs.google.com/spreadsheets/d/1ZgIqAwUv4A53Wl4m2bf-mKgzAqhE-dBqFX0N20s7Cd0/edit) |
| CKO: Ignite to Win Summary | [Google Doc](https://docs.google.com/document/d/1TC8oVtYPwktNuAl9un3paIuyh4qFJOGnd8ER3ICvbkY/edit) |
| Inbound FY27 AOP | [Google Doc](https://docs.google.com/document/d/1D5yoqAxfGHI7d241VlfEEn_wFAzCQXUuhQatGxFri9w) |
| Upmarket Readiness AOP | [Google Doc](https://docs.google.com/document/d/1O8gxemdO-oDA_zQrvFJ8Hl_t26gDtoJaockVxiask8c) |
| Operating Model Evolution | [Google Doc](https://docs.google.com/document/d/1kc_5DVwC2EwEQ-JQbuEXKNEGnQm5bPNiyQsNULEhfuo) |
