# Pending Definitions — Data Gaps Blocking Jarvis

**Purpose:** Inventory of analytical gaps that prevent Jarvis from fully answering executive questions.

**Status:** Updated 2026-03-30
**Owner:** Bridie Meredith (Analytics) + data engineering owners per gap

---

## Resolved Gaps ✅

| Gap | Description | Resolved | How |
|-----|-------------|----------|-----|
| **Gap 11 (Segment Denormalization)** | Segment not on revenue tables; required expensive SFDC joins. | 2026-03-30 | Built `LU_TEAM_SEGMENT` lookup table + daily refresh task. 100% coverage, <100ms join latency. |

---

## Open Gaps (Priority Order)

### Gap 15 — Customer_Engagement__c SFDC Object Not in Snowflake (GTME BLOCKER)

**What's needed:** `Customer_Engagement__c` Salesforce custom object synced to Snowflake via Fivetran.

**Why it matters:**
- Blocks EQ Quanstrom's GTME Tasks & Projects workflow (intervention analysis, sentiment trends, churn risk)
- Missing fields: Meeting Type (Intervention), Stage (Complete), Sentiment Details, Latest Engagement Next Steps
- Free-text CRM fields not available at query time

**Current state:**
- Jarvis can analyze intervention *patterns* and churn *risk* from existing Snowflake tables
- Partial substitutes available: `GTME_CALLS_AI_ANALYSIS`, `INTERVENTIONS` table
- Cannot see: intervention type tags, call-level stage, next steps bullets (CRM-entered free text)

**Blocker:** `Customer_Engagement__c` not included in current Fivetran sync. Requires Sales Ops approval for schema change.

**Open question:** EQ to clarify whether he needs per-account summaries (runtime LLM query) or portfolio-level pattern classification (requires pre-processing pipeline). Answer determines solution architecture.

**Resolution path:**
1. EQ confirms use case (per-account vs. portfolio patterns)
2. Sales Ops approves Fivetran schema change
3. Deepak Kumar adds `Customer_Engagement__c` to Fivetran sync
4. dbt model + data-catalog entry
5. Update Jarvis context file with field mapping

**Owner:** Deepak Kumar (Fivetran config)
**Estimate:** 1–2 days once Sales Ops approves

**Jarvis fallback:**
> "I can see intervention patterns and sentiment trends from `GTME_CALLS_AI_ANALYSIS` and `INTERVENTIONS`, but the detailed CRM fields — intervention type tags, next steps bullets, and call-level stage — aren't in Snowflake yet because `Customer_Engagement__c` hasn't been synced via Fivetran. Deepak Kumar is on it; ETA 1–2 days after Sales Ops approves. In the meantime I can show you the intervention signal patterns from the structured tables."

---

### Gap 16 — GTME Expected Renewal Outcome Forecast Picklist

**What's needed:** Pre-close renewal forecast picklist (Flat / Expand / Churn / Downgrade / No Response) that GTMEs enter on open deals.

**Why it matters:**
- Blocks forward-looking churn and expansion forecasting from GTME book of business
- Current `RENEWAL_OUTCOME` field only holds post-close values — can't see what a GTME is forecasting *before* renewal

**Current state:**
- `RENEWAL_OUTCOME` in Snowflake: post-close only
- Pre-close forecast field exists in SFDC but SFDC API name unconfirmed
- No Snowflake equivalent

**Blocker:** Sales Ops must confirm the SFDC API field name for the pre-close picklist.

**Resolution path:**
1. Single Slack to Sales Ops: confirm SFDC API name for the Expected Renewal Outcome picklist
2. Deepak adds field to Fivetran sync (1-day fix)
3. Validate and document

**Owner:** Deepak Kumar (after Sales Ops confirms)
**Estimate:** 1 day once field name confirmed

**Jarvis fallback:**
> "I can see post-close renewal outcomes from `RENEWAL_OUTCOME`, but the pre-close forecast field — what GTMEs are predicting before a deal closes — isn't in Snowflake yet. We're waiting on Sales Ops to confirm the SFDC field name. Once confirmed, it's a 1-day sync. For now I can show you historical renewal outcomes or open deal churn risk signals."

---

### Gap 17 — AM-Specific Renewal Forecast Fields

**What's needed:** AM-specific renewal forecasting fields (`AM_RENEWAL_FORECAST_C`, `AM_RENEWAL_CONFIDENCE_C`, `AM_NEXT_STEP_C` or equivalent).

