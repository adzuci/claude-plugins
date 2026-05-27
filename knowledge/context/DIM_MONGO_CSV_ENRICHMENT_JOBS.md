# DIM_MONGO_CSV_ENRICHMENT_JOBS

> One row per CSV enrichment job (data duel). Tracks processed rows, matches, fill counts, and job status.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_CSV_ENRICHMENT_JOBS` |
| **Grain** | One row per CSV enrichment job (`CSV_ENRICHMENT_JOB_ID`) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Enrichment — Mounica Sonikar |

## Key Columns

| Column | Type | Description |
|---|---|---|
| `CSV_ENRICHMENT_JOB_ID` | TEXT | PK |
| `TEAM_ID` | TEXT | Submitting team |
| `MODALITY` | TEXT | Entity type (contacts, organizations) |
| `PROCESSED_ROWS` | NUMBER | Rows processed after dedup — use as denominator for rates |
| `ROW_COUNT` | NUMBER | Raw uploaded row count |
| `MATCHES` | NUMBER | Rows matched to an Apollo record |
| `STATUS_CD` | TEXT | Job status — actual values: `success`, `failed`, `created`. Filter to `'success'` for outcome metrics. |
| `CREATED_AT_UTC` | TIMESTAMP_NTZ | Job creation time UTC |
