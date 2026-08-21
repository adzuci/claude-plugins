# OOMKilled vs Evicted

These two are easy to conflate and they mean different things. One is scoped to your container. The other means the whole node ran out of memory.

## OOMKilled — Container Exceeded Its Own Limit

The container's cgroup hit `resources.limits.memory`. The kernel OOM killer terminates the process. Exit code is `137` (128 + SIGKILL 9).

- **Scope**: that one container.
- **Pod object**: survives. Kubelet restarts the container per `restartPolicy` and the restart count increments.
- **Where it surfaces**: the pod's `.status.containerStatuses[].lastState.terminated.reason`.

```bash
kubectl -n <ns> get pod <pod> \
  -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.restartCount}{"\t"}{.lastState.terminated.reason}{"\t"}{.lastState.terminated.exitCode}{"\n"}{end}'

kubectl -n <ns> describe pod <pod> | grep -A4 'Last State'
```

## Evicted — The Node Ran Low On Memory

Kubelet detected the node crossing its memory eviction threshold and proactively evicted pods to reclaim allocatable memory. Nothing about your container's own limit is necessarily involved.

- **Scope**: the node. Other pods on that node were eviction candidates too, ranked by QoS class and how far they exceeded their requests.
- **Pod object**: moves to phase `Failed` with reason `Evicted` and is **terminated, not restarted in place**. A Deployment must reschedule a replacement, possibly on a different node.
- **Where it surfaces**: pod-level `.status.phase` / `.status.reason`, plus an event whose message cites the node's threshold and available memory (for example, "The node was low on resource: memory").

```bash
kubectl -n <ns> get pod <pod> \
  -o jsonpath='{.status.phase}{"\t"}{.status.reason}{"\t"}{.status.message}{"\n"}'

# Evicted pods across the namespace
kubectl -n <ns> get pods --field-selector status.phase=Failed

# The event that names the node threshold
kubectl -n <ns> get events --field-selector involvedObject.name=<pod> \
  --sort-by=.lastTimestamp

# Node-side confirmation
kubectl get node <node> \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status}{" "}{end}{"\n"}'
kubectl top node <node>
```

## Quick Comparison

| | OOMKilled | Evicted |
|---|---|---|
| Trigger | Container exceeded its own memory limit | Node crossed its memory eviction threshold |
| Actor | Kernel OOM killer | Kubelet |
| Exit code | `137` | n/a — pod terminated, not a container exit |
| Surfaces at | `containerStatuses[].lastState.terminated.reason` | pod `.status.phase=Failed`, `.status.reason=Evicted` + event |
| Pod object | Survives, restart count increments | Terminated; controller must reschedule |
| Blast radius | That container | The node — other pods were candidates too |
| Restart behavior | Kubelet restarts in place | Rescheduled elsewhere, possibly delayed |

## Worked Example — The Incident This Skill Came From

1. An engineer ran a one-shot `rails runner` via `kubectl exec` inside a live `sidekiq-google-search-linkedin-shared` pod in prod. The `rails runner` process allocated inside the container's existing cgroup, on top of what Sidekiq was already using. The container crossed its memory limit and was **OOMKilled**. Blast radius: that Sidekiq container, restarted in place.

1. On retry, the same allocation pushed the **node** past its memory eviction threshold. Kubelet evicted the pod: `Failed` / `Evicted`, with an event citing the node being low on memory.

The second outcome is the more serious signal. An OOMKill says "my container asked for too much." An eviction says "the node has no memory left" — which means other tenants on that node were at risk, the pod was destroyed rather than restarted, and rescheduling depends on another node having capacity. If a post-run health check reports `Evicted`, treat it as a node-level event and hand off to `/apollo-eng-devops:kubernetes-specialist`.

Practical consequence: after an eviction the pod may be gone entirely, so a "pod not found" result from the post-run health check is itself a finding. Check the Deployment's replica counts and namespace events, not just the pod name.
