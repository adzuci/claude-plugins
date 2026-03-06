# Alerting Guidelines

Alert quality rules for Apollo's Grafana alerting stack, with Apollo-specific patterns.

---

## Core Rules

### Every alert must be actionable

If an alert fires and there is no action to take, it is a metric — not an alert. Remove it from the alert queue and add it to a dashboard panel instead.

Test: "If this alert fires at 3am, what is the exact first step the on-call engineer takes?" If the answer is anything other than a specific, concrete action, the alert needs to be revised or removed.

### Alerts fire on symptoms, not causes

| Type | Example | Verdict |
|------|---------|---------|
| Symptom (good) | Error rate > 1% for 5 min | Alert — user is experiencing failures |
| Symptom (good) | p99 latency > 2s for 5 min | Alert — user is experiencing slow responses |
| Cause (bad for alerts) | Redis CPU > 80% | Dashboard panel — may not be causing user impact |
| Cause (bad for alerts) | ES JVM heap > 75% | Dashboard panel — early warning, not a symptom |

### SLO burn rate alerts preferred over static thresholds

**Static threshold**: "Alert if error rate > 2%"
- Problem: 2% might be acceptable for one service and catastrophic for another

**SLO burn rate**: "Alert if error budget is burning at 14.4x normal rate (1-hour window)"
- 14.4x burn rate = error budget will be exhausted in 5 days (for 1-month window)
- Adjust the multiplier based on alert sensitivity vs. noise tolerance

### Every alert must have a runbook link

Required alert annotation fields:
```
runbook: <URL>
summary: <one-line description in user terms>
description: <current metric value and context>
```

---

## Severity Model

| Severity | Criteria | Response | Channel |
|----------|---------|----------|---------|
| P1 | SLO breach, active user impact, revenue loss | Page immediately, 24/7 | `#incidents` |
| P2 | Error budget at risk, degraded service | Investigate within 2 hours | `#eng-infrastructure-alerts` |
| P3 | Early warning, trend alert, no current user impact | Review in next sprint | `#eng-infrastructure-alerts` |

Do not route P3 alerts to `#incidents`. P3 noise in the incidents channel trains engineers to ignore it.

---

## Alert Audit Process

Run quarterly or whenever alert fatigue is reported:

1. **Pull firing history**: last 30 days, alert name, fire count, duration, resolution
2. **Rank by noise**: highest fire frequency = highest priority for audit
3. **For each high-frequency alert, assess**:
   - Mean time to resolve: < 5 min consistently → likely noisy
   - Correlation with actual user impact: < 50% → likely false positive
   - Most common resolution action: "nothing" or "silence" → should be removed
4. **Actions per alert**: tune threshold, increase time window, demote severity, or remove
5. **Document changes** with rationale — future engineers should understand why thresholds are set as they are

---

## Apollo-Specific Alert Patterns

### Elasticsearch cluster health

```
Metric: elasticsearch_cluster_health_status
Values: green=0, yellow=1, red=2
```

- **Red** (`status=2`): P1 — cluster is unavailable or data loss is occurring. Page immediately.
- **Yellow** (`status=1`): P2 — some replica shards are unassigned. Investigate within 2 hours.
- **Green** (`status=0`): healthy — no alert

**Apollo cluster names**: `main`, `activities`, `field-enrichment`, `custom-objects` — alert labels should include cluster name.

Known false positive: Saturday 17:00 UTC — staging ES restore job causes brief yellow status. Add a silencing rule for this window or document it in the runbook.

### Elasticsearch backup failure

- Alert on explicit backup failure, not on backup duration
- `eng-infrastructure-alerts` channel already receives these; check before creating duplicates
- Escalation: `@oncall-xfn-team-devops`

### Sidekiq queue depth

Alert on queue depth relative to baseline, not on absolute values:
- Queue consistently processing → depth fluctuates around baseline (not alertable)
- Queue growing without bound → depth increases monotonically (P2 alert)
- Queue backed up to N jobs without movement in M minutes → P1 if critical queue

Recommended: alert on queue growth rate, not queue depth snapshot.

```
# Pseudo-rule: alert if critical queue has grown by > 1000 jobs in last 5 minutes
# and is not recovering
```

### Redpanda / Kafka consumer lag

- Alert on consumer lag that is growing, not on a static threshold
- Some lag is normal during batch processing windows
- Alert if lag exceeds `max_acceptable_lag` for a sustained window (5-10 min)
- Per-consumer-group alerts are more actionable than aggregate lag alerts

### GKE node pressure

- Alert on `MemoryPressure=True` or `DiskPressure=True` at P2
- These conditions trigger pod evictions — investigate before they escalate
- Do not alert on individual pod restarts; alert on sustained CrashLoopBackOff (e.g., restart count > 5 in 10 min)

### `#eng-infrastructure-alerts` channel hygiene

This channel receives a high volume of automated alerts. Before adding new alerts to this channel:
- Review the existing alert volume to ensure new alerts are distinguishable
- Use message formatting that includes severity, service name, and runbook link
- Do not send P3 alerts or informational messages to this channel
