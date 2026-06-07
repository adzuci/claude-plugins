# Scenario: Driver connection pool exhaustion

- **SEV:** 2
- **Source:** Generic MongoDB driver failure mode (no specific Apollo RCA).
- **Prevention guardrail:** pool-size vs. concurrency review; slow-query budget.

## Inject (show this first)

```
[FIRING:1] App timeouts waiting on MongoDB [Engagement] Sequences (devops)
Value: timeout_waiting_for_connection=2.1k/min, p99_checkout_ms=9800
Mongo server CPU and disk look normal.
```

## Symptom layers (reveal one at a time)

1. **Client-side waits:** apps log "timed out waiting for a connection from the pool" /
   `waitQueueTimeoutMS` exceeded. The **server** looks healthy — CPU, disk, and its own
   op latency are normal. The pain is in the client.
1. **Connections all busy:** the driver's pool is at max; checkout wait time is seconds.
   Sidekiq concurrency was recently raised (or a new worker fleet deployed) without
   raising `maxPoolSize`.
1. **One slow query holds connections:** a moderately slow query (300–800ms) is run at
   high concurrency, so every pooled connection is occupied long enough to starve the rest.

## Red herrings

- "Mongo is overloaded — scale the cluster." (Server is fine; the bottleneck is the pool.)
- "Network latency to Mongo." (Round-trips are normal; checkout wait is the signal.)
- "Add more app pods." (More pods × same per-pod pool can make total connections worse.)

## Discriminating question

"Is the wait on the **client pool** or on the **server**?" Pool-checkout timeouts with a
healthy server = pool exhaustion, not a database problem. Compare active connections vs.
`maxPoolSize` and worker concurrency.

## Expected diagnosis path

Client checkout timeouts + healthy server → pool at max → concurrency outgrew pool size,
amplified by a slow query holding connections.

## Correct mitigation (reversible-first) + rollback

1. **Relieve concurrency:** reduce Sidekiq concurrency / scale down the offending worker
   fleet (reversible) so demand fits the pool.
1. **Verify:** checkout waits drop, timeouts clear.
1. **Then** out of incident: right-size `maxPoolSize` for the concurrency, and fix or
   index the slow query so connections free up faster.

**Rollback:** restoring the old concurrency is the rollback for step 1.

## Debrief questions

- What's the relationship between worker concurrency, pod count, and total Mongo connections?
- Why can a *non-slow* server still produce app timeouts?
- What dashboard panel would have shown pool saturation before the page?
