# INT_TEAM_PRODUCT_INFO_CLEANED

> Cleaned team-level product/plan information. Intermediate table.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.INT_TEAM_PRODUCT_INFO_CLEANED` |
| **Grain** | One row per team-product mapping |
| **Row count** | ~5.3M (2026-03-06) |
| **Refresh cadence** | Unknown — not found in airflow-dags. Likely dbt model. |
| **Trust level** | Use with caution (ANALYTICS schema, INT prefix = intermediate) |
| **Owner** | <!-- TODO --> |
| **DAG** | Not found in airflow-dags. INT prefix suggests dbt intermediate model. |

## Description

Intermediate table with cleaned product/plan info per team (25 distinct users, 11.3K queries). The "INT_" prefix indicates this is a dbt intermediate model — cleaned/transformed version of raw product info, likely feeding downstream dimension tables.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_MONGO_TEAMS_PRODUCT_INFO | Raw source (ANALYTICS_DATAPLATFORM) |
| Product/plan configuration | Plan details |

## Key Columns

<!-- TODO: Full column list — run `SHOW COLUMNS IN TABLE ANALYTICS_DB.ANALYTICS.INT_TEAM_PRODUCT_INFO_CLEANED` -->

Known columns from query usage (Hex notebooks):
- First paid plan date / first purchase date — used as cohort entry point
- Product/plan info — edition, pricing variant, seat counts

## How It's Used

### Common query patterns

**Cohort expansion analysis (Growth Expansion Hex notebook):**
```sql
-- % teams expanding (seats/credits) from first paid plan — weekly cohort
-- Cohort entry: first paid >= 2025-06-01, 90-day / 13-week window
SELECT ...
FROM analytics_db.analytics_datascience.int_team_product_info_cleaned
CROSS JOIN generator(rowcount => 400)  -- date spine
WHERE first_paid_date >= '2025-06-01'
...
```

**FY27 R&D activation gate:**
- Used to check whether a team converted to paid within `activation_window` days of creation
- Also used in Custom-edition seat expansion analysis (cohort entry = first paid in 2025)

### Key consumers
- Growth Expansion Hex dashboard (`dataframe_5` — cohort expansion rates)
- FY27 R&D Performance Dashboard (activation gate, Custom plan expansion)
- Pricing Dashboard (migration cohort analysis)

## Known Issues & Gotchas

- INT prefix = dbt intermediate model — not a final reporting table. Downstream consumers prefer this over raw `DIM_MONGO_TEAMS_PRODUCT_INFO` because it's cleaned.
- In ANALYTICS schema (mixed trust) — but widely used in production Hex dashboards.
- `analytics_datascience` schema reference appears in some Hex queries — verify correct schema before querying (`ANALYTICS` vs `ANALYTICS_DATASCIENCE`).

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial — column usage pending) | Brighid (via Claude) |
| 2026-03-20 | Added usage context from Hex notebooks — cohort expansion, activation gate, Custom plan expansion | Leo (via Claude) |