**Why it matters:**
- Blocks AM-level renewal forecast visibility separate from GTME fields
- Can't distinguish AM vs GTME renewal activity without dedicated fields or confirmed shared-field filter

**Current state:**
- No dedicated AM renewal fields confirmed in Snowflake
- Unclear whether dedicated SFDC fields exist or if AMs share GTME fields (filtered by `POSITION_C`)

**Blocker:** Sales Ops must confirm whether dedicated AM fields exist in SFDC.

**Resolution path:**
- Path A (if dedicated fields exist): Sync to Snowflake via Fivetran, document
- Path B (if shared with GTME): Document filter pattern (`WHERE POSITION_C = 'AM'`) and update Jarvis SQL patterns

**Owner:** Deepak Kumar (after Sales Ops confirms)
**Estimate:** 1 day once confirmed

**Jarvis fallback:**
> "I don't yet have AM-specific renewal forecast fields in Snowflake. If AMs share fields with GTMEs, I can filter by position — but I need Sales Ops to confirm the field structure first. In the meantime I can pull AM renewal history from closed deals or show you AM-attributed churn signals."

---

### Gap 3 — Cohort-Level NRR with Segment (CRITICAL)

**What's needed:** M3/M6/M12 cohort NRR broken down by account segment at acquisition time (VSB/SMB/MM/Ent).

**Why it matters:**
- Executive asks: "Are VSB/SMB +10pt NRR improvement on track?"
- Can't answer without cohort NRR by segment
- Blocks Q1, Q13 in executive_questions_resolution.md

**Current state:**
- Quarterly aggregate NRR available (`FCT_ACCOUNT_QUARTERLY_NRR`) — HIGH trust
- Cohort data fragments exist in `FCT_DAILY_REVENUE` but no cohort NRR table
- Segment requires either: (a) historical SFDC snapshots at signup time, OR (b) join through current segment with caveat

**Blocker:** Requires segment denormalization decision (Gap 11 partial).

**Resolution path:**
1. ✅ Build `LU_TEAM_SEGMENT` lookup (DONE 2026-03-30)
2. Build `M3_COHORT_NRR` table from `FCT_DAILY_REVENUE` + segment lookup (ETA: early April, Bridie)
3. Break down by segment + core/non-core flag (same table)

**Estimate:** 2-4 hours SQL + validation

---

### Gap 2 — Persona & ICP Vocabulary (BLOCKING MULTIPLE QUESTIONS)

**What's needed:** Standardized definitions mapping buyer personas (GTM Engineer, RevOps, AE-led, etc.) to data filters.

**Why it matters:**
- Executive asks: "How is AI Sheets adoption among GTM Engineers?"
- Can't identify "GTM Engineer" cohort without definition
- Blocks Q5 (AI adoption), Q6 (Inbound targeting), product bet tracking

**Current state:**
- Product personas exist (GTM Engineer, RevOps, etc.) but not mapped to data
- No standard cohort definition in Snowflake
- Inbound/Dialer targeting happens in product layer (no Snowflake visibility)

**Blocker:** Product + Sales must define each persona operationally.

**Resolution path:**
1. Adhiraj + AI PM to define "AI Sheets power user" (Q2 target)
2. Create ICP lookups mapping team characteristics to persona:
   - GTM Engineer: Team size 5-50, >70% CRM users, >5 emails/user/day
   - RevOps: Team size 1-10, heavy automation users, credits/seats over emails
   - AE-led: Company size 100-500, seats 5+, dialer or enrichment primary
3. Build `DIM_PERSONAS` lookup table in Snowflake
4. Join to fact tables for segment-by-persona analysis

**Estimate:** 1-2 weeks (depends on product team turnaround on definitions)

---

### Gap 5 — Structured Churn Taxonomy (BLOCKING PRODUCT DECISIONS)

**What's needed:** Structured categorization of why teams churned (e.g., "not_using_enough", "competitive_loss", "role_change", "product_gap").

**Why it matters:**
- Executive asks: "Why are teams churning?"
- Current VoC data is unstructured; can't query trends
- Blocks Q3 in executive_questions_resolution.md
- Drives product prioritization

**Current state:**
- `CANCELLATION_SURVEYS` in RAW_MONGO (raw survey responses, unstructured)
- Zendesk churn tickets exist (`FCT_ZENDESK_CHURN_TICKETS`, 101K rows)
- No normalized taxonomy; manual tagging would be required for analysis

**Blocker:** Requires (a) Mongo mirror setup (DE), (b) taxonomy design (Product/VoC), (c) classification workflow.

