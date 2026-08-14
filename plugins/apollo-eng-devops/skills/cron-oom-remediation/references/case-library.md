# Cron OOM case library

Corpus: every Jira ticket titled `Cron OOM Killed [Infra] Kubernetes (…)` — **173 alert tickets
across 36 distinct crons**, 2025-10-15 → 2026-08-08, plus the pre-alert IE-5199/IE-5200 pair.
Ticket noise is high: the modal cron fires 5–19 tickets for one underlying cause, and 89 of the
173 carry no human comment at all — 82 of those closed `Duplicate` or `Canceled`. Resolutions
across the corpus: 65 Duplicate, 49 Canceled, 45 Done, 5 Won't Do, 5 False positive. Read this
table before opening a new investigation; a large share of "new" alerts are a cron already in it.

## Merged fixes, by class

| cron | PR | class | what changed |
|---|---|---|---|
| `hubspot-setup` | [#70178](https://github.com/apolloio/leadgenie/pull/70178) | project | `Team.where(...).each` → `.only([:hubspot_job_sync_statuses, :hubspot_linked_at, :domain, :cached_current_arr]).each` |
| `preverified-emails` | [#87364](https://github.com/apolloio/leadgenie/pull/87364) | chunk | `enqueue_jobs` (~5M args built in memory) → `unsafe_fast_enqueue_jobs`, batches of 1000 |
| `hubspot-sync-updates-*` | [#93851](https://github.com/apolloio/leadgenie/pull/93851) | chunk | flush `WorkerHelper::Enqueue.bulk` every 1000 args instead of once at the end |
| `hubspot-sync-updates-*` | [#94037](https://github.com/apolloio/leadgenie/pull/94037) | limit | 4Gi — needed *because* #93851 alone was insufficient |
| `kill-slow-queries-noncustomer` | [#95220](https://github.com/apolloio/leadgenie/pull/95220) | limit | bump — **recurred**, see #97642 |
| `heaviest-gmail-senders` | [#95321](https://github.com/apolloio/leadgenie/pull/95321) | project + limit | `batch_load(Team, ids)` → field list; pre-loads `master_team` targets so `Team#status` can't lazy-load full docs |
| `calculate-bounces-{team,user}` | [#96690](https://github.com/apolloio/leadgenie/pull/96690) | stream + chunk | `pluck(:id).map` → `.only(:id).batch_size(1000).each_slice(1000)` + bulk enqueue per slice; staggered the two schedules |
| `kill-slow-queries-contacts` | [#97141](https://github.com/apolloio/leadgenie/pull/97141) | upstream | killed the *input*: made enrichment team discovery a covered `DISTINCT_SCAN`, ending the kill-storm the killer pod was serializing |
| `search-person-title-normalization` | [#97179](https://github.com/apolloio/leadgenie/pull/97179) | two-phase | `.limit(10_000).to_a` → `pluck(:id)` then `each_slice(500)` re-query. No limit bump; still on the 2.5Gi default |
| `liveintent-file-ingestor` | [#97484](https://github.com/apolloio/leadgenie/pull/97484) | limit | 2Gi → 4Gi |
| `kill-slow-queries-noncustomer` | [#97642](https://github.com/apolloio/leadgenie/pull/97642) | trim + limit | stopped materialising huge command docs; 8Gi |
| `check-flagged-routables`, `auto-archive-sequences` | [#99366](https://github.com/apolloio/leadgenie/pull/99366) | limit | per-cron 4Gi |
| `(fleet default)` | [#99496](https://github.com/apolloio/leadgenie/pull/99496) | limit | default 2Gi → 2.5Gi |
| `salesforce-sync-updates-high-backlog` | [#99589](https://github.com/apolloio/leadgenie/pull/99589) | limit | 4Gi |
| `deactivate-inactive-voice` | [#99595](https://github.com/apolloio/leadgenie/pull/99595) | project | `batch_load(User, ids)` → `(User, ids, :id, [:team_id, :deleted])`; loop read exactly those two fields off ~28 KB docs |
| `email-tracking-check-creating-routables` | [#99746](https://github.com/apolloio/leadgenie/pull/99746) | limit | 5Gi |
| `self-service-cleanup-accounts` | [#99903](https://github.com/apolloio/leadgenie/pull/99903) | stream | `Team.where(...).to_a` (×2 passes) → `.only(PLATFORM_ACCESS_FIELDS + [:root_domain]).batch_size(1000).no_timeout.each` with id/domain accumulators |
| `email-directory` | [#91652](https://github.com/apolloio/leadgenie/pull/91652) (closed) | architectural | split the Microsoft directory scrape into its own worker + cron. The mid-term answer for any cron doing real work inline |

Split: **7 limit-only, 10 code, 1 architectural.** Both classes are common; neither is the
default answer.

## Effect of each fix

Kills are `sum(increase(kube_events_tracker_oomkilled_total[1h]))` summed over range and divided
by 3. Post-window starts at merge + 2h (deploy lag) and runs to min(+30d, today).

| cron | fix | kills 14d before | kills after | window |
|---|---|---|---|---|
| `check-flagged-routables` | limit #99366 | 30 | 0 | 7.7d |
| `auto-archive-sequences` | limit #99366 | 7 | 0 | 7.7d |
| `liveintent-file-ingestor` | limit #97484 | 6 | 0 | 24.0d |
| `salesforce-sync-updates-high-backlog` | limit #99589 | 7 | 0 | 5.9d |
| `email-tracking-check-creating-routables` | limit #99746 | 16 | 0 | 5.1d |
| `kill-slow-queries-noncustomer` | limit #95220 | 1 | **4** | 30.0d |
| `hubspot-sync-updates-2` | code #93851 | 1 | **1** | 30.0d |
| `hubspot-sync-updates-2` | limit #94037 (after code) | 2 | 0 | 30.0d |
| `deactivate-inactive-voice` | project #99595 | 1 | 0 | 6.4d |
| `self-service-cleanup-accounts` | stream #99903 | 87 | 0 | 2.3d |
| `search-person-title-normalization` | chunk #97179 | 73 | 0 | 24.0d |
| `calculate-bounces-team` | stream #96690 | 11 | 0 | 30.0d |
| `calculate-bounces-user` | stream #96690 | 13 | 0 | 30.0d |
| `preverified-emails` | chunk #87364 | 15 | 0 | 30.0d |
| `kill-slow-queries-noncustomer` | trim+limit #97642 | 1 | 0 | 22.8d |
| `heaviest-gmail-senders` | project+limit #95321 | 4 | 0 | 30.0d |
| `hubspot-setup` | project #70178 | 11 | 0 | 30.0d |

The two non-zero rows are the argument for Step 3: #95220 raised a limit on a workload-driven
cron and bought 25 days; #93851 fixed the code on a cron that *also* needed headroom. Sizing the
population first tells you which of those you are in.

## Censoring evidence (Step 1 of SKILL.md)

Peak RSS in the 72–96h before each fix, against the limit in force at the time:

| cron | peak MB | limit MB | peak/limit | truth |
|---|---|---|---|---|
| `self-service-cleanup-accounts` | 15350 | 15360 | 1.00 | code |
| `search-person-title-normalization` | 2043 | 2048 | 1.00 | code |
| `preverified-emails` | 2045 | 2048 | 1.00 | code |
| `promos-completion-process` | 2041 | 2048 | 1.00 | code |
| `deactivate-inactive-voice` | 4066 | 4096 | 0.99 | code |
| `auto-archive-sequences` | 2035 | 2048 | 0.99 | **limit** |
| `calculate-bounces-team` | 2023 | 2048 | 0.99 | code |
| `calculate-bounces-user` | 2035 | 2048 | 0.99 | code |
| `hubspot-sync-updates-2` | 2033 | 2048 | 0.99 | code |
| `crm-configuration-sync` | 2024 | 2048 | 0.99 | code |
| `team-deactivate-duplicate-crm` | 2011 | 2048 | 0.98 | code |
| `notification-push-new-ui` | 2004 | 2048 | 0.98 | — |
| `liveintent-file-ingestor` | 1984 | 2048 | 0.97 | **limit** |
| `heaviest-gmail-senders` | 1965 | 2048 | 0.96 | code |
| `nylas-cleanup-accounts` | 1841 | 2048 | 0.90 | — |
| `email-tracking-check-creating-routables` | 2931 | 5120 | 0.57 | **limit** |
| `salesforce-sync-updates-high-backlog` | 2116 | 4096 | 0.52 | **limit** |
| `check-flagged-routables` | 2045 | 4096 | 0.50 | **limit** |
| `kill-slow-queries-noncustomer` | 5277 | 8192 | 0.64 | code |

All four rows below 0.7 are sampling a window that already contains the limit bump, so even the
apparent headroom there is an artifact of remediation history rather than a reading of demand.

## Fleet baseline (2026-08-12)

`max by (container)(max_over_time(container_memory_working_set_bytes{container=~"cron-.*"}[24h]))`,
403 containers:

```
p1   371 MB    p25 1657 MB    p75 1786 MB    p95 2161 MB
p5   754 MB    p50 1769 MB    p90 1993 MB    p99 2684 MB
p10 1005 MB                                  max 3435 MB
```

Split by sample count: **351 crons got more than one cadvisor scrape** (median peak 1,772 MB,
245 of them inside 1,650–1,900 MB — that plateau is the Rails boot cost, not workload), and
**52 got exactly one scrape** (peaks 264–1,397 MB, every one of them under 1,400 MB). Only 9 of
the 351 multi-sample crons read below 1,400 MB. A lone sample lands at a random point in the
boot ramp; it is not a peak.

Boot composition, from reproducing a prod cron boot locally (2026-08): gems 320 MB →
initializers +1,150 MB → `eager_load` +180 MB → YJIT +85 MB = **1,646 MB**, against a prod p50
peak of 1,666 MB at the time. It has since drifted to ~1,770 MB. Crons cross their ceiling one
at a time, fattest first — which is why an OOM wave arrives with no offending deploy.

## Structural notes

- 507 cron jobs; 68 carry an explicit memory override (3 × 2Gi, 2 × 2.5Gi, 10 × 3Gi, 24 × 4Gi,
  10 × 5Gi, 3 × 6Gi, 7 × 7Gi, 2 × 8Gi, 3 × 10Gi, and one each at 15/16/20/30Gi).
- Direct-invoke crons (`Orchestrator.instance.x`, `Model.class_method`) do their work in the cron
  pod and own its memory. Crons that only call `Worker.enqueue` hand the work to Sidekiq — their
  OOM is in the enqueue path, not the job.
- Proposed, not built: convert direct-invoke crons to enqueue-on-Sidekiq; boot diet (lazy Mongo
  clients, env-gated warmup initializers, `DISABLE_YJIT` for runners); a boot-RSS budget in CI.

## Non-OOM causes that arrive as OOM alerts

- **`activeDeadlineSeconds` SIGTERM** reads as a killed pod. INCIDENT-31077
  (`cron-liveintent-file-ingestor`) was a 300s deadline against a 5-minute enqueue of 86k GCS
  files on a cold node — diagnosed from logs showing SIGTERM, fixed by raising the deadline, not
  memory. Check the termination reason before assuming OOM.
- **Auto-resolved flaps.** A large share of the corpus (`cron-billing-daily-cost`,
  `cron-heaviest-gmail-senders`, `cron-diamond-data`, `cron-email-directory`) auto-resolved in
  PagerDuty within 5–10 minutes and closed with no action. Confirm the alert is still firing
  before doing any of this.
- **Dead crons.** `cron-heaviest-gmail-senders` was flagged for deletion in June 2026 as no
  longer used. Deleting the job is a legitimate remediation.
