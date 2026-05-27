# LU_DARWINBOX_POSITIONS

> Daily position-level snapshots from Darwinbox (HR system) — full org chart for all Apollo functions. Used for headcount tracking, org change analysis, and manager hierarchy joins.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS` |
| **Grain** | One row per (position DBID × DATASET_DATE) — daily snapshots |
| **Total rows** | ~858,578 (254 daily snapshots × ~3,380 positions) |
| **Snapshot range** | 2025-07-02 → 2026-03-19 (254 snapshots, ~daily) |
| **Distinct positions** | 3,704 unique DBIDs |
| **Distinct emails** | 1,240 distinct work emails |
| **Refresh cadence** | Daily |
| **Trust level** | High — sourced directly from Darwinbox (source of truth for HR org data) |
| **Owner** | Data Platform |

## Description

This is the position-level HR lookup table, sourced from Darwinbox (Apollo's HRIS). It captures a daily snapshot of every **position** in the org — including occupied, active, archived, and pending-archival states. Useful for point-in-time headcount, org chart reconstruction, manager hierarchy traversal, and tracking role/department changes over time.

Note: This is a **position** table, not an **employee** table. One DBID = one org chart slot. Positions can be vacant (Active, not yet filled) or occupied by an employee. Archived positions represent roles that no longer exist.

Compare to `DARWINBOX_ACTIVE_ENGG_DATA` (P0): that table covers engineering headcount only and is a current-state view. `LU_DARWINBOX_POSITIONS` covers **all departments** with full **history**.

## Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DBID | TEXT (PK) | Unique Darwinbox position ID | Format: `ZL<number>`. Join key across org queries. |
| FULL_NAME | TEXT | Employee name in the position | NULL/empty for most Archived positions |
| POSITION_STATUS | TEXT | Position state | `Occupied`, `Active` (unfilled), `Archived`, `Pending Archival` |
| JOB_PROFILE | TEXT | Job profile code/identifier | |
| JOB_PROFILE_TITLE | TEXT | Human-readable job title | e.g., "Account Executive - Mid Market Outbound" |
| WORK_EMAIL | TEXT | Employee's work email | NULL for vacant/archived positions |
| DATE_OF_JOINING | TEXT | Hire date | **Stored as TEXT** (e.g., "06-02-2025") — cast explicitly for date math |
| DEPARTMENT_L1 | TEXT | Top-level department with GC code | e.g., `Sales (GC1.11010)`, `Engineering (GC3.21010)` — multiple GC prefixes = multiple legal entities |
| DEPARTMENT_L2 | TEXT | Sub-department | e.g., `Account Executives (GC1.11040)` |
| CURRENT_DEPARTMENT | TEXT | Current department assignment | Shorter name without GC code |
| MANAGER_NAME_WITH_EMPLOYEE_ID | TEXT | Manager name + APL employee ID | e.g., `Matt Curl (APL871)` — parse with regex to extract APL ID |
| MANAGER_POSITION_ID | TEXT | Direct manager's DBID | Self-join to this table for manager chain |
| EMPLOYEE_TYPE | TEXT | Employment classification | `Employee`, `EOR Employee`, `Independent Contractor`, `Consultant`, `Temporary Employee`, `Intern` |
| DATASET_DATE | TEXT | Snapshot date | **Stored as TEXT** (format `YYYYMMDD`, e.g., `20260319`) — cast for date filtering |

## Key Data Facts

### Position status distribution (all snapshots)
| Status | Count |
|---|---|
| Archived | 600,989 |
| Occupied | 219,481 |
| Active (unfilled) | 37,990 |
| Pending Archival | 118 |

### Latest snapshot (2026-03-19) — Occupied positions by department
| Department | Positions |
|---|---|
| Sales | 135 |
| Engineering (GC3) | 132 |
| Engineering (GC1) | 65 |
| Marketing | 63 |
| Support | 52 |
| Success (GC6) | 48 |
| Engineering (GC7) | 48 |
| Support (GC6) | 45 |
| People | 32 |
| Revenue | 24 |
| Design | 23 |
| Data | 21 |
| Finance | 21 |
| Product | 21 |
| Engineering (GC2) | 14 |

**Total occupied latest snapshot: ~846 positions.**

### Employee type (all snapshots)
| Type | Count |
|---|---|
| Employee | 463,853 |
| (blank) | 144,956 |
| EOR Employee | 108,168 |
| Independent Contractor | 91,898 |
| Consultant | 48,593 |
| Temporary Employee | 1,033 |
| Intern | 77 |

## How It's Used

### Common query patterns

```sql
-- Current headcount by department (latest snapshot)
SELECT DEPARTMENT_L1, COUNT(*) AS headcount
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS
WHERE POSITION_STATUS = 'Occupied'
  AND DATASET_DATE = (SELECT MAX(DATASET_DATE) FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS)
