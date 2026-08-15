# PR Review Mode — General Mongo Query/Schema Health

**Status: experimental.** Manual, non-blocking second opinion — never gates a merge.

## Division of labor

This mode is deliberately **broader and lower-confidence** than
`/apollo-eng:mongo-pr-guard`. Don't reimplement mongo-pr-guard's checks here — delegate to
it:

1. **Proven-incident patterns (BLOCK-worthy) → delegate, but only if it's actually
   installed.** `mongo-pr-guard` ships in the separate `apollo-eng` plugin, not this one —
   it may not be enabled in every session. See "Step 1: Check availability" below before
   calling it. When available, run `/apollo-eng:mongo-pr-guard <target>` and fold its
   BLOCK/WARN findings straight into the combined report. That skill owns: shard-key-
   without-migration, `.hint()`+`.or()` collisions, `.hint()` on a field whose predicate can
   fall outside a partial index's filter, `mongoid.yml` routing changes, unsharded bulk
   writes, and new models without a shard key. It is intentionally narrow — "only flags
   patterns with proven blast radius" — by design.
1. **General query/schema health (WARN-only, no incident precedent yet) → this mode's own
   job.** These are real patterns from `packs/mongo/spec/validate_mongo_index_spec.rb` and
   the target repo's `apollo-review-bot` learned rules
   (`.ai/apollo-review-bot/code-quality-rules.md`), not (yet) tied to an Apollo SEV. Lower
   confidence, more false-positive-prone — always label findings from this half as WARN and
   invite the author to confirm, never BLOCK.

If a pattern here accumulates its own incident later, move it into `mongo-pr-guard` as a new
numbered check rather than growing this list indefinitely.

**Do not run the general-health pass alone as a substitute when mongo-pr-guard is
unavailable.** The whole point of this mode is being a one-stop shop that never silently
drops the proven-incident half — if that half can't run, stop and say so (see Step 1)
instead of reporting only the lower-confidence WARN pass.

## When to invoke this mode

```
/apollo-eng-devops:mongo-specialist review 98835 --repo apolloio/leadgenie
/apollo-eng-devops:mongo-specialist review --repo apolloio/leadgenie   # current branch vs main
```

## Workflow

1. **Check availability of `apollo-eng` before delegating.** `mongo-pr-guard` lives in the
   `apollo-eng` plugin, a separate install from this one (`apollo-eng-devops`). Check, in
   order:

   - Look for `enabledPlugins["apollo-eng@apollo-plugins"]` (`true`) in the project's
     `.claude/settings.json` (if the repo has one) and the user's `~/.claude/settings.json`.
     Project-level settings win when both are present; either one being `true` counts as
     available.
   - If you can't read those files (no filesystem access, different client), fall back to
     attempting the call itself in the next step and treat an "unrecognized command" /
     "unknown skill" style response as unavailable — don't guess.

   **If available:** continue to step 2.

   **If NOT available:** stop here — do not run the general-health pass on its own. Tell the
   user plainly, then end the mode:

   ```
   ## Mongo Review — apollo-eng not installed

   This mode delegates proven-incident checks to /apollo-eng:mongo-pr-guard, which ships
   in the `apollo-eng` plugin. That plugin isn't enabled in this session, so I can't run
   the full one-stop review.

   To enable it:
   - Claude Code CLI: run `/plugin`, or add `"apollo-eng@apollo-plugins": true` under
     `enabledPlugins` in `.claude/settings.json` or `~/.claude/settings.json`.
   - Claude Desktop: `+` -> Plugins -> Add Plugins.
   - Org-wide default install: ask #it-help-desk.
   (The `apollo-plugins` marketplace itself is installed by default for all Apollo Claude
   users — this is just about enabling the one plugin.)

   Re-run `/apollo-eng-devops:mongo-specialist review <target>` once it's enabled.
   ```

1. **Delegate:** run `/apollo-eng:mongo-pr-guard <target>` (same PR number/branch and
   `--repo`). Keep its report's findings verbatim for the combined output — don't
   re-summarize or re-judge them.

1. **Get the diff for the general-health pass**, filtered to Ruby/model files, same as
   mongo-pr-guard's Step 1:

   ```bash
   gh pr diff <NNN> --repo <owner/repo> -- '*.rb'
   ```

