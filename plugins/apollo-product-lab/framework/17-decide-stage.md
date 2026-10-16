# 17 — DECIDE, in depth

> Deep dive on the second box of [10-harness-overview](./10-harness-overview.md). Stages C (Specify), D (Design) and E (Architecture review).
> **Status: draft for review. Nothing binding.**

## 1. What DECIDE answers

FIND establishes what is true. DECIDE commits to **what we will build and how**, and it is the last point where changing your mind is cheap.

Three questions, three stages, one gate each:

| Question | Stage | Gate |
|---|---|---|
| What are we building, for whom, and why is it worth it? | C — Specify | G2a |
| What does it look like, and which option survives the constraints? | D — Design | G2b |
| How is it built, and what does that make hard later? | E — Architecture review | G3 |

## 2. C and D run in parallel, not in sequence

The instinct is PRD → design. That is wrong here for a specific reason: **a PRD written without design input makes UI assumptions silently**, and the reference instance shows exactly this — a PRD describing a picker over existing platform lists, a flow that turned out to be prohibited, with no design ever validated against it.

So both consume FIND's output directly, and both work against **the same extracted invariants**. They are allowed to diverge; the Stage E arbiter reconciles. What keeps divergence bounded is the shared constraint set, not sequencing.

The cost of parallel is one class of rework: design exploring a direction Specify later rules out of scope. That is cheaper than the alternative, because design rework is hours and a wrong PRD is weeks.

## 2.1 Somebody has to write it — the authoring step

**Cold start, no PRD (resolved 2026-09-21):** the order is fixed. Stage B first: research over the
internal record (Glean), the codebase, and the web, plus the competitive lens (how the two or three
named competitors solve it, pros and cons, options), then the AI opportunity lens (doc 42: where a
suggestion, score, explanation, generator, assistant or automation would shorten the journey, with a now /
next version / never question per row), then the platform lens when the intake's sibling check found the
same or a near-same capability elsewhere in Apollo (doc 47: feature parity, shared flow and shared backend
rows, each with a platformize now / do locally and record / never question). Only then does `/apollo-rnd:prd-one-pager` author,
with those snapshots as its input, so the PRD's problem statement is evidence-checked and its options
name the competitor approaches it rejected, and its scope says which AI assists are in this version and
which are deferred with a reason. A PM who arrives with only a sentence gets research, not a
form. `harness-intake` runs this order automatically.

An earlier draft of this document described DECIDE almost entirely as checking. That was a real omission: **if nothing has been written yet, there is nothing to check.** Both C and D need an explicit *produce* step, and both take the same two modes FIND does.

| | If the artifact exists | If it does not |
|---|---|---|
| Stage C | Gap-fill: add the missing sections, reconcile against FIND | **Author the PRD from scratch** |
| Stage D | Evaluate the existing options against constraints | **Generate options** |

### Stage C, in running order

Four analysts, then an author, then an arbiter. The order matters: the author needs the analysis, and the arbiter needs something to reconcile.

| Step | Who | Produces |
|---|---|---|
| 1 (parallel, read-only) | Competitive position | Feature matrix vs named competitors, differentiation claim, every claim cited |
| 1 | Business case | ROI model: inputs, falsifiable assumptions, sensitivity |
| 1 | **Measurement** | **Success metrics with actual numbers, and how each is measured.** Wraps the existing `feature-to-metrics-spec` skill |
| 1 | Scope slicing | MVP / v1 / v2 boundaries against the dependency graph and estimate |
| 2 | **PRD author** | **The PRD**: problem, target user, success metrics, non-goals, acceptance criteria, open questions. Consumes all four analyst outputs and the FIND problem statement |
| 3 | Arbiter | One recommendation, recorded dissent, and what it overrode |

**Measurement was missing and it matters.** The PRD schema requires "success metrics with numbers," but no agent was producing them — so the requirement was unsatisfiable by construction. `feature-to-metrics-spec` already exists and does exactly this; compose it rather than writing a fifth analyst.

**`prd-one-pager` formats; it does not author.** It converts existing content into PRD shape. The author is what produces the content. Treating the formatter as the authoring step was the original error.

### Stage D, in running order

| Step | Who | Produces |
|---|---|---|
| 1 | **Read Figma** | Existing components, tokens, screens, code mappings. Always first — see §3 |
| 2 | **Design generator** | N options as code, built from existing components rather than invented ones |
| 3 (parallel) | Flow coverage, constraint compliance, state completeness, design-system conformance, usability validation | Pass/fail/unknown per option, with evidence |
| 4 | Arbiter | Which options survive. **Does not rank them** |

