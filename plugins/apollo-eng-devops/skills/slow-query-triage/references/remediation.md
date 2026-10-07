# Slow Query Remediation — The Ladder

The fix menu behind the ranked recommendations in the digest. The script emits only the tiers whose preconditions hold; this file explains each one, what it costs, and when it is the wrong answer.

**Order matters.** Tiers are cheapest-and-most-reversible first. A guardrail that stops the page today buys the time to do the structural fix properly. Skipping to a reshard because the graph looked bad is how a slow query becomes a quarter of work.

## 0 · Stop the bleeding (minutes)

| Action | When | Trade-off |
| --- | --- | --- |
| `maxTimeMS` on the query path, below the Query Killer threshold | Always applicable | The op self-cancels with a catchable error instead of running long enough to page. You must handle the error — a bare timeout is a 500 unless the caller degrades gracefully |
| Route or silence the alert for a non-paging origin | Origin is `manual-console` or `scheduled` | Only after confirming the origin. Silencing a `user-request` page hides customer pain |

`maxTimeMS` is the single most under-used lever. It converts "unbounded op that pages on-call" into "bounded failure the application owns", without touching the data model.

## 1 · Query shape (hours)

| Action | When | Trade-off |
| --- | --- | --- |
| Add the shard key to the filter | Confirmed shard key absent from filter, fan-out `proven` or `likely` | The highest-leverage change available: N-shard fan-out becomes a 1-shard read. Requires the caller to *know* the shard key — sometimes a real API change |
| Chunk a large `$in` | `$in` list >25 elements | More round trips, each cheap and cacheable. Watch for N+1 |
| Drop index-hostile predicates (`$ne`, `$nin`, unanchored regex, `$where`) | Present in the filter | Usually needs a modelling change (a boolean flag instead of a negation) |
| Project only needed fields | Large documents | Cuts network and deserialization, not index work. Rarely the main win alone |

If the collection is sharded and the filter cannot include the shard key, that is a **data-model finding**, not a query bug — escalate it to tier 4 rather than pretending an index will fix it.

## 2 · Indexing (hours to days)

| Action | When | Trade-off |
| --- | --- | --- |
| Add an index | `plan_summary` shows `COLLSCAN` | Use `apollo-eng-devops:create-mongo-index`. Every index costs write throughput and RAM |
| Extend an existing index to be shard-key-prefixed | `IXSCAN` present and fan-out proven | Lets Mongos target. Prefer extending over adding — index count is a budget |
| Partial or sparse index | Predicate selects a small, stable subset | Cheaper to maintain; only used when the query matches the filter expression exactly |
| Covering index | Query reads few fields | Avoids document fetches entirely |

**Do not add another index on the filter field when the plan is already an `IXSCAN` and the op is fanning out.** Each shard is already using an index and each shard is still slow — the cost is routing, not lookup. Another index adds write amplification and changes nothing.

## 3 · Access pattern (days)

| Action | When | Trade-off |
| --- | --- | --- |
| Paginate / `limit` | Unbounded result sets | Changes the API contract |
| Move off the request path (async + poll, or a job) | Origin is `user-request` and the read is inherently multi-second | Best UX fix for a read that cannot be made fast; adds a job and a status surface |
| Batch at the caller | Origin is `background-job` and the query runs per item | Fewer, larger ops; watch memory |
| Read from a secondary | Analytics, backfills, exports | Stale reads. Never for read-your-writes paths |
| Off-peak scheduling | Origin is `scheduled` | Does not make it faster; stops it competing with user traffic |

## 4 · Architecture (weeks)

| Action | When | Trade-off |
| --- | --- | --- |
| Precompute / cache the aggregate | Recurring or fleet-wide | Removes the query rather than tuning it. Invalidation is the real cost |
| Denormalize a counter or rollup | The query exists only to count or sum | Write-path complexity and drift risk |
| Archive cold data | Collection growth is the driver | Big, durable win; needs a retention decision from the data owner |
| Reshard the collection | The shard key is wrong for the dominant access pattern | **Last resort.** Expensive, risky, and needs a DBA. Justify it with more than one incident |

## 5 · Process and guardrails (ongoing)

| Action | When | Trade-off |
| --- | --- | --- |
| Backfill runbook: `maxTimeMS`, batch size, secondary read preference, off-peak | Origin is `manual-console` | The cheapest durable fix for hand-run ops. Costs nothing but discipline |
| Exclude manual origins from the paging lane | Manual ops are paging on-call | Requires the origin signal to be reliable — check the confidence first |
| Alert threshold review | The threshold pages before customers notice | Do not raise a threshold to hide a real regression |
| Add the pattern to the playbook | Any novel finding | Turns one investigation into a faster next one |

## Choosing, by origin

| Origin | Start at | Usually wrong |
| --- | --- | --- |
| `user-request` | 0 (`maxTimeMS`) → 1 (query shape) → 3 (off the request path) | Jumping to a reshard; adding an index that duplicates an existing `IXSCAN` |
| `background-job` | 0 → 3 (batching, concurrency) | Treating it as customer-facing latency |
| `scheduled` | 3 (off-peak, chunking) → 4 (precompute) | Paging a human at all |
| `manual-console` | 5 (runbook) → 0 (alert routing) | Opening a code bug against the controller |

## Choosing, by evidence strength

- **Fan-out `proven` + confirmed shard key** — tier 1 shard-key fix is justified; write the ticket.
- **Fan-out `proven`, shard key unconfirmed** — confirm the key first. Every tier below branches on it.
- **Fan-out `likely`** — gather one more incident before committing engineering time; ship the tier 0 guardrail now.
- **`single-shard`** — this is not a routing problem. Look at document size, plan, working set, and volume.
- **`deploy-correlated`** — read the diff before designing anything. A revert is a legitimate fix and often the fastest one.
