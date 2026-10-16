# 43: The learning loop, reuse-first design, owning teams, and review defaults

> Decision 2026-10-06. The harness passed its own gates on work that a human reviewer then sent
> back for a different approach. This doc makes the harness learn from each of those misses,
> check the existing code path and the owning team before it designs, and get one review from a
> second model family on medium and high work. Every rule here is input to a human gate. None of
> it approves anything.

Terms used below:

- **Harness artifact**: anything the harness produced and a person reviews. A PRD, an ERD (entity
  relationship design, the data model), a design, a plan, a PR, or a Notion page made from one.
- **Gate**: a point where a person or a check decides whether work may go on (doc 12).
- **Lens**: one reviewer viewpoint in the council, such as product, backend or adversary (doc 34).
- **Model family**: the company whose model did the work. Anthropic (Claude) and OpenAI (GPT) are
  two families. A reviewer from the same family as the author tends to share its blind spots.
- **Cross-family review**: a review by a model from a different family than the one that wrote
  the artifact (doc 32, doc 34 §3).

## 1. Why

Three cases drove this.

- **E1, a backend PR rejected after the harness passed it.** An engineer used the harness end to
  end on an enhancement to an existing email feature (fallback text for template tags that have no
  value). The frontend PR merged. A senior reviewer rejected the backend PR, and it was rebuilt.
  The reviewer said the change fought the existing flow: the send path already substitutes every
  tag in one pass, and the change added more passes and a lot of link rewriting at send time. The
  reviewer asked to let substitution finish as usual and only fill the unresolved tags. Fallbacks
  should be checked when the template is saved, not at send time. There were too many options. The
  change also replaced invalid link destinations with a placeholder, which can hurt how mailbox
  providers judge Apollo's sending domains. Email deliverability is owned by another team. A CI
  check flagged that team's file, but only after the code was written. The engineer said they did
  not know the backend flow well and followed the harness. The area had no harness folder; it was
  an existing product being changed.
- **E2, architecture rework on a harness-built ERD.** A new product's data model passed its own
  council and a cross-family review. An EM and a staff engineer then changed it a lot. Every change
  was Apollo platform knowledge the architecture stage did not apply: existing list and contact
  change hooks, short background jobs, how a new database collection gets its indexes, database
  index filter limits, and how secrets are read.
- **E3, slow sessions for a designer.** A designer reported that small design edits were slow and
  that the model did tasks they did not expect. Not confirmed as the harness. The plugin's session
  hook, the snapshot skill's wide trigger and repo commands that assume a checkout are the likely
  parts (section 10).

A fourth gap, E4: published pages had to be rewritten into plain language by hand. Section 9
makes that a check.

## 2. Escapes: how the harness learns from a miss

### 2.1 What an escape is

An **escape** is a finding by a person or a bot on a harness artifact, after a gate passed, that
changes the approach or finds a defect. Examples: a reviewer asks for a different design; a review
bot finds a secret read from the environment; a staff engineer replaces a table.

These are not escapes:

- a nit or style comment;
- a **changed requirement**: the person changed what they want. It is recorded, in a separate
  list, because it says nothing about whether a gate worked.

### 2.2 Capture is automatic

Nobody should have to remember to report a miss.

1. **Stamp on publish.** When the harness publishes an artifact it writes its run and artifact ids
   on it:
   - PR body: one line, `Harness run: <initiative>/<run-id>`, written by the step in doc 20 §8c and
     checked with `gh pr view --json body`.
   - Notion page: a footer line, `Harness run: <initiative>/<run-id> · artifact: <snapshot file name>`.
     The file name is an id, not a path; the Notion page still carries no local paths.
1. **Scan for candidates.** `/harness-escape scan <initiative>` finds stamped PRs and pages and
   pulls, since the last scan: review comments from people and bots, reviews that request changes,
   and later revisions of the artifact. It writes candidates to
   `.ai/<initiative>/escapes/candidates.md`.
1. **When the scan runs.** At the start of every `harness-intake` and `harness-snapshot read` for
   the same initiative, after the team sync, and by hand. It is cheap: it looks only at stamped PRs
   updated since the last scan, at most 20 per scan. It pages through comments, drops duplicates by
   source id, keeps unfinished sources for the next scan, and moves a source's cursor only past data
   it actually collected. It writes files only when something changed; those changes are pushed with
   the run's record at the next boundary.

### 2.3 Adjudication is human

Collection never edits a rule, a lens or a check. A named **maintainer**, the initiative's EM by
default and recorded in `harness-manifest.md` as `escape_maintainer:`, rules on each candidate:

- `escape`: it changed the approach or found a defect;
- `not`: not an escape (a nit, a misread, a duplicate);
- `changed-requirement`: the ask changed.

For reviewer rules, the adjudicated record enters `framework/rules/registry.yml` as a `candidate` with
the comment URL as its source. That registry is the learning loop's state. Promotion and retirement use
the replay and paired-probe rules in doc 54. The learner only writes a proposal; a person changes the
registry and reviewer prompt.

A miss counts against a gate only if that gate's declared job covered it **and** the gate had the
evidence at the time. A gate cannot miss what nobody gave it.

### 2.4 Routing

An adjudicated escape is routed like a rejection (`agents/product-orchestrator.md`, Stage H): back
to the stage that owned the defect, not the stage that found it. It gets one Stage H ledger event.

### 2.5 The fix, and when it counts as proven

`/harness-escape fix <escape-id>` writes the fix: a candidate registry row for a reviewer rule, a row in
`platform-rules.md`, a lens checklist row, or an executable check, plus an eval fixture in
`framework/eval/escapes/`.

A fix is **replay-verified** only when all of these hold:

- the fixture archives the original artifact bytes, the repo revision, the evidence the gate had,
  the instructions, and the model and tool settings;
- the new check flags the defective case, does **not** flag its corrected version, and flags one
  held-out variant it was not written against;
- an executable check runs deterministically; a model check runs 3 times and reports how many runs
  found the defect and how many raised false alarms.

If the originals were not archived, the record says **retrospective case, not replay**. It is
still useful as a lesson. It is not evidence that the fix works.

### 2.6 Metrics

Reported monthly by `/harness-escape report`: escapes per run by stage, false alarms per check,
and rework PRs (a PR closed and rebuilt, or reopened for an approach change).

## 3. Platform rules

`framework/platform-rules.md` holds Apollo platform facts that a design must respect. Each row has:
the rule, when it applies, exceptions, an authoritative source (code or a canonical doc, never an
incident alone), the executable check if one exists, an owner, and a review date.

The architecture, backend and db-perf lenses check every row that applies and mark it `checked`,
`failed`, `unverified` or `not applicable`, with evidence. Reading the file is not a check.

Governance:

- The owning domain team approves when a rule applies.
- The harness maintainer removes duplicates and prunes stale rows every quarter.
- Prefer a link to an executable check or a canonical doc over a copied rule. A copied rule goes
  stale; a check does not.
- Choices that were right for one incident (status fields, call-id rows, a search snapshot) are
  worked examples, kept in their own section, not rules.

## 4. Current behaviour map, and reuse first

Before any design that changes existing behaviour, the architecture or backend lens writes a
**current behaviour map**:

1. Trace the real path end to end, citing functions and the specs that cover them. For E1 that is:
   template save, then tag substitution, then the final email output.
1. Explain every pass, option or call the design adds, and why the existing path cannot do it.
1. Put validation of author-supplied configuration at save time, unless there is a stated reason
   not to. Keep the protections the existing path already applies to resolved values (for E1: the
   checks on links that came from real contact data); a new path must not drop them.
1. List the regression cases. For E1: unresolved tags, and invalid link destinations.
1. "No existing path" is allowed only with the list of what was searched (files, symbols, specs).

Lens evidence is produced, not claimed. "Read the rules" without the rows filled is a `failed` row.

## 5. The owning team

Lenses are chosen by what the change affects, not by whether users can see it:

| The change affects | Lens added |
|---|---|
| backend code | backend |
| a query, a schema or an index | db-perf |
| a surface in `surface-owners.yml` owned by a team other than the author's | owning-team lens, loaded with that team's rules |

How ownership is detected:

- At intake, against the behaviour map, and again against the real diff before review.
- With the repo's own matching, not a hand-written glob: `ApolloDevTeam.team_to_sensitive_files_hash`
  in `packs/util/lib/apollo_dev_team.rb` (what CI runs), `apollo-dev-teams.yml` and
  `surface-owners.yml`.
- Behaviour that is sensitive but matches no file still needs an owner's assessment. E1's link
  rewriting is an example: the risk is to domain reputation, which `surface-owners.yml` gives to
  Deliverability.

The owner's answer is recorded before the disputed behaviour is coded: `approved`, `changed` or
`not needed`, with who and when. Posting a design in a channel is not a review.

## 6. Sizing, and cross-family review by default

Classify the whole change, including its related PRs. Splitting work into small PRs does not make
it small. The highest trigger wins.

