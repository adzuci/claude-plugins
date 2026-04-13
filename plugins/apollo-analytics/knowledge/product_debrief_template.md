# Product Area Debrief — Standard Template

**Owner:** Leo Liu | **Updated:** 2026-03-20 | **Status:** Canonical — use for all product area debriefs

This is the standard execution framework for any product area general inquiry or debrief. Follow this order every time. Do not skip steps.

---

## Execution Order

### Step 1 — Data (Snowflake)

Pull usage metrics and KPIs for the product area first. Always first.

- Volume trend (WAT, sends, actions — whatever applies)
- Engagement trend (open, reply, CVR, activation rate)
- Quality metrics (bounce, error, churn — whatever applies)

**WAT source of truth:** WAT source varies by product area — always consult the **Key Tables by Product Area** table below before writing a WAT query. For most feature areas, the SoT is `DIM_ACTIVE_TEAMS_DAILY` (L7 feature columns). For AI Assistant, use `DIM_MONGO_ASSISTANT_THREADS`. For sequences/email, use `FCT_TEAM_EMAILER_MESSAGES_DAILY`. Do NOT default to `DIM_TEAMS_DAILY` as a catch-all WAT source — per CLAUDE.md guardrail, `DIM_TEAMS_DAILY` is not the canonical WAT source for adoption reporting. Credit, call, and support tables are supplementary — not for defining WAT.

**Credit volume source of truth:** Use `AGG_TEAM_CREDITS` filtered by `FEATURE_TYPE` (not `CREDIT_TYPE` — that column has duplicate naming variants across pipelines and is unreliable as a filter). For waterfall: `FEATURE_TYPE IN ('waterfall_enrichment', 'waterfall_mobile_enrichment', 'api_waterfall_enrichment')`. Standard exclusions: `ai_email`, `csv_export`, `crm_field_enrichment`, all CRM push types, `conversation`. See `domain/credit_types.md` for full FEATURE_TYPE taxonomy and `data-catalog/context/AGG_TEAM_CREDITS.md` for verified value list.

Label every finding: **"From Snowflake (TABLE_NAME):"**

---

### Step 2 — What Customers Are Saying

**This step is 100% customer language. No internal Slack, no team opinions.**
Sources: customer call transcripts (HVO, GTME, Gong, Gong Opportunity) and support tickets. All are direct customer voice.

#### Customer Calls (HVO + GTME + Gong + Gong Opportunity)

Show **both**:

**1. Volume + commonality** — aggregate by month. How often does this topic/feature appear?

| Month | Total Calls | Feature Discussed | Feature Created | Pain Point Mentions | Trend |
|-------|-------------|-------------------|-----------------|---------------------|-------|
| ...   | ...         | ...               | ...             | ...                 | ...   |

