# Grafana Apdex Reference

Use this reference only after Snowflake reports a dip or the user passes `--deep`.

## Preferred Dashboard

- Dashboard: `[PLAT-1365] Efficient Apdex Triage`
- UID: `plat-1365-apdex`
- URL: <https://apolloio.grafana.net/d/plat-1365-apdex/plat-1365-efficient-apdex-triage>
- Preferred datasource UID: `eeloo3k56g9vkd`

Fetch the dashboard first if Grafana MCP supports dashboard reads. Use its current panel queries as source of truth if they differ from this reference.

## Triage Order

Compare the dip window against the baseline window used by Snowflake.

1. Overall Apdex: confirm the dip exists in Grafana for the same window.
1. Apdex Loss: quantify where user impact is concentrated.
1. Endpoint Impact: rank endpoints contributing the most loss.
1. Endpoint Apdex: find endpoints with low Apdex and meaningful volume.
1. Throughput: check whether the dip is traffic-mix or volume related.
1. P99 Latency: confirm whether latency moved with Apdex.
1. Component Impact: check component or `access_mode` concentration.

If `--transaction REGEX` is provided, apply it to endpoint or transaction filters where the dashboard queries support it. Otherwise use all transactions.

## Query Guidance

Prefer panel-equivalent queries from `plat-1365-apdex` over hand-written PromQL. The dashboard has historically included panels for:

- Overall Apdex
- Apdex Loss
- `>1s` RPS
- Included RPS
- Top Endpoint Issues
- Endpoint Impact
- Endpoint Apdex
- Throughput
- P99 Latency
- Component Apdex
- Component Impact
- Component Trend

When a panel query needs variables, resolve them as:

| Variable | Default |
|---|---|
| environment | production |
| transaction | `.*` unless `--transaction` is provided |
| comparison window | previous comparable Snowflake window |

## Investigation Notes

- Treat Grafana as the time-series/detail layer, not the source of record for weekly KR reporting.
- Rank contributors by impact, not only by worst Apdex. A tiny endpoint with terrible Apdex is rarely the first KR explanation.
- Check throughput before blaming latency. Traffic mix shifts can move aggregate Apdex.
- Check p99 latency and errors separately. Apdex can move from slow satisfied/tolerating requests, not only hard failures.
- If recent deploy annotations are available, mention correlation only. Do not call it causal without endpoint/component evidence.

## Missing Grafana

If Grafana MCP is unavailable, report a Snowflake-only triage and use the setup instructions in `SKILL.md`.

Also note that Apollo VPN may be required for the MCP server.
