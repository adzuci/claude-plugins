# HTML Report Reference

Use this reference only when `/apollo-eng-devops:check-apdex --html` is passed.

## Output Contract

Always print the compact terminal report first. Then write a local static HTML report and print its absolute path.

Default path pattern:

```text
/tmp/check-apdex-report-YYYYMMDD-HHMMSS.html
```

If the environment cannot write to `/tmp`, write to the current working directory and say why.

## Content

The HTML report should include:

- Title: `Check Apdex Report`
- Generated timestamp
- OKR/KR context: `DevOps KR1.2 Apdex reporting`
- Verdict
- Current window and baseline window
- Current Apdex, baseline Apdex, and Apdex-point delta
- Apdex-over-time graph from the returned scalar rows
- Freshness from `load_date`
- Transaction volume
- Source/cache status: Snowflake executed, cache hit, stale cache, SQL-only not executed, or partial
- Grafana triage dashboard link: <https://apolloio.grafana.net/d/plat-1365-apdex/plat-1365-efficient-apdex-triage>
- Top Snowflake-visible contributors, if queried
- Grafana findings, if deep triage ran
- Next checks
- Data caveats
- SQL/source execution state: Snowflake executed, cache hit, stale cache, SQL-only not executed, or partial

Include the exact Snowflake table used and whether Grafana was used. Always include the Grafana dashboard link even if Grafana MCP was not called.

If data came from cache, include cache path, cache generated timestamp, cache age, and whether the cache was considered fresh or stale.

## Format

Keep the report dependency-free:

- Plain HTML and inline CSS only
- No external assets
- No JavaScript required
- Escape all dynamic text before writing it into HTML

Use compact operational styling: readable tables, restrained colors, and no decorative hero/marketing layout.

## Apdex Trend Graph

When at least two Apdex rows are available, include an over-time chart in the HTML report.

Preferred implementation:

- Inline SVG generated from the returned rows
- X-axis labels from `start_date_pst`
- Y values from `apdex_value`
- Current point highlighted
- Baseline point visually distinct when `--baseline previous`
- No external charting libraries

If SVG generation is awkward in the current environment, use a compact table plus text sparkline. The graph must be derived from the same rows used for the verdict.

## SQL-Only State

If Snowflake did not execute and the user chose SQL-only, the HTML report may still be written, but it must clearly show:

```text
Source: SQL-only not executed
```

Do not show a verdict based on unexecuted SQL.