The generator is the piece that was missing. Without it, Stage D on a greenfield feature has five checkers and nothing to check.

## 3. Design tooling: Figma is the source of truth, Fabric Studio is the default workbench

**Workbench choice (2026-09-21).** Fabric Studio is the default because a prototype there is real
`@apolloio/fabric-core` code and can be diffed against production. A designer may choose **Claude Design**
instead (faster to explore, comments built in, but it imitates Fabric and cannot be diffed as code) or work
**Figma-only** through the Figma MCP. Onboarding records `design_workbench` in the profile; the Design
source block names it; `design-diff` runs code-to-code only for Fabric Studio and falls back to a
screenshot-and-state review for the other two. Whatever the workbench, the **Figma MCP connector is
required for the designer persona**: Figma holds the components, tokens and Code Connect map the review
reads first.

Updated 2026-09-18. The first version of this section named Claude Design as the workbench. The
Ads M1 pilot replaced it with **Fabric Studio** (`apolloio/fabric-studio`) and the harness adopts
that for every initiative, not only Ads. The order below is the part that must not change.

### Review the whole flow, then diff it

Every Fabric Studio branch has a **Storyboard** (`/storyboard`, grid button in the studio bar; PR
#348): every page of the prototype rendered live on one screen, the way Figma shows a file's pages.
Stage D reviews read it before commenting on a single screen. Reviewers comment **in the studio**, Figma-style (fabric-studio#348, 2026-09-20): the speech-bubble button pins a thread to the component under the click, anchored to the same build-time stamp Inspect uses, with reply and resolve. Threads persist in the browser and leave by share link, Markdown, or a committed `src/prototypes/<id>/comments.json` that ships with the preview. The Storyboard shows open-comment counts per page and links each page to its `figma` frame; Figma stays the design source of truth, the studio is where the review happens. The gap between prototype and
production is produced by the `design-diff` skill: a deterministic inventory (routes, components,
fabric-core imports, copy) and then one of five buckets per gap, with the constraint register
winning over both sides. The gap list is the D→F handoff and the designer's feedback in one file.

### Read Figma first, always

Figma holds the company's accumulated design: components, variables and tokens, existing screens,
and Code Connect mappings from Figma components to real code components. That is design's
equivalent of domain memory. An agent that generates a design without reading Figma first invents
a component that already exists, uses a colour that is not a token, and proposes a pattern the team
abandoned two quarters ago.

### Then generate variants as code, in Fabric Studio

Design-as-code makes constraint checking deterministic: you can grep a prototype for a pre-checked
attribute, prohibited copy, or a missing required state. That argument was always right; the tool
was wrong. Claude Design produced self-contained HTML that *imitated* Fabric, so every survivor had
to be re-derived by an engineer and the compliance grep ran against markup nobody would ship.

Fabric Studio is a scaffolded Vite + React app pre-wired with `@apolloio/fabric-core` (the same
package leadgenie ships) and the Figma connector. A prototype there is real Fabric code:

- **Setup** (once per designer or agent host): Apollo VPN, Node 22, GitHub access, Claude Code with
  the Figma connector. Clone `https://github.com/apolloio/fabric-studio.git`; the README's paste-in
  prompt does the rest.
- **One branch per prototype**: `prototype/{owner}-{initiative}`; `master` is the untouched scaffold.
  The module lives at `src/prototypes/{id}/` under the prototype contract
  (`specs/system/prototype-authoring.md`) and a compliance audit runs after every edit.
- **A deployed preview per branch**: `fabric-studio-{branch-slug}.staging.apollo-forge.io` (VPN
  only), so the arbiter's checkers and the human at G2b look at a running thing, not a screenshot.
- **Harness handshake**: the initiative's frontend knowledge file names the branch, the module path
  and the components in scope. That single pointer is what makes "read the prototype first" a
  checkable rule instead of a wish.

What Fabric Studio does not give you, and the frontend surface must fill: `react-intl` messages
(prototypes hard-code strings), state management, real API calls, tests, and any legally
constrained copy the prototype softened. It also runs React 19 while leadgenie runs 18; the port
must avoid 19-only APIs.

### Then write the survivor back to Figma

Designers review in their tool. Push the surviving option back via the Figma write path for human
review and ownership. Fabric Studio's `npm run harvest` promotes a contract-compliant prototype
module into the shared catalog; use it when a prototype should outlive its initiative.

### The discipline that prevents a mess

**Figma is canonical. Prototype branches are the workbench. Production is production.** Three
places, three roles, and the frontend surface's standing rule is prototype-first: before proposing
or coding a UI change, read the prototype component and state what the prototype does, what
production does, and whether the gap is a port, a compliance override (the constraint register
wins), or an engineering constraint. The gap list is the feedback that goes back to the designer;
that loop is how a design change reaches code without an engineer redrawing it from memory.

Never let production drift into a second design source. A prototype that no longer matches
production is a finding for the designer, not a reason to stop reading it.

The earlier blocker (no way to render variants side by side) is gone: every prototype branch has a
preview URL, and Playwright is available to the reviewer agents.

## 4. Eliminating design options without making taste calls

The hard part of Stage D, and where an agent most easily oversteps.

**The rule: agents eliminate on constraints, humans choose on taste among the survivors.** Making that real requires the elimination to be assertion-based rather than opinion-based.

Each constraint becomes a **checkable predicate against a specific element, copy string, or field**. Then the output is a matrix, not a recommendation:

| | Option A | Option B | Option C |
|---|---|---|---|
| Attestation unbundled and pre-unchecked | ✅ | ❌ prechecked | ✅ |
| No "targeting" claim on a signal surface | ✅ | ✅ | ❌ copy says "target these accounts" |
| Required platform fields present | ❌ missing business name | ✅ | ✅ |
| All required states covered | ⚠️ no disconnected state | ✅ | ✅ |

Every cell carries evidence — the element, the string, the missing field. A cell without evidence is `unknown`, never a fail.

Three rules on top:

- **The arbiter reports which options survive. It does not rank survivors.** Ranking is where taste smuggles itself in.
- **If every option fails, that is a finding, not a reason to pick the least-bad.** The constraint set and the options are both suspect and a human decides which.
- **If more than one survives, say so and stop.** The human picks, explicitly, and that choice is recorded as a decision with alternatives-rejected.

## 5. Stage C: the business case is where DECIDE earns its cost

Of the three Stage C specialists, the business case is the one that most often changes the answer — and it is the one most likely to be skipped because it is uncomfortable.

Two disciplines make it useful rather than decorative:

**Assumptions must be falsifiable and separated from inputs.** "SMB customers will adopt this" is not an assumption, it is a hope. "At least 15% of teams with a connected ad account will create one audience in the first 30 days" is an assumption — it names a number that can be wrong.

**The model must reconcile against constraints, not just market size.** On the reference instance the business case had to reconcile an SMB target segment against a platform spend threshold, and separately against a compliance constraint that capped the achievable match rate at the low band. Neither appears in a normal TAM calculation, and both bound the outcome harder than the market does.

This is also where **buyer voice belongs** — Gong, G2, competitive positioning. Not in FIND, where it would contaminate the problem statement with the concerns of people who are not the users.

## 6. Stage E: making the panel not a rubber stamp

Four reviewers checking **different things**, which is what makes them not four opinions on one question:

| Reviewer | Checks |
|---|---|
| Seam | Does the abstraction hold for the second and third consumer, or only the first? |
| Data model | Shard key, index coverage, append-only vs mutable, migration shape, **and the roadmap lens below** |
| Failure mode | Partial failure, retry semantics, revoked credentials, mid-run state change |
| Blast radius | Migrations, reindexes, T0 collections, cross-pack reach |
| **Infra (be-platform lens)** | The Load model (§6.2) row by row against `apollo-infra-patterns.md` IP1 to IP18: per-batch query and write counts, fan-out, job args, Redis as record, status filters on claims, per-team concurrency, shard keys, an index reader per index, and a reader per field. Agent `infra-lens` on gpt-6-astra (role `review.infra`) |

Plus the standing rules from the quorum design: blinded from each other, none sees an upstream approval, one mandated adversary, escalate on disagreement rather than voting it away, and high agreement treated as a warning rather than a pass.

**The output is a plan with recorded dissent**, not a consensus document. A panel that produces unanimity and no dissent has either found a genuinely clean plan or failed to decorrelate, and the two look identical from outside — which is why the dissent record is mandatory rather than optional.

### 6.1 The data-model review has a roadmap lens (added 2026-09-18)

Learned on Ads M1 when the EM's first read of the ERD found a Google-shaped model for a product whose
own decision log named LinkedIn and Meta next. The reviewer had checked shard keys and indexes and
never asked the cheaper question. Four checks, run before the first external review of any ERD:

1. **Design for the stated roadmap, not the first integration.** If the PRD, roadmap, or decision log
   names more than one provider, platform, channel, or tenant type, every entity and field name must be
   neutral, the variant is an enum field, and variant-specific extras live in one metadata hash. Test:
   *does the second provider land as an enum value plus an adapter?* If a field is prefixed with the
   first provider's name, it fails.
1. **Justify every table.** Each collection carries one paragraph: why it is a table and what was
   considered instead. A 1:1 collection needs a reason that survives *what makes this 1:N later?*; if
   the answer is "nothing", merge it into its parent.
1. **State, not table.** An obligation whose identity already exists on another row (a removal for an
   identifier that has a row, a retry for a request that has a row) is a state on that row plus an
   operation record, not a new collection. Two places to update one fact is how the fact gets lost.
1. **One model for the first review.** The document reviewers see carries a single ERD with the
   rationale inline. Baselines and reconciliation notes belong in the decision log, not beside the
   diagram; a first-time reader given two models will review the wrong one.

The reviewer states, per check, pass or fail with the field or table named. "Looks fine" is not an
outcome (block-never-bless, §6 above).

### 6.2 The scale gate: no design passes without a Load model (added 2026-10-08)

Learned on the Ads Audience Sync backend: the ERD named every collection and index and passed two model
reviews, and the code built from it then took about 90 comments from a senior reviewer, most of them
scale and wiring: per-sync and per-contact queries in loops, the daily call budget only in Redis,
1,000 ids in job args, a single global sync slot, claims without status filters, a re-upload path no
code reached. Each would have been visible in a table that asked for numbers.

- **The ERD template (`templates/erd.md`) has a required §5 Load model.** One row per collection, job,
  hook and endpoint: max size per team and in total, queries and writes per batch, batch size, fan-out,
  largest job arg, Redis use and its rebuild path, behaviour when Redis, Elasticsearch or the outside
  API is down, and concurrency per team and globally with what holds it. Numbers with a source, or
  `[assumed]`; "small" is not a value.
- **A hook or call on another team's path carries host-path columns** (IP18; added after a past Ads
  backend review where a hook row read "one Redis lookup" and passed, while it added about 30% to a shared
  Redis at the host's peak): the host path and its peak calls/s (source: a metric query), I/O per host call
  for (a) a team that does not use the feature and (b) one that does, the shared resource it touches, that
  resource's measured peak, and the projected increase (host peak x calls per call), summed over every row
  on the same resource. `[assumed]` is allowed
  only with the named metric a human checks before merge.
- **The architect does not hand a design to review without it.** A domain-owner architect agent that
  writes or revises an ERD fills the table and checks it against `apollo-infra-patterns.md` before the
  council runs (template rule in `skills/product-harness-init/templates/domain-owner-agent.md`).
- **The design review fails a design that lacks it.** The infra lens marks a missing table, a missing
  row, or a cell with no number as `failed`, and the council memo cannot recommend acceptance while a
  Load model row is `failed`. A human may waive a row in the decision record, by name and with a reason.
- **The Load model is the contract for the PR review.** The infra lens and db-perf compare the code's
  per-batch counts with the table; a count above the model's is a finding even when the code "looks
  fine".

### 6.3 Every design change gets Astra xhigh, and a cross-family review (Akansh, 2026-10-08)

**Rule.** Any design change is reviewed by Astra (OpenAI `gpt-6-astra`, reasoning effort `xhigh`)
before it is accepted. A design change is: a new ERD; a change to an ERD's design content (§1 to §7 of
`templates/erd.md`); an architecture decision added to a decision log; and a PR change that alters the
design (a new collection, field, index, job, hook, endpoint or state, or a change to the Load model's
numbers). Size does not matter (doc 43 §6 still sizes the code review; this rule is for the design).

- **Two requirements, kept apart.** The Astra xhigh review is required whatever the author's family.
  Independence is a separate question, decided from the artifact's recorded author family (its
  `produced_by`, or the commit authors and their recorded tooling; unknown or mixed is `unknown`), not
  from the host the session runs on. If the author family is OpenAI, Astra is not independent: add a
  review by `anthropic/fable-5-1` as the cross-family reader, and record both.
