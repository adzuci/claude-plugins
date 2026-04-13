# LU_TEAM_SEGMENT — Team to Account Segment Lookup

**Location:** `ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT`
**Grain:** One row per APOLLO_TEAM_ID
**Materialized:** Daily (refresh script in `sql/lu_team_segment.sql`)
**DRI:** Bridie Meredith
**Built:** 2026-03-30
**Purpose:** Denormalization bypass for segment-sliced queries. Join this instead of going through DIM_SALESFORCE_APOLLO_TEAMS → DIM_SALESFORCE_ACCOUNTS every time.

---

## Schema

| Column | Type | Notes |
|--------|------|-------|
| `APOLLO_TEAM_ID` | VARCHAR | Primary key. Team identifier. |
| `ACCOUNT_SEGMENT` | VARCHAR | The segment value (VSB, SMB, Mid-Market, Enterprise). Sourced from DIM_SALESFORCE_ACCOUNTS.ACCOUNT_SEGMENT. |
| `SFDC_ACCOUNT_ID` | VARCHAR | The Salesforce Account ID (for debugging/audit joins). |
| `UPDATED_AT` | TIMESTAMP_NTZ | When this row was last materialized. |

---

## Distribution (as of 2026-03-30)

**Team distribution by segment** (11,442,653 total teams):

| Segment | Team Count | % of Teams |
|---------|------------|-----------|
| VSB | 10,146,483 | 88.7% |
| SMB | 705,951 | 6.2% |
| Enterprise | 336,891 | 2.9% |
| Mid-Market | 253,328 | 2.2% |

**Note:** This differs from the *account* distribution (see `domain/segment_join_canonical.md`) because accounts have unequal team counts. Enterprise accounts have many teams; VSB accounts have fewer.

---

## Standard Usage

```sql
-- Segment-sliced active team count
SELECT
  lu.ACCOUNT_SEGMENT as segment,
  COUNT(DISTINCT lu.APOLLO_TEAM_ID) as active_teams
FROM ANALYTICS_DB.PLAYGROUND.AGG_TEAM_CREDITS agg
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON agg.TEAM_ID = lu.APOLLO_TEAM_ID
WHERE agg.DATE_UTC = CURRENT_DATE()
GROUP BY lu.ACCOUNT_SEGMENT
ORDER BY segment;
```

---

## Refresh

**Automated (Production):** Daily Snowflake Task runs at 02:00 UTC.
```sql
-- Task: TSK_REFRESH_LU_TEAM_SEGMENT
-- Runs: Daily at 02:00 UTC (after SFDC sync ~00:30 UTC)
-- Calls: SP_REFRESH_LU_TEAM_SEGMENT() → SP_VALIDATE_LU_TEAM_SEGMENT()
-- Duplication handling: MERGE-based (no truncate, idempotent)
```

**Manual Refresh:**
```sql
-- Step 1: Run the refresh procedure (MERGE-based)
CALL ANALYTICS_DB.PLAYGROUND.SP_REFRESH_LU_TEAM_SEGMENT();

-- Step 2: Run data quality checks
CALL ANALYTICS_DB.PLAYGROUND.SP_VALIDATE_LU_TEAM_SEGMENT();

-- Step 3: Verify results
SELECT ACCOUNT_SEGMENT, COUNT(*) as count, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
FROM ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT
GROUP BY ACCOUNT_SEGMENT
ORDER BY count DESC;
```

**Procedure Details:**
- `SP_REFRESH_LU_TEAM_SEGMENT()` — MERGE-based refresh. Inserts new teams, updates changed segments, deletes teams with lost SFDC linkage. No duplication risk.
- `SP_VALIDATE_LU_TEAM_SEGMENT()` — Five data quality checks: NULL primary keys, invalid segment values, SFDC coverage, segment distribution sanity, recency of UPDATED_AT.

See `sql/lu_team_segment.sql` for full procedure definitions.

---

## Related Tables

- `DIM_SALESFORCE_APOLLO_TEAMS` — Source for APOLLO_TEAM_ID
- `DIM_SALESFORCE_ACCOUNTS` — Source for ACCOUNT_SEGMENT
- `domain/segment_join_canonical.md` — Canonical join path + caveats

---

## Why This Table Exists

**Gap 11 (Denormalization):** Segment was not materialized on fact tables. Every segment-sliced query required a Salesforce join, adding complexity and risk. LU_TEAM_SEGMENT provides a lightweight alternative: join this instead of joining through SFDC.

This does not solve Gap 11 fully (which would require denormalizing onto FCT_DAILY_REVENUE and AGG_TEAM_CREDITS themselves), but it eliminates the recurring SFDC join penalty for analytics queries.
