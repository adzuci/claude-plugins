# FCT_POTENTIAL_FRAUD_TEAMS

> Fraud signal flags per team — boolean indicators for various fraud/abuse patterns.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_FRAUD.FCT_POTENTIAL_FRAUD_TEAMS` |
| **Grain** | One row per TEAM_ID |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative for fraud flags |
| **Owner** | Fraud Analytics (Taomei Li / Kaitlyn Maglietto) |

## Description

Team-level fraud signal table with boolean flags for various fraud patterns: high credit usage, payment failures, high risk scores, invitation overuse, domain abuse, IP-based multi-team creation, and excessive login attempts. Used by Fraud Looker dashboards (2,515 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB team data | Team attributes |
| Fraud detection pipeline | Computes fraud signal flags |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| TEAM_ID | TEXT | Primary key — maps to APOLLO_TEAM_ID | |
| TEAM_CREATED_DATE | DATE | When the team was created | |
| DELETED | BOOLEAN | Whether the team has been deleted | |
| IS_SOURCE_DELETED | BOOLEAN | Whether the source record is deleted | |
| POTENTIAL_FRAUD_HIGH_CREDIT_USAGE | BOOLEAN | High credit consumption pattern | |
| POTENTIAL_FRAUD_PAYMENT_FAILURES | BOOLEAN | Pattern of payment failures | |
| POTENTIAL_FRAUD_HIGH_RISK_SCORE | BOOLEAN | High risk score from fraud model | |
| POTENTIAL_FRAUD_INVITATION_OVERUSE | BOOLEAN | Excessive invitation/referral usage | |
| POTENTIAL_FRAUD_MANY_BLOCKS | BOOLEAN | Many blocks/bans on the team | |
| POTENTIAL_FRAUD_DOMAIN | BOOLEAN | Suspicious domain patterns | |
| POTENTIAL_FRAUD_MANY_TEAMS_CREATED_PER_IP | BOOLEAN | Multiple teams from same IP | |
| POTENTIAL_FRAUD_EXCESSIVE_LOGINS_ON_CREATION_DAY | BOOLEAN | Suspicious login pattern on day 1 | |

## How It's Used

### Common query patterns

- Aggregate fraud signal prevalence: SUM(POTENTIAL_FRAUD_*::INT) by date
- Join to DIM_TEAMS_DAILY for segment-level fraud analysis
- Filter out potential fraud teams from other analyses

### Key consumers

- Fraud Looker dashboards (2,515 queries/14d)
- Taomei Li (Fraud Analytics)
- Kaitlyn Maglietto (HVO Signals / Fraud)

## Known Issues & Gotchas

- TEAM_ID maps to APOLLO_TEAM_ID (not SFDC_TEAM_ID)
- Boolean flags are independent — a team can trigger multiple flags simultaneously
- DELETED and IS_SOURCE_DELETED are different: DELETED is application-level, IS_SOURCE_DELETED is source system
- No severity scores — all flags are binary (true/false)

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
