# Decisions Log — Data Analytics & Jarvis

**Purpose:** Authoritative record of strategic decisions made by the Analytics/Data Leads team. Prevents re-litigating settled questions and gives Jarvis and new team members the "why" behind current design choices.
**Owner:** Bridie Meredith + Leo Liu
**Format:** Newest first.

---

## 2026-03-31 — Leads Meeting

### [DEC-004] Analytics Copilot as the canonical domain context source for Jarvis

**Decision:** The `analytics-copilot` repo (specifically `domain/`) is the authoritative source of domain knowledge. Jarvis's `knowledge/` directory is a curated, trimmed export from it. Edits to domain context go to analytics-copilot first, then sync to jarvis.

**Rationale:** analytics-copilot has richer context, version history, and team contribution workflows. Jarvis's knowledge base needs to stay lean (token budget), so the sync pipeline is the right abstraction — not maintaining two sources of truth independently.

**Implications:**
- Do not edit `jarvis/knowledge/` directly for domain content changes; edit analytics-copilot and run the sync
- Exception: gap fallback responses and jarvis-specific routing can be authored directly in jarvis
- `sync-to-jarvis` pipeline script needs a review pass (jarvis/knowledge/ has diverged — see Action Log)

---

### [DEC-003] Build a FAQ for common Jarvis questions

**Decision:** Create and maintain a FAQ document covering the most common questions Jarvis users ask (or should ask). Surfaced via Jarvis skill routing.

**Rationale:** Beta users are hitting the same questions repeatedly; an inline FAQ reduces repetitive support overhead and sets expectations about what Jarvis can and can't do.

**Implications:**
- FAQ should cover: how to set up, what questions Jarvis can answer, known gaps + ETAs, how to report a wrong answer
- Wire into Jarvis routing so it surfaces proactively on setup/onboarding questions
- Owner: Bridie (draft); Leo (review)

---

### [DEC-002] Use Analytics Copilot as a QA tool to validate Jarvis accuracy

**Decision:** Analytics Copilot (the analytics team's full Claude Code environment) will be used as a ground-truth checker for Jarvis answers. When Jarvis produces a metric or analysis, Copilot can independently run the same query with fuller context to verify correctness.

**Rationale:** Jarvis operates with a constrained context (exec-facing, token-budgeted). It can drift or hallucinate. Having Copilot as a QA layer — accessible to the analytics team — lets us catch and correct errors before they reach exec decision-making.

**Implications:**
- Build eval test cases in `plugin/e2e_tests.sql` against known-good answers from Copilot
- Periodic QA runs: run Jarvis question set through both systems and diff the answers
- When Jarvis answers something surprising, the first instinct is to verify in Copilot before flagging as a bug

---

### [DEC-001] Emphasize Product Insights and Leo's templates as a primary Jarvis output format

**Decision:** Product Insights reports — following Leo's established templates — should be a first-class output format Jarvis can generate. This includes CBR reports, weekly insights, and product debrief summaries.

**Rationale:** Leo's templates are already trusted and used company-wide. Jarvis should be able to populate them, not invent its own format. This also makes Jarvis output immediately actionable for recipients familiar with the existing format.

**Implications:**
- Templates to wire: `template_cbr_report.md`, `template_stakeholder_update.md`, `product_debrief_template.md`
- Jarvis routing: when asked for a "product debrief" or "CBR" or "weekly insights", load the relevant template and populate from Snowflake data
- Existing `/product-debrief` skill is a start; extend to cover more template types
- Leo to confirm canonical template set; Bridie to wire routing

---

## Prior Decisions (pre-log)

### [DEC-000] Patrick (via Leo) to push plugin through IT for Claude Enterprise deployment

**Decision:** Plugin deployment path is through Patrick, coordinated via Leo. Not a self-service IT request.

**Rationale:** MCP approval requires internal IT review; Leo has the relationship.

**Implications:** Do not attempt direct IT ticket for plugin deploy; route through Leo → Patrick.