**Resolution path:**
1. Propose taxonomy (5-7 main categories + subcategories)
2. De to mirror `CANCELLATION_SURVEYS` to ANALYTICS_DATAPLATFORM
3. Build normalization function (classify raw text to taxonomy)
4. Join to `FCT_DAILY_REVENUE` churn events
5. Build `V_CHURN_REASONS_BY_SEGMENT` view

**Estimate:** 1-2 weeks (depends on DE + Product availability)

**Proposed taxonomy:**
- `not_using_enough` — Low engagement, didn't hit habits
- `complexity` — Product too hard, onboarding didn't work
- `competitive_loss` — Lost deal to competitor
- `role_change` — User left company or changed roles (not a product fix)
- `budget_constraint` — Company-wide headcount/cost cuts
- `product_gap` — Feature missing or broken
- `cost` — Too expensive for value perceived
- `other` — Miscellaneous

---

### Gap 7 — F14D Activation in Snowflake (BLOCKING LEADING INDICATOR)

**What's needed:** F14D Habit RA Rate (4+ Record Actions in first 14 days) computed in Snowflake instead of Amplitude-only.

**Why it matters:**
- F14D is the #1 leading indicator for NRR improvement (Gate of Theory of Change)
- Currently unmeasurable from warehouse; full dependency on Data Science team
- Blocks Q7, and prevents Jarvis from automating activation monitoring

**Current state:**
- Amplitude metric exists; baseline ~12%, target 17%
- Record Actions defined (email, call, sequence add, enrichment request, etc.)
- No warehouse events table for structured Record Actions

**Blocker:** Requires event-level Record Actions from Mongo → Snowflake pipeline.

**Resolution path:**
1. Adhiraj to build `DIM_ACTIVATION` table from Mongo events:
   - team_id, signup_date, activation_date, record_actions_in_f14d, is_activated_flag, segment
   - Grain: one row per team
2. Backfill from Jan 2026 onwards
3. Build view `V_F14D_ACTIVATION_RATE_BY_SEGMENT` for reporting

**Estimate:** 1-2 weeks (Adhiraj owns; in progress per metrics intake)

---

### Gap 4 — Partner ARR Tracking (BLOCKING PARTNER OKR)

**What's needed:** Flag or lookup table identifying partner-sourced revenue (PartnerStack) in `FCT_DAILY_REVENUE`.

**Why it matters:**
- Executive asks: "How are we pacing on $7.2M FY27 partner revenue target?"
- Partner program exists but not visible in revenue tables
- Blocks accurate NNARR attribution (new vs. partner-sourced vs. organic)

**Current state:**
- PartnerStack platform exists (external, not integrated)
- No pipeline from PartnerStack → Snowflake
- Revenue is flowing through (included in ARR) but not tagged

**Blocker:** Martin + Jennifer Rhima own PartnerStack pipeline; in progress (3-4 week build estimated).

**Resolution path:**
1. PartnerStack API pull to Snowflake (DE)
2. Match partner-sourced teams to SFDC accounts
3. Flag in `FCT_DAILY_REVENUE` (add PARTNER_SOURCE_IND column)
4. Build `V_PARTNER_ARR_BY_TIER` view

**Estimate:** 3-4 weeks (Martin + Jennifer own)

---

### Gap 6 — Inbound Revenue Attribution (BLOCKING PRODUCT EXPANSION)

**What's needed:** Lookup or flag identifying inbound add-on teams in revenue tables.

**Why it matters:**
- Executive asks: "Inbound pacing toward $6.4M target?"
- Inbound product exists; teams are adopting; but not tagged in Snowflake
- Blocks Q6 tracking and product bet graduation

**Current state:**
- Inbound teams tracked in Mongo (`teams.inbound_status`)
- Q1 traction: ~170 teams, $300k+ ARR
- Revenue flows through but not isolated in FCT_DAILY_REVENUE

**Blocker:** Requires product team to provide team list or flag definition.

**Resolution path:**
1. Product to provide flag (e.g., `inbound_activated_at` in Mongo)
2. DE to build Mongo mirror + lookup table `DIM_INBOUND_TEAMS`
3. Join to revenue tables
4. Build `V_INBOUND_ARR_BY_SEGMENT` view

**Estimate:** 3-5 days (if product provides flag immediately)

---

### Gap 9 — SSO/SCIM Adoption for Enterprise (BLOCKING UPMARKET STRATEGY)

