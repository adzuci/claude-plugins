# SRE Top 10: Enforceable Reliability Modules

Each module includes a core principle, an enforceable check, and Apollo-specific context.

---

## 1. Embracing Risk

**Principle**: Unrealistic reliability targets waste engineering effort. The right target is the one users need — and no higher. Incremental improvement in availability has diminishing returns and increasing cost.

**Enforceable check**: Does this service have a documented availability target? Is that target calibrated against user tolerance and business impact, or is it a guess?

**Apollo context**: Not every service needs five nines. Internal tooling (admin dashboards, background enrichment jobs) can tolerate higher error rates than customer-facing search and sequence APIs. Check whether the service has a documented SLO before investing in reliability improvements.

---

## 2. SLOs and Error Budgets

**Principle**: SLOs define the target reliability level. Error budgets quantify how much unreliability is acceptable in a rolling window. When budget is exhausted, reliability work takes precedence over feature work.

**Enforceable check**: What are the current SLOs for this service? What is the error budget status for the current 30-day window?

**Apollo context**:
- GKE services: measure latency p50/p99 and 5xx rate at the ingress level
- Elasticsearch clusters: indexing latency, query latency, cluster health status
- Sidekiq: job failure rate, queue depth growth, job latency
- Redpanda: consumer lag as a proxy for pipeline SLO breach
- MongoDB: op latency p99, replication lag

---

## 3. Eliminating Toil

**Principle**: Toil is manual, repetitive, automatable work that grows with service scale. If the SRE team spends more than 50% of time on toil, reliability suffers because there is no time for engineering work.

**Enforceable check**: Which steps in this runbook are manual and could be automated? Is this runbook growing over time?

**Apollo context**: Common toil sources at Apollo:
- Manual ES index health checks that could be automated alerts
- Manual Sidekiq queue drain verification post-deploy
- Manual Redpanda consumer group lag checks
- Repeated GKE pod restart investigations for the same service

---

## 4. Monitoring Distributed Systems

**Principle**: Monitor symptoms (user-facing effects), not causes (internal system state). The four golden signals are latency, traffic, errors, and saturation.

**Enforceable check**: Does this service have alerting on all four golden signals? Are alerts firing on symptoms or on internal state?

**Apollo context**:
- GKE: instrument at the service mesh / ingress level for latency and error rate; node-level for saturation
- ES: query latency and error rate are symptoms; JVM heap and shard count are causes
- Sidekiq: job latency and failure rate are symptoms; queue depth is an early warning cause metric
- Redpanda: consumer lag is a symptom of pipeline degradation

---

## 5. Automation Evolution

**Principle**: Automation follows a maturity ladder: no automation → externally maintained scripts → internally maintained automation → self-healing systems. The goal is to move up the ladder, not to stay at manual.

**Enforceable check**: Where does this operational procedure sit on the automation ladder? What would it take to move it up one level?

**Apollo context**: Apollo's GKE and Terraform V2 patterns represent the infrastructure-as-code layer. Runbooks that reference manual `kubectl` commands are candidates for automation via Kubernetes operators, CronJobs, or GitHub Actions.

---

## 6. Release Engineering

**Principle**: Reliable releases require: reproducible builds, version control for all configuration, canary deployments for blast radius reduction, and always-available rollback.

**Enforceable check**: Does this deploy have a rollback procedure? Is the rollback tested? What is the blast radius if this deploy goes wrong?

**Apollo context**:
- GKE deployments: rolling updates for stateless services, blue/green for risky schema-adjacent changes
- Terraform changes: plan before apply, always review the diff
- ES index mappings: mapping changes are irreversible — new index + reindex is the safe path
- Sidekiq job changes: old job code must remain deployed until all in-flight jobs complete

---

## 7. Simplicity

**Principle**: Operational complexity kills reliability. Every additional service, configuration option, and abstraction layer increases the probability of failure and slows incident response.

**Enforceable check**: Can a new engineer understand and debug this system in under 30 minutes from the runbook alone? If not, it is too complex.

**Apollo context**: Apollo's infrastructure spans GKE, ES, Mongo, Redpanda, and Sidekiq. Each integration point is a failure domain. Challenge whether new integration points are necessary before adding them.

---

## 8. Practical Alerting

**Principle**: Every alert must be actionable. An alert that fires with no clear action is noise, and noise trains engineers to ignore alerts, which causes missed incidents.

**Enforceable check**: If this alert fires at 3am, what exactly does the on-call engineer do? Is that documented in a runbook? If the answer is "nothing, just wait" — it is not an alert.

**Apollo context**:
- `#eng-infrastructure-alerts`: review patterns before adding new alerts to this channel — it already carries high volume
- ES backup failure alerts: distinguish between the weekly Saturday staging restore (expected) and actual backup failures
- Sidekiq queue depth: set thresholds relative to normal throughput, not absolute values
- GKE pod restarts: alert on sustained CrashLoopBackOff, not on the first restart

---

## 9. Effective Troubleshooting

**Principle**: Structured debugging avoids wasted effort and harmful side effects. Observe before hypothesizing. Test one hypothesis at a time. Never apply a fix without understanding why it works.

**Enforceable check**: Have we gathered enough signal before applying a mitigation? Do we understand why this mitigation should work?

**Apollo context**: The ordered flow: Describe → Logs → Events → Exec → Metrics → Scale. Skipping steps leads to "fixed it but I'm not sure why" — which means it will happen again. For ES cluster issues, always check cluster health and shard allocation before touching index settings.

---

## 10. Incident Management and Postmortems

**Principle**: Incidents are normal in complex systems. What differentiates good SRE teams is how they respond (structured, calm, documented) and how they learn (blameless postmortems with actionable follow-ups).

**Enforceable check**: Does this incident have a declared commander? Is the timeline being recorded? Will this incident get a postmortem?

**Apollo context**:
- SEV1/SEV2: postmortem required within 5 business days
- Timeline format: `HH:MM UTC | Action | Owner`
- Postmortem action items: categorize as prevent / detect / mitigate / process
- `@oncall-xfn-team-devops`: primary escalation path for infrastructure incidents
