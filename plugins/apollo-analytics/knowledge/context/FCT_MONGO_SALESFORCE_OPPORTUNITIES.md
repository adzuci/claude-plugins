# FCT_MONGO_SALESFORCE_OPPORTUNITIES

> Historical Mongo-sourced Salesforce opportunities. **Data through July 2024 only — do not use for current-period analysis.**

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_SALESFORCE_OPPORTUNITIES` |
| **Grain** | One row per Salesforce Opportunity |
| **Row count** | ~77K closed-won New Business (through Jul 2024) |
| **Refresh cadence** | None — historical snapshot, no longer refreshed |
| **Coverage period** | 2022-01-01 to 2024-07-03 |
| **Trust level** | Use with caution — historical only, no current-period data |
| **Owner** | Data Platform |
| **DAG** | None (static) |

## Description

Mongo-sourced copy of Salesforce opportunity data. Contains historical closed-won deals through early July 2024. **This table is NOT a substitute for DIM_SALESFORCE_OPPORTUNITIES for any analysis requiring current data.** It exists as a historical reference and was used before the canonical SFDC dim was widely available.

If you are considering using this table, check whether `DIM_SALESFORCE_OPPORTUNITIES` is accessible under your role first. If it is, use that instead — it has current data and 413 columns vs. this table's limited schema.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ID | TEXT | Opportunity ID | |
| TYPE | TEXT | Opportunity type | New Business, Upsell, Renewal, etc. |
| IS_WON | BOOLEAN | Won flag | |
| IS_CLOSED | BOOLEAN | Closed flag | |
| CLOSED_AT | TIMESTAMP | Close date | **Max value: ~2024-07-03** |
| LEAD_SOURCE | TEXT | Lead source | |
| LEAD_SOURCE_BUCKET | TEXT | Channel bucket | System, Inbound, Partner, etc. |
| PACKAGE_TYPE_C | TEXT | Package type | Only reliable segment proxy in this table |
| NEW_ANNUALIZED_DELTA_ARR | NUMBER | ARR delta | |
| SALESFORCE_ACCOUNT_ID | TEXT | SFDC Account FK | |

## How It's Used

### When NOT to use this table
- Any analysis requiring data after July 2024
- Current-period revenue, pipeline, or ARR reporting
- Executive-facing metrics where recency matters

### When this table is acceptable
- Historical trend analysis explicitly scoped to pre-2024 periods
- Backfill or validation of historical data points
- Comparing historical baselines to current metrics (when clearly labeled as historical)

## Known Issues & Gotchas

- **CRITICAL: Data ends July 2024.** Any query against this table returns nothing for Oct 2024 onward. Jarvis must warn users if this table is used.
- No `ACCOUNT_SEGMENT` column — use `PACKAGE_TYPE_C` as a rough proxy or join to SFDC Account
- Closed-lost coverage is sparse (~248 records vs ~77K closed-won) — cannot support loss analysis
- `TERMINATION_REASON_C` is almost entirely NULL
- Requires `DATACONSUMER_ROLE` or higher

## Current-Period Alternative

Use `ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_OPPORTUNITIES` instead. Requires `DATA_ANALYST_SECURE` or `DEVELOPER_ROLE`. Contains current data with 413 columns and full schema.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-03 | Created context file after EQ Quanstrom's session exposed silent fallback to stale data | Bridie (via Jarvis) |
