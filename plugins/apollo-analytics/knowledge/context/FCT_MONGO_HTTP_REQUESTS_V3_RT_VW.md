# FCT_MONGO_HTTP_REQUESTS_V3_RT_VW

> Real-time view of Apollo HTTP API requests — raw source for MCP usage. **As of 2026-03-23, prefer DIM_USERS / DIM_TEAMS new API columns for standard MCP analytics.**

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` |
| **Grain** | One row per HTTP API request |
| **Row count** | Very large — real-time, unbounded |
| **Refresh cadence** | Real-time view (no lag) |
| **Trust level** | Use with caution — requires elevated role (not available under DEVELOPER_ROLE) |
| **Owner** | Data Platform / Fraud (Taomei Li) |
| **DAG** | Real-time view — no Airflow DAG |

> **Schema conflict note:** `executive_priorities_fy27.md` lists this as `ANALYTICS_DATAPLATFORM`; `cbr_data_sources.md` lists it as `ANALYTICS_DB.ANALYTICS`. The ANALYTICS schema is what was validated in live sessions — use that. Confirm with Taomei or Shyam before querying.

## Description

Real-time view of all HTTP requests made to Apollo's API surface. Previously the primary source for MCP adoption tracking. **As of 2026-03-23, Shyam has landed API/MCP columns directly in `DIM_USERS` and `DIM_TEAMS` — prefer those for standard analytics.** This table remains useful for real-time monitoring and fraud (Taomei Li), and for raw request-level drill-downs.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| REQUEST_TIMESTAMP | TIMESTAMP | When the request was made | Use for DAU/DAT windows |
| TEAM_ID | TEXT | Apollo team making the request | Join to DIM_TEAMS for segment |
| USER_ID | TEXT | Apollo user making the request | May be NULL for API key requests |
| USER_AGENT | TEXT | Client identifier | `'Apollo-MCP/1.0'` = MCP connector |
| ENDPOINT | TEXT | API endpoint called | |
| STATUS_CODE | NUMBER | HTTP response code | |

<!-- TODO: Confirm full column list — need access to run INFORMATION_SCHEMA.COLUMNS query. Ask Taomei or Shyam. -->

## How It's Used

### MCP connector adoption query
```sql
-- MCP active teams/users per day
SELECT
    DATE_TRUNC('day', REQUEST_TIMESTAMP) AS ds,
    COUNT(DISTINCT TEAM_ID) AS mcp_active_teams,
    COUNT(DISTINCT USER_ID) AS mcp_active_users,
    COUNT(*) AS total_requests
FROM ANALYTICS_DB.ANALYTICS.FCT_MONGO_HTTP_REQUESTS_V3_RT_VW
WHERE USER_AGENT = 'Apollo-MCP/1.0'
  AND REQUEST_TIMESTAMP >= CURRENT_DATE - 30
GROUP BY 1
ORDER BY 1 DESC;
```

### Weekly MCP WAT (with segment)
```sql
SELECT
    DATE_TRUNC('week', REQUEST_TIMESTAMP) AS week,
    sa.ACCOUNT_SUBSEGMENT,
    COUNT(DISTINCT r.TEAM_ID) AS mcp_wat
FROM ANALYTICS_DB.ANALYTICS.FCT_MONGO_HTTP_REQUESTS_V3_RT_VW r
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa
    ON r.TEAM_ID = sa.TEAM_ID
WHERE r.USER_AGENT = 'Apollo-MCP/1.0'
  AND r.REQUEST_TIMESTAMP >= CURRENT_DATE - 90
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

### Key consumers
- **Fraud team** (Taomei Li) — real-time abuse detection
- **Analytics / Leo** — MCP adoption metrics for FY27 executive reporting

## Known Issues & Gotchas

- **Prefer DIM_USERS / DIM_TEAMS for standard MCP analytics** — Shyam landed `first/last_active_date_api_calls`, `active_days_api_calls`, `active_counts_api_calls` with 3-segment breakdown (overall, Apollo-MCP, partner) as of 2026-03-23.
- **Requires elevated role** — `DEVELOPER_ROLE` does NOT have access. Need `ANALYST_ROLE` or higher. Confirm with Taomei or Shyam before running.
- **Schema ambiguity** — two docs cite different schemas (`ANALYTICS` vs `ANALYTICS_DATAPLATFORM`). Use `ANALYTICS_DB.ANALYTICS` based on cbr_data_sources.md.
- **Real-time = unbounded** — always use tight `REQUEST_TIMESTAMP` filters + `LIMIT`. No `SELECT *`.
- **API key requests** — `USER_ID` may be NULL when requests come from API key auth (team-only attribution).

## Business Terms

| Term | Definition |
|---|---|
| Apollo MCP Connector | Customer-facing MCP server Apollo ships to let AI agents (e.g., Claude) call Apollo's API natively. GA launched with Anthropic partnership. |
| MCP DAU / MCP WAT | Distinct users / teams using the MCP connector in a given day / week, filtered by `USER_AGENT = 'Apollo-MCP/1.0'` |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-23 | Created context file — MCP usage source, permission caveat, sample queries | Jarvis |
| 2026-03-23 | Demoted from primary MCP source — Shyam landed API/MCP columns in DIM_USERS/DIM_TEAMS | Jarvis |
