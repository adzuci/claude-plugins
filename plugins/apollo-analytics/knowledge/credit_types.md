# Apollo Credit Types — Canonical Reference

**Owner:** Leo Liu | **Updated:** 2026-03-22
**Source:** [Credit Data Meaning spreadsheet](https://docs.google.com/spreadsheets/d/1f6QZ30OgwJ4TgH35ZC_Wf1Pt31cjbZvTnrHMyUcgqsI/edit?gid=0#gid=0) (Leo Liu, last updated Nov 17 2025)

---

## Credit Type Reference

| Credit Type | What triggers it | Consumes Unified Credits? | Consumes Different Type? | Amount |
|---|---|---|---|---|
| Power Up | Running a Power Up (research, personalized opener, etc.) | Yes | No | 1 unified credit per execution |
| AI Email | AI-written emails | **No** | Yes — AI Word Credits | Draws from Apollo's AI pool (3B credits); **not billed to customers** |
| **Waterfall Enrichment** | Enrichment via vendors | Yes | **Yes — waterfall trial credits** | Vendor data consumes trial first, then unified (≈1 credit per record) |
| API Enrichment | Enrichment via API | Yes | No | 1 unified credit per record enriched |
| Auto Enrich Contact | Auto-enrichment when saving a contact | Yes | No | 1 unified credit per contact |
| Person Enrichment | Requesting an email in prospecting | Yes | No | 1 unified credit per record |
| Mailwarming | Mailbox warmup service | Yes | No | Unified credits monthly per inbox; first inbox free |
| **Direct Dial (lookup)** | Requesting a direct phone number in prospecting | Yes | No | **3–10 unified credits per number (region-based)** |
| Dialer Minutes (US) | Outbound calls, domestic | No | Yes | 3 minutes per $ spent |
| Dialer Minutes (Intl) | Outbound calls, international | No | Yes | 1 minute per $ spent |
| LinkedIn Emails | Pulling emails via LinkedIn extension | Yes | No | 1 unified credit per email |
| Change Job | Enrichment on contact job change | Yes | No | 1 unified credit per change event |
| CRM Field Enrichment | Syncing values into CRM fields | **No** | Free | Credits already consumed during email/phone enrichment |
| Rules Engine | Workflow automation logic | Yes | No | Charges unified credits to prospect automatically; not charged separately |
| Searcher Emails | Exporting/revealing emails via Searcher | Yes | No | 1 unified credit per email |
| CSV Enrichment Email | Uploading CSV for email enrichment | Yes | No | 1 unified credit per row enriched |
| CSV Export | Exporting enriched CSV | No | Free | Credits consumed at enrichment time, not export |
| Reverify Emails | Email re-verification | Yes | No | 1 unified credit per reverify |
| Domain Purchasing | Buying sending domains | Yes | No | ≈15–25 credits per domain |
| Inbox Purchasing | Buying inboxes (mailboxes) | Yes | No | ≈30–50 credits per inbox monthly |
| Pre-Meeting Insights | Power-ups on Meetings | No | Free today | |
| Nooks Integration | Export to Nooks | No | Free today | |
| Orum Integration | Export to Orum | No | Free today | |
| Salesloft / Pipedrive / HubSpot / Salesforce / Outreach / Zapier Push | CRM/integration sync | No | Free — integration actions | |
| Conversation | Conversation intelligence (transcripts, summaries) | No | Free — included feature | Not credit-billed |

---

## Key Facts for Analysis

### AGG_TEAM_CREDITS — Canonical Credit SoT

`AGG_TEAM_CREDITS` is the **canonical source of truth for customer-billed credit consumption**. Use it for all credit volume reporting. `WATERFALL_CREDIT_USAGE` and other DS tables are supplementary deep-dive tables, not billing SoT.

**Critical:** Filter by `FEATURE_TYPE`, not `CREDIT_TYPE`. `CREDIT_TYPE` has duplicate naming variants (snake_case vs Title Case) and is inconsistently populated. `FEATURE_TYPE` is the stable, canonical filter.

### Waterfall Enrichment Credit Complexity
Waterfall uses **waterfall trial credits first**, then falls back to unified credits.

**Waterfall FEATURE_TYPE values in AGG_TEAM_CREDITS (verified 2026-03-22):**

| FEATURE_TYPE | Description | Scale (weekly, Mar 2026) |
|---|---|---|
| `waterfall_enrichment` | Email waterfall via vendor cascade | ~9.6–11.7M credits, ~33–35K teams |
| `waterfall_mobile_enrichment` | Phone number waterfall via vendor cascade | ~1.7–2.8M credits, ~5–5.7K teams |
| `api_waterfall_enrichment` | API-triggered waterfall enrichment | ~12–29K credits, ~30–64 teams |

**Standard query pattern:**
```sql
SELECT
    DATE_TRUNC('week', DS) AS week_start,
    FEATURE_TYPE,
    COUNT(DISTINCT TEAM_ID) AS teams,
    SUM(CREDITS_USED) AS total_credits
FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS
WHERE DS >= DATEADD('week', -8, CURRENT_DATE())
  AND FEATURE_TYPE IN ('waterfall_enrichment', 'waterfall_mobile_enrichment', 'api_waterfall_enrichment')
GROUP BY 1, 2
ORDER BY 1 DESC, 4 DESC;
```

Note: The ≈1 credit per record is a simplification — vendor data queries can trigger multiple attempts, especially with stop condition SS1 (stop on verified only), which runs every vendor before finding a match.

### Phone Number Pricing Gap
**Direct Dial = 3–10 unified credits per number (region-based).** Support tickets report customers told 1 credit/number in demos, then charged 9–35. The 3–10 range from this doc vs 9–35 in support tickets suggests:
- Phone enrichment via **waterfall** (trying multiple vendors) multiplies credit cost
- Or regional pricing for international numbers hits the high end
- The demo pricing mismatch is not just communication — the actual credit math differs from what's documented here

### What NOT to count as customer-facing credit consumption
Credit types where `Consumes Unified Credits = No` should **not** be included in customer credit consumption metrics:
- AI Email (AI Word Credits pool, not customer-billed)
- CRM push actions (Salesforce, HubSpot, Pipedrive, etc.)
- Conversation intelligence
- CSV Export
- CRM Field Enrichment
- Dialer Minutes (separate $ pool)

### Open question (as of Nov 2025 — Leo + Bridie)
Whether `Consumes Unified Credits = No` rows should be excluded from `dbt_development_db.dbt_adhoc.agg_user_credit_consumption` was an open question. Status unknown — verify before using that table for customer-facing credit metrics.

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-22 | Created from Credit Data Meaning spreadsheet | Leo (via Jarvis) |
