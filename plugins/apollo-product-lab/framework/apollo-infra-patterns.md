# Apollo infrastructure and scale patterns

> Read by the architect (doc 17 §6, the Load model), the infra lens of the council (doc 34), and the
> backend, db-perf and security reviewers. Each entry says what Apollo does, when it applies, a do and a
> don't, a real example, and the check a reviewer runs. A reviewer marks each applicable entry
> `checked`, `failed`, `unverified` or `not applicable` with evidence. Reading the file is not a check.

**Where these came from.** The Ads Audience Sync backend (leadgenie PRs 106144, 106751, 106759, 106754,
106779 and the consolidated 107058) was designed by the harness architect and passed our reviewer agents.
A senior reviewer then left 90 findings the harness had missed; a replay of that review (doc 44 §5)
measured the reviewers before and after these patterns. Every "don't" below cites one of those
comments by PR and comment id. Every "do" cites code on leadgenie `origin/master`, checked
2026-10-08; paths are relative to the leadgenie repo root.

**Precedence.** `.ai/apollo-review-bot/static-review-context.md` (SC rules) wins over this file, and this
file wins over generic Rails or Mongo advice. Where an SC rule or a `code-quality-rules.md` rule says the
same thing, the entry names it; do not raise both.

**Severity.** A miss on IP1 to IP9 on a path that runs per team, per contact or per sync is `major`; on a
T0/T1 collection or a removal, consent or billing path it is `blocker`. IP18 on a host path that runs for every team is `blocker`. IP13 to IP16 are correctness
findings (category `wiring` or `test_gap`), never `nit`.

| Id | Pattern | Category |
|---|---|---|
| IP1 | One read per batch, not per item | `n_plus_one` |
| IP2 | One write per batch; combine find-then-update | `n_plus_one` |
| IP3 | Fan out with `pluck` ids and bulk enqueue | `fan_out` |
| IP4 | Job args are ids, not payloads | `job_args` |
| IP5 | Redis is a cache or a lock, never the record | `redis_truth` |
| IP6 | Embedded document edits are not in `changes` | `embedded_changes` |
| IP7 | MongoSearcher for list endpoints, keyset for scans | `pagination` |
| IP8 | Every claim and every read filters on status | `status_filter` |
| IP9 | Bound concurrency per team, not globally | `concurrency` |
| IP10 | Reuse before build | `duplication` |
| IP11 | Shard key in every query and update | `shard_key` |
| IP12 | Partial indexes match the query predicate | `index` |
| IP13 | Every new field has a reader | `wiring` |
| IP14 | Every predicate can be true in production | `wiring` |
| IP15 | Specs must not stub the unit under test | `test_gap` |
| IP16 | Every state has an exit; heavy work leaves the request | `wiring` |
| IP17 | Compute once per flow | `duplication` |
| IP18 | A hook on a host write path costs nothing for a team that does not use the feature | `host_path_cost` |

---

## IP1. One read per batch, not per item

- **Pattern.** Load everything a loop needs before the loop with one `$in` query (on the shard key
  prefix), then group in Ruby. A Mongo call inside `each`/`map` whose filter uses the loop variable is
  an N+1.
- **Applies when.** Any loop over contacts, rows, syncs, lists, entries or ids, including a loop of
  service calls that each do one read (`runs.each { Runs.start(_1) }` where `start` reads).
- **Do.** `packs/1p_intent/app/workers/first_party_intent/intent_aggregate_worker.rb:52`
  (`where(team_id:, :organization_id.in => organization_ids)`, one query for all orgs).
- **Don't.** PR 107058 `change_hooks.rb:116`, `:126`, `:153`, `:166`, `change_notifier.rb:35`, `:86`,
  `read_slots.rb:56`, `reuploads.rb:61`, `:138`, `ledger_check.rb:166`, `:173` (comments 4214831760,
  4214826185, 4214822798, 4215197086, 4214872640, 4214877127, 4217071940, 4217384724, 4217616529,
  4207665184, 4207928662): per-sync or per-contact reads in loops. Also `runs.rb:252` (4217261874): fine
  for one sync, N+1 as soon as the caller loops.
