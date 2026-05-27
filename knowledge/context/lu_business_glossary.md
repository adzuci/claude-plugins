# LU_BUSINESS_GLOSSARY

> Canonical business term definitions with SQL predicates used by the Jarvis plugin to translate exec language into filters.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_BUSINESS_GLOSSARY` |
| **Grain** | term |
| **Grain columns** | term |
| **Row count** | ~42 |
| **Refresh cadence** | manual |
| **Coverage period** | ongoing |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Stores canonical definitions for every business term executives and AEs use when asking data questions. The Jarvis plugin reads this table to resolve ambiguous language (e.g., "core accounts", "WAT", "NRR") into precise SQL filters and column references. AEs own the definitions; DE owns the table infrastructure. Contains ~42 terms spanning metrics, segments, product features, pipeline stages, fiscal concepts, and engineering metrics.

## Upstream Sources

| Source | Relationship |
|---|---|
| Manually curated | Extracted from domain knowledge and AE/Finance input |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| term | VARCHAR(200) | Business term (primary key) | e.g. `ARR`, `WAT`, `Golden Population` |
| category | VARCHAR(50) | Term category | Values: `metric`, `segment`, `product`, `pipeline`, `retention`, `engineering`, `fiscal`, `operations` |
| definition | VARCHAR(4000) | Plain-English definition | Used by the plugin for exec-facing explanations |
| sql_predicate | VARCHAR(4000) | SQL fragment or column reference | Used by the plugin to generate filters |
| related_tables | VARCHAR(2000) | Comma-separated table names where this term is applicable | |
| owner | VARCHAR(200) | Team or person responsible for the definition | |
| aliases | VARCHAR(1000) | Alternative names for this term | e.g. `Annual Recurring Revenue` for `ARR` |
| see_also | VARCHAR(1000) | Related terms worth cross-referencing | |
| created_at | TIMESTAMP_NTZ | Row creation timestamp | |
| updated_at | TIMESTAMP_NTZ | Last update timestamp | |

## Known Issues

- `sql_predicate` is free-text — no validation that the SQL is syntactically correct or references real columns
- Some predicates are column names only (e.g. `ARR column directly`) rather than executable SQL fragments

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
