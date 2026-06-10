# Product Area Debrief — Standard Template

**Owner:** Leo Liu | **Updated:** 2026-03-20 | **Status:** Canonical — use for all product area debriefs

This is the standard execution framework for any product area general inquiry or debrief. Follow this order every time. Do not skip steps.

______________________________________________________________________

## Execution Order

### Step 0.5 — ARR Pacing vs Plan (CONDITIONAL — dialer and inbound only)

**Only include this card when the product area is `dialer` or `inbound`** — the only areas with add-on ARR. Skip entirely for all other product areas (sequences, credits, api, enrichment, ai, prospecting, etc.). Override with `--pacing` to force-include or `--no-pacing` to force-skip.

When applicable, include a compact ARR pacing card that frames the company context. This appears in the HTML between the verdict and Step 1.

**Query:** Run `sql/arr_pacing_vs_plan.sql` (canonical). It returns monthly ARR from FCT_DAILY_REVENUE (IS_PARENT_ACCOUNT = TRUE) with FY27 quarterly targets inlined.

**FY27 quarterly targets** (from `domain/annual_targets.md`):
| Quarter | End month | Target |
|---|---|---|
| Q1 | Apr 2026 | $205.6M |
| Q2 | Jul 2026 | $230.3M |
| Q3 | Oct 2026 | $258.3M |
| Q4 | Jan 2027 | $278.1M |

**HTML output:** Render as a compact card above the tab bar, below the verdict:

```html
<div class="arr-pacing-card">
  <div class="arr-pacing-title">ARR Pacing vs Plan</div>
  <div class="arr-pacing-grid">
    <div class="arr-stat">
      <div class="arr-stat-label">Current ARR</div>
      <div class="arr-stat-value">$XXX.XM</div>
    </div>
    <div class="arr-stat">
      <div class="arr-stat-label">Next Target (QX)</div>
      <div class="arr-stat-value">$XXX.XM</div>
    </div>
    <div class="arr-stat">
      <div class="arr-stat-label">vs Plan</div>
      <div class="arr-stat-value [ahead|behind]">+$XX.XM</div>
    </div>
    <div class="arr-stat">
      <div class="arr-stat-label">MoM Net New</div>
      <div class="arr-stat-value">$XX.XM</div>
    </div>
  </div>
  <div class="arr-pacing-sparkline">[last 6 months mini bar chart]</div>
</div>
```

CSS:

```css
.arr-pacing-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: 14px 18px; margin: 12px 0 16px 0; }
.arr-pacing-title { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 10px; }
.arr-pacing-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.arr-stat-label { font-size: 10px; color: var(--dim); margin-bottom: 2px; }
.arr-stat-value { font-size: 18px; font-weight: 700; color: var(--text); }
.arr-stat-value.ahead { color: var(--accent2); }
.arr-stat-value.behind { color: var(--accent3); }
```

**Area-specific ARR overrides:**

When an area has an override below, run that query **instead of** the company-wide `arr_pacing_vs_plan.sql`. The card shape stays the same but the title, stats, and source change.

| Area | Source | Card title | Query |
|---|---|---|---|
| inbound | `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` | Inbound Add-On ARR | See below |

**Inbound ARR query** (uses `additional_fee_by_source:"inbound"` with ARR formula `fee * 12 / billing_interval_months`):

```sql
WITH weekly_inbound_arr AS (
    SELECT
        DATE_TRUNC('week', DATE(date_time_string))::date AS week_start
        , COUNT(DISTINCT team_id) AS active_teams
        , SUM(12 * additional_fee_by_source:"inbound"::number / billing_interval_months) AS total_inbound_arr
    FROM analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports
    WHERE additional_fee_by_source:"inbound"::number > 0
        AND DAYOFWEEK(DATE(date_time_string)) = 6  -- Saturday snapshots
        AND DATE(date_time_string) >= DATEADD('week', -30, CURRENT_DATE())
        AND team_id NOT IN ('68e6fb07946dcf000d2e3516', '620210171b9d04008e2ac0e0')
    GROUP BY 1
)

SELECT
    week_start
    , active_teams
    , ROUND(total_inbound_arr, 0) AS total_inbound_arr
    , LAG(total_inbound_arr) OVER (ORDER BY week_start) AS prior_week_arr
    , ROUND(total_inbound_arr - COALESCE(LAG(total_inbound_arr) OVER (ORDER BY week_start), 0), 0) AS wow_net_new_arr
FROM weekly_inbound_arr
ORDER BY week_start
```

Render as the same 4-stat card with: **Current Inbound ARR** (latest week), **Active Teams**, **WoW Net New ARR**, and a weekly sparkline.

