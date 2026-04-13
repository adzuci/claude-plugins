# SEQUENCES

> ✅ **Canonical source for sequence-level email analysis.** Default to this table for open rate, reply rate, bounce rate, and engagement metrics at the sequence grain. Only use `FCT_MONGO_EMAILER_MESSAGES` when the ask is explicitly message-level or contact-level.

**Schema:** `ANALYTICS_DB.ANALYTICS_DATASCIENCE`
**Type:** Dimension / pre-aggregated summary
**Grain:** One row per emailer sequence (emailer campaign)
**Join key:** `APOLLO_TEAM_ID` (customer team), `EMAILER_CAMPAIGN_ID`

## What it contains

Per-sequence email performance metrics — lifetime aggregates for every Apollo sequence created by a customer team. Includes engagement signals (opens, replies, interested), deliverability metrics (bounces, hard bounces), step structure metadata, and timestamps.

## Key columns

| Column | Description |
|---|---|
| `APOLLO_TEAM_ID` | Customer team — use this to filter to a specific account |
| `EMAILER_CAMPAIGN_ID` | Sequence/campaign ID — joins to `FCT_MONGO_EMAILER_CAMPAIGNS`, `FCT_MONGO_EMAILER_MESSAGES` |
| `EMAILER_CAMPAIGN_NAME` | Display name of the sequence |
| `EMAIL_SENT_COUNTS` | Total emails sent |
| `EMAIL_DELIVERED_COUNTS` | Successfully delivered |
| `EMAIL_OPENED_COUNTS` | Opened (use delivered as denominator for open rate) |
| `EMAIL_REPLY_RECEIVED_COUNTS` | Any reply received |
| `EMAIL_INTEREST_RECEIVED_COUNTS` | Positive/interested reply flagged by Apollo AI |
| `EMAIL_BOUNCED_COUNTS` | Total bounces (soft + hard) |
| `EMAIL_HARD_BOUNCED_COUNTS` | Hard bounces only |
| `EMAIL_SOFT_BOUNCED_COUNTS` | Soft bounces only |
| `LAST_SENT_AT` | Timestamp of the last email sent in this sequence |
| `IS_ACTIVE` / `IS_ARCHIVED` | Sequence status flags |
| `AUTOMATIC_EMAIL_STEP_COUNTS` | How many auto-email steps in the sequence |
| `PHONE_CALL_STEP_COUNTS` | How many call steps |

## Rate calculation convention

```
open_rate       = EMAIL_OPENED_COUNTS           / EMAIL_DELIVERED_COUNTS
reply_rate      = EMAIL_REPLY_RECEIVED_COUNTS   / EMAIL_DELIVERED_COUNTS
interested_rate = EMAIL_INTEREST_RECEIVED_COUNTS / EMAIL_DELIVERED_COUNTS
bounce_rate     = EMAIL_BOUNCED_COUNTS          / EMAIL_SENT_COUNTS
hard_bounce_rate = EMAIL_HARD_BOUNCED_COUNTS    / EMAIL_SENT_COUNTS
```

## Benchmark thresholds (informal)

| Metric | Good | Warn | Danger |
|---|---|---|---|
| Open rate | ≥ 20% | 10–20% | < 10% |
| Reply rate | ≥ 5% | 2–5% | < 2% |
| Bounce rate | < 3% | 3–8% | > 8% |
| Hard bounce rate | < 2% | 2–5% | > 5% |

## What's NOT here

- **Meeting booked per sequence** — no FK from emailer messages to calendar/meeting events in Snowflake. Not trackable at sequence grain.
- **Per-step breakdowns** — use `DIM_MONGO_EMAILER_STEPS` or `FCT_MONGO_EMAILER_MESSAGES` for step-level data.
- **Per-contact activity** — use `FCT_MONGO_EMAILER_MESSAGES` (message-level, has `CONTACT_ID`, `STATUS`, `OPENED`, `REPLIED`).

## Verified usage

Used in `teammates/leo_liu/account_lookup.py` — `fetch_deliverability()` function queries this table by `APOLLO_TEAM_ID` to render the Email Deliverability section of the account profile report. Verified 2026-03-21 against glean.com (20 sequences returned).
