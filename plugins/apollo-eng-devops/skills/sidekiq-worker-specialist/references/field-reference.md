# Sidekiq Worker Values — Field Reference

## Chart defaults

**Source of truth:** [`kubernetes/charts/sidekiq-workers/values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml) in [`apolloio/leadgenie`](https://github.com/apolloio/leadgenie). Read the `defaults:` block at activation.

| `defaults` key | Role |
|----------------|------|
| `concurrency` | Threads per pod when worker omits `threads_per_pod` |
| `min_workers` | Floor thread budget when worker omits `min_workers` |
| `max_workers` | Thread ceiling when worker omits `max_workers` (prod workers must set `max_workers` explicitly per CI) |
| `targetCPUUtilizationPercentage` | HPA CPU target when worker omits `autoscaling.targetCPUUtilizationPercentage` |
| `workerResources.requests` / `limits` | Per-pod CPU/memory when worker `resources` omits fields |
| `maxUnavailable` / `maxUnavailablePreemptive` | Rolling-update disruption % (preemptive workers use the latter) |
| `terminationGracePeriodSeconds` | Pod termination grace |
| `env` | Extra env vars applied to all workers unless overridden |

Partial `resources` overrides merge with `defaults.workerResources` in [`templates/deployment.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/deployment.yaml).

## HPA replica bounds

**Do not duplicate formula logic here.** Read [`kubernetes/charts/sidekiq-workers/templates/hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml) at activation and derive `minReplicas` / `maxReplicas` from the worker entry plus chart `defaults:`.

That template defines:

- Effective concurrency (`threads_per_pod` vs `defaults.concurrency`, including the strict branch when `max_workers < defaults.concurrency`)
- `minReplicas` and `maxReplicas` on the HPA resource
- Which autoscaling metrics are attached (CPU, external queue latency)

Use those rendered bounds in impact tables and when comparing HPA headroom in Grafana.

HPA metrics (unless overridden per worker) — defined in [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml):

- CPU utilization (target = `autoscaling.targetCPUUtilizationPercentage` or chart `defaults.targetCPUUtilizationPercentage`)
- `sidekiq_queue_latency` external metric when `autoscaling.targetLatency` or `targetQueueLatencies` set (scale-up threshold in same template)

### HPA metrics and Grafana verification

**Reach goal:** When Grafana MCP is enabled (`mcp__grafana__query_prometheus` available), query utilization before tuning — same signals the HPA uses. VPN required; install via [`grafana-observability`](../grafana-observability/SKILL.md#setup-grafana-mcp-server). If unavailable, skip and use GKE MCP / kubectl.

1. Resolve effective targets from the worker entry and chart `defaults:`.
1. Query Prometheus (search Sidekiq dashboards first if label names are unclear):

**CPU utilization** (fleet average vs HPA CPU target %):

```promql
100 * sum(rate(container_cpu_usage_seconds_total{namespace="default", pod=~"sidekiq-<worker>.*", container!=""}[5m]))
/ sum(kube_pod_container_resource_requests{namespace="default", pod=~"sidekiq-<worker>.*", resource="cpu", container!=""})
```

**Queue latency** (when `autoscaling.targetLatency` or `targetQueueLatencies` is set; label may be `queue` or `name`):

```promql
sidekiq_queue_latency{queue="<queue_name>"}
```

**HPA headroom** (pinned at max → candidate for raising `max_workers`):

```promql
kube_horizontalpodautoscaler_status_current_replicas{horizontalpodautoscaler="sidekiq-<worker>"}
kube_horizontalpodautoscaler_spec_max_replicas{horizontalpodautoscaler="sidekiq-<worker>"}
```

3. Interpret (infra changes only after ruling out slow code/DB):
   - **High latency, moderate CPU** → likely I/O or DB bound; optimize queries/code before scaling.
   - **High CPU per job** (e.g. `sidekiq_job_runtime` rising) → code inefficiency; more replicas multiply waste.
   - **CPU sustained above target + backlog + efficient per-job runtime** → raise `max_workers`.
   - **Latency above scale-up threshold + efficient jobs** → raise `max_workers` or tighten `targetLatency` only after confirming throughput need.
   - **CPU low with spare replica headroom** → avoid over-provisioning.

## Worker entry fields

| Field | Required | Notes |
|-------|----------|-------|
| `max_workers` | **Yes** (prod) | Thread budget ceiling; mandatory per CI |
| `min_workers` | No | Keeps minimum slots for SLA-critical queues |
| `threads_per_pod` | No | Inherits `defaults.concurrency`; lower when per-pod OOM/CPU bound |
| `preemptive` | No | `true` → spot node scheduling (prod) |
| `preemptiveOptions` | No | Override `nodePoolNames`, `tolerationKeys`, `spotTierPreferences` |
| `maxUnavailable` | No | Rolling update disruption % (≤100) |
| `alert_if_paused` | No | Alert when queue paused |
| `alert_pause_threshold_in_minutes` | No | Paused-queue alert threshold |
| `queues` | Shared only | List of queue names or `[name, weight]` pairs |
| `autoscaling.targetLatency` | No | Seconds; dedicated single-queue worker |
| `autoscaling.targetCPUUtilizationPercentage` | No | Override `defaults.targetCPUUtilizationPercentage` |
| `autoscaling.targetQueueLatencies` | No | Per-queue latency map (seconds, positive integers) |
| `resources.requests/limits` | No | Per-pod; partial override OK |
| `resources.*.ephemeralStorage` | No | Opt-in only; workers that spool large `/tmp` |
| `env` | No | Extra container env vars |
| `terminationGracePeriodSeconds` | No | Inherits `defaults.terminationGracePeriodSeconds` |

## Cluster type recipes

### Dedicated (key = queue name)

Use when:

- Latency SLA (`autoscaling.targetLatency`)
- Resource isolation (heavy memory/CPU)
- Static IP egress (`preemptive-static-ip`)
- Migration worker rules — see [`sidekiq_queue_config_checks_spec.rb`](https://github.com/apolloio/leadgenie/blob/master/packs/sidekiq/spec/sidekiq_queue_config_checks_spec.rb)

Deployment processes exactly one queue (worker key) unless `queues:` overrides.

### Shared `processor`

Non-preemptive general workloads. Append `[queue, weight]` to existing `queues:` list. Large `min_workers`/`max_workers` on the cluster entry control the whole fleet.

### Shared preemptive (`preemptive-high`, `preemptive-email-guesser-step2`, etc.)

Batch, crawler, migration, and heavy jobs on spot nodes. Multiple queues per deployment.

## Deriving impact from YAML

Do not hardcode sizing numbers in this skill. At activation, read:

| Source | Use for |
|--------|---------|
| [`kubernetes/charts/sidekiq-workers/values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml) | Chart `defaults:` (`concurrency`, `workerResources`, HPA CPU target, etc.) |
| [`kubernetes/charts/sidekiq-workers/templates/hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml) | `minReplicas`, `maxReplicas`, effective concurrency, latency scale-up threshold |
| [`kubernetes/production/sidekiq-workers/values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/production/sidekiq-workers/values.yaml) | Peer worker entries to copy structure and realistic sizing |

