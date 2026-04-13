---
name: data-catalog-search
description: Search the governed data catalog to find the right tables and understand business terms
trigger-conditions:
  - "what tables have [topic]"
  - "where does [data] live"
  - "find tables for [concept]"
  - "what tables do you have"
  - "which table should I use for [concept]"
  - "show me the catalog"
not-for:
  - "what is [metric] / define [metric]" → use metric-lookup first
  - "amplitude event / mongo collection / sfdc object / salesforce field" → use source-catalog (power-user only)
---

# Data Catalog Search

Use this skill when composing ad-hoc queries (no pre-approved metric matches) or when a user asks "what tables do you have?" or "where does X data live?"

## Step 1: Find Relevant Tables

```sql
SELECT table_name, description, grain, trust_tier, known_issues, key_columns
FROM ANALYTICS_DB.PLAYGROUND.LU_DATA_CATALOG
WHERE status IN ('playground', 'production')
  AND (LOWER(table_name) ILIKE '%<keyword>%' OR LOWER(description) ILIKE '%<keyword>%')
ORDER BY
  CASE trust_tier WHEN 'canonical' THEN 1 WHEN 'preferred' THEN 2 WHEN 'reference' THEN 3 ELSE 4 END
```

## Step 2: Interpret Business Terms

If the user uses a business term, look it up before writing SQL:

```sql
SELECT term, definition, sql_predicate, related_tables, aliases
FROM ANALYTICS_DB.PLAYGROUND.LU_BUSINESS_GLOSSARY
WHERE LOWER(term) ILIKE '%<term>%' OR LOWER(aliases) ILIKE '%<term>%'
```

Use the returned `sql_predicate` to construct correct WHERE clauses. Never hardcode business logic.

## Composition Rules

When building an ad-hoc query from catalog tables:

1. **Always prefer canonical tables** over preferred/reference/avoid
2. **Join to `LU_TEAM_ATTRIBUTES`** (on `team_id`) for any segmentation (segment, region, plan, core account, golden population)
3. **Join to `LU_FISCAL_CALENDAR`** (on `ds = calendar_date`) for fiscal year/quarter grouping
4. **Filter `arr > 0`** for "paid teams" unless explicitly asked about free teams
5. **Never query tables with `trust_tier = 'avoid'`**
6. **For feature/activity questions:** use `DIM_TEAMS_DAILY` with `IS_PAID_IND = true` — always filter to single date or narrow range (8.6B rows)
7. **For feature-level user counts:** prefer `FCT_TEAM_FEATURE_USERS_DAILY` (lighter weight)
8. **LIMIT all queries:** default 20, max 100

## Trust Tier Hierarchy

| Tier | Meaning | Action |
|------|---------|--------|
| canonical | Gold standard, deliberately maintained | Use first |
| preferred | Reliable, maintained by known owner | Use when canonical unavailable |
| reference | Supplementary, may have gaps | Use for enrichment only |
| avoid | Known issues, deprecated, or unreliable | Never query |

## Key Tables (49 in catalog)

The catalog covers revenue, credits, support, email, product metrics, AI analytics, team attributes, and fiscal calendar tables. Run the full catalog query to see all available tables:

```sql
SELECT table_name, trust_tier, grain, description
FROM ANALYTICS_DB.PLAYGROUND.LU_DATA_CATALOG
WHERE status IN ('playground', 'production')
ORDER BY trust_tier, table_name
```

## 49 Business Terms in Glossary

Common terms that trip people up:
- **WAT:** Weekly Active Teams, Sunday anchor. Exec context = paid WAT (~69K)
- **NRR:** M3 Cohort NRR (62-78%), NOT aggregate net retention (~96%)
- **Golden Population:** Core plan, North America, Sales dept >3, 1-2 seats
- **PLSM:** Product-Led Sales Motion
- **PQA:** Product Qualified Account (3+ MAU)
- **Active Days:** #1 retention predictor (26+ days = 76% retention)

## Tracking

- **Query tag:** Pass `--context catalog_search` when running queries via `snowflake_query.py`
- **Pulse:** After completing the search, fire: `python3 scripts/snowflake_query.py --pulse catalog_search --detail "<search terms and tables found>"`