- **What is reviewed.** The review is bound to a hash of the design content (§1 to §7), recorded in the
  ERD frontmatter as `design_sha`. Adding the review record (§8), fixing a typo in it, or recording a
  decision does not change the hash and does not need a new review; a change to §1 to §7 does.
- **Route.** The `council-adversary` or `infra-lens` agent through shunt (both `model: gpt-6-astra`;
  the Astra route runs at `xhigh`), or `codex exec -m gpt-6-astra -c model_reasoning_effort="xhigh" -c sandbox_mode="read-only"` with the brief on stdin (doc 44 §3): the ERD's path and its diff since the last reviewed `design_sha`, the question, and file pointers; the reviewer reads the repo itself, so no pasted file bodies (doc 46 §5).
- **Evidence.** The served model, provider and effort come from the run's own record (codex stderr
  header, or `scripts/served-models.sh` for a lens that ran alone in its window), never from the
  request. No evidence means `independence: unknown`.
- **Record.** The ERD's §8 table gets one row per reviewed `design_sha`: reviewer, served model and
  effort, date, blockers, the hash that fixed them, and the fallback used.
- **Fallback when OpenAI is unreachable.** Run the same brief on `anthropic/fable-5-1`, tag the row
  `independence: same-family`, and leave `status: in review`. Acceptance on a fallback review needs an
  explicit waiver in the decision record: who, when, why, and when Astra will re-run. Without a waiver
  the design is not accepted, and a re-run on Astra replaces the fallback row when it is reachable.