**2. Specific issues with verbatim examples** — do NOT summarize at a high level. For each pain point theme:
- State the specific problem (what breaks, what confuses, what's missing)
- Show the verbatim quote from the call note or pain point field
- State the frequency (N mentions in last 3 months)
- Map to a Jira issue if one exists

Example:
> **Top pain points (Sequences, last 3 months):**
> - **False daily sending limit** (14 mentions): Users report emails stop sending mid-day despite not hitting their actual limit. Apollo shows a "daily limit reached" error that clears itself the next day. → INCIDENT-26156 (false daily limit bug, Lok, in mitigation)
>   - Verbatim: "My sequences stopped sending at 11am every day this week — says limit reached but I only sent 40 emails"
>   - Verbatim: "Daily limit resets but never actually sends — been broken for 3 days"
> - **Manual vs automatic step confusion** (8 mentions): Users don't understand why some sequence steps send automatically while others require manual approval; contacts get stuck. → INCIDENT-26544 (stale index, Filip Szewczyk)
>   - Verbatim: "Set up sequence but contacts stuck on step 2 — never moved forward"
> - **Mailbox warmup / Gmail disconnect** (6 mentions): Gmail mailboxes disconnect after 24–48 hours and require re-auth; warmup period resets.
>   - Verbatim: "My Gmail keeps disconnecting — had to reconnect 4 times this week"

The standard is: anyone reading this should understand the exact user experience failure, not just the category.

Label: **"From customer calls (HVO / GTME / Gong):"** — always note which table each quote came from.

#### Support (DIM_SUPPORT_CONVERSATIONS)

- Monthly ticket volume for relevant topic categories (use `GENERAL_CONVERSATION_TOPIC`)
- Trend: growing / stable / declining
- Join to `ANALYTICS_DB.ANALYTICS_COMMON.CONVERSATION_SUMMARY` on `conversation_id` for full text if needed

Label: **"From Support (DIM_SUPPORT_CONVERSATIONS):"**

---

### Step 3 — Internal Signals (Slack + Jira)

**Internal team context only — NOT customer voice. Clearly separated from Step 2.**

#### Jira

Search active issues:
```
statusCategory in ("In Progress") AND text ~ "<topic>" AND updated >= -30d ORDER BY updated DESC
```

Group results:
- **Active incidents** (bugs/fires in production)
- **Product work in flight** (features, experiments, ramps)
- **Blocked**

Cross-reference BAT pain points to open Jira issues where the connection is clear.

Label: **"From Jira (PROJECT-KEY):"**

#### Slack

Search for product signals, launches, team discussions, feature announcements. Summarize — don't paste raw output.

Label: **"From Slack (#channel, date):"**

---

## Output Format

**Verdict always comes first** — both in the written output and in any HTML rendered version. Readers should see the bottom line before the supporting data.

```
### Verdict  ← ALWAYS FIRST
| Area | Status | Signal |
|------|--------|--------|
| Volume/adoption | ✅ Working / ⚠️ Watch / 🔴 Not working | [data point] |
| Engagement | ... | ... |
| Product investment | ... | ... |

**Bottom line:** [2-3 sentence summary — what's working, what's broken, what's the highest-leverage action]

---

### Step 1 — Data (Snowflake: TABLE_NAME)
[metrics table + trend narrative]

### Step 2 — Customer call signals (HVO + GTME + Gong + Gong Opportunity)
[volume + commonality table by month, broken out by source]
[top pain point themes — verbatim quotes tagged by source, frequency, Jira mapping]

### Step 2 — Support (DIM_SUPPORT_CONVERSATIONS)
[ticket volume by topic + trend]

### Step 3 — Slack signals
[key signals with #channel + date]

### Step 3 — Jira (active work)
**Incidents:** [key | summary | owner]
**In flight:** [key | summary | owner | status]
**Blocked:** [key | summary | owner]
```

**HTML rendering rule:** When generating HTML for a debrief, the Verdict section (`<!-- VERDICT -->`) must be the first `<div class="section">` after the header/badge block. Steps 1–3 follow below it.

**Methodology tab — required on every HTML debrief.** Always the last tab in the nav. Must contain:

1. **Data Sources** — every table queried, what it was used for, and the exact filter applied (including "0 results" on BAT sources — transparency is the point)
2. **Metric Definitions** — every metric shown defined precisely: what counts, which column, edge cases
3. **Key Queries** — the core SQL queries run, verbatim in `<pre>` blocks. Not pseudocode — the actual query.
4. **Known Caveats & Limitations** — selection bias, snapshot vs historical, missing data, n-size warnings, anything that changes how a reader interprets the numbers

The methodology tab is the audit trail. Anyone must be able to reproduce the analysis from it alone.

---

## Key Tables by Product Area

**WAT SoT by product area** — always start from `DIM_ACTIVE_TEAMS_DAILY` feature columns for adoption. Use secondary tables for deeper analysis (credit volume, send counts, call volume, etc.).

| Product Area | WAT Source (SoT) | WAT Column | Secondary Table (depth) | BAT Signal Column | Support Topic |
|---|---|---|---|---|---|
| Waterfall Enrichment | `DIM_ACTIVE_TEAMS_DAILY` | `ENRICHMENT_WATERFALL_USER_COUNTS_L7 > 0` | `AGG_TEAM_CREDITS` (credit volume), `DIM_MONGO_WATERFALL_STEP_RESULTS` (match rates) | PAIN_POINT ILIKE '%waterfall%' or '%enrichment%' | `CSV Enrichment`, `CRM Enrichment` |
| API Enrichment | `DIM_ACTIVE_TEAMS_DAILY` | `ENRICHMENT_API_USER_COUNTS_L7 > 0` | `AGG_USER_API_CALLS_DAILY` | `PAIN_POINT ILIKE '%api%'` | `API` |
| CSV Enrichment | `DIM_ACTIVE_TEAMS_DAILY` | `ENRICHMENT_CSV_USER_COUNTS_L7 > 0` | `AGG_TEAM_CREDITS` | — | `CSV Enrichment` |
| Outreach / Sequences | `DIM_TEAMS_DAILY` → `FCT_TEAM_EMAILER_MESSAGES_DAILY` | sends/opens/replies | `FCT_TEAM_EMAILER_MESSAGES_DAILY` | `SEQUENCE_CREATED`, `MAILBOX_LINKED` | `Emails`, `Sequences` |
| Dialer / Calls | `DIM_TEAMS_DAILY` → `FCT_TEAM_PHONE_CALLS_DAILY` | call counts | `FCT_TEAM_PHONE_CALLS_DAILY` | `IS_DIALER_DISCUSSED` | `Calls` |
| Inbound | `DIM_ACTIVE_TEAMS_DAILY` | *(no dedicated L7 column yet — use FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS inbound_fee for ARR)* | `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` — `inbound_fee` | `INBOUND_REACTION` | No dedicated topic — search `AI_GENERATED_SUMMARY` + `AI_ISSUE_SUMMARY` |
| AI Features | `DIM_ACTIVE_TEAMS_DAILY` | `AI_PLATFORM_USER_COUNTS_L7 > 0` | `TEAM_AI_ASSISTANT_DAILY` | `IS_AI_REFERRED` | *(search AI in topic)* |
| Credits | `DIM_ACTIVE_TEAMS_DAILY` | active teams with any credit usage | `FCT_TEAM_CREDITS_DAILY` | `CREDITS_BY_DEFAULT` | `Subscription and Usage Management` |
| Chrome Extension | `FCT_TEAM_FEATURE_USERS_DAILY` | — | — | — | `Chrome Extension` |
| CRM / Integrations | `DIM_SALESFORCE_APOLLO_TEAMS` | — | — | — | `Hubspot`, `API` |
| Apollo MCP Connector | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS` | `ACTIVE_COUNTS_MCP_API_CALLS > 0` or `FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL` | `ANALYTICS_DATAPLATFORM.FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` (controller/action breakdown, requires DEVELOPER_ROLE+) | PAIN_POINT + AI_GENERATED_SUMMARY ILIKE '%mcp%' OR '%claude%' | Search AI_GENERATED_SUMMARY for 'mcp', 'claude', 'oauth' |

---

## Customer Call Table Reference

| Table | What it covers | Key signal columns |
|---|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING` | HVO onboarding calls (~26K rows, daily refresh) | `AHA_FEATURES`, `FEATURE_DISCUSSED`, `PAIN_POINT`, `SEQUENCE_CREATED`, `MAILBOX_LINKED`, `IS_DIALER_DISCUSSED`, `IS_INBOUND_DISCUSSED`, `IS_AI_REFERRED`, `UPSELL_OPPORTUNITY` |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS` | Weekly aggregated signals per team | Downstream of HVO_CALLS_AI_PROCESSING |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS` | GTME call transcripts | LLM-extracted signals |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_CALLS_AI_ANALYSIS` | Gong calls | LLM-extracted signals |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` | Gong opportunity calls | LLM-extracted signals |

> Note: `ARRAY_CONTAINS` on `AHA_FEATURES` / `FEATURE_DISCUSSED` may not match due to VARIANT type casting. Use `SEQUENCE_CREATED`, `MAILBOX_LINKED`, and free-text `PAIN_POINT` LIKE filters as reliable alternatives.

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-20 | Created from outreach debrief session | Leo Liu |
| 2026-03-22 | Added WAT SoT rule: always use DIM_ACTIVE_TEAMS_DAILY feature L7 columns, never credit tables. Added waterfall row to key tables. Added full WAT-by-area table. | Leo Liu |
| 2026-03-24 | Added MCP Connector row to key tables; DIM_USERS (ACTIVE_COUNTS_MCP_API_CALLS) is SoT, FCT_MONGO_HTTP_REQUESTS_V3_RT_VW for controller-level breakdown | Leo |
