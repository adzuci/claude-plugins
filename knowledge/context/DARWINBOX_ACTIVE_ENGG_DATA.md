# DARWINBOX_ACTIVE_ENGG_DATA

> Active engineering headcount from Darwinbox HR system.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DARWINBOX_ACTIVE_ENGG_DATA` |
| **Grain** | One row per active engineer |
| **Row count** | ~1.1K (2026-03-06) — small reference table |
| **Refresh cadence** | Daily (external data ingestion from Darwinbox API) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | External data ingestion pipeline. Config: `dags/external_data_ingestion/config/darwinbox_engg.yml` |

## Description

HR headcount table for engineering (28 distinct users). Primarily queried for the EMAIL column to map engineers to other systems (GitHub, Snowflake). Very small but widely used as a reference/lookup.

## Upstream Sources

| Source | Relationship |
|---|---|
| Darwinbox HR API | Primary source |

## Key Columns

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| EMAIL | TEXT | 29 | 3,054 | Engineer email | **Primary join key** — maps to GitHub, Snowflake users |
| NAME | TEXT | 1 | 1 | Engineer name | Rarely queried directly |
| LEVEL | TEXT | 1 | 1 | Engineering level | |

## How It's Used

### Common query patterns
- **Email-based joins**: Map engineers to GitHub authors, Snowflake query users
- **Headcount filtering**: Filter engineering metrics to active employees only

### Key consumers
- Engineering dashboards (alongside GITHUB_DEVELOPER_TEAMS, FCT_LEADGENIE_GITHUB_COMMIT_DATA)

## Known Issues & Gotchas

- EMAIL is the only heavily-used column — essentially a lookup of "who is an active engineer"
- Very small (~1.1K rows) — no performance concerns
- Separate `darwinbox.yml` config exists for broader Darwinbox data (non-engineering)

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history analysis | Brighid (via Claude) |
