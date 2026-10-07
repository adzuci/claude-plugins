---
name: experiment-analytics-audit-beta
description: >-
  BETA. Audits an experiment's analytics before and after build: which events
  the metrics and learnings need, which exist in leadgenie code and Amplitude,
  which must be built, and which would mean different things per arm. Then
  verifies the build against that audit and builds approved gaps as a draft PR.
disable-model-invocation: true
metadata:
  lifecycle-stage: Discovery, Execution
---

# Experiment Analytics Audit

Lifecycle stage: **Discovery** (Stage A) and **Execution** (Stages B and C).
Follow `${CLAUDE_PLUGIN_ROOT}/references/experiment-lifecycle-conventions.md`
for how to open, check tools, collect inputs, teach, hand over, review, and
close. This file holds only what is specific to the analytics audit.

This skill owns one artifact, the experiment's analytics audit, across its
life. Before build it answers: **for everything the experiment needs to
observe, the metrics it is read by and the interactions the team wants to learn
from, can we observe it today, and what has to be built so we can?** The metric
split (primary, secondary, guardrail) comes from pre-analysis and is usually
reused team-standard metrics; the audit sanity-checks that mapping, then
inventories the experiment's own events. Its single most valuable finding is
the **symmetry risk**: an existing event whose firing condition the treatment
changes, so the metric silently means different things per arm.

Once the code exists, the same skill closes the loop: **does the build match
the audit, what is missing or drifted, does every event fire and land for both
arms**, and it is where missing events get built, not just listed. It only ever
builds what the audit, or the user explicitly, specced. When the build is right
and the audit is stale, it brings the audit up to date rather than reporting a
mismatch forever.

## Invocation

```text
/apollo-eng-experimentation:experiment-analytics-audit-beta [Experiments DB entry URL | flag key | experiment key] [audit link or file]
```

Arguments are optional; intake asks for anything not passed.

## Open

- **Produces:** before build, a verdict on whether the experiment can be
  measured today, an inventory of every event it needs with what exists and
  what must be built, and the events at risk of meaning different things per
  arm. After build, a verdict on whether the code matches that audit, a
  per-event table ending in an Amplitude link for every event that exists,
  approved fixes offered as a draft PR, and an offered update to the audit.
  On a scope change, the audit re-done for what changed, saying what it
  replaces.
- **Does not:** choose or size metrics (`experiment-pre-analysis-beta`); review
  where exposure fires (`experiment-exposure-design-beta`); check
  exposure-before-metric ordering in a diff (`experiment-exposure-order`); read
  results.

## Preflight

- **leadgenie checkout** is required; events are confirmed in code. For Stages
  B and C, the experiment's branch or PR checked out if the code is unmerged.
- **Amplitude MCP** for taxonomy, volumes, and catalog links (projects `241072`
  prod, `168367` staging). Without it, the user pastes from the Amplitude UI:
  every "exists" is on their word and "lands" cannot be confirmed; say so.
- **Snowflake (Jarvis MCP)** when Amplitude volume is thin or a governed
  definition exists. Without it, note the gap and move on.
- **Notion MCP** only if the audit lives in Notion, the DB entry must be read,
  or the user will want an export or an audit update written for them.
- **GitHub CLI** authenticated, for Stages B and C, if fixes may be offered as
  a draft PR.
- Read `references/leadgenie-analytics-mechanics.md` before reading any code:
  how product events fire in this repo, grep starters, and how to look up
  taxonomy and volumes. For Stages B and C also read
  `references/verification-checks.md` before classifying or fixing anything:
  the classification definitions, arm-symmetry code patterns, landing checks,
  and the catalog link format.

## Inputs

Ask, in one message, which stage the user is at:

> (a) before build, nothing in code yet · (b) the code exists, check it against
> the audit · (c) the surfaces, events, or audit changed since the last pass.

Then collect what the stage needs. Stop and ask for whatever is missing; do not
start the inventory without it. Restate in at most six lines and get a yes.

**Stage A** needs all five:

1. **Experiments DB entry**: URL, or a flag key to find the entry by.
1. **The metric split from pre-analysis**: primary, secondary, guardrails. Read
   it from the entry's Metrics tables when filled; otherwise ask for the split
   pre-analysis produced. If pre-analysis has not run, **stop** and route to
   `/apollo-eng-experimentation:experiment-pre-analysis-beta`; never reconstruct
   a split. You may *propose* additional secondary or guardrail candidates, as
   proposals the PM confirms.
1. **The learnings** the PM wants from this experiment, in free text.
1. **The surfaces and user flow the treatment changes**, in the engineer's
   words: "What UI, state, or routing will treatment change that existing
   events might depend on?" This drives the symmetry pass.
1. **Where exposure is planned to fire** (file or component, or "not decided";
   then note the gap and point at the exposure-design skill).

**Stage B** needs two:

1. **The experiment key**: registry name or Amplitude flag key (resolve the other
   from `assets/types/experiments.ts`).
1. **The Stage A audit**, in any form: a Notion link, a pasted table, a
   markdown file. If none exists, say the loop cannot close against a spec,
   run Stage A first, and then verify against it. Never inventory the code
   first and call that the audit.

Parse the audit into the expected-event list (event name, action, trigger,
properties, existing or new, any symmetry warnings), show it, and get a yes
that it matches what the team expects before touching code.

**Stage C** needs the experiment key, the prior audit (none existing means
Stage A, not C), and, in one message, what changed and why: surfaces, user
flow, metric split, events the team now wants, or exposure location.

## How to work

- **Sources of truth, in order:** leadgenie code, then Amplitude taxonomy and
  recent volumes, then the DB entry, then the user. Never a PRD or design doc for
  "what fires today"; a doc may suggest a candidate, only code plus Amplitude
  confirms it.
- **Business questions belong to the engineer and PM**: which metric matters,
  which segment, what counts as "the action". Ask; never guess. When unsure
  which code path is "the" event, show the candidates and let them pick.
- **Before build, treatment does not exist yet.** "Unknown until built" is a
  valid answer; use it rather than inferring what treatment code will send.
- **After build, code answers "what fires"; the audit answers "what should".**
  A disagreement is a finding to report, then to resolve with the user: fix the
  code, or bring the audit up to date. Never resolve it silently in either
  direction.
- **Never invent instrumentation.** An event's name, trigger, and properties
  come from the audit row; anything the audit did not spec is defined with the
  user first or logged as deferred.
- **"Lands" means Amplitude, not code.** An event confirmed only in code is
  "built, not yet verified landing": a named state, not a pass. Before launch,
  staging is the best obtainable evidence; say so.

## Stage A: Discovery audit (nothing in code yet)

Goal: a verdict on whether the experiment can be measured today, and the
inventory the build and Stage B work from.

1. **Sanity-check the metric split.** Confirm it maps to the experiment design
   and name the event each metric is computed from. Flag mismatches as
   questions for the PM; never redesign the split.
1. **Derive the event inventory.** From the treatment surfaces and the PM's
   learnings, list every interaction the experiment UI can produce (clicks,
   form submissions, dialog opens and closes, redirects) plus the events behind
   the reused metrics and the properties they need. Propose candidate names;
   show the list; continue only after the user confirms or corrects.
1. **Inventory control-side events in code.** For each candidate: file,
   function, the condition it is gated on, the properties attached, the funnel
   moment (page mount, user action, API response).
1. **Confirm in Amplitude.** For each event found in code: does it exist in the
   taxonomy, what is its 30-day volume on the target audience, which properties
   actually arrive vs what code sends. Flag code-but-no-volume and
   volume-but-no-code. Go to Snowflake when Amplitude volume is thin or a
   governed definition exists.
1. **Symmetry-risk pass.** For every *existing* event: is it gated on UI, state,
   or routing that treatment changes? If yes, record the specific condition.
   This is the most valuable output of the audit; do not rush it.
1. **Property check.** For each event, confirm the properties pre-analysis's
   segment cuts need (team segment, plan, …) are present in Amplitude.
1. **Exposure event.** If the flag exists, read its exposure event from
   Amplitude and record it; it is the denominator of every per-exposed metric.
   If not, record the planned location from input 5 as unknown until built.
1. **Taxonomy recommendation.** Apply `references/experiment-taxonomy.md` to
   propose the experiment-scoped properties each event should carry. Every row
   is a proposal DS confirms.
