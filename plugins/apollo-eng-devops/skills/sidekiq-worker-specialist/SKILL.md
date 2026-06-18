---
name: sidekiq-worker-specialist
description: Tunes Apollo Sidekiq worker Helm values — max_workers, threads_per_pod, resources, autoscaling, shared vs dedicated clusters.
disable-model-invocation: true
---

# Sidekiq Worker Specialist

You tune Sidekiq worker fleet config in Helm values: thread budgets (`max_workers`), pod ceilings, and per-pod resources. Remember — `max_workers` is concurrent job slots, not pod count. Values control **Kubernetes Deployments and HPAs**, not GKE nodes.

## Key files

| File | Purpose |
|------|---------|
| `https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml` | Production worker fleet config |
| `https://github.com/apolloio/leadgenie/blob/master/kubernetes/staging/sidekiq-workers/values.yaml` | Staging overrides (subset; PR preview via `Need_Sidekiq_Env` label) |
| `https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/` | Helm chart (deployment, HPA, configmap templates) |
| `leadgenie/kubernetes/charts/sidekiq-workers/cluster-owners.yaml` | Team ownership per worker key |
| `https://github.com/apolloio/leadgenie/blob/master/packs/sidekiq/spec/sidekiq_queue_config_checks_spec.rb` | CI validation — run before opening PR |

Notion references (read when choosing cluster type or autoscaling). **Internal Apollo Notion pages — require login.** Do not fetch these URLs directly; they will fail without authentication. Share the links for the user to open, or use the Notion MCP if connected.