- **Bounded: two passes per design** (doc 46 §4). Pass 1 reviews the full design; pass 2 reviews the
  delta that fixed pass 1's blockers. If pass 2 still has blockers, stop and give the human options; a
  further pass runs only when a human explicitly asks, and the decision record says who. A fallback run
  that stands in for an unreachable Astra pass, and the Astra re-run that later replaces it, take that
  pass's slot; they do not add passes. Each pass counts against the council budget (doc 34).
- **Blockers are fixed before acceptance.** Non-blocking findings go to the decision log with a reason
  if they are not taken.

## 6.4 Rules a past Ads M1 build paid for

- **Lead with options, never with a question.** A deferred decision goes to the human as two to four
  researched options (competitors and platform docs) with one recommendation, logged as
  `pending human choice`; asking "worker or on-click?" pushed the research onto the EM.
- **Platform facts that shape the model are [P]-sourced before DECIDE closes.** Two unpriced provider
  facts (no webhook, no member listing) reshaped the model late; each became an options memo decided in
  one round.
- **Every ERD carries a scale posture table** (settled by construction / unproven / gate before GA) and a
  recommended load test, beside the Load model of §6.2; a design called solid until asked "is it
  scalable" had its launch inside the HTTP request and unpriced quotas.
- **Correct a human-authored source with a new version, not an edit in place.** PRD gaps found in audit
  become a PRD v2 that cites the original, so provenance and the delta stay reviewable.