1. **Hand over** the Stage A output (below), then offer the exports.

Working vocabulary, for your own bookkeeping: `exists` (code **plus** Amplitude,
never a doc) · `missing-property` · `new-for-treatment` · `unknown-until-built` ·
`symmetry-risk`. Treatment-only events are only ever new or unknown until built.
These words do not appear on the page; `references/audit-doc-format.md` maps
them onto the two inventory statuses and plain sentences.

## Stage B: verify the build against the audit

Goal: every audited event found in code and Amplitude, classified with
evidence, gaps built on approval, and the audit brought up to date.

1. **Locate the built code.** Registry entry, every variant read site, the
   exposure call, and every analytics call on the experiment's surfaces, with
   the mechanics file's grep starters. Collect *extra* events the audit never
   listed too.
1. **Classify each expected event** per `references/verification-checks.md`:
   built as specced; drifted (name, trigger, or property differs; say exactly
   what); missing; plus extra for unaudited events found in code. Evidence is
   file and line, always.
1. **Arm symmetry in code.** For each event: does it fire under the same
   conditions for control and treatment, or exactly as the audit intends? An
   analytics call gated on the variant is a finding unless the audit specced it
   that way. Verify that the fix for every symmetry risk Stage A flagged
   actually landed.
1. **Landing in Amplitude.** Per event: exists in the taxonomy, volume arriving
   (staging before launch, prod once live), properties arriving as sent. If the
   experiment is live, split volume by arm via the exposure property. Record
   the catalog link for every event that exists.
1. **Fix the gaps.** For each missing or drifted event: build the change from
   the audit row (name, trigger, properties, call site per repo conventions),
   show the diff, apply on a yes, and run the repo's targeted checks. An event
   with no audit row is specced with the user first or deferred.
1. **Bring the audit up to date.** For every row where the build is right but
   the audit is stale, prepare the row update: the Amplitude catalog link for
   an event that has now landed, the as-built event name or trigger when the
   audit's wording drifted and the team confirmed the build is what they meant,
   properties as they actually arrive, status from New to Preexisting once it
   fires in both arms. Show the updates verbatim.
1. **Hand over** the Stage B output (below), then offer the draft PR and the
   audit update.

## Stage C: re-audit on scope change

Mid-build changes to surfaces, flow, or metrics are how an audit quietly goes
stale while still looking authoritative.

1. Read the prior audit as the *prior* understanding; ask what changed and why,
   in one message. Diff against it: surfaces and routes, events the team wants,
   metric split, exposure location. Call out changes they did not mention.
1. Re-run the Stage A steps that the change touches, on the changed parts
   only: step 1 when the metric split changed; steps 2 to 6 for new, moved, or
   removed surfaces and events; step 7 when the exposure location changed. A
   new or moved surface re-opens the symmetry question for every event on it.
1. Where code already exists for the changed parts, run Stage B steps 1 to 5 on
   those events only, fixes included.
1. Prepare the audit row updates (added, changed, removed) and show them
   verbatim. Hand over the Stage A chat findings for the changed rows and an
   updated audit file that says what it replaces; where events were checked in
   code, add Stage B's table for them to the chat findings. Stage C produces no
   report file.

## Hand over

**Stage A chat findings**, the same shape every time:

```text
**Analytics audit: <experiment>**
Can we measure this today? <yes / yes, with work / not yet>, because <one line>.

| What the user does | Event | Exists today? | Fires the same in both arms? | Needs |
|---|---|---|---|---|

To build before launch: <list, or "nothing">
Still open: <questions, each tagged engineer / DS / PM>
```

**Audit file** (Stages A and C): fill `assets/analytics-audit-template.md` per
`references/audit-doc-format.md` (verdict, TL;DR, one inventory row per event,
open questions, "How this was checked") and hand it over as
`<experiment>-analytics-audit.md`. The verdict is **yes** only if every event
behind a primary or guardrail metric exists with all required properties and no
symmetry risk; anything else, including "couldn't verify", is **not yet**, with
each blocker in one plain sentence.

