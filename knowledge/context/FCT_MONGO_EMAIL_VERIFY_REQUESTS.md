# FCT_MONGO_EMAIL_VERIFY_REQUESTS

> Fact table for every email enrichment request — the source of truth for email reveals across all non-waterfall flows.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAIL_VERIFY_REQUESTS` |
| **Grain** | One row per email verification request (`EMAIL_VERIFY_REQUESTS_ID`), deduplicated to latest state via `RNK_DESC = 1` |
| **Row count** | ~224M (2026-04-17) |
| **Refresh cadence** | Daily (via `STG_MONGO__EMAIL_VERIFY_REQUESTS` staging layer) |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative |
| **Owner** | Data Platform |
| **DAG** | `STG_MONGO__EMAIL_VERIFY_REQUESTS` staging → `FCT_MONGO_EMAIL_VERIFY_REQUESTS` |

## Description

Mirrors the MongoDB `EmailVerifyRequest` collection. Each row represents one email enrichment request — whether triggered from People Finder (add_to_prospect), the API, workflows, or batch CSV import. Covers **all email enrichment flows except waterfall** (waterfall is disabled for free teams and tracked separately via `FCT_MONGO_TYPED_CUSTOM_FIELD_AUTO_GENERATE_WORKFLOW_REQUESTS`). Primary consumers: data platform pipeline, credit accounting, and impact analysis for product restrictions.

Per Jaspreet Anand (2026-04-17): "EmailVerifyRequest is central for all flows for email enrichment (except waterfall enrichment). Waterfall isn't enabled for free teams anyway. So we should be good."

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `EmailVerifyRequest` collection | 1:1 via staging layer |
| `STG_MONGO__EMAIL_VERIFY_REQUESTS` | Staging layer |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `EMAIL_VERIFY_REQUESTS_ID` | TEXT | Primary key (from MongoDB `_id`) | |
| `TEAM_ID` | TEXT | Team that owns the request | FK to DIM_MONGO_TEAMS |
| `USER_ID` | TEXT | User who initiated the request | FK to DIM_MONGO_USERS |
| `STATUS_CD` | TEXT | Request status | Values: `completed`, `pending`, `failed`. Filter to `completed` for actual reveals. |
| `NUM_CONTACTS` | NUMBER | Contacts in the request batch | Use `COALESCE(NUM_CONTACTS, 1)` — individual reveals may be NULL |
| `ENRICHMENT_TYPE_CD` | TEXT | Enrichment method | `'1'` = native, `'2'` = waterfall. Free teams only have native. |
| `IS_COMPOSITE` | BOOLEAN | Composite (multi-sub) request flag | Filter `IS_COMPOSITE = FALSE` to avoid double-counting — composite parent's `NUM_CONTACTS` duplicates the sum of its children |
| `PARENT_EVR_ID` | TEXT | Parent request ID if this is a child | NULL for standalone and composite parent requests |
| `DISABLE_CREDIT_CHARGE` | BOOLEAN | Whether credit was charged | Useful for identifying internal/test requests |
| `CREATED_AT_UTC` | TIMESTAMP_NTZ | UTC creation timestamp | Use for daily date bucketing |
| `UPDATED_AT_UTC` | TIMESTAMP_NTZ | UTC last update timestamp | Used for deduplication ranking |
| `RNK_DESC` | NUMBER | Deduplication rank | Always filter `RNK_DESC = 1` to get latest record state |
| `ARCGATE_REQUEST_ID` | TEXT | Arcgate (external verifier) job ID | |
| `CURRENT_IP` | TEXT | IP address of requester | Useful for abuse detection |
| `LOAD_DATE` | DATE | Warehouse load date | |

## How It's Used

### Common query patterns

**Daily email reveal count per team (for free plan cap analysis):**
```sql
SELECT
    TEAM_ID,
    DATE(CREATED_AT_UTC) AS activity_date,
    SUM(COALESCE(NUM_CONTACTS, 1)) AS emails_revealed
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAIL_VERIFY_REQUESTS
WHERE STATUS_CD = 'completed'
  AND COALESCE(ENRICHMENT_TYPE_CD, '1') = '1'   -- native only
  AND COALESCE(IS_COMPOSITE, FALSE) = FALSE       -- exclude composite parents
  AND RNK_DESC = 1
  AND CREATED_AT_UTC >= DATEADD('day', -30, CURRENT_DATE)
GROUP BY 1, 2
```

### Key consumers

- Free plan restriction impact sizing (this analysis — 2026-04-17)
- Credit accounting pipeline
- Email enrichment volume monitoring

## Known Issues & Gotchas

- **Composite double-counting:** Composite parent records (`IS_COMPOSITE = TRUE`) have a `NUM_CONTACTS` equal to the sum of all child requests. If you include both parent and children, you double-count. **Always filter `IS_COMPOSITE = FALSE`** (or `COALESCE(IS_COMPOSITE, FALSE) = FALSE`) to keep only leaf/standalone records.
- **Waterfall exclusion:** `ENRICHMENT_TYPE_CD = '2'` records are waterfall requests. These are separate from native enrichment and not available to free teams. For free plan analysis, filter to `ENRICHMENT_TYPE_CD = '1'` or `IS NULL`.
- **RNK_DESC deduplication:** Always add `WHERE RNK_DESC = 1` — without it, you get multiple versions of the same request as it transitions through status states.
- **NULL NUM_CONTACTS:** Individual people finder reveals may have `NUM_CONTACTS = NULL` or `0`. Use `COALESCE(NUM_CONTACTS, 1)` to count them as 1 email revealed.
- **STATUS_CD filter matters:** `pending` and `failed` requests did not result in an email reveal. Always filter to `STATUS_CD = 'completed'` for volume analysis.

## Slack Context

- Jaspreet Anand (#proj-restrict-free-teams-at-three-months-fy27q2, 2026-04-17): proposed using EmailVerifyRequest as the enforcement mechanism for the free team daily email cap — covers all flows (add_to_prospect, API, workflows) except waterfall.

## Business Terms

| Term | Definition |
|---|---|
| Email enrichment | The act of revealing / verifying an email address for a contact. Billed as a credit event. |
| Composite request | A batch request that spawns multiple sub-requests. Parent record's NUM_CONTACTS is the sum of children — filter to `IS_COMPOSITE = FALSE` to avoid double-counting. |
| Native enrichment | Apollo's own email verification flow (`ENRICHMENT_TYPE_CD = '1'`), as opposed to waterfall (`'2'`). |
| Waterfall enrichment | Third-party email sourcing flow, not available to free teams. |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-17 | Created context file — discovered during free plan email cap impact analysis | Andrew Green |
