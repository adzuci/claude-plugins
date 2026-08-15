---
name: mongo-pr-guard
description: MongoDB safety review for PRs. Detects patterns that have caused real production incidents at Apollo (unsharded collections, hint+or query collisions, hint+partial-index mismatches, bulk write risks, cluster routing changes). Activate when /mongo-pr-guard is called, or proactively when reviewing a PR that touches Mongoid model files, query code, or config/mongoid.yml.
argument-hint: optional PR number or branch name (defaults to current branch diff vs master)
---

# Mongo PR Guard

Detect MongoDB patterns that have caused real production incidents at Apollo.
Each check below maps to one or more actual RCAs. This skill is intentionally narrow —
it only flags patterns with proven blast radius, not hypothetical risks.

> **Note:** This skill complements (does not replace) the existing static analyzer in
> `packs/mongo/spec/mongo_query_static_analyzer_spec.rb`. That analyzer validates hint/index
> alignment but **explicitly skips `.or()` queries** (see `CRITERIA_CHANGERS`), and it does
> not check whether a `.hint()`'d field's query predicate actually satisfies that index's
> `partial_filter_expression` (Check 6). This skill covers those gaps.

______________________________________________________________________

## Step 1: Get the diff

If a PR number or branch was provided as an argument, use it. Otherwise use the current branch.

```bash
# For current branch:
git diff origin/master...HEAD -- "*.rb" "config/mongoid.yml" "db-migration-files/*.rb"

# For a specific PR number (replace NNN):
gh pr diff NNN -- "*.rb" "config/mongoid.yml" "db-migration-files/*.rb"
```

List the changed files to orient:

```bash
git diff origin/master...HEAD --name-only -- "*.rb" "config/mongoid.yml"
```

Print a one-line summary of: how many model files changed, whether mongoid.yml changed,
whether any db-migration-files changed, and whether any worker files changed.

______________________________________________________________________

## Step 2: Run all 6 checks

Run each check independently. For each finding, record:

- **Severity**: BLOCK (must fix before merge) or WARN (must explicitly acknowledge before merge)
- **Check name**
- **File and line**
- **What was found**
- **Why it's risky** (link to the source incident)
- **Recommended action**

Collect all findings — do not stop early. Present them all together in Step 3.

______________________________________________________________________

### Check 1 — Shard key declared but no migration call

**What to look for:**

In the diff, find any Mongoid model file that adds or modifies a `shard_key` declaration:

```
shard_key <field>: '<strategy>'
```

For each model that has this, check whether `MongoUtil.shard_collection(ModelName)` appears
anywhere in the diff (db-migration-files, rake tasks, or anywhere else in the PR).

If `shard_key` is added/changed AND `MongoUtil.shard_collection` is NOT present → **BLOCK**.

If `shard_key` was already present before the diff (i.e., the diff only shows surrounding
context lines but did not add the `shard_key` line itself) → skip this check for that model.

**Why this matters:**

