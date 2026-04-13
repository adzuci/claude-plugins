# Jarvis Knowledge Base Manifest

**Purpose:** Inventory of Jarvis's live knowledge base — what Jarvis knows, how confident it is, and what's blocked.

**Date:** 2026-03-31
**Status:** Live
**Maintained by:** Bridie Meredith

> **All files in `jarvis/knowledge/` (except this file and `domain_context.md`) are managed by one-way sync from `analytics-copilot`.** Do not edit synced files directly — changes will be overwritten. To update Jarvis's knowledge, edit the source in `analytics-copilot` and run `/sync-jarvis`. The authoritative list of synced files is `analytics-copilot/domain/SYNC_MANIFEST.md`.

---

## Overview

Compiled documentation that enables Jarvis to answer 15 executive questions without requiring exploration. The knowledge base bridges the gap between "raw data access" and "contextual understanding."

### Key Stats
- **9 new/updated domain docs**
- **1 segment lookup table + refresh automation (LU_TEAM_SEGMENT)**
- **8 executable business questions** (Q1, Q2, Q4, Q8, Q9, Q11, Q12, Q15)
- **7 blocked questions with explicit gap documentation** (Gaps 2, 3, 5, 6, 7, 14, and pending Gap 10)
- **10 structured data requirements** (REQ-1 through REQ-10)

---

## What's Included (Ready to Transfer)

### Tier 1: Strategy & Context (Required Reading for Jarvis)

| File | Purpose | Use Case | Status |
|------|---------|----------|--------|
| **annual_targets.md** | FY27 OKR targets by metric | Exec asks "On track?" → Jarvis looks up target, queries actual, shows delta | ✅ LIVE |
| **theory_of_change.md** | Causal chain driving growth strategy | Exec asks "Why?" → Jarvis explains the chain: activation → habit → retention → expansion | ✅ LIVE |
| **business_state.md** | Current momentum snapshot (living doc) | Exec asks "How are we?" → Jarvis references live status of each lever + known risks | ✅ LIVE |
| **product_portfolio_taxonomy.md** | H1/H2/H3 classification + graduation criteria | Exec asks "Is [product] on track?" → Jarvis finds product, looks up target + criteria | ✅ LIVE |
| **pending_definitions.md** | Inventory of data gaps + how to handle them | Exec asks about blocked question → Jarvis explains blocker + ETA | ✅ LIVE |
| **rnd_okr_structure.md** | R&D OKR structure for FY27 Q1 — how product teams organize and track progress | "What is Bela's org working on?", "OKR status?" → R&D team structure + scorecard | ✅ LIVE (snapshot — goes stale; prefer live Snowflake for actuals) |
| **executive_profiles.md** | What each exec cares about, data consumption style, how to engage | Tailor response tone, depth, and framing to the exec asking the question | ✅ LIVE |
| **fiscal_calendar.md** | Apollo FY27 quarter boundaries (Feb-start fiscal year) | Correctly interpret "Q1", "Q2", "this quarter" in exec questions | ✅ LIVE |
| **decisions_log.md** | Authoritative record of strategic decisions by Analytics/Data Leads | Prevent re-litigating settled questions; explain "why is it designed this way?" | ✅ LIVE |

### Tier 1-Admin: Jarvis Maintenance (Internal Only — not for exec-facing responses)

| File | Purpose | Audience | Status |
|------|---------|----------|--------|
| **jarvis_health_playbook.md** | How to keep Jarvis accurate: sync pipeline, weekly refresh, quality scorecard | Analytics team (Bridie, Leo, Deepak) | ✅ LIVE |
| **jarvis_update_protocol.md** | How to update Jarvis's knowledge base; sync workflow and policy | Analytics team contributors | ✅ LIVE |
| **contribution_guidelines.md** | Protected files, edit policies, contribution rules for analytics-copilot | Analytics team, DS contributors | ✅ LIVE |
| **jarvis_action_log.md** | Running record of Jarvis improvements shipped + pending work items | Analytics team (Bridie) | ✅ LIVE |

---

### Tier 2: Metric Methodologies (Reference for Specific Questions)

