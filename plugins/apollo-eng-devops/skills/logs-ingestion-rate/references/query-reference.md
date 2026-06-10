# Logs Ingestion Query Reference

## Datasource configuration

- Logs: Loki `grafanacloud-logs`
- Alert state history: Loki `grafanacloud-alert-state-history`
- Grafana Cloud usage metrics: Prometheus `grafanacloud-usage`
- Kubernetes and workload metrics: Prometheus `grafanacloud-prom`

Use `grafanacloud-usage` for Grafana Cloud ingestion metrics. Use
`grafanacloud-prom` for `kube_*`, pod, deployment, HPA, and container metrics.

## Log query backend selection

Loki via Grafana is the primary backend for the log-volume steps (Steps 3 and
4). Some runtimes expose Grafana MCP without a Loki/LogQL query tool, so those
steps cannot run against Loki there.

Use New Relic only when the invocation includes the `newrelic` argument. Without
that argument, do not query New Relic; compare the current Grafana ingestion
trend against the previous 7 days and report unavailable Loki-only steps
explicitly.

When `newrelic` is passed and a **New Relic MCP is available**, use it as an
opt-in fallback to run equivalent NRQL against the `Log` event type. Discover
available New Relic MCP tools and `Log` attributes first; do not assume
attribute names.

Always state which backend you used. If neither Loki nor New Relic is
queryable, explicitly report which steps could not be verified.

## Optional New Relic: Step 3 NRQL fallback template

Only run this section when `newrelic` was passed.

Run this over the alert window, faceting on the best available attribute
(`service_name`, `service`, `entity.name`, `namespace`, ...):

Use ISO 8601 UTC timestamps when substituting `SINCE` and `UNTIL` placeholders,
for example `2026-06-10T14:30:00Z`.

```sql
SELECT bytecountestimate() AS bytes, count(*)
FROM Log FACET service_name
SINCE '<alert_start-30m>' UNTIL '<alert_start+10m>'
LIMIT 10
```

## Optional New Relic: Step 4 NRQL fallback templates

Only run this section when `newrelic` was passed.

Pull offender lines in a narrow peak window:

```sql
SELECT * FROM Log WHERE service_name = '<contributor>'
SINCE '<peak-5m>' UNTIL '<peak+5m>' LIMIT 500
```

Find dominant message templates:

```sql
SELECT count(*) FROM Log WHERE service_name = '<contributor>'
FACET message SINCE '<peak-5m>' UNTIL '<peak+5m>' LIMIT 20
```

## Known high-volume baseline interpretation

| Service | Interpretation |
| --- | --- |
| `sidekiq-enrichment-generation-worker` | Usually high baseline; look for step-change |
| `rails-api` | Usually high baseline; check retry storms or traffic change |
| `mongo` | Usually high baseline; check sudden growth before blaming it |

## Known offender pattern

| Service | Known cause | Fix |
| --- | --- | --- |
| `sidekiq-processor` | Logs one `resolve_values completed` line per field per record; records with 60+ fields amplify volume about 60x | Log once per record with aggregate field summary |
