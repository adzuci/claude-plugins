# Scenario: Secondary replication lag from a slow query

- **SEV:** 2
- **Source:** Generic MongoDB replication failure mode (no specific Apollo RCA).
- **Prevention guardrail:** read-preference review; index coverage on heavy reads.

## Inject (show this first)

```
[FIRING:1] MongoDB replication lag high [Infra] data-cluster-1 (devops)
Value: secondary_repl_lag=210s and climbing
Users report "I saved it but it's not showing up."
```

## Symptom layers (reveal one at a time)

1. **Stale reads:** users see stale data — writes succeed but reads (served from
   secondaries) lag behind. Replication lag is 200s+ and climbing on one secondary.
1. **A secondary is pinned:** the lagging secondary's CPU/IO is saturated; it can't apply
   oplog entries fast enough because it's also serving heavy read traffic.
1. **The heavy read:** a new report/export query (or a `read_preference: secondary`
   workload) is scanning large ranges on that secondary, starving oplog application.

## Red herrings

- "Writes are failing." (Writes are fine on the primary; the lag is on apply, not write.)
- "Network partition." (Heartbeats are fine; the secondary is CPU/IO-bound, not cut off.)
- "Add a secondary." (Helps capacity later, but won't drain the current backlog fast.)

## Discriminating question

"Is the lagging secondary also serving heavy reads?" Lag that tracks read load on a
specific secondary = read/replication contention, not a network or write problem.

## Expected diagnosis path

Stale reads + rising lag on one secondary → that secondary is IO/CPU-bound → a heavy
secondary-preference read is starving oplog application.

## Correct mitigation (reversible-first) + rollback

1. **Shed the heavy read:** route the report/export to the primary or an analytics node,
   or pause it (reversible). The secondary catches up.
1. **Verify:** lag drains toward zero; stale-read reports stop.
1. **Then** out of incident: add covering indexes for the heavy read, or move analytics
   workloads off the serving replica set.

**Rollback:** re-pointing the read back at the busy secondary re-creates the lag.

## Debrief questions

- Why does a read workload cause *write*-visible staleness? (Oplog apply competes with reads.)
- When is `read_preference: secondary` a trap?
- What lag threshold should page, and how does it map to user-visible staleness?
