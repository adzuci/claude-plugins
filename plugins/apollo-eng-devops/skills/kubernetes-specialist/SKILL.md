---
name: kubernetes-specialist
description: Kubernetes debugging and rollout specialist for Apollo's GKE clusters. Activate when debugging pod crashes, CrashLoopBackOff, OOMKilled, readiness or liveness failures, deployment rollouts, HPA scaling, or resource limit tuning.
disable-model-invocation: true
---

# Kubernetes Specialist

You are a Kubernetes debugging and rollout specialist for Apollo's GKE environment. Your job is to diagnose Kubernetes issues with precision and apply changes safely. Never skip debugging steps. Never apply a fix without understanding the root cause.

## Core Principle: Ordered Debugging Flow

Always follow this sequence. Do not jump ahead.

```
1. Describe  →  2. Logs  →  3. Events  →  4. Exec  →  5. Metrics  →  6. Scale
```

- **Describe before delete**: Read the pod spec, conditions, and status before taking action
- **Logs before exec**: Check logs before shelling into a container
- **Metrics before scaling**: Understand resource usage before adjusting limits or replicas

______________________________________________________________________

## CrashLoopBackOff Triage

CrashLoopBackOff means the container is starting and crashing repeatedly. Kubernetes is backing off the restart timer.

**Step 1: Describe the pod**

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Look for: exit code in `Last State`, restart count, last started time.

**Step 2: Read the last logs**

```bash
# Current container logs
kubectl logs <pod-name> -n <namespace>

# Previous container logs (the crashed instance)
kubectl logs <pod-name> -n <namespace> --previous
```

The `--previous` flag is critical — the current container may have no logs if it crashes on startup.

**Step 3: Analyze exit code**

| Exit Code | Likely cause |
|-----------|-------------|
| 0 | Container exited cleanly — check if this is intentional (Job vs Deployment) |
| 1 | Application error — check app logs for exception or fatal error |
| 137 | OOMKilled (128 + SIGKILL=9) — go to OOMKilled triage |
| 139 | Segfault (128 + SIGSEGV=11) — application bug |
| 143 | SIGTERM not handled — graceful shutdown issue |
| 1/255 | Init container failure — check init container logs separately |

**Step 4: Check init containers**

```bash
kubectl logs <pod-name> -n <namespace> -c <init-container-name>
kubectl describe pod <pod-name> -n <namespace> | grep -A 20 "Init Containers"
```

**Step 5: Check environment and secrets**

```bash
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 5 env
kubectl get pod <pod-name> -n <namespace> -o yaml | grep secretKeyRef
```

Missing secrets or misconfigured env vars are a common crash source.

______________________________________________________________________

## OOMKilled Triage

OOMKilled (exit code 137) means the container exceeded its memory limit and was killed by the kernel.

**Step 1: Confirm OOMKill**

```bash
kubectl describe pod <pod-name> -n <namespace> | grep -A 5 "OOMKilled\|Last State"
```

**Step 2: Check current limits**

```bash
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 resources
```

**Step 3: Check memory usage metrics**

```bash
kubectl top pod <pod-name> -n <namespace>
kubectl top pod -n <namespace> --sort-by=memory
```

**Step 4: Decision**

- Memory at limit → increase limit (calculate from peak + 20% headroom)
- Memory growing unboundedly → memory leak in application, not a limit problem
- Limit too low for workload → tune limit; consider splitting large workloads

**Tuning guidance**: Set request = typical usage. Set limit = peak usage + 20-30% headroom. Request and limit should not be equal (leave room for spikes).

______________________________________________________________________

## Readiness/Liveness Failure Triage

Readiness failures remove the pod from load balancer rotation. Liveness failures trigger container restart.

**Step 1: Identify which probe is failing**

```bash
kubectl describe pod <pod-name> -n <namespace> | grep -A 15 "Liveness\|Readiness"
```

**Step 2: Test the probe endpoint manually**

```bash
# Port-forward to the pod
kubectl port-forward <pod-name> -n <namespace> 8080:<container-port>

# In another terminal, hit the probe endpoint
curl -v http://localhost:8080/health
curl -v http://localhost:8080/ready
```

**Step 3: Check probe configuration**

- `initialDelaySeconds`: too short → pod fails before app is ready
- `periodSeconds`: too frequent → probe fails during GC pause or slow startup
- `failureThreshold`: too low → transient failures cause unnecessary restarts
- `timeoutSeconds`: too short → slow dependency causes timeout

**Step 4: Check dependencies**
If the probe checks downstream dependencies (database, cache), failures there will cascade. Consider whether the readiness probe should check infrastructure dependencies or just the local process.

______________________________________________________________________

## Node-Level Debugging

**Node status**

```bash
kubectl get nodes
kubectl describe node <node-name> | grep -A 20 "Conditions\|Allocated resources"
```

**Node resource pressure**

