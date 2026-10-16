# 33 — Deterministic stage snapshots: the only handoff between agents, stages, and sessions

> Why this exists: on Ads M1 a long session was compacted twice. After each compaction the
> continuation lost exact spec names, cited a decision that did not exist yet, and once pushed the
> frontend branch without the backend it depended on because a chained command had masked a failure.
> A background fork re-ran work it had been told to skip. None of that survives a rule that says
> **the conversation is not the record; the snapshot on disk is.**

## 1. The rule

Every stage, every council lens, and every multi-step build task writes a snapshot **before it reports**,
and every stage **starts by reading** the previous snapshot rather than the conversation. Agent reports
are reconciled against disk (`git status`, the snapshot, the ledger), never trusted.

```
.ai/<initiative>/runs/<run-id>/
  index.md                       # ordered list of snapshots with status; the run's table of contents
  A.audit.snapshot.md            # one per stage: A audit, B research, C specify, D design,
  C.specify.snapshot.md          #   E review, F.<slice>.build, G verify
  council.<change-slug>.md       # one per council (doc 34)
```

A snapshot is Markdown with frontmatter (`templates/stage-snapshot.md`). It is **append-mostly**: a
re-run of the same stage writes a new dated snapshot and links the old one; it never edits history.

## 2. What makes it deterministic

- **Inputs are named with paths and content hashes**, so a later reader knows exactly what the stage saw.
- **Facts carry a source** (path:line, URL with date and tier, or "asserted by <human>, <date>").
- **Decisions carry alternatives rejected.** A decision without them is a preference (doc 12).
- **Open questions carry an owner** or the literal word `unowned`.
- **Checks are pass/fail rows**, not prose. "Looks good" is not an outcome.
- **The human-facing copy is a Notion page, always.** Engineers, PMs and designers do not read `.md`
  files in a repo. Every snapshot, memo, gap list and decision record publishes a Notion page under the
  initiative's Notion parent (`harness-manifest.md: notion_parent`) written for a reader who never saw
  the chat, and the snapshot lists it under Mirrors with `updated: yes` and the URL. The `.md` on disk is
  the machine record and the source of the hashes; Notion is where people read. Historical Slack
  messages and closed PRs are not mirrors; they get a link to the current record at most.
- **Voice on the Notion page** (`templates/notion-page.md`): lead with the decision or finding in one
  sentence; short sentences; a term of art gets a gloss the first time; no agent or stage names without
  saying what they mean; options as a table with a recommendation; who decides and by when. It should
  read like a colleague wrote it, because the audience is colleagues.
- **The ledger gets one event** per snapshot (`ledger/append.py`), linking the snapshot path.

## 3. Reading order at the start of any stage or session

1. `runs/<run-id>/index.md` → the latest snapshot per stage.
2. The initiative's knowledge files (`domain/*.md`) for decisions and invariants.
3. `git status --short` and `git log --oneline -3` on every branch in play.
4. Only then the conversation summary, and only for intent, never for facts.

If a fact in the conversation conflicts with a snapshot, the snapshot wins and the conflict is written
into the new snapshot's `reconciliation` section.

## 4. What it costs and what it buys

One file write per stage, about 300–800 words. It buys: compaction-proof continuity, a legible replay
corpus, an audit trail a reviewer can read without the chat, and a place where the mirror discipline
(a past Ads M1 build found its ERD mirror a week stale) is checked rather than remembered.

## Notion is part of the write, not a mirror step (2026-09-24)

A stage snapshot, a council memo, a decision record or a gap list is **not written** until its Notion page exists and its URL sits in the `notion:` frontmatter field and in the run `index.md`. The inbound-router run on 2026-09-22 produced `B2.external-evidence.snapshot.md` with no page because the step read as a mirror to do afterwards; it is now the fourth write in the order snapshot → Notion → index → ledger, `record-sync.sh push` lists any record missing the field, and the skill must say in its first line when a page is `blocked:`. Lens files stay machine-only.
