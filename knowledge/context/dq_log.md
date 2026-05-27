# DQ_LOG

> Append-only data quality check log written by PLAYGROUND stored procedures.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.DQ_LOG` |
| **Grain** | (table_name, check_name, checked_at) |
| **Grain columns** | table_name, check_name, checked_at |
| **Row count** | varies (append-only) |
| **Refresh cadence** | daily (appended by each procedure run) |
| **Coverage period** | ongoing |
| **Trust level** | Reference |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Every stored procedure in the PLAYGROUND schema logs its quality checks here. Row count checks, row count regressions, duplicate grain checks, freshness checks, and table-specific assertions all append a result row. This table is the paper trail for the DQ framework — not a source of truth for business metrics, but the receipt that confirms they ran.

## Upstream Sources

| Source | Relationship |
|---|---|
| PLAYGROUND stored procedures | Each procedure INSERTs one row per check |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| table_name | VARCHAR | Name of the table being checked | e.g. `FCT_TEAM_REVENUE_DAILY` |
| check_name | VARCHAR | Name of the check | e.g. `row_count`, `duplicate_grain`, `freshness` |
| checked_at | TIMESTAMP_NTZ | When the check ran | Used as the time dimension |
| status | VARCHAR | Result: `PASS` or `FAIL` | |
| detail | VARCHAR | Human-readable description of the result | Includes counts, thresholds, observed values |
| row_count | NUMBER | Row count observed during check | NULL for non-row-count checks |
| expected_min | NUMBER | Minimum expected row count (for regression checks) | NULL if not applicable |
| run_id | VARCHAR | Identifier for the procedure run that logged this row | Useful for grouping multi-check runs |

## Known Issues

- No DDL file exists — column list inferred from procedure logic and check types
- No alerting wired to FAIL rows yet; monitoring requires manual queries against this table

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
