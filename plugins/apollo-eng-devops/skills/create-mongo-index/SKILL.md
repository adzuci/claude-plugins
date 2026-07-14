---
name: create-mongo-index
description: Manual-invocation only. Safely plan Apollo MongoDB index creation with read-only checks, timing gates, DevOps handoff text, and human-run command templates. Run via /apollo-eng-devops:create-mongo-index.
argument-hint: model or collection plus index fields, PR, or Slack thread
disable-model-invocation: true
---

# Create Mongo Index

Use this skill to plan MongoDB index creation safely. It performs read-only triage and
produces a human-approved execution plan. It must not create indexes itself.

## Hard safety boundary

Do **not** run production write commands. In particular, do not run:

- `create_indexes`
- `create_one`
- `createIndex`
- Atlas writes
- `mongo-upgrade` write actions
- balancer, shard, or chunk-migration mutations

You may show human-run commands for approved operators, clearly marked as writes, after
the read-only checks and coordination gates are complete.

## Shared context

For shared Apollo Mongo facts, load the sibling `mongo-specialist` references instead of
duplicating them:

- `../mongo-specialist/references/read-only-commands.md`
- `../mongo-specialist/references/mongo-clusters.md`
- `../mongo-specialist/references/slack-channels.md`
- `../mongo-specialist/references/tapdata.md`
- `../mongo-specialist/references/mongo-people.md`
- `../mongo-specialist/references/related-mongo-skills.md`

Use this skill's own references for index-specific context:

- [`references/index-workflow.md`](references/index-workflow.md) — flowchart, auto-create
  rules, required gates, and authoritative runbook links.
- [`references/past-index-creations.md`](references/past-index-creations.md)

## Workflow

1. Identify the request: model/collection, desired key pattern, source PR, query shape,
   current urgency, and whether the requester already has BE Platform review.
1. Run or ask the user to run only read-only checks:
   - model file index declaration
   - existing production indexes
   - estimated collection size
   - database, collection, and cluster
   - active index builds, if relevant
1. Classify by size:
   - `<490K` / roughly `<500K`: likely auto-created by normal deploy flow; verify current
     Notion wording and ask BE Platform to review query pattern.
   - Near threshold: treat as ambiguous and ask DevOps to confirm.
   - `>500K`: DevOps coordination required before merge/deploy.
   - `>20M`: announce in `#xfn-h-devops`, confirm best timing with another team member,
     prefer off-hours/weekend planning, and consider the `mongo-upgrade` path.
1. Require BE Platform query-pattern review before creation. The index should match the
   intended filter/sort/hint shape and not create a conflicting index name.
1. Draft the handoff:
   - model and collection
   - desired index key/options/name
   - collection size and cluster
   - PR and query-shape link
   - timing recommendation
   - explicit ask for second-person timing confirmation if `>20M`
1. If the user asks for execution commands, provide human-run write templates only after
   labeling them as writes and restating prerequisites. Do not run them.
1. Provide read-only verification commands for after the human-run write.

## Output format

Keep responses concise:

- **Verdict:** auto-create, DevOps required, or needs more information.
- **Evidence:** size, cluster, existing indexes, PR/query shape.
- **Required coordination:** BE Platform, `#xfn-h-devops`, second reviewer, TapData/Mason
  if cluster-internal risk.
- **Commands:** read-only checks first; write templates only if explicitly requested.

## Canonical sources

- Adding Indexes to the Mongo Collections:
  `https://app.notion.com/p/apolloio/Adding-Indexes-to-the-Mongo-Collections-18fab2b3b4968091b280e6b461d26656?source=copy_link`
- DevOps / Infrastructure Oncall Guidelines:
  `https://app.notion.com/p/apolloio/DevOps-Infrastructure-Oncall-Guidelines-32fab2b3b49680699bf1c1191364dc30`