> The `IpHem` model (PR #84485, Mar 2026) declared `shard_key ip_address: 'hashed'` but
> `MongoUtil.shard_collection(IpHem)` was never run in production. The collection stayed
> unsharded. A bulk ingest of 99M records in ~1 hour hit the email-3 shard's 1,200 MB/s
> disk throughput limit. 366K+ errors across 100+ services. TTM: 122 min.
> **Source:** [RCA: email-3 MongoDB Shard Outage](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1)

**Recommended action:**

Add a migration file in `db-migration-files/` that calls `MongoUtil.shard_collection(ModelName)`.
Add a note in the PR description for DevOps to run it post-deployment. Example:

```ruby
# db-migration-files/YYYY_MM_DD_shard_model_name.rb
MongoUtil.shard_collection(ModelName)
```

Also verify in the PR description that DevOps has been looped in to run this in production.

______________________________________________________________________

### Check 2 — `.hint()` on a query chain containing `.or()`

**What to look for:**

In the diff, find any Ruby code that chains `.hint(...)` and `.or(...)` together in the same
query (in either order). Both single-line and multi-line chains count.

Patterns to grep for in added lines (lines starting with `+` in the diff):

```
\.hint\(.*\).*\.or\(
\.or\(.*\).*\.hint\(
\.or\b     # flag any new .or() call and check if .hint() is nearby in the same chain
```

For each match, read surrounding context (up to 20 lines) to determine if `.hint()` is
in the same query chain. If yes → **BLOCK**.

**Why this matters:**

> PR #76873 (Dec 2025) added `.hint(team_id: 'hashed')` to a `.or()` query in
> `OverviewLayoutService.get_layouts()`. One `.or()` branch was `{ owner_id: user.id }` —
> no `team_id` field. MongoDB forced a full collection scan on every page load. Latency
> spiked immediately. Mitigated by rollback. TTM: 34 min.
>
> The existing static analyzer (`mongo_query_static_analyzer_spec.rb`) defines `.or` in
> `CRITERIA_CHANGERS` and **explicitly skips** these query chains — it will not catch this.
> **Source:** [RCA: INCIDENT-24318 SEV-1 Application Latency](https://www.notion.so/2daab2b3b49680ca93b0c9c0acd92133)

**Recommended action:**

Remove the `.hint()` from the `.or()` query and let MongoDB choose its own plan, OR restructure
to avoid OR semantics (e.g., split into two separate queries). If a hint is truly necessary,
confirm that **every branch** of the `.or()` contains the hinted field.

To suppress a known-safe case, add the comment `# mongo_query_static_analyzer_spec: safe`
on the line immediately before the query — but only after confirming all `.or()` branches
include the hinted index field.

______________________________________________________________________

### Check 3 — `config/mongoid.yml` changed

**What to look for:**

Check if `config/mongoid.yml` appears in the list of changed files. If yes → **WARN**.

Read the changed lines in `mongoid.yml` and identify:

- Which client names were added, removed, or modified
- Which hosts/replica sets changed
- Whether any `store_in client:` references in the diff match the changed clients

**Why this matters:**

> Client names in `mongoid.yml` are misleading. `performance_insensitive_noncustomer_data`
> actually routes through the email-3 shard, not a data cluster. When the IpHem model used
> `store_in client: 'performance_insensitive_noncustomer_data'`, it unknowingly routed
> 99M bulk inserts through email-3, which serves 100+ other services.
>
> The SEV-0 Node pool migration (Nov 2025) also involved misconfigured firewall rules across
> 19 Terraform workspaces — the new node pool CIDR was missing from Redis Rate Limiter rules.
> **Source:** [RCA: email-3 MongoDB Shard Outage](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1),
> [RCA: SEV-0 app.apollo.io Outage](https://www.notion.so/2abab2b3b496806f9cebc5cf763ff891)

**Recommended action:**

For each changed client in `mongoid.yml`:

1. Identify the actual MongoDB cluster behind it (not just the name)
1. Check how many other models use `store_in client: '<name>'` — grep the codebase
1. Confirm disk throughput headroom on the target cluster if writes are expected to increase
1. If adding a new client pointing to an existing cluster, consider whether the name accurately
   reflects the cluster's actual purpose

______________________________________________________________________

### Check 4 — Bulk/mass writes to an unsharded or newly-sharded collection

**What to look for:**

In the diff, identify any added code that performs bulk or high-volume writes. Look for:

```ruby
insert_many(
bulk_write(
.create  # in a loop or .each block
.upsert_one
update_many(
find_and_modify
```

Also look for worker files that process large datasets and call `.save`, `.create`, or
`.update` on Mongoid models in a loop.

For each bulk write pattern found, identify the target model. Then check:

1. Does the model file have a `shard_key` declaration? If not, the collection may be unsharded.
1. Was `shard_key` added in this same PR (Check 1 above)? If so, was `MongoUtil.shard_collection`
   confirmed to have been run in production?

If bulk writes target a collection with **no confirmed sharding** → **BLOCK**.
If bulk writes target a collection that was **just sharded in this PR** with no migration yet run → **BLOCK** (combine with Check 1 finding).

**Why this matters:**

> IpHem: 99M records inserted in ~1 hour to an unsharded collection. All writes routed to
> a single shard. Disk throughput hit 1,200 MB/s limit (had been at 70%+ for 2 weeks with
> no alerting). 366K errors across 100+ services.
> **Source:** [RCA: email-3 MongoDB Shard Outage](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1)

**Recommended action:**

Before merging any PR with bulk writes to a collection:

1. Confirm the collection is sharded in production (check via Rails console or ask DevOps)
1. If not sharded, shard it first (use `/mongo-shard-collection` skill)
1. Add rate limiting if writing >1M docs/hour — use `WorkerHelper::Fraction` or batched
   sleeping to spread writes over time

______________________________________________________________________

### Check 5 — New Mongoid model with no shard key and no explanation

**What to look for:**

In the diff, find any **new** Mongoid model files (new file, not modified). A model file:

- Is under `app/models/`, `packs/*/app/models/`
- Contains `include Mongoid::Document`

For each new model, check:

- Does it have a `shard_key` declaration? If yes → skip (Check 1 handles it).
- Does it have a comment like `# small collection` or `# sharding not needed` near the top? If yes → skip.
- Does it appear in any worker, bulk import, or service that processes large volumes? → **WARN**.
- Even without obvious bulk usage → **WARN** (proactive, to prevent future incidents).

**Why this matters:**

> New collections without shard consideration often grow quietly until they hit a limit.
> The recommended threshold from the email-3 RCA is **10M documents** (the original alarm
> threshold was 100M — far too late). At Apollo's write volume, new collections can cross
> 10M records within weeks of launch.

**Recommended action:**

For each new model, answer: "Will this collection grow beyond 10M documents?" If yes or
unknown, add a `shard_key` now and open a DevOps request to shard it in production before
data grows. If the collection is intentionally small (e.g., config, feature flags), add
a comment explaining why:

```ruby
# Small config collection — no sharding needed (expected < 10K docs)
class FeatureConfig
  include Mongoid::Document
  ...
end
```

______________________________________________________________________

### Check 6 — `.hint()` on a field whose value can fall outside a partial index's filter

**What to look for:**

In the diff, find any Ruby code that calls `.hint(<fields>)` on a Mongoid criteria chain
(with or without `.or()` — this check is **not** limited to `.or()` chains; Check 2 covers
that narrower case). Grep added lines for:

```
\.hint\(
```

For each hit:

1. Identify the model class the query runs against (e.g. `Contact` in `Contact.hint(...)`).
1. Find that model's file and read its `index(...)` declarations. Match one against the
   hinted field(s) (same fields, direction can differ). If that index declaration has a
   `partial_filter_expression`, note its condition (e.g. `<field>.exists => true`).
1. Look at the same chain's `.where(...)` (or `.criteria`) predicate for that field. Ask: can
   this predicate's value ever fall outside the partial filter's condition?
   - A literal `nil`, or a bare local variable/method result with no guard before the query,
     is the common case when the partial filter requires `$exists => true` — trace the value
     back to where it's assigned; if it comes from a helper method, read that helper (just
     the method body, not the whole file) and check for `return nil` / blank-returning paths.
   - Also flag an explicit value or range in `.where()` that plainly contradicts the partial
     filter's condition (e.g. filter restricts to `status: 'active'`, query passes `status: 'inactive'`).
1. If the predicate can fall outside the filter and there is no guard (e.g. no
   `if <field>.present?` / `unless <field>.nil?`) before the query → **BLOCK**.

**Why this matters:**

> PR #98835 (Jul 2026) added a LinkedIn reverse-lookup to `enricher.rb`:
> `Contact.hint(linkedin_url: -1, team_id: -1).where(linkedin_url: linkedin_url, ...)`, where
> `linkedin_url` came from `LinkedinUrlUtil.sanitize_person_url`, which returns `nil` for
> short/non-person URLs. The hinted index,
> `index({linkedin_url: -1, team_id: -1}, {partial_filter_expression: Contact.where(:linkedin_url.exists => true).selector})`,
> only covers documents where `linkedin_url` exists — a `nil` value falls **outside** that
> filter. Mongo couldn't use the hinted index for those rows and instead scanned broadly
> (~5,000 unrelated null-`linkedin_url` contacts per shard per call), spiking worker queue
> latency. SEV-1, fixed in PR #99141 by adding an `if linkedin_url.present?` guard.
>
> This has no `.or()` in the chain, so `mongo_query_static_analyzer_spec.rb`
> (`CRITERIA_CHANGERS`-based skip logic doesn't apply here) and Check 2 above (`.or()`-
> specific) both miss it — it needs this dedicated check.
> **Source:** [RCA: SEV-1 Stuck CSV Enrichment Jobs Increase Worker Queue Latency](https://app.notion.com/p/apolloio/SEV-1-Stuck-CSV-Enrichment-Jobs-Increase-Worker-Queue-Latency-3b2ab2b3b49680f28a70d614b1e9a08f?source=copy_link)

**Recommended action:**

Add a presence/existence guard before the hinted query so the predicate always satisfies the
partial filter, e.g.:

```ruby
if linkedin_url.present?
  Contact.hint(linkedin_url: -1, team_id: -1).where(linkedin_url: linkedin_url, ...)
end
```

If the field's absence is a valid case the query needs to handle, don't hint it — let Mongo
choose a plan that can also use a non-partial index or a collection scan for that branch, or
split into two queries (one guarded/hinted, one unguarded/unhinted).

______________________________________________________________________

## Step 3: Output the findings report

Format findings as a structured report:

```
## Mongo PR Guard Report

**PR / Branch:** <name>
**Checks run:** 6
**Findings:** <N> (X blocks, Y warnings)

---

### 🔴 BLOCK — <Check Name>
**File:** `path/to/file.rb` (line N)
**Found:** <what was found in the diff>
**Risk:** <one sentence on why this is dangerous>
**Action:** <specific thing to do before merging>
**Incident reference:** [<RCA title>](<link>)

---

### 🟡 WARN — <Check Name>
...
```

If there are **no findings**, output:

```
## Mongo PR Guard Report — All Clear ✅

**PR / Branch:** <name>
**Checks run:** 6
**Findings:** 0

No MongoDB incident patterns detected in this diff.
```

______________________________________________________________________

## Step 4: Offer to help fix

If running interactively (i.e., invoked directly by the user, not from a git hook or CI):

For each BLOCK finding, ask:

> "Would you like me to generate the fix for [finding]?"

For WARN findings:

> "Would you like me to help investigate [finding] further?"

Do not auto-fix — always ask first. Changes to model files and migration scripts
need human confirmation.

If the argument contains `--hook` (i.e., invoked from a git pre-push hook), skip all
follow-up questions. Output only the report from Step 3, then exit. The hook script
will parse the output and decide whether to block the push.

______________________________________________________________________

## General guidelines

- Only scan **added lines** in the diff (lines starting with `+`) for pattern detection.
  Context lines and removed lines are for understanding only.
- If the diff is large (>500 lines of Ruby changes), warn the user that context window
  usage is high and suggest running the skill on specific files if accuracy degrades.
- If running on a PR number, use `gh pr diff <NNN>` — do not checkout the branch.
- Never suggest disabling or working around `# mongo_query_static_analyzer_spec: safe`
  suppression comments that already exist in the codebase without first confirming the
  suppression is valid.
- Cross-reference findings with the existing static analyzer results when possible:
  ```bash
  SKIP_COVERAGE=1 bin/rspec packs/mongo/spec/mongo_query_static_analyzer_spec.rb
  ```
  If the static analyzer also flags the same file, mention it in the report so the author
  knows to address both.
