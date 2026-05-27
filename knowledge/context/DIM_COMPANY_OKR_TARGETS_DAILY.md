# DIM_COMPANY_OKR_TARGETS_DAILY

> Daily company-level OKR targets for team registrations and new self-serve ARR.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_COMPANY_OKR_TARGETS_DAILY` |
| **Grain** | One row per calendar date |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative — canonical OKR targets |
| **Owner** | Analytics / Finance |

## Description

Simple daily lookup table containing company-level OKR targets. Currently tracks two targets: total team registration and new self-serve ARR. Used by Looker dashboards (526 queries/14d) to overlay targets on actual performance charts. This is the source of truth for "are we on track?" OKR questions involving registration and SS ARR targets.

## Upstream Sources

| Source | Relationship |
|---|---|
| Finance OKR planning | Manual target entry, likely from AOP process |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CALENDAR_DATE | DATE | The date this target applies to | Nullable — check for NULLs |
| TOTAL_TEAM_REGISTRATION_TARGET | FLOAT | Daily target for total team registrations | Cumulative or daily? Verify before use |
| TOTAL_NEW_SS_ARR_TARGET | FLOAT | Daily target for new self-serve ARR | In USD. Cumulative or daily? Verify before use |

## How It's Used

### Common query patterns

- Join to actuals tables on CALENDAR_DATE to compute actual vs target
- Filter to specific date ranges for OKR reporting periods
- Used in Looker target-overlay dashboards

### Key consumers

- Looker dashboards (526 queries in 14 days)
- OKR reporting / exec reviews

## Known Issues & Gotchas

- Only 3 columns — very limited scope (registrations + SS ARR only). Other OKR targets (NRR, WAT, activation, etc.) are NOT in this table.
- FLOAT type on targets — watch for floating-point precision in comparisons
- All columns are nullable — a missing date means no target was set
- Unclear if targets are cumulative (YTD) or daily run-rate — verify before interpreting
- For broader OKR tracking, also check `domain/rnd_okr_structure.md` and `domain/annual_targets.md`

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
