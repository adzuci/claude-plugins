# DIM_MONGO_SSO_CONFIGS

> One row per SSO configuration per team. Tracks which teams have set up SSO (OAuth or SAML), which identity provider they use, and whether the config is active or partial.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_SSO_CONFIGS` |
| **Grain** | One row per SSO config (`SSO_CONFIG_ID`) — a team can have multiple configs |
| **Row count** | <!-- TODO: check --> |
| **Refresh cadence** | Daily (LOAD_DATE) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Engineering / Data Platform |
| **DAG** | <!-- TODO: confirm --> |

## Description

Dimension table sourced from MongoDB capturing SSO configuration state for Apollo teams. A team may have zero, one, or multiple SSO config records (e.g. both OAuth and SAML set up). Use `ACTIVE = TRUE` to filter to live configurations. Use `PARTIAL = TRUE` to identify incomplete setups (SP entity ID only, IDP not yet fully configured).

SSO is an Org-plan-only feature — presence of a config indicates the team is on Org or was at some point. Useful for analyzing SSO adoption rates, IDP distribution, and whether SSO is a driver of Org plan purchases.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `SSO_CONFIG_ID` | TEXT | Unique SSO config identifier | PK |
| `TEAM_ID` | TEXT | Team this config belongs to | Join key — note: `TEAM_ID` not `APOLLO_TEAM_ID` |
| `IDP` | TEXT | Identity provider | Values: `gmail`, `ms_exchange`, `okta`, `entra_id` |
| `TYPE` | TEXT | SSO protocol | `oauth` or `saml` |
| `ACTIVE` | BOOLEAN | Config is currently active | Filter to `ACTIVE = TRUE` for live SSO |
| `PARTIAL` | BOOLEAN | Incomplete setup | `TRUE` = SP entity ID only, IDP not fully configured |
| `CREATED_AT_UTC` | TIMESTAMP_NTZ | When config was created | |
| `UPDATED_AT_UTC` | TIMESTAMP_NTZ | Last update | |
| `LOAD_DATE` | DATE | Snowflake load date | |

## How It's Used

### Common query patterns

```sql
-- Teams with active SSO (any IDP)
SELECT DISTINCT team_id FROM analytics_db.analytics_dataplatform.dim_mongo_sso_configs
WHERE active = true;

-- SSO adoption rate among Org plan teams
SELECT
    count_if(s.team_id is not null) as sso_configured,
    count_if(s.active = true) as sso_active,
    count(*) as total_teams
FROM analytics_db.analytics_datascience.dim_teams t
LEFT JOIN analytics_db.analytics_dataplatform.dim_mongo_sso_configs s
    ON t.apollo_team_id = s.team_id AND s.active = true
WHERE t.team_edition ilike 'custom%' AND t.is_paid_ind = true;
```

### Key consumers

- Pricing & packaging analysis (SSO as Org plan driver)
- Security/compliance feature adoption tracking
- Onboarding analysis

## Known Issues & Gotchas

- Join key is `TEAM_ID`, not `APOLLO_TEAM_ID` — easy to miss when joining to DIM_TEAMS or FCT_DAILY_REVENUE
- A team can have multiple rows (multiple configs) — use `DISTINCT team_id` or aggregate when counting teams
- `PARTIAL = TRUE` records are incomplete setups; exclude them when measuring active SSO adoption
- SSO is Org-plan-only — non-Org teams with a config may indicate recent downgrades or legacy data

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-25 | Created context file — discovered during 1-seat Org plan SSO analysis | Andrew (via Jarvis) |