**What's needed:** True SSO configuration data in Snowflake (currently MFA is proxy only).

**Why it matters:**
- Enterprise readiness signal; feature lock-in metric
- Executive asks: "SSO adoption among MM+Ent?"
- Current proxy (MFA adoption) is not precise enough

**Current state:**
- `DIM_MONGO_SSO_CONFIGS` table exists (schema unknown; may be partial)
- `sso_config.rb` in leadgenie codebase but not synced to Snowflake
- MFA adoption available (`DIM_MONGO_MFA_CONFIGS`, 31K rows)

**Blocker:** Requires Mongo mirror confirmation + Snowflake sync.

**Resolution path:**
1. Verify `DIM_MONGO_SSO_CONFIGS` exists and is complete
2. Build `V_SSO_ADOPTION_BY_SEGMENT` view
3. Document in data-catalog

**Estimate:** 1-2 days (if table exists)

---

### Gap 14 — Headcount Data Source (BLOCKING REVENUE/EMP METRIC)

**What's needed:** Confirm source of truth for headcount; ensure it's accessible in Snowflake.

**Why it matters:**
- Executive asks: "Revenue per employee ($300k target)?"
- ARR is known, but headcount source unclear (DARWINBOX? External HR system?)

**Current state:**
- DARWINBOX data in Snowflake (unknown if complete)
- External HR systems (Bamboo? Lattice?) not confirmed synced
- Finance owns headcount; coordination needed

**Blocker:** Requires Finance clarification + coordination.

**Resolution path:**
1. Finance to confirm: Is headcount in Snowflake? Which table?
2. If yes: Build `V_REVENUE_PER_EMPLOYEE` view
3. If no: Establish regular headcount sync process

**Estimate:** 1 day (clarification) + 1-2 hours SQL once confirmed

---

### Gap 10 — People Metrics (Regrettable Attrition, Engagement)

**What's needed:** Standard definitions + Snowflake access for people metrics (attrition classification, engagement survey scores).

**Why it matters:**
- Executive asks: "Can we hit AI growth AND org health simultaneously?"
- People metrics are OKRs but not yet in Snowflake or standardized
- Blocks assessment of whether growth initiatives are sustainable

**Current state:**
- DARWINBOX has headcount + position history (no attrition classification)
- Engagement surveys exist (unknown if in Snowflake; source unclear)
- "Regrettable" vs. non-regrettable is HR interpretation, not data

**Blocker:** Requires HR + People Ops definitions + Snowflake access.

**Resolution path:**
1. HR to define: "regrettable attrition" classification (criteria: exit reason + tenure)
2. HR/Finance to provide engagement survey data (score scale, current baseline)
3. Build `DIM_PEOPLE_METRICS` table with attrition_classification, engagement_score
4. Build `V_PEOPLE_HEALTH_BY_DEPT` view

**Estimate:** 2-3 weeks (requires HR stakeholder coordination)

---

## How Jarvis Handles Blocked Questions

When a gap blocks a question, Jarvis should say:

**Example (Gap 3):**
> "I can show you aggregate quarterly NRR ($X), but I can't yet break it down by entry segment (VSB vs. SMB). The team is building a segment-aware cohort NRR table — should be available by early April. Until then, I'm using the aggregate, which masks segment-specific risks."

**Example (Gap 2):**
> "AI Sheets adoption data isn't yet separated in our warehouse — I can show you overall AI WAU (target 15K, current $X), but I can't segment to 'GTM Engineer adoption' because the team is still finalizing what identifies an AI Sheets power user. Adhiraj is working on this definition — should be locked by end of Q2."

**Example (Gap 5):**
> "We don't have structured churn reasons in Snowflake yet. Voice of Customer says 36% of churners are role/responsibility changes, 19% report 'wasn't sure how to get value.' The team is building a churn taxonomy and promoting cancellation survey data to the warehouse — should be queryable by mid-April."

---

---

### Gap 18 — product_metrics_daily Not Documented (BLOCKS WAT SOURCE GRADING)

**What's needed:** Data catalog context file for `ANALYTICS_DB.ANALYTICS_DATASCIENCE.product_metrics_daily`.

**Why it matters:**
- Canonical source for WAT, WAU, and other rolling window metrics
- Without a context file, Jarvis falls back to `DIM_TEAMS_DAILY`/`FCT_TEAM_FEATURE_USERS_DAILY` for WAT queries
- Source grading on all WAT eval questions caps at 40 until this is documented
- Identified in eval run 2026-03-31

