# DIM_MONGO_EMAIL_ACCOUNTS_RT_VW

> Real-time view of email account configurations. Very wide table (100+ columns) covering Gmail, Nylas, MS Exchange, SendGrid, Mailgun integrations plus mailwarming/warmup settings.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_EMAIL_ACCOUNTS_RT_VW` |
| **Grain** | One row per email account |
| **Row count** | ~14.8M (as of 2026-03-26) |
| **Refresh cadence** | Real-time view |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | N/A — real-time view on top of DIM_MONGO_EMAIL_ACCOUNTS |

## Description

Real-time view of the email accounts dimension table. Contains current-state configuration for every connected email account in Apollo — spanning Gmail, MS Exchange, Nylas, SendGrid, and Mailgun integrations. Includes mailwarming/warmup configuration, sending limits, sync state, and account health. Use this for current-state queries; use the base `DIM_MONGO_EMAIL_ACCOUNTS` table for historical analysis.

## Key Columns (grouped by domain)

### Core Identity
| Column | Type | Description |
|---|---|---|
| _ID | TEXT | Unique email account identifier |
| TEAM_ID | TEXT | Team ID |
| USER_ID | TEXT | User ID |
| EMAIL | TEXT | Email address |
| EMAIL_ID | TEXT | Email identifier |
| TYPE_CD | TEXT | Account type |
| ACTIVE | BOOLEAN | Whether account is active |
| DEFAULT | BOOLEAN | Whether this is user's default account |
| BANNED | BOOLEAN | Whether account is banned |
| INACTIVE_REASON | TEXT | Reason for inactivity |

### Mailwarming / Warmup
| Column | Type | Description |
|---|---|---|
| IS_OPTED_IN_MAILWARMING | BOOLEAN | Opted into mailwarming |
| MAILWARMING_MAX | NUMBER | Max mailwarming emails |
| MAILWARMING_TO_SEND_DAILY | NUMBER | Daily mailwarming target |
| MAILWARMING_EMAILS_LANDED_IN_INBOX | NUMBER | Warmup emails that hit inbox |
| MAILWARMING_EMAILS_LANDED_IN_SPAM | NUMBER | Warmup emails that hit spam |
| MAILWARMING_STARTED_AT | TIMESTAMP_NTZ | When warmup started |
| TRUE_WARMUP_STATUS_CD | TEXT | Warmup status |
| TRUE_WARMUP_DAILY_LIMIT | NUMBER | True warmup daily limit |
| TRUE_WARMUP_STARTED_AT | TIMESTAMP_NTZ | When true warmup started |

### Sending Limits & Policy
| Column | Type | Description |
|---|---|---|
| EMAIL_DAILY_THRESHOLD | NUMBER | Daily sending limit |
| MAX_OUTBOUND_EMAILS_PER_HOUR | NUMBER | Hourly sending cap |
| SECONDS_DELAY_BETWEEN_EMAILS | NUMBER | Throttle delay between sends |
| SHARING_POLICY_CD | TEXT | Sharing policy |
| EMAIL_SENDING_POLICY_CD | TEXT | Sending policy |
| NEXT_EMAIL_CAN_SEND_AT | TIMESTAMP_NTZ | Earliest next send time |
| MAILBOOST | BOOLEAN | Mailboost enabled |

### Sync State
| Column | Type | Description |
|---|---|---|
| LINKED_AT | TIMESTAMP_NTZ | When account was linked |
| REVOKED_AT | TIMESTAMP_NTZ | When access was revoked |
| LAST_SYNCED_AT | TIMESTAMP_NTZ | Last sync timestamp |
| ALL_HISTORY_SYNCED | BOOLEAN | Full history sync complete |

### Provider-Specific (Gmail, MS Exchange, Nylas, SendGrid, Mailgun)
The table has 30+ provider-specific columns for OAuth tokens, sync cursors, subscription IDs, and API keys. These are primarily operational — rarely needed for analytics.

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_MONGO_EMAIL_ACCOUNTS` | Base table — this is the real-time view |
| `DIM_MONGO_EMAIL_ACCOUNT_PURCHASES` | Join on EMAIL_ACCOUNT_PURCHASE_ID for provisioning info |
| `DIM_MONGO_TRACKING_DOMAINS` | Join on TEAM_ID for tracking domain config |
| `FCT_MONGO_EMAILER_MESSAGES` | Message-level activity from these accounts |

## Known Issues & Gotchas

- **Very wide table (100+ columns)** — always SELECT specific columns, never SELECT *.
- **Contains sensitive data** — OAuth tokens (GMAIL_ACCESS_TOKEN, MS_EXCHANGE_ACCESS_TOKEN, NYLAS_ACCESS_TOKEN), API keys (SENDGRID_API_KEY, MAILGUN_API_KEY), refresh tokens. Handle with care.
- **Real-time view** — reflects current state only. No historical snapshots.
- **CDC_METADATA is OBJECT type** — change data capture metadata, typically not needed for analytics.
- **ALIASES and AUTHENTICATION_SCOPES are ARRAY types** — need LATERAL FLATTEN for element-level analysis.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
