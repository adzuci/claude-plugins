# Deliverability — Domain Reference

> **Owner:** Valery | **Updated:** 2026-03-27

## TL;DR

Deliverability analysis covers email sending health — whether emails reach inboxes, bounce, get spam-blocked, get opened, and get replied to. The core table is `FCT_MONGO_EMAILER_MESSAGES`. Connected to mailbox info (`DIM_MONGO_EMAIL_ACCOUNTS`), tracking domain config (`DIM_MONGO_TRACKING_DOMAINS`), and domain authentication health (`DIM_MONGO_DOMAIN_DIAGNOSES`). Most analyses require standard exclusions: filter to relevant email types and statuses, exclude free domains, exclude Apollo internal teams.

Most deliverability tables refresh weekly — rates are typically analyzed at weekly granularity.

---

## Tables

### `FCT_MONGO_EMAILER_MESSAGES`
**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES`

See data catalog for full column reference.

- **Primary timestamp:** `COMPLETED_AT`
- **Status filter:** `status IN ('Completed', 'Failed')` — completed = successfully sent, failed = attempted but failed. Other statuses (scheduled, paused, draft, etc.) are not relevant for deliverability.
- **Type filter:** `TYPE IN ('outreach_automatic_email', 'outreach_manual_email')`. Extension emails (`extension`) can be added but are excluded for cold outreach analyses.
- **Join to mailbox:** `EMAIL_ACCOUNT_ID` → `DIM_MONGO_EMAIL_ACCOUNTS.EMAIL_ACCOUNT_ID`
- **Join to tracking domain:** `TRACKING_DOMAIN_ID` → `DIM_MONGO_TRACKING_DOMAINS.TRACKING_DOMAIN_ID`

---

### `DIM_MONGO_EMAIL_ACCOUNTS`
**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_EMAIL_ACCOUNTS`

Used for mailbox-level filtering, channel segmentation, and mailwarming context.

- **`TYPE_CD`** — filter out `sendgrid` and `mailgun` for most analyses (provider-led, low control). Label as `'SendGrid/Mailgun'` vs `'Direct'` when segmenting by channel.
- **Mailwarming** — gradually ramps up sending volume and creates engagement to prepare a mailbox for higher-volume sending. Completed mailwarming filter:
  ```sql
  MAILWARMING_VENDOR_END_DATE IS NOT NULL
  AND MAILWARMING_VENDOR_END_DATE < CURRENT_DATE()
  AND MAILWARMING_VENDOR_END_DATE >= MAILWARMING_VENDOR_START_DATE
  ```
- Connected to purchases via `DIM_MONGO_EMAIL_ACCOUNT_PURCHASES` and the real-time view `DIM_MONGO_EMAIL_ACCOUNTS_RT_VW`.

---

### `DIM_MONGO_TRACKING_DOMAINS`
**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TRACKING_DOMAINS`

Tracking subdomains used for email activity and engagement tracking. Connects to emailer messages via `TRACKING_DOMAIN_ID`.

- **`TYPE_CD`** values: `custom` (unique to the company), `shared` (Apollo-provided), `NULL` (not configured — nullified subdomains stay NULL)

---

### `DIM_MONGO_DOMAIN_DIAGNOSES`
**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_DOMAIN_DIAGNOSES`

Domain authentication health per (team, domain). Not directly joined to emailer messages — connect via team + domain, or via `DIM_MONGO_EMAIL_ACCOUNTS`.

- **Best timestamp:** `UPDATED_AT_UTC`
- **Healthy domain:** `SPF_STATUS_CD = 'good' AND DKIM_STATUS_CD = 'good' AND DMARC_STATUS_CD = 'good'`
- Only relevant for **custom (non-free) domains** — free email providers don't support this
- Diagnoses can be triggered automatically or manually by the user
- This table is a snapshot (latest state only). For authentication status over time, use Amplitude events: `Domain Authentication Healthy` / `Domain Authentication Unhealthy`

---

