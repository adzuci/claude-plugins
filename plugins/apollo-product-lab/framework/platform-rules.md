# Platform rules: Apollo facts a design must respect

> Read by the architecture, backend and db-perf lenses before they review a design (doc 43 §3).
> Each lens marks every row that applies as `checked`, `failed`, `unverified` or
> `not applicable`, with evidence. Reading this file is not a check.

Paths are relative to the `apolloio/leadgenie` repo root. A source is code or a canonical doc, never
an incident on its own. Each row was checked against the source on 2026-10-06; the review date is
when the owner checks it again.

Scale and infrastructure patterns (batching, fan-out, job args, Redis, concurrency, wiring) live in
[apollo-infra-patterns.md](./apollo-infra-patterns.md) as IP1 to IP18; the lenses check those too.

## How to add or change a row

- Add rows through `/harness-escape fix` or a PR that cites the source. Name the owner.
- The owning domain team approves when the row applies. The harness maintainer removes duplicates
  and prunes stale rows every quarter.
- Prefer a link to an executable check (a spec, a cop, a CI job) over restating it. A copied rule
  goes stale; a check does not.
- If the source does not say what the row says, the row is wrong. Soften it or delete it.

## Rules

### R1. React to list and contact changes through the existing change paths

| Field | Value |
|---|---|
| Rule | When a feature must react to "a contact was added to or removed from a list" or "a contact changed", hook into the existing change paths instead of building a new change feed. The repo has no general change-data-capture stream (a feed of every database change); none was found in a search on 2026-10-06, so confirm with the owner before assuming one. |
| Applies when | A design needs to notice list membership changes, contact field changes, or list deletion. |
| Exceptions | Changes made by bulk paths that bypass these methods. List deletion has two paths: `Label#destroy_self` runs callbacks, but bulk deletion (`EntityProgressJob` job type `:delete_labels`) uses `Label.delete_all`, which skips Mongoid callbacks. A design must cover both. |
| Source | `packs/crm_platform/lib/label_upsert.rb` (`LabelUpsert.add_or_remove`); `packs/crm_platform/lib/contact_upsert.rb` (`ContactUpsert.process_changes`); `packs/crm_platform/app/models/label.rb` (`destroy_self`, and the comment above `destroy_book_of_business_finder_views`); `packs/util/app/models/entity_progress_job.rb` |
| Executable check | none |
| Owner | crm-platform pack owners (resolve in `apollo-dev-teams.yml`) |
| Review date | 2027-01-06 |

### R2. Keep background jobs short; make long ones resumable

| Field | Value |
|---|---|
| Rule | A Sidekiq job (a background job) should ideally finish in under 10 minutes. A job that can run longer must be resumable: it saves its progress (last processed id, a cursor) and continues from there after an interruption. Design multi-minute work as several small staged jobs that each save progress. |
| Applies when | Any new or changed worker, especially one that loops over a large collection or calls an outside API. |
| Exceptions | none stated in the source. The source says "ideally" for the 10-minute target; resumability above 10 minutes is a hard rule. |
| Source | `.cursor/rules/backend.mdc` (the job design rules near "ALWAYS keep jobs short and focused" and its checklist item "If the job runs longer than 10 minutes, is it resumable?"); `WorkerHelper::Fraction` for batching (repo `CLAUDE.md`) |
| Executable check | none; the backend reviewer checks it |
| Owner | be-platform |
| Review date | 2027-01-06 |

### R3. Plan every index of a new Mongo collection in its first schema PR

| Field | Value |
|---|---|
| Rule | After each deploy, `PostDeploymentTasks.auto_shard_new_collections` walks every Mongoid model. For a model that declares a shard key and whose collection is not sharded yet, `MongoUtil.shard_collection_if_unsharded` calls `create_indexes` only if no index starts with the shard key, and then shards the collection. Indexes are not created on any later deploy by this path. So list every index the feature will need in the first schema PR, and verify they exist before code that depends on them runs. |
| Applies when | A new Mongoid model or collection, or a new index on an existing one. |
| Exceptions | A model with no shard key declaration is skipped by this task entirely; ask devops how its indexes get created. |
| Later changes | A new index on an existing sharded collection: reviewers ask the author to "contact the devops on how and when the new index would be created" (code-quality rule P13). Dropping an index or choosing a shard key: ask devops and be-platform first. The source does not state a fixed process for these, so the lens marks them `unverified` until the owner answers. |
| Source | `packs/deploy/lib/post_deployment_tasks.rb` (`auto_shard_new_collections`; it pages be-platform when sharding fails); `packs/util/lib/mongo_util.rb` (`shard_collection_if_unsharded`); `.ai/apollo-review-bot/code-quality-rules.md` P13 |
| Executable check | none for completeness; `bundle exec rspec packs/mongo/spec/validate_mongo_index_spec.rb` checks index shape |
| Owner | be-platform, devops |
| Review date | 2027-01-06 |

