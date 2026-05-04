# Routing Rules: DevOps vs Backend Platform

Every triaged ticket gets exactly one team. If you can't justify the routing in one clause, route it as `?` and ask the reporter.

## DevOps owns

- Kubernetes / GKE: node pools, HPA, pod scheduling, cluster upgrades.
- Datastores at the cluster level: Elasticsearch shard/index ops, MongoDB cluster health, Redpanda broker ops.
- Networking: DNS, Cloudflare, ingress, certs, VPN.
- IAM, secrets management, vault, GCP project config.
- CI/CD pipelines (GitHub Actions runners, Argo, deploy tooling).
- Observability infra (Grafana, Prometheus, alert rules).
- Base image CVEs (the OS layer, not the app deps).
- Terraform and IaC.

## Backend Platform owns

- Application code in Rails / Node services.
- Sidekiq job code (logic, retries, dead set handling) — DevOps owns the queue infra, Backend Platform owns the jobs running on it.
- API regressions, controller/service errors.
- App-level dependency CVEs (Ruby gems, npm packages used by app code).
- Schema changes and migrations.
- Feature flag misconfiguration in app code.
- Search relevance / ES query logic (DevOps owns the cluster, Backend owns the queries).

## Tie-breakers

- **CVE in a gem used only by a deprecated path**: Backend Platform comments on reachability; DevOps does not own gem upgrades.
- **Sidekiq queue depth alarm**: DevOps if queue infra is degraded (Redpanda lag, worker pods OOM); Backend Platform if a specific job class is slow or erroring.
- **Mongo connection errors**: DevOps if cluster health is bad; Backend Platform if a specific query is malformed or unindexed.
- **Deploy failure**: DevOps if pipeline / runner / image push is broken; Backend Platform if app boot fails or migration errors.

## When to route as `?`

- Ticket is a one-liner with no service named.
- Reporter is unknown / external and the description is generic ("site is slow").
- Symptoms span multiple services with no clear primary.
- "Fix the security thing" with no CVE id or scanner output.

For `?` rows, propose a reporter comment from `comment-templates.md` (the "ask-reporter" block) — don't guess.
