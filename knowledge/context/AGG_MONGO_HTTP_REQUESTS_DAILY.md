# AGG_MONGO_HTTP_REQUESTS_DAILY

> Daily aggregation of HTTP requests to Apollo's backend, broken out by team, user, user agent, controller/action, and access mode.

## Overview

| Field | Value |
|---|---|
| **Full path** | `analytics_db.analytics_datascience.agg_mongo_http_requests_daily` |
| **Grain** | One row per event_date × apollo_team_id × apollo_user_id × user_agent × controller × action × access_mode_cd × is_extension_call × godmode × request_host |
| **Row count** | Large — daily rolling table |
| **Refresh cadence** | Daily |
| **Trust level** | Authoritative |
| **Owner** | Data Science (Kirk Hlavka — shipped the 30x-compressed replacement for raw HTTP request scanning; 20+ users tagged to migrate per `domain/domain_context.md`) |
| **DAG** | Unknown |

## Description

Aggregates raw HTTP request logs from Apollo's MongoDB backend to a daily grain. Each row captures the count of requests (total, successful, client errors, throttled, server errors) for a specific combination of team, user, access mode, controller/action, and request host. Primary use case is understanding API vs MCP vs browser-based usage patterns.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `event_date` | DATE | Calendar date of requests | |
| `apollo_team_id` | TEXT | Team identifier | |
| `apollo_user_id` | TEXT | User identifier | |
| `user_agent` | TEXT | HTTP user agent string | `'Apollo-MCP/1.0'` identifies MCP traffic |
| `controller` | TEXT | Rails controller path (e.g. `api/v1/mixed_people`) | Combine with `action` for the full endpoint |
| `action` | TEXT | Rails action within the controller (e.g. `search`, `match`) | Combine with `controller` for the full endpoint |
| `request_host` | TEXT | Host the request was made to | `'mcp.apollo.com'` also identifies MCP |
| `access_mode_cd` | TEXT | How the request was authenticated | `'api_key'` and `'api_access_token'` = API key usage |
| `is_extension_call` | BOOLEAN | Whether request came from Chrome extension | |
| `godmode` | BOOLEAN | Internal admin/impersonation requests | Filter out for customer analysis |
| `number_of_requests` | NUMBER | Total requests (includes errors) | |
| `number_of_successful_requests` | NUMBER | Requests with 2xx response | Use this for usage metrics |
| `number_of_client_error_requests` | NUMBER | 4xx responses | |
| `number_of_throttled_requests` | NUMBER | Rate-limited requests | |
| `number_of_server_error_requests` | NUMBER | 5xx responses | |

## How It's Used

### Common query patterns

```sql
-- MCP requests: user_agent = 'Apollo-MCP/1.0' OR request_host = 'mcp.apollo.com'
-- API key requests: access_mode_cd in ('api_key', 'api_access_token')
-- Always aggregate on number_of_successful_requests for usage metrics
```

### Key consumers

- API/MCP usage analysis for new teams
- **Surface-attribution reconciliation for `FCT_MONGO_CREDIT_USAGE_DETAILS`** — the credit_usage_details table has a `SURFACE` column with significant NULLs, and upper-ups suspect extension traffic is disproportionately un-tagged. `is_extension_call` here is the DS-side attribution that DP's credit pipeline hasn't picked up. Upstream fix is the real answer (Bridie flagged to team 2026-04-17); for interim quantification, join on `(event_date, apollo_team_id, apollo_user_id, controller, action)` to measure what share of null-surface credit rows correspond to `is_extension_call = TRUE`.

## Known Issues & Gotchas

- **Lives in `ANALYTICS_DATASCIENCE`, not `ANALYTICS_DATAPLATFORM`.** Schema-ownership note — this is the DS-side knock-off of the HTTP request stream. DP has a separate `FCT_MONGO_HTTP_REQUESTS_V2` (1.4B rows, 517GB) which lacks `is_extension_call`; DP's `FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` has it but is elevated-role-only. **This is the DEV_ROLE-accessible source for extension attribution.** (Documented 2026-04-17.)
- **Daily grain only** — if you need per-request-level join (e.g., via `FCT_MONGO_CREDIT_USAGE_DETAILS.HTTP_REQUEST_ID`), this table doesn't have request IDs. Use the V3 raw/view path.
- `godmode = TRUE` rows should be filtered out of customer-facing analyses.