- **Check.** For every loop in the diff, list the Mongo calls the body makes, directly or through a
  method it calls (open the callee). If any filter depends on the loop variable, it is IP1. Count the
  commands with the leadgenie spec helper `count_mongo_commands` when a spec exists. Rule: P3, P11.

## IP2. One write per batch; combine find-then-update

- **Pattern.** Writes for a batch go in one `bulk_write` (ordered: false) or one `update_many`. A row
  that may not exist is one `update_one(filter, {$set: ..., $setOnInsert: defaults}, upsert: true)`,
  not a find, then an insert or an update. Two queries that touch the same document are one
  `find_one_and_update`.
- **Applies when.** Saving per-item state in a loop; insert-if-missing; claim-then-read.
- **Do.** `packs/deliverability/app/services/deliverability/sequence_snapshot_refresher.rb:173`
  (bulk `update_one` with `$setOnInsert`, `upsert: true`);
  `packs/ui/app/workers/migration/finder_view_name_location_migration_worker.rb:83` (`bulk_write`);
  `packs/ui/app/models/finder_view_last_view.rb:59` (one `find_one_and_update` with `$setOnInsert`).
  Cop `Mongoid/UseBulkOperations` flags `record.save` in a loop; the new `Mongoid/NoQueryInLoop` cop
  (leadgenie, if registered) flags reads and writes keyed on the loop variable.
- **Don't.** PR 106759 `connections.rb:24` (4205502274): one insert per account. PR 107058
  `change_hooks.rb:49` (4207458207) N+1 writes; `suppression_entries.rb:29` (4214799837) a find and an
  update on one entry.
- **Check.** Count writes per batch in the Load model (doc 17 §6.2). More than one write per item per
  batch needs a stated reason. Rule: P7, P8.

## IP3. Fan out with `pluck` ids and bulk enqueue

- **Pattern.** A scheduler plucks the ids that are due (`.pluck(:_id)`, on an index, with the status
  filter of IP8) and enqueues one job per id with `WorkerHelper::Enqueue.bulk` in slices of 1,000 to
  10,000. The job takes the lock. Very large collections use `WorkerHelper::Fraction` or
  `WorkerHelper::IdBatch` instead of plucking everything.
- **Applies when.** A cron that finds due work, a sweep, a backfill.
- **Do.** `packs/crm_integration/app/workers/crm/configuration_sync_worker.rb:36` (pluck, `each_slice`,
  `Enqueue.bulk`); `packs/util/app/workers/worker_helper.rb:14` (`Enqueue.bulk`, size must be
  1,000..10,000), `:103` (`Fraction`), `:386` (`IdBatch`).
- **Don't.** PR 107058 `due_syncs.rb:15` (4217005134): a hand-written paged scan with slots where
  "pluck the due ids and bulk enqueue `scan_page_worker`, which locks" handles about 10,000 ids per run.
- **Check.** A cron that loads documents (not ids) to decide what to enqueue, or enqueues one
  `perform_async` per item in a loop, is IP3. Rule: R1, R2, W2, `code-quality-rules.md` R18 (arg shape).

## IP4. Job args are ids, not payloads

- **Pattern.** Sidekiq args live in Redis. Pass ids. A set larger than about 100 ids goes into a Mongo
  document and the job gets that document's id. `perform_persisted` does not avoid this: it saves the
  event in Mongo and `EventDispatcher#enqueue_events` then pushes the full `event.args` through
  `Enqueue.bulk` into Redis
  (`packs/sidekiq_persisted_events/app/public/sidekiq_persisted/event_dispatcher.rb:91`).
- **Applies when.** Any `perform_async`, `perform_in`, `perform_persisted` or `Enqueue.bulk` call.
- **Do.** `packs/util/app/workers/entity_progress_job/entity_progress_job_worker.rb:8`
  (`perform(entity_progress_job_id)`; the work list lives on the `EntityProgressJob` document).
- **Don't.** PR 107058 `change_notifier.rb:23` (4215097335): up to 1,000 contact ids per job.
- **Check.** For each enqueue, state the largest arg in the Load model. Arrays whose size scales with
  a list, a team or a page are IP4 above 100 entries. Rule: R11.

