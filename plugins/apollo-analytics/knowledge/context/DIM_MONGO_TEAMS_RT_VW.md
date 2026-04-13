# DIM_MONGO_TEAMS_RT_VW

> Real-time view of DIM_MONGO_TEAMS with current plan state. Used to identify teams on specific product plans (Inbound, Dialer) and access the `product_infos` array.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_TEAMS_RT_VW` |
| **Grain** | One row per team (`_ID`) — real-time snapshot |
| **Row count** | ~same as DIM_MONGO_TEAMS (~3.4M) |
| **Refresh cadence** | Real-time view (no materialization lag) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | View over DIM_MONGO_TEAMS — no separate DAG |

## Description

Real-time view variant of `DIM_MONGO_TEAMS`. Use this instead of `DIM_MONGO_TEAMS` when you need current plan state or need to access `product_infos` — a nested array of all plans a team has ever had. Primary use case is identifying teams currently on Inbound or Dialer plans by flattening `product_infos` and filtering on `plan_id`.

## Upstream Sources

| Source | Relationship |
|---|---|
| `DIM_MONGO_TEAMS` | View over the base table with real-time data |
| MongoDB `teams` collection | Ultimately sourced from here |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `_ID` | TEXT | Team ID | PK. Equivalent to `APOLLO_TEAM_ID` in SFDC tables |
| `PRODUCT_INFOS` | VARIANT | Array of all plan objects for this team | **Must use `LATERAL FLATTEN`** — see pattern below |
| `TEAM_NAME` | TEXT | Team name | |
| `CREATED_AT` | TIMESTAMP | Team creation timestamp | |

### `product_infos` array element fields

Each element in `product_infos` after flattening (`pf.value`):

| Field | Extract as | Description |
|---|---|---|
| `plan_id` | `pf.value:"plan_id"::string` | Plan identifier — filter with `ILIKE '%inbound%'` or `'%dialer%'` |
| `start_date` | `pf.value:"start_date"::date` | Plan start date — used for SFDC opp matching (±1 day) |
| `end_date` | `pf.value:"end_date"::date` | Plan end date |
| `canceled_at` | `pf.value:"canceled_at"::date` | Cancellation date |

## How It's Used

### Common query patterns

**Identify teams on Inbound plans (for SFDC opp matching):**
```sql
SELECT
    mt._id                               AS apollo_team_id,
    pf.value:"plan_id"::string           AS plan_id,
    pf.value:"start_date"::date          AS start_date,
    pf.value:"end_date"::date            AS end_date,
    pf.value:"canceled_at"::date         AS canceled_at
FROM analytics_db.analytics_dataplatform.dim_mongo_teams_rt_vw mt
CROSS JOIN LATERAL FLATTEN(input => mt.product_infos) AS pf
WHERE pf.value:"plan_id"::string ILIKE '%inbound%'   -- or '%dialer%'
  AND mt._id NOT IN ('68e6fb07946dcf000d2e3516', '620210171b9d04008e2ac0e0')
```

**Typical join to DIM_SALESFORCE_APOLLO_TEAMS:**
```sql
INNER JOIN analytics_db.analytics.dim_salesforce_apollo_teams sat
  ON mt._id = sat.apollo_team_id
```

### Key consumers
- **CBR Inbound / Dialer ARR query** — plan identification for SFDC sales motion matching
- Any analysis requiring current plan state or plan history

## Known Issues & Gotchas

- **`product_infos` requires `LATERAL FLATTEN`** — you cannot filter on plan_id without flattening first
- **Use `_ID` not `TEAM_ID`** — the PK column is `_ID` (MongoDB convention). When joining to SFDC tables use `_ID = apollo_team_id`
- **RT_VW vs base table**: Use RT_VW when you need current/live plan state. Use `DIM_MONGO_TEAMS` for historical snapshots or when RT latency doesn't matter
- **`product_infos` contains all historical plans** — filter on `start_date` / `end_date` / `canceled_at` if you only want active plans

## Business Terms

| Term | Definition |
|---|---|
| `product_infos` | JSON array of all subscription plan objects a team has had, including plan_id, billing dates, cancellation info |
| Inbound plan | Plan with `plan_id ILIKE '%inbound%'` — Apollo Inbound product add-on |
| Dialer plan | Plan with `plan_id ILIKE '%dialer%'` — Apollo Parallel Dialer product add-on |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created — documented product_infos pattern + Inbound/Dialer plan identification | Leo |
