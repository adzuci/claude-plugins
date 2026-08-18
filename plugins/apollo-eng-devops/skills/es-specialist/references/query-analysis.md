# Query Analysis: Classification, Attribution, and Fix Verification

How to turn raw slow-query captures into named causes and proven fixes. Distilled from the es8-main-v1 RCA.

______________________________________________________________________

## Slow-Task Classification

For every slow task captured from `GET /_tasks?actions=indices:data/read/search*&detailed=true`:

1. **Record**: running time, body size (bytes), leaf-clause count, indices targeted, `X-Opaque-Id`.
1. **Bucket by kind**: `plain` (no joins), `join` (Siren Federate clauses present), `knn` (vector search), `oversized` ("monster").
1. **Define the oversized class from the data**: sort bodies by size and look for the gap. es8-main-v1: monsters >80KB when the next-largest team peaked \<30KB. Do not hardcode the number for a different cluster — re-derive the gap.
1. **Produce a census per capture**: kind counts + top users (e.g., "plain=508, join=1,388, knn=10, monster=…; top users X×19, Y×18").

### Perpetrators Versus Victims

The single most useful analytical split:

- **Perpetrators** — the outlier class (oversized bodies, extreme runtimes). They occupy the shared resource.
- **Victims** — everything else that got slow at the same instant. Their composition identifies the *sensitive subsystem*: es8's victims were 73% join-bearing (1,388 of 1,906 non-monster slow queries) → cold reads hurt Siren join legs disproportionately, which pointed the investigation at segment/cache churn rather than at the victims themselves.

Kind-classification cues in bodies: Siren clauses `doc_ids`, `index_join`, `hash_semi_join` (each with `job_id`, `input_data_id`, `dewey_path`); `siren_federate_join_score_*` fields inside `function_score`; `_siren_fixed_point` runtime mappings; `knn` blocks (es8 lookalikes: k=1000 over org keyword-vectors, join projecting scores into people, function_score re-rank).

______________________________________________________________________

## Attribution Chain

1. **`X-Opaque-Id`** header on Apollo search traffic: `es_<user_id>_…` — extract the user ID from every slow task.
1. **Resolve user → team** via the staging Rails console.
1. **Corroborate independently** in Snowflake `PARAMS_STR` scans: a team compiling the same query shape shows a byte-identical parameter-size ceiling across requests (es8: two unrelated teams both capped at exactly 541,339 bytes — the 2,000-ZIP compilation signature).
1. **Sweep for the same signature across all teams** before concluding it is one customer. The fix target is the query *compiler* and its blast radius.

