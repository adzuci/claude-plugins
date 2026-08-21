# Related Runbooks And Skills

This skill is a gate, not an encyclopedia. Three other things cover adjacent ground. Use them instead of duplicating their content here.

## The Boundary In One Line Each

- **`/apollo-eng-devops:k8s-safe-exec`** (this skill) — gates **before** a command runs, and verifies health after.
- **`/apollo-eng-devops:kubernetes-specialist`** — diagnoses **after** something breaks.
- **Notion runbook** — the manual human walkthrough for a person doing it by hand.

## Notion: How To SSH Into Kubernetes Pod And Start Rails

"Runbook: How to SSH into Kubernetes Pod and Start Rails"
<https://www.notion.so/apolloio/How-to-SSH-into-Kubernetes-Pod-and-Start-Rails-5478c4e317c54c4194c1d09f0dd737cb>

The human-facing walkthrough. It documents both the `kubectl exec -it` path and an ephemeral-pod trick. Its prerequisites are the ones `scripts/preflight.sh` checks mechanically:

- `gcloud init` completed, and kubectl installed via `gcloud components install kubectl`.
- **Staging VPN** connected for staging work.
- **Prod is a separate VPN** with restricted access — only the infra team plus some senior engineers can connect to prod pods directly. If you cannot reach prod, this is the usual reason, and it is not something to retry around.
- A preview environment's namespace is commented on your PR by the `apolloio-ci` bot. If the comment is missing, add the `Need_Preview_Env` label to the PR.

Point users at the runbook when they want to understand the manual flow or when they are working outside a Claude session. Do not restate its steps in this skill.

## /apollo-eng-devops:kubernetes-specialist

The debugging and rollout reference for Apollo's GKE clusters: CrashLoopBackOff triage, OOMKilled triage and limit tuning, readiness/liveness failures, node-level debugging, rollouts and rollbacks, HPA guidance, and resource request/limit sanity checks.

Hand off to it when the post-run health check comes back bad — `OOMKilled`, `Evicted`, `CrashLoopBackOff`, a stuck rollout, or replica counts that do not recover. Do not reimplement its triage flow inside this skill.

## /apollo-eng-devops:sidekiq-worker-specialist

Tunes Apollo Sidekiq worker Helm values: `max_workers`, `threads_per_pod`, resources, autoscaling, and shared vs dedicated clusters.

Relevant when the pod you were about to exec into is a Sidekiq worker and the memory-risk pre-check shows it is chronically near its limit. That is a sizing problem, not a one-off command problem — the durable fix lives in the Helm values, not in a safer exec.