1. **Grep added lines (`^\+`) for these patterns.** For each hit, read ~15 lines of
   surrounding context — not the whole file — before deciding whether to include it:

   | Pattern | Grep signal | Source | Why WARN |
   | --- | --- | --- | --- |
   | Skip/limit pagination instead of cursor/batches | `\.skip\(.*\.limit\(` or `.limit\(` chained after `.skip\(` | apollo-review-bot P1 | Scans all docs up to the skip point; prefer `each_batch`/cursor. |
   | Possible N+1 | a Mongoid query (`Model.where`/`.find`/`.first`) inside a method that is itself called per-record in a loop (check the call site) | apollo-review-bot P3 | Re-running a query per record instead of preloading/memoizing once. |
   | Loop instead of bulk op | `.each` / `.each_with_index` block containing `.save`, `.update`, or `.create` on a Mongoid model | apollo-review-bot P7 | Prefer `MongoUtil.bulk_update` or similar. |
   | Unbounded bulk operation | `bulk_write(`, `insert_many(`, `update_many(` with no visible batch-size limit (`each_slice`, `in_batches`) nearby | apollo-review-bot P8 | Can exceed Mongo limits or spike memory without an explicit batch size. |
   | Missing field projection | a `.where(...)` used only to check existence/read a couple of fields, with no `.only(...)`/`.pluck(...)` | apollo-review-bot P12 | Loads full documents when only a few fields are needed. |
   | `team_id` not the leading field in a new compound index for a multi-tenant collection | new `index({...})` where `team_id` is present but not first | apollo-review-bot P10 | Queries missing `team_id` first can force cross-team scans. |
   | Bool/enum as the leading index field with no `partial_filter_expression` | new `index({<bool_or_enum_field>: ..., ...})` with no `partial_filter_expression` option, where the first field is a `Mongoid::Boolean` or a `simple_enum` `_cd` field | `validate_mongo_index_spec.rb` check 1 | Low-cardinality leading field is inefficient without a partial filter. |
   | Redundant index (common prefix) | a new `index(...)` whose leading fields are a prefix of (or fully overlap with) another declared index on the same model | `validate_mongo_index_spec.rb` check 2 | The narrower index is redundant; remove it. |
   | Falsy field default | new Mongoid field with `default: nil`, `default: false`, `default: true`, `default: 0`, or `default: {}` | `validate_mongo_index_spec.rb` check 3 | Wastes storage; omitting the default has the same effect. |

1. **Report.** Combine mongo-pr-guard's findings with this mode's WARN-only findings under
   one heading:

   ```
   ## Mongo Review (experimental)

   ### From /apollo-eng:mongo-pr-guard
   <paste that skill's findings verbatim, including its "All Clear" case>

   ### General query/schema health (WARN — lower confidence, not yet incident-linked)
   - **File:** `path/to/file.rb:LINE` — <pattern name>
     **Found:** <what was found>
     **Why it might matter:** <one sentence>
     **Suggested action:** <what to check/change>

   If none, say so plainly: "No general-health findings in this diff."
   ```

## Scope notes

- This mode reads models/diffs read-only via `gh`, same as the rest of `mongo-specialist` —
  no Rails boot, no DB connection, no production writes.
- Keep reads targeted (grep for the table's signals, then read only the matching context) —
  don't paste whole model or diff files into context. See mongo-pr-guard's own guidance on
  scanning only added (`+`) lines.
- This is exploratory. If it proves useful across several real PRs, the natural next step is
  a CI check in the target repo — see `/apollo-eng:mongo-pr-guard`'s own notes for the
  incident-pattern half of that cost/benefit question; this general-health half is lower
  confidence and likely needs more real-PR tuning before it's CI-ready.
- The availability gate in Step 1 exists because `mongo-pr-guard` and `mongo-specialist`
  ship in different plugins (`apollo-eng` vs `apollo-eng-devops`) — unlike a sibling skill
  in the *same* installed plugin (always present once that plugin is installed), a
  cross-plugin dependency can genuinely be missing. Never skip the check and assume it's
  there.
