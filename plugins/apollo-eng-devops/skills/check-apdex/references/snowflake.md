# Snowflake Apdex Reference

Use this reference when running `/apollo-eng-devops:check-apdex` against Snowflake.

## Source

Start with the live analytics_dataplatform table:

```sql
ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS
```

If that fails, search for the model by name:

```sql
SELECT table_catalog, table_schema, table_name
FROM ANALYTICS_DB.INFORMATION_SCHEMA.TABLES
WHERE LOWER(table_name) = 'fct_mongo_performance_metrics_records'
ORDER BY table_catalog, table_schema, table_name;
```

If no table is found in `ANALYTICS_DB`, broaden the search to accessible databases only if the Snowflake MCP supports it.

## Live Schema Notes

- `start_date_pst` and `end_date_pst` are integer `YYYYMMDD` keys, not Snowflake `DATE` columns.
- Convert date keys with `TO_DATE(TO_VARCHAR(start_date_pst), 'YYYYMMDD')`.
- For explicit date filters, convert the user date to an integer key with `TO_NUMBER(TO_CHAR('{{from_date}}'::DATE, 'YYYYMMDD'))`.
- Pull scalar metrics first. The contributor fields are large VARIANT arrays and can exceed MCP response limits if selected across multiple rows.

## Columns to Prefer

Scalar columns:

- `precise_apdex`: primary Apdex metric
- `apdex`: fallback Apdex metric
- `transaction_count`: traffic volume
- `num_transactions_over_60_seconds`, `pct_transactions_over_60_seconds`
- `num_transactions_over_20_seconds`, `pct_transactions_over_20_seconds`
- `num_transactions_over_8_seconds`, `pct_transactions_over_8_seconds`
- `pct_transactions_over_2_seconds`
- `transaction_error_pct`
- `slow_ui_loaders_total_60secs`
- `slow_ui_loaders_total_20secs`
- `slow_ui_loaders_total_8secs`
- `load_date`

Large VARIANT columns:

- `apdex_most_impactful_transactions`
- `top_transactions_over_60_seconds`
- `top_transactions_over_20_seconds`
- `top_transactions_over_8_seconds`
- `top_transactions_over_2_seconds`
- `transaction_errors`

Column names may be uppercased by Snowflake. Use `DESCRIBE TABLE` if a query fails from casing or drift.

`transaction_error_pct` has historically appeared near `1.0` across records, which may indicate a success/coverage-style ratio rather than a literal error rate. Report it as observed data only and do not treat it as a regression signal unless its semantics are confirmed.

## Latest Scalar Records Query

Use this when no explicit date range is provided. It returns enough recent scalar rows to compare the latest available row against the previous comparable row or a median baseline.

```sql
ALTER SESSION SET QUERY_TAG = '{"app":"devops","action":"check_apdex"}';

SELECT
  start_date_pst AS start_date_pst_key,
  end_date_pst AS end_date_pst_key,
  TO_DATE(TO_VARCHAR(start_date_pst), 'YYYYMMDD') AS start_date_pst,
  TO_DATE(TO_VARCHAR(end_date_pst), 'YYYYMMDD') AS end_date_pst,
  COALESCE(precise_apdex, apdex) AS apdex_value,
  precise_apdex,
  apdex,
  transaction_count,
  num_transactions_over_60_seconds,
  pct_transactions_over_60_seconds,
  num_transactions_over_20_seconds,
  pct_transactions_over_20_seconds,
  num_transactions_over_8_seconds,
  pct_transactions_over_8_seconds,
  pct_transactions_over_2_seconds,
  transaction_error_pct,
  slow_ui_loaders_total_60secs,
  slow_ui_loaders_total_20secs,
  slow_ui_loaders_total_8secs,
  load_date
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS
ORDER BY start_date_pst DESC
LIMIT 8;
```

## Explicit Window Scalar Query

Replace `{{from_date}}` and `{{to_date}}` with quoted `YYYY-MM-DD` literals.