## IP5. Redis is a cache or a lock, never the record

- **Pattern.** A counter, budget, quota or watch list that must survive a Redis restart or eviction
  lives in Mongo, updated with `$inc` or `find_one_and_update`. Redis may cache it (and is rebuilt from
  Mongo) or rate-limit around it. Say what happens when Redis is down: the feature degrades, it does
  not overspend or forget.
- **Applies when.** Daily or monthly call budgets, per-account quotas, "already processed" sets,
  membership watch sets.
- **Do.** Credits: `packs/billing/app/models/credit_usage.rb:589` (`find_or_create_by!` then
  `usage.inc(num_credits:)`), with the Redis cache only decremented beside it (`:591`). Locks:
  `packs/util/lib/zp_redis/distributed_lock.rb:24` (`DistributedLock.with_lock`). Rate limits:
  `packs/3p_data_tool/lib/third_party_data_integrations/leaky_bucket_rate_limiter.rb:3`.
- **Don't.** PR 107058 `account_call_budget.rb:23` (4217173805): the daily Google call budget only in
  Redis ("what happens if Redis goes down during the day?"); `check_contacts_worker.rb:98` (4215122494):
  a Redis watch set nobody removes a deleted list from.
- **Check.** Every Redis key in the diff is labelled cache, lock or rate limit in the Load model, with
  its rebuild path. A key that is the only copy of a number the product enforces is IP5.

## IP6. Embedded document edits are not in `changes`

- **Pattern.** Mongoid's `model.changes` has no entry for edits inside `embeds_many` documents
  (`Contact#contact_emails`, `contact_campaign_statuses`, `phone_numbers`). A hook keyed on those field
  names never fires. Use `ChangeHandler.get_changes_v2(model, include_embedded: true)` or compare with
  the pre-change copy `ContactUpsert.process_changes` already holds. Embedded edits written with
  `update_many` (sequence status) skip model callbacks entirely; hook the writer.
- **Applies when.** Any change hook, dirty check or "only update if changed" on a model with embeds.
- **Do.** `packs/crm_platform/lib/change_handler.rb:842` (`get_changes_v2`, doc comment at :836);
  `packs/crm_platform/app/models/contact.rb:98` and `:397` (the embeds).
- **Don't.** PR 107058 `change_hooks.rb:36` (4207269280): matched `contact_emails` and
  `contact_campaign_statuses` in `changes`, so secondary-email and sequence changes were never seen.
- **Check.** For each key a hook reads from `changes`/`previous_changes`, confirm it is a top-level
  field. For an embed, name the writer that bypasses callbacks. Write the negative spec with a real
  `ContactUpsert`, not a hand-built `changes` hash.

## IP7. MongoSearcher for list endpoints, keyset for scans

- **Pattern.** A UI list with filters, sort and pages uses a `MongoSearcher::<X>Searcher` class
  (`include MongoSearcher::Base::Core`). An internal scan pages by keyset: `where(:_id.gt => cursor)`,
  `order_by(_id: :asc)`, `limit(n + 1)` to learn whether there is more. The cursor is validated (a
  malformed id is a 400, not page 1), ties on a non-unique sort key break on `_id`, and the sort runs in
  Mongo on an index. If you choose keyset over MongoSearcher for an endpoint, say why in the PR.
- **Applies when.** Any paginated endpoint or batch scan.
- **Do.** `packs/search_mongo_queries/lib/mongo_searcher/domains_searcher.rb:3` (a searcher), caller
  `packs/deliverability/app/controllers/api/v1/domains_controller.rb:16`; keyset
  `packs/deliverability/app/services/deliverability/sequence_snapshot_invalidator.rb:98`. Cop
  `Mongoid/AvoidSkipLimitPagination`.
- **Don't.** PR 106779 `sync_pages.rb:57`, `:69` (4206330549, 4206330575): no MongoSearcher and no
  cursor edge cases; `audience_syncs.rb:62` (4205502684): a 90-day cut-off instead of paging.
- **Check.** Name the index that serves the sort; test a malformed cursor and a tie. Rule: P1 (sort
  in Mongo).

## IP8. Every claim and every read filters on status