| File | Metric | Purpose | Status |
|------|--------|---------|--------|
| **activation_methodology.md** | F14D Habit RA Rate | Explains what/why; definition for Q7 | ✅ LIVE (methodology) |
| **churn_taxonomy_draft.md** | Churn reasons by category | Framework for Q3; awaiting product/VoC finalization | 🟡 DRAFT (taxonomy) |
| **ai_sheets_user_definition.md** | GTM Engineer cohort definition | Placeholder for Q5 granularity; awaiting product persona definition | 🟡 DRAFT (pending Gap 2) |
| **inbound_team_identification.md** | Inbound add-on revenue attribution | Data source + mapping for Q6; awaiting product flag definition | 🟡 DRAFT (pending Gap 6) |

---

### Tier 3: Domain Knowledge (Created in Prior Session)

| File | Purpose | Status |
|------|---------|--------|
| **segment_join_canonical.md** | Segment join patterns — LU_TEAM_SEGMENT preferred; SFDC join as legacy fallback | ✅ UPDATED 2026-04-07 (LU_TEAM_SEGMENT is now canonical; SFDC join demoted to legacy) |
| **lu_team_segment_patterns.md** | 5 reusable SQL patterns for segment queries using LU_TEAM_SEGMENT | ✅ LIVE (new 2026-03-30) |
| **product_debrief_template.md** | Canonical 3-step execution framework for all product area debriefs | ✅ LIVE — referenced by product-debrief skill; WAT source guidance updated 2026-04-07 |
| **product_disambiguation.md** | Which table/column to use for each "product" lens (feature/plan/add-on/credit) | ✅ LIVE — use when exec says "product" ambiguously |
| **sql_patterns.md** | Canonical SQL patterns and conventions for Apollo analytics queries | ✅ LIVE — reference before writing ad-hoc queries |

---

### Tier 4: Data Catalog Updates (Created in Prior Session)

| File | Change | Status |
|------|--------|--------|
| **data-catalog/glossary_entries.md** | Added "Account Segment (Lookup Table)" entry | ✅ UPDATED 2026-03-30 |
| **data-catalog/table_inventory.md** | Added "Lookup Tables — Denormalization Bypasses" section with LU_TEAM_SEGMENT | ✅ UPDATED 2026-03-30 |
| **data-catalog/lu_team_segment.md** | Schema, distribution, refresh automation for LU_TEAM_SEGMENT | ✅ LIVE 2026-03-30 |

---

## Which Executive Questions Can Jarvis Answer Now?

### Answerable TODAY (8/15)

| Q | Question | Status | Jarvis Strategy |
|---|----------|--------|-----------------|
| **Q2** | Churn rate by segment? | ✅ YES | Query + show by segment |
| **Q4** | Use cases per paid team? | ⚠️ PARTIAL | Accept DS table quality; caveat |
| **Q8** | Credit engagement experiment? | ✅ YES | Query GOLD_TEAM_CREDITS |
| **Q9** | MM+Ent pipeline health? | ✅ YES | Standard SFDC query |
| **Q11** | ARR by segment × motion? | ✅ YES | FCT_DAILY_REVENUE + segment join |
| **Q12** | Growth accounting bridge? | ✅ YES | CHANGE_CATEGORY grouping |
| **Q15** | Waterfall hit rates? | ✅ YES | Standard WATERFALL query |
| **Q1** | NRR on track? | ⚠️ PARTIAL | Aggregate quarterly yes; M3 cohort NO (Gap 3) |

### Blocked / Partially Blocked (7/15)

| Q | Question | Blocker | ETA to Unblock |
|---|----------|---------|----------------|
| **Q3** | Why churning? | Gap 5 (churn taxonomy) | Mid-April |
| **Q5** | AI adoption? | Gap 2 (AI Sheets persona) | End of Q2 |
| **Q6** | Inbound pacing? | Gap 6 (inbound flag) | End of Q1 |
| **Q7** | Activation rate? | Gap 7 (Snowflake version) | Mid-April |
| **Q10** | SSO/SCIM adoption? | Gap 9 (data source) | 1-2 days |
| **Q13** | NRR annualized? | Gap 3 (segment) | Early April |
| **Q14** | Revenue per employee? | Gap 14 (headcount source) | 1 day (Finance clarification) |

---

### Tier 5: Analyst Suits (Synced from analytics-copilot)

