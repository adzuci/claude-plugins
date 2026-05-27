# Product Disambiguation Guide

"Product" is intentionally ambiguous at Apollo. It means different things to different audiences. This guide tells you which lens to use based on context, and which table/column to query for each.

---

## The Four Lenses

### Lens 1 — Feature Area (default for exec questions)
How executives and PMs think about products. What capability is the team using?

| Exec term | Data equivalent | Table | Column |
|---|---|---|---|
| Email / Outreach | `email_credit`, `ai_email` | AGG_TEAM_CREDITS | `FEATURE_TYPE` |
| Dialer | `direct_dial_credit` | AGG_TEAM_CREDITS | `FEATURE_TYPE` |
| Enrichment / Waterfall | `waterfall_enrichment`, `waterfall_mobile_enrichment`, `api_waterfall_enrichment`, `export_credit` | AGG_TEAM_CREDITS | `FEATURE_TYPE` |
| AI features / AI Power-Up | `ai_credit`, `ai_email` | AGG_TEAM_CREDITS | `FEATURE_TYPE` |
| Prospecting / GenPipe | `USE_CASE_GENPIPE_TRADITIONAL`, `USE_CASE_GENPIPE_NEXTGEN` | DIM_ACTIVE_TEAMS_DAILY | `USE_CASE_*` |
| Sequences | Sequence activity L7 | DIM_TEAMS_DAILY | `SEQUENCE_*_USER_COUNTS_L7` |
| AI Assistant | Thread/message counts | TEAM_AI_ASSISTANT_DAILY | `WAU`, `TOTAL_THREADS` |

**Use this lens when:** "Which products are underperforming?", "How is [feature] doing?", "Product engagement", "WAT by product"

---

### Lens 2 — Plan Edition (subscription tier)
Billing-level product classification. Which tier is the team on?

| Edition | Filter |
|---|---|
| Free | `APOLLO_EDITION = 'Free'` |
| Basic | `APOLLO_EDITION = 'Basic'` |
| Professional | `APOLLO_EDITION = 'Professional'` |
| Custom / Org | `APOLLO_EDITION = 'Custom'` |

**Table:** `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS.APOLLO_EDITION`

**Use this lens when:** "How is the Free plan doing?", "Professional vs Custom retention", "Edition mix", "upgrade from Basic to Pro"

---

### Lens 3 — Add-on Module (purchasable discrete product)
Standalone products that teams buy on top of their base plan. Both priced at $149/mo (seat-based: $149, $447, $894, $1,428).

| Add-on | Filter | ARR formula |
|---|---|---|
| Inbound Router | `additional_fee_by_source:"inbound"::number > 0` | `inbound_fee / billing_interval_months * 12` |
| Dialer Add-on | `additional_fee_by_source:"dialer"::number > 0` | `dialer_fee / billing_interval_months * 12` |

**Table:** `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS.ADDITIONAL_FEE_BY_SOURCE`
**Alternative for current state:** `DIM_MONGO_TEAMS_RT_VW.product_infos` flattened for `%inbound%` or `%dialer%` plans

**Use this lens when:** "Inbound Router ARR", "Dialer add-on attach rate", "add-on performance", "Inbound churn"

---

### Lens 4 — Credit Product (consumption-based)
What types of credits is the team consuming? Relevant for monetization and packaging analysis.

Key groupings:
- **Unified credits** — `unified_lead_credit` (the migration target; teams may/may not be migrated)
- **Export credits** — `export_credit`
- **Direct dial credits** — `direct_dial_credit`
- **AI credits** — `ai_credit`, `ai_email` (NOTE: `ai_email` draws from Apollo's pool, NOT customer-billed — exclude from customer consumption metrics)
- **Waterfall** — `waterfall_enrichment` + `waterfall_mobile_enrichment` + `api_waterfall_enrichment`

**Tables:** `AGG_TEAM_CREDITS` (FEATURE_TYPE), `FCT_TEAM_CREDIT_USE_DAILY`, `FCT_TEAM_CREDIT_LIMITS_DAILY`
**Always filter by `FEATURE_TYPE`**, not `CREDIT_TYPE` — CREDIT_TYPE has duplicate naming variants.

**Use this lens when:** "Credit consumption by product", "which credit types are underutilized?", "credit utilization rate"

---

## Routing Rules

| Question contains | Use lens | Default table |
|---|---|---|
| "product" with no further context | **Lens 1** (Feature Area) | AGG_TEAM_CREDITS or DIM_ACTIVE_TEAMS_DAILY |
| "plan", "edition", "tier", "Free/Basic/Pro/Custom" | **Lens 2** (Plan Edition) | FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS |
| "Inbound Router", "Dialer add-on", "add-on" | **Lens 3** (Add-on Module) | FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS |
| "credits", "consumption", "utilization" | **Lens 4** (Credit Product) | AGG_TEAM_CREDITS |
| "ARR by product" | Clarify: add-on ARR (Lens 3) or revenue by feature cohort (Lens 1 + FCT_MONTHLY_REVENUE join) |

**When ambiguous:** Default to Lens 1. If the answer would materially differ across lenses, ask one clarifying question:
> "Are you asking about feature areas (Email, Dialer, Enrichment), plan tiers (Free/Pro/Custom), or add-on products (Inbound Router, Dialer)?"

---

## What NOT to use for "product" questions

- **`PRODUCT_ID`** in FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS — raw plan identifier, hundreds of values, not exec-friendly. Use APOLLO_EDITION instead.
- **`PRICING_VARIANT`** — similarly granular, not mapped to exec vocabulary. Avoid for high-level product questions.
- **`CREDIT_TYPE`** in AGG_TEAM_CREDITS — has duplicate naming variants from two pipelines. Use `FEATURE_TYPE` instead (canonical and stable).

---

## CBR-Level Product Metrics (exec benchmarks)

From the FY27 AOP:
- **Dialer ARR target:** $1.7M
- **AI credits target:** 27M/mo
- **AI Assistant WAU target:** 10K paid core, 25% W4 retention
- **Enrichment/Waterfall credits target:** +402% YoY
- **AI Power-Up credits target:** +151% YoY

These are the benchmarks Bela-style exec questions are implicitly measuring against.