| Size | Any one of these |
|---|---|
| **High** | a new product; a new data class; consent; money; auth or permissions; a contract between teams; deletion of customer data |
| **Medium** | any other behaviour change; a new endpoint; a new background job; a schema or index change; a change in a surface owned by a team other than the author's |
| **Low** | only when tests show the output is unchanged, and no trigger above applies |

Facts that are not known yet are listed, and the change is medium until they are. Reclassify
against the actual diff before review.

A **design change** (a new ERD, a change to an ERD's design content, an architecture decision, or a PR
change that alters the design) gets an Astra xhigh review whatever its size, bound to the design's
`design_sha`, plus an Anthropic reading when the recorded author family is OpenAI (doc 17 §6.3). Sizing below decides the
code review, not that one.

For **medium and high** work:

- one consolidated cross-family review of the design artifact, and one of the PR diff, before
  human review. One review per artifact, not one per lens.
- The reviewer is the adversary the council already runs, not an extra one: for the design artifact,
  Astra (OpenAI gpt-6-astra at extra-high effort) through Codex or the shunt adversary
  (`council-adversary`); for the PR diff, the existing PR adversary (`/codex:adversarial-review`, the
  council's pr kind).
- Independence is decided from the artifact's recorded author family and the reviewer's served
  model, as in `harness-council` step 3b. If no second family is reachable, the gate record says
  so.
- Record tokens, minutes and prompt characters per review, so the cost is measured, not guessed.
- At most two passes per artifact, the second on the delta only; blockers after pass 2 go to the human
  with options, not to a third pass (doc 46 §4, §5).
- The review is advisory input to the human gate. It never approves.

## 7. Enhancements on existing products

Most work changes a product that already exists. Intake and onboarding ask one question:

1. a new product;
1. a feature inside an existing harness initiative (it has a `.ai/<initiative>/` folder);
1. a change to an existing Apollo product that has no harness folder.

For case 3, intake bootstraps a light initiative. Its first snapshot is the current behaviour map
(section 4) plus the owners (section 5). It creates no new agents.

Lenses for an enhancement, chosen by what it touches (section 5):

- Product and UX lenses when users will see different behaviour.
- One combined competitor and AI opportunity page, one page at most, only when user-visible
  behaviour changes.
- The research lens only when the area has no prior research.
- The adversary always, for medium and high work.

## 8. Uncertainty and accountability

- Every gate row is one of: `checked`, `failed`, `unverified`, `not applicable`. A row nobody could
  check is `unverified`, never `checked`.
- A named engineer owns the approach. The harness advises them.
- If the engineer's own knowledge disagrees with the harness, the harness reopens the
  investigation. It does not repeat its answer louder.
- Models agreeing with each other is not approval.

## 9. Plain language check

Every human-facing output (a Notion page, a PR description, a memo, a Slack draft) passes one
comprehension check before it is published. A fresh agent that saw no chat reads only the page and
answers three questions:

1. What was decided or found?
1. What follows from it?
1. What must the reader do?

If it cannot answer from the page alone, rewrite and check again. Zero findings is a valid result.
Keep the technical meaning; plain does not mean vague.

Writing rules: define a term the first time it appears; short sentences; no internal name without
saying what it is; units on every number; no local file paths on a page a reader opens outside the
repo.

## 10. Sessions without a repo, and quiet sessions

Many people run the plugin from Claude Desktop, installed from a zip, with no repo checkout and no
shunt. For them:

- **Repo state.** The hook and every skill first resolve the repo root with
  `git rev-parse --show-toplevel`, so a session started in a subfolder (for example `packs/`) still
  finds the record. All `.ai/` paths are relative to that root. There are three states:
  - **no git repo**: no-repo mode. Repo, git, gh and `.ai` steps are skipped entirely, said in one
    line. Nothing is tried and left to fail.
  - **a git repo with no `.ai/` at its root**: the harness is not initialised here. Intake or
    `product-harness-init` may bootstrap `<root>/.ai/`; other skills say so and write nothing.
  - **a git repo with `.ai/` at its root**: normal operation.
- The session hook makes bounded local reads only. It never pulls, never asks the model to do work,
  and probes shunt for at most one second, only for personas that write code.
- Snapshots and Notion publishing happen only inside an explicit harness run (a run id is bound and
  the work is a harness stage). A Figma edit or a storyboard update outside a run writes nothing.
- A zip install does not update itself. The hook prints the loaded version and build (the plugin
  checkout's commit, or the `BUILD` file the zip build writes); the README says how to update.

## Seed escapes

E1 and E2 are recorded as retrospective cases in `eval/escapes/`. Their originals were not archived,
so they are lessons, not replays.