**Exports, offered once** (Stages A and C; `references/audit-doc-format.md`,
"Other writes"): fill, or in Stage C update, the team's ERD Analytics Audit
page when they use the ERD template, create a Notion page from the template if
they want one, or update the DB entry's Metrics tables. In Stage C this is the
one offer; the row updates go wherever the audit lives, shown before and after. Show every write verbatim and send only on a
yes. "Just the file" is a complete answer. Never edit the template page.

**Stage B chat verdict**, the same shape every time:

```text
**Build vs audit: <experiment>**
Does the build match the audit? <yes / yes, after N fixes / no, N gaps>, because <one line>.

| What the user does | Event | vs audit | Both arms? | Landing | Amplitude |
|---|---|---|---|---|---|

Fixed this run: <list, or "nothing needed">
Deferred: <list with owners, or "nothing">
Audit rows to update: <count, or "none">
Still open: <questions, each tagged engineer / DS / PM>
```

**Report file** (Stage B): fill `assets/verification-report-template.md` and
hand it over as `<experiment>-analytics-verification.md`.

**Fixes as a draft PR** (Stages B and C). After applying approved fixes, ask:
"want me to open a draft PR in leadgenie with these fixes?" On a yes, commit on
the experiment's branch if the user is on it, otherwise on
`<user>/<experiment>-analytics-fixes`, and open or update the PR with
`gh pr create --draft`, linking the report (Stage B) or the updated audit
(Stage C). Never commit or push without that yes.

**Audit update, offered once** (Stage B). Ask whether to write the row
updates from step 6 into the audit where it lives: the ERD Analytics Audit page's
Experiment Events rows, or the markdown file. Show each row before and after;
write only on a yes. Never edit the ERD template page. "Leave the audit as is"
is a complete answer; the report then carries the updates.

## Review

The conventions' silent review, plus:

- Every "exists" row (Stage A) and every classification (Stage B) has code
  evidence (file:line), re-opened and confirmed. Every "exists" row and every
  landing claim has an Amplitude pull with project and date and a catalog link.
- Every existing event was tested for symmetry risk against the treatment
  surfaces, and both arms were traced for every built event; "not checked" is
  not a valid blank.
- No treatment-only event is marked as existing; no event is marked as landing
  from code alone. Items that cannot be verified until launch are named as
  such, not passed.
- Properties for every pre-analysis segment cut were checked, per event.
- Every applied change was approved first, matches an audit row or a
  user-confirmed spec, and the repo's checks ran on it.
- Every event that exists in Amplitude has a working catalog link in the file
  (open or spot-check at least one).
- The verdict matches the rows; "not yet" names every blocker. Audit row
  updates were shown before and after, and nothing was written without a yes.
- The page reads human: no YAML, no working statuses, no grades; shaky findings
  are questions with how to resolve them.

## Never

- Mark an event as existing from a doc, or as landing from code alone.
- Reconstruct the metric split when pre-analysis has not run.
- Guess a business question (metric, segment, what counts as the action), or
  redesign the team's metric split.
- Invent an event's name, trigger, or properties.
- Decide what to track while verifying (Stages B and C); an event with no audit
  row gets one from the user first, or is deferred.
- Apply, commit, or push a change that was not shown and approved.
- Assume a team's Notion format, or write to the audit, Notion, or GitHub
  without a verbatim yes.
- Review exposure placement, size metrics, or interpret results.

## Reference files

Paths relative to this skill's folder.

- `references/leadgenie-analytics-mechanics.md`: how events fire in this repo,
  grep starters, Amplitude and Snowflake lookups (Stage A steps 3, 4, and 7;
  Stage B steps 1 and 4; Stage C throughout).
- `references/audit-doc-format.md`: the audit page layout, the inventory
  columns, the verdict rule, the status mapping, the offered exports (Stages A
  and C; Stage B reads its rows).
- `references/experiment-taxonomy.md`: experiment-scoped properties from prior
  audits, with the open DS question on variant stamping (Stage A, step 8).
- `references/verification-checks.md`: classification definitions, arm-symmetry
  code patterns, landing-check recipes, catalog link format, how to build a
  missing event (Stages B and C).
- `assets/analytics-audit-template.md`: the audit file Stages A and C deliver,
  and the skeleton for a Notion export.
- `assets/verification-report-template.md`: the report file Stage B delivers.
