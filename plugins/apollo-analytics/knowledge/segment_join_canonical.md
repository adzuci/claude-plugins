# Segment Join Path — SQL Patterns & Reference

**Purpose:** Document the preferred and legacy approaches to joining team-level metrics to account segment. As of 2026-03-30, `LU_TEAM_SEGMENT` is the canonical lookup — use it for 99% of queries. The SFDC join is preserved here as a validation fallback.

**Preferred approach:** `ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT` — see [lu_team_segment_patterns.md](lu_team_segment_patterns.md) for query patterns.

**Status:** LIVE — LU_TEAM_SEGMENT is the SoT. SFDC join is legacy/validation only.

**Maintenance:** Updated by Bridie Meredith. Validated against DIM_SALESFORCE_ACCOUNTS schema.

---

## The Canonical Join Path

**Start table:** `DIM_SALESFORCE_APOLLO_TEAMS` (11.4M rows, all teams with SFDC linkage)
**Middle join:** On `SFDC_ACCOUNT_ID`
**End table:** `DIM_SALESFORCE_ACCOUNTS`
**Result column:** `ACCOUNT_SEGMENT`

```sql
DIM_SALESFORCE_APOLLO_TEAMS.SFDC_ACCOUNT_ID
  → DIM_SALESFORCE_ACCOUNTS.ID
  → ACCOUNT_SEGMENT
```

**Coverage:** 100% (11,442,653 of 11,442,653 teams match). No NULL values in ACCOUNT_SEGMENT.

---

## Segment Values (Authoritative)

The `ACCOUNT_SEGMENT` field contains exactly four values:

| Segment | Row Count | % of Total | Definition (Apollo internal) |
|---------|-----------|------------|------------------------------|
| **VSB** | 5,009,722 | 84.5% | Very Small Business (1-50 employees estimated) |
| **SMB** | 722,482 | 12.2% | Small / Medium Business (50-500 employees) |
| **Mid-Market** | 138,550 | 2.3% | Mid-Market (500-2000 employees) |
| **Enterprise** | 55,037 | 0.9% | Enterprise (2000+ employees) |

**Source:** Salesforce ACCOUNT_SEGMENT field, synced to Snowflake daily.

---

## Related Segment Fields (DO NOT USE FOR PRIMARY JOINS)

For context only — these exist but should not be used for standard segment-sliced metrics:

| Field | Status | Notes |
|-------|--------|-------|
| `ACCOUNT_SUB_SEGMENT` | Non-standard | Granular ("VSB - Enriched", "VSB - Freemail", etc.). Use only for specific analyses. |
| `ACCOUNT_SEGMENT_DEFAULT` | Deprecated | Mostly NULL or duplicates ACCOUNT_SEGMENT. Do not use. |
| `ACCOUNT_SEGMENT_OVERRIDE` | Unused | All NULL. Ignore. |
| `ACCOUNT_SALES_DEPARTMENT_TIER` | Different concept | Not a market segment. Do not conflate. |

---

## SQL Pattern — Standard Usage

**Preferred method (as of 2026-03-30):** Use `LU_TEAM_SEGMENT` lookup table instead of the raw join.

```sql
SELECT
  lu.APOLLO_TEAM_ID,
  lu.ACCOUNT_SEGMENT as segment,
  COUNT(*) as count
FROM ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
GROUP BY lu.APOLLO_TEAM_ID, lu.ACCOUNT_SEGMENT
ORDER BY segment, count DESC
```

**When to use LU_TEAM_SEGMENT:**
- ✅ Any segment-sliced metric (counts, revenue, ARR, churn by segment)
- ✅ Joining fact tables (FCT_DAILY_REVENUE, AGG_TEAM_CREDITS, etc.) to segment
- ✅ Team-level segment analysis (fastest path)
- ✅ 99.9% of segment queries

**When to use the legacy SFDC join:**
- ⚠️ Only if you need real-time SFDC updates (table syncs daily at ~00:30 UTC, not real-time)
- ⚠️ Testing/validation of LU_TEAM_SEGMENT correctness

**Legacy method (direct SFDC join):**

```sql
SELECT
  t.APOLLO_TEAM_ID,
  t.TEAM_NAME,
  s.ACCOUNT_SEGMENT as segment,
  COUNT(*) as count
FROM ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS t
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS s
  ON t.SFDC_ACCOUNT_ID = s.ID
WHERE t.SFDC_ACCOUNT_ID IS NOT NULL
GROUP BY t.APOLLO_TEAM_ID, t.TEAM_NAME, s.ACCOUNT_SEGMENT
ORDER BY segment, count DESC
```

---

**Performance comparison:**

| Method | Row scan | Join latency | Refresh lag | Use case |
|--------|----------|--------------|-------------|----------|
| `LU_TEAM_SEGMENT` | 11.4M rows | <100ms | Daily (~00:30-02:00 UTC) | 99% of queries |
| SFDC join | 11.4M + 1M rows | 500ms-2s | Real-time | Validation, edge cases |

See `data-catalog/lu_team_segment.md` for lookup table schema and refresh schedule.

---

## Important Caveats

1. **Segment is NOT on revenue tables directly.** If you need segment-sliced ARR, MRR, or churn metrics, you must LEFT JOIN from your fact table (e.g., `FCT_DAILY_REVENUE`) through teams to SFDC. This is a known denormalization gap documented as Gap 11 in `pending_definitions.md`.

2. **Historical accuracy:** ACCOUNT_SEGMENT reflects the *current* SFDC value. Time-travel segment for historical cohorts is not yet supported — this is a dependency for accurate cohort NRR by segment.

3. **Unlinked teams:** If a team's `SFDC_ACCOUNT_ID` is NULL, it has no segment. These teams should be excluded from segment-sliced analysis or handled as a separate "Unlinked" category depending on use case.

---

## Common Queries

> Use `LU_TEAM_SEGMENT` for all standard queries. The SFDC join patterns are in the Legacy section above.

### Segment-sliced active team count (current day) — preferred
```sql
SELECT
  lu.ACCOUNT_SEGMENT as segment,
  COUNT(DISTINCT t.TEAM_ID) as active_teams
FROM ANALYTICS_DB.ANALYTICS.AGG_TEAM_CREDITS t
JOIN ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT lu
  ON t.TEAM_ID = lu.APOLLO_TEAM_ID
WHERE t.DATE_UTC = CURRENT_DATE()
GROUP BY lu.ACCOUNT_SEGMENT
ORDER BY segment
```

### Segment breakdown of total teams — preferred
```sql
SELECT
  ACCOUNT_SEGMENT,
  COUNT(*) as teams,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM ANALYTICS_DB.PLAYGROUND.LU_TEAM_SEGMENT
GROUP BY ACCOUNT_SEGMENT
ORDER BY COUNT(*) DESC
```

---

## Gap Tracking

**Resolved by this doc:** Confirms exact ACCOUNT_SEGMENT values for executive reporting (VSB, SMB, Mid-Market, Enterprise). Unblocks Q2 (churn by segment), Q11 (ARR by segment × sales motion), and all segment-sliced metrics.

**Still blocked on Gap 11:** Denormalizing segment onto `FCT_DAILY_REVENUE` and other fact tables to avoid expensive joins on every segment-sliced query. **DRI:** Bridie Meredith. **Timeline:** Pending architecture decision.

**Still blocked on Gap 3 (time-travel segment):** Computing cohort NRR by *entry* segment (not current segment). Requires historical SFDC snapshots. **DRI:** Bridie + Snowflake DE team.
