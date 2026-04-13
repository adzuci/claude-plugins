# LU_TEAM_SEGMENT — Query Patterns & Jarvis Integration

**Purpose:** This file documents common SQL patterns using LU_TEAM_SEGMENT so Jarvis (and analysts) can reuse them for segment-sliced metrics.

**Status:** Live as of 2026-03-30. Replaces expensive SFDC joins for 99% of segment queries.

---

## Quick Reference

- **Location:** `ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT`
- **Grain:** One row per `APOLLO_TEAM_ID`
- **Refresh:** Daily at 02:00 UTC (Snowflake Task: `TSK_REFRESH_LU_TEAM_SEGMENT`)
- **Row count:** 11.4M teams, 100% SFDC-linked coverage
- **Segment values:** `VSB`, `SMB`, `Mid-Market`, `Enterprise`

---

## Core Pattern: Segment-Sliced Team Metrics

**Use case:** Count active teams by segment on a given day.

```sql
SELECT
  lu.ACCOUNT_SEGMENT as segment,
  COUNT(DISTINCT agg.TEAM_ID) as active_teams,
  ROUND(100.0 * COUNT(DISTINCT agg.TEAM_ID) / SUM(COUNT(DISTINCT agg.TEAM_ID)) OVER (), 1) as pct
FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS agg
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON agg.TEAM_ID = lu.APOLLO_TEAM_ID
WHERE agg.DATE_UTC = CURRENT_DATE() - 1
  AND lu.ACCOUNT_SEGMENT IS NOT NULL  -- Optional: filter out unlinked teams
GROUP BY lu.ACCOUNT_SEGMENT
ORDER BY COUNT(*) DESC;
```

**Key points:**
- Join on `TEAM_ID = APOLLO_TEAM_ID` (exact match, no ambiguity)
- Filter `lu.ACCOUNT_SEGMENT IS NOT NULL` only if you want to exclude unlinked teams
- Use `LEFT JOIN` so unlinked teams don't drop from your denominator (unless intentional)

---

## Pattern 2: Segment-Sliced Revenue Metrics

**Use case:** ARR by segment as of a date.

```sql
SELECT
  lu.ACCOUNT_SEGMENT as segment,
  SUM(rev.ARR) as total_arr,
  COUNT(DISTINCT rev.TEAM_ID) as team_count,
  ROUND(SUM(rev.ARR) / COUNT(DISTINCT rev.TEAM_ID), 0) as avg_arr_per_team
FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE rev
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON rev.TEAM_ID = lu.APOLLO_TEAM_ID
WHERE rev.DATE_UTC = CURRENT_DATE() - 1
  AND rev.ARR > 0
GROUP BY lu.ACCOUNT_SEGMENT
ORDER BY SUM(rev.ARR) DESC;
```

**Key points:**
- Works with any fact table (FCT_DAILY_REVENUE, FCT_MONTHLY_REVENUE, AGG_TEAM_CREDITS, etc.)
- Always check the fact table's granularity (daily vs. monthly) before `GROUP BY` to avoid double-counting

---

## Pattern 3: Cohort Analysis — Retention by Entry Segment

**Use case:** Churn rate by the segment at signup (not current segment).

```sql
-- This pattern requires a historical snapshot at activation time
-- For now, use the lookup table + a backup to a team activation table
SELECT
  lu.ACCOUNT_SEGMENT as entry_segment,
  t.TEAM_CREATED_DATE,
  COUNT(DISTINCT t.TEAM_ID) as teams_activated,
  COUNT(DISTINCT CASE WHEN rev.ARR > 0 THEN rev.TEAM_ID END) as teams_retained_m3,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN rev.ARR > 0 THEN rev.TEAM_ID END) / COUNT(DISTINCT t.TEAM_ID), 1) as retention_pct
FROM ANALYTICS_DB.ANALYTICS.DIM_MONGO_TEAMS t
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON t.TEAM_ID = lu.APOLLO_TEAM_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE rev
  ON t.TEAM_ID = rev.TEAM_ID
  AND rev.DATE_UTC = DATEADD(month, 3, t.TEAM_CREATED_DATE)
WHERE YEAR(t.TEAM_CREATED_DATE) = 2026
GROUP BY lu.ACCOUNT_SEGMENT, t.TEAM_CREATED_DATE
ORDER BY entry_segment, TEAM_CREATED_DATE;
```

**⚠️ Caveat:** This uses **current** segment (from LU_TEAM_SEGMENT) at M3 check, not entry segment. For true cohort NRR by entry segment, we need historical SFDC snapshots (Gap 3 in `pending_definitions.md`).

