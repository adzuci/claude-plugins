# Scenario: Unsharded collection hotspot

- **SEV:** 1
- **Source:** [RCA: email-3 MongoDB Shard Outage](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1) (PR #84485, Mar 2026). TTM 122 min.
- **Prevention guardrail:** `mongo-pr-guard` Check 1 (shard key declared, no migration call) and Check 4 (bulk write to unsharded collection).

## Inject (show this first)

```
[FIRING:1] High MongoDB disk write throughput [Infra] email-3 (high devops prod-app)
Value: write_MBps=1198 (limit 1200), p99_write_latency=4.2s
366K+ errors observed across dependent services in the last 5 min.
```

## Symptom layers (reveal one at a time)

1. **Disk + latency:** the `email-3` shard's disk write throughput is pinned at ~1,200
   MB/s (its hard limit). Write latency p99 has climbed from ~20ms to 4s. Only **one**
   shard is hot; the others are idle.
1. **Blast radius:** 100+ services that share `email-3` are throwing timeouts — this is
   not contained to one feature. Error rate is climbing, not flapping.
1. **Recent change:** a new bulk ingest job started ~50 min ago and has written ~80M of a
   planned 99M records into a recently-added collection (`IpHem`). The collection has a
   `shard_key ip_address: 'hashed'` declared in the model.

## Red herrings

- "It's a slow query — let's kill long-running ops." (The writes are the load, not reads.)
- "Scale up the shard / add disk." (Disk throughput is capped; you cannot scale out of a
  single-shard write storm mid-incident.)
- "Roll back the last app deploy." (The deploy is fine; the *job* is the load.)

## Discriminating question

"Is the collection actually sharded in production, or just declared sharded in the model?"
A `shard_key` in the model does **nothing** until `MongoUtil.shard_collection` is run.
Confirm via `sh.status()` / Rails console — the collection is unsharded, so every write
lands on the primary shard.

## Expected diagnosis path

Disk throughput pinned on one shard → all writes hitting one shard → collection declared
sharded but never migrated → bulk job is the write source.

## Correct mitigation (reversible-first) + rollback

1. **Stop the bleed:** pause/throttle the bulk ingest job (reversible — resume later).
   This immediately drops write load.
1. **Verify recovery:** disk throughput falls, dependent-service errors clear.
1. **Then** plan the real fix out of incident: shard the collection
   (`MongoUtil.shard_collection`) and re-run the ingest rate-limited (`WorkerHelper::Fraction`
   or batched sleeps, < 1M docs/hr).

**Rollback:** resuming the unthrottled job re-creates the incident — do not resume until
the collection is sharded.

## Debrief questions

- Why did a `shard_key` in the model not protect us? What step was missing?
- The disk had been at 70%+ for two weeks with no page. What alert should have existed?
- Which `mongo-pr-guard` check would have blocked PR #84485 pre-merge?
