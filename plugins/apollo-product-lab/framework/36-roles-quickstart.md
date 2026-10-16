# 36 — Quickstart by role: product, design, engineering, QA

One page per person who is not the harness maintainer. Everything below runs inside Claude Code in
`apolloio/leadgenie`; the same files run in Codex with the differences in doc 35.

## Before anything: run `/harness-onboard`

First time, and while the plugin is still a PR: the six-step onboarding page in Notion covers launch, install from the branch, the eight questions with sample answers, the second family, connectors, and the first command, for Claude Code and Codex: https://app.notion.com/p/3e3ab2b3b49681ee86eefd10d1755937

It asks your persona, detects which connectors and tools you have, walks you through the missing
ones (doc 39), writes `~/.claude/harness-profile.yml`, and shows your first command. Ten minutes.

## Then: is the initiative set up?

`ls .ai/<initiative>/` should show `document-graph.yml`, `domain/`, `runs/`, `harness-manifest.md`.
If not, ask the harness maintainer to run `/product-harness-init <initiative>`. It emits the domain
agents, the knowledge files, the Design source block, and the model routing for the initiative; it
runs nothing.

## End to end (one person, whole pod)

Choose this in onboarding when you are not a single role: a founder-style PM, a tech lead running a small
feature alone, or anyone evaluating the framework. You get every persona's first command, own every gate
yourself, and the council still runs with all lenses so your own work is never reviewed only by you.

## You do not pick the stages; you give a statement

After onboarding, `/harness-intake "<one sentence of what you want>"` decides what to produce for your role:
a PM's sentence becomes research, a competitive comparison and an AI-opportunity scan (where a suggestion,
score or assistant would shorten the journey, each with a now / next / never question, doc 42), a platform scan when the capability has siblings elsewhere in Apollo (doc 47), then a PRD; a designer's becomes a prototype
plan and a storyboard review; an engineer's becomes an ERD or plan council; QA's becomes a test plan. It
sizes the work, lists the artifacts that exist and those that are missing, names the compliance and legal
checks that apply, reads what already exists (PRD, design, ERD) so it asks only the decisions those leave open,
then starts the local steps, in parallel where they are independent, and reports progress every 5 to 10 minutes (doc 49).

## Tracker and grill defaults

Onboarding recommends one update tracker. Intake must complete every listed grill decision before the
run advances. Facts in documents or code are looked up, not asked (doc 53).

| Role | Default tracker | Required grill decisions |
|---|---|---|
| PM | both | problem and who has it; success metric; scope out; launch gate |
| Designer | Notion | user flows covered; states (empty/loading/error/permission); design-system components; open copy |
| Engineer | Jira | data model and ownership; failure and retry behaviour; rollout and flag; observability; migration/backfill |
| QA | Jira | acceptance criteria; test environments and data; regression scope |
| EM | both | owners per slice; timeline and checkpoints; cross-team dependencies; risk |
| Researcher | Notion | question; sources; decision the research serves |
| End to end | both | the PM, engineer and QA items above |

## Who reviews your work, and the brief you get first

Every artifact is read by the roles that have to live with it (doc 34 §2b), on top of your own peer:

| You write | Reviewed by | Your peer | Brief you get before you start |
|---|---|---|---|
| PRD | design, engineering feasibility, UX research | the product lens | journeys and states design needs, expensive requirements and existing models from engineering, which user claims have evidence |
| Design | product, peer design, UX research, engineering feasibility | the peer design lens | requirements and acceptance criteria, components and data that exist, evidence on the user's task |
| ERD, plan or PR | product, design, QA | architecture and the backend/frontend reviewers | requirements and priority, states and copy to carry, invariants that need a negative test |

A change the router skips for demonstrated low risk (doc 43 §6) gets no council, so none of this runs; file
count is not the test.

## Product manager

1. Put the PRD where the harness can read it (Notion or a repo path) and add it to `document-graph.yml`.
1. `/harness-council <initiative> prd "<page or path>"` → a memo with gaps (metrics without numbers,
   missing acceptance criteria, contradictions with the constraint register), options with a
   recommendation, and competitor evidence with sources and dates.
1. When the capability exists elsewhere in Apollo, the memo also carries platform rows (doc 47): parity gaps and
   shared flows as scope lines, each with a platformize now / do locally and record / never question you answer.
1. You own gate **G2a** (worth building, falsifiable business case). Decide in the memo's options table;
   the harness records your choice with alternatives rejected.
