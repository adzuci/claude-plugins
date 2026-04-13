---
name: account-deep-dive
description: Generate a comprehensive profile for a specific team/account combining revenue, credits, support, email, and events
trigger-conditions:
  - "account [name]"
  - "tell me about [company]"
  - "team [name] profile"
  - "[company] deep dive"
  - "[company] account"
  - "look up [company]"
  - "what do we know about [customer]"
  - "team_id [id]"
not-for:
  - "credit utilization overall / across all teams" → use credit-analysis
  - "[area] performance across all accounts" → use product-debrief
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

**Always write an HTML file** to `debriefs/<team_name_slug>_account_<YYYY_MM_DD>.html` and commit it:
```
docs(debrief): add account deep dive <team_name> <YYYY-MM-DD>
```

The HTML file uses dark-mode styling (same palette as product-debrief):
- bg `#0f1117`, surface `#1a1d27`, border `#2e3248`
- accent `#6c63ff`, teal `#00d4aa`, red `#ff6b6b`, yellow `#ffd166`
- System fonts: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Monospace: `'SF Mono', 'Fira Code', 'Consolas', monospace`

### HTML layout

```
Page header (team name + team_id + segment pill + ARR badge)
Risk Signals banner (⚠️ — shown at top if any risk flags exist, hidden if clean)
─────────────────────────────────────────────────────
KPI cards row: ARR | Plan | Region | Billing Term | Is Core
─────────────────────────────────────────────────────
Section: Credit Utilization (30d)
  Table: feature_type | credits_used | limit | utilization % (color-coded: green <70%, yellow 70-90%, red >90%)
Section: Support Activity (30d)
  Table: date | conversation_count | turned_to_ticket
  Note Intercom spike caveat if Mar 2+ data is present
Section: Email Activity (30d)
  Table: date | message_type | delivered | opened | replied | open_rate | reply_rate
Section: Notable Events (90d)
  Timeline list: date · event_type · event_detail
```

Also present a brief inline summary in chat (no HTML rendering in chat):

> **Account Profile: [Team Name]** (team_id: [X])
>
> **Segment:** [segment] | **Plan:** [plan] | **ARR:** $[X] | **Region:** [region]
>
> **Credit Utilization (30d):** [table of feature_type, avg utilization]
>
> **Support (30d):** [X] conversations, [Y] tickets
>
> **Email (30d):** [delivered/opened/replied summary]
>
> **Recent Events:** [notable events list]
>
> **Risk Signals:** [flag anything unusual — declining utilization, support spikes, cancellation events]
>
> HTML saved to: `debriefs/<team_name_slug>_account_<YYYY_MM_DD>.html`

## Gotchas

- `IS_CONVERSATION_TURNED_TICKET` spiked 10x starting Mar 2 — likely Intercom rule change, not real volume. Mention this if the spike appears.
- Credit utilization can return NaN due to `credit_type` name mismatches. Use `feature_type` instead.

## Tracking

- **Query tag:** Pass `--context account_deep_dive` when running queries via `snowflake_query.py`
- **Pulse:** After completing the deep dive, fire: `python3 scripts/snowflake_query.py --pulse account_deep_dive --detail "<team_name> revenue + credits + support"`
