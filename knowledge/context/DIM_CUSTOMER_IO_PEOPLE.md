# DIM_CUSTOMER_IO_PEOPLE

> Bridge table mapping Customer.io person IDs to Apollo team IDs. The join key for lifecycle email analysis.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_CUSTOMER_IO_PEOPLE` |
| **Grain** | One row per Customer.io person (CIO_CUSTOMER_ID) |
| **Row count** | ~15M (as of Apr 2026); non-employee subset ~14.9M |
| **Refresh cadence** | Daily |
| **Coverage period** | Feb 2020 – ongoing |
| **Trust level** | Authoritative for CIO↔Apollo identity resolution |
| **Owner** | Lifecycle / Data Platform |
| **DAG** | <!-- TODO: confirm DAG --> |

## Description

This table resolves Customer.io's internal person ID (`INTERNAL_CUSTOMER_ID`, also known as `cio_id`) to Apollo's `APOLLO_TEAM_ID`. It is the required bridge whenever joining `FCT_CUSTOMER_IO_DELIVERY_METRICS` (which uses `CIO_CUSTOMER_ID`) to any Apollo team or user dimension. Without this table, CIO delivery data cannot be segmented by plan, ARR, or account type.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `INTERNAL_CUSTOMER_ID` | VARCHAR | CIO's internal person ID (`cio_id`) | = `CIO_CUSTOMER_ID` in FCT_CUSTOMER_IO_DELIVERY_METRICS |
| `CUSTOMER_ID` | VARCHAR | External ID (usually Apollo user ID) | |
| `APOLLO_TEAM_ID` | VARCHAR | Apollo team ID — join to DIM_TEAMS | Key join column |
| `EMAIL` | VARCHAR | User email address | |
| `IS_SUPPRESSED` | BOOLEAN | If true, CIO has suppressed this person from sends | Filter `IS_SUPPRESSED = FALSE` for active audience |
| `IS_APOLLO_EMPLOYEE` | BOOLEAN | True if Apollo employee | Always filter `IS_APOLLO_EMPLOYEE = FALSE` for customer analysis |
| `IS_MISSING_EMAIL` | BOOLEAN | True if email field is blank in CIO | |
| `WORKSPACE_ID` | NUMBER | CIO workspace | |
| `CREATED_AT` | TIMESTAMP | When person was first added to CIO | |
| `UPDATED_AT` | TIMESTAMP | Most recent update | Use for latest-state joins |

## How It's Used

### Common query patterns

```sql
-- Standard join: CIO delivery metrics → Apollo team segment
SELECT t.ACCOUNT_SUB_SEGMENT, SUM(f.SENT_COUNT)
FROM ANALYTICS_DB.ANALYTICS.FCT_CUSTOMER_IO_DELIVERY_METRICS f
JOIN ANALYTICS_DB.ANALYTICS.DIM_CUSTOMER_IO_PEOPLE p
  ON f.CIO_CUSTOMER_ID = p.INTERNAL_CUSTOMER_ID
  AND p.IS_APOLLO_EMPLOYEE = FALSE
  AND p.IS_SUPPRESSED = FALSE
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t
  ON p.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
GROUP BY 1;
```

### Key consumers

- Lifecycle marketing analysis (email funnel by segment)
- FCT_CUSTOMER_IO_POST_CLICK_TEAM_ACTIVATION (uses this bridge)
- CIO coverage gap analysis (paid teams not in CIO)

## Alternative: CUSTOMER_IO__PEOPLE (raw source, more complete)

`ANALYTICS_DB.ANALYTICS.CUSTOMER_IO__PEOPLE` is the upstream raw table. It has **18.2M rows** (IS_LATEST=TRUE, non-employee) vs. DIM's **15.0M** — **3.2M CIO people exist in the raw table but are filtered out of DIM**. If coverage completeness matters (e.g., segment reach analysis), prefer the raw table.

Key difference: raw table has `APOLLO_USER_ID`, not `APOLLO_TEAM_ID`. Requires an extra hop via `INT_CUSTOMER_IO_USER_TEAM_MAPPING` to reach team level. Credit: Andrew Green (2026-04-14).

```sql
-- More complete join pattern (Andrew Green's approach)
FROM ANALYTICS_DB.ANALYTICS.FCT_CUSTOMER_IO_DELIVERY_METRICS d
JOIN ANALYTICS_DB.ANALYTICS.CUSTOMER_IO__PEOPLE p
    ON p.CIO_CUSTOMER_ID = d.CIO_CUSTOMER_ID
    AND p.IS_LATEST_NON_DELETED_RECORD = TRUE
    AND p.IS_APOLLO_EMPLOYEE = FALSE
JOIN ANALYTICS_DB.ANALYTICS.INT_CUSTOMER_IO_USER_TEAM_MAPPING m
    ON p.APOLLO_USER_ID = m.APOLLO_USER_ID
JOIN ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS t
    ON m.APOLLO_TEAM_ID = t.APOLLO_TEAM_ID
```

| Table | Rows (non-employee) | Team join | Notes |
|---|---|---|---|
| `CUSTOMER_IO__PEOPLE` (IS_LATEST=TRUE) | 18.2M | Via `INT_CUSTOMER_IO_USER_TEAM_MAPPING` | More complete, raw source |
| `DIM_CUSTOMER_IO_PEOPLE` | 15.0M | Direct `APOLLO_TEAM_ID` column | Convenience, but 3.2M missing |

## Known Issues & Gotchas

- **DIM is filtered — 3.2M CIO people are in the raw source but missing from DIM.** Coverage gap analysis using DIM understates reach. Use `CUSTOMER_IO__PEOPLE` with `IS_LATEST_NON_DELETED_RECORD = TRUE` for the most complete population.
- `APOLLO_TEAM_ID` can be NULL in DIM — not all CIO people have a mapped team. Filter `IS NOT NULL` when joining to DIM_TEAMS.
- Always exclude `IS_APOLLO_EMPLOYEE = TRUE` for customer analysis.
- `INTERNAL_CUSTOMER_ID` (DIM) = `CIO_CUSTOMER_ID` (raw) — same field, different column names across tables.
- Coverage gap numbers in the lifecycle marketing deep dive (Apr 2026) were computed using DIM and are therefore understated.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file — lifecycle marketing deep dive | Jarvis |
| 2026-04-14 | Added raw source comparison + Andrew Green's join pattern; DIM completeness caveat | Jarvis (via Andrew Green) |
