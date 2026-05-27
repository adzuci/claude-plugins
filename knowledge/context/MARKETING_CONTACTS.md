# MARKETING_CONTACTS

> Comprehensive marketing contact dimension — person + account + deal + activity + integration data in one wide table.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.MARKETING_CONTACTS` |
| **Grain** | One row per UNIQUE_ID (person-level) |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing (current snapshot) |
| **Trust level** | Standard — Looker marketing dashboards |
| **Owner** | Analytics / Marketing |

## Description

Extremely wide marketing contact table (256 columns) joining person-level data with account attributes, deal stages, activity metrics, integration flags, and opt-out status. Used heavily by Looker marketing dashboards (2,741 queries/14d). This is a denormalized "everything about a marketing contact" table — person demographics, SFDC linkage, opportunity stages, team/edition info, activity counts, and opt-out/compliance fields.

## Upstream Sources

| Source | Relationship |
|---|---|
| Apollo contacts database | Person attributes |
| SFDC | Opportunity/deal data, contact linkage |
| HubSpot | Marketing opt-out status |
| Customer.io | CIO unsubscribe data |
| Amplitude | Activity counts (L28 rolling window) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| UNIQUE_ID | TEXT | Primary key | |
| PERSON_ID | TEXT | Apollo person ID | |
| EMAIL | TEXT | Contact email | |
| APOLLO_USER_ID | TEXT | Links to APOLLO_USERS if they're a user | |
| APOLLO_TEAM_ID | TEXT | Team linkage | |
| SFDC_CONTACT_ID | TEXT | Salesforce contact | |
| SFDC_ACCOUNT_ID | TEXT | Salesforce account | |
| PRIMARY_PERSONA | TEXT | Persona classification | |
| SENIORITY | TEXT | Seniority level | |
| LEAD_SOURCE | TEXT | How the lead was acquired | |
| MQL_DATE | DATE | Marketing qualified lead date | |
| OPPORTUNITY_ID | TEXT | Associated SFDC opportunity | |
| STAGE_NAME | TEXT | Current opportunity stage | |
| STAGE_*_DATE | DATE | Timestamps for each deal stage | |
| CURRENT_APOLLO_EDITION | TEXT | Team's current plan | |
| IS_PAYING | BOOLEAN | Whether the team is paying | |
| HAS_OPTED_OUT_OF_COMMUNICATIONS | BOOLEAN | Consolidated opt-out flag | |
| ACCOUNT_SEGMENT | TEXT | Account segment (Enterprise, Mid-Market, etc.) | |
| IS_ACTIVE_L28 | NUMBER | Active in last 28 days | NUMBER not BOOLEAN |

## How It's Used

### Common query patterns

- Marketing funnel analysis (lead → MQL → opportunity → closed won)
- Attribution by lead source / UTM parameters
- Segment-level conversion rates
- Opt-out / compliance reporting

### Key consumers

- Looker marketing dashboards (2,741 queries/14d)
- Growth/marketing team
- RevOps pipeline analysis

## Known Issues & Gotchas

- **256 columns** — never use SELECT *. Always specify needed columns.
- Current snapshot only — no historical dimension. For time-series, join to dated tables.
- VARIANT columns (PERSONAL_EMAILS, LINKEDIN_URLS, INDUSTRIES, etc.) need LATERAL FLATTEN
- IS_ACTIVE_L28 is NUMBER (0/1), not BOOLEAN — filter with `= 1` not `= TRUE`
- PAGE_VIEWS_L28 is OBJECT type — needs special handling
- Denormalized: person + team + account + deal data all in one row — be careful about what grain you're analyzing (person vs team vs deal)
- Contains PII (EMAIL, PHONE_NUMBER, names) — handle appropriately

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
