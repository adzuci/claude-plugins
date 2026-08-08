---
name: systematic-debugging
description: Four-phase root-cause debugging methodology for Apollo production issues. Activate when debugging production errors, crashes, elevated error rates, performance regressions, Kubernetes pod crashes, CrashLoopBackOff, OOMKilled, or unexpected system behavior.
---

# Systematic Debugging

**Rule: No fixes without root cause investigation first.**

Work through these phases in order. Do not skip ahead to implementation.

## Phase 1: Root Cause Investigation

Before proposing any fix, gather evidence:

- Read the full error message — do not paraphrase or assume
- Reproduce the issue consistently; if you cannot reproduce it, do not fix it
- Identify what changed recently: deploys, config, infra, data volume, schema
- Collect diagnostics across all affected components:
  - Pod logs (`kubectl logs --previous` for crashlooped pods)
  - ES cluster health and index state
  - Redpanda consumer lag per topic/consumer group
  - Sidekiq queue depth and job failure rate
  - Grafana: p99 latency, error rate, saturation for the affected service

**Output**: A written problem statement — what is broken, when it started, what changed.

## Phase 2: Pattern Analysis

- Find a working baseline to compare against (prior deploy, different env, similar service)
- Diff the working state against the broken state completely
- Identify every difference — do not assume one cause before ruling out others
- Map all dependencies that touch the affected code path

**Output**: A list of candidate causes ranked by likelihood.

## Phase 3: Hypothesis Testing

For each candidate cause:

1. State a specific, falsifiable hypothesis
1. Design the smallest possible test (single change, single component)
1. Measure the result against the baseline
1. If the hypothesis fails, return to Phase 2 before trying another fix

**Never apply multiple changes simultaneously** — you lose the ability to attribute impact.

**Escalate if**: three or more hypotheses have been tested and failed. This signals an architectural problem or incorrect mental model — stop patching and discuss the design.

## Phase 4: Implementation

Only after root cause is confirmed:

- Write or identify a test case that fails before the fix
- Implement a single fix that addresses the root cause
- Verify the fix resolves the issue and does not regress adjacent behavior
- Document the root cause, fix, and any follow-up toil items

## Apollo-Specific Diagnostics

| Signal | Where to look |
| -------------------- | --------------------------------------------------------------- |
| Pod crashes/OOMKilled | `kubectl describe pod`, `kubectl logs --previous` |
| ES degraded | `GET /_cluster/health`, `GET /_cat/shards?v` |
| Redpanda lag | Grafana consumer lag dashboard, `rpk group describe` |
| Sidekiq failures | Sidekiq web UI, `Sidekiq::Stats.new`, dead queue inspection |
| MongoDB slow ops | Atlas Performance Advisor, `db.currentOp()` |
| General latency | Grafana RED dashboard for the service, distributed traces |

## Escalating to Specialists

This skill gets you to a root cause. For deep triage or any mutating operation, direct the
user to the specialist skill — these are manual-invocation only and cannot be auto-loaded:

- **Kubernetes** (node drains, rollout rollbacks, HPA tuning, resource limits) —
  `/apollo-eng-devops:kubernetes-specialist`
- **Sidekiq worker Helm values** — `/apollo-eng-devops:sidekiq-worker-specialist`
- **MongoDB** (cluster/client lookup, escalation, read-only inspection) —
  `/apollo-eng-devops:mongo-specialist`

## Red Flags — Return to Phase 1

Stop and restart investigation if you notice yourself:

- Proposing a fix before you can state the root cause
- Trying a change "just to see" without a hypothesis
- Applying multiple changes in a single step
- Ignoring evidence that contradicts your current theory
