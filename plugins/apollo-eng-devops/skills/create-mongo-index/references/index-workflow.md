# Index Creation Workflow Reference

Authoritative runbooks (source of truth, re-check current wording):

- [Adding Indexes to the Mongo Collections](https://app.notion.com/p/apolloio/Adding-Indexes-to-the-Mongo-Collections-18fab2b3b4968091b280e6b461d26656?source=copy_link)
- [DevOps / Infrastructure Oncall Guidelines](https://app.notion.com/p/apolloio/DevOps-Infrastructure-Oncall-Guidelines-32fab2b3b49680699bf1c1191364dc30)

## Auto-create rules

Code behavior in leadgenie:

- `HealthChecker.check_non_existing_prod_mongo_indices`
  (`packs/observability/lib/health_checker.rb`, run by `SidekiqHealthcheckWorker`) lists
  declared-but-missing indexes and calls `klass.create_indexes` only when
  `klass.count < MongoUtil::AUTO_CREATE_INDEX_COLLECTION_SIZE_THRESHOLD`.
- The constant is `500_000` (`packs/util/lib/mongo_util.rb`), strict `<`, exact `count`.
- If any discrepancy remains after that pass, it calls `Pager.alert` with paging key
  `missing_mongo_index` (immediate). At or above the threshold, the index must already
  exist before the model declaration merges.
- Triage uses `estimated_count`, which can differ from exact `count`; be conservative near
  the boundary.

Older docs and Slack say `<490K` or roughly `500K`. The Notion runbook remains the source
of truth for process.