| File | Analyst | Domain | Status |
|------|---------|--------|--------|
| **suits/leo_analyst_suit.md** | Leo Liu | NRR/GRR, cohort retention, mix-shift decomposition, segment economics, ARR modeling | ✅ LIVE |
| **suits/leo_leader_suit.md** | Leo Liu | Management coaching, career advice, analytics integrity, feedback delivery | ✅ LIVE |
| **suits/index.md** | — | Routing rules: explicit + implicit triggers for suit activation | ✅ LIVE (jarvis-native) |

Suits teach Jarvis to think and communicate like a specific analyst. Routing logic is in `suits/index.md` — suits activate explicitly ("use Leo's suit") or implicitly when the task matches the suit's domain keywords. Suit content files are synced from `analytics-copilot/teammates/`; the index is jarvis-native.

**Sync verification:** `python3 ~/workspace/analytics-copilot/scripts/verify_suit_sync.py` checks for content drift and index completeness.

---

## How to Use This Knowledge Base

### For Jarvis Developers

1. **System prompt:** Import `annual_targets.md`, `theory_of_change.md`, `business_state.md` into Jarvis's system prompt
2. **Fallback docs:** Wire in `pending_definitions.md` so Jarvis knows what to say when blocked
3. **MCP/Tools:** When Jarvis gets a query, it should:
   - Recognize the intent (e.g., "Are we on track?" → leads to annual_targets.md)
   - Look up the relevant doc
   - Query Snowflake for current data
   - Blend the two and respond

4. **Metric-specific:** For queries mentioning F14D, churn, AI Sheets, or Inbound:
   - Reference the corresponding methodology file
   - Explain what's live vs. what's pending

### For Analytics Team

1. **Weekly refresh:** Update `business_state.md` with new momentum signals (every Monday)
2. **Monitor blockers:** Track ETA on Gaps 2, 3, 5, 6, 7, 14 in `pending_definitions.md`
3. **Validate queries:** Use `segment_join_canonical.md` and `lu_team_segment_patterns.md` as templates
4. **New metric:** If adding a new KPI, create a methodology file (see activation_methodology.md as template)

### For Executives / Stakeholders

1. **What can Jarvis answer?** This manifest (section "Which executive questions can Jarvis answer now?")
2. **Why is Jarvis blocked on [X]?** See `pending_definitions.md` for blocker + ETA
3. **What are we targeting?** See `annual_targets.md`
4. **What's the strategy?** See `theory_of_change.md`
5. **How are we doing?** See `business_state.md`

---

## How This Knowledge Base Is Maintained

All files in `jarvis/knowledge/` (except `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` and `domain_context.md`) are **automatically synced** from `analytics-copilot` via `scripts/sync-jarvis.sh`.

**Never edit synced files directly.** Edit the source in `analytics-copilot` and run `/sync-jarvis`.

For the full list of synced files and instructions, see `analytics-copilot/domain/SYNC_MANIFEST.md`.

---

## Known Limitations & Caveats

1. **Living documents:** `business_state.md` should be updated weekly; others (targets, strategy) quarterly
2. **Blocked questions:** 7 of 15 are blocked on data infrastructure gaps; these should unblock progressively (March → June timeline)
3. **Draft documents:** `churn_taxonomy_draft.md`, `ai_sheets_user_definition.md`, `inbound_team_identification.md` awaiting product/VoC finalization
4. **Personas:** No standardized persona → data filter mapping yet (Gap 2); ICP vocabulary still under development

---

## Success Metrics (for Transfer)

Once transferred to Jarvis:

1. **Jarvis can answer 8/15 questions on first try** (no exploration needed)
2. **Jarvis properly blocks on 7/15** (explains blocker + ETA, not "I don't know")
3. **Weekly business_state.md updates** (kept current by analytics team)
4. **Data gaps close on schedule** (Gap 3, 5, 7 by mid-April; Gap 2 by end of Q2)

---

## Questions?

For questions on any of these docs, contact:
- **Strategy & context:** Bridie Meredith (Analytics)
- **Metric definitions:** Adhiraj Yadav (Metrics owner)
- **Product bets:** Leo Liu (Strategy)
- **Data infrastructure:** Data Engineering team

---

**Last updated:** 2026-04-09
**Next review:** Weekly (business_state.md), Quarterly (all others)