```sql
ALTER SESSION SET QUERY_TAG = '{"app":"devops","action":"check_apdex"}';

SELECT
  start_date_pst AS start_date_pst_key,
  end_date_pst AS end_date_pst_key,
  TO_DATE(TO_VARCHAR(start_date_pst), 'YYYYMMDD') AS start_date_pst,
  TO_DATE(TO_VARCHAR(end_date_pst), 'YYYYMMDD') AS end_date_pst,
  COALESCE(precise_apdex, apdex) AS apdex_value,
  precise_apdex,
  apdex,
  transaction_count,
  num_transactions_over_60_seconds,
  pct_transactions_over_60_seconds,
  num_transactions_over_20_seconds,
  pct_transactions_over_20_seconds,
  num_transactions_over_8_seconds,
  pct_transactions_over_8_seconds,
  pct_transactions_over_2_seconds,
  transaction_error_pct,
  slow_ui_loaders_total_60secs,
  slow_ui_loaders_total_20secs,
  slow_ui_loaders_total_8secs,
  load_date
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS
WHERE start_date_pst >= TO_NUMBER(TO_CHAR('{{from_date}}'::DATE, 'YYYYMMDD'))
  AND start_date_pst <= TO_NUMBER(TO_CHAR('{{to_date}}'::DATE, 'YYYYMMDD'))
ORDER BY start_date_pst DESC;
```

## Baseline Rules

For `--baseline previous`, compare the selected current row with the immediately preceding comparable row.

For `--baseline median`, compute the median of returned rows excluding the current row. If the Snowflake MCP result is easier to process in SQL, use:

```sql
WITH records AS (
  SELECT
    start_date_pst AS start_date_pst_key,
    end_date_pst AS end_date_pst_key,
    TO_DATE(TO_VARCHAR(start_date_pst), 'YYYYMMDD') AS start_date_pst,
    TO_DATE(TO_VARCHAR(end_date_pst), 'YYYYMMDD') AS end_date_pst,
    COALESCE(precise_apdex, apdex) AS apdex_value,
    transaction_count,
    load_date,
    ROW_NUMBER() OVER (ORDER BY start_date_pst DESC) AS recency_rank
  FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS
  QUALIFY recency_rank <= 8
),
current_record AS (
  SELECT * FROM records WHERE recency_rank = 1
),
baseline AS (
  SELECT MEDIAN(apdex_value) AS baseline_apdex
  FROM records
  WHERE recency_rank > 1
)
SELECT
  current_record.start_date_pst_key,
  current_record.end_date_pst_key,
  current_record.start_date_pst,
  current_record.end_date_pst,
  current_record.apdex_value AS current_apdex,
  baseline.baseline_apdex,
  current_record.apdex_value - baseline.baseline_apdex AS apdex_delta,
  current_record.transaction_count,
  current_record.load_date
FROM current_record
CROSS JOIN baseline;
```

## Contributor Queries

Run these only after the scalar query identifies the current row. Replace `{{current_start_date_pst_key}}` with the integer key from `start_date_pst_key`.

Top Apdex-impacting transactions:

```sql
SELECT
  f.index AS rank,
  f.value:endpoint::STRING AS endpoint,
  f.value:count::NUMBER AS count,
  f.value:apdex_impact::FLOAT AS apdex_impact,
  TO_JSON(f.value) AS raw_value
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS t,
  LATERAL FLATTEN(input => t.apdex_most_impactful_transactions) f
WHERE t.start_date_pst = {{current_start_date_pst_key}}
ORDER BY f.index
LIMIT 10;
```

Top very slow transactions:

```sql
SELECT
  'over_60_seconds' AS bucket,
  f.index AS rank,
  TO_JSON(f.value) AS raw_value
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_PERFORMANCE_METRICS_RECORDS t,
  LATERAL FLATTEN(input => t.top_transactions_over_60_seconds) f
WHERE t.start_date_pst = {{current_start_date_pst_key}}
ORDER BY f.index
LIMIT 10;
```

If either query fails because the VARIANT shape changed, rerun with only `TO_JSON(f.value) AS raw_value` and report the raw fields without guessing.

## Interpretation

- Use Apdex-point deltas, not percent change, for the primary verdict.
- Treat the default threshold as a `0.005` Apdex-point drop.
- Check transaction volume before declaring a regression. Low-volume rows can move more easily.
- Use `load_date` to state freshness explicitly.
- The admin performance-monitoring data is weekly/admin-shaped. Do not present it as a live production time series.
- Arrays and nested transaction fields identify likely contributors, not confirmed root cause. Use Grafana for time-series confirmation.
- A sub-threshold single-week drop may still be worth investigating if the multi-week trend is consistently downward or a slow-tail metric spikes materially.
