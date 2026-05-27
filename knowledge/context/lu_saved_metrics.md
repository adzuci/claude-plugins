# LU_SAVED_METRICS

> Canonical metric definitions with pre-validated SQL. The Jarvis plugin executes approved metrics verbatim when execs ask metric questions.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS` |
| **Grain** | (metric_name, variant) |
| **Grain columns** | metric_name, variant |
| **Row count** | ~27 |
| **Refresh cadence** | manual |
| **Coverage period** | ongoing |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Stores pre-validated metric SQL definitions that the Jarvis plugin executes verbatim. AE metric owners write and approve the SQL; DE owns the table infrastructure. Plugin only uses rows where `status='approved'` — draft and deprecated rows are silently skipped. No plugin redeploy required when a metric is updated: change the row, set status to `approved`, and the next conversation picks it up. Supports multiple variants per metric (e.g., `ARR by Segment` with `daily_snapshot` and `trend` variants).

## Upstream Sources

| Source | Relationship |
|---|---|
| Manually curated by metric owners | AE team writes SQL; DE validates grain and table references |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| metric_name | VARCHAR(200) | Metric display name (part of PK) | e.g. `ARR by Segment` |
| variant | VARCHAR(200) | Variant of the metric (part of PK) | Default: `default`; e.g. `daily_snapshot`, `trend` |
| description | VARCHAR(4000) | Plain-English description of what the metric measures | Shown to exec when confirming query intent |
| metric_sql | VARCHAR(16000) | Parameterized SQL executed by the plugin | Uses `:param_name` syntax for parameters |
| grain | VARCHAR(200) | Result grain description | e.g. `segment`, `team_id`, `monthly cohort` |
| parameters | VARCHAR(2000) | Parameter names and types | e.g. `ds DATE` |
| default_parameters | VARCHAR(2000) | Default values for parameters | e.g. `ds=CURRENT_DATE()-1` |
| output_columns | VARCHAR(2000) | Expected output column list | Used by plugin to describe result shape |
| related_terms | VARCHAR(1000) | Business glossary terms this metric relates to | Links to LU_BUSINESS_GLOSSARY |
| owner | VARCHAR(200) | Metric owner (AE or team) | |
| status | VARCHAR(20) | `approved`, `draft`, or `deprecated` | Plugin only executes `approved` rows |
| okr_target | VARCHAR(500) | Associated OKR target if applicable | e.g. `82% to 90%` |
| notes | VARCHAR(4000) | Implementation notes, gotchas, caveats | |
| created_at | TIMESTAMP_NTZ | Row creation timestamp | |
| updated_at | TIMESTAMP_NTZ | Last update timestamp | |

## Known Issues

- 3 draft metrics awaiting AE input: M3 Cohort NRR, F14D Habit RA Rate, Inbound Revenue Attribution — these will NOT be executed by the plugin until status is set to `approved`
- `metric_sql` is stored as text with no compile-time validation — a syntax error won't surface until the plugin attempts execution

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
