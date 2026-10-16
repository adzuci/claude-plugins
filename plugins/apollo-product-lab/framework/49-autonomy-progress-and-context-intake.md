# 49 — Run in parallel, report progress, and start from the context you already have

> Decision 2026-10-14 (Akansh). Three habits slowed an Ads build. Independent work waited for a "go" it did
> not need. Long stretches passed with no word on what the harness was doing or how far along it was. And
> intake behaved as if every initiative started from zero, when the person usually already has a PRD, a
> design, an ERD, or all three.

## 1. Parallel by default

When the plan has steps that do not depend on each other, start them together, in one message, without
asking first. Examples: reviewer lenses on the same diff, an implementer on one slice while the main
session writes docs, specs on one worktree while another rebases, research questions with no shared input.

**Ask first only for:**

1. **Outward or shared actions**: a push, a PR, a merge, a Slack, Notion, Jira or GitHub comment, anything
   another person or system sees.
1. **Destructive or hard-to-reverse actions**: deleting, overwriting, force-pushing, a production or staging
   console write.
1. **Decisions that belong to a person**: a product, legal or compliance call, a human gate named by the
   plan, or a choice between options where the answer changes what gets built (doc 43 §8).

Everything else that is local, reversible and already in the plan runs. A confirmation is never asked as a
formality ("shall I continue?") between steps the person already approved.

**Do not parallelize** two writers on the same files, a step that reads another's output, or work whose
combined cost the person has capped (doc 46 §4, workflow size limits). Say which steps run in parallel and
which wait, in one line, when they start.

## 2. Progress pulse every 5 to 10 minutes

While a run is working, the person gets one plain line at least every 10 minutes of wall-clock time, and at
every stage or slice boundary:

```
[harness] 60% · BUILD slice 2 of 3 · now: specs for the vendor cap · next: rebase #107872 · waiting on: nothing
```

1. **The percentage** is `done steps / planned steps` from the intake plan table, counting each slice,
   lens and gate as one step. Re-plan, not stretch, when new steps appear: say "plan grew from 8 to 11
   steps" and recompute.
1. **One line, no jargon.** What is being built, what comes next, and any human gate it is waiting on.
   Findings and detail stay in the snapshots; the pulse is for orientation.
1. **Background work counts.** While agents or long commands run, the pulse names them ("3 reviewers
   running, 1 back") instead of going quiet. Never report a result that has not arrived.
1. **The stage-end summary** is three to five short lines: what changed, what was verified (with counts),
   what is open, and the next step. The loop report (doc 46 §6) follows it.
1. **Post only at stage boundaries.** Run `scripts/post-update.py` with the stage-end summary and execute
   its JSON plan. The 5-to-10-minute pulse stays in the current conversation; do not post every pulse to
   Jira or Notion.

## 3. Context-first intake: not every initiative starts at zero

Before asking the person anything, find out what already exists and read it.

1. **Find the artifacts.** PRD, design (Figma, Fabric Studio, Claude Design), ERD or plan, tracker epic,
   prior research, earlier runs' snapshots, recorded decisions. Look in `.ai/<initiative>/`, the links the
   statement gives, Notion, Glean, and the repo.
1. **Build the context snapshot.** One `A.context` snapshot: each fact with its source, the decisions
   already made (and by whom), and what the artifacts disagree on. Repo context comes from the repo:
   its `CLAUDE.md`, pack `INTERFACE.md` files and the codebase explorer agent, not from interviewing the
   person.
1. **Skip the stages the artifacts already cover.** A PRD skips the PRD stage and gets an audit and a council
   on its gaps. A design skips framing. An ERD goes straight to the roadmap lens and the ERD council. The
   intake plan marks each skipped stage `covered by <artifact>`.
1. **Grill every role, but ask only unresolved decisions.** Load the persona's mandatory items from
   `templates/grill-checklist.yml`. Every question the artifacts or code can answer is looked up, not
   asked. Ask remaining decisions one at a time, recommendation first. The `A.context` snapshot gets a
   `## Grill` section with one sourced answer or `deferred: <reason>` per item. `scripts/grill-check.py`
   enforces it before the run advances. A full `grill-me` interview is only for a genuinely ambiguous idea
   with no artifacts.

### The shortlist, and what the harness takes from each (2026-10-14)

| Tool | Verdict | Why |
|---|---|---|
| Matt Pocock's `grill-me` / `grilling` | **adopt the method** in step 4 | Facts first, questions only for decisions, one at a time with a recommendation. Written into intake, so nothing is installed. `grill-me` itself (a full interview) is only for an ambiguous plan with no artifacts. |
| Everything Claude Code `codebase-onboarding` | **optional, for an unfamiliar repo** | An architecture map and a starter `CLAUDE.md` for a repo the harness has not seen. Apollo repos already have `CLAUDE.md`, `INTERFACE.md` and an explorer agent. Not verified by us yet. |
| `claude-mem` | **not by default** | Session memory overlaps stage snapshots, the ledger and run indexes (docs 33, 43), which are reviewable files. It records tool use into a local store, so it needs a data-handling review before use on customer data. |
| Addy Osmani's `context-engineering` | **reference for briefs** | A design aid for what an agent should see and when. Doc 46 §4 already applies it to review briefs, and doc 48 §2 to implementer briefs. |