**Current state:** Table exists and is queryable; referenced in question patterns and CBR sources doc but no formal catalog entry.

**Resolution path:**
1. Query `INFORMATION_SCHEMA.COLUMNS` for `product_metrics_daily` — get full column list + sample metric/topic/use_case values
2. Create `data-catalog/context/PRODUCT_METRICS_DAILY.md`
3. Add to `scripts/sync-jarvis.sh` + `domain/SYNC_MANIFEST.md`
4. Sync to jarvis

**Owner:** Bridie | **Complexity:** S | **Estimate:** Next eval prep session

---

### Gap 19 — IS_PARENT_ACCOUNT=TRUE North Star ARR Not Proactively Surfaced

**What's needed:** Jarvis should always offer the IS_PARENT_ACCOUNT=TRUE "North Star" aggregate ARR view (~$330-340M) alongside team-level ARR (~$165-175M) when answering exec ARR questions.

**Why it matters:**
- Execs expect ~$336M; Jarvis returns ~$166M without labeling it as team-level
- Avg ARR per team is $1,880 (team-level) vs $3,760 (North Star) — ~2x difference creates confusion
- q9_paid_teams_avg_arr_comparison soft-fails on this; no exec question should silently return the wrong view
- Identified in eval run 2026-03-31

**Current state:** FCT_TEAM_REVENUE_DAILY.md documents the duality. Jarvis does not proactively surface it.

**Resolution path:** Add to `jarvis/CLAUDE.md` guardrails and `domain_context.md` revenue_org_structure: "For exec ARR totals, always surface IS_PARENT_ACCOUNT=TRUE view; label team-level vs North Star explicitly."

**Owner:** Bridie | **Complexity:** S | **Estimate:** 30 min

---

### Gap 20 — OUTREACH_MENTIONED Boolean Missing from GONG_CALLS_AI_ANALYSIS

**What's needed:** Add `OUTREACH_MENTIONED` as a boolean extraction target in the Gong AI analysis pipeline, following the same pattern as `SALESLOFT_MENTIONED` and `ZOOMINFO_MENTIONED`.

**Why it matters:**
- EQ Quanstrom's competitive displacement analysis is incomplete — Outreach is a major competitor but can't be trended
- `COMPETITORS_DISCUSSED` array only tracks 12 named competitors; Outreach is not one of them
- 45K raw transcript keyword hits for "outreach" exist but are noise-polluted by common English usage ("outreach program", "outreach effort")
- A structured boolean flag with NLP-aware extraction would separate product mentions from generic usage
- Blocks quarterly Outreach displacement rate trending (same analysis that shows ZI displacement at ~20% of NB wins)

**Current state:**
- `COMPETITORS_DISCUSSED` VARIANT array captures structured competitor mentions but excludes Outreach
- `SALESLOFT_MENTIONED` and `ZOOMINFO_MENTIONED` booleans exist and follow the extraction pattern
- `OUTREACH_MENTIONED` does not exist in schema
- Raw transcript keyword search returns 45K hits but is unreliable without NLP classification

**Blocker:** Requires Gong AI pipeline update (DAPI LLM extraction logic) to add Outreach to the extraction target list.

**Resolution path:**
1. Confirm Gong call processing pipeline (DAPI) configuration and extraction target list
2. Add `OUTREACH_MENTIONED` to extraction targets (copy SALESLOFT/ZOOMINFO pattern)
3. Backfill historical calls (last 6 months minimum)
4. Validate against raw transcript hits — structured extraction should capture a subset of the 45K raw matches
5. Update `GONG_CALLS_AI_ANALYSIS` data-catalog entry with new column

**Owner:** Data Platform / DAPI team
**Complexity:** S (pattern exists, configuration addition)
**Estimate:** 1-2 days (config change + backfill + validation)

**Jarvis fallback:**
> "Outreach competitive displacement cannot be trended yet — `OUTREACH_MENTIONED` hasn't been added to the Gong AI extraction pipeline. The `COMPETITORS_DISCUSSED` array tracks 12 named competitors but Outreach isn't one of them. Raw transcript keyword matches (45K hits) are noise-polluted. This is a known data gap (Gap 20) and the fix is in the backlog."

---

## Closure Criteria

Each gap is considered **CLOSED** when:
1. Documented in data-catalog with schema + update frequency
2. Validated with test query against real data
3. Documented in domain context (theory, patterns, usage)
4. Removed from this file

Update this file weekly as gaps close or new gaps are identified.
