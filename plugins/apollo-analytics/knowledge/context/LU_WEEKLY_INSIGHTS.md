# LU_WEEKLY_INSIGHTS

## Location
- **Database:** ANALYTICS_DB
- **Schema:** PLAYGROUND
- **Full path:** `ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS`

## Description
Weekly strategic recommendations surfaced from analytics deep-dives and E-Staff decision packages. Each row is a specific actionable insight with owner, priority, effort estimate, and expected impact. Loaded manually after each weekly E-Staff brief.

## Grain
One row per **insight** (`INSIGHT_ID`). Typically 5-10 insights per week.

## Refresh Cadence
Weekly (manual). Loaded by the analytics team after each E-Staff brief via `sql/lu_weekly_insights.sql`.

**Staleness warning:** If `MAX(WEEK_OF)` is more than 14 days old, the table is stale. The `weekly-insights` plugin skill must fall back to `MAX(WEEK_OF)` when current week has no data — never return 0 rows.

## Owner
Bridie Meredith (Analytics Engineering)

## Columns

| Column | Type | Description |
|---|---|---|
| `INSIGHT_ID` | VARCHAR(50) | Primary key. Format: `WK{YYYY-MM-DD}-{NNN}` |
| `WEEK_OF` | DATE | Week the insight was generated for (Sunday start) |
| `CATEGORY` | VARCHAR(50) | Insight category: retention, pipeline, onboarding, strategy, product |
| `HEADLINE` | VARCHAR(500) | One-line actionable recommendation |
| `DETAIL` | VARCHAR(4000) | Full context: evidence, magnitude, suggested action |
| `OWNER` | VARCHAR(200) | Recommended owner/team for the action |
| `PRIORITY` | VARCHAR(10) | P0 (immediate) / P1 (this sprint) / P2 (backlog) |
| `EFFORT` | VARCHAR(20) | Low / Medium / High effort estimate |
| `EXPECTED_IMPACT` | VARCHAR(500) | Quantified expected impact |
| `SOURCE_REPORT` | VARCHAR(500) | Path to the source analysis |
| `CREATED_AT` | TIMESTAMP_NTZ | Row creation timestamp |
| `UPDATED_AT` | TIMESTAMP_NTZ | Last update timestamp |

## Common Queries

### Latest week's insights
```sql
SELECT HEADLINE, CATEGORY, PRIORITY, OWNER, EXPECTED_IMPACT
FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS
WHERE WEEK_OF = (SELECT MAX(WEEK_OF) FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS)
ORDER BY PRIORITY, CATEGORY
```

### Insights by category
```sql
SELECT CATEGORY, COUNT(*) AS insight_count
FROM ANALYTICS_DB.PLAYGROUND.LU_WEEKLY_INSIGHTS
GROUP BY CATEGORY ORDER BY insight_count DESC
```

## Known Gotchas
- **Staleness:** Only ~6 rows as of initial load (all from 2026-03-24). Table requires weekly manual refresh. If a user asks for current week and gets 0 rows, fall back to `MAX(WEEK_OF)`.
- **Not a time-series table.** Don't trend over multiple weeks unless enough data has accumulated. Each week is an independent set of recommendations.
- **PLAYGROUND schema.** This is a lookup/registry table, not a fact table. Part of the Jarvis governed registry alongside LU_SAVED_METRICS, LU_BUSINESS_GLOSSARY, etc.

## DDL
Source: `sql/lu_weekly_insights.sql`