- **Pattern.** A claim (`update` that takes ownership of rows) filters on the status that makes the row
  claimable, an empty or expired claim (`claim_id: nil` or `claim_expires_at < now`), and the shard key.
  A read that plans work re-applies the same filter. Startable, sendable and live status sets are
  explicit allow-lists in one constant, and paused, ended, deleting and deleted are excluded from every
  scheduler query.
- **Applies when.** Claims, schedulers, sweeps, "load the rows to save", state transitions.
- **Do.** The atomic claim in
  `packs/crm_integration/app/workers/external_sequence_deploy_worker.rb:295` to `:325` (count free slots
  from locks, the real ceiling is `try_acquire_lock` in `#perform`).
- **Don't.** PR 107058 `ledger_check.rb:205`, `:277` (4208088647, 4208228307); `due_syncs.rb:23`
  (4217014196); `run_due_syncs_worker.rb:18`, `:67` (4217136031, 4217188947: paused and ended were
  startable); PR 106779 `audience_syncs.rb:15` (4205502639: `deleting` not excluded).
- **Check.** For each query on a model with a status field, write its status predicate next to it. A
  claim without a status and expiry predicate is IP8. Rule: R15 (TOCTOU).

## IP9. Bound concurrency per team, not globally

- **Pattern.** Apollo bounds concurrent work with team-keyed locks (one or N slots per team, each a lock
  name; the job's atomic `try_acquire_lock` is the ceiling) and with queue weights. There is no
  `sidekiq-unique-jobs` or `Sidekiq::Limiter` (`sidekiq-limit_fetch` is commented out in the Gemfile
  because it "locks redis and slows it down"). One global slot for a whole feature serializes every
  team behind the slowest one.
- **Applies when.** Any lock, slot, semaphore or "only one at a time" rule.
- **Do.** `packs/crm_integration/app/workers/external_sequence_deploy_worker.rb:295` (slot key per team
  and CRM), `:320` (`lock_names_for`, 1 slot by default, `MAX_CONCURRENT_JOBS` behind a flag);
  `packs/email_messaging/lib/mailer/per_contact_task_lock.rb:9` (per-contact lock).
- **Don't.** PR 107058 `read_slots.rb:22` and `run_due_syncs_worker.rb:35` (4217239243, 4217337533):
  one sync at a time.
- **Check.** The Load model states max concurrent per team and in total, and what holds the limit
  (lock name, queue weight). "One at a time" needs a reason that names the shared resource.

## IP10. Reuse before build

- **Pattern.** Before writing a helper, grep for it. The common ones: `EmailUtil`
  (`packs/email_accounts/lib/email_util.rb:4`, sanitize and validate; hashing is `set_email_hash` in
  `packs/email_messaging/app/models/concerns/email_status_functionality.rb:65`); `UserAction` for an
  audit trail; `MongoSearcher`; `ChangeHandler`; `ZpRedis::DistributedLock`; `LeakyBucketRateLimiter`;
  `WorkerHelper`; `MongoUtil.bulk_write` (`packs/util/lib/mongo_util.rb:890`); `as_enum` with
  `map: :string`.
- **Applies when.** A new normalizer, hasher, audit field, lock, pager, rate limiter or change feed.
- **Don't.** PR 106751 `identifier_normalizer.rb:14` (4206329039: EmailUtil); PR 106144
  `suppression_entry.rb:29` (4194198006: record it in UserAction); PR 107058 `reuploads.rb:115`
  (4217545956: logic repeated from the ledger iteration).
- **Check.** For each new class or module, record the grep you ran and the nearest existing helper.
  Run `flay` on the pack when a PR adds more than 500 lines. Rule: C20.

## IP11. Shard key in every query and update

- **Pattern.** Every read and write on a sharded collection carries the full shard key prefix (usually
  `team_id`), so it is routed to one shard. In development and test, `update_one` without it raises
  `MongoUpdateShouldContainShardKey` (`app/overrides/mongoid_overrides.rb:744`; the check is installed
  under `if !Rails.env.production?` at `:760`, so production does not raise, it scatters).
- **Distribution.** A hashed `team_id` spreads different teams across shards. It does not split one team:
  every document of a team has the same hash, so a single-field `team_id: 'hashed'` key puts a whole team
  in one chunk. For a collection where one team can be large (a per-contact ledger), add a ranged suffix
  (`shard_key team_id: 'hashed', audience_sync_id: 1, identifier_hash: 1`) so the balancer can split a
  big team.
- **Do.** `packs/1p_intent/app/models/website_visitor_domain_tracker.rb:25` (`shard_key team_id:
  'hashed'`) and `:75` (query with `team_id`).
- **Don't.** PR 106144 `member_contribution.rb:93` (4205503515): the reviewer asked for the hashed
  prefix with a ranged suffix on the per-contact ledger.
- **Check.** db-perf M3, M4. In the Load model, every query row names its shard key match, and a
  collection whose largest team exceeds a chunk names its suffix.

## IP12. Partial indexes match the query predicate

- **Pattern.** A partial index serves a query only when the query's filter implies the
  `partial_filter_expression`. Hinting a partial index with a predicate it excludes fails
  (SC3). Status-scoped sweeps are a good fit for a partial index on the due status.
- **Do.** `packs/1p_intent/app/models/website_visits/intent_event.rb:48`
  (`partial_filter_expression: { processed: false }`).
- **Check.** SC3 for the hint; list each new index with the query that uses it (production method, not a spec).
  The test env raises "No good index was used" from `spec/support/mongo_criteria_override.rb:79`.

## IP13. Every new field has a reader

- **Pattern.** A persisted field or Redis key that only gets written is an unwired feature. Find an
  app-code reader (not a spec, not an index catalogue). In a stack of PRs, look on the stack tip. An
  index needs a named purpose instead of a reader: the production method whose query it serves, or a
  constraint it enforces (a unique index, a TTL index), stated in the model or the ERD.
- **Don't.** PR 106144 `audience_sync.rb:31` (4196719544) and `member_contribution.rb:38`..`:40`
  (4194447032, 4194457744, 4194662254): `reupload_by` was written and indexed, and no code read it, so
  re-upload before the membership duration was never wired. `audience_sync.rb:23` (4205503652): nothing
  updates the list ids when a list is deleted.
- **Check.** `git grep -n <field> <stack_tip_ref> -- 'packs/**/app/**' 'app/**' ':!*spec*'` for every
  new field; zero readers is `wiring`, `major`.

## IP14. Every predicate can be true in production

- **Pattern.** For each condition that gates behaviour, name one realistic production input that makes
  it true and one that makes it false. Evaluate allow-lists and regexes against the real value set (the
  enum's full list, seeded defaults such as `ContactStage` defaults). A constant compared with a constant,
  or an enum value nothing ever sets, is dead.
- **Don't.** PR 106754 `eligibility.rb:300`, `:301` (4206329915, 4206329938): consent is never
  `granted`, so every contact is ineligible and the upload path never runs; `eligibility.rb:17`, `:26`
  (sources and stages that no default value matches). PR 106779 `audience_sync_presenter.rb:52`
  (4205502652): a branch for `deleted` rows the controller never loads. PR 107058 `ledger_check.rb:259`
  (4208144614): an empty-rows branch that cannot happen.
- **Check.** Allow-lists over stored values. Report unreachable branches as `wiring`, `major`;
  `blocker` when the branch is the product's main path.

## IP15. Specs must not stub the unit under test

- **Pattern.** A spec that stubs, wraps or replaces the return value of the method that decides the
  outcome (`allow(Eligibility).to receive(:call).and_return(eligible)`) proves nothing about it. Use
  factories to build the state; stub only the external edge (Google, ES).
- **Don't.** The Ads eligible path was reachable only in specs that rewrote `Eligibility.call`
  (escape analysis, finding 1).
- **Check.** Read every spec in the diff for stubs on project code. `code-quality-rules.md` T21, T22.
  Report at `major` with category `test_gap`.

## IP16. Every state has an exit; heavy work leaves the request

- **Pattern.** Classify every status the code stores or returns as transient (`calculating`,
  `pending`, `waiting`, `checking`) or terminal (`deleted`, `ended`). For every transient one, find the
  code that moves it out; a terminal one needs none. Work above a few hundred documents or any outside API fan-out in a web
  request moves to a job, and the UI learns the result through Pusher or polling.
- **Don't.** PR 106754 `eligibility_preview.rb:23` (4206329886): up to 5,000 ids across collections
  inline, and `calculating` has no producer; PR 106759 `available_accounts.rb:21` (4205502257): many
  Google calls in one request; PR 107058 `change_notifier.rb:67` (4215132862): work that belongs in
  the job.
- **Check.** List each transient state with its exit (file:line). In the Load model, the "request path" row gives
  the worst-case reads and outside calls per request.

## IP17. Compute once per flow

- **Pattern.** One flow reads a document once, validates a value once (in the model or service),
  and claims a row once. A second identical query, a second Eligibility pass, a second claim, or a
  check repeated in a caller and its callee is IP17.
- **Don't.** PR 106779 `audience_sync_presenter.rb:16` (4205502665, queried twice in create);
  `audience_syncs_controller.rb:49` and PR 106759 `connections_controller.rb:60` (4205502657,
  4205502292, validated twice); PR 107058 `ledger_check.rb:172`, `:174` (4208038202, 4208047791: claimed
  twice, Eligibility twice); `run_due_syncs_worker.rb:66` (4217147783, checked again in ReadSlot).
- **Check.** Trace the request or job end to end and list each query; duplicates are IP17. Rule: C4.

## IP18. A hook on a host write path costs nothing for a team that does not use the feature

- **Pattern.** A hook, callback or notifier the feature adds to another team's write path (contact
  upsert, replies, sequences, lists, stages, unsubscribes) first asks an in-process question that needs
  no I/O: is this team one that uses the feature? The answer comes from an in-memory set refreshed on a
  timer from one shared key, never from a per-call lookup. Only a using team pays any Redis, Mongo or
  outside call, and that per-call cost is priced against the host path's real rate and the shared store's
  measured headroom.
- **Do.** Gate on an in-process set of team ids that have ever enabled the feature, refreshed once a
  minute from one Redis set; a non-using team makes zero Redis or Mongo calls in the hook. Give any I/O
  the hook still does a timeout that the host path can afford, and keep it off the write path when it can
  move to a job.
- **Don't.** PR 107058 (Ads change hooks on the host paths above): every call made two Redis lookups on
  the shared rate-limiter Redis for every team, including the teams that never use Ads, each with a 0.1 s
  timeout on the write path. At the host's peak (contact upsert about 5.1K calls/s) that added about 12K
  commands/s to a store peaking at 41K commands/s and 0.74 of its single core, shared with every rate
  limiter in the app. The ERD's hook row said "one Redis lookup", IP5 held, and the infra lens passed:
  nobody multiplied the per-call cost by the host rate.
- **Check.** (1) The hook's first statement before any I/O is an in-process gate; any I/O above it is
  `failed`. (2) Every per-call I/O on a shared store is priced as host peak calls/s x store calls per host
  call, against that store's measured peak (commands/s and CPU for Redis, ops/s for Mongo); the Load model's
  host-path columns (doc 17 §6.2) carry both numbers with their metric. A row without them is `failed`, and
  a projected increase that takes a single-threaded store near one core is a `blocker`. (3) The budget is
  per shared resource, not per row: sum the projected increase of every host-path row (this design's and
  the ones already on record for that store) at coincident host peaks, and check the total against the
  store's measured peak; five rows that each fit can together saturate it.

---

## Conventions that ride with these patterns

These are repo conventions; a repo that records them in its own review context (in leadgenie: `.ai/apollo-review-bot/static-review-context.md`) is the authority on exact wording.
snake_case JSON (the frontend camelizes), `belongs_to` instead of a bare `*_id` field, leave a false
boolean unset, permission filters with `except:`, sort in Mongo and never cap before an in-memory sort,
validate once, Redis not the source of truth, small job args, embedded edits, `pluck` plus bulk enqueue.

## How to add an entry

An entry needs a source (code on master or a canonical doc), a real example, and an owner who can say
it is still true. Add it through `/harness-escape fix` when a review misses something; the escape record (doc 43,
`eval/escapes/`) is what the next reviewer change is measured against.