### `DIM_MONGO_BLACKLIST_CHECKS`
**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_BLACKLIST_CHECKS`

Blacklist detection scores — a user can run a diagnosis to see if their mailbox is on a blacklist. New as of early 2026. Latest status per mailbox is also surfaced in `DIM_MONGO_EMAIL_ACCOUNTS.BLACKLIST_HEALTH_STATUS` (new column, may not be populated yet).

---

### `DIM_MONGO_EMAIL_ACCOUNT_PURCHASES` / `DIM_MONGO_DOMAIN_PURCHASES`
Purchase records for mailboxes and domains bought through Apollo. Connect to `DIM_MONGO_EMAIL_ACCOUNTS` or `DIM_MONGO_EMAIL_ACCOUNTS_RT_VW`.

---

## Standard Exclusions

### 1. Email status and type
```sql
WHERE eml.status IN ('Completed', 'Failed')
  AND eml.type IN ('outreach_automatic_email', 'outreach_manual_email')
  -- 'extension' can be added but is typically excluded for cold outreach
```

### 2. Free email domains
```sql
WHERE domain NOT IN (
    SELECT domain FROM ANALYTICS_DB.ANALYTICS.FREE_EMAIL_PROVIDER_DOMAINS
)
```

### 3. Apollo internal teams
```sql
-- Preferred: join to DIM_TEAMS in ANALYTICS_DATASCIENCE (IS_INTERNAL_DOMAIN exists here, not in DIM_MONGO_TEAMS)
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t ON eml.TEAM_ID = t.APOLLO_TEAM_ID
WHERE t.IS_INTERNAL_DOMAIN = FALSE
```

---

## Common Segmentation Dimensions

| Dimension | Source | Notes |
|---|---|---|
| **Mailbox provider type** | `DIM_MONGO_EMAIL_ACCOUNTS.TYPE_CD` | gmail, ms_exchange, nylas, mailgun, sendgrid, etc. |
| **Direct vs aggregate** | `DIM_MONGO_EMAIL_ACCOUNTS.TYPE_CD` | Direct: gmail, ms_exchange, nylas. Aggregate: sendgrid, mailgun. |
| **Tracking subdomain type** | `DIM_MONGO_TRACKING_DOMAINS.TYPE_CD` | custom, shared, NULL |
| **Free domain** | `ANALYTICS_DB.ANALYTICS.FREE_EMAIL_PROVIDER_DOMAINS` | Important segmentation factor — free domains behave differently and are excluded from domain-level analyses |

---

## Rate Definitions

Use `DIV0()` for all rate calculations to avoid divide-by-zero. All flags are 0/1 integers.

| Metric | Numerator | Denominator | Notes |
|---|---|---|---|
| **Delivery rate** | `delivered = 1` | all sent | |
| **Overall bounce rate** | `bounced = 1` | all sent | Includes hard + soft + spam blocks. `delivery_rate + overall_bounce_rate = 100%` |
| **Hard bounce rate** | `bounced = 1 AND hard_bounced_for_email_algorithm = 1` | all sent | |
| **Soft bounce rate** | `bounced = 1 AND spam_blocked = 0 AND hard_bounced_for_email_algorithm = 0` | all sent | |
| **Spam block rate** | `bounced = 1 AND spam_blocked = 1` | all sent | Spam blocks are part of overall bounce, not separate |
| **Open rate (filtered)** | `opened = 1` | `open_tracking_enabled = 1 AND delivered = 1` | Preferred — excludes bot opens |
| **Open rate (unfiltered)** | `opened = 1 OR bot_opened = 1` | `open_tracking_enabled = 1 AND delivered = 1` | Adds bot opens |
| **Reply rate** | `replied = 1` | `delivered = 1` | |

> **Open rate gotcha:** Always filter denominator to `open_tracking_enabled = 1 AND delivered = 1`. `open_tracking_enabled` is preferred over the older `enable_tracking` column (both exist, both appear in queries).

> **Bounce thresholds:** > 5% overall bounce rate is high. > 10% is extremely high.

> **Recency bias:** Engagement metrics (open rate, reply rate) are measured at send date (`completed_at`), but opens and replies can trickle in for days or weeks after sending. The most recent week in any report will appear lower than fully-baked weeks — this is expected, not a signal. If someone flags a drop in the latest week, list recency as a possible explanation before drawing conclusions.

---

## Reference Query — Weekly Deliverability by Channel

```sql
SELECT
    DATE_TRUNC('week', eml.completed_at) AS sent_week,
    CASE
        WHEN ea.type_cd IN ('sendgrid', 'mailgun') THEN 'SendGrid/Mailgun'
        ELSE 'Direct'
    END AS channel,

    -- Counts
    COUNT(DISTINCT eml.emailer_messages_id)                                                                                                                                AS message_count_sent,
    COUNT(DISTINCT CASE WHEN eml.bounced = 1 THEN eml.emailer_messages_id END)                                                                                             AS message_count_bounced,
    COUNT(DISTINCT CASE WHEN eml.bounced = 1 AND eml.hard_bounced_for_email_algorithm = 1 THEN eml.emailer_messages_id END)                                                AS message_count_hard_bounce,
    COUNT(DISTINCT CASE WHEN eml.bounced = 1 AND eml.spam_blocked = 0 AND eml.hard_bounced_for_email_algorithm = 0 THEN eml.emailer_messages_id END)                      AS message_count_soft_bounce,
    COUNT(DISTINCT CASE WHEN eml.bounced = 1 AND eml.spam_blocked = 1 THEN eml.emailer_messages_id END)                                                                    AS message_count_spam_blocked,
    COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END)                                                                                           AS message_count_delivered,
    COUNT(DISTINCT CASE WHEN eml.opened = 1 THEN eml.emailer_messages_id END)                                                                                              AS message_count_opened,
    COUNT(DISTINCT CASE WHEN eml.open_tracking_enabled = 1 AND eml.delivered = 1 THEN eml.emailer_messages_id END)                                                         AS message_count_tracked_delivered,
    COUNT(DISTINCT CASE WHEN eml.replied = 1 THEN eml.emailer_messages_id END)                                                                                             AS message_count_replied,

    -- Rates
    DIV0(COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                                                                          AS delivery_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.bounced = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                                                                          AS overall_bounce_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.bounced = 1 AND eml.hard_bounced_for_email_algorithm = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                                                                          AS hard_bounce_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.bounced = 1 AND eml.spam_blocked = 0 AND eml.hard_bounced_for_email_algorithm = 0 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                                                                          AS soft_bounce_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.bounced = 1 AND eml.spam_blocked = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT eml.emailer_messages_id))                                                                                                                          AS spam_blocked_rate,
    DIV0(COUNT(DISTINCT CASE WHEN eml.opened = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.open_tracking_enabled = 1 AND eml.delivered = 1 THEN eml.emailer_messages_id END))                                                   AS open_rate_filtered,
    DIV0(COUNT(DISTINCT CASE WHEN eml.opened = 1 OR eml.bot_opened = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.open_tracking_enabled = 1 AND eml.delivered = 1 THEN eml.emailer_messages_id END))                                                   AS open_rate_unfiltered,
    DIV0(COUNT(DISTINCT CASE WHEN eml.replied = 1 THEN eml.emailer_messages_id END),
         COUNT(DISTINCT CASE WHEN eml.delivered = 1 THEN eml.emailer_messages_id END))                                                                                    AS reply_rate

FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES eml
JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_EMAIL_ACCOUNTS ea
    ON eml.email_account_id = ea.email_account_id
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t
    ON eml.team_id = t.apollo_team_id

WHERE eml.status IN ('Completed', 'Failed')
  AND DATE(eml.completed_at) >= DATE_TRUNC('WEEK', DATEADD(month, -3, CURRENT_DATE()))
  AND DATE(eml.completed_at) <= CURRENT_DATE - DAYOFWEEK(CURRENT_DATE) + 1
  AND eml.type IN ('outreach_automatic_email', 'outreach_manual_email')
  AND t.is_internal_domain = FALSE
  AND ea.type_cd NOT IN ('sendgrid', 'mailgun') -- Direct sends only; exclude to isolate mailbox-level deliverability

GROUP BY 1, 2
ORDER BY 1, 2;
```
