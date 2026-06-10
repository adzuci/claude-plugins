# Deliverability — Domain Reference

> **Owner:** Valery | **Updated:** 2026-05-18

## TL;DR

Deliverability analysis covers email sending health — whether emails reach inboxes, bounce, get spam-blocked, get opened, and get replied to. The core table is `FCT_MONGO_EMAILER_MESSAGES`. Connected to mailbox info (`DIM_MONGO_EMAIL_ACCOUNTS`), tracking domain config (`DIM_MONGO_TRACKING_DOMAINS`), and domain authentication health (`DIM_MONGO_DOMAIN_DIAGNOSES`). Most analyses require standard exclusions: filter to relevant email types and statuses, exclude free domains, exclude Apollo internal teams.

Most deliverability tables refresh weekly — rates are typically analyzed at weekly granularity.

______________________________________________________________________

## Setup Enforcement Program

**What it is.** Originally planned to roll out to all users — blocks sending after a team accumulates some send volume from an unhealthy domain.

**V1 experiment.** Ran on new users as a controlled experiment. v1 was the strictest version: any error on SPF/DKIM/DMARC counted as unhealthy and triggered a block. Treatment group saw a retention drop, so v1 was rolled back. Diagnostic: only 8 teams actually hit the block, and those 8 did not churn — so the enforcement gate itself was not the driver. The messaging around the block and the remediation funnel did not work. The remediation funnel goes through Entri and is very manual.

**GTME interventions.** Introduced in response — hand-touch CS remediation to lift the % of healthy domains in the managed sender base and improve their deliverability directly, independent of the enforcement gate.

**Planned (currently postponed).** Both planned versions are less strict than v1; both use the three-band classification (**healthy** / **gray** / **critical**) where **critical = `SPF = 'error' AND DKIM = 'error'`**. Spectrum from strictest to loosest:

| Version | Cohort | Block trigger |
|---|---|---|
| v1 (rolled back) | New users | Any error on SPF/DKIM/DMARC |
| Managed enforcement (planned) | Managed accounts | Stricter than unmanaged, less strict than v1 — not all errors are critical |
| v2 experiment (planned) | Unmanaged teams | Critical band only — sending allowed otherwise |

**Takeaway from v1.** The Entri-based remediation funnel is the lever for deliverability — that's where v1 surfaced friction, and where movement in the % of healthy domains will come from.

______________________________________________________________________

## Product Levers — In-Flight Features (2026)

Catalog of the product-side deliverability interventions and where their signal lives in Snowflake. Add new ones here when they ship.

### Catch-all domain exclusion (TEAM-level, default-ON)

Blocks outbound sends to catch-all domains — domains whose MX accepts mail for any address, producing high bounce / low engagement. On by default.

| Signal | Where to look |
|---|---|
| Per-team toggle state | `DIM_MONGO_TEAMS.CATCHALL_PROTECTION_ENABLED` — current snapshot shows ~5.0M rows NULL, 1 row FALSE, 0 rows TRUE. Working hypothesis: NULL = enabled (default-on, no explicit write). **Confirm with eng before reporting NULL as "on" in a numeric KPI.** |
| Blocked-send events | `FCT_MONGO_EMAILER_MESSAGES` where `STATUS = 'Failed'` AND `NOT_SENT_REASON = 'catchall_domain_blocked'`. Time axis: use `FAILED_AT` (not `COMPLETED_AT` — blocked sends never complete). ~80–1,200 blocks/week since Jan 2026; peak 2026-03-02 (1,191). |
| Historical toggle history | Not currently captured cleanly — `DIM_MONGO_TEAMS` is a current-state snapshot. Toggle-over-time tracking method still TBD. |

### Blocklist / blacklist checks (MAILBOX-level, user-initiated)

User-run diagnostic from the Deliverability Suite checking the mailbox against known blocklists (Spamhaus, Barracuda, etc.). One row per check.

**Table:** [`DIM_MONGO_BLACKLIST_CHECKS`](../data-catalog/context/DIM_MONGO_BLACKLIST_CHECKS.md)

| Column | Meaning |
|---|---|
| `BLACKLIST_CHECK_ID` | PK |
| `EMAIL_ACCOUNT_ID` / `EMAIL` / `FROM_EMAIL` | Mailbox |
| `STATUS_CD` | Process status — did the check complete (orchestration-level)? |
| `FINAL_STATUS` | Result. Main values: `completed` = healthy (no providers flagging), `warning` = blocked by at least one provider. Less common: `error` (upstream provider error), `pending`, `failed` (our-side issue). Dominant operational states: `completed` and `warning`. |
| `SCORE` | Numeric score (provider-specific). |
| `EXTERNAL_VENDOR_ID` / `EXTERNAL_VENDOR_CHECK_ID` | Upstream IDs |
| `UPDATED_AT_UTC` | Most recent check time |

