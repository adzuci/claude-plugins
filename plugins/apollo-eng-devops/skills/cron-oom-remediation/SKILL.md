---
name: cron-oom-remediation
description: Diagnose a Kubernetes cron OOMKilled alert in leadgenie and ship the right fix — a memory-limit bump or a code change (streaming / projection / chunking). Use when a "Cron OOM Killed" alert or INCIDENT ticket lands.
argument-hint: cron deployment name or INCIDENT key (e.g. cron-deactivate-inactive-voice, INCIDENT-32102)
disable-model-invocation: true
---

# Cron OOM Remediation

[OOMKilled runbook](https://app.notion.com/p/apolloio/Runbook-for-Resolving-OOM-Killed-Event-29aab2b3b496807d8522c932dd928c15) · [INFRA-2077](https://apollopde.atlassian.net/browse/INFRA-2077) · covers `cron-*` jobs in `kubernetes/production/cron/values.yaml`

Every cron OOM is one fork: **raise the limit, or change the code.** Neither obvious signal
decides it. The killed run's peak always reads ~100% of the limit — it is censored, and 14 of 19
historically-fixed crons sat at 0.96–1.00 across *both* answers. Grepping for `.to_a` doesn't
decide it either; both crons correctly fixed by a bump have one, over 72 documents and ~8 MB.

**Count the population in prod. That is the decision.** Everything below serves that.

## 1. Confirm

```promql
# kills — range query at 1h step, sum the buckets, divide by 3
sum(increase(kube_events_tracker_oomkilled_total{deployment="cron-<name>"}[1h]))
max_over_time(kube_pod_container_resource_limits{resource="memory",container="cron-<name>"}[7d]) / 1048576
```

Still firing? Many of these auto-resolve in minutes. Get the current limit and the job's
`values.yaml` entry. A first kill with no deploy behind it means a population grew into the
ceiling.

## 2. Read the code

`command:` in `values.yaml` is a literal Ruby entry point. Find what it materializes — `.to_a`,
`.each` on an unbounded criteria, `pluck(:id).map`, `batch_load(Model, ids)` with no field list,
`enqueue_jobs` — and note **which fields the loop body actually reads**.

A cron that only calls `Worker.enqueue` hands the work to Sidekiq; its OOM is in the enqueue path.

## 3. Count it in prod

Read-only. Every probe here is a count, a projection, or an RSS measurement — never call a model
method that writes, enqueues, or hits a vendor API.

```bash
eval "$(grep -E '^export MONGO_(USER|PASS)=' ~/.zshrc)"
HIDDEN_MONGO=true MONGO_ROOT_USER=$MONGO_USER MONGO_ROOT_PASSWORD=$MONGO_PASS \
  NEW_RELIC_AGENT_ENABLED=false SKIP_COVERAGE=1 bundle exec rails runner -e staging /tmp/probe.rb
```

Measure RSS around the load, not BSON — BSON understates it ~4× (`GC.start` then
`` `ps -o rss= -p #{Process.pid}` ``, before and after, twice).

Every cron pod boots the full Rails monolith at **~1,770 MB** against a **2.5Gi** default limit.
So:

- **workload ≲ 200 MB → bump the limit.** That is the whole fix. The kills are boot plus
  run-to-run variance clipping the ceiling.
- **bigger, or the population is growing → change the code.** A bump recurs — #95220 bought 25
  days on a workload-driven cron before it came back.

Re-read the baseline instead of trusting the number; it creeps as the repo grows:
`quantile(0.5, max by (container)(max_over_time(container_memory_working_set_bytes{container=~"cron-.*"}[24h])))`

## 4. Fix

`.only()` is the instinct and the weak choice: it cuts BSON 93% but RSS only 36%, because
Mongoid's per-document object cost dominates. Streaming cuts RSS ~95%.

| how the set is used | fix | template |
|---|---|---|
| iterated once; read-only, or writing fields the criteria doesn't filter on | **stream** — `.only(...).batch_size(1000).no_timeout.each`, accumulate ids/tallies only | #99903 |
| whole set must stay resident | **project** — `.only(...)`, `batch_load(Model, ids, :id, fields)` | #99595 |
| building Sidekiq args | **chunk** — `each_slice(1000)` + bulk enqueue per slice | #96690 |
| the loop mutates the field the criteria filters on | **two-phase** — `pluck(:id)`, then `each_slice(N)` and re-query | #97179 |

That last row is a correctness trap, not a style choice: `VoiceSetting.active` selects
`active: true` and the body sets it false, so a cursor would skip records. `.to_a` was
accidentally safe.

**Prove equivalence on real data, read-side only** — build both id sets (and any accumulator),
diff them, run nothing else. Never execute the mutating body: `VoiceSetting#deactivate`
deregisters CNAM through a vendor API, and pointing Mongo somewhere safe doesn't undo that.

## 5. Verify

Measure from **deploy time, not merge time**. Kills must be 0; report N clean runs, peak, limit,
headroom. If you shipped a code fix, check whether an earlier emergency bump can come back down.

## Gotchas

- The OOM tracker counts every kill **3×**. And `increase(...[30d])` silently drops kills on it —
  bucket at `[1h]` and sum. Selecting it raw errors; wrap in `sum()`.
- Labels differ: cadvisor `container=`, tracker `deployment=`, Loki `service_name=`. A `pod=~`
  matcher returns nothing and reads as "no kills".
- **One cadvisor sample is not a peak** — short pods often get one scrape, which lands mid-boot.
  Require ≥2.
- The kill lands *after* the work completes, and `backoffLimit: 1` means two kills per schedule
  slot is one failed run.
- Before crediting a default-limit bump, check the cron doesn't have its own override —
  INCIDENT-32102 was closed against a default bump that couldn't reach it.
- An `activeDeadlineSeconds` SIGTERM looks identical to an OOM.

## Output

A fix PR (bump with the sizing in a comment, or the smallest code diff plus a spec pinning the
batch size), the verification numbers, and triage fields for INFRA-2077: `cron`, `first_kill`,
`kills_per_day`, `limit_mb`, `peak_mb`, `verdict`, `population`, `estimated_mb`, `owner`,
`recommended_action`. Hand the text back — don't post to Jira or Slack.

`references/case-library.md` — 173 alerts, 36 crons, every merged fix and what it measured.
