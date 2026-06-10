---
name: logs-ingestion-rate
description: Manual-invocation only. Investigate Apollo's Grafana Cloud logs ingestion rate alert (UID eetj859g01kw0f, "Logs Ingestion Rate - 5m - Observability stack") and decide whether it is actionable or should be tuned. Run via /apollo-eng-devops:logs-ingestion-rate.
disable-model-invocation: true
---

# Logs Ingestion Rate Investigation

Investigate Grafana alert `eetj859g01kw0f`, "Logs Ingestion Rate - 5m -
Observability stack", and decide whether the alert fired for an actionable
reason or should be tuned.

## Applicability Gate

Before running queries, inspect the current context.

Use this skill only when one of these is true:

- The alert UID is `eetj859g01kw0f`
- The alert name is `Logs Ingestion Rate - 5m - Observability stack`
- The user explicitly asks to investigate Grafana Cloud logs ingestion rate

If the visible alert is different, stop and say:

```text
This skill is not applicable to the primary alert in this context: <alert name>.
This runbook is for the Logs Ingestion Rate alert `eetj859g01kw0f`. I can check
logs ingestion as supporting context, but the primary investigation should use a
runbook for <alert type>.
```

Example: if a Slack thread is about `[Security] Significant Staging Egress Traffic`, do not run this as the primary runbook. Offer logs ingestion only as
secondary context.

## Arguments

- `newrelic`: opt into the New Relic fallback templates in
  [`references/query-reference.md`](references/query-reference.md) when Loki is
  not queryable. Without this argument, do not query New Relic; use Grafana
  Cloud usage, Loki/Grafana Explore, and the previous 7 days of Grafana trends.
  Example: `/apollo-eng-devops:logs-ingestion-rate newrelic`.

## Execution Context

This skill must work in three places:

- **Slack thread via Grafana Assistant**: read the current thread for the alert
  title, firing time, linked alert, and prior comments. Use thread context for
  applicability, but still state the exact alert and time window used.
- **Claude with Grafana MCP**: use available Grafana MCP tools to inspect
  datasources, Prometheus, dashboards, and annotations. The Grafana MCP toolset
  is usually partial: Prometheus queries (Steps 2 and 5) work, but Loki/LogQL
  (Steps 3-4) and the alert-rule definition plus Loki-based alert-state history
  (Step 1) are typically NOT exposed as MCP tools. When those tools are missing,
  route those steps to the Grafana Assistant/Explore UI, and explicitly report
  which steps could not be run rather than guessing. Use New Relic only when the
  invocation includes the `newrelic` argument.
- **Grafana Assistant sidebar**: use the active Grafana page, selected alert,
  dashboard, Explore query, or user prompt as context. If no alert time is
  visible, ask for the firing timestamp or fetch alert state history first.

Do not assume thread/page/sidebar context is complete. Prefer explicit alert
UID, alert name, and UTC firing timestamp when available.

## Datasources

Use the datasource mapping, backend selection, and NRQL fallback templates in
[`references/query-reference.md`](references/query-reference.md).

## Required Inputs

Determine:

- Alert UID and name
- Firing start time in UTC
- Current state and duration, if still firing
- Environment, cluster, namespace, or service filters from the alert labels or
  surrounding context

Default investigation window: `alert_start - 30m` to `alert_start + 10m`.
Use a `30s` or `1m` step for range queries.

## Step 1: Confirm Rule and Firing History

Fetch the exact alert rule when possible. Record:

- Query and datasource
- Threshold
- Evaluation interval
- Pending period
- Labels and routing
- Runbook link

Then inspect roughly the last 30 days of alert state history for
`eetj859g01kw0f`.

Count transitions into `Alerting` or `Firing`, not every evaluation sample.
Report:

- Firing count
- First and latest firing
- Median and max duration, if available
- Repeated days or time-of-day clustering
- Whether prior firings appear actionable

Via the Grafana MCP the rule definition and the Loki-based alert state history
(datasource `grafanacloud-alert-state-history`) are typically unavailable as
tools. When either is missing, say so and fall back to the Grafana
Assistant/Explore UI — annotations are NOT a substitute for state history. Any
threshold-breach count from metrics is only an approximation and must be labeled
as approximate.

## Step 2: Confirm Platform-Level Ingestion

Prefer the same metric family used by the alert rule. For Grafana Cloud usage,
query total logs ingestion:

```promql
sum(grafanacloud_logs_instance_bytes_received_per_second)
```

Compare the alert-time peak against:

- Pre-alert baseline: `alert_start - 30m` to `alert_start - 10m`
- Previous 7 days of Grafana Cloud ingestion trend, preferably same-hour
  baseline plus 7d p95/p99
- Last 24h p95 or p99, as supporting context