Latest status per mailbox is also surfaced in `DIM_MONGO_EMAIL_ACCOUNTS.BLACKLIST_HEALTH_STATUS` — coverage may be incomplete.

### Inbox Placement Tests (MAILBOX-level, user-initiated)

Diagnostic that sends **100 test emails** from the mailbox to a panel of seed addresses across major mailbox providers, then reports where each landed.

**Table:** [`DIM_MONGO_INBOX_PLACEMENT_TESTS`](../data-catalog/context/DIM_MONGO_INBOX_PLACEMENT_TESTS.md)

| Column | Meaning |
|---|---|
| `INBOX_PLACEMENT_TEST_ID` | PK |
| `EMAIL_ACCOUNT_ID` / `FROM_EMAIL` | Mailbox tested |
| `INBOX_COUNT` / `SPAM_COUNT` / `PROMOTION_COUNT` / `UNDELIVERED_COUNT` | Outcome bucket counts (sum ≈ 100) |
| `STATUS_CD` | `completed` / `sending_emails` / `checking_placement` / `failed` |
| `PROVIDERS` / `EMAILS` / `PLACEMENT_CHECKS` | VARIANT — flatten for per-provider drill-down |
| `UPDATED_AT_UTC` | Most recent test time |

Complementary to the population-level `DIM_MONGO_DOMAIN_DIAGNOSES` view: per-mailbox outcomes when auth state is healthy but performance still looks off.

### Sequence autopause on high bounce (PLANNED)

Auto-pause a sequence at the team/mailbox level when bounce rate crosses a threshold within a rolling window. Status: planned, not yet shipped — no Snowflake signal yet. Track via the project channel and add the table reference here when it ships.

______________________________________________________________________

## Tables

### `FCT_MONGO_EMAILER_MESSAGES`

**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_MESSAGES`

See data catalog for full column reference.

- **Primary timestamp:** `COMPLETED_AT`
- **Status filter:** `status IN ('Completed', 'Failed')` — completed = successfully sent, failed = attempted but failed. Other statuses (scheduled, paused, draft, etc.) are not relevant for deliverability.
- **Type filter:** `TYPE IN ('outreach_automatic_email', 'outreach_manual_email')`. Extension emails (`extension`) can be added but are excluded for cold outreach analyses.
- **Join to mailbox:** `EMAIL_ACCOUNT_ID` → `DIM_MONGO_EMAIL_ACCOUNTS.EMAIL_ACCOUNT_ID`
- **Join to tracking domain:** `TRACKING_DOMAIN_ID` → `DIM_MONGO_TRACKING_DOMAINS.TRACKING_DOMAIN_ID`

______________________________________________________________________

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

______________________________________________________________________

### `DIM_MONGO_TRACKING_DOMAINS`

**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TRACKING_DOMAINS`

Tracking subdomains used for email activity and engagement tracking. Connects to emailer messages via `TRACKING_DOMAIN_ID`.

- **`TYPE_CD`** values: `custom` (unique to the company), `shared` (Apollo-provided), `NULL` (not configured — nullified subdomains stay NULL)

______________________________________________________________________

### `DIM_MONGO_DOMAIN_DIAGNOSES`

**Full path:** `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_DOMAIN_DIAGNOSES`

Domain authentication health per (team, domain). Not directly joined to emailer messages — connect via team + domain, or via `DIM_MONGO_EMAIL_ACCOUNTS`.

- **Best timestamp (current state):** `UPDATED_AT_UTC`
- **Healthy domain (latest snapshot):** `SPF_STATUS_CD = 'good' AND DKIM_STATUS_CD = 'good' AND DMARC_STATUS_CD = 'good'`
- Only relevant for **custom (non-free) domains** — free email providers don't support this
- Diagnoses can be triggered automatically or manually by the user
- Refresh cadence: **weekly** (Sunday/Monday). Not CDC — between refreshes the table is static.

**Historical status arrays (added 2026-05-06):** Three VARIANT columns store the per-category history.

| Column | Contains |
|---|---|
| `SPF_STATUS_HISTORY` | Array of `{recorded_at:{"$date": ts}, status, spf_values[]}` events |
| `DKIM_STATUS_HISTORY` | Array of `{recorded_at:{"$date": ts}, status, dkim_signature, dkim_values[]}` events |
| `DMARC_STATUS_HISTORY` | Array of `{recorded_at:{"$date": ts}, status, dmarc_values[]}` events |

- **History start:** 2026-05-06. No `recorded_at` exists before that date.
- **Status values:** `good`, `warning`, `error`, `pending` (matches scalar `*_STATUS_CD`).
- **Empty array** = diagnosis still pending (no event yet captured).
- **Parse pattern:**
  ```sql
  TRY_TO_TIMESTAMP_NTZ(h.value:recorded_at:"$date"::string) AS recorded_at
  , h.value:status::string                                  AS status
  FROM <table> d, LATERAL FLATTEN(input => d.spf_status_history) h
  ```
