# FCT_TEAM_CREDITS_DAILY

> Daily credit snapshot per team in wide format — email, export, mobile, dialer, and unified credit limits and usage from Mongo audit reports.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_CREDITS_DAILY` |
| **Grain** | One row per team + date (`team_id` + `ds`) |
| **Row count** | ~71.7M (estimated from catalog) |
| **Refresh cadence** | Daily (Snowflake Task: `TASK_REFRESH_FCT_TEAM_CREDITS_DAILY`, runs at 06:00 UTC) |
| **Trust level** | Canonical (Playground) — higher-trust source than AGG_TEAM_CREDITS but less granular |
| **Owner** | Data Engineering (Brighid Meredith) |
| **DAG** | Snowflake Task `PLAYGROUND.TASK_REFRESH_FCT_TEAM_CREDITS_DAILY` with stored procedure `SP_REFRESH_FCT_TEAM_CREDITS_DAILY` |

## Description

Wide-format daily credit snapshot per team. Contains limits and daily/cycle usage for 5 credit categories: email, export, mobile, dialer (minutes), and unified. This is the simpler, higher-trust Mongo-sourced credit table. For the full credit breakdown by credit_type and feature_type (including credit_sources), see `AGG_TEAM_CREDITS` or the normalized tables `FCT_TEAM_CREDIT_LIMITS_DAILY` / `FCT_TEAM_CREDIT_USE_DAILY`.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` | Primary source — same source as FCT_TEAM_REVENUE_DAILY |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | TEXT | Apollo team ID | FK to DIM_MONGO_TEAMS.TEAM_ID |
| ds | DATE | Snapshot date | Derived from `CREATED_AT_UTC::DATE` |
| email_credit_limit | NUMBER | Email credit upper limit | |
| email_credits_used_today | NUMBER | Email credits consumed today | |
| email_credits_used_in_cycle | NUMBER | Email credits consumed in billing cycle | |
| export_credit_limit | NUMBER | Export credit upper limit | |
| export_credits_used_today | NUMBER | Export credits consumed today | |
| mobile_credit_limit | NUMBER | Mobile credit upper limit | |
| mobile_credits_used_today | NUMBER | Mobile credits consumed today | |
| dialer_credit_limit | NUMBER | Dialer credit upper limit (minutes) | |
| dialer_minutes_used_today | NUMBER | Domestic dialer minutes consumed today | |
| unified_credit_limit | NUMBER | Unified credit upper limit | |
| unified_credits_used_today | NUMBER | Unified credits consumed today | |
| bounced_emails_this_cycle | NUMBER | Bounced email count in billing cycle | |

## How It's Used

### Common query patterns
- Daily credit utilization rates: `email_credits_used_today / NULLIF(email_credit_limit, 0)`
- Teams approaching credit limits: filter where `*_used_in_cycle / NULLIF(*_limit, 0) > 0.9`
- Credit consumption trends over time by team
- Join with `DIM_MONGO_TEAMS` for team attributes (plan, edition, etc.)

### Key consumers
- Analytics team (credit utilization dashboards)
- Downstream tables: `FCT_TEAM_CREDIT_LIMITS_DAILY`, `FCT_TEAM_CREDIT_USE_DAILY` are chained after this task

## Known Issues & Gotchas

- **Duplicate rows in source:** `FCT_MONGO_DAILY_TEAM_AUDIT_REPORTS` has duplicate rows on specific dates (same issue as the revenue table — AuditReportGenerationWorker runs multiple times). Deduplicated via `GROUP BY + ANY_VALUE`.
- **Wide format:** Each credit type is a separate column pair (limit + usage). For normalized credit_type-level analysis, use `FCT_TEAM_CREDIT_LIMITS_DAILY` and `FCT_TEAM_CREDIT_USE_DAILY` instead.
- **No credit_type x feature_type breakdown:** This table does not show which features consumed which credits. Use `FCT_TEAM_CREDIT_USE_DAILY` for that.
- **DQ checks:** Row count, row count regression, duplicate grain, and freshness checks run on each refresh.

## Slack Context

- **Credits dashboard (Brendan Walker):** Trying to understand free user credit consumption paths leading to upgrades — needs this table joined with FCT_DAILY_REVENUE for conversion analysis.

## Business Terms

| Term | Definition |
|---|---|
| credit_limit | Maximum number of credits allocated to a team for a billing cycle |
| credits_used_today | Credits consumed on a single calendar day |
| credits_used_in_cycle | Cumulative credits consumed in the current billing period |
| unified_credit | Apollo's consolidated credit type that can be used across multiple features |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-11 | Created context file | Brighid (via Claude) |
