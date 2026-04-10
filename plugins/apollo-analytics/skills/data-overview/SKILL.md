---
name: data-overview
description: Overview of data infrastructure, key datasets, and how to get access. Use when the user asks where Apollo data lives, how to find a Snowflake table, how to get data access, what schema to query, or wants to search the data catalog.
---

# Data Overview

Use this skill when someone asks about the data platform, where data lives, how to get access, or how to find a specific dataset.

## Warehouse & Key Schemas

Primary warehouse: **Snowflake** (`APOLLOORG-APOLLO` account) using `ANALYTICS_DB` as the main analytics database, with `ELT_WH` / `ELT_WH_DP` as primary warehouses for compute.

| Schema | Purpose | Owner |
|---|---|---|
| `ANALYTICS` | Core product / revenue / GTM analytics marts and facts used for standard reporting & BI | Data Platform / Analytics |
| `ANALYTICS_DATAPLATFORM` | Raw + staged warehouse mirrors (e.g. Mongo snapshots, GitHub timelines) powering downstream models | Data Platform |
| `ANALYTICS_DATASCIENCE` | Data science / experimentation and advanced modeling workspace | Data Science / Analytics |
| `PLAYGROUND` | Sandboxed schema for ad-hoc analysis, prototyping, and engineer experimentation | Data Platform (developer role) |

## Finding the Right Table

Search the governed data catalog:

```sql
SELECT table_name, description, grain, trust_tier, known_issues, key_columns
FROM ANALYTICS_DB.PLAYGROUND.LU_DATA_CATALOG
WHERE status IN ('playground', 'production')
  AND (LOWER(table_name) ILIKE '%<keyword>%' OR LOWER(description) ILIKE '%<keyword>%')
ORDER BY
  CASE trust_tier WHEN 'canonical' THEN 1 WHEN 'preferred' THEN 2 WHEN 'reference' THEN 3 ELSE 4 END
LIMIT 20
```

Look up business terms before writing SQL:

```sql
SELECT term, definition, sql_predicate, related_tables
FROM ANALYTICS_DB.PLAYGROUND.LU_BUSINESS_GLOSSARY
WHERE LOWER(term) ILIKE '%<term>%'
```

## ETL / ELT Pipelines

- **Pipeline tool:** dbt (`dbt_apollo` project) for modeling, with multiple warehouse size profiles
- **Orchestration:** Airflow DAGs for ingestion into Snowflake (e.g. Mongo snapshot DAGs), plus dbt scheduled runs
- **On-call/owner:** Data Platform team (`#data-infra` / analytics engineering) owns ingestion + dbt pipelines

## Analytics Tools

| Tool | Used by | Access request |
|---|---|---|
| Apollo Analytics (in-app) | GTM (Sales, RevOps, Marketing), CS | Enabled via Apollo plan; workspace admins manage access |
| Looker / internal BI | Product, Analytics, Leadership | Ask in `#xfn-team-discovery-and-analytics` for dashboard/report access |
| Hex | Analytics & Data teams, some EMs | Request project / dataset access from analytics owners or `#xfn-team-discovery-and-analytics` |

## Getting Access

1. **Warehouse / ETL / analytics tooling** (Snowflake, dbt, Hex, Looker): open an Infra Access or analytics request ticket following the engineering env guide, and post context in `#data-infra` or `#xfn-team-discovery-and-analytics` as needed.
1. **In-app Apollo Analytics or GTM dashboards**: work through your Apollo workspace admin / GTM ops, or file a support ticket via the Apollo "Submit a request" page if it's customer-facing.

## Output Format

When someone asks "where does X data live?", present:

> **Dataset:** [table_name]
> **Schema:** [schema] | **Grain:** [grain] | **Trust tier:** [tier]
> **Description:** [what it contains]
> **Key columns:** [relevant columns]
> **Known issues:** [any caveats]
> **Access:** [how to get it]

## Gotchas

- Trust tier matters: **canonical** > **preferred** > **reference** > **avoid** (never query `avoid` tables)
- `PLAYGROUND` tables may change without notice — check `LU_DATA_CATALOG.status` before building on them
- Large tables (`DIM_TEAMS_DAILY` at 8.6B rows, `FCT_AMPLITUDE_EVENTS` at ~20B rows) require date filters — never scan them fully
- Business terms have specific Apollo definitions in `LU_BUSINESS_GLOSSARY` — do not guess what "active", "churn", or "conversion" means
