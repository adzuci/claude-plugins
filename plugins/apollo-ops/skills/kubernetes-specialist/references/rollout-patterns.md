# Kubernetes Rollout Patterns

Rollout strategy selection guide with when-to-use guidance, configuration examples, and Apollo-specific notes.

______________________________________________________________________

## Strategy Selection Guide

| Strategy | When to use | Risk level | Rollback speed |
|----------|-------------|------------|----------------|
| Rolling update | Stateless services, backward-compatible changes | Low | Fast (undo) |
| Blue/green | Schema-adjacent changes, requires clean traffic cutover | Medium | Fast (traffic switch) |
| Canary | High-blast-radius changes, gradual exposure | Low-Medium | Fast (route traffic back) |
| Feature flag | Any change, preference during incidents | Lowest | Instant |

**Default**: Use rolling update for most stateless service deploys. Escalate to canary or blue/green only when the change is risky.

______________________________________________________________________

## Rolling Update

**When to use**: Stateless services, backward-compatible API changes, routine dependency upgrades.

**Requirements**: Healthy readiness probes configured. Without readiness probes, Kubernetes cannot determine when a new pod is ready to receive traffic.

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Extra pods during rollout (absolute or %)
      maxUnavailable: 0  # Zero pods unavailable at any time (safest)
```

For high-availability services: set `maxUnavailable: 0` and `maxSurge: 1` (or higher for faster rollout).

**Verify rollout**:

```bash
kubectl rollout status deployment/<name> -n <namespace>
# Wait for: "deployment "<name>" successfully rolled out"
```

**Rollback**:

```bash
kubectl rollout undo deployment/<name> -n <namespace>
kubectl rollout status deployment/<name> -n <namespace>
```

______________________________________________________________________

## Blue/Green Deployment

**When to use**: Schema migrations where old and new code cannot coexist, major API version changes, cases where you need instant full cutover with instant rollback.

**How it works**: Two identical deployments (`-blue` and `-green`). Traffic is controlled by a Kubernetes Service selector. Switch the selector to cut over; switch back to roll back.

**Requires**: A mechanism to switch traffic (Service selector update, Ingress rule change, or load balancer update).

```bash
# Switch service selector from blue to green
kubectl patch service <svc-name> -n <namespace> \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback: switch back to blue
kubectl patch service <svc-name> -n <namespace> \
  -p '{"spec":{"selector":{"version":"blue"}}}'
```

**Note**: Blue/green doubles resource consumption during the transition period. Ensure cluster capacity can absorb both deployments.

______________________________________________________________________

## Canary Deployment

**When to use**: High-blast-radius changes (affects all users), new code paths that cannot be validated in staging, gradual confidence building.

**How it works**: A small percentage of replicas runs the new version. Monitor for errors and latency before promoting to full rollout.

**Simple canary with replica count**:

```bash
# Start canary: 1 of 10 pods runs new version = ~10% traffic
# Existing deployment: 9 replicas of v1
# Canary deployment: 1 replica of v2

# Scale canary up gradually:
kubectl scale deployment/<name>-canary --replicas=3 -n <namespace>
# Now 3 of 12 pods = ~25% traffic

# Full promotion: update main deployment to v2, delete canary
kubectl set image deployment/<name> <container>=<image>:v2 -n <namespace>
kubectl delete deployment/<name>-canary -n <namespace>
```

**Monitor during canary**:

```bash
# Watch error rate per version in Grafana
# Or check pod-level metrics:
kubectl top pod -n <namespace> -l version=canary
```

______________________________________________________________________

## Feature Flags

**When to use**: Any production change, especially during or shortly after incidents. Prefer feature flags over deploys whenever the change can be controlled at the application level.

**Why first**: Feature flags decouple deployment from release. Code is deployed but not active until the flag is enabled. Rollback is instant (flip the flag) without a deploy.

Apollo context: Check whether the service uses a feature flag system before deploying risky changes. If it does, prefer gating the feature with a flag and deploying first, then enabling the flag after confirming deploy health.

______________________________________________________________________

## Rollback Procedures

### Deployment rollback

```bash
# Rollback to previous revision
kubectl rollout undo deployment/<name> -n <namespace>

# Rollback to specific revision (check history first)
kubectl rollout history deployment/<name> -n <namespace>
kubectl rollout undo deployment/<name> -n <namespace> --to-revision=<N>

# Verify rollback completed
kubectl rollout status deployment/<name> -n <namespace>

# Confirm running image version
kubectl get deployment/<name> -n <namespace> -o yaml | grep image:
```

### ConfigMap/Secret rollback

Rollbacks via `kubectl rollout undo` only revert the Deployment spec (image, env, etc.). ConfigMaps and Secrets are not versioned by default — you must reapply the previous version manually.

If a ConfigMap change caused an incident:

```bash
# Edit to revert to previous values
kubectl edit configmap <name> -n <namespace>
# Then trigger pod restart:
kubectl rollout restart deployment/<name> -n <namespace>
```

______________________________________________________________________

## HPA Configuration

**Scale-up aggressively, scale-down conservatively.**

```yaml
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <name>
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60  # Scale up when avg CPU > 60%
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Replicas
        value: 1
        periodSeconds: 60  # Remove at most 1 replica per minute
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Replicas
        value: 4
        periodSeconds: 60  # Add up to 4 replicas per minute
```

**Requirements**: Resource requests must be set. Without `resources.requests.cpu`, the HPA cannot calculate utilization percentage.

**Check HPA status**:

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
# Look for: "AbleToScale" and "ScalingActive" conditions
```

______________________________________________________________________

## Apollo-Specific Rollout Notes

**GKE node pool awareness**: When a new deployment requires nodes from a specific pool (e.g., high-memory workloads), check that the node pool has capacity before rolling out. Insufficient node pool capacity causes pods to stay `Pending`.

**Cloudflare tunnel deployment**: Changes to the Cloudflare tunnel deployment affect external traffic routing. Coordinate with the network team before rolling out changes to the tunnel node pool. Never drain a Cloudflare tunnel node without verifying traffic is routed to another tunnel first.

**`preview-master` namespace (staging)**: This namespace on the staging cluster is used for PR preview environments. Rolling updates here may disrupt active PR previews. Communicate changes to the team if a disruptive rollout is needed.

**Sidekiq workers**: When deploying a new Sidekiq worker version, ensure old jobs in-flight complete before removing old worker class definitions. The safe pattern: deploy new code with old class still present → drain queues → remove old class in follow-up deploy.
