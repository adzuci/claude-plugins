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
- The same thread reinforced the pattern: define the index in the model, but if collection
  size is above roughly 500K, reach out to DevOps before merging.

## Very large collections need off-hours/weekend planning

- TypedCustomFieldValue, May 2026: collection was in the billions. DevOps planned weekend
  work and asked for BE Platform review. The attempt hit `IndexKeySpecsConflict` because
  an index name already existed with a different partial filter; verify names/options
  before creating.
- Large April 2026 index work: a roughly 2B document collection was directed toward
  weekend timing. The index completed in about an hour in that case, but do not reuse that
  as a generic estimate.

## Useful pitfalls

- Existing index name conflicts can block creation even when the key pattern looks right.
  Compare `name`, `key`, `partialFilterExpression`, `sparse`, `unique`, and TTL options.
- Do not infer success just because a thread says "started." Verify with read-only
  `currentOp` / index status and final `collection.indexes` output.
- A page during an index window may be unrelated; verify impact with Grafana/PD evidence.