### R4. Index shape rules for MongoDB 6.0

| Field | Value |
|---|---|
| Rule | An index whose first field is a boolean or an enum must have a `partial_filter_expression` on that field, or a recorded exception. A partial filter can use only the operators MongoDB supports in partial filters (equality, `$exists: true`, `$gt`, `$gte`, `$lt`, `$lte`, `$type`, and from 6.0 `$and`, `$or`, `$in`); `$ne` is not one of them. A query that hints a partial index must match its filter. |
| Applies when | Any new or changed index. |
| Exceptions | Indexes listed in `packs/mongo/spec/validate_mongo_index_exceptions.rb`, after a devops discussion (the spec's failure message says how). |
| Source | `packs/mongo/spec/validate_mongo_index_spec.rb` (first-field rule); MongoDB manual, "Partial Indexes" (supported filter operators); `.ai/apollo-review-bot/static-review-context.md` SC3 (hints on partial indexes); local Mongo image `mongo:6.0.27` in `docker-compose.yml` |
| Executable check | `bundle exec rspec packs/mongo/spec/validate_mongo_index_spec.rb`; `packs/mongo/spec/hint_partial_filter/validate_hint_partial_filter_spec.rb` (hints) |
| Owner | devops |
| Review date | 2027-01-06 |

### R5. Read secrets through CredentialsProvider

| Field | Value |
|---|---|
| Rule | Read every API token, signing key or other secret with `CredentialsProvider.instance.credential(...)`. Never hardcode it and never read it from `ENV`. |
| Applies when | Any code that needs a secret, including a new provider integration. |
| Exceptions | none stated |
| Source | `.ai/apollo-review-bot/code-quality-rules.md` SEC3 |
| Executable check | the review bot (SEC3); no cop yet |
| Owner | security |
| Review date | 2027-01-06 |

### R6. Changes to what goes into an outbound email need a Deliverability assessment

| Field | Value |
|---|---|
| Rule | A change to email templates, link tracking, link destinations or the content shape of outbound email can affect how mailbox providers judge Apollo's sending domains. Get a Deliverability owner's assessment before coding it, and let them decide how invalid destinations are handled. |
| Applies when | The change touches template rendering, tag substitution, links or tracking in sent email. |
| Exceptions | Follow the `do_not_route` list under Deliverability in `surface-owners.yml`: AI-generated email content or templates go to Warm Outbound, sequence analytics in dashboards go to Rep Experience, and deliverability credits or send limits go to Growth pricing and packaging. Read the list at review time; it changes. "Not needed" is a valid owner answer, recorded with who and when (doc 43 §5). |
| Source | `surface-owners.yml` (Deliverability owns "Email templates and snippets", with its `do_not_route` exceptions; "Email open/click tracking", "Domain reputation and domain diagnostics"); `apollo-dev-teams.yml` marks `packs/email_messaging/lib/mailer/assemble.rb` as a Deliverability sensitive file |
| Executable check | the CI sensitive-files approval (`ApolloDevTeam.team_to_sensitive_files_hash` in `packs/util/lib/apollo_dev_team.rb`), which fires after the code exists; run it against the planned file list at intake too |
| Owner | deliverability |
| Review date | 2027-01-06 |

## Worked examples (context, not rules)

These were the right choices for one product (an audience sync for ads). Use them as examples of
what a lens should consider, not as mandates.

- **Status fields over version counters.** A record that moves through explicit states (a small
  state machine) shows its journey; a version number does not.
- **Mark rows with a call id instead of embedding member lists.** One sync call could cover up to
  5,000 members. Embedding their ids in one document makes it large and hard to query; marking
  each member row with the call id and a partial index does not.
- **Price a lock before choosing it.** Locking 100,000 to 250,000 contacts for a run has a memory
  cost and a risk of running out of memory. An Elasticsearch point-in-time (a frozen view of the
  search index, with keep-alive and a timeout) served as the run's snapshot instead.