- **Point-in-time status:** For "status as of date D", take the latest history element per category with `recorded_at <= D` (carry forward across refreshes — auth state persists until a new event lands).
- **Worked example:** Domain `acme.com` has SPF history `[{2026-05-06, good}]`, DKIM history `[{2026-05-06, good}, {2026-05-15, warning}]`, DMARC history `[{2026-05-06, good}]`. As-of `2026-05-10` (Sunday of week 2026-05-04), SPF=good, DKIM=good (the 05-15 event is past the as-of), DMARC=good → healthy. As-of `2026-05-17` (Sunday of week 2026-05-11), SPF=good (carried forward — no new SPF event this week), DKIM=warning (05-15 event now in scope), DMARC=good → gray. A category not touched in a given week keeps its last known status; only a new history entry can change it.
- For long-range time series prior to 2026-05-06, use Amplitude events: `Domain Authentication Healthy` / `Domain Authentication Unhealthy`.

______________________________________________________________________

### `DIM_MONGO_BLACKLIST_CHECKS`

Canonical reference: [§ Product Levers → Blocklist / blacklist checks](#blocklist--blacklist-checks-mailbox-level-user-initiated) above, and the data-catalog entry [`DIM_MONGO_BLACKLIST_CHECKS.md`](../data-catalog/context/DIM_MONGO_BLACKLIST_CHECKS.md).

______________________________________________________________________

### `DIM_MONGO_EMAIL_ACCOUNT_PURCHASES` / `DIM_MONGO_DOMAIN_PURCHASES`

Purchase records for mailboxes and domains bought through Apollo. Connect to `DIM_MONGO_EMAIL_ACCOUNTS` or `DIM_MONGO_EMAIL_ACCOUNTS_RT_VW`.

______________________________________________________________________

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

______________________________________________________________________

## Common Segmentation Dimensions

| Dimension | Source | Notes |
|---|---|---|
| **Mailbox provider type** | `DIM_MONGO_EMAIL_ACCOUNTS.TYPE_CD` | gmail, ms_exchange, nylas, mailgun, sendgrid, etc. |
| **Direct vs aggregate** | `DIM_MONGO_EMAIL_ACCOUNTS.TYPE_CD` | Direct: gmail, ms_exchange, nylas. Aggregate: sendgrid, mailgun. |
| **Tracking subdomain type** | `DIM_MONGO_TRACKING_DOMAINS.TYPE_CD` | custom, shared, NULL |
| **Free domain** | `ANALYTICS_DB.ANALYTICS.FREE_EMAIL_PROVIDER_DOMAINS` | Important segmentation factor — free domains behave differently and are excluded from domain-level analyses |
| **Managed vs unmanaged** | `DIM_SALESFORCE_APOLLO_TEAMS` + `DIM_SALESFORCE_ACCOUNTS` | See definition below — used to compare deliverability outcomes and to apply different gray-area thresholds |

______________________________________________________________________

## Managed vs Unmanaged Teams (Deliverability Enforcement)

For deliverability work, "managed" = team has a named CS owner (AM or GTME) on its Salesforce account AND carries paid ARR. Unmanaged = everyone else (typically self-serve, no human contact). We segment by this dimension because deliverability outcomes differ materially and because the **gray-area threshold** between healthy and critical is calibrated differently for the two populations (see classification below).

**Canonical filter:**

```sql
WITH managed AS (
  SELECT DISTINCT t.apollo_team_id::string AS team_id
  FROM   ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS t
  JOIN   ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS dsa
    ON   dsa.id = t.sfdc_account_id
  WHERE  (dsa.am_name IS NOT NULL OR dsa.gtme_name IS NOT NULL)   -- has CS owner
    AND  t.apollo_team_id IS NOT NULL
    AND  t.arr > 0                                                -- paid
)
-- Then: LEFT JOIN managed m ON m.team_id = eml.team_id
--       CASE WHEN m.team_id IS NOT NULL THEN 'managed' ELSE 'unmanaged' END
```

Notes:

- `am_name` (Account Manager) and `gtme_name` (GTM Engineer) are both forms of CS ownership — either qualifies.
- `arr > 0` excludes free / churned / zero-ARR teams from the managed bucket.
- Apply managed as a **segmentation cut**, not as an exclusion — after standard exclusions (internal teams, free domains, sendgrid/mailgun).

______________________________________________________________________

## Domain Health Classification

Auth state is graded per (team, domain) using the latest entry in each `*_STATUS_HISTORY` array with `recorded_at <= as_of_date` (carry forward across refreshes — see `DIM_MONGO_DOMAIN_DIAGNOSES` above).

| Band | Definition | Operational meaning |
|---|---|---|
| **Healthy** | `SPF = 'good' AND DKIM = 'good' AND DMARC = 'good'` | Safe to send. **Two variants — be explicit which you use; see note below.** |
| **Critical** | `SPF = 'error' AND DKIM = 'error'` (regardless of DMARC — this also covers the all-three-error case) | Should not be sending — escalate / pause |
| **Gray area** | Everything that is neither healthy nor critical (warnings, partial-good, single-error states, etc.) | Sending allowed; not at scale. Threshold between gray and critical is calibrated differently for managed vs unmanaged — **exact rubric owned by Valery Satsevich (Iris), target close 2026-05-27.** |
| **Pending** | No `recorded_at <= as_of_date` exists in any of the three history arrays | Diagnosis has not run yet — treat as unknown, not as bad |

> **"Healthy" — two variants. Always label which one a given report uses.**
>
> 1. **Auth-only** (default): 3-of-3 `good` on SPF/DKIM/DMARC.
> 1. **Auth + tracking subdomain**: 3-of-3 `good` AND a custom tracking subdomain is configured (`DIM_MONGO_TRACKING_DOMAINS.TYPE_CD = 'custom'`).
>
> Variant 2 is the stricter sender-reputation bar — Apollo-shared click-tracking CNAMEs hurt domain trust. Use it for reputation-sensitive contexts (CS audits, scaled outbound playbooks); use variant 1 for headline rollups.

______________________________________________________________________

## % Healthy Domains In Use — Weekly

Headline deliverability-enforcement KPI: of all (team, domain) pairs that **actually sent email** in a given window, what % were healthy at the end of that window. "In use" matters because a dormant domain's auth state is operationally irrelevant.

**Definitions:**

| Term | Definition |
|---|---|
| **In-use pair** | A distinct (team_id, `send_from:domain`) that produced at least one `Completed`/`Failed` outreach email in the window, after standard exclusions (internal teams, free domains, sendgrid/mailgun). |
| **Window — 7d** | Pair sent in the target ISO week (Mon–Sun). |
| **Window — 28d** | Pair sent in the target week or any of the 3 prior weeks. |
| **As-of date** | Window end (Sunday of target week). Status = latest history entry per category with `recorded_at <= as_of_date`. |
| **% healthy** | `count(healthy) / count(in_use_pairs)`. Report alongside % critical, % gray, and % pending. State which **healthy** variant (auth-only vs auth + tracking) was used. |

**Why two windows:** 7d = active this week; 28d = recently-active pairs whose auth still matters. **Initial observation** (week of 2026-05-04, n=1 snapshot): 28d catches 28% more pairs than 7d in managed (10,222 vs 7,985) and 44% more in unmanaged (34,447 vs 23,895); the extra pairs skew 2 pp less healthy in both segments — consistent with the hypothesis that broken domains often paused sending *because* of auth problems, but not yet confirmed across multiple weeks.

**Canonical query:** [`teammates/valery_satsevich/queries/deliverability_debrief.sql`](../teammates/valery_satsevich/queries/deliverability_debrief.sql) — `q3_pct_healthy_in_use_weekly`, produces `(week_start, window, segment) → total / healthy / unhealthy / pending` with managed/unmanaged split. Currently uses **auth-only** healthy and a simplified 3-band classification (healthy / unhealthy / pending). Update to the 4-band (healthy / gray / critical / pending) split is pending the managed-vs-unmanaged gray-area rubric (target close 2026-05-27, Valery). The deliverability-debrief skill consumes this query directly — there is no separate standing copy.

**Known limitations:**

- History data starts 2026-05-06; weeks before week of 2026-05-04 are excluded.
- Diagnoses refresh weekly (Sun/Mon) — a domain fixed mid-week won't flip to healthy until the next snapshot.

______________________________________________________________________

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

> **Bounce thresholds (direct sends only):** > 5% overall bounce rate is high. > 10% is extremely high. **These thresholds do NOT apply to SendGrid/Mailgun.** ESP-aggregate channels structurally bounce 2–4× higher than direct sends because of different pool / reputation models — assigning red/yellow status to them by direct-send thresholds is a misread. Either report ESP channels separately with their own baseline, or label as "channel: ESP" with no traffic-light status. Never mix ESP and direct sends in the same scorecard.

> **Recency bias:** Engagement metrics (open rate, reply rate) are measured at send date (`completed_at`), but opens and replies can trickle in for days or weeks after sending. The most recent week in any report will appear lower than fully-baked weeks — this is expected, not a signal. If someone flags a drop in the latest week, list recency as a possible explanation before drawing conclusions.

______________________________________________________________________

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
