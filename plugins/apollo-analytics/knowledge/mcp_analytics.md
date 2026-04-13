# MCP Connector Analytics

**Owner:** Leo Liu | **Created:** 2026-03-24 | **Status:** Active — MCP launched 2026-02-23

Context and patterns for analyzing Apollo's MCP (Model Context Protocol) connector — the Claude integration that lets AI agents call Apollo's API natively. GA launched with Anthropic partnership.

---

## What MCP Is

Apollo ships an MCP server that lets Claude (and other AI clients) call Apollo's API natively — prospecting, enrichment, CRM reads/writes — without leaving the AI interface.

### What Claude CAN do via MCP
- People search / prospecting
- Person and org enrichment
- CRM reads (contacts, accounts, opportunities)
- CRM writes (create/update contacts and accounts)
- Add contacts to existing sequences (`emailer_campaigns/add_contact_ids`)

### What Claude CANNOT do via MCP (web UI only)
- Create email sequences or campaigns from scratch
- Send emails
- Manage contact lists
- View analytics dashboards
- Manage integrations
- Access deals pipeline

This boundary matters for analysis: MCP users who show high sequence activation likely did creation in web and execution touches via MCP.

---

## Data Sources

### Primary: DIM_USERS (ANALYTICS_DATASCIENCE)
Shyam added MCP-specific columns 2026-03-23. Use these for standard MCP adoption analytics.

| Column | Description |
|---|---|
| `FIRST_ACTIVE_DATE_MCP_API_CALLS` | First day user made an MCP API call |
| `ACTIVE_DAYS_MCP_API_CALLS` | Total days active via MCP |
| `ACTIVE_COUNTS_MCP_API_CALLS` | Total MCP API call count |
| `FIRST_ACTIVE_DATE_API_CALLS` | Overall API (MCP + partner) |
| `ACTIVE_DAYS_API_CALLS` | Overall API active days |

MCP user definition: `FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL`

DIM_TEAMS has the same columns at team level.

### Secondary: FCT_MONGO_HTTP_REQUESTS_V3_RT_VW (ANALYTICS_DATAPLATFORM)
Use for request-level drill-downs: what controllers/actions MCP users are hitting.

- **Schema:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM` (NOT ANALYTICS — confirmed via live query)
- **MCP filter:** `USER_AGENT = 'Apollo-MCP/1.0'`
- **Key columns:** `CONTROLLER`, `ACTION`, `USER_ID`, `TEAM_ID`, `REQUEST_TIMESTAMP`
- **Permission:** Requires DEVELOPER_ROLE or higher
- **Gotcha:** Real-time, unbounded — always filter by `REQUEST_TIMESTAMP` and use LIMIT

---

## Controller → Category Mapping

| Controller pattern | Category |
|---|---|
| `people/*search*` | Prospecting |
| `people/*match*`, `people/bulk_match` | Person Enrichment |
| `organizations/*` | Org Enrichment |
| `contacts/*`, `accounts/*` | CRM Management |
| `emailer_campaigns/*` | Sequence (read/add contacts — not create) |

---

## Cohort Design — Key Principles

1. **Fixed observation window** — always restrict to users with ≥N days of tenure as of analysis date. MCP launched 2026-02-23, so cohort starts there. For 14-day window: `signup_date <= CURRENT_DATE - 14`.

2. **Lookalike matching** — compare MCP users to non-MCP peers from same strata: `signup_week × IS_PAID_IND × ACCOUNT_SUB_SEGMENT`. Prevents apples-to-oranges comparisons.

3. **Employee filter** — always `IS_APOLLO_EMPLOYEE_IND = FALSE`.

See `domain/sql_patterns.md` for canonical query implementations.

---

## Key Findings — Feb 23–Mar 10 Cohort (14-day window)

From the MCP User Onboarding & Activation analysis (Leo, 2026-03-24):

- **1,816 MCP users** in 2.5 weeks post-launch
- **818 (45%) signed up Day 0** — came for MCP, not the web product
- **78% free, 68% VSB** at signup
- **FTP lift: 4–28× vs matched peers** depending on segment (VSB-Enriched 24.5% vs 5.7% peers)
- **Median 0–2 days from MCP first use to paid upgrade** — likely credit-ceiling driven
- **84% of MCP users never touched web features** in 14-day window → net-new user type, not cannibalization
- **Top MCP workflow:** prospect (people/search) → enrich (people/match) → save to CRM (contacts/create)
- **111 users added contacts to existing sequences via MCP** — MCP CAN interact with sequences (just can't create them)

---

## Known Issues (as of Mar 2026)

### OAuth token caching bug (HIGH PRIORITY — ~10+ support tickets)
Users upgrading from free to Basic/Pro still get "not accessible with this access token on a free plan" errors on `/v1/people/match` and `/v1/mixed_people/api_search` until they manually re-authenticate. Customers don't know to re-auth. Likely churning newly converted users silently.

### Plan access restriction
MCP is currently gated to Org plan. Basic/Pro users (~80–90K paid teams) are locked out. Multiple support tickets from confused users. Competitive risk: Lusha gives MCP on all plans.

### Prospecting filter gap
MCP doesn't expose full filter set (industry, tech stack, headcount ranges) available in web UI. Flagged in both support tickets and GTME call transcripts.

### Custom field limitation
Only standard fields (first_name, last_name, email) are writable via MCP. Custom fields blocked.

---

## BAT Signals for MCP

When querying BAT assets for MCP context:

**HVO_CALLS_AI_PROCESSING:** Filter `PAIN_POINT ILIKE '%mcp%' OR AHA_MOMENT ILIKE '%claude%' OR CUSTOMER_INTENDED_USE_CASE ILIKE '%api%'`

**GTME_CALLS_AI_ANALYSIS:** Filter `COMMENTS_ON_AI ILIKE '%mcp%' OR COMMENTS_ON_AI ILIKE '%claude%'`

**DIM_SUPPORT_CONVERSATIONS (ANALYTICS schema):** Filter `AI_GENERATED_SUMMARY ILIKE '%mcp%' OR AI_GENERATED_SUMMARY ILIKE '%claude%' OR AI_GENERATED_SUMMARY ILIKE '%oauth%'`. Date column: `CONVERSATION_CREATED_AT` (verify — `CONVERSATION_MAIN_CATEGORY` is unreliable, often NULL).

---

## Competitive Context

- **ZoomInfo:** Launched their own Claude MCP connector, Feb 2026
- **Clay:** Launched interactive MCP App, Jan 2026. GTME signals: Clay wins on visual automation UX; Apollo MCP wins on data quality and prospecting depth.
- **Lusha:** MCP available on all plans including free (competitive risk given Apollo's Org-only restriction)

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created from MCP onboarding analysis session | Leo Liu (via Jarvis) |