For a worker change, pick a **similar peer** in production values (same cluster type: dedicated vs shared, preemptive vs not), apply [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml) to compute before/after replica bounds, then fill the impact table.

### Patterns (no fixed numbers)

| Scenario | What to read |
|----------|--------------|
| Default sizing (no `threads_per_pod`) | Worker's `max_workers` + chart `defaults.concurrency` → `hpa.yaml` |
| Per-pod tuning | Worker with explicit `threads_per_pod` in production values → `hpa.yaml` |
| Strict concurrency | Worker where `max_workers < defaults.concurrency` → strict branch in `hpa.yaml` |

## Fleet totals at max scale

After resolving `minReplicas`, `maxReplicas`, and effective concurrency from [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml), merge per-pod resources from the worker entry and chart [`defaults.workerResources`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml) (see [`deployment.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/deployment.yaml) for merge rules). Report fleet CPU/memory at `maxReplicas`.

## CI constraints

Enforced in [`sidekiq_queue_config_checks_spec.rb`](https://github.com/apolloio/leadgenie/blob/master/packs/sidekiq/spec/sidekiq_queue_config_checks_spec.rb) — read the spec for current limits (worker name length, migration rules, queue parity, etc.). Do not duplicate thresholds here.

## Deploy context

- Helm release name: `sidekiq-workers`
- Deployed via production pipeline (rollback planning: [`devops`](../devops/SKILL.md) safe-mitigation path)
- Staging PR previews: label `Need_Sidekiq_Env`, edit [`kubernetes/staging/sidekiq-workers/values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/staging/sidekiq-workers/values.yaml)
