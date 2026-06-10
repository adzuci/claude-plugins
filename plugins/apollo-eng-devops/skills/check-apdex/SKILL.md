---
name: check-apdex
description: Manual-invocation only. Snowflake-first Apdex dip investigation. Run via /apollo-eng-devops:check-apdex.
disable-model-invocation: true
---

# Check Apdex

**Invoke directly.** This skill is not auto-activated. Run it as a slash command: `/apollo-eng-devops:check-apdex [args]`. The short description above is intentional so the skill stays out of unrelated sessions.

Use this skill to check Apollo Admin Apdex, decide whether a dip is meaningful, and triage likely sources. Snowflake is the default source of truth; Grafana is the deep-dive layer after Snowflake shows a dip or the user explicitly passes `--deep`.

Audience: Apollo engineers and DevOps KR owners.

## Arguments

All arguments are optional. With no args, check the latest available Snowflake Apdex record against the previous comparable record.

```text
/apollo-eng-devops:check-apdex [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--baseline previous|median] [--threshold N] [--deep] [--no-grafana] [--transaction REGEX] [--html] [--refresh]
```

| Argument | Default | Meaning |
|---|---:|---|
| `--from YYYY-MM-DD` | latest record | Start date for the current window |
| `--to YYYY-MM-DD` | latest record | End date for the current window |
| `--baseline MODE` | `previous` | Compare against `previous` comparable record or rolling `median` of the returned records |
| `--threshold N` | `0.005` | Minimum Apdex-point drop that counts as a meaningful dip |
| `--deep` | off | Run Grafana triage even if Snowflake does not cross the dip threshold |
| `--no-grafana` | off | Stay Snowflake-only even if a dip is detected |
| `--transaction REGEX` | all | Limit Grafana endpoint triage to matching transactions |
| `--html` | off | Also write a local static HTML report |
| `--refresh` | off | Ignore local Snowflake cache and query Snowflake |

If positional args are present, ask the user to rerun with named args. There is intentionally no `routine` argument.

## Workflow

### 1. Parse arguments

Echo the resolved settings:

```text
baseline=previous threshold=0.005 deep=false no_grafana=false transaction=.* html=false refresh=false
```

If both `--from` and `--to` are provided, use that as the current window. If only one is provided, ask for the missing bound before querying.

### 2. Preflight tools

Print a single-line availability table:

```text
Tools: Snowflake [ok/missing]  Grafana [ok/missing]  Cache [hit/stale/missing]
```

Before blocking on Snowflake, read [`references/cache.md`](references/cache.md). If the cache is valid for the requested window and `--refresh` is not passed, use the cache and skip Snowflake. Report `Source: cache hit` and the cache age.

Snowflake is required when the cache is missing, stale, bypassed by `--refresh`, or does not cover the requested window. If Snowflake MCP is missing or unauthorized and no valid cache can satisfy the request, stop and prompt exactly:

```text
Snowflake MCP is required for /apollo-eng-devops:check-apdex.
Set up Snowflake access, use stale cache, continue SQL-only, or cancel?
```

- If the user chooses setup, read [`references/mcp-setup.md`](references/mcp-setup.md) and give the relevant Snowflake setup steps.
- If the user chooses stale cache, read [`references/cache.md`](references/cache.md), use the newest available cache entry, and mark the result as stale/cache-backed.
- If the user chooses SQL-only, read [`references/snowflake.md`](references/snowflake.md), print the exact SQL to run, and mark the result as not executed.
- If the user cancels, stop.

Grafana is optional during preflight. Missing Grafana should not block the Snowflake check. If Grafana is needed later and unavailable, read [`references/mcp-setup.md`](references/mcp-setup.md) before printing setup instructions.

### 3. Run Snowflake check

If a valid cache was found, use the cached Snowflake rows and skip this step. Otherwise read [`references/snowflake.md`](references/snowflake.md), then query `fct_mongo_performance_metrics_records` and update the cache using [`references/cache.md`](references/cache.md).

Use `precise_apdex` as the primary metric and fall back to `apdex`. Check freshness via `load_date`. Pull scalar context first: transaction count, slow transaction counts/pcts, and transaction error pct.

Do not select the large VARIANT contributor arrays with the multi-row scalar query. If contributor detail is needed, use the one-row contributor queries in [`references/snowflake.md`](references/snowflake.md) after identifying the current `start_date_pst` key.

If the fully qualified table path fails, search Snowflake metadata for `fct_mongo_performance_metrics_records` before giving up.

### 4. Decide whether there is a dip

Compare the current row to the baseline:

- `previous`: previous comparable Snowflake record
- `median`: median Apdex across the returned lookback, excluding the current row

Verdict rules:

- `data stale/insufficient`: current row is missing, Apdex is null, transaction count is too sparse to trust, or freshness is not good enough for the requested window
- `dip detected`: Apdex drop is greater than or equal to `--threshold`
- `no meaningful dip`: Apdex drop is below `--threshold`

### 5. Escalate to Grafana when needed

Use Grafana only when:

- Snowflake verdict is `dip detected`
- `--deep` is passed

Do not use Grafana if `--no-grafana` is passed.

If Grafana is unavailable, produce the Snowflake-only triage, read [`references/mcp-setup.md`](references/mcp-setup.md), and include the Grafana setup command.

If Grafana is available, read [`references/grafana.md`](references/grafana.md) and use dashboard UID `plat-1365-apdex` as the preferred triage path.

### 6. Report

Keep the report compact:

```text
Verdict: dip detected | no meaningful dip | data stale/insufficient
OKR: DevOps KR1.2 Apdex reporting
Window: <current> vs <baseline>
Apdex: <current> vs <baseline> (<delta>)
Trend: <compact Apdex-over-time sparkline or dated list from returned rows>
Freshness: <load_date>
Volume: <transaction_count>
Source: Snowflake executed | cache hit | stale cache | SQL-only not executed
Grafana: https://apolloio.grafana.net/d/plat-1365-apdex/plat-1365-efficient-apdex-triage

Top contributors:
1. ...
2. ...
3. ...

Next checks:
- ...
```

If no meaningful dip is found, do not run deep triage unless `--deep` was passed. If the drop is sub-threshold but the trend or slow-tail metrics look concerning, say it may be worth investigating and explain the evidence. If the cause is not supported by evidence, say what is missing instead of guessing.

When multiple Apdex rows are available, include a compact over-time view in the terminal report. Prefer a tiny sparkline or short dated list that shows the latest 8 Apdex values from oldest to newest. Do not let the graph replace the numeric current-vs-baseline verdict.

If `--html` is passed, also read [`references/html-report.md`](references/html-report.md) and write a dependency-free static HTML report. Keep the terminal report as the primary output and include the absolute path to the HTML file.

## Guardrails

- Snowflake first, Grafana second.
- Do not claim Snowflake is live/current beyond the row freshness you observed.
- Do not propose fixes before there is a supported root-cause hypothesis.
- Do not write Jira tickets, incident notes, or comments from this skill without explicit user approval.
