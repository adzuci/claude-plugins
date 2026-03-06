# Safe Production Mitigation Checklist

Before applying any mitigation to a production system, work through this checklist. These rules apply during incidents and during normal maintenance windows.

---

## Universal Rules

### One change at a time

Never apply multiple mitigations simultaneously. If the situation worsens after a change, you must be able to attribute it to a specific action. If you apply three changes at once and things get worse, you have no information about which change to revert.

### Rollback plan before you act

Before applying any change, state the rollback procedure out loud (or in the incident channel). If you cannot articulate a rollback, do not make the change. A mitigation you cannot undo is not a mitigation — it is a risk.

### Prefer reversible over irreversible

Order of preference (most reversible first):
1. Feature flag off
2. Rollback deploy
3. Revert config change
4. Scale adjustment
5. Hotfix deploy
6. Schema/data change (last resort, never mid-incident)

### Validate before prod when possible

If staging exists and replicates the issue, verify your mitigation there first. If you cannot reproduce in staging, document why you are proceeding directly to production.

### Capture timestamps for every action

Every action in production gets a timestamp. Use `HH:MM UTC | Action | Owner`. This is not optional. The timeline is the incident record.

### Minimal blast radius

Choose the mitigation that affects the fewest services and systems. If you can fix a downstream service without touching the upstream, start there.

---

## Apollo-Specific Checks

### Before any Kubernetes deploy

- Check current pod health: `kubectl get pods -n <namespace> | grep -v Running`
- Check HPA status: `kubectl get hpa -n <namespace>`
- Verify rollout strategy in Deployment spec (`maxSurge`, `maxUnavailable`)
- Confirm readiness probe is configured and healthy before rolling

### Before and after any Sidekiq change

- Check queue depth before: note depth for all critical queues (default, critical, low)
- After deploy: watch queue depth for 5 minutes — growth indicates a job processing failure
- If queues are draining abnormally slowly: check for job errors before continuing
- Do not deprovision Sidekiq workers while queues have jobs in-flight

### Before any Elasticsearch index operation

- Check cluster health: `GET /_cluster/health` — do not proceed if `yellow` or `red`
- Check pending tasks: `GET /_cluster/pending_tasks` — if tasks are backed up, wait
- For index changes: new index + reindex is always safer than modifying existing mappings
- Known clusters: `main`, `activities`, `field-enrichment`, `custom-objects` — know which you are touching
- Never force-delete shards during an active incident without explicit guidance from infra team

### Before any MongoDB change

- Check replication lag across replica set before schema changes
- If running a migration: use background index builds, never foreground during business hours
- Verify Redpanda consumer lag before Mongo schema changes — downstream consumers may fall behind

### Before any Redpanda / Kafka change

- Check consumer lag across all consumer groups before making changes: high lag means downstream services are behind
- Do not change topic retention or partition count during active processing
- Consumer group reset is irreversible — double-check the offset before committing

### Before declaring an issue novel

- Check `#eng-infrastructure-alerts` for prior context — many issues are recurring
- Check recent deploys in the last 2 hours
- Check Grafana for correlated changes in other services (annotation overlays)

---

## What Never to Do Mid-Incident

- Do not run database migrations
- Do not drop or truncate indices, tables, or collections
- Do not change retention policies
- Do not modify IAM roles or network policies
- Do not delete Kubernetes namespaces or PersistentVolumeClaims
- Do not run `kubectl delete` on anything you do not understand
- Do not `git push --force` to shared branches

If any of the above appear necessary to resolve the incident, escalate to the infra team and get explicit approval with a documented rollback plan.
