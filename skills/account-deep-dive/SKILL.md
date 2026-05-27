---
name: account-deep-dive
description: Generate a comprehensive profile for a specific team/account combining revenue, credits, support, email, and events
---

# Account Deep Dive

Use this skill when a user asks about a specific team, account, or customer. Combines multiple data sources into a single profile.

## Required Input

The user must provide a `team_id`. If they provide a company name instead, look it up:

```sql
SELECT team_id, team_name, account_segment
FROM ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES
WHERE LOWER(team_name) ILIKE '%<company_name>%'
LIMIT 5
```

## Query Sequence

Run these in order and compile the results:

### 1. Revenue & Segment

```sql
SELECT r.ds, r.arr, t.account_segment, t.billing_term, t.plan_name, t.region, t.is_core_account
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_REVENUE_DAILY r
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES t ON r.team_id = t.team_id
WHERE r.team_id = :team_id AND r.ds = CURRENT_DATE() - 1
LIMIT 1
```

### 2. Credit Utilization by Type

```sql
SELECT u.ds, u.feature_type, u.credits_used,
       l.credit_limit,
       ROUND(DIV0(u.credits_used, l.credit_limit) * 100, 1) AS utilization_pct
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_USE_DAILY u
LEFT JOIN ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDIT_LIMITS_DAILY l
    ON u.team_id = l.team_id AND u.ds = l.ds AND u.feature_type = l.feature_type
WHERE u.team_id = :team_id AND u.ds >= CURRENT_DATE() - 30
ORDER BY u.ds DESC, u.credits_used DESC
LIMIT 20
```

### 3. Support Activity (Last 30 Days)

```sql
SELECT ds, conversation_count, is_conversation_turned_ticket
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_SUPPORT_DAILY
WHERE team_id = :team_id AND ds >= CURRENT_DATE() - 30
ORDER BY ds DESC
LIMIT 20
```

### 4. Email Activity (Last 30 Days)

```sql
SELECT ds, message_type, SUM(delivered_count) AS delivered, SUM(opened_count) AS opened, SUM(replied_count) AS replied
FROM ANALYTICS_DB.PLAYGROUND.FCT_TEAM_EMAILER_MESSAGES_DAILY
WHERE team_id = :team_id AND ds >= CURRENT_DATE() - 30
  AND message_type IN ('outreach_automatic_email', 'outreach_manual_email')
GROUP BY 1, 2 ORDER BY 1 DESC
LIMIT 20
```

### 5. Notable Events (Last 90 Days)

```sql
SELECT event_date, event_type, event_detail
FROM ANALYTICS_DB.PLAYGROUND.LU_NOTABLE_TEAM_EVENTS
WHERE team_id = :team_id AND event_date >= CURRENT_DATE() - 90
ORDER BY event_date DESC
LIMIT 20
```

## Output Format

Present as a structured profile:

> **Account Profile: [Team Name]** (team_id: [X])
>
> **Segment:** [segment] | **Plan:** [plan] | **ARR:** $[X] | **Region:** [region]
>
> **Credit Utilization (30d):**
> [table of feature_type, avg utilization]
>
> **Support (30d):** [X] conversations, [Y] tickets
>
> **Email (30d):** [delivered/opened/replied summary]
>
> **Recent Events:** [notable events list]
>
> **Risk Signals:** [flag anything unusual — declining utilization, support spikes, cancellation events]

## Gotchas

- `IS_CONVERSATION_TURNED_TICKET` spiked 10x starting Mar 2 — likely Intercom rule change, not real volume. Mention this if the spike appears.
- Credit utilization can return NaN due to `credit_type` name mismatches. Use `feature_type` instead.