**Skip condition:** Only skip if the user explicitly says `--no-pacing`. Otherwise, always include.

______________________________________________________________________

### Step 1 — Data (Snowflake)

Pull usage metrics and KPIs for the product area first. Always first.

- Volume trend (WAT, sends, actions — whatever applies)
- Engagement trend (open, reply, CVR, activation rate)
- Quality metrics (bounce, error, churn — whatever applies)

**WAT source of truth:** Always pull WAT from `DIM_TEAMS_DAILY` (L7 columns) using a fixed day-of-week anchor (Sunday): `COUNT(DISTINCT apollo_team_id) WHERE *_USER_COUNTS_L7 > 0 AND DAYNAME(DATE) = 'Sun'`. `DIM_TEAMS_DAILY`, `DIM_USERS_DAILY`, and `DIM_USERS` are the Snowflake translations of the metrics DB and are the SoT for all standard usage reporting. Credit tables (AGG_TEAM_CREDITS, FCT_TEAM_CREDIT_USE_DAILY), call tables, and support tables are supplementary — for deeper dives only, not for defining WAT or any adoption metric.

**Credit volume source of truth:** Use `AGG_TEAM_CREDITS` filtered by `FEATURE_TYPE` (not `CREDIT_TYPE` — that column has duplicate naming variants across pipelines and is unreliable as a filter). For waterfall: `FEATURE_TYPE IN ('waterfall_enrichment', 'waterfall_mobile_enrichment', 'api_waterfall_enrichment')`. Standard exclusions: `ai_email`, `csv_export`, `crm_field_enrichment`, all CRM push types, `conversation`. See `domain/credit_types.md` for full FEATURE_TYPE taxonomy and `data-catalog/context/AGG_TEAM_CREDITS.md` for verified value list.

Label every finding: **"From Snowflake (TABLE_NAME):"**

______________________________________________________________________

### Step 2 — What Customers Are Saying

**This step is 100% customer language. No internal Slack, no team opinions.**
Sources: customer call transcripts (HVO, GTME, Gong, Gong Opportunity) and support tickets. All are direct customer voice.

#### Customer Calls (HVO + GTME + Gong + Gong Opportunity)

Show **both**:

**1. Volume + commonality** — aggregate by month. How often does this topic/feature appear?

| Month | Total Calls | Feature Discussed | Feature Created | Pain Point Mentions | Trend |
|-------|-------------|-------------------|-----------------|---------------------|-------|
| ... | ... | ... | ... | ... | ... |

**2. Specific issues with verbatim examples** — do NOT summarize at a high level. For each pain point theme:

- State the specific problem (what breaks, what confuses, what's missing)
- Show the verbatim quote from the call note or pain point field
- State the frequency (N mentions in last 3 months)
- Map to a Jira issue if one exists

Example:

> **Top pain points (Sequences, last 3 months):**
>
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

______________________________________________________________________

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

______________________________________________________________________

## Output Format

**Verdict always comes first** — both in the written output and in any HTML rendered version. Readers should see the bottom line before the supporting data.

### Visual requirements (ALL debriefs)

Every HTML debrief must include these. Tables-only output is a regression — see the AI Platform debrief (`teammates/pubudu_wariyapola/Product_Debrief/AI_Platform_Debrief_2026_04_22/ai_platform_debrief.html`) as the exemplar.

1. **Chart.js** — `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>` in `<head>`
1. **KPI summary cards** — 4–6 large-number cards at the top of the Data tab (metric label, current value, WoW delta). Use `.kpi-row` / `.kpi-card` grid.
1. **Interactive trend charts** — at least one Chart.js line chart for the primary metric trend in the Data tab. Dark-mode colors: grid `rgba(46,50,72,0.5)`, ticks `#8b8fa3`, primary line `#6c63ff`, secondary `#00d4aa`.
1. **Takeaways tab** — second-to-last tab (before Methodology). 2×2 card grid: What We Know / Risks & Open Questions / Strategic Bets / Recommended Next Analyses.

### Tab structure (single-area)

Tabs: **Data** | **Customer Voice** | **Internal Signals** | **Takeaways** | **Methodology**

```
Verdict  ← ALWAYS ABOVE TABS
| Metric | Current | Prior | WoW Δ | vs Target | Why it moved |

**Bottom line:** [2-3 sentence TL;DR]

---
[ARR Pacing Card]
---

[Tab: Data]
  KPI summary cards (4-6 headline metrics)
  Chart.js trend chart(s)
  Data tables with step labels + source attribution

[Tab: Customer Voice]
  Call themes — verbatim quotes, source + date, Jira coverage badges
  Support tickets — volume trend + excerpts

[Tab: Internal Signals]
  Jira cross-reference (Covered / Partial / Gap tiers)
  Slack signals with #channel + date

[Tab: Takeaways]
  What We Know / Risks / Strategic Bets / Next Analyses (2×2 grid)

[Tab: Methodology]
  Data Sources / Metric Definitions / Key Queries / Caveats
```

**HTML rendering rule:** When generating HTML for a debrief, the Verdict section (`<!-- VERDICT -->`) must be the first `<div class="section">` after the header/badge block.

**Methodology tab — required on every HTML debrief.** Always the last tab in the nav. Must contain:

1. **Data Sources** — every table queried, what it was used for, and the exact filter applied (including "0 results" on BAT sources — transparency is the point)
1. **Metric Definitions** — every metric shown defined precisely: what counts, which column, edge cases
1. **Key Queries** — the core SQL queries run, verbatim in `<pre>` blocks. Not pseudocode — the actual query.
1. **Known Caveats & Limitations** — selection bias, snapshot vs historical, missing data, n-size warnings, anything that changes how a reader interprets the numbers

The methodology tab is the audit trail. Anyone must be able to reproduce the analysis from it alone.

______________________________________________________________________

## Key Tables by Product Area

**WAT SoT by product area** — always start from `DIM_ACTIVE_TEAMS_DAILY` feature columns for adoption. Use secondary tables for deeper analysis (credit volume, send counts, call volume, etc.).

| Product Area | WAT Source (SoT) | WAT Column | Secondary Table (depth) | BAT Signal Column | Support Topic |
|---|---|---|---|---|---|
| Waterfall Enrichment | `DIM_ACTIVE_TEAMS_DAILY` | `ENRICHMENT_WATERFALL_USER_COUNTS_L7 > 0` | `AGG_TEAM_CREDITS` (credit volume), `DIM_MONGO_WATERFALL_STEP_RESULTS` (match rates) | PAIN_POINT ILIKE '%waterfall%' or '%enrichment%' | `CSV Enrichment`, `CRM Enrichment` |
| API Enrichment | `DIM_ACTIVE_TEAMS_DAILY` | `ENRICHMENT_API_USER_COUNTS_L7 > 0` | `AGG_USER_API_CALLS_DAILY` | `PAIN_POINT ILIKE '%api%'` | `API` |
| CSV Enrichment | `DIM_ACTIVE_TEAMS_DAILY` | `ENRICHMENT_CSV_USER_COUNTS_L7 > 0` | `AGG_TEAM_CREDITS` | — | `CSV Enrichment` |
| Outreach / Sequences | `USER_SEQUENCE_ACTIONS_DAILY` (WAU); `SEQUENCES` + `DIM_USERS` (creation volume by method); `FCT_MONGO_EMAILER_MESSAGES` (send volume). See canonical queries in `domain/sequences.md` §Reference queries. **Always split by segment + tenure** — older users engage disproportionately more. | sends/opens/replies; creation volume; email_per_team density | `FCT_TEAM_EMAILER_MESSAGES_DAILY` (daily rollup); `FCT_MONGO_EMAILER_MESSAGES` (message-level); deliverability context in `domain/deliverability.md` | `SEQUENCE_CREATED`, `MAILBOX_LINKED` | `Emails`, `Sequences` |
| Dialer / Calls | `FCT_MONGO_PHONE_CALLS` (per-call SoT — `TWILIO_CALL_SID IS NOT NULL`, internal teams excluded) + `DIM_TEAMS_DAILY` (segmentation) + `USER_DIALER_ACTIONS_DAILY` (user activity). **Do NOT use `FCT_TEAM_PHONE_CALLS_DAILY` or any `PLAYGROUND.*` table.** Supporting: `FCT_AMPLITUDE_EVENTS` (phone-number events), HVO BAT, parallel-session tables, add-on tables. See `domain/dialer.md` §Canonical tables and §Credits — three FEATURE_TYPEs. | call counts; mode mix split by add-on status; `phone_call` credits (call) vs `direct_dial` (number download) vs `dialer_phone_number` (number purchase) | Build team-day rollup from `FCT_MONGO_PHONE_CALLS` directly. | `IS_DIALER_DISCUSSED` | `Calls` |
| Inbound | `USER_INBOUND_ACTIONS_DAILY` (schema: `ANALYTICS_DATASCIENCE`) — no L7 column in `DIM_ACTIVE_TEAMS_DAILY`; use canonical queries in `domain/inbound.md` §Reference queries | WAU/WAT by action type (7-day window join to `DIM_USERS_DAILY`); team activation (28-day); week-4 retention; setup completion; quota exhaustion | `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` — `inbound_fee` (ARR); `FCT_AMPLITUDE_EVENTS` — `event_type_id` 863902943/879431855 (setup + limits) | `INBOUND_REACTION` | No dedicated topic — search `AI_GENERATED_SUMMARY` + `AI_ISSUE_SUMMARY` |
| AI Features | `DIM_ACTIVE_TEAMS_DAILY` | `AI_PLATFORM_USER_COUNTS_L7 > 0` | `TEAM_AI_ASSISTANT_DAILY` | `IS_AI_REFERRED` | *(search AI in topic)* |
| Credits | `DIM_ACTIVE_TEAMS_DAILY` | active teams with any credit usage | `FCT_TEAM_CREDITS_DAILY` | `CREDITS_BY_DEFAULT` | `Subscription and Usage Management` |
| Prospecting / GenPipe | `DIM_ACTIVE_TEAMS_DAILY` — `USE_CASE_GENPIPE_TRADITIONAL_USER_COUNTS_L7 > 0` / `USE_CASE_GENPIPE_NEXTGEN_USER_COUNTS_L7 > 0`. Sunday anchor. See canonical queries in `domain/prospecting.md` §Reference queries. **Always show Traditional vs. NextGen separately + feature-level breakdown (13 columns).** | Traditional WAT; NextGen WAT; 13-feature breakdown; F14D Habit RA Rate; CSV credits/mo | `AGG_USER_GENPIPE_ACTIVATION_EVENTS_DAILY` (activation); `AGG_TEAM_CREDITS` WHERE `FEATURE_TYPE = 'csv_enrichment_email'` (CSV credits OKR: 7M/mo); sub-feature deep dives in `domain/sequences.md`, `domain/dialer.md` | `PAIN_POINT ILIKE '%prospecting%'` OR `CUSTOMER_INTENDED_USE_CASE ILIKE '%prospecting%'` | No dedicated topic — search `AI_GENERATED_SUMMARY` + `AI_ISSUE_SUMMARY` for "prospecting", "lead generation", "pipeline" |
| Chrome Extension | `FCT_TEAM_FEATURE_USERS_DAILY` | — | — | — | `Chrome Extension` |
| CRM / Integrations | `DIM_SALESFORCE_APOLLO_TEAMS` | — | — | — | `Hubspot`, `API` |
| Apollo MCP Connector | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS` | `ACTIVE_COUNTS_MCP_API_CALLS > 0` or `FIRST_ACTIVE_DATE_MCP_API_CALLS IS NOT NULL` | `ANALYTICS_DATAPLATFORM.FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` (controller/action breakdown, requires DEVELOPER_ROLE+) | PAIN_POINT + AI_GENERATED_SUMMARY ILIKE '%mcp%' OR '%claude%' | Search AI_GENERATED_SUMMARY for 'mcp', 'claude', 'oauth' |

______________________________________________________________________

## Customer Call Table Reference

| Table | What it covers | Key signal columns |
|---|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.HVO_CALLS_AI_PROCESSING` | HVO onboarding calls (~26K rows, daily refresh) | `AHA_FEATURES`, `FEATURE_DISCUSSED`, `PAIN_POINT`, `SEQUENCE_CREATED`, `MAILBOX_LINKED`, `IS_DIALER_DISCUSSED`, `IS_INBOUND_DISCUSSED`, `IS_AI_REFERRED`, `UPSELL_OPPORTUNITY` |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.WEEKLY_TEAM_SIGNALS_FROM_HVO_CALLS` | Weekly aggregated signals per team | Downstream of HVO_CALLS_AI_PROCESSING |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GTME_CALLS_AI_ANALYSIS` | GTME call transcripts | LLM-extracted signals |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_CALLS_AI_ANALYSIS` | Gong calls | LLM-extracted signals |
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.GONG_OPPORTUNITY_CALLS_AI_ANALYSIS` | Gong opportunity calls | LLM-extracted signals |

> Note: `ARRAY_CONTAINS` on `AHA_FEATURES` / `FEATURE_DISCUSSED` may not match due to VARIANT type casting. Use `SEQUENCE_CREATED`, `MAILBOX_LINKED`, and free-text `PAIN_POINT` LIKE filters as reliable alternatives.

______________________________________________________________________

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-20 | Created from outreach debrief session | Leo Liu |
| 2026-03-22 | Added WAT SoT rule: always use DIM_ACTIVE_TEAMS_DAILY feature L7 columns, never credit tables. Added waterfall row to key tables. Added full WAT-by-area table. | Leo Liu |
| 2026-03-24 | Added MCP Connector row to key tables; DIM_USERS (ACTIVE_COUNTS_MCP_API_CALLS) is SoT, FCT_MONGO_HTTP_REQUESTS_V3_RT_VW for controller-level breakdown | Leo |
