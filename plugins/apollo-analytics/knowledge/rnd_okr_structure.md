# R&D OKR Structure — FY27 Q1

**Owner:** Bridie Meredith | **Updated:** 2026-04-02
**Source:** Bi-weekly R&D Huddles updates (Mar 16-30), shared by Jaime DyBuncio (Bela's Chief of Staff)
**Audience:** Jarvis — use this to understand how Bela's product org frames priorities, tracks progress, and organizes teams

______________________________________________________________________

## How to Use This File

When answering questions about what Bela cares about, what R&D is working on, or how product teams map to company objectives, reference this structure. The OKR hierarchy below is how CPO directs actually organize and review their work in biweekly huddles.

**Quarter cadence:** Apollo uses Feb-start fiscal quarters. FY27 Q1 = Feb 1 – Apr 30, 2026. See [`fiscal_calendar.md`](fiscal_calendar.md).

**⚠ Staleness warning:** The scorecard below is a snapshot from the biweekly R&D Huddle (as of Mar 30). These values go stale quickly. When answering exec questions about current OKR status, **pull live metrics from Snowflake** (e.g., ARR from FCT_DAILY_REVENUE, WAT from FCT_TEAM_FEATURE_USERS_DAILY) instead of echoing the values below. Use this file for the OKR structure and targets — not as the source of current actuals.

______________________________________________________________________

## 5 Company Objectives (R&D Scope)

| # | Objective | Horizon | One-liner |
|---|-----------|---------|-----------|
| 1 | **Meet the Moment** | — | AI transformation in people, company, operations, and product |
| 2 | **Improve NRR** | H1 | Improve VSB/SMB NRR by 10+ pts via activation, onboarding, expansion |
| 3 | **Upmarket Readiness** | H1 | Generate $37.7M MM/Ent ARR, improve win rate and churn |
| 4 | **New Product Revenue** | H2 | Inbound $6.4M, Dialer $4.1M, AI Sheets alpha |
| 5 | **Build the Future** | H3 | Single AI assistant for every rep + #1 agentic GTM API |

______________________________________________________________________

## Q1 OKR Scorecard (Top 16 Metrics)

**For metrics marked LIVE, run the SQL below instead of using snapshot values.**

| Objective | Metric | Q1 Target | Source | Status |
|-----------|--------|-----------|--------|--------|
| Obj 3 | Data Duel: Account Match | 74% → 90% | Hex "Enrichment OKRs" (partial — raw_fivetran_db) | Snapshot only |
| Obj 3 | Data Duel: Contact Match | 58% → 80% | Hex "Enrichment OKRs" (partial — raw_fivetran_db) | Snapshot only |
| Obj 3 | Data Duel: Fill Rate | ≥80% matched | Hex "Enrichment OKRs" / DIM_MONGO_CSV_ENRICHMENT_JOBS | Snapshot only |
| Obj 3 | Deliverability: % ARR Exposed | 9.3% → 6.0% | Buildable (FCT_MONGO_EMAILER_MESSAGES + FCT_DAILY_REVENUE) — not yet registered | Snapshot only |
| Obj 3 | Deliverability: CIR | 3.8% → 2.5% | **LIVE** — see query below | |
| Obj 3 | CRM Integration: CIR | 0.26% → 0.16% | fct_user_crm_integration_status_daily — no catalog entry yet | Snapshot only |
| Obj 3 | Analytics: Close MM gaps | 80%+ gaps, 3+ partners ≥8/10 | Qualitative milestone — not queryable | Manual |
| Obj 3 | Prospecting: CSV Credits/mo | 7M/mo | **LIVE** — see query below | |
| Obj 3 | Prospecting: NLS accuracy/P50 | 90% accuracy, P50 5s | Engineering observability — not in Snowflake | Manual |
| Obj 2 | Onboarding: Habit RA | 12% → 17% | BLOCKED — draft in lu_saved_metrics, awaiting Adhiraj's event IDs | Snapshot only |
| Obj 2 | AI Assistant: W4 Retention | 13.4% → 20% | **LIVE** — see query below | |
| Obj 2 | AI Credit Consumption | 37M → 55M/mo | **LIVE** — see query below | |
| Obj 4 | Inbound ARR | $1.25M Q1 ending | **LIVE** — see query below | |
| Obj 4 | Dialer ARR | $1M Q1 ending | **LIVE** — see query below | |
| Obj 4 | AI Sheets | 90% Clay parity, 8/10 partners | Qualitative milestone — no warehouse persona flag yet | Manual |
| Obj 5 | MCP | DAU, WAT, Credits | **LIVE** — see query below | |
| Obj 5 | Co-Sell (Assistant 2.0) | 5+ design partners | Qualitative milestone — Notion/slides | Manual |

______________________________________________________________________

## Live OKR Queries

When generating the CPO/OKR report, run these queries instead of echoing cached values.

### Deliverability CIR (Complaint + Invalid Rate)

```sql
-- Reference: domain/deliverability.md
SELECT
    DATE_TRUNC('month', created_at_utc)::date AS month,
    COUNT(*) AS total_emails,
    SUM(CASE WHEN bounced = 1 AND spam_blocked = 1 THEN 1 ELSE 0 END) AS complaints_invalid,
    ROUND(100.0 * complaints_invalid / NULLIF(total_emails, 0), 2) AS cir_pct
FROM analytics_db.analytics_dataplatform.fct_mongo_emailer_messages
WHERE created_at_utc >= DATEADD('month', -3, CURRENT_DATE())
GROUP BY 1
ORDER BY 1 DESC;
```

### CSV Credit Consumption (Monthly)

```sql
SELECT
    DATE_TRUNC('month', ds)::date AS month,
    SUM(credits_used) AS csv_credits_used
FROM analytics_db.analytics.agg_team_credits
WHERE feature_type = 'csv_enrichment_email'
  AND ds >= DATEADD('month', -3, CURRENT_DATE())
GROUP BY 1
ORDER BY 1 DESC;
```

### AI Credit Consumption (Monthly Total)

```sql
SELECT
    DATE_TRUNC('month', ds)::date AS month,
    SUM(credits_used) AS total_ai_credits
FROM analytics_db.analytics.agg_team_credits
WHERE feature_type NOT IN ('ai_email', 'conversation')
  AND credit_type NOT IN ('conversation_credit')
  AND ds >= DATEADD('month', -3, CURRENT_DATE())
GROUP BY 1
ORDER BY 1 DESC;
```

### AI Assistant W4 Retention

```sql
-- Reference: teammates/pubudu_wariyapola/ai_assistant_retention_all_weeks.sql
-- Paid Core users only. W4 = days 22-28 post first active date.
WITH user_first AS (
    SELECT user_id, MIN(DATE(created_at_utc)) AS first_active_date
    FROM analytics_db.analytics_dataplatform.dim_mongo_assistant_threads t
    JOIN analytics_db.analytics_datascience.dim_users u ON t.user_id = u.apollo_user_id
    WHERE u.is_paid = TRUE AND u.has_free_email_domain = FALSE
    GROUP BY 1
),
user_activity AS (
    SELECT DISTINCT t.user_id, DATE(created_at_utc) AS active_date
    FROM analytics_db.analytics_dataplatform.dim_mongo_assistant_threads t
    JOIN user_first f ON t.user_id = f.user_id
)
SELECT
    DATE_TRUNC('week', f.first_active_date)::date AS cohort_week,
    COUNT(DISTINCT f.user_id) AS cohort_size,
    COUNT(DISTINCT CASE
        WHEN DATEDIFF('day', f.first_active_date, a.active_date) BETWEEN 22 AND 28
        THEN f.user_id END) AS w4_retained,
    ROUND(100.0 * w4_retained / NULLIF(cohort_size, 0), 1) AS w4_retention_pct
FROM user_first f
LEFT JOIN user_activity a ON f.user_id = a.user_id
WHERE f.first_active_date >= DATEADD('month', -3, CURRENT_DATE())
GROUP BY 1
ORDER BY 1 DESC;
```

### Inbound ARR

```sql
SELECT
    date(date_time_string) AS dd,
    SUM(12 * additional_fee_by_source:"inbound"::number / NULLIF(billing_interval_months, 0)) AS inbound_arr,
    COUNT(DISTINCT CASE WHEN additional_fee_by_source:"inbound"::number > 0 THEN team_id END) AS paid_inbound_teams
FROM analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports
WHERE date_time_string >= DATEADD('day', -7, CURRENT_DATE())::varchar
  AND team_id NOT IN ('68e6fb07946dcf000d2e3516', '620210171b9d04008e2ac0e0')
GROUP BY 1
ORDER BY 1 DESC
LIMIT 1;
```

### Dialer ARR

```sql
SELECT
    date(date_time_string) AS dd,
    SUM(12 * additional_fee_by_source:"dialer"::number / NULLIF(billing_interval_months, 0)) AS dialer_arr,
    COUNT(DISTINCT CASE WHEN additional_fee_by_source:"dialer"::number > 0 THEN team_id END) AS paid_dialer_teams
FROM analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports
WHERE date_time_string >= DATEADD('day', -7, CURRENT_DATE())::varchar
  AND team_id NOT IN ('68e6fb07946dcf000d2e3516', '620210171b9d04008e2ac0e0')
GROUP BY 1
ORDER BY 1 DESC
LIMIT 1;
```

### MCP (DAU, WAT, Credits)

```sql
-- MCP DAU (last 7 days)
SELECT
    DATE(request_time) AS dd,
    COUNT(DISTINCT user_id) AS mcp_dau,
    COUNT(DISTINCT apollo_team_id) AS mcp_wat
FROM analytics_db.analytics.fct_mongo_http_requests_v3_rt_vw
WHERE user_agent = 'Apollo-MCP/1.0'
  AND request_time >= DATEADD('day', -7, CURRENT_DATE())
GROUP BY 1
ORDER BY 1 DESC;

-- MCP Credits (weekly)
SELECT
    DATE_TRUNC('week', ds)::date AS week,
    SUM(credits_used) AS mcp_credits
FROM analytics_db.analytics.agg_team_credits
WHERE ds >= DATEADD('week', -4, CURRENT_DATE())
  -- Filter to MCP-originated feature types (check AGG_TEAM_CREDITS for exact types)
GROUP BY 1
ORDER BY 1 DESC;
```

______________________________________________________________________

## Team → Objective Mapping

| Team | Primary Objective | Key KRs |
|------|-------------------|---------|
| Fabric & Service Design | Obj 1: Meet the Moment | KR1.1 |
| AI Assistant | Obj 2: Improve NRR + Obj 5: Build the Future | KR2.1, KR5.1 |
| Onboarding | Obj 2: Improve NRR | KR2.2 |
| Conversion (Growth Product) | Obj 2: Improve NRR | W2 FTP ≥ 1.33%, Trial W2 CVR ≥ 3.5%, SS Annual ≥ 7.0% — see `domain/conversion_team_q2_fy27_okr.md` |
| Concept Car / Kaizen | Obj 2: Improve NRR | KR2.1 |
| Deliverability | Obj 3: Upmarket Readiness | KR3.2, KR3.3 |
| Data | Obj 3: Upmarket Readiness | KR3.1, KR3.3 |
| Data Duels | Obj 3: Upmarket Readiness | KR3.1, KR3.2 |
| CRM Integrations | Obj 3: Upmarket Readiness | KR3.2, KR3.3 |
| Analytics & Discovery | Obj 3: Upmarket Readiness | Analytics KR1.1, KR1.2 |
| Prospecting | Obj 3: Upmarket Readiness | Prospecting KR1.1–3.1 |
| Inbound | Obj 4: New Product Revenue | KR4.1 |
| Dialer | Obj 4: New Product Revenue | KR4.2 |
| AI Sheets | Obj 4: New Product Revenue | KR4.3 |
| Apollo Co-Sell (fka Assistant 2.0) | Obj 5: Build the Future | KR5.1 |
| MCP | Obj 5: Build the Future | KR5.2 |

______________________________________________________________________

## Objective Detail

### Objective 1: Meet the Moment

AI transformation in people, company, operations, and product. Invest in people and leaders.

Key highlights (Q1):

- Pocus acquisition: Isaac Pohl-Zaretsky (AI Sheets lead), Claire Seaver (Discovery & Analytics PM), Hana Kim (Pocus integration), 11 engineers
- Product Builder L5 role in POC; PM rubric revision toward Builder/AI-native skills
- Athena PRD Agent: 55+ PRDs generated, hours → minutes
- Fabric Studio alpha coming April
- Experiment digest channel (#amplitude-experiment-digest) vibe-coded post all-hands

### Objective 2: Horizon 1 — Improve NRR

Improve VSB and SMB NRR by 10+ pts. Decrease TTV, optimize onboarding and activation.

**AI Assistant** (KR2.1):

- Paid Core WAUs: 10K+ (from 3.6K pre-GA)
- W1 retention: 27.9% (from 19%), F7D high-value action rate: 4.8% → 21.5%
- W4 retention: 11.1% — below 13.4% baseline, well below 20% target
- Risk: Execution Engine drops requests; 29.1% of conversations end without action

**Onboarding** (KR2.2):

- Wizard removal: 100% rollout, stat-sig +1.74% FTP lift
- Champion Onboarding Flow: launched 3/26
- Habit RA: ~11.7% vs 17% target
- Key insight: "Activation breaks before or at the first outbound experience, not after it"

**Concept Car / Kaizen** (KR2.1):

- 4 experiments designed, sized, ready for eng — not yet in development
- Focus: email trigger on copy, action bar cleanup, simplified email compose, export→nudge

### Objective 3: Horizon 1 — Upmarket Readiness

Generate $37.7M in MM/Ent ARR. Improve upmarket win rate 39%→42%. Improve MM churn 6 pts.

**Data**: Account match 85% (big recovery from CSV scrubbing). Fill rate gaps structural (funding 19%). SFDC V2 broken — 0/37 duels.
**Deliverability**: Setup enforcement live (20% new signups). 29% of support = deliverability. $13M+ ARR at risk.
**CRM Integrations**: Sync visibility 100% GA. Only 3% of 1,249 complaints are actual bugs — rest is UX confusion.
**Analytics & Discovery**: API V1 live (193 metrics, 83 dims). MCP staging (67 metrics). Design partners: Glean, Domo, Anthropic, TransPerfect, Uber.
**Prospecting**: NLS V2 94.4% success. CSV credits ~6.6M/mo. Snowflake native connector ERD approved, BE dev started.

### Objective 4: Horizon 2 — New Product Revenue

**Inbound** (KR4.1): $1M ARR — first add-on to hit milestone. 610+ paid customers. W4 retention ~73% vs ~18% overall. FTP conversion 0.8% vs 2% target.
**Dialer** (KR4.2): ~$800K ARR. Self-serve outperforming. Win rate 35.6%. Activation funnel critical risk (~5% enriched→first call). ~6 weeks before exhausting user base without fix.
**AI Sheets** (KR4.3): ~70% MVP complete. Prospeo + LeadMagic live. Isaac (ex-Pocus CTO) leading. Controlled customer rollout April.

### Objective 5: Build the Future

Build the single AI assistant every rep uses. Become #1 API for agentic GTM.

**Co-Sell / Assistant 2.0** (KR5.1): 3/5 design partners signed. Slack POC live staging. 0/5 running autonomous workflows — first test (Slack Daily Brief) this week. Validate or pivot by 5/7.
**MCP** (KR5.2): Peak DAU 2,492 (+40% WoW), WAT 7,472 (+150% WoW), Credits 100K+/wk. Moving from Tiger Team to dedicated scrum. Legal/compliance gating expansion beyond Anthropic.

______________________________________________________________________

## Update Cadence

This file reflects the **biweekly R&D Huddle** — CPO directs meet every two weeks to review OKR progress across all product teams. Jaime DyBuncio (Bela's Chief of Staff) coordinates.

**To update:** Ask Jaime or check the R&D Huddles Notion page for the latest biweekly update. Update this file with new metrics and status changes.

**Commentary sourcing (TODO):** Jaime requested that Jarvis source ongoing commentary from the product digest and key Slack channels rather than relying solely on domain context files. This is not yet implemented — the current plugin does not have Slack or Notion access.