1. What you will not get: a number the harness invented and passed as fact. Invented numbers are marked
   `[ASSERTED]`.

## UX designer

You can work from the terminal, the Desktop Code tab, claude.ai/code or claude.ai chat (doc 45). You
share a Figma file, a Fabric Studio prototype or a Claude Design project; the harness never asks you for
a PR or a staging link. You may start from only a thought or a PRD: `/harness-intake "<the thought>"`
runs, in order, competitive analysis, the AI lens (where AI can shorten the journey), a reuse audit
against Fabric (`@apolloio/fabric-core` docs, `@apolloio/fabric`, Storybook) and the platform lens
(doc 47: the same flow elsewhere in Apollo, proposed as one reusable flow with UX-parity rows per entry point), then the review panel:
research, product, engineering feasibility, UX and a cross-family adversary where one is reachable.

1. Build in **Fabric Studio** (`apolloio/fabric-studio`, one `prototype/{you}-{initiative}` branch,
   README setup once). Figma stays the source of truth; the branch is the workbench.
1. Tell the harness the branch; it goes in the frontend knowledge file's Design source block.
1. `/harness-council <initiative> design "<branch>"` → pass/fail against required states and constrained
   copy, a port list for engineering, and the places where a constraint overrides the design.
1. You own gate **G2b** (which surviving option). The harness never ranks survivors on taste.
1. When you change the prototype, the frontend agent diffs it against production and sends you the gap
   list; you never redraw from an engineer's memory.

## Engineer

1. `/harness-snapshot read <initiative> <run>` at the start of every session; the conversation is not the record.
1. Before an ERD or plan goes to review: `/harness-council <initiative> erd "<path>"` → the roadmap lens
   (provider-neutral names, every table justified, state over table, one model) and the scale posture
   table. Fix shape before indexes. When the model or service has a sibling backend, the memo carries shared-backend
   rows (doc 47: reuse or extract, pack boundary, owning team, ERD delta) for you and the owning team to answer.
1. Build with the initiative's `<x>-backend` / `<x>-frontend` agents; the preventive gates are in their
   knowledge files (runtime verify, build to PRD, preflight new artifact types, CI rules).
1. Before a PR leaves draft: `/harness-council <initiative> pr <number>`.
1. You own gates **G3** (plan) and **G4a** (code). Sensitive-file approvals and policy-bot are people.

## QA

1. The test plan is derived: acceptance criteria (Stage C) and the required-state list (Stage D) are the
   inputs. If either is missing, that is a finding, not something to invent.
1. `/harness-council <initiative> verify "<preview url>"` → the derived suite, a negative test per
   invariant (what must *not* happen), and bug records routed to the stage that produced the defect.
1. You own gate **G5a**. Run the negative tests against the live preview, not against a mock.

## Recording a decision

A council memo ends with options; it is not a decision. When you choose, run
`/harness-council <initiative> decide <memo-slug> <option> "<your name>" "<why>"`. That writes the
decision record (option, who, rationale, the input hashes it rests on, remaining conditions, gate
status) and the ledger event; downstream stages read that file, never the chat. If an input changes
afterwards the decision reopens for that scope.

## Skills each role already has

Doc [38](./38-skill-reuse-map.md) is the index. The short version:

- **PM**: `/apollo-rnd:prd-one-pager` (author a PRD, Stage C), `feature-to-metrics-spec`, `product-reviewer` lens,
  `/apollo-analytics:*` for governed numbers, `product-ship-post` at launch.
- **Designer**: `/apollo-rnd:setup-fabric-studio` once, then the Fabric Studio branch; review all pages at once on the
  branch's `/storyboard`; the gap list against production comes from `/design-diff <initiative>`.
- **Engineer**: `tdd-loop`, `ci-speed-run`, `backend-quality`/`frontend-quality`, `deslop`, `codeowners-split-prs`
  then `ship-it`, `code-review` for the pr council, `/codex:review` as the second family, `make-it-work` when stuck.
- **QA**: `feature-qa-wizard` from the D snapshot, `qa-steps-for-eng`/`-non-eng`, `playwright-cli`/`playwright-trace`
  against the preview, `bug-bash-generator`.

## Everyone

- Decisions come as options with a recommendation; you choose. If you receive an open question instead,
  that is a harness defect: say so.
- Every stage leaves a snapshot in `runs/`; if a mirror you read (Notion, a PR) is stale, the snapshot's
  Mirrors table will say `updated: no`, and the stage is not done.
