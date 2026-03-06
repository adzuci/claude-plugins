# Incident Decision Framework

Use this framework to structure incident response from first signal to resolution.

______________________________________________________________________

## Step 1: Is This an Incident?

Answer these questions in order:

1. **Is there active user impact?**

   - Yes → proceed to SEV classification
   - No → treat as production debugging (use devops debugging flow)

1. **Is the impact growing, stable, or recovering?**

   - Growing → escalate SEV level, increase comms cadence
   - Stable → maintain current SEV, focus on mitigation
   - Recovering → verify trend before declaring resolved

1. **Is this caused by a recent change?**

   - Yes (deploy, config change, migration in last 2h) → rollback is first mitigation to consider
   - No → deeper investigation required before mitigation

______________________________________________________________________

## Step 2: Classify Severity

| SEV | Criteria | Response |
|-----|----------|----------|
| SEV1 | All users impacted, revenue loss, data loss, complete service outage | Page IC + exec escalation immediately |
| SEV2 | Partial user impact, degraded service for a significant user segment | Page IC, notify stakeholders |
| SEV3 | Degraded service with workaround available | Investigate during business hours, notify team |
| SEV4 | Minor issue, no user impact, cosmetic or edge case | Ticket + fix in next sprint |

______________________________________________________________________

## Step 3: What SLO Is Breached or At Risk?

Identify the specific SLO:

- **Availability SLO**: percentage of successful requests in rolling window
- **Latency SLO**: p99 latency target (e.g., < 500ms for 95% of requests)
- **Throughput SLO**: minimum processing rate (e.g., Sidekiq job throughput)
- **Data freshness SLO**: maximum acceptable lag (e.g., Redpanda consumer lag < 5 min)

If no SLO is defined, treat the incident as SLO-defining evidence — document the observed baseline and use it to set a target post-incident.

______________________________________________________________________

## Step 4: Error Budget Status

Determine error budget consumption:

- **Budget healthy (< 50% consumed in window)**: slower, more careful mitigation acceptable
- **Budget at risk (50–80% consumed)**: fast mitigation, prioritize reliability work this sprint
- **Budget exhausted (> 80% consumed)**: reliability work blocks feature work immediately after resolution

______________________________________________________________________

## Step 5: Mitigation Decision Matrix

| Signal | Preferred mitigation | Notes |
|--------|---------------------|-------|
| Recent deploy caused regression | **Rollback** | First choice — fast and reversible |
| Config or feature flag change | **Revert config / disable flag** | Faster than code rollback |
| Traffic spike causing saturation | **Scale up** | Temporary; address root cause after |
| Memory leak or resource exhaustion | **Restart + scale + investigate** | Don't just restart without investigating |
| Data corruption or bad state | **Feature flag off + halt writes** | Never patch data mid-incident |
| Dependency outage (third party) | **Circuit breaker / fallback** | Escalate to vendor; communicate ETA |
| ES cluster yellow/red | **Do not write, do not index** | Check shard allocation first |
| Sidekiq queue growth | **Pause non-critical queues, scale workers** | Identify job causing backup first |

______________________________________________________________________

## Step 6: Timeline Format

Record every action during the incident:

```
HH:MM UTC | [Action taken] | [Owner]
```

Example:

```
14:32 UTC | Incident declared SEV2, IC assigned | @alice
14:35 UTC | Identified spike in 5xx errors on /api/sequences endpoint | @bob
14:38 UTC | Correlated with 14:20 deploy of sequences-service v2.3.1 | @bob
14:41 UTC | Initiated rollback to v2.3.0 | @alice
14:49 UTC | Rollback complete, error rate returning to baseline | @alice
14:55 UTC | Confirmed recovery, monitoring for 15 min | @alice
15:12 UTC | Incident resolved, SEV2 downgraded, postmortem scheduled | @alice
```

______________________________________________________________________

## Step 7: Follow-Up Categorization

Every incident generates follow-ups. Categorize each:

| Category | Description | Example |
|----------|-------------|---------|
| **Toil** | Manual work that should be automated | "Manually checked queue depth 8 times" |
| **Bug** | Code defect that caused or contributed to incident | "Nil pointer in sequence job retry logic" |
| **Infra** | Infrastructure gap (capacity, config, topology) | "No HPA on sequences-service" |
| **Process** | Gap in runbook, communication, or process | "No runbook for ES yellow state" |

Action items must have: description, owner, due date, and category.