Known gap (RCA remediation #15): `X-Opaque-Id` carries user only. Propose enriching it with `team_id` + feature tag for instant attribution in any tasks-API or slowlog view.

______________________________________________________________________

## Siren Federate Internals

What the plugin adds, and where it breaks:

- **Planner job queue**: each searcher has a **200-job cap**. The cluster's latency cliff: fine until arrival rate × service time crosses the cap, then queue growth, multi-second p99, and 429s for everyone. Watch depth (alert ≥50), not just rejections.
- **Join cache**: keyed on the join's projection alias. Anything per-request in the alias (the es8 bug: `SecureRandom.hex(8)` per request, Apr 2025–Jul 2026) makes every entry unique → structural 0% hit rate with healthy-looking counters. The fix pattern: derive the alias from a content hash of the join definition, which also makes cache entries addressable for replay verification. Healthy reference: ~90% hit rate; the plugin caps ~100k entries per searcher.
- **Join strategies**: `INDEX_JOIN` suits small key sets (Siren guidance: "up to a few thousand keys"); `hash_semi_join` materializes tuple collections and ships them between nodes — visible as `federate/data create/delete` task churn in captures. The CBO can mis-estimate cardinality and pick hash-semi-join for ~1k-key joins; verify strategy choice against actual key cardinality when join legs are slow.
- **Cost model**: a single join leg made slow by cold reads occupies a planner slot for its full runtime. Slot-time, not query count, is what fills the queue.

______________________________________________________________________

## Query-Rewrite Equivalence Protocol

Before proposing any rewrite of a production query shape:

1. **Capture real production bodies** from `tasks_search_detailed.json` — never validate on synthetics alone.
1. **Scrub Siren-internal clauses** (`doc_ids`, `hash_semi_join`, `index_join`) to `match_all`, identically in both the original and rewritten variant (these clauses reference ephemeral job state and cannot replay).
1. **Replay both with `size: 0` and `track_total_hits: true`**. Require `hits.total.relation == "eq"` and equal totals; a lower-bound total is not an equivalence result.
1. **Run a separate document-equivalence replay** with a deterministic unique sort, identical pagination, and preferably one shared PIT with `search_after`. Compare every page of IDs, or an aggregate hash of all returned IDs, for the original and rewritten queries.
1. **Require zero result-set delta on multiple full live queries.** Report any synthetic-case delta explicitly (es8 AND-flatten: 0 delta on all 5 live queries, +0.7% on a location-only synthetic — shipped for product sign-off, not silently accepted).
1. **Measure with safeguards**: prefer an isolated or staging cluster before replaying production bodies. Set an explicit request timeout and capped request rate (for example, at most 4 workers and one request per worker per second). Establish a pre-approved abort threshold from pool capacity and baseline; stop immediately if active search threads exceed 70% of capacity or queue depth rises above baseline. Then measure clause-count reduction, latency ratio, and the bounded probe's pool behavior (es8: original ramped pools 234 → 1,310 active threads with ~2× self-contention; the flattened variant at 1.7× throughput was baseline-indistinguishable).
1. **Reject recall-changing variants** even when they are faster: an OR-flatten variant was rejected at +665% recall because the city↔ZIP pairing was semantically load-bearing.

______________________________________________________________________

## Fix-Proof Patterns

How to demonstrate a production fix actually worked:

- **Matched-hour, day-over-day**: compare the known worst hour (es8: h15 UTC) before vs after, not daily averages. For every window, report the >5s slow-task rate, total request sample size, and workload composition (team, query kind, and size buckets); use raw counts only as supporting data. Example supporting data: p99 113s → 28.8s, >5s count 4,342 → 2,968 at the same hour.
- **Clean-window isolation**: to measure one fix without confounders, pick windows with the other pressures absent (es8 join-cache fix: pre-fix vs post-fix mornings 06:00–08:00, no merge waves, no volleys → lookalike p99 −17%). Report the same normalized rate, sample size, and workload composition for both windows.
- **Live per-event verification**: watch individual triggering events post-fix (es8: a merge wave after the day's largest write burst — 174k docs/min — produced zero slow tasks; isolated waves drained in \<60s). Compare the event's slow-task rate and workload composition with a comparable pre-fix event; raw zero counts alone are not proof.
- **Cross-validate one number from independent systems**: es8's would-be cache hit rate ≈40% was confirmed by New Relic `used_cache` attributes (38–41%) and Mongo app-cache creates (455k/day ≈ 43% churn). One number from three systems is evidence; one number from one system is a hypothesis.
- **State residual risk explicitly**: "squalls persist, amplitude reduced" — mechanism mitigated, not eliminated. Name what remains (es8: a second team with the same query signature is "a squall-trigger waiting for schedule overlap").

______________________________________________________________________

## Detection to Propose After Any Investigation

The RCA's prevention list, generalized — after finding a mechanism, propose the telemetry that would have found it in minutes:

1. Productionized incident watcher (20s task-age sampling + auto-capture with bodies) with Slack/PD alerts. Before enabling body capture, redact sensitive query values, pseudonymize `X-Opaque-Id` before storage, restrict access, encrypt data in transit and at rest, audit access, and delete captures within seven days unless incident-retention policy approves an extension.
1. ES search slowlog on the hot indices (warn >10s, info >5s) with body logging → slow queries become grep-able in Loki. Apply the same redaction, pseudonymization, restricted access, encryption, audit logging, and seven-day retention limit before enabling body logging.
1. Compiled-query budget telemetry: emit (team, user, feature, clauses, bytes) when a compiled query exceeds ~50KB / ~200 clauses — catches monster cohorts at creation time, weeks before incidents.
1. Per-team duration-domain dashboard: busy-hours + >15s counts by team/hour; alert on new top-10 entrants.
1. Scrape join-cache stats + planner queue into Grafana; alert on hit% \<70% sustained or queue >50 — turns 15-month cache regressions into same-day pages.
1. Segment-churn alerting: segment-drop rate + filter-cache eviction rate per index family — the leading indicator of every squall.
1. Standing query-shape census: daily off-incident sample of in-flight bodies by size × team × join type — surfaces new monster cohorts as drift.
