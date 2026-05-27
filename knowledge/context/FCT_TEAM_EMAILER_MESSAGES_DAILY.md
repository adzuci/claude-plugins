# FCT_TEAM_EMAILER_MESSAGES_DAILY

> Daily emailer message activity per team — message counts, engagement metrics (opens, replies, bounces) by campaign, message type, and status.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EMAILER_MESSAGES_DAILY` |
| **Grain** | One row per team + date + campaign + message type + status (`team_id` + `ds` + `campaign_id` + `message_type` + `status`) |
| **Row count** | ~30.2M (from catalog) |
| **Refresh cadence** | Daily (Snowflake Task: `TASK_REFRESH_FCT_TEAM_EMAILER_MESSAGES_DAILY`, runs at 06:00 UTC) |
| **Trust level** | Canonical (Playground) — source is high-trust ANALYTICS_DATAPLATFORM |
| **Owner** | Data Engineering (Brighid Meredith) |
| **DAG** | Snowflake Task `PLAYGROUND.TASK_REFRESH_FCT_TEAM_EMAILER_MESSAGES_DAILY` with stored procedure `SP_REFRESH_FCT_TEAM_EMAILER_MESSAGES_DAILY` |

## Description

Daily aggregation of emailer message activity from the Mongo emailer_messages collection. Includes all message types: outreach (automatic and manual), extension emails, downloaded emails, and conversation followup emails. Consumers filter by `message_type` to scope to their domain. This is the aggregated counterpart to the source table `FCT_MONGO_EMAILER_MESSAGES` (~22B rows).

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES` | Primary source — Mongo emailer_messages collection |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | TEXT | Apollo team ID | FK to DIM_MONGO_TEAMS.TEAM_ID |
| ds | DATE | Message completion date | Derived from `COMPLETED_AT::DATE` |
| campaign_id | TEXT | Emailer campaign ID | **NULL for downloaded_email** |
| message_type | TEXT | Type of email message | See values below |
| status | TEXT | Message status | **NULL for downloaded_email** |
| message_count | NUMBER | Number of messages | `COUNT(*)` |
| user_count | NUMBER | Distinct users sending | `COUNT(DISTINCT USER_ID)` |
| contact_count | NUMBER | Distinct contacts messaged | `COUNT(DISTINCT CONTACT_ID)` |
| opened_count | NUMBER | Messages opened | `SUM(OPENED::INT)` |
| replied_count | NUMBER | Messages replied to | `SUM(REPLIED::INT)` |
| delivered_count | NUMBER | Messages delivered | `SUM(DELIVERED::INT)` |
| bounced_count | NUMBER | Messages bounced | `SUM(BOUNCED::INT)` |
| spam_blocked_count | NUMBER | Messages spam-blocked | `SUM(SPAM_BLOCKED::INT)` |

### message_type values

| Value | Domain | Description |
|---|---|---|
| `outreach_automatic_email` | Genpipe / Sequences | Automated sequence emails |
| `outreach_manual_email` | Genpipe / Sequences | Manually triggered sequence emails |
| `extension_email` | Extension | Emails sent via Chrome extension |
| `downloaded_email` | Bulk downloads | Email downloads (campaign_id and status are NULL) |
| `conversation_followup_email` | Conversations | Follow-up emails from conversations |

## How It's Used

### Common query patterns
- **Sequence email activity:** `WHERE message_type IN ('outreach_automatic_email', 'outreach_manual_email')`
- **Open/reply rates:** `SUM(opened_count) / SUM(message_count)`, `SUM(replied_count) / SUM(message_count)`
- **Bounce rates:** `SUM(bounced_count) / SUM(delivered_count + bounced_count)`
- **Email volume trends:** `SELECT ds, SUM(message_count) ... GROUP BY ds`
- **Campaign performance:** Group by `campaign_id` for per-campaign metrics
- Join with `DIM_MONGO_TEAMS` for team attributes

### Key consumers
- Genpipe / pipeline generation metrics
- Email Activity metric (sequences domain)
- Product analytics (email feature adoption)

## Known Issues & Gotchas

- **NULL campaign_id and status for downloaded_email:** 84% of rows are `downloaded_email` type, which has NULL `campaign_id` and `status`. Filter these out for sequence/outreach analysis.
- **Future dates in ds:** `ds` includes future dates (scheduled sends) and rare corrupt dates (e.g., year 2126). **Filter `ds <= CURRENT_DATE()` if you only need completed messages.**
- **DQ checks:** Row count, row count regression, duplicate grain, freshness, and future_dates (>1 year out) checks run on each refresh.
- **Genpipe coverage is partial:** This table covers email-only pipeline activity. For the full pipeline generation picture (including plays/rule_actions and Amplitude events), a separate `FCT_TEAM_GENPIPE_DAILY` is planned but not yet built (blocked on LU_ENUM).

## Slack Context

<!-- TODO: search Slack for emailer/sequence discussions -->

## Business Terms

| Term | Definition |
|---|---|
| message_type | The category of email message sent through Apollo's platform |
| campaign_id | Identifier for an emailer campaign (sequence) |
| open rate | Percentage of delivered messages that were opened by the recipient |
| reply rate | Percentage of delivered messages that received a reply |
| bounce rate | Percentage of sent messages that failed to deliver |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-11 | Created context file | Brighid (via Claude) |