## 7. What DECIDE must not do

- **Not build.** The most common way a DECIDE stage fails is producing implementation instead of a decision.
- **Not commit to an estimate without codebase reality.** The reference instance moved from "estimate is light" to "estimate is wrong" on one research pass. An estimate that has not been checked against what exists is a guess with a number on it.
- **Not let design imply backend capability.** A screen showing a match rate implies an API that returns one. Every such implication is a requirement, and unstated ones are how scope arrives late.
- **Not let the arbiter pick on taste.** See §4.
- **Not treat a surviving option as a chosen one.** Survival is a constraint result; choice is a human act.

## 8. Gates

| Gate | Asks | Cheap rejection |
|---|---|---|
| **G2a** | Is the problem worth solving, is the business case falsifiable, is scope right? | Kills the initiative before any design work |
| **G2b** | Which option survives? If more than one, which do you choose and why? | Records the taste call as a decision |
| **G3** | Is the plan sound, and is the recorded dissent acceptable? | The expensive gate — it authorises build |

Same ask-before-assume rule as FIND: at most three decision-relevant clarifying questions at stage entry, each with a stated default, never asking what an artifact already answers.

## 9. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q-D1 | Is `get_code_connect_map` populated for the components this initiative would use, or is coverage patchy? A sparse map degrades conformance checking from a lookup back to a judgment | author + Design | Deterministic design-system conformance |
| Q-D2 | ~~Rendering variants still needs Playwright MCP or `agent-browser`. Neither installed~~ **Resolved:** Playwright MCP installed (doc 39); the Fabric Studio Storyboard renders all pages side by side | author + AI Tooling | closed |
| Q-D3 | Who owns pushing a survivor into Figma — the agent via the write path, or a designer by hand? The write path is untested here, and a bad automated write into a shared file is expensive to undo | author + Design | Figma write-back |
| Q-D4 | C and D running parallel is designed, not tested. Both real runs stopped before DECIDE | author | Parallel C/D |
| Q-D5 | Where does the constraint set physically live so C, D and E all read the same one? Today invariants live in a domain knowledge file, which is the right shape but was seeded for one initiative only | author | Shared constraints |
