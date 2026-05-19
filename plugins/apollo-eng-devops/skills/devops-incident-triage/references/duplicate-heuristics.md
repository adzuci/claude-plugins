# Duplicate Heuristics

The goal is one "real" ticket per issue. Be conservative — false positives waste reporter time. If two tickets look similar but you're not certain, don't merge; add a "possibly related" comment instead.

## Group candidates by

1. **Same component or service label** AND
1. **Title token overlap ≥ 0.5** (Jaccard over lowercase tokens, stopwords removed) OR **same exact error string** in description.

A pair must satisfy at least one of these to be a candidate. A single shared word ("error", "slow", "failed") is not enough.

## Pick the canonical ticket

Among a candidate group, the canonical ticket is the one with the most context. Tiebreaker order:

1. Most linked artifacts (PD links, PRs, runbooks).
1. Most comments from non-reporters.
1. Oldest `created` timestamp.

The other tickets in the group get an issue link of type `Duplicate` pointing to the canonical, plus a short comment from `comment-templates.md`.

## Do not merge when

- Tickets share only a label like `security` or `production` — those are too broad.
- One ticket is a CVE finding and the other is a runtime symptom, even if they end up being the same root cause. Link with `Relates` instead so both stay open until the underlying fix lands.
- Reporters differ and one ticket has reproduction steps the other lacks. Merging loses signal.
- Status differs (one is `In Progress`, the other `Open`). Comment instead of merging.
- **Same alert fires across multiple days on separate occasions.** That's a *recurring* issue, not a duplicate. Closing recurring instances as duplicates buries the recurrence signal — the third firing of the same alert this week is more important than the first. Either keep each open, or consolidate into one root-cause ticket assigned to the owning team and link the rest with `Relates`.
- **Title contains "Again", "Recurring", "Still", or similar reporter frustration markers.** The reporter is telling you the root cause isn't fixed; honor that signal.

## Recurring vs duplicate — quick test

- Same host/service + same alert + multiple firings inside the **same on-call shift** (hours) → **duplicates**. Merge to the still-acked or oldest-with-context.
- Same host/service + same alert + firings across **multiple days** → **recurring**. Do not merge; route to the owning team for memory/disk/limit fix.

## Examples

**Merge**: `INCIDENT-503 "search 500s on people-search"` + `INCIDENT-507 "people search returning 500"` — same component label `people-search`, title Jaccard 0.6, both Open. Canonical is the one with the linked PR.

**Don't merge**: `INCIDENT-501 "CVE-2025-1234 in nokogiri"` + `INCIDENT-512 "ES cluster red"` — both have label `security` but different components and unrelated symptoms.

**Don't merge, link as Relates**: `INCIDENT-490 "Sidekiq queue lag"` + `INCIDENT-491 "enrichment job slow"` — likely the same root cause but different symptoms; keep both until diagnosis confirms.
