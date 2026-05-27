# FCT_MONGO_CREDIT_USAGE_DETAILS

> Granular credit usage details from MongoDB.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_CREDIT_USAGE_DETAILS` |
| **Grain** | One row per credit usage detail record |
| **Row count** | ~200M (2026-04-17) — grows; events span 2025-12 to present in current build |
| **Refresh cadence** | Daily (dbt model) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |
| **DAG** | Likely `dbt_models_group_1`. Source: MongoDB credit_usage_details collection. |

## Description

Granular credit usage details. One row per credit-consuming event, with attribution (surface, request type, API endpoint) and a direct FK to the underlying HTTP request. Used for detailed credit analysis, surface-level reporting, and debugging.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `credit_usage_detail_id` | TEXT | Primary key | |
| `credit_usage_id` | TEXT | FK to `FCT_MONGO_CREDIT_USAGES` | |
| `team_id` | TEXT | Apollo team ID | |
| `user_id` | TEXT | Apollo user ID | May be null for API-key calls |
| `request_id` | TEXT | Application request ID | |
| `http_request_id` | TEXT | **Direct FK to the HTTP request row** | Deterministic join to raw HTTP V3 / V2 when precision needed |
| `request_type` | TEXT | Type of request | |
| `sidekiq_job_id` | TEXT | If credit was billed from async job | |
| `from_api_client` | BOOLEAN | API vs non-API attribution | Populated; use for API cuts without SURFACE |
| `num_credits` | NUMBER | Credits consumed | |
| `aggregation_count` | NUMBER | Aggregation factor | |
| `api_endpoint` | TEXT | Endpoint called | |
| `surface` | TEXT | **Surface attribution (extension / web / mobile / etc.)** — has significant NULLs, see gotchas |
| `surface_cta` | TEXT | CTA within the surface | |
| `spend_type_cd` | TEXT | Spend type enum | |
| `charged_credit_type_cd` | TEXT | Credit type charged | Canonical type code from LU_ENUM |
| `created_at_utc` | TIMESTAMP_NTZ | Event time | |
| `updated_at_utc` | TIMESTAMP_NTZ | Last update time | |
| `load_date` | DATE | **Full-refresh marker, NOT a partition** — every row has `load_date = CURRENT_DATE()` after the daily rebuild. Use `created_at_utc::date` for event-time slicing. | |

## Known Issues & Gotchas

- **`SURFACE` null rate is high but NOT extension-biased (Track 1 verdict 2026-04-17).** 80% of `unified_lead_credit` burn in last 30d has null surface. Quantified: null pool is structurally API-key + async sidekiq traffic — neither has a user-facing surface. Extension share of joinable null pool: 0.01%. SURFACE's actual meaning is **"UI surface that triggered a UI-initiated credit charge"** — it doesn't apply to API calls (use `api_endpoint`) or sidekiq jobs (use `request_type` + `sidekiq_job_id`). Real UI-tagging gap: ~147M credits in 30d where `from_api_client=FALSE` AND non-sidekiq AND `surface IS NULL` (66% null rate) — that's the narrowed upstream fix scope. Full writeup in `teammates/bridie_meredith/reports/surface_attribution_trust_2026-04-17.md`.
- **Three attribution axes — use the right one:**
  - API traffic: `from_api_client=TRUE` + `api_endpoint` (controller#action format)
  - Async jobs: `sidekiq_job_id IS NOT NULL` + `request_type` (EmailVerifyRequest, DirectDialVerifyRequest, CsvEnrichmentJob, etc.)
  - UI traffic: `from_api_client=FALSE` + non-sidekiq + `surface` (populated ~34% of the time)
- **`api_endpoint` format is `controller#action`** (hash-delimited). To join to agg HTTP tables: `SPLIT_PART(api_endpoint,'#',1)` = controller, `SPLIT_PART(api_endpoint,'#',2)` = action.
- **`HTTP_REQUEST_ID`** joins deterministically to raw HTTP V3 for per-request precision. Raw V3 is VARIANT-only; V3 view is elevated-role-only. For daily grain without elevated role, use `AGG_MONGO_HTTP_REQUESTS_DAILY`.
- Related to FCT_MONGO_CREDIT_USAGES (higher level) and AGG_TEAM_CREDITS (aggregated).
- Credit type mapping issues apply here too.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file (partial) | Brighid (via Claude) |
| 2026-04-17 | Landed full column list (19 fields, incl. HTTP_REQUEST_ID as FK, SURFACE, FROM_API_CLIENT). Documented SURFACE null trust concern + reconciliation path via AGG_MONGO_HTTP_REQUESTS_DAILY. Bridie flagged upstream fix to team. | Brighid (via Jarvis) |
| 2026-04-17 | Track 1 quantification run. Falsified extension-bias hypothesis (extension share = 0.01%). Reframed SURFACE semantics to "UI-triggered UI-initiated charges." Corrected `load_date` from "partition" to "full-refresh marker." Row count ~200M. Added three-attribution-axis guidance. | Brighid (via Jarvis) |
