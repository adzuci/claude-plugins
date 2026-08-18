# Latency Investigation Playbook

Step-by-step methodology for recurring ES latency where global dashboards look fine. Distilled from the es8-main-v1 recurring latency RCA (Amol Patil, Jun–Jul 2026).

______________________________________________________________________

## The 12-Step Runbook

**Step 1 — Snapshot cluster vitals, expecting them to be clean.** Record status, node count, active shards, pending tasks at every capture — to rule out the usual suspects and to timestamp. In all nine es8-main-v1 captures the cluster was green with 0 pending tasks. Green is a precondition check, not a conclusion.

**Step 2 — Abandon global percentiles; switch to the duration domain.** Chart counts of requests >5s / >15s / >30s and busy-hours (Σ duration) per team, user, feature, and hour. Four reasons global stats hide these incidents:

- **Volume dilution**: 17k heavy requests/week inside 600k+ searches/hour is invisible in any global p50/p95.
- **Damage is slot-time, not counts**: 10.7s avg × 17k/wk ≈ 51 busy-hours/wk of occupancy — equivalent to millions of fast queries — while request counts barely move.
- **CPU stays flat**: when the bottleneck is queue occupancy + disk, CPU/heap alerting never fires.
- **Tail metrics are the only witness**: the signal exists only when slicing request logs by team/duration and reading bodies off the tasks API.

**Step 3 — Get query bodies.** Dashboards do not carry them. Repeatedly, or on a timer:

```
GET /_tasks?actions=indices:data/read/search*&detailed=true
```

Returns every in-flight search with running time and full query source (up to 1MB+). Before production use, bound this capture: use a 10s request timeout, permit only one in-flight capture, and back off after a timeout or error. Persist at most 100 tasks per capture and truncate each body at 100 KiB with an explicit truncation marker; record a representative sample of the remaining tasks in the census rather than repeatedly fetching or storing unbounded results.

**Step 4 — Classify every slow task** into plain / join / knn / oversized. Define "oversized" from the observed body-size distribution gap (es8: >80KB vs next-largest \<30KB), not from a guess. Produce a census per capture: kind counts + top users.

**Step 5 — Split perpetrators from victims.** Perpetrators = the outlier class. Victims = everything else slow at the same instant. The victim composition identifies the sensitive subsystem: in es8-main-v1, 1,388 of 1,906 non-monster slow queries (73%) carried joins → the Siren join leg was the pressure point.

**Step 6 — Attribute every heavy query to a human.** `X-Opaque-Id` → user → team; corroborate via an independent source (Snowflake request-log parameter-size signatures). See [query-analysis.md](query-analysis.md).

**Step 7 — Check whether the queue, not the CPU, is the bottleneck.** Flat CPU + exploding latency + 429s = a bounded job queue with a hard cap (es8: Federate planner, 200 jobs/searcher) filled by slot occupancy, not request rate.

**Step 8 — Correlate with write/merge behavior at minute resolution.** Segment-count delta per minute, write docs/20s. Hour granularity hides the coincidence structure that actually triggers incidents.

**Step 9 — Prove cold-cache effects with per-disk metrics scoped to the node group.** Cluster totals stay flat; the 5–9× disk-read rise only exists sliced to the specific data tier's disks (GCM per-disk `read_bytes` for Apollo).

**Step 10 — Check every cache's actual hit rate, and read its key construction in code.** A key containing anything per-request (random, timestamp, UUID) is a structurally 0% cache regardless of what its counters imply.

**Step 11 — Build the change timeline.** Correlate incident onset against merged PRs, limit raises, feature-enforcement flags, ingestion-volume changes, and infra events, asking "what changed 1–4 weeks before the first incident?" The es8 timeline: a latent cache-key defect (Apr 2025) + ingest volume 4× (spring) + a query-size limit doubled (Jun 11) + server-side enforcement that bypassed app caches (Jul 2) + one customer's usage pattern (Jul 7) + a GCP host event (Jul 13). No single change caused it; the sequence armed it.

**Step 12 — Hunt the disconfirming case.** Find (a) heavy load with no incident and (b) an incident with only one pressure present. es8 had both: heavy CoAdvantage windows after the merge fix passed cleanly, and a pure volley tripped thresholds with no merge wave. Conclusion: the pressures were multipliers; no single pressure was necessary or sufficient alone, but some combination was present in every real incident. If you cannot find either case, your linear model of a threshold system is probably wrong.

______________________________________________________________________

## The Threshold-Machine Model

> The system is a threshold machine, not a linear one.

Multiple independent pressures (merge-wave cold reads, heavy-query slot occupancy, cache-miss recompute) vary independently. Any subset usually stays under the cliff (es8: the 200-job planner cap); incidents occur when they stack in the same minutes. Consequences for method:

- Weekend/off-peak traffic looks clean even though the mechanism is always present.
- Hour-scale comparisons look "the same" between incident and non-incident days; only minute-scale stacking differs.
- Fixing any one pressure lowers incident frequency without eliminating the mechanism — verify residual behavior, not just "fixed."

______________________________________________________________________

## Hypothesis Elimination Patterns

How the es8 investigation killed wrong theories — reusable tests:

| Hypothesis | Elimination test |
|---|---|
| "It's a host/node problem" | Queue ordering: nodes froze (CPU 50%→1%) *before* planner queue went 1–2 → 190. Freeze caused the spike — a separate cause, excluded from the recurring chain but kept as a capacity contributor. |
| "It's CPU/heap/GC" | CPU flat during every squall; heap deaths reclassified as the *endpoint* of queue pressure, not the cause. |
| "It's cluster/shard state" | Green, ~21k shards, 0 pending tasks in every capture. |
| "It's just more usage" | Volume +34% while >15s queries went 2 → 2,483. "Usage grew modestly — cost per query exploded." The explosion is in the duration domain, exactly what clause amplification + cache bypass predicts. |
| "It's one bad customer" | Found heavy usage without incident and an incident without the customer. Also found a second team with a byte-identical query ceiling → fix the compiler and the blast radius, not the customer. |
| "The cache is fine" | Read the key construction in code (randomized alias → structurally 0%), then confirmed empirically post-fix (0% → 90.4%). |
| "Repeat queries are slow" | First-vs-repeat analysis: repeats already fast (p50 ~160ms via request/app caches); the cache win lives in the tail and first-page requests. |

______________________________________________________________________

## Capture-Rig Spec

The tool that cracked the case: a minute-resolution recorder + trigger-driven auto-capture, built *before* deep analysis because slow queries carry no bodies in any dashboard.

**Fast tier — every 20s:** in-flight task ages (from `_tasks`), planner/threadpool queue depths, rejection counters. Apply the Step 3 single-flight, timeout, backoff, sampling, and truncation limits to every detailed task capture.

**Slow tier — every 60s:** per-index write/merge/segment/cache counters; per-node CPU, heap, GC, disk-IO; Siren join-cache counters (`GET /_siren/cache`).

**Trigger conditions** (any): ≥30 tasks >15s · ≥40 tasks >5s · planner queue ≥12 · rejections >0 · write burst · merge wave.

**On trigger, write a timestamped capture dir** (`YYYYMMDDTHHMMSSZ`) containing:

- `tasks_search_detailed.json` — full bodies from the tasks API
- Hot threads for the suspect node group
- Thread-pool state and Federate data-task counts
- Cluster vitals
- A computed slow-task census: kind counts + top users

Before productionizing, redact sensitive query values and pseudonymize `X-Opaque-Id` and top-user values with a stable one-way token before storage. Restrict capture access to the incident-response group, encrypt data in transit and at rest, and audit access. Retain at most 60 captures and delete each capture within seven days unless the incident-retention policy explicitly approves an extension. Make the census greppable. Productionizing this rig as a service with Slack/PagerDuty alerts was remediation #8 of the RCA — it detects squall onset in \<60s with query bodies attached.

______________________________________________________________________

## Command Inventory

Run commands from the `plugins/apollo-eng-devops/skills/es-specialist/` skill context when using its local references or capture artifacts. The API examples below have no relative file paths: replace `<index>` and `<node-name-pattern>` with the approved target and send them through the approved read-only ES client.

**Verbatim from the RCA** (confirmed exact):

```
GET /_tasks?actions=indices:data/read/search*&detailed=true
GET /_siren/cache
```

Notes: `_tasks` returns full query source per in-flight search. `/_siren/cache` returns per-node aggregates only — the plugin exposes no key-listing API.

**Reconstructed canonical forms** — the RCA quotes these tools' *output*, not the calls; parameters below are inferred from output headers. Confirm with Amol before treating as gospel:

```
# Hot threads, scoped to the suspect node group
# (output header shows: interval=500ms, busiestThreads=4, ignoreIdleThreads=true)
GET /_nodes/<node-name-pattern>/hot_threads?threads=4&interval=500ms&ignore_idle_threads=true

# Per-index write/merge/segment/cache counters
GET /<index>/_stats/indexing,merge,segments,query_cache,request_cache

# Per-node CPU/heap/GC/disk
GET /_nodes/stats/os,jvm,fs,thread_pool

# Search thread pools
GET /_cat/thread_pool/search,search_worker?v&h=node_name,name,active,queue,rejected

# Segment counts (for the sawtooth)
GET /_cat/segments/<index>?v
GET /_cat/indices/<index>?v&h=index,segments.count,docs.count
```

**External data sources used in the RCA:**

| Source | Identifier | Used for |
|---|---|---|
| Google Cloud Monitoring | per-disk `read_bytes` | Cold-segment proof: 5–9× disk-read rise on the org-people tier while cluster totals stayed flat |
| Snowflake | `FCT_MONGO_HTTP_REQUESTS_V3_RT_VW` | Request-level latency; per-team/duration slicing; busy-hours |
| Snowflake | `PARAMS_STR` scans | Cross-team query-shape census by byte signature |
| New Relic | `used_cache` attributes | Cross-validating cache hit-rate estimates |
| MongoDB | app-cache create counts | Independent cache-churn cross-check |
| ES master logs + recovery history | | Node-ejection forensics |
| Staging Rails console | | `X-Opaque-Id` user → team resolution |

______________________________________________________________________

## Heuristics Worth Remembering

- "Usage grew modestly — cost per query exploded." Check the duration domain before accepting a volume explanation.
- "Damage is slot-time, not counts."
- "Tail metrics were the only witness."
- Green health + 0 pending tasks + flat CPU were all true during every incident.
- A cache with counters can still be structurally 0% effective; verify the key, then the rate.
- Fix the compilation and the blast radius, not one customer.
- Every causal link needs its own independent evidence source — and a hunt for the disconfirming case.
