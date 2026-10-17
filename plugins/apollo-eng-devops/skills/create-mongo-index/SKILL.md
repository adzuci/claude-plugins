---
name: create-mongo-index
description: Manual-invocation only. Plan safe Apollo MongoDB index creation with read-only triage, size gates, operator handoffs, and human-run command templates.
argument-hint: model or collection plus index fields, PR, or Slack thread
disable-model-invocation: true
---

# Plan Mongo Index Creation

Perform read-only triage and produce a human-approved execution plan. Never create an
index directly.

## Hard safety boundary

Do **not** run production writes: index creation or deletion, `mongo-upgrade` write
actions, or balancer, shard, and chunk-migration mutations. After
all gates pass, you may show approved operators clearly labeled human-run write templates.

## Shared context

Load only the relevant sibling `mongo-specialist` references:

- [`read-only-commands.md`](../mongo-specialist/references/read-only-commands.md) for
  inspection and [`mongo-clusters.md`](../mongo-specialist/references/mongo-clusters.md)
  to verify the database and cluster.
- [`slack-channels.md`](../mongo-specialist/references/slack-channels.md) and
  [`mongo-people.md`](../mongo-specialist/references/mongo-people.md) for coordination.
- [`tapdata.md`](../mongo-specialist/references/tapdata.md) only for cluster-internal risk;
  [`related-mongo-skills.md`](../mongo-specialist/references/related-mongo-skills.md) only
  for routing.

Use this skill's own references for index-specific context:

- [`references/index-workflow.md`](references/index-workflow.md) — source evidence and
  authoritative runbook links.
- [`references/past-index-creations.md`](references/past-index-creations.md)

## Workflow

1. Identify the request: model/collection, desired key pattern, source PR, query shape,
   current urgency, and whether the requester already has BE Platform review. When
   available, read both the Slack thread and the PR diff for the exact key, name, and
   `partial_filter_expression`. Confirm the query predicate implies the partial filter;
   otherwise the planner cannot use the index.
1. Run or ask the user to run only read-only checks:
   - model file index declaration
   - existing production indexes
   - estimated collection size
   - database, collection, and cluster
   - active index builds, if relevant
1. Classify by size:
   - `< 500_000` (exact `count`): the leadgenie healthcheck auto-creates declared indexes
     after merge (see [auto-create rules](references/index-workflow.md#auto-create-rules)).
     If the source PR introduces or changes the query or index shape, confirm appropriate
     owner review before merge.
   - Near threshold: triage uses `estimated_count`, the code uses exact `count`; treat as
     ambiguous and ask DevOps to confirm.
   - `>= 500_000`: not auto-created. DevOps builds the index **before** the model
     declaration merges, or the healthcheck pages `missing_mongo_index`.
   - `>20M`: announce in `#xfn-h-devops`, confirm best timing with another team member,
     prefer off-hours/weekend planning, and consider the `mongo-upgrade` path.
   - `>100M`: see [very large collections](#very-large-collections-100m).
1. Confirm the query and index shape have appropriate owner review. Use BE Platform for
   new or changed query patterns unless the source PR already has equivalent owner
   approval. DevOps owns collection sizing, cluster and timing risk, and production
   execution. DevOps-only coordination is sufficient when creating or synchronizing an
   already-reviewed index shape. Check for conflicting names/options, release freezes,
   and launch dates. For cross-repo work: build the index, merge the leadgenie
   declaration, then merge dependent PRs.
1. Draft a handoff with the model/collection, index key/options/name, size and cluster,
   PR/query links, timing, and required coordination. For `>20M`, explicitly request
   second-person timing confirmation.
1. If requested, provide clearly labeled human-run write templates after restating the
   prerequisites.
1. Provide read-only verification commands for after the human-run write.

## Very large collections (>100M)

- The build scans every document, even for a small partial index. Duration is not
  measured; the few precedents in
  [past index creations](references/past-index-creations.md) provide only low-confidence
  guidance.
- Watch during the build: replication lag, disk IO, mongos latency, and active balancer or
  chunk migrations.
- Abort criteria: sustained replication lag or mongos latency the on-call cannot accept.
  Human-run abort or rollback (write): identify the build with `currentOp`, then run
  `db.<collection>.dropIndexes("<index_name>")` on the primary for replica sets. For
  sharded collections, run it through `mongos`, then verify every participating shard.
  Do not use `killOp` for index builds on replica sets or sharded clusters.

## Sharded collections

- `createIndexes` runs on shards containing data for the collection; one slow or
  unhealthy participating shard sets the pace.
- Check balancer state and in-flight chunk migrations before starting.
- After the build, verify the index on every shard that contains the collection's data or
  chunks, not just via mongos. Do not treat a shard without the collection as missing the
  index. In leadgenie, `HealthChecker.check_mongo_index_discrepancies_on_shards` (weekly,
  in `check_every_week`) reports per-shard missing or mismatched indexes.

## Output format

Keep responses concise:

- **Verdict:** auto-create, DevOps required, or needs more information.
- **Evidence:** size, cluster, existing indexes, PR/query shape.
- **Required coordination:** query or index owner review when the shape changes; DevOps
  for production sizing, timing, and execution; `#xfn-h-devops`, a second reviewer, and
  TapData/Mason as applicable.
- **Commands:** read-only checks first; write templates only if explicitly requested.