---

## Pattern 4: Segment Filter in WHERE Clause

**Use case:** Filter teams to a specific segment before computing metrics.

```sql
SELECT
  agg.TEAM_ID,
  SUM(agg.CREDITS_USED) as total_credits,
  COUNT(DISTINCT agg.DATE_UTC) as active_days
FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS agg
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON agg.TEAM_ID = lu.APOLLO_TEAM_ID
WHERE agg.DATE_UTC >= CURRENT_DATE() - 90
  AND lu.ACCOUNT_SEGMENT = 'Enterprise'  -- Enterprise teams only
GROUP BY agg.TEAM_ID
ORDER BY total_credits DESC;
```

**Key points:**
- Filter `lu.ACCOUNT_SEGMENT IN (...)` for multi-segment queries
- This is faster than filtering on DIM_SALESFORCE_ACCOUNTS because LU is smaller

---

## Pattern 5: Segment with Temporal Analysis (Monthly Rollup)

**Use case:** Revenue trend by segment over time.

```sql
SELECT
  TRUNC(rev.DATE_UTC, 'MONTH') as month,
  lu.ACCOUNT_SEGMENT as segment,
  SUM(rev.ARR) as total_arr,
  COUNT(DISTINCT rev.TEAM_ID) as active_teams
FROM ANALYTICS_DB.ANALYTICS.FCT_DAILY_REVENUE rev
LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON rev.TEAM_ID = lu.APOLLO_TEAM_ID
WHERE rev.DATE_UTC >= '2026-01-01'
  AND rev.ARR > 0
GROUP BY TRUNC(rev.DATE_UTC, 'MONTH'), lu.ACCOUNT_SEGMENT
ORDER BY month, segment;
```

---

## When NOT to Use LU_TEAM_SEGMENT

- **Real-time SFDC changes:** If a segment changed in SFDC in the last few hours and you need that update immediately, use the SFDC join directly (rare).
- **Account-level segment analysis:** If you need account segment (not team segment), join to DIM_SALESFORCE_ACCOUNTS directly. LU_TEAM_SEGMENT is team-granular.
- **Unlinked teams:** If you specifically need teams with `SFDC_ACCOUNT_ID IS NULL`, filter them in the source fact table before joining LU (or use LEFT JOIN with `lu.APOLLO_TEAM_ID IS NULL`).

---

## Performance Notes

| Operation | Time | Notes |
|-----------|------|-------|
| LU_TEAM_SEGMENT join | <100ms | 11.4M row lookup, highly selective |
| SFDC join (legacy) | 500ms-2s | Joins 11.4M teams to 1M+ accounts |
| Segment filter in WHERE | <50ms | Index on ACCOUNT_SEGMENT on the lookup |

**Rule of thumb:** Use LU_TEAM_SEGMENT by default. Only switch to SFDC join if you hit a specific blocker.

---

## Jarvis Context

**For Jarvis to suggest LU_TEAM_SEGMENT patterns:**

When a user asks for segment-sliced metrics, Jarvis should:
1. Recognize the pattern: "by segment" or "across segments" or "Enterprise vs SMB"
2. Recommend the LU_TEAM_SEGMENT join instead of SFDC joins
3. Use one of the patterns above (Template 1-5) as a starting point
4. Cite this file: `domain/lu_team_segment_patterns.md`

**Example Jarvis response:**

> You're looking for active team count by segment. I'll use the LU_TEAM_SEGMENT lookup table — it's 100x faster than joining SFDC directly.
>
> ```sql
> SELECT lu.ACCOUNT_SEGMENT, COUNT(DISTINCT agg.TEAM_ID) as teams
> FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS agg
> LEFT JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu ON agg.TEAM_ID = lu.APOLLO_TEAM_ID
> WHERE agg.DATE_UTC = CURRENT_DATE() - 1
> GROUP BY lu.ACCOUNT_SEGMENT ORDER BY teams DESC;
> ```

---

## Refresh & Validation

The lookup table is maintained automatically:
- **Procedure:** `SP_REFRESH_LU_TEAM_SEGMENT()` (MERGE-based, no duplicates)
- **Validation:** `SP_VALIDATE_LU_TEAM_SEGMENT()` (5 data quality checks)
- **Task:** `TSK_REFRESH_LU_TEAM_SEGMENT` (daily at 02:00 UTC)

See `data-catalog/lu_team_segment.md` for full refresh instructions.