- [Sidekiq Overview](https://www.notion.so/apolloio/Sidekiq-Overview-5db91d4ed34a4f249762fa72e918912b)
- [Dedicated cluster concurrency / latency](https://www.notion.so/apolloio/Sidekiq-Dedicated-Cluster-Concurrency-Limit-Latency-Requirement-341e7e436cd1431e91c1f1e2fee0c29c)

______________________________________________________________________

## Mental model (read before editing)

```
workers.<name>  →  Deployment sidekiq-<name>  +  HPA  +  ConfigMap (concurrency + queues)
```

| Field | Meaning |
|-------|---------|
| `max_workers` | **Total Sidekiq thread budget** (concurrent jobs), **not** pod count |
| `min_workers` | Floor thread budget while HPA scales up (optional; default in chart `defaults:`) |
| `threads_per_pod` | Threads per pod; default `defaults.concurrency` in [`values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml) |
| `resources` | **Per-pod** CPU/memory; omitted fields inherit chart defaults |
| `preemptive: true` | Schedule on spot/preemptible node pools (prod only) |
| `queues` | Present only on **shared** clusters; dedicated clusters use the key name as queue |

### Pod count bounds

**Read [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml)** — do not hardcode replica math. That template maps `max_workers`, `min_workers`, and `threads_per_pod` (plus chart `defaults:`) to HPA `minReplicas` / `maxReplicas` and effective Sidekiq concurrency.

Omitted `resources` fields inherit [`defaults.workerResources`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml) from the chart — read at activation, do not assume values here.

See [`references/field-reference.md`](references/field-reference.md) for field tables, cluster-type recipes, and YAML sources for sizing.

______________________________________________________________________

## Ordered workflow

Always follow this sequence. Do not edit values before understanding current fleet behavior.

```
1. Classify change  →  2. Gather evidence  →  3. Compute impact  →  4. Edit values  →  5. Validate  →  6. Document in PR
```

### Step 1: Classify the change

| Goal | Where to edit |
|------|---------------|
| New queue, no latency SLA, batch/low priority | Shared `preemptive-high` or `preemptive` cluster `queues:` list |
| New queue, user-facing latency SLA | New **dedicated** worker key matching queue name |
| New queue, general app work | Shared `processor` cluster `queues:` list |
| Tune throughput / cost of existing fleet | Existing dedicated worker entry |
| OOM or CPU pressure | `resources` and/or `threads_per_pod` on that worker |
| Queue backlog, HPA pinned at max replicas | Raise `max_workers` (horizontal ceiling) |

**Choosing preemptive cluster:** Use `preemptive-high` for higher-priority batch work that tolerates spot eviction; use `preemptive` for lowest-priority background or crawler queues. Match the cluster that already hosts similar workloads in production values.

Worker key name must match the Sidekiq queue name for dedicated clusters (key = queue). Name length limit is in [`sidekiq_queue_config_checks_spec.rb`](https://github.com/apolloio/leadgenie/blob/master/packs/sidekiq/spec/sidekiq_queue_config_checks_spec.rb).

### Step 2: Gather evidence (before changing numbers)

Confirm the bottleneck — do not guess. **High CPU or queue latency does not always mean raise `max_workers`** — slow DB queries, N+1 loads, blocking I/O, or heavy per-job CPU can look like an infra problem. Rule out code inefficiency first (see [Tuning decision order](#tuning-decision-order)).

- **Slow jobs / high per-job runtime** (flat CPU but growing latency, or CPU scales linearly with job count) → optimize worker code or queries before scaling fleet
- **HPA pinned at max replicas** + high CPU + growing backlog **and** jobs are already efficient → raise `max_workers`
- **OOMKilled** (exit 137) → raise memory limit or lower `threads_per_pod`
- **CPU throttling** impacting throughput → raise CPU limit or lower `threads_per_pod`
- **Per-pod saturated but low replica count** → raise `max_workers` first, not threads (after code check)
- **Per-pod saturated at max replicas** → lower `threads_per_pod` or raise per-pod resources

Use GKE MCP or kubectl on deployment `sidekiq-<worker-name>`: `kubectl describe hpa`, `kubectl top pods`, pod events for OOMKill.

**Reach goal — Grafana utilization (optional):** When `mcp__grafana__query_prometheus` is in the available tools list (VPN + [Grafana MCP](../grafana-observability/SKILL.md#setup-grafana-mcp-server)), pull live metrics for the worker **before** changing values. Compare against the effective HPA targets from values (see [`references/field-reference.md`](references/field-reference.md#hpa-metrics-and-grafana-verification)). Include a short evidence block in the PR:

| Signal | Compare to |
|--------|------------|
| Fleet CPU utilization % | `autoscaling.targetCPUUtilizationPercentage` or chart `defaults.targetCPUUtilizationPercentage` |
| `sidekiq_queue_latency` | `autoscaling.targetLatency` or `targetQueueLatencies` (scale-up threshold in [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml)) |
| HPA current vs max replicas | `maxReplicas` from [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml) |

If Grafana MCP is not connected, continue with GKE MCP / kubectl only — do not block the workflow.

### Step 3: Compute impact (required in every PR)

Fill this table for the worker entry being changed:

**Shared-cluster queue append:** If you only add a queue to an existing shared cluster's `queues:` list and do not change cluster-level sizing fields, mark unchanged metrics as **N/A** and note that fleet bounds are unchanged. Recompute only if you also change `max_workers`, `resources`, or other cluster-level fields on that worker entry.

| Metric | Before | After |
|--------|--------|-------|
| `max_workers` (thread budget) | | |
| `threads_per_pod` | | |
| `max_replicas` (pods) | | |
| Per-pod CPU request / limit | | |
| Per-pod memory request / limit | | |
| Fleet CPU request at max scale | | |
| Fleet memory request at max scale | | |
| `preemptive` | | |

Resolve effective per-pod resources: merge worker `resources` with chart defaults for any omitted field. Derive `max_replicas` (HPA `maxReplicas`) from [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml) — do not duplicate that logic here.

### Step 4: Edit values

**Do not invent sizing numbers.** Read [`kubernetes/production/sidekiq-workers/values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/production/sidekiq-workers/values.yaml) for peer workers of the same cluster type and copy their field structure. Read chart defaults from [`kubernetes/charts/sidekiq-workers/values.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/values.yaml).

**Dedicated cluster** (latency-sensitive or isolated workload): new worker key = queue name; include `max_workers` and fields matching similar dedicated entries in production values.

**Shared cluster** (append to existing `queues:` — do not create duplicate queue entries): add `[queue_name, priority_weight]` to the target cluster's `queues:` list in production values.

**New queue:** Register the Ruby Sidekiq worker class and enqueue to that queue name in application code before or in the same PR as the Helm values change — CI checks queue ↔ Ruby worker parity.

**Rules:**

- Every worker entry **must** have `max_workers` (CI enforced — see spec below)
- Migration worker rules: enforced in [`sidekiq_queue_config_checks_spec.rb`](https://github.com/apolloio/leadgenie/blob/master/packs/sidekiq/spec/sidekiq_queue_config_checks_spec.rb)
- No duplicate queue names across workers (causes pod crashes)
- `autoscaling.targetQueueLatencies` keys must match queues in that worker's `queues:` list
- Add inline comment explaining **why** when changing limits (follow existing values.yaml style)

**Also update** `cluster-owners.yaml` when adding a new worker key.

**Staging:** `preemptive` is not supported on staging. Add worker to `kubernetes/staging/sidekiq-workers/values.yaml` for PR preview testing (`Need_Sidekiq_Env` label).

### Step 5: Validate

```bash
cd leadgenie
bundle exec rspec packs/sidekiq/spec/sidekiq_queue_config_checks_spec.rb
```

This spec verifies: queue ↔ Ruby worker parity, `max_workers` present, no duplicate queues, migration rules, autoscaling queue names, worker name length.

### Step 6: PR description

Include:

- Impact table from Step 3
- Evidence (HPA state, OOM events, queue latency, incident link)
- Rollout risk (preemptive = spot eviction; large `max_workers` = cluster resource cost)
- Staging tested? (yes/no)

______________________________________________________________________

## Tuning decision order

1. Optimize worker code — N+1 queries, slow DB calls, memory bloat, blocking I/O, redundant serialization. Scaling a slow job multiplies cost without fixing latency.
1. Raise `max_workers` if horizontally capped with backlog **and** per-job cost is acceptable
1. Adjust `threads_per_pod` when per-pod resources are saturated but replica count is low
1. Raise CPU only on confirmed throttling
1. Raise memory only on OOMKilled

______________________________________________________________________

## Common mistakes

| Mistake | Reality |
|---------|---------|
| `max_workers: 15` = 15 pods | = 15 **threads**; derive max pods from [`hpa.yaml`](https://github.com/apolloio/leadgenie/blob/master/kubernetes/charts/sidekiq-workers/templates/hpa.yaml) using current `defaults.concurrency` |
| Omitted `memory` = no memory | Inherits chart `defaults.workerResources` — read at activation |
| Raise threads to fix OOM | More threads per pod **increases** per-pod memory pressure |
| Add queue to two workers | Duplicate queue → pods crash (CI catches this) |
| Skip `cluster-owners.yaml` | Ownership audit fails on PR |

______________________________________________________________________

## Related skills

- [`kubernetes-specialist`](../kubernetes-specialist/SKILL.md) — pod/HPA debugging after deploy
- [`devops`](../devops/SKILL.md) — production change risk framing

## References

- [`references/field-reference.md`](references/field-reference.md) — fields, cluster recipes; sizing from leadgenie YAML only
