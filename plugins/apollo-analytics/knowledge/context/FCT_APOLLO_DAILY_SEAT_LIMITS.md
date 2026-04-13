# FCT_APOLLO_DAILY_SEAT_LIMITS

> Daily snapshot of seat limits (paid, free, trial, total) for every Apollo team, with change tracking and categorization.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_APOLLO_DAILY_SEAT_LIMITS` |
| **Grain** | One row per team per day |
| **Row count** | <!-- TODO: check --> |
| **Refresh cadence** | Daily |
| **Trust level** | Authoritative |
| **Owner** | Analytics / Data Engineering |
| **DAG** | <!-- TODO: confirm --> |

## Description

Tracks the daily seat limit state for each Apollo team, broken down into paid, free, and trial seat counts. Includes prior-day comparisons, change flags, and change categorization (aligned with financial model logic). Useful for analyzing seat purchase behavior, upgrade/downgrade patterns, and seat inflation analysis.

## Upstream Sources

| Source | Relationship |
|---|---|
| Salesforce opportunities | Drives paid seat limits via SFDC opp dates |
| Mongo teams product info | `FIRST_PLAN_DATE`, `LAST_PLAN_DATE` |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `APOLLO_TEAM_ID` | TEXT | Team identifier | Join key |
| `DATE_PERIOD` | DATE | Date of record (PST) | |
| `PAID_SEAT_LIMIT` | NUMBER | Paid seats on this day | Primary column for seat count analysis |
| `FREE_SEAT_LIMIT` | NUMBER | Free seats on this day | |
| `TRIAL_SEAT_LIMIT` | NUMBER | Trial seats on this day | |
| `SEAT_LIMIT` | NUMBER | Total seats (paid + free + trial) | |
| `CHANGE_CATEGORY` | TEXT | Category of paid seat change (aligned with financial models) | e.g. 'new', 'expansion', 'contraction', 'churn' |
| `HAS_PAID_SEAT_LIMIT_CHANGE` | BOOLEAN | True if paid seat limit changed vs prior day | |
| `PAID_SEAT_LIMIT_CHANGE` | NUMBER | Delta in paid seats vs prior day | |
| `SEAT_LIMIT_FIRST_PAID_MONTH_RESET` | NUMBER | Seat limit at end of first paid month; resets on new/reactivated customers | Used for cohort anchoring |
| `IS_PAID_ACTIVE` | BOOLEAN | True if paid seat limit > 0 | |
| `IS_LAST_DATE_PERIOD` | BOOLEAN | True if this is the team's last record | |
| `SFDC_ACCOUNT_ID` | TEXT | Parent SFDC account ID | |

## How It's Used

### Common query patterns

- Join to `FCT_DAILY_REVENUE` on `apollo_team_id + date_period` to get seat counts at time of purchase/change
- Filter `HAS_PAID_SEAT_LIMIT_CHANGE = TRUE` to find seat change events
- Use `SEAT_LIMIT_FIRST_PAID_MONTH_RESET` for cohort seat size anchoring

### Key consumers

- Pricing & packaging analysis (seat minimum research)
- Revenue cohort models
- Seat utilization / inflation analysis

## Known Issues & Gotchas

- `CHANGE_CATEGORY` logic is directed by finance — aligns with `FCT_DAILY_REVENUE` change categories
- `SEAT_LIMIT_FIRST_PAID_MONTH_RESET` resets on reactivation (churn > 3 months), so not a true historical anchor

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-25 | Created context file — discovered during 1-seat Org plan pricing analysis | Andrew |
