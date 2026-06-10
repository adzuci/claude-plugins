# MCP Connector Analytics

**Owner:** Leo Liu | **Created:** 2026-03-24 | **Status:** Active — MCP launched 2026-02-23

Context and patterns for analyzing Apollo's MCP (Model Context Protocol) connector — the Claude integration that lets AI agents call Apollo's API natively. GA launched with Anthropic partnership.

______________________________________________________________________

## 🔱 Source of Truth — MCP Product Operating Metrics & Health (Hex)

**Canonical dashboard:** [v0 — MCP Product Operating Metrics & Health](https://app.hex.tech/apollo/hex/v0-MCP-Product-Operating-Metrics-Health-032tHIa3sHMEzsCAk5F3af)

**Maintainer:** Mounica Sonikar (Hydro)

**Use this rule:** Any analytical question about MCP — adoption, usage, credit consumption, ARR attribution, segment cuts, surface attribution — MUST reconcile with the data sources defined in this Hex. If a Snowflake query produces a number that disagrees with the Hex, the Hex is correct and the query is wrong (or measuring something different). Document the reconciliation; do not publish the divergent number.

**Why this matters:**

- The Hex is the version that goes to product/exec audiences. Internal Snowflake numbers must roll up to it, not contradict it.
- Surface attribution for credit consumption uses `FCT_MONGO_CREDIT_USAGE_DETAILS.SURFACE = 'mcp'` — not `FCT_MONGO_CREDIT_USAGES`, not the request-level join through `FCT_MONGO_HTTP_REQUESTS_V3`. Multiple analysts have produced inflated MCP numbers by joining through the upstream tables; the canonical surface column avoids that.
- MCP user/team identification, adoption windows, and active-user definitions are codified in the Hex SQL. Reproduce them, do not invent them.

**Before answering any MCP question:**

1. Open the Hex and find the canonical metric/definition the question maps to.
1. Use the same source tables and filters in your Snowflake query.
1. If your number diverges from the Hex by more than rounding, stop and reconcile before publishing.

**Catalog companion:** see [`data-catalog/context/FCT_MONGO_CREDIT_USAGE_DETAILS.md`](../data-catalog/context/FCT_MONGO_CREDIT_USAGE_DETAILS.md) for the surface-attribution table — full schema, the three-axis attribution framework (API / sidekiq / UI), and the SURFACE-NULL rate caveats from Brighid's 2026-04-17 trust audit.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## Controller → Category Mapping

| Controller pattern | Category |
|---|---|
| `people/*search*` | Prospecting |
| `people/*match*`, `people/bulk_match` | Person Enrichment |
| `organizations/*` | Org Enrichment |
| `contacts/*`, `accounts/*` | CRM Management |
| `emailer_campaigns/*` | Sequence (read/add contacts — not create) |

______________________________________________________________________

## Cohort Design — Key Principles

1. **Fixed observation window** — always restrict to users with ≥N days of tenure as of analysis date. MCP launched 2026-02-23, so cohort starts there. For 14-day window: `signup_date <= CURRENT_DATE - 14`.

1. **Lookalike matching** — compare MCP users to non-MCP peers from same strata: `signup_week × IS_PAID_IND × ACCOUNT_SUB_SEGMENT`. Prevents apples-to-oranges comparisons.

1. **Employee filter** — always `IS_APOLLO_EMPLOYEE_IND = FALSE`.

See `domain/sql_patterns.md` for canonical query implementations.

______________________________________________________________________

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

______________________________________________________________________

## Known Issues (as of Mar 2026)

### OAuth token caching bug (HIGH PRIORITY — ~10+ support tickets)

Users upgrading from free to Basic/Pro still get "not accessible with this access token on a free plan" errors on `/v1/people/match` and `/v1/mixed_people/api_search` until they manually re-authenticate. Customers don't know to re-auth. Likely churning newly converted users silently.

### ~~Plan access restriction~~ — RESOLVED (confirmed Apr 2026)

~~MCP is currently gated to Org plan.~~ Data as of Apr 2026 confirms MCP is available across all paid plan tiers. Plan distribution of active MCP users: Starter ~45%, Basic ~25%, Professional ~24%, Custom ~3%. No Org-only gating observed in usage data.

### Prospecting filter gap

MCP doesn't expose full filter set (industry, tech stack, headcount ranges) available in web UI. Flagged in both support tickets and GTME call transcripts.

### Custom field limitation

Only standard fields (first_name, last_name, email) are writable via MCP. Custom fields blocked.

______________________________________________________________________

## BAT Signals for MCP

When querying BAT assets for MCP context:

**HVO_CALLS_AI_PROCESSING:** Filter `PAIN_POINT ILIKE '%mcp%' OR AHA_MOMENT ILIKE '%claude%' OR CUSTOMER_INTENDED_USE_CASE ILIKE '%api%'`

**GTME_CALLS_AI_ANALYSIS:** Filter `COMMENTS_ON_AI ILIKE '%mcp%' OR COMMENTS_ON_AI ILIKE '%claude%'`

**DIM_SUPPORT_CONVERSATIONS (ANALYTICS schema):** Filter `AI_GENERATED_SUMMARY ILIKE '%mcp%' OR AI_GENERATED_SUMMARY ILIKE '%claude%' OR AI_GENERATED_SUMMARY ILIKE '%oauth%'`. Date column: `CONVERSATION_CREATED_AT` (verify — `CONVERSATION_MAIN_CATEGORY` is unreliable, often NULL).

______________________________________________________________________

## Competitive Context

- **ZoomInfo:** Launched their own Claude MCP connector, Feb 2026
- **Clay:** Launched interactive MCP App, Jan 2026. GTME signals: Clay wins on visual automation UX; Apollo MCP wins on data quality and prospecting depth.
- **Lusha:** MCP available on all plans including free (competitive risk given Apollo's Org-only restriction)

______________________________________________________________________

## MCP New ARR Attribution — Moderate Correlation Logic

**Owner:** Mounica Sonikar | **Added:** 2026-04-15

### Definition

**Moderate correlation:** A team is considered MCP-attributed if their `FIRST_PAID_DATE` falls within **±7 days** of their `FIRST_ACTIVE_DATE_MCP_API_CALLS`.

```
ABS(DATEDIFF('day', first_paid_date, first_active_date_mcp_api_calls)) <= 7
```

New ARR = ARR at the time the team first paid (`CHANGE_CATEGORY IN ('new', 'new_reactivated')`).

### Canonical Query

```sql
WITH mcp_attributed AS (
    SELECT
        apollo_team_id,
        first_paid_date,
        first_active_date_mcp_api_calls,
        DATEDIFF('day', first_paid_date, first_active_date_mcp_api_calls) AS days_new_to_mcp
    FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS
    WHERE first_paid_date IS NOT NULL
      AND first_active_date_mcp_api_calls IS NOT NULL
      AND ABS(DATEDIFF('day', first_paid_date, first_active_date_mcp_api_calls)) <= 7
)
SELECT
    DATE_TRUNC('week', r.date_period)   AS week_start,
    COUNT(DISTINCT r.apollo_team_id)    AS new_teams,
    SUM(r.arr)                          AS net_new_arr
FROM mcp_attributed m
JOIN ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE r
    ON r.apollo_team_id = m.apollo_team_id
   AND r.change_category IN ('new', 'new_reactivated')
   AND r.is_parent_account = FALSE
GROUP BY 1
ORDER BY 1
;
```

### Results as of 2026-04-15

| Week | New Teams | Net New ARR |
|---|---|---|
| Feb 16 | 15 | $27K |
| Feb 23 | 103 | $112K |
| Mar 2 | 181 | $173K |
| Mar 9 | 306 | $351K |
| Mar 16 | 392 | $437K |
| Mar 23 | 515 | $540K |
| Mar 30 | 389 | $395K |
| Apr 6 | 414 | $465K |
| Apr 13 (partial) | 138 | $162K |

- **8 complete weeks total:** ~$2.5M cumulative
- **Avg per week:** ~$312K
- **13-week run rate:** ~$4.1M

> ⚠️ **Correlation only — not causal attribution.** These figures reflect teams whose first paid date fell within ±7 days of MCP activation. MCP adoption and paid conversion are both downstream of high-intent signal. DiD and RD analyses found no detectable causal effect of MCP on ARR in the 2-month post-launch window.

### Notes

- Snapshot as of 2026-04-15 — run the canonical query above for current numbers.
- MCP first appears in data Feb 16, 2026 (consistent with GA launch Feb 23)
- No `new_reactivated` teams observed in this cohort as of Apr 2026
- `days_new_to_mcp` negative = team became paid before MCP activation; positive = after

______________________________________________________________________

## Product Debrief Framing Rules — MANDATORY for any `/product-debrief mcp` run

**Owner:** Mounica Sonikar | **Established:** 2026-05-06 (codified after the May 4 MCP debrief iteration)

These rules apply *every time* anyone runs `/product-debrief` on MCP. They override generic debrief defaults. Do not relitigate them per session — they are the team's established decisions.

### 1. Structure: 2 steps, not 3

- **Step 1 — Numbers** (Snowflake, Hex-reconciled): adoption, requests, credits, ARR, cohort flow, OAuth-app split.
- **Step 2 — Customer voice** (BAT calls + support tickets): themes only, not full ticket dumps. Each theme gets a `❌ No Jira ticket` badge if untracked.
- **Do NOT include a "Step 3 · Internal Signals" tab.** Internal Slack posts and team-update channel chatter do not belong in a published debrief — they're noise to execs and bake stale gossip into the artifact. If something internal is load-bearing, fold it into the bottom-line narrative instead.

### 2. Source-of-Truth banner — mandatory at top

Every MCP debrief HTML must open with a prominent banner linking to the [v0 MCP Hex](https://app.hex.tech/apollo/hex/v0-MCP-Product-Operating-Metrics-Health-032tHIa3sHMEzsCAk5F3af) and stating that Hex wins any disagreement. Use this exact banner pattern (or visually equivalent):

```
🔱 Source of truth for all MCP analytics: <link to v0 Hex>. Every number in this debrief reconciles to that dashboard's filters and definitions per domain/mcp_analytics.md §Source of Truth. If a downstream query disagrees with the Hex, the Hex wins.
```

### 3. Acquisition vs stickiness — keep them separate

MCP is a **real acquisition channel** (~$4M cumulative new ARR through Apr 27, moderate-correlation methodology). MCP is **not a stickiness lever** (causal NRR analyses — RDD on new customers, DiD+PSM on existing — both null on retention). Do not collapse the two. The acquisition story and the retention story have different evidence and different implications. Cite the causal NRR analysis (`mcp_causal_nrr_rdd_20260430`) when scoping the null result; do not extrapolate it to acquisition.

### 4. Credit decline framing — "Credit Decline Analysis," not "Cap-Out"

When credit consumption drops, name the section **"Credit Decline Analysis"** and decompose using the cohort flow framework: NEW / STABLE-or-GREW / DECLINED / CHURNED, split by paid/free. Cap-utilization is one *possible* contributor to the DECLINED bucket — investigate it as a hypothesis, not a foregone conclusion.

### 5. No prescriptive product fixes from a single ticket

Customer-voice themes describe a pattern. They do not authorize prescribing a product fix (e.g. "the fix is à-la-carte credit add-ons") unless a separate analysis or PM-level decision supports it. Describe the friction and quantify it; let product own the prescription.

### 6. No internal-source attributions in published output

Do not name Slack-poster names (e.g. "per Jon Jenkins' post in #mcp-team-updates") in the debrief. Internal source attributions are appropriate in worklogs and provisional notes, not in published artifacts that travel to execs and external stakeholders.

### 7. Default omissions (include only if specifically asked)

- Credit-type breakdown by FEATURE_TYPE (Lead/Export/Email/AI/Direct dial) — adds noise without changing the headline; omit unless the question is specifically about credit-type mix.
- Multi-seat expansion verdict row — DAU/DAT for MCP teams vs Apollo-overall typically differs by \<0.1, which isn't material; omit unless a meaningful gap shows up.
- OAuth caching bug section — known issue with low ticket volume; mention in a single line if needed, not as a verdict-level finding.

### 8. Numbers reconcile to Hex first (pre-flight, not post-flight)

Before building any new MCP debrief section, run the canonical filter against the Hex headline numbers (WAT, requests, credits) for the latest week and confirm match within rounding. If they don't match, stop and reconcile *before* building downstream cuts. Canonical filter:

```
USER_AGENT ILIKE 'Apollo-MCP%' AND GODMODE = FALSE AND NUMBER_OF_SUCCESSFUL_REQUESTS > 0
```

Omitting `NUMBER_OF_SUCCESSFUL_REQUESTS > 0` inflates WAT by ~10% — caught in the v1/v2 pass of the May 4 debrief.

### 9. Queries tab — mandatory

Every MCP debrief HTML must include a Queries tab with the full SQL backing every claim. Methodology section explains *what* was done; Queries tab lets a reviewer reproduce it.

### 10. Provenance for cited analyses

When citing the causal NRR result or any other peer-reviewed analysis, link to `analysis/registry.json` entry and the published GCS report URL. Provisional / unreviewed analyses must carry the standard "Jarvis-generated, not peer-reviewed" caveat per CLAUDE.md.

______________________________________________________________________

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created from MCP onboarding analysis session | Leo Liu (via Jarvis) |
| 2026-04-15 | Added moderate correlation ARR attribution methodology + canonical query | Mounica Sonikar (via Jarvis) |
| 2026-04-28 | Corrected Plan access restriction known issue — confirmed via data that MCP is available on all plan tiers, not Org-only | Mounica Sonikar (via Jarvis) |
| 2026-05-06 | Added Product Debrief Framing Rules (mandatory for all `/product-debrief mcp` runs) — codified May 4 debrief decisions: 2-step structure, Source-of-Truth banner, acquisition-vs-stickiness separation, default omissions, Hex-first reconciliation | Mounica Sonikar (via Jarvis) |