Report baseline bytes/s, peak bytes/s, peak/baseline ratio, and whether the
signal is a brief spike or sustained baseline shift.

## Step 3: Identify Top Contributors

This is a LogQL/Loki step; the Grafana MCP usually has no Loki query tool, so
run it via the Grafana Assistant/Explore UI. Do not fabricate contributor
numbers. Use New Relic only when the invocation includes the `newrelic`
argument.

Discover available Loki labels first. Prefer the most specific stable
dimension available, in this order: `service_name`, `service`, `app`,
`namespace`, `deployment`, `pod`, `container`, `cluster`, `department`.

If `service_name` exists, use Loki `grafanacloud-logs` over the alert window:

```logql
topk(10, sum by (service_name) (
  bytes_rate({service_name=~".+"}[5m])
))
```

If another dimension is the best available label, substitute it:

```logql
topk(10, sum by (<label>) (
  bytes_rate({<label>=~".+"}[5m])
))
```

Also check unlabeled traffic for the selected label:

```logql
sum(bytes_rate({<label>=""}[5m]))
```

If the tenant does not support that missing-label selector, discover available
labels first and report the caveat.

If Loki is not queryable and `newrelic` was not passed, skip contributor
ranking and report that the Grafana/Loki source was unavailable.

For each top contributor, calculate:

- Peak bytes/s during the alert window
- Baseline bytes/s in the pre-alert window
- Peak/baseline ratio
- Peak timestamp
- Share of total ingestion

Do not call a known high-volume service the cause unless it changed relative to
its own baseline.

Known high-volume baseline interpretation is in
[`references/query-reference.md`](references/query-reference.md).

## Step 4: Drill Into Offenders

This is a LogQL/Loki step; the Grafana MCP usually has no Loki query tool, so
run it via the Grafana Assistant/Explore UI. Do not fabricate contributor
numbers. Use New Relic only when the invocation includes the `newrelic`
argument.

For each suspicious contributor, query a narrow window around the peak. Use the
same label dimension selected in Step 3 (`<label>`), not always `service_name`:

```logql
{<label>="<contributor>"} | json
```

If JSON parsing fails or hides useful lines, rerun raw:

```logql
{<label>="<contributor>"}
```

If Loki is not queryable and `newrelic` was passed, use the Step 4 NRQL
templates in [`references/query-reference.md`](references/query-reference.md)
for offender-line sampling and message-template faceting. If `newrelic` was not
passed, report this step as unavailable rather than using another backend.

Sample 100-500 lines. Group evidence by:

- Message template
- Log level
- Logger, component, job, or endpoint
- Stack trace or retry loop
- High-cardinality fields
- Repeated structured payloads

Known offender patterns and fixes are in
[`references/query-reference.md`](references/query-reference.md).

## Step 5: Check Deploy, Scale, and Workload Correlation

Use `grafanacloud-prom` for Kubernetes pod restart metrics. Scope by suspected
cluster, namespace, and pod/deployment labels when available.

Pod restart rate:

```promql
sum by (namespace, pod) (
  increase(kube_pod_container_status_restarts_total[40m])
)
```

Interpretation:

- Pod restarts rising near the alert window can explain a new deployment or
  restart loop.
- Flat restart rate plus repeated messages means logging bug, retry storm, or
  unexpected workload behavior is more likely.
- A known operational event can make the alert expected, but still evaluate
  whether paging was useful.

## Step 6: Decide Alert Logic Recommendation

Always make one alert recommendation:

- **Keep**: rare, actionable, and has clear owner action
- **Tune threshold/window**: useful signal, but too sensitive
- **Split by service/team**: one service repeatedly dominates
- **Suppress or exclude baseline**: expected high-volume source is not
  actionable
- **Change to delta/anomaly logic**: absolute threshold fires on normal growth
- **Demote route**: useful trend, not page-worthy
- **Delete**: frequent and no responder action

If the alert fired repeatedly in the last 30 days without clear mitigation or
user-impact correlation, recommend an alert logic change.

## Output Format

Return exactly these sections:

1. **Summary**: one sentence with suspected source and impact
1. **Applicability**: whether this was the right skill for the context
1. **Alert Window**: absolute UTC start/end, step, and datasources
1. **30-Day History**: firing count, duration stats, and source/caveat
1. **Top Contributors**: table with service, baseline bytes/s, peak bytes/s,
   ratio, share, peak timestamp
1. **Evidence**: 3-5 bullets with log pattern, sample template, deploy/scale
   correlation, and missing-label notes
1. **Likely Cause**: concise cause with confidence
1. **Recommended Service Action**: owner-facing fix or mitigation
1. **Alert Recommendation**: keep, tune, split, suppress, demote, or delete
1. **Queries Run**: datasource, query, start/end, and step
