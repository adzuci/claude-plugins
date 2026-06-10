# Cache Reference

Use this reference to avoid repeated Snowflake queries for `/apollo-eng-devops:check-apdex`.

## Default Behavior

Cache Snowflake results locally and reuse them when they are fresh enough for the requested check. The cache is an optimization only; never cache secrets, credentials, MCP tokens, or raw auth output.

Default directory:

```text
/tmp/check-apdex
```

Default cache file:

```text
/tmp/check-apdex/snowflake-cache.json
```

If `/tmp` is unavailable, use the current working directory:

```text
./.check-apdex-cache/snowflake-cache.json
```

## Cache Contents

Store JSON with this shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-08T03:30:00Z",
  "source_table": "ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS",
  "query_mode": "latest",
  "window": {
    "from": null,
    "to": null
  },
  "latest_load_date": "2026-06-07",
  "rows": [],
  "contributors_by_start_date_pst_key": {}
}
```

`rows` should contain scalar Snowflake rows from `snowflake.md`. Contributor arrays should be stored only after one-row contributor queries are run.

## Freshness Rules

Use the cache when all are true:

- `--refresh` is not passed.
- The cache file exists and parses as JSON.
- `schema_version` is supported.
- `source_table` matches the live table in `snowflake.md`.
- Cache `generated_at` is less than 24 hours old.
- The cached rows cover the requested window. For the default latest-record check, this means at least two rows are present.

Treat the cache as stale when any freshness rule fails.

Always query Snowflake when:

- `--refresh` is passed.
- The cache is missing or stale and Snowflake MCP is available.
- The user supplied `--from` / `--to` and the cached rows do not cover that range.
- The skill needs contributor details for a current row that are not already cached.

If Snowflake is unavailable but a stale cache exists, offer the stale cache as an explicit user choice. If used, mark the report:

```text
Source: stale cache
```

## Cache Writes

After a successful Snowflake query:

1. Create the cache directory if needed.
1. Write to a temporary file in the same directory.
1. Rename the temporary file over `snowflake-cache.json`.

This avoids partially written cache files.

## Reporting

Every report should include one of:

```text
Source: Snowflake executed
Source: cache hit
Source: stale cache
Source: SQL-only not executed
```

If cache is used, include the cache path and cache generated timestamp.