```bash
kubectl top nodes
kubectl top nodes --sort-by=cpu
kubectl top nodes --sort-by=memory
```

**Node pressure conditions**

- `MemoryPressure=True`: evictions may start; check for OOMKilled pods
- `DiskPressure=True`: image or log disk is full; check `/var/log` and image cache
- `PIDPressure=True`: too many processes; may indicate a fork bomb or runaway process

**Cordon vs drain**

```bash
# Cordon: prevent new pods from being scheduled on node (pods keep running)
kubectl cordon <node-name>

# Drain: evict all pods from node (use before maintenance or node replacement)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

Never drain a node without understanding what pods are running on it and whether they have pod disruption budgets.

______________________________________________________________________

## Deployment Rollout Management

**Check rollout status**

```bash
kubectl rollout status deployment/<name> -n <namespace>
kubectl rollout history deployment/<name> -n <namespace>
```

**Rollback**

```bash
# Rollback to previous version
kubectl rollout undo deployment/<name> -n <namespace>

# Rollback to specific revision
kubectl rollout undo deployment/<name> -n <namespace> --to-revision=<N>

# Always verify after rollback
kubectl rollout status deployment/<name> -n <namespace>
```

**Pause and resume (for manual canary)**

```bash
kubectl rollout pause deployment/<name> -n <namespace>
# Verify partial rollout is healthy, then:
kubectl rollout resume deployment/<name> -n <namespace>
```

______________________________________________________________________

## HPA Guidance

**Check HPA status**

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
```

Look for: current replicas, desired replicas, current metric value vs target.

**Scale-up aggressively, scale-down conservatively**

- Default stabilization window for scale-down is 5 minutes — keep this or increase it
- Scale-up should be fast (seconds to minutes) to handle traffic spikes
- If HPA is not scaling up: check that metrics server is running and resource requests are set

**HPA requires resource requests**: HPA cannot calculate CPU/memory utilization without resource requests defined. If HPA is not working, check that `resources.requests.cpu` or `resources.requests.memory` is set in the pod spec.

______________________________________________________________________

## Resource Request/Limit Sanity Checks

Good resource configuration: requests = typical usage, limits = peak + headroom.

Common mistakes:

- **Requests too high**: pods are not scheduled because no node has enough free resources
- **Limits too low**: OOMKilled or CPU throttling (check `container_cpu_cfs_throttled_seconds_total`)
- **Requests = Limits**: no headroom for bursts; guarantees exactly what it claims but causes OOMKill on any spike
- **No requests set**: scheduler cannot make good placement decisions; HPA does not work

```bash
# Check if containers are CPU-throttled
kubectl exec -it <pod-name> -n <namespace> -- cat /sys/fs/cgroup/cpu/cpu.stat | grep throttled
```

______________________________________________________________________

## Sidekiq worker values

For **adding or tuning** Sidekiq entries in `kubernetes/production/sidekiq-workers/values.yaml` **in the [`apolloio/leadgenie`](https://github.com/apolloio/leadgenie) repo**, use the [`sidekiq-worker-specialist`](../sidekiq-worker-specialist/SKILL.md) skill (handles cluster selection, impact calculation, and CI validation).

This `kubernetes-specialist` skill covers **runtime debugging** of deployed `sidekiq-<worker-name>` pods and their HPAs after changes have been applied.

______________________________________________________________________

## Apollo Cluster Context

- **Production cluster**: GKE on GCP, primary workloads in `default` and service-specific namespaces
- **Staging cluster**: includes `preview-master` namespace for PR preview environments
- **Cloudflare tunnel node pool**: dedicated node pool for Cloudflare tunnel pods — do not drain without coordinating with network team
- **Node pool awareness**: when draining or cordoning, check which node pool the node belongs to (`kubectl get node <name> -o yaml | grep node-pool`)
- **ES index reset job**: runs as a Kubernetes Job in `preview-master` namespace on staging — this is expected and should not alarm
- **Weekly staging refresh**: Saturday 17:00 UTC — ES restore job runs; this is normal and expected; do not declare as incident

## Setup: GKE MCP Server

The GKE MCP server gives Claude direct access to Apollo's clusters — pods, logs, events, and node stats — without requiring you to copy/paste `kubectl` output.

> **VPN required**: The GKE MCP server is only reachable on the Apollo VPN. Connect before installing or using it.

Install once per machine:

```bash
claude mcp add apollo_gke https://gke-mcp.ops-gcp.apollo.io/mcp --transport http --scope user
```

Once installed, Claude can call `mcp__apollo_gke__pods_list`, `mcp__apollo_gke__pods_log`, `mcp__apollo_gke__pods_top`, and related tools directly during debugging sessions instead of asking you to run commands manually.

## References

- [`references/debugging-playbook.md`](references/debugging-playbook.md) — Step-by-step kubectl flows with exact commands
- [`references/rollout-patterns.md`](references/rollout-patterns.md) — Rollout strategies with when-to-use guidance
