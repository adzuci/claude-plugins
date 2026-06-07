# Scenario: `.hint()` on a `.or()` query → full collection scan

- **SEV:** 1
- **Source:** [RCA: INCIDENT-24318 SEV-1 Application Latency](https://www.notion.so/2daab2b3b49680ca93b0c9c0acd92133) (PR #76873, Dec 2025). TTM 34 min.
- **Prevention guardrail:** `mongo-pr-guard` Check 2 (`.hint()` on a chain containing `.or()`).

## Inject (show this first)

```
[FIRING:1] High application latency [Growth] Layouts (p99 page load 8.1s)
Value: p99_ms=8124, baseline=420
Started ~6 min after the 14:30 deploy.
```

## Symptom layers (reveal one at a time)

1. **Latency, not errors:** page loads are slow (p99 8s vs 420ms baseline) but not
   erroring. CPU on the Mongo primary is elevated. Throughput of a specific query is up.
1. **Query profile:** `db.currentOp()` / profiler shows one query doing `COLLSCAN` —
   examining millions of docs per call — on every page load. It runs against the layouts
   collection.
1. **Recent change:** the 14:30 deploy included PR #76873, which added
   `.hint(team_id: 'hashed')` to a query in `OverviewLayoutService.get_layouts()`. The
   query uses `.or(...)`, and one `.or()` branch is `{ owner_id: user.id }` — no
   `team_id` field.

## Red herrings

- "Traffic spike — autoscale the app." (RPS is normal; per-query cost exploded.)
- "Mongo needs more memory / a bigger primary." (Treats the symptom; the plan is wrong.)
- "Add an index on `owner_id`." (Plausible later, but the hint is forcing the wrong plan
  *now*; the fastest safe fix is to remove the hint.)

## Discriminating question

"Does every branch of the `.or()` contain the hinted field?" The hint pins an index that
one branch can't use, so Mongo falls back to a full collection scan for that branch on
every call. (The existing static analyzer skips `.or()` chains — it will not catch this.)

## Expected diagnosis path

Latency spiked right after a deploy → one query is doing a COLLSCAN → the query has a
`.hint()` forced onto an `.or()` whose branches don't all share the hinted field.

## Correct mitigation (reversible-first) + rollback

1. **Roll back the deploy** (or revert PR #76873). Fastest reversible fix — restores the
   prior, correct query plan immediately.
1. **Verify:** COLLSCAN disappears, p99 returns to baseline.
1. **Then** out of incident: remove the `.hint()` from the `.or()` query (let Mongo plan
   it), or split into two queries, or confirm every `.or()` branch carries the hinted field.

**Rollback:** re-deploying the unfixed code reproduces the COLLSCAN.

## Debrief questions

- Why didn't the static analyzer catch this? (It defines `.or` as a criteria-changer and
  skips those chains.)
- A hint is a promise that an index applies. When is that promise unsafe?
- Which `mongo-pr-guard` check closes this gap, and what does it look for?
