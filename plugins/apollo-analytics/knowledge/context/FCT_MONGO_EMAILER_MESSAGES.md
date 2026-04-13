# FCT_MONGO_EMAILER_MESSAGES

> Email/sequence message events from MongoDB. One row per emailer message.

> ⚠️ **Use `ANALYTICS_DATASCIENCE.SEQUENCES` instead** for any sequence-level aggregation (open rate, reply rate, bounce rate by sequence). This table is the right choice only when the ask is explicitly **message-level or contact-level** — e.g. per-contact open tracking, individual message status, or row-level filtering. See `data-catalog/context/SEQUENCES.md`.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES` |
| **Grain** | One row per emailer message |
| **Row count** | ~22.1B (2026-03-06) — extremely large table |
| **Refresh cadence** | Weekly (Sundays 3AM UTC). Mongo snapshot ingestion, not CDC. |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | `super_admin_analytics_emailer_messages` (weekly snapshot). Config: `dags/mongo/config/ingestion_configs/super_admin_analytics/emailer_messages.yml`. Source: MongoDB `leadgenie_emailermessages_production.emailer_messages` |

## Description

Core email activity table (36 distinct users). Tracks all emailer messages including outreach emails (automatic and manual). Contains semi-structured recipient data.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `emailer_messages` collection | Primary source |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| CONTACT_ID | TEXT | 32 | 1,488 | Contact reference | **FK to DIM_MONGO_CONTACTS.CONTACT_ID** |
| STATUS | TEXT | 31 | 5,832 | Message status | Delivery status |
| BOUNCED | NUMBER | 31 | 3,387 | Bounce flag | Numeric flag (0/1) — use `= 1` / `= 0`, not `= TRUE` / `= FALSE`. Email deliverability. |
| HARD_BOUNCED_FOR_EMAIL_ALGORITHM | BOOLEAN | 30 | 1,007 | Hard bounce for algo | Deliverability scoring |
| COMPLETED_AT | TIMESTAMP | 29 | 6,186 | Completion timestamp | Highest query count — time-series analysis |
| TEAM_ID | TEXT | 29 | 4,109 | Team ID | **FK to DIM_MONGO_TEAMS.TEAM_ID** |
| EMAILER_MESSAGES_ID | TEXT | 28 | 4,516 | Message ID | **Primary key** |
| OPENED | NUMBER | 26 | 2,891 | Open flag | Numeric flag (0/1) — use `= 1` / `= 0`, not `= TRUE` / `= FALSE`. Engagement metric. |
| REPLIED | NUMBER | 26 | 2,779 | Reply flag | Numeric flag (0/1) — use `= 1` / `= 0`, not `= TRUE` / `= FALSE`. Engagement metric. |
| EMAILER_CAMPAIGN_ID | TEXT | 26 | 1,747 | Campaign/sequence ID | FK to sequence/campaign tables |
| RECIPIENTS | VARIANT | 26 | 542 | Semi-structured recipient data | Access via `recipients:domain::string` |
| SPAM_BLOCKED | NUMBER | 25 | 2,661 | Spam block flag | Numeric flag (0/1) — use `= 1` / `= 0`, not `= TRUE` / `= FALSE`. Deliverability. |
| TYPE | TEXT | 24 | 3,545 | Message type | Values: outreach_automatic_email, outreach_manual_email |
| DELIVERED | NUMBER | 24 | 2,959 | Delivery confirmation | Numeric flag (0/1) — use `= 1` / `= 0`, not `= TRUE` / `= FALSE`. |
| UPDATED_AT | TIMESTAMP | 24 | 459 | Last update | |

## How It's Used

### Common query patterns
- Filtered by `TYPE IN ('outreach_automatic_email', 'outreach_manual_email')` for sequence/outreach analysis
- Recipients parsed as semi-structured: `recipients:domain::string`
- Exploratory `SELECT *` with LIMIT for investigating specific cases

### Key consumers
- Analysts (ad-hoc email analysis)
- Valeriya Satsevich (recent heavy user)

## Known Issues & Gotchas

- TYPE values may not be intuitive — `automatic_outreach_email` vs `outreach_automatic_email` (both appear in queries)
- RECIPIENTS is semi-structured (VARIANT) — requires colon notation to access fields

## Slack Context

- **Deliverability is a top concern**: Multiple channels (#outbound-feedback, #email-abuse-response) discuss bounce rates, spam blocks, and email reputation. Customer-facing "Deliverability Agent" exists in-product.
- **Customer success uses deliverability metrics**: CS teams run deliverability audits per account — tracking filtered open rates, spam block rates, bounce rates vs 2% threshold, reply rates. Example: Emerge customer improved open rates from 3.98% to 12.87%.
- **DCS Scoreboard needs**: Section on lifecycle programs tracks emails sent, opened, clicked, converting. Needs data from this table.
- **Competitor pressure**: Customers using tools like Allegro for deliverability management. Apollo's deliverability features are a competitive differentiator.
- **Key columns for business**: STATUS (delivery status), BOUNCED, SPAM_BLOCKED, OPENED, REPLIED, DELIVERED are the deliverability health metrics. HARD_BOUNCED_FOR_EMAIL_ALGORITHM feeds the email scoring system.

## Business Terms

| Term | Definition |
|---|---|
| Outreach Email | An email sent through Apollo's sequence/outreach system |
| Emailer Message | Any message sent through Apollo's email infrastructure |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-02 | Schema drift fix: BOUNCED, OPENED, REPLIED, DELIVERED, SPAM_BLOCKED corrected from BOOLEAN → NUMBER (0/1 flags) | Brighid (via Claude) |
| 2026-03-05 | Created context file from query history analysis | Brighid (via Claude) |