GROUP BY 1 ORDER BY 2 DESC;

-- Point-in-time headcount on a specific date
SELECT COUNT(*) FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS
WHERE POSITION_STATUS = 'Occupied'
  AND DATASET_DATE = '20260101';

-- Org hierarchy: find all direct reports of a manager
SELECT * FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS
WHERE MANAGER_POSITION_ID = 'ZL871'  -- Matt Curl's position ID
  AND DATASET_DATE = (SELECT MAX(DATASET_DATE) FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS)
  AND POSITION_STATUS = 'Occupied';

-- Headcount trend over time
SELECT DATASET_DATE, COUNT(*) AS occupied_positions
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.LU_DARWINBOX_POSITIONS
WHERE POSITION_STATUS = 'Occupied'
GROUP BY 1 ORDER BY 1;
```

### Key consumers
- HR / People Analytics — headcount reporting, attrition tracking
- Engineering headcount analysis (alongside `DARWINBOX_ACTIVE_ENGG_DATA`)
- Manager hierarchy joins for per-rep or per-team analytics
- <!-- TODO: confirm if Hex dashboards consume this directly -->

## Related Tables

| Table | Relationship |
|---|---|
| `DARWINBOX_ACTIVE_ENGG_DATA` | Sister table — engineering-only, current state only. Trust this for engineering headcount; use LU_DARWINBOX_POSITIONS for cross-functional or historical. |
| `GITHUB_DEVELOPER_TEAMS` | Downstream join — map Darwinbox employees to GitHub team membership |
| `FCT_LEADGENIE_GITHUB_COMMIT_DATA` | Downstream join — engineering headcount → commit activity |
| `DIM_SALESFORCE_USERS` | Cross-reference — sales reps appear in both; join on email |

## Known Issues & Gotchas

- **DATASET_DATE and DATE_OF_JOINING are TEXT** — cast explicitly: `TO_DATE(DATASET_DATE, 'YYYYMMDD')` and `TO_DATE(DATE_OF_JOINING, 'MM-DD-YYYY')`
- **Multiple GC-code variants for Engineering** — `GC1`, `GC2`, `GC3`, `GC6`, `GC7` all appear as DEPARTMENT_L1 prefixes. These likely represent different legal entities or org versions. Use `LIKE '%Engineering%'` or `CURRENT_DEPARTMENT` to aggregate across entities.
- **Blank EMPLOYEE_TYPE** — ~145K rows have no type. These are mostly older archived records.
- **FULL_NAME is empty for most archived positions** — not a data quality issue; names are redacted on archive.
- **MANAGER_NAME_WITH_EMPLOYEE_ID** — includes APL ID in parentheses inline (e.g., `Matt Curl (APL871)`). Parse with `REGEXP_SUBSTR` to extract the APL ID.
- **Position vs. Employee grain** — 3,704 distinct positions but only 1,240 distinct emails. Many positions are vacant, archived, or held by contractors without work emails.
- **This is NOT a slowly-changing-dimension (SCD)** — it's raw daily snapshots. To get "as of" a date, always filter `WHERE DATASET_DATE = '<date>'`. For current state, use `MAX(DATASET_DATE)`.

## Business Terms

| Term | Definition |
|---|---|
| DBID | Darwinbox position ID — the unique identifier for an org chart slot (not the person, the role) |
| Occupied | Position currently filled by an active employee |
| Active | Position exists in the org but is currently vacant (open role) |
| Archived | Position has been closed/eliminated |
| EOR Employee | Employer of Record — contractor hired through a third-party EOR like Deel or Remote |
| GC code | Cost center / org unit code in Darwinbox (e.g., GC1.11010 = Sales, entity 1) |
| APL ID | Apollo internal employee ID (e.g., APL871) — appears in MANAGER_NAME_WITH_EMPLOYEE_ID |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Created context file from Snowflake exploration | Leo (via Claude) |
