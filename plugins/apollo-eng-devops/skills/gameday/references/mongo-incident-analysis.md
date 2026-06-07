# Apollo MongoDB Incident Analysis

A synthesis of Apollo's documented MongoDB production incidents. This is the source
material the gameday scenario cards distill into drills, and a shareable narrative for
on-call onboarding. It is intentionally pattern-focused: the goal is to recognize the
*shape* of these failures early, not to memorize specifics.

> Built from the RCAs catalogued in the `apollo-eng:mongo-pr-guard` skill. Each incident
> there maps to a pre-merge guardrail; this doc maps the same incidents to *response*
> muscle. Read both: prevention (mongo-pr-guard) and response (gameday) are two halves.

______________________________________________________________________

## Timeline

| Date | Incident | SEV | TTM | Root cause | RCA |
| --- | --- | --- | --- | --- | --- |
| Mar 2026 | email-3 shard outage (IpHem, PR #84485) | 1 | 122 min | Bulk 99M-record ingest into a collection declared `shard_key` but never migrated → all writes on one shard → disk throughput hit 1,200 MB/s | [RCA](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1) |
| Mar 2026 | email-3 misrouting (IpHem `mongoid.yml`) | 1 | — | `store_in client: 'performance_insensitive_noncustomer_data'` actually routed through the shared email-3 shard serving 100+ services | [RCA](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1) |
| Dec 2025 | INCIDENT-24318 application latency (PR #76873) | 1 | 34 min | `.hint(team_id: 'hashed')` on a `.or()` query whose `{ owner_id: … }` branch lacked `team_id` → full collection scan on every page load | [RCA](https://www.notion.so/2daab2b3b49680ca93b0c9c0acd92133) |
| Nov 2025 | SEV-0 app.apollo.io outage (node pool migration) | 0 | — | Misconfigured firewall rules across 19 Terraform workspaces; new node-pool CIDR missing from Redis Rate Limiter rules (infra-adjacent, surfaced alongside the Mongo routing work) | [RCA](https://www.notion.so/2abab2b3b496806f9cebc5cf763ff891) |

______________________________________________________________________

## Cross-cutting themes

1. **A `shard_key` declaration is not sharding.** Declaring `shard_key` in a Mongoid model
   does nothing until `MongoUtil.shard_collection` runs in production. The gap between
   "looks sharded" and "is sharded" caused the largest outage. Always confirm via
   `sh.status()`, never the model.

1. **`mongoid.yml` client names lie.** Names like
   `performance_insensitive_noncustomer_data` describe *intent*, not the physical cluster.
   The same name routed "low-priority" writes onto the shard serving 100+ customer-facing
   services. Read what a client maps to; count how many models share it.

1. **Alerting fired at the wall, not with runway.** Disk write throughput sat at 70%+ for
   **two weeks** before the page. The first alert was at the hard limit. The document-count
   alarm was set at 100M when the cheap action point was **10M**. Leading indicators
   (burn warnings, trend/forecast alerts) were missing.

1. **Query-planner traps hide behind hints.** A `.hint()` is a promise that an index
   applies to the query. On an `.or()` whose branches don't all carry the hinted field,
   that promise breaks and Mongo falls back to a COLLSCAN. The static analyzer explicitly
   skips `.or()` chains, so this class needs a dedicated check.

1. **Blast radius is a shared-resource problem.** The worst incidents weren't contained to
   one feature — a single hot collection or misrouted writer took down 100+ services
   sharing a shard. Broad, owner-less error patterns point at a shared resource (a shard,
   a cluster, a client), not a single feature.

______________________________________________________________________

## Detection gaps (what was missing)

- No **warning** threshold on Mongo disk write throughput (only a limit-level page).
- No **trend/forecast** alert ("disk throughput will hit limit in N days").
- No **per-collection document-count** alert at the 10M action threshold.
- No pre-merge check linking a `shard_key` declaration to a migration call.
- No pre-merge check for `.hint()` + `.or()` collisions (analyzer skipped them).
- No review gate forcing a `mongoid.yml` client change to be traced to its real cluster.

______________________________________________________________________

## Prevention → guardrail mapping

| Theme | Pre-merge guardrail (`mongo-pr-guard`) | Response drill (`gameday`) |
| --- | --- | --- |
| Declared-but-unsharded | Check 1 (shard key, no migration) | `unsharded-hotspot` |
| Bulk write to unsharded collection | Check 4 | `unsharded-hotspot` |
| Misleading `mongoid.yml` client | Check 3 | `mongoid-misroute` |
| `.hint()` on `.or()` | Check 2 | `hint-or-fullscan` |
| New model, no shard key, quiet growth | Check 5 | `disk-saturation` |
| Late/limit-only alerting | (observability, not a PR check) | `disk-saturation` |

______________________________________________________________________

## How to use this for on-call upskilling

1. Read this doc once for the pattern vocabulary.
1. Run the three Apollo-real gameday cards (`unsharded-hotspot`, `hint-or-fullscan`,
   `mongoid-misroute`) tabletop, solo.
1. Run them again **with a senior engineer** facilitating — they'll inject variations and
   surface incidents not yet written up here. Add new cards from what they teach.
1. Add the generic cards (`replica-failover`, `connection-pool-exhaustion`,
   `slow-query-oplog-lag`) to round out failure-mode coverage beyond sharding.
