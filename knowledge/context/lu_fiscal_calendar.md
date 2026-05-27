# LU_FISCAL_CALENDAR

> Date dimension covering 2020–2030 with calendar attributes. Canonical source for fiscal date alignment at Apollo.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_FISCAL_CALENDAR` |
| **Grain** | calendar_date |
| **Grain columns** | calendar_date |
| **Row count** | ~4018 |
| **Refresh cadence** | static (generated once, extended annually) |
| **Coverage period** | 2020-01-01 through 2030-12-31 |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Generated date spine covering 2020–2030 (~4,018 rows). Contains calendar attributes: month, week start, year, month number, day of month, ISO day of week, and day of year. Consumers derive Apollo fiscal year and quarter from `calendar_month_num` using the Apollo offset rule. Week starts Monday (ISO convention, consistent with `DIM_ACTIVE_TEAMS_DAILY`).

**CRITICAL:** Apollo fiscal Q1 = February–April, NOT calendar Q1. FY2027-Q1 = Feb–Apr 2026. All fiscal reporting must derive from this table or apply the same offset. Do not use calendar quarters for exec-facing fiscal period labels.

## Upstream Sources

| Source | Relationship |
|---|---|
| Snowflake GENERATOR | Date spine generated via `DATEADD('day', seq4(), '2020-01-01')` |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| calendar_date | DATE | The date (primary key) | Range: 2020-01-01 to 2030-12-31 |
| calendar_month | DATE | First day of the calendar month | `DATE_TRUNC('month', calendar_date)` |
| calendar_week_start | DATE | Monday of the ISO week | `DATE_TRUNC('week', calendar_date)` |
| calendar_year | NUMBER | Calendar year | e.g. `2026` |
| calendar_month_num | NUMBER | Calendar month number (1–12) | Used to derive Apollo fiscal quarter: Q1=2-4, Q2=5-7, Q3=8-10, Q4=11-1 |
| calendar_day_of_month | NUMBER | Day of month (1–31) | |
| day_of_week_iso | NUMBER | ISO day of week (1=Mon, 7=Sun) | |
| day_of_year | NUMBER | Day of year (1–366) | |

## Known Issues

- Does not contain pre-computed fiscal quarter or fiscal year columns — consumers must derive these using Apollo's Feb-start offset
- No `is_business_day` or holiday flag — not a full business calendar

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
