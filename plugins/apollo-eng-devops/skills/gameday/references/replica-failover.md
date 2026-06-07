# Scenario: Primary stepdown / election storm

- **SEV:** 2
- **Source:** Generic MongoDB replica-set failure mode (no specific Apollo RCA).
- **Prevention guardrail:** retry/timeout config review; connection-string `retryWrites`.

## Inject (show this first)

```
[FIRING:1] MongoDB write errors spiking [Infra] data-cluster-2 (devops)
Value: NotWritablePrimary / NotMasterErrors=812 in 2 min
Reads mostly OK; writes failing intermittently.
```

## Symptom layers (reveal one at a time)

1. **Write-only errors:** apps see `NotWritablePrimary` / `NotMaster` errors on writes;
   reads against secondaries still succeed. Errors come in bursts, then briefly clear.
1. **An election happened:** the replica set just held an election — the previous primary
   stepped down. Brief windows with **no primary** are when writes fail.
1. **Why it stepped down:** the old primary lost heartbeat (node pressure, network blip,
   or a maintenance event). The set re-elected, but the app's driver took time to discover
   the new primary, and writes weren't retried.

## Red herrings

- "The database is down." (It isn't — reads work; only the no-primary window hurts writes.)
- "Restart all app pods." (May help discovery but masks the real gap: no write retry.)
- "Failover the cluster manually again." (Another election makes it worse.)

## Discriminating question

"Did we lose the primary, and are our writes idempotent + retried?" An election is normal;
the incident is that the app didn't ride through it. Check `retryWrites=true` and that
write timeouts are longer than the election window.

## Expected diagnosis path

Write-only `NotWritablePrimary` errors in bursts → a recent election / stepdown → driver
slow to rediscover primary and no write retries.

## Correct mitigation (reversible-first) + rollback

1. **Confirm a healthy primary now** (`rs.status()`); if elections are still flapping,
   stabilize the unhealthy node (cordon/drain if it's node pressure).
1. **Verify writes recover** once a stable primary is elected and discovered.
1. **Then** out of incident: ensure `retryWrites=true`, tune server-selection/write
   timeouts to exceed normal election time, make the failing writes idempotent.

**Rollback:** none destructive here; avoid manual stepdowns during recovery.

## Debrief questions

- Elections are expected. What makes them invisible to users vs. an incident?
- What is our server-selection timeout, and is it longer than a typical election?
- Which writes in the failing path are not idempotent / not retried?
