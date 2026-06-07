# Scenario: `mongoid.yml` client name misroutes writes through a shared shard

- **SEV:** 1
- **Source:** [RCA: email-3 MongoDB Shard Outage](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1) (Mar 2026).
- **Prevention guardrail:** `mongo-pr-guard` Check 3 (`config/mongoid.yml` changed).

## Inject (show this first)

```
[FIRING:1] Elevated errors across multiple services [Infra] email-3 (high devops)
Value: error_rate=3.4%, affected_services=100+
No single feature owner is paging; symptoms are broad.
```

## Symptom layers (reveal one at a time)

1. **Broad, not narrow:** errors and latency span 100+ unrelated services that have one
   thing in common — they all use the `email-3` Mongo shard.
1. **A new heavy writer:** one model (`IpHem`) recently started writing a large volume.
   Its model declares `store_in client: 'performance_insensitive_noncustomer_data'` — a
   name that sounds like an isolated, low-priority cluster.
1. **The name lies:** in `config/mongoid.yml`, the client
   `performance_insensitive_noncustomer_data` actually resolves to the **email-3 shard**,
   not a separate data cluster. The "noncustomer / performance-insensitive" writes are
   landing on a shard that serves 100+ customer-facing services.

## Red herrings

- "email-3 hardware is failing." (Hardware is fine; it's being overloaded by a misrouted
  writer.)
- "The new writer's own feature is broken." (Its feature is fine; the *blast radius* is
  everyone else on email-3.)
- "DNS / connection issue." (Connectivity is fine; routing-by-name is the trap.)

## Discriminating question

"What physical cluster does this `mongoid.yml` client name actually point to?" Never trust
the client name's vibe — read the hosts/replica set it maps to and count how many models
`store_in` that same client.

## Expected diagnosis path

Broad cross-service errors on one shard → a new heavy writer pointed at a deceptively-named
client → that client resolves to the shared `email-3` shard.

## Correct mitigation (reversible-first) + rollback

1. **Stop the bleed:** pause the new writer (reversible) to relieve email-3.
1. **Verify:** cross-service errors clear.
1. **Then** out of incident: repoint `IpHem` to an appropriate isolated client/cluster,
   or shard it, and rename misleading clients so the next engineer isn't fooled.

**Rollback:** resuming the writer against the same client re-loads email-3.

## Debrief questions

- How should `mongoid.yml` client names be validated in review when they don't reflect the
  real cluster?
- What grep would tell you, before merge, how many models share a given client?
- Which `mongo-pr-guard` check fires on a `mongoid.yml` change, and what does it ask you
  to verify?
