# Reliability Design Review Checklist

Use this checklist when reviewing any new service, feature, pipeline, or infrastructure change. Completing this checklist before launch is the cheapest reliability investment available.

______________________________________________________________________

## 1. SLO Definition

- [ ] Latency target defined: p50 and p99 for user-facing endpoints
- [ ] Error rate target defined: acceptable 5xx rate per rolling window
- [ ] Availability target defined: monthly or weekly uptime percentage
- [ ] Data freshness target defined (if applicable): maximum acceptable lag
- [ ] SLO window defined: 30-day rolling or calendar month?
- [ ] Who owns the SLO? Who is paged when it breaches?

**If no SLOs are defined**: the service cannot be safely operated. Define them before launch or accept that reliability is undefined.

______________________________________________________________________

## 2. Failure Mode Analysis

For each external dependency (database, queue, cache, third-party API):

- [ ] What happens when this dependency is slow (latency spike)?
- [ ] What happens when this dependency is unavailable (outage)?
- [ ] What happens when this dependency returns corrupt data?
- [ ] Is there a circuit breaker or timeout?
- [ ] Is there a fallback path (cache, degraded mode, queue)?
- [ ] Will failure cascade to upstream services?

**Apollo-specific dependencies to check**:

- Elasticsearch: what if cluster is yellow/red during indexing?
- MongoDB: what if replication lag spikes during a read?
- Redpanda: what if consumer lag grows unbounded?
- Sidekiq: what if job queue depth exceeds worker capacity?

______________________________________________________________________

## 3. Toil Assessment

- [ ] What manual operational work does this service create on day 1?
- [ ] What manual work will it create at 10x scale?
- [ ] Are there any steps in the deployment runbook that must be performed by a human?
- [ ] Are there any monitoring responses that require a human to take repetitive action?
- [ ] Is there a plan to automate the highest-toil items within 2 sprints of launch?

______________________________________________________________________

## 4. Observability Requirements

- [ ] Metrics: which four golden signals (latency, traffic, errors, saturation) are instrumented?
- [ ] Logs: are logs structured (JSON)? Do they include correlation IDs for distributed tracing?
- [ ] Traces: is distributed tracing enabled for cross-service calls?
- [ ] Alerts: at minimum, alerts for p99 latency breach and error rate breach
- [ ] Dashboard: USE method for infrastructure resources, RED method for service endpoints
- [ ] Runbook: linked from every alert

______________________________________________________________________

## 5. Rollout Strategy

- [ ] Is this a stateless service? → rolling update is appropriate
- [ ] Does this change include a schema change or data migration? → blue/green or feature flag required
- [ ] Is the blast radius high (affects all users)? → canary deployment required
- [ ] Is a feature flag available? → prefer feature flag over deploy for first exposure

**Rollout order** (safest to riskiest):

1. Feature flag (no deploy required, instant rollback)
1. Canary (% traffic routing, gradual exposure)
1. Blue/green (full traffic switch, fast rollback)
1. Rolling update (default for low-risk stateless services)

______________________________________________________________________

## 6. Rollback Plan

- [ ] How do you roll back a bad deploy? (`kubectl rollout undo` or equivalent)
- [ ] How long does rollback take? Is it fast enough for SEV1?
- [ ] If a database migration is involved, can it be reversed?
- [ ] Is the previous version still available in the image registry?
- [ ] Are feature flags available to disable the new behavior without a deploy?

______________________________________________________________________

## 7. Runbook Required?

A runbook is required if any of the following are true:

- [ ] The service has an on-call rotation or is paged on failure
- [ ] Recovery requires non-obvious steps (not just "restart the pod")
- [ ] The service interacts with data stores in ways that could cause data loss or corruption
- [ ] The service has operational procedures that must be followed in a specific order

Runbook minimum contents: what the service does, how to confirm it is healthy, how to restart it safely, who to escalate to.

______________________________________________________________________

## 8. Apollo-Specific Patterns

### Elasticsearch index changes

- New index + reindex pattern: never modify existing index mappings in-place for breaking changes
- Mapping additions (backward compatible) can be applied with `PUT /<index>/_mapping`
- Alias-based index management: services should read/write via alias, not direct index name
- Reindex jobs: run as Kubernetes Jobs in the appropriate namespace; do not run ad-hoc

### MongoDB migrations

- Background index builds only — never foreground during business hours
- Migration scripts must be idempotent
- Test against a production-sized dataset before running in prod
- Coordinate with Redpanda consumer owners before schema changes

### Terraform V2 patterns

- All infra changes via Terraform — no manual GCP console changes in production
- Plan output must be reviewed before apply
- Sensitive resources (IAM, network, databases): require second reviewer on PR

### Redpanda consumer lag handling

- New consumers: start at latest offset, not earliest, unless data backfill is required and coordinated
- Schema changes: use schema registry, coordinate with all consumer teams before deploying
- Consumer group reset: document the intent and get approval before executing

### Sidekiq queue growth during deploy

- Keep old worker code available until all in-flight jobs complete
- Use `Sidekiq::Queue.new('queue_name').size` to verify drain before decommissioning workers
- If a new job class is introduced, old workers must be drained before removing old class definition
