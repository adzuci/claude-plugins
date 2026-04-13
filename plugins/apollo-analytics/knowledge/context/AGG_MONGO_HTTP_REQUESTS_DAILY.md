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
| **Owner** | Data Science / Analytics |
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
