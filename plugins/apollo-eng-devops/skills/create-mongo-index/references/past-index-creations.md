# Past Index Creation Examples

These examples are from internal Glean/Slack evidence gathered when creating this skill.
They are illustrative, not policy. Re-check source threads and Notion runbooks before
making production decisions.

## New or small collections can auto-create

- PR #90782 / new collection case: DevOps guidance said indexes for collections smaller
  than roughly 500K documents are auto-created and do not require DevOps approval. The
  collection was new / size zero.
- Waterfall::WaterfallStepResult, Jan 2025: about 448,821 records; DevOps said it should
  auto-create, while still asking for BE Platform query-pattern review.

## Around 500K requires care

- WebsiteVisitor, May 2026: `WebsiteVisitor.count` was 508,413 and DevOps treated it as
  over the auto-create threshold. Related smaller collection
  `StandaloneFormEnrichmentResponse.count` was 44,108 and expected to auto-create.

## Very large collections need off-hours/weekend planning

- TypedCustomFieldValue, May 2026: collection was in the billions. DevOps planned weekend
  work and asked for BE Platform review. The attempt hit `IndexKeySpecsConflict` because
  an index name already existed with a different partial filter; verify names/options
  before creating.
- Large April 2026 index work: a roughly 2B document collection was directed toward
  weekend timing. The index completed in about an hour in that case, but do not reuse that
  as a generic estimate.
- CustomFieldValue, 2026-06-08: about 2.4B documents on the `custom-objects` cluster; two
  indexes reported done within about 65 minutes
  ([thread](https://apolloio.slack.com/archives/C69FJ9NEM/p1780904442251379)). Estimate
  from the thread, not a measurement; low confidence.
- `typed_custom_field_auto_generate_workflow_requests`, Sep 2026: about 515.5M documents
  (`estimated_count`, 2026-09-29), cluster `main`, sharded on hashed `_id`, 23 existing
  indexes. Partial `{created_at: 1}` index for leadgenie PR 104709. Above the auto-create
  threshold, so scheduled off-hours after the 2026-09-30 ApolloNEXT launch.

## Useful pitfalls

- Existing index name conflicts can block creation even when the key pattern looks right.
  Compare `name`, `key`, `partialFilterExpression`, `sparse`, `unique`, `collation`,
  `hidden`, and TTL options.
- Do not infer success just because a thread says "started." Verify with read-only
  `currentOp` / index status and final `collection.indexes` output.
- A page during an index window may be unrelated; verify impact with Grafana/PD evidence.
