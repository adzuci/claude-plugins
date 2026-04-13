# Jarvis Action Log

**Purpose:** Running record of improvements shipped to Jarvis and work items pending.
**Owner:** Bridie Meredith
**Updated:** 2026-03-31

---

## Completed ✅

| Date | Item | Notes |
|------|------|-------|
| 2026-03-19 | Launched Analytics Copilot MCP beta | Announced to Bela Stepanova |
| 2026-03-26 | Launched #jarvis-beta-users channel | Beta exec cohort onboarded (EQ, Matt Curl, Bela, Ford, James Boone, Kirk Hlavka, John Choi, Will Masket) |
| 2026-03-27 | Jarvis repo published + setup instructions | github.com/apolloio/jarvis; setup video + walkthrough shared |
| 2026-03-30 | Compiled executive knowledge base (12 docs) | annual_targets, theory_of_change, business_state, product_portfolio_taxonomy, activation_methodology, churn_taxonomy_draft, segment_join_canonical, lu_team_segment_patterns, product_disambiguation |
| 2026-03-30 | Built `LU_TEAM_SEGMENT` lookup (Gap 11) | 100% coverage, <100ms join latency; daily refresh task |
| 2026-03-30 | Built product disambiguation guide | Canonical column per lens (feature/plan/add-on/credit); FY27 AOP benchmarks |
| 2026-03-30 | Built `pending_definitions.md` blocker inventory | 15 gaps documented with fallback responses + ETAs |
| 2026-03-30 | Wired full agent routing in `agents/jarvis.md` | Explicit triggers per knowledge doc |
| 2026-03-31 | Added Gaps 15-17 (EQ Quanstrom feedback) | GTME SFDC fields missing from Snowflake; synced to both repos |

---

## In Progress 🔄

| Item | Owner | Blocker | ETA |
|------|-------|---------|-----|
| Gap 15: `Customer_Engagement__c` Fivetran sync | Deepak Kumar | EQ to clarify use case + Sales Ops approval | TBD |
| Gap 16: GTME pre-close renewal picklist | Deepak Kumar | Sales Ops to confirm SFDC field name | 1 day after confirmed |
| Gap 17: AM renewal forecast fields | Deepak Kumar | Sales Ops to confirm field structure | 1 day after confirmed |
| Gap 3: M3_COHORT_NRR table by segment | Bridie | LU_TEAM_SEGMENT done; needs SQL build | Early April |
| Gap 7: F14D Activation in Snowflake | Adhiraj | Mongo → Snowflake event pipeline | Mid-April |
| MCP Snowflake connection unblock | Deepak Kumar | Privacy/IT approval pending | TBD |
| Revisit sync-to-jarvis pipeline script | Bridie | jarvis/knowledge/ has diverged from analytics-copilot | ASAP |

---

## Backlog 📋

| Item | Priority | Notes |
|------|----------|-------|
| FAQ for common Jarvis questions | High | Decided in leads meeting 2026-03-31; reduces repetitive support |
| QA framework: use Analytics Copilot to validate Jarvis accuracy | High | Decided in leads meeting 2026-03-31; Copilot as ground truth checker |
| Product Insights materials emphasis | High | Leo's templates; surface via Jarvis skill routing |
| Gap 2: Persona/ICP definitions → DIM_PERSONAS | Medium | Depends on Adhiraj + AI PM; Q2 |
| Gap 5: Churn taxonomy → CANCELLATION_SURVEYS | Medium | Mid-April; needs taxonomy design + Mongo mirror |
| Gap 4: Partner ARR (PartnerStack) | Medium | Martin + Jennifer; 3-4 weeks |
| Gap 6: Inbound Revenue Attribution flag | Medium | Product to provide flag; 3-5 days once provided |
| Gap 9: SSO/SCIM adoption table | Low | DIM_MONGO_SSO_CONFIGS may exist; verify |
| Gap 14: Headcount source (DARWINBOX?) | Low | Finance clarification needed |
| Gap 10: People metrics (attrition, engagement) | Low | HR/People Ops definitions needed |
