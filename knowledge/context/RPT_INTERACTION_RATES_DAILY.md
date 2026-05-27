# RPT_INTERACTION_RATES_DAILY

> Daily support interaction rates — human vs AI deflection rates for all and paid users (L7 rolling).

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.RPT_INTERACTION_RATES_DAILY` |
| **Grain** | One row per DATE_DAY |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Standard — pre-computed report table |
| **Owner** | Analytics / Support |

## Description

Pre-aggregated daily report of support interaction rates with L7 (last 7 day) rolling metrics. Tracks human interactions, AI-only interactions, support team interactions, and computes deflection rates for all users and paid users separately. Used by support analytics and Looker (686 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_SUPPORT_CONVERSATIONS | Conversation-level data |
| Support interaction pipeline | Classifies interactions by type |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DATE_DAY | DATE | Calendar date (primary key) | |
| ACTIVE_USERS_L7 | NUMBER | Active users in last 7 days | |
| HUMAN_INTERACTIONS_L7 | NUMBER | Human-handled interactions (L7) | |
| AI_ONLY_INTERACTIONS_L7 | NUMBER | AI-only interactions (L7) | |
| SUPPORT_TEAM_AND_FIN_INTERACTIONS_L7 | NUMBER | Support team + Fin interactions (L7) | |
| PAID_ACTIVE_USERS_L7 | NUMBER | Paid active users (L7) | |
| CUSTOMER_INTERACTION_RATE | NUMBER | % of active users who interacted with support | |
| HUMAN_INTERACTION_RATE | NUMBER | % of interactions handled by humans | |
| DEFLECTION_RATE | NUMBER | % of interactions handled by AI only | Key AI effectiveness metric |
| PAID_CUSTOMER_INTERACTION_RATE | NUMBER | Interaction rate for paid users only | |
| PAID_HUMAN_INTERACTION_RATE | NUMBER | Human interaction rate for paid users | |
| PAID_DEFLECTION_RATE | NUMBER | AI deflection rate for paid users | |

## How It's Used

### Common query patterns

- Track AI deflection rate trends over time
- Compare paid vs all-user interaction patterns
- Support capacity planning (human interaction volume)

### Key consumers

- Support analytics (686 queries/14d)
- Looker support dashboards
- AI effectiveness reporting

## Known Issues & Gotchas

- L7 rolling window — each day's numbers reflect the prior 7 days, NOT just that day
- Rates are NUMBER type (likely 0-1 scale or 0-100) — verify scale before reporting
- Only 15 columns — simple pre-aggregated report, not granular
- No segment or team breakdown — company-level only

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
