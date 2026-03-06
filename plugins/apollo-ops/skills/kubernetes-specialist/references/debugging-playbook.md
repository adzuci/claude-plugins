# Kubernetes Debugging Playbook

Step-by-step kubectl flows for diagnosing pod and cluster issues. Follow each flow in order — do not skip steps.

---

## Flow 1: Pod Status Investigation

Start here for any pod that is not in `Running` state or is running but unhealthy.

```bash
# Get pod status overview
kubectl get pods -n <namespace>
kubectl get pods -n <namespace> -o wide  # shows node assignment

# Get detailed pod status
kubectl describe pod <pod-name> -n <namespace>
```

Key fields to read in `kubectl describe`:
- **Status**: `Pending`, `Running`, `Succeeded`, `Failed`, `Unknown`
- **Conditions**: `PodScheduled`, `Initialized`, `ContainersReady`, `Ready`
- **Events**: scroll to the bottom — events are the most diagnostic field
- **Last State**: shows exit code and reason for the previous container instance

---

## Flow 2: Event Retrieval

Events show what Kubernetes has done to the pod, sorted by recency.

```bash
# Events for a specific pod
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>

# All events in namespace, sorted by time
kubectl get events -n <namespace> --sort-by=.lastTimestamp

# All events across namespaces (broad investigation)
kubectl get events --all-namespaces --sort-by=.lastTimestamp | tail -50
```

Common event messages and what they mean:

| Event message | Meaning |
|---------------|---------|
| `Failed to pull image` | Image not found or registry auth failure |
| `Back-off restarting failed container` | CrashLoopBackOff — container exiting repeatedly |
| `Insufficient cpu/memory` | Node does not have enough resources to schedule pod |
| `0/N nodes are available` | No schedulable nodes matching pod requirements |
| `Liveness probe failed` | Container is running but not healthy; restart triggered |
| `Readiness probe failed` | Container not yet ready to receive traffic |
| `Evicted` | Node was under resource pressure; pod evicted |
| `OOMKilling` | Container exceeded memory limit |

---

## Flow 3: Log Retrieval

```bash
# Current container logs (streaming)
kubectl logs <pod-name> -n <namespace> -f

# Current container logs (last N lines)
kubectl logs <pod-name> -n <namespace> --tail=100

# Previous container logs (crashed instance)
kubectl logs <pod-name> -n <namespace> --previous

# Logs from a specific container in a multi-container pod
kubectl logs <pod-name> -n <namespace> -c <container-name>

# Logs from all pods in a deployment (via label selector)
kubectl logs -n <namespace> -l app=<app-name> --all-containers
```

Always check `--previous` for CrashLoopBackOff pods — the current container may have crashed before writing any logs.

---

## Flow 4: CrashLoopBackOff Decision Tree

```
CrashLoopBackOff detected
│
├── kubectl logs --previous
│   ├── Application exception/fatal → code bug, review app logs
│   ├── "Address already in use" → port conflict, check service/pod config
│   ├── "No such file or directory" → missing config/secret mount
│   ├── Empty / no output → crash before any log output
│   │   └── Check exit code in kubectl describe
│   │       ├── 137 → OOMKilled (go to OOMKill flow)
│   │       ├── 139 → Segfault (application bug, native code)
│   │       └── Other → Check init containers
│   └── Connection refused → dependency not ready
│       └── Check readiness gates and startup probe configuration
│
└── kubectl describe pod
    ├── Check Limits → if memory limit very low → increase limit
    ├── Check Env/Secrets → if secretKeyRef → verify secret exists
    └── Check Init Containers → if init container failed → check init logs
```

---

## Flow 5: OOMKilled Investigation

```bash
# Confirm OOMKill
kubectl describe pod <pod-name> -n <namespace> | grep -B 2 -A 5 "OOMKilled\|Last State"

# Check current memory limits
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources}'

# Check current memory usage
kubectl top pod <pod-name> -n <namespace>
kubectl top pod -n <namespace> --sort-by=memory | head -20

# Check if there's a memory trend in Grafana
# Look for: container_memory_working_set_bytes for the pod
```

Decision:
- **Memory at limit, not growing**: limit is too low → increase limit by 30-50%
- **Memory growing without bound**: memory leak → do not just increase limit; investigate leak
- **Memory spiky**: need higher headroom → increase limit, set request lower

---

## Flow 6: Readiness Probe Failure Investigation

```bash
# Check probe configuration
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 "Readiness\|Liveness"

# Test probe endpoint directly
kubectl port-forward pod/<pod-name> -n <namespace> <local-port>:<container-port>
# In another terminal:
curl -v http://localhost:<local-port>/<probe-path>

# Check if dependency is causing probe failure
kubectl exec -it <pod-name> -n <namespace> -- curl -v http://localhost:<port>/<probe-path>

# Check startup timing
kubectl describe pod <pod-name> -n <namespace> | grep -E "initialDelaySeconds|periodSeconds|failureThreshold"
```

---

## Flow 7: Node Resource Pressure

```bash
# Check all nodes
kubectl top nodes
kubectl get nodes

# Identify pods on a specific node
kubectl get pods --all-namespaces -o wide | grep <node-name>

# Check node conditions
kubectl describe node <node-name> | grep -A 5 Conditions

# Check allocatable vs requested resources
kubectl describe node <node-name> | grep -A 20 "Allocated resources"
```

Rules:
- `MemoryPressure`: pods may be evicted; check for `Evicted` pods in namespace
- `DiskPressure`: clean up unused images or increase disk; `kubectl get pods` for `Evicted` pods
- Cordon before draining: `kubectl cordon <node-name>` prevents new scheduling without disrupting existing pods

---

## Flow 8: Exec Into Container (Last Resort)

Only exec if logs and describe have not identified the issue. Exec is a last resort because it requires the container to be running.

```bash
# Open a shell
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
# or if bash is not available:
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Run a single command without interactive shell
kubectl exec <pod-name> -n <namespace> -- env
kubectl exec <pod-name> -n <namespace> -- cat /etc/config/app.yaml
kubectl exec <pod-name> -n <namespace> -- curl -v http://localhost:8080/health
```

Do not modify files inside a running container as a fix — the change will be lost on restart. Fix the underlying Deployment/ConfigMap/Secret instead.
