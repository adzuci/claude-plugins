# 12 — Product-Building Harness (Design for Review)

> Extends the framework in [01-decisions.md](./01-decisions.md) and [02-architecture.md](./02-architecture.md).
> Incorporates surviving material from the Notion doc "Engineering Agentic Harness" (2026-04-07); see §13.
> **Status: draft for engineer review. Nothing here is binding.**
> Audience: Apollo engineers and AI Tooling. Read time ~15 min.

## 1. What this is

A pipeline that takes a product initiative from "we have some docs" to "we have a reviewed, verified PR", with cross-functional agent roles (research, PM, design, architecture, engineering, QA, review) and enforced human gates.

**What it is not, stated plainly because the framing matters for review:** this does not automate a product team. The evidence (§7) says agent fan-out wins at read-only investigation and adversarial verification, and degrades at parallel writing and at agents approving each other. So the harness automates *artifact consistency and verification*. Humans still decide.

## 2. Why now: the gap is authoring and consistency, not execution

An audit of ~120 skills, 24 sub-agents and 11 `.ai/` projects in leadgenie, plus all 24 plugins in `apolloio/claude-plugins`, found:

| Capability | State |
|---|---|
| Build pipeline (plan to PR to review) | Exists: `auto-pr`, `customer-problem-loop` ("Loopbot", 9 checkpointed stages with an authorization-gate table) |
| PRD authoring | Exists: `apollo-rnd/skills/prd-one-pager` |
| QA / bug bash | Exists: `end-to-end-bug-bash`, `manual-test-execution`, `bug-bash-generator` |
| Code review personas | Exists: 4 reviewer sub-agents plus `pr-tech-lead-synthesizer` |
| Eval infrastructure | Exists: HarnessBench, `stage-contract.json`, `audit_stage_adherence.py` |
| **Design / Figma** | **Nothing, in either repo.** Figma appears only as an input link |
| **Architecture-review persona** | **Nothing** |
| **Multi-persona approval quorum** | **Nothing** |
| **Cross-artifact consistency check** | **Nothing** |
| **Learning from human pushback** | Designed but unbuilt (the `.ai/wo-oncall/` ledger); `update-review-rubric` gestures at it |

Across every skill and agent in both repos, `PRD`, `Figma`, `user story` and `acceptance criteria` appear only as *consumed inputs*, never as authored outputs. All 24 sub-agents are engineering/infra personas. There is no PM persona and no design persona anywhere.

Independently corroborated: the 2026-04 "Engineering Agentic Harness" proposal also defines **no** PM, design, architect, or QA persona. Its only decomposition is task-shaped ("Teammate 1: fix the flaky test / Teammate 2: update the related spec / Teammate 3: verify no regressions").

So the build surface is narrow: consistency checking, a design persona, an architecture panel, and a learning loop. Everything else is wiring existing skills together.

## 3. Layer mapping (no new vocabulary)

This harness introduces **no new layers**. It is composed of existing ones:

| Framework layer | What this harness contributes |
|---|---|
| LAYER 0 — Skills | The stage skills (§4) |
| LAYER 1 — Sub-agents | Design persona, architecture reviewer, consistency auditor workers |
| LAYER 2 — Orchestration | Supervisor plus handoff tools, per D2. In Claude Code the human is the supervisor |
| LAYER 3 — Runtime (Pantheon) | Only if/when a stage runs headless or scheduled |
| LAYER 4 — Distribution | `claude-plugins`, per D5's split |

The pipeline steps below are called **Stages** to avoid colliding with LAYER numbering.

**One axis the 5-layer model does not name.** The earlier proposal separated three things that vary independently: a fixed **harness**, per-phase **skills**, and per-output-type **middleware** ("deterministic middleware — force PR, error recovery"). Middleware is not a skill, not a sub-agent, and not runtime infra. In this design its home is the hook layer (§6), which the 5-layer table also does not name. Worth resolving in the framework proper rather than here.

## 3.1 Archetypes and bootstrap

The harness is generic; a *harness instance* is not. What varies per product is captured in one dimension: the **archetype**. Get it wrong and you generate a plausible but useless instance, so it is decided before anything else.

| Archetype | Domain surfaces | External knowledge | Compliance weight |
|---|---|---|---|
| Third-party platform integration | architect, backend, frontend | Platform API and policy, **primary source required** | High: platform ToS plus regional law |
| Internal workflow / tooling | backend, frontend | Competitor UX only, secondary acceptable | Low |
| Data / ML pipeline | architect, backend, data | Vendor docs and papers; primary for model and licence terms | Medium: provenance and retention |
| Developer / API product | architect, backend | Competitor API design, secondary acceptable | Low to medium |
| Pure UI surface on existing backend | frontend | Design and UX patterns, secondary acceptable | Low |

Classify by what the product **depends on**, not what it looks like. A UI that talks to someone else's API is a platform integration, not a UI surface.

**No default trio.** A product with one meaningful surface gets one domain owner. Extra agents are coordination cost with no counterparty.

**Bootstrap is a skill, not a manual step:** `${CLAUDE_PLUGIN_ROOT}/skills/product-harness-init/`. Given an initiative it classifies the archetype, inventories artifacts to derive which stages fire, then emits the document graph, the domain-owner agent set, seeded knowledge files, an external-acquisition plan with per-category tier requirements, and a manifest of what needs a human. It **emits only; it never runs a stage.**

Templates live beside it (`templates/domain-owner-agent.md`, `templates/domain-knowledge.md`) so a new instance is generated rather than hand-written. The three hard rules in the agent template are substituted verbatim, not paraphrased: never implement, never rewrite history, and no decision entry without alternatives-rejected.

**Seeding rule.** An empty knowledge file makes a useless agent; a fabricated one makes a dangerous agent. Seed only from artifacts that exist, and where a section has no source, write that the section is thin. The highest-value seeding step is the **invariant-extraction pass**: convert each constraint-register item that gates a milestone into a checkable assertion with an ID and a source. A prose obligation that cannot be checked in review will not be enforced.

## 4. Stages

Each stage declares an **existence precondition**: it fires only when its artifact is absent or stale. A stage whose artifact already exists switches to review/gap-fill mode instead of authoring.

| Stage | Fires when | Mode if artifact exists | Composes |
|---|---|---|---|
| **A. Audit** | always | n/a (always runs) | new |
| **B. Research** | open questions have no owner or answer | verify freshness | new (thin) |
| **C. Specify** | no PRD, or PRD missing metrics / acceptance criteria | gap-fill | function team (§4.1) |
| **D. Design** | no design artifact | option evaluation against constraints | new |
| **E. Consolidate** | always, once B–D are approved | n/a | new (quorum, §5) |
| **F. Build** | plan approved | n/a | wraps `auto-pr` |
| **G. Verify** | build complete | n/a | wraps `end-to-end-bug-bash`, reviewer sub-agents |
| **H. Learn** | any human override occurred | n/a | new (ledger, §8) |

**Stage A is the one to build first**, for three reasons: it is deterministic (schema and cross-reference checks, not model judgment), it is the cheapest stage by an order of magnitude, and its output is immediately useful on its own. GitHub Spec Kit's `/speckit.analyze` is prior art for exactly this shape.

Stage A emits structured findings (artifact, location, contradiction class), never prose. Contradiction classes: missing-required-section, stale-relative-to-sibling, mutually-exclusive-claim, unestimated-requirement, unowned-decision.

### 4.1 Function teams: work decomposition, not seniority

Each authoring stage (B, C, D) is a small team, not one agent. **The decomposition axis is the work, not the org chart.**

Rejected: a Group PM / Senior PM / PM Analyst hierarchy. Those are three agents answering the same question at different notional levels, which is the correlated-judgment failure from §5 — role framing measured statistically indistinguishable from baseline, and persona injection showed no improvement across tasks. Three articulate agents agreeing, at 3x cost.

Adopted: specialists that produce **different artifacts from different evidence**, then one arbiter. This is the shape Anthropic's multi-agent research system uses for its reported +90.2%: parallel investigation of distinct sub-questions, not parallel opinions on one.

**Somebody has to write it.** Four analysts run in parallel and read-only, then an **author** writes the PRD, then the arbiter reconciles. Two corrections from an earlier draft: a **measurement** analyst was missing, which made the PRD schema's "success metrics with numbers" requirement unsatisfiable by construction — no agent produced them; it wraps the existing `feature-to-metrics-spec` skill. And `prd-one-pager` *formats*, it does not author — treating the formatter as the authoring step is why this stage read as pure checking.

Mode split, same as FIND: if a PRD exists the author gap-fills; if none exists it authors from scratch. Full running order in [17-decide-stage.md](./17-decide-stage.md) §2.1.

Stage C (Specify) as the reference instance:

| Agent | Produces | Verification handle |
|---|---|---|
| Competitive position | Feature matrix against named competitors, with a differentiation claim | Every claim cited; sources dated; borrowed numbers attributed to their origin |
| Business case | ROI model: explicit inputs, assumptions, sensitivity | Arithmetic checkable; each assumption stated so it can be falsified |
| Scope slicing | MVP / v1 / v2 boundaries | Consistent with the estimates doc and the dependency graph |
| **Arbiter** | One recommendation plus recorded dissent | Must name what it overrode and why |

Rules:

1. The arbiter **never redoes the analysis**. It reconciles and owns the call. The agent doing the work cannot be the one grading it.
2. Specialists are blinded from each other. They produce; they do not review.
3. Seniority exists **only** at the arbiter position. No duplicate-level reviewers of the same question.
4. `prd-one-pager` is retained **only as the final formatting step**, once the analysis exists. It converts existing context into PRD shape; it is a document generator, not a strategy engine, and composing it as the PM stage was an error in an earlier draft of this doc.

### 4.2 Stage D — Design team

Read Figma first, then **generate**, then check, then arbitrate. Without the generator this stage has five checkers and nothing to check on a greenfield feature.

| Agent | Produces | Verification handle |
|---|---|---|
| **Read Figma** | Existing components, tokens, screens, code mappings | Always first. Generating without it produces designs that ignore the existing system |
| **Design generator** | N options as code, built from existing components rather than invented ones | Each option traceable to the components it reuses |
| Flow coverage | Requirement-to-screen matrix, both directions | Deterministic once both sides are enumerable. Catches missing screens *and* unplanned scope |
| Constraint compliance | Pass/fail per hard external constraint, per screen | Each constraint is an assertion against specific copy or a specific field |
| State completeness | Empty, loading, error, partial-failure, permission-denied, disconnected states per screen | Enumerated state list; absence is objective |
| Design-system conformance | Custom UI flagged where a Fabric component exists | Near-deterministic against `node_modules/@apolloio/fabric-core/component-docs.md` |
| **Arbiter** | One recommendation, recorded dissent, and which options survive | Must name what it overrode |

**Usability validation belongs here too** — a fifth specialist asking "can a user complete the task with this design?", against a named task and a defined success condition. It is **not** discovery research: discovery asks what the problem is and runs in Stage B (§4.6); usability asks whether *this* design solves it. Conflating them is how a PRD gets written before anyone checks what users do.

**Visual taste is deliberately not an agent.** Hierarchy, polish, and whether a design feels right are where agents are weakest and humans strongest. The division of labour is: **agents eliminate on constraints, humans choose on taste among the survivors.** With multiple design options in play, the arbiter narrows the set; it does not pick the winner.

**Design-as-code is what makes this work.** Design variants are Fabric Studio prototypes (`apolloio/fabric-studio`, one `prototype/{owner}-{initiative}` branch each, real `@apolloio/fabric-core` components, a deployed preview per branch). They are diffable and revertable, each change carries a changelog line naming the requirement or constraint that drove it, and design review moves *down* the reliability hierarchy: you can grep a prototype for a pre-checked attribute, prohibited copy, or a missing required state, and because it is the same component library production ships, the port is a diff rather than a redraw. Constraint compliance and state completeness stop being judgment calls. (Claude Design filled this slot until 2026-09-18; it imitated Fabric rather than using it, so every survivor had to be re-derived. Doc 17 §3 has the full rationale and the setup.)

The two blockers recorded earlier are closed: prototype branches have preview URLs and the reviewer agents have Playwright, and a prototype on a shared branch is readable by every agent, so a design run always has something to diff against.

### 4.3 Compliance is not a stage

The instinct is to put legal review between design and engineering. **That is the wrong shape, and the Ads audit demonstrates why.** Compliance did not fail there by being skipped in sequence. It failed because a constraint register existed and *nothing validated against it*: six of thirteen milestone-gating items were unpriced, seven of thirty items had no status line to stamp, and the register itself went stale four days after the platform answered.

So compliance is a **constraint source that every stage validates against**, which is exactly the edge topology Stage A already implements.

| Agent | Produces | Notes |
|---|---|---|
| Constraint extractor | Prose policy/legal docs converted to a machine-checkable register: item id, assertion, gating scope, owner, status, `as_of` | Would have caught items with no status line, and the missing owner column |
| Platform-policy watcher | Diff between the register and the platforms' actual published policy | Scheduled, not per-run. This is the agent that catches a register going stale |
| Coverage checker | Every gating constraint traced to estimated work and a code owner | Generalisation of Stage A's `constraint-register` to `estimate` edge |

**The arbiter here is a human, and that is a hard boundary.** An agent must never issue a legal verdict. Its job is to make the human's verdict cheap and to make its absence loud. Every other function team in this document has an agent arbiter; this one does not.

### 4.4 Stage E — Architecture review

The original framing was "staff engineer plus tech lead plus EM plus architect". Those are seniority titles reviewing the same artifact, which is §5's correlated-judgment failure. Decomposed by what is actually being checked:

| Agent | Checks |
|---|---|
| Seam reviewer | Does the abstraction hold for the second and third consumer, or only the first? |
| Data-model reviewer | Shard key, index coverage, append-only vs mutable, migration shape. Largely covered by the existing `db-perf` agent |
| Failure-mode reviewer | Partial failure, retry semantics, revoked credentials, mid-run state changes |
| Blast-radius reviewer | Migrations, reindexes, T0 collections, cross-pack reach. Feeds the §6.1 scope gate |
| **Arbiter** | One verdict plus recorded dissent, under §5's blinding and cross-family rules |

### 4.5 Stage F — Engineering fan-out

Decomposed by **slice ownership**, not seniority. One agent per genuinely independent slice, each in its own worktree.

| Agent | Role | Status |
|---|---|---|
| Slice owner (N of them) | Implements one independent slice end-to-end in an isolated worktree | **Not new** — this is `auto-pr` run per worktree. Building a third abstraction for it would violate the no-abstraction-without-a-second-use rule |
| Contract keeper | Owns any interface two or more slices share. Slice owners consume the contract; they do not each invent it | **Built**: `${CLAUDE_PLUGIN_ROOT}/agents/slice-contract-keeper.md` |
| Integrator | Serialises merges, and hunts *semantic* conflict | **Built**: `${CLAUDE_PLUGIN_ROOT}/agents/slice-integrator.md` |

The two built agents exist because they address the two documented failure modes that worktrees do not: **conflicting implicit decisions** at a shared boundary (contract keeper, invoked before slices start and again on any change request — slice owners request contract changes, they never make them), and **semantic conflict that passes compile, lint and tests** (integrator: duplicate abstractions, one concept under two names, divergent error handling for the same failure, retry double-counting, two migrations on one collection, sequencing assumptions across slices).

Both are explicitly barred from doing the work they judge. The contract keeper never implements a slice; the integrator never fixes what it finds, and never merges to the default branch. The integrator is also required to state what it exercised versus only read — "reviewed statically, not exercised at runtime" is an expected outcome, since sequencing and retry bugs are invisible to static reading.

Three rules from the documented failure modes:

1. **N equals the number of genuinely independent slices**, not a headcount. On Ads that is 2, because the estimate itself says M1 and M2 run in parallel and converge only at S4. Practical ceiling reported elsewhere is 4-8 concurrent worktrees before review becomes the bottleneck.
2. **Worktrees give file isolation, not semantic isolation.** Agents produce duplicate abstractions and contradictory decisions that compile and lint clean. That is the integrator's entire job, and it is why the contract keeper exists.
3. **Merges are serialised.** Merge one, rebase the next, review the next. Simultaneous merges compound conflicts.

### 4.5b External knowledge acquisition (the greenfield bootstrap)

Domain agents bootstrapped only from internal artifacts inherit the organisation's blind spots. On the pilot, the PRD, the estimate and the legal register between them never mention **how anyone else solved this** — not one competitor's sync semantics, not one platform UX convention. A domain owner built from those three sources is confidently parochial.

So greenfield domains need an external acquisition pass, and it applies to every function, not just engineering.

| Function | External knowledge needed | Acceptable source tier | Decay |
|---|---|---|---|
| PM | Competitor feature matrices, pricing and packaging, published match rates, positioning | Secondary acceptable | Medium (quarterly) |
| Design | UX flows, state vocabularies, consent-presentation patterns | Secondary acceptable | Low (yearly) |
| Architect | Platform API contracts, quotas, deprecations | **Primary required** | High (weeks) |
| Backend | Same, plus SDK behaviour and error shapes | **Primary required** | High |
| Frontend | Platform-facing copy conventions, what a platform permits you to claim | Primary for claims, secondary for patterns | Medium |
| Compliance | Platform policy, ToS, regional rules | **Primary required** | High |

#### Three rules

**1. Source tiering is mandatory.** Every claim carries a tier, a URL, and a retrieval date:

- **[P] primary** — the platform's or vendor's own docs, policy, or pricing page
- **[S] secondary** — blog, review, tutorial, third-party summary
- **[U] unconfirmed** — believed but not substantiated

This is the third application of one mechanism. Stage A has the two-quote rule, Stage B has the citation rule, external acquisition has tiering. Same reason each time: **an unsourced claim is deleted, not hedged.**

**2. The required tier varies by claim type**, and this is the nuance that matters. A blog is a perfectly good source for "how does Hightouch present run history" and a terrible source for "what does the Data Manager API accept." Building an integration on a secondary account of an API contract is how you ship against a policy that changed six months ago.

**3. Record decay per section.** External knowledge goes stale at wildly different rates, and mixing rates in one file makes refresh a judgment call instead of a mechanical job. Per-section decay is what makes the compliance team's **platform-policy watcher** (§4.3) implementable — it needs to know what to re-verify and how often.

#### Why this is the highest-risk output in the harness

Every model has plausible-sounding training data about every major platform API. An agent asserting "Google requires X" from memory rather than from a source produces output that is confident, specific, checkable in principle, and checked by nobody. It will be believed, built on, and discovered wrong at integration time.

That is a worse failure than the agent saying nothing. Hence tiering, and hence the standing instruction in every domain agent: where the record is thin, **say the record is thin** rather than filling the gap with plausible domain knowledge.

#### File layout

`.ai/<initiative>/domain/external/` — `platform-<name>.md`, `competitors.md`, `ux-patterns.md`. Kept separate from the internally-sourced domain files so the sourcing standard for each is unambiguous.

#### Current tooling blocker

> **Superseded 2026-09-20:** `WebFetch` and `WebSearch` are available to the reviewer agents in the current Claude Code setup; the paragraph below is the record of the original gap. External claims are still tiered ([P]/[S]/[U]) and a claim without a primary source is still deleted, not hedged.

`WebFetch` is denied in this environment, so acquisition agents can only obtain **search-result summaries**. That caps every claim at **[S]**, which is below the bar rule 2 sets for architect, backend and compliance knowledge — precisely the categories where being wrong is most expensive. Until that is resolved, platform API knowledge must be treated as provisional and verified by a human against primary docs before anything is built on it. See Q11.

### 4.5a Domain-owner agents (persistent, not per-stage)

Distinct from every function team above, because they are **not scoped to a stage** and they **persist across the product's life**.

A human domain owner's value is not seniority, it is that they remember why the seam looks like this, which approach was already tried, and which collection needs index care. That is the one thing from the seniority framing that genuinely transfers, because it is *accumulated context* rather than a persona.

Naming convention, templatable per initiative: `<surface>-architect`, `<surface>-backend`, `<surface>-frontend`.

**The agent file is thin; the knowledge file is the asset.** Behaviour lives in `.claude/agents/<name>.md`; knowledge lives in `.ai/<initiative>/domain/*.md` and is read on demand. This keeps agent definitions small (progressive disclosure) and makes the knowledge diffable, reviewable, and attributable.

**Correction (2026-09-08): that knowledge needs a typed schema, not prose under headings.** An external ablation — holding the model constant and varying only the memory representation — measured **typed memory at +11.8 points over file-based notes.** That is the most credible single number found in any external source, because it isolates a harness effect rather than a model difference.

Our domain files are prose under headings, chosen for diffability and human review. That choice costs real capability. **So: invariants, open decisions, rejected approaches and platform quirks become records with ids, status and relationships** — still in a human-readable, diffable store, because the win is in the typing rather than in hiding it.

The same source's **reflection pass** — periodically merge duplicates, link related records, prune dead ones — is also the only mechanism found anywhere that speaks to the eval-decay problem.

**And one hazard where knowledge or findings pass upstream.** Foundation models operate on a fixed role schema and do not natively distinguish "assistant A" from "assistant B." So wherever we deliberately *do* pass upstream content — an arbiter reading reviewer findings, an escalation packet — prior agents' messages must be **re-cast as narrative with their tool calls explicitly marked as theirs**, or the receiving agent absorbs them as its own actions and its own capability. Our blinding is implemented by omission, which is safe; this gap sits precisely where omission is not an option.

Each domain owner runs in two modes, exactly as a human owner does:

- **Guide**, before someone designs: has this been decided? does it violate an invariant? what was tried and rejected? Crucially, *"not yet decided" is a valid answer* — it tells the asker they are making a new decision, which is the moment to record it.
- **Review**, after someone implements: does this contradict a recorded decision, break an invariant, or **silently create a new decision nobody recorded**? The third case is the most valuable and the easiest to miss. An implementation that quietly picks a retry owner or an error semantic has made an architectural decision.

Three hard rules: they never implement (an author cannot judge their own work), they never rewrite history (a reversal is appended with a pointer to the original), and a decision entry without **alternatives-rejected** is a preference, not a decision, and will be relitigated within a quarter.

**The greenfield problem, and why it does not sink the idea.** For a new product the domain agent has no domain. Its value is low at slice 1 and high at slice 10, and pretending otherwise at slice 1 is how a wrong decision gets locked in — so the agents are instructed to say "the log is thin" rather than filling gaps with plausible architecture.

But they need not start empty. The Ads instances were bootstrapped from Stage A and Stage B output: 9 binding invariants extracted from the constraint register and written as checkable assertions, 8 named undecided decisions with what each is blocked on, 4 rejected approaches with reasons, 7 enumerated compliance enforcement points, ~25 required UI states, and 6 legally-constrained copy rules. That is a real starting corpus, and it exists only because the audit and research ran first.

**This is also the persistence mechanism for Stage H.** Learning that lives in a ledger nobody reads is not learning. Routing it into the domain owner that gets consulted before the next slice is what closes the loop. See Q6.

### 4.6 Stage B — Research

Decomposed by **evidence type**, because the three kinds of open question need entirely different sources and have entirely different failure modes.

| Agent | Answers | Verification handle |
|---|---|---|
| Codebase reality | "Do we already have this?" | Must cite `file:line` and real field names. "Not found" is a valid answer; inference from adjacent code is not |
| **User evidence** | "What do users do today, where do they struggle, what do they ask for?" | Every claim traced to a query, a cohort, a ticket, or a replay ID |
| External source | "What does the vendor or platform actually say?" | Primary sources only (docs, ToS, API reference). Every claim carries a URL and a retrieval date. Blogs and summaries are not sources |
| Precedent | "How did we solve this before, and what happened?" | Links to real artifacts: prior PRs, incidents, RCA docs, past initiatives |
| **Arbiter** | One answer set, **plus every question it could not answer, each with a named owner** | Unanswered-with-owner is a first-class output, not a failure |

**User evidence is discovery research, and it belongs here rather than in Design.** If user research runs only at Stage D it happens *after* the PRD is written, so the problem statement was never evidence-checked — it was asserted and then decorated. Usability validation of a specific design is a different activity and does belong in D (§4.2).

Note the current evidence asymmetry: Amplitude (including session replay), Intercom, Jira, Glean and (since 2026-10-12) Enterpret are reachable, but Gong, Sprig and G2 are not authenticated. So discovery can establish **friction** reliably and **motivation** only weakly, and must say which it is doing. See [16-find-stage.md](./16-find-stage.md) §6.

**The citation rule is Stage B's version of Stage A's two-quote rule.** Research is where hallucination risk is highest, so: every claim carries a source, and a claim without a source is dropped rather than hedged. Same mechanism, same reason.

**Codebase reality is the highest-value of the three**, and the pilot proves why. Three unestimated compliance requirements swing between cheap and architecturally invasive depending on a single question: does a consent-evidence store, a global suppression model, or per-identifier provenance already exist? That is the difference between "the estimate is light" and "the estimate is wrong", and both the PRD and the legal register leave it blank — the register explicitly asks for it (*"Evidence needed: current privacy/suppression models"*).

**The arbiter's unanswered-with-owner output is the fix for the failure mode the pilot exhibited most.** Thirty constraint items sat pending with no named owner; role lists ("Legal, PM, Partnerships") are not owners. A research stage that returns "I could not determine X, and Y owns finding out" converts a silent gap into a tracked one.

**Worked example, Ads Builder.** Each specialist has real, non-obvious work on a live program:

- *Competitive position*: the M1 PRD names Vector and ContactLevel and borrows ContactLevel's match-rate figures (70–90% versus ~30% for cold CSV) without validating them.
- *Business case*: reconciling an SMB target segment against Google's **USD $50,000 lifetime-spend gate** for advanced Targeting. This contradiction is a business-case output; no PRD formatter would ever surface it.
- *Scope slicing*: M1 Phases 0–6 and M2 S1–S5 carry estimates, but Google's written 1P-only ruling (2026-08-25) changed what MVP is, and the slices have not been re-cut since.

**Triggers and output types.** Artifact-absence is a *precondition*, not a trigger. Stages need both, and each stage's output needs a deterministic delivery path (the middleware axis from §3):

| Stage | Trigger | Output type (middleware) |
|---|---|---|
| A. Audit | manual, or scheduled weekly per initiative | findings comment on the source doc |
| B. Research | unowned open question detected by A | doc update plus owner assignment |
| C. Specify | A reports missing required section | PRD revision, human-approved |
| D. Design | A reports design/PRD divergence | annotated option comparison |
| E. Consolidate | B–D gates all green | plan document plus recorded dissent |
| F. Build | plan approved | draft PR, never auto-merge |
| G. Verify | PR opened (webhook) | review comments plus bug records |
| H. Learn | human override recorded | ledger entry plus eval case |

## 5. Quorum design

Approval quorum is the part most likely to be wrong, so it gets the most scrutiny.

**The database analogy, and where it breaks.** A Raft or Paxos quorum bounds failure because replicas fail *independently*. Five replicas running identical buggy code do not detect the bug; they agree on it. A single-model quorum is that case: shared weights mean correlated errors, so effective N collapses far below actual N.

Consequences measured in the literature (caveats in §7):

- On high-quality patches, **83% of agentic reviewer errors were false approvals** (167 vs 105 false rejections). As generators improve, reviewer error concentrates on wrongly approving.
- Below roughly 0.5 per-item accuracy, **majority voting is worse than a single model** (one benchmark: 56.7% vs 70.0%).
- Labelling vulnerable code "secure" collapsed detection: GPT-4o-mini 97.2% to 3.6%; Claude 3.5 Haiku -59.9pp; Sonnet -16.7pp. **An upstream agent asserting "this is correct" is an attack on every downstream reviewer.**
- Soft decorrelation does not work: strong role framing, explicit dissent instructions, and both combined were statistically indistinguishable from baseline (48.3% disagreement). Only a hard devil's-advocate mandate moved it, to 99.2%.

**Therefore, binding rules for any approval quorum in this harness:**

1. **Cross-family required.** At least one voter from a genuinely different model **lineage** — not a different version, and not a different tool. Routing policy, the family taxonomy, and the current blockers are in [13-model-routing.md](./13-model-routing.md).

   Two traps this rule exists to catch. **Fable 5 is a Claude model** (`claude-fable-5`), so Opus + Fable is a same-lineage pair and does not satisfy this. And **a harness is not a model**: Codex is an agent loop that happens to run a non-Claude model, so it counts only if the *model* is dispatchable as a reviewer — which today it is not. Verified 2026-09-03: no LLM-provider MCP, no provider CLI on `PATH`, no keys, plugin not installed. **Stage E's cross-family requirement is currently unimplementable, not merely inconvenient.** *(Superseded 2026-09-19: OpenAI gpt-6-astra is dispatchable with repository tools through shunt, see [37](./37-model-bridge-and-context-budget.md) §1 and the `council-adversary` agent; the paragraph is kept as the record of why the rule exists.)*

   Do not resolve this by adding more Claude voters. Three Claude models voting is a 3x bill for correlated agreement. If no cross-family path is approved, the honest design is fewer LLM votes and more deterministic gates — which §8 argues is both cheaper and more reliable anyway.
2. **Blinded.** No reviewer sees another reviewer's verdict, and no reviewer sees upstream approval status. Authorship anonymised.
3. **One mandated adversary**, instructed to refute by default, distinct from "a persona with opinions".
4. **Escalate on disagreement; never vote it away.** Three voters minimum.
5. **High agreement is a warning, not a pass.** Track inter-reviewer agreement as a health metric; a unanimous panel is a prompt to check for correlation, not a signal of correctness.
6. **Rules before judgment.** Anything expressible as a schema, lint, grep or CI check must be a deterministic gate, not a model vote. Anthropic's own verifier hierarchy ranks LLM-as-judge last.

**Resolved 2026-09-19:** the cross-family vote is dispatched through shunt (`model: gpt-6-astra` in agent frontmatter, doc 37); the Codex *plugin* commands remain human-triggered and serve the PR kind (doc 38). Gemini and DeepSeek stay gated on approvals (`scripts/bridge.sh`).

### 5.1 The quorum that actually works: artifacts, not models

Discovered while running Stage A, and it is cheaper and more reliable than any model quorum in this document.

**When three artifacts cover the same fact and one disagrees, the topology localises the error with no voting at all.**

On the Ads set, the PRD claimed a paused sync leaves platform members untouched. The legal register said removals continue. The estimate independently said "a paused sync still runs removals." Same pattern on audience ownership: the PRD offered a picker for pre-existing lists, the register forbade it, and the estimate listed it as out of scope. In both cases the PRD was the outlier **two artifacts to one**.

That conclusion required no personas, no model votes, and no cross-family dispatch. It fell out of declaring the edges. And the replicas genuinely fail independently, because they are different documents written at different times by different people — which is exactly the property §5 says a single-model quorum cannot have.

**Caveat (Astra review 2026-09-19):** overlap *localises* a discrepancy; it does not establish which claim is true. Documents copy one another (the ADR-P3 research lens borrowed the backend lens's evidence), so a two-to-one document majority is a pointer to check, not an independent verification. Resolve it against a primary source or the running system.

**Design consequence:** prefer overlapping artifact coverage over additional model voters. Three edges touching one fact is a real quorum; three Opus agents opining on it is not. When a config can be shaped so that important facts are covered by three artifacts rather than two, do that instead of adding reviewers.

**No prior art internally.** The earlier harness proposal contains zero treatment of correlated error, false approval, blinding, or cross-family voting. This section is entirely additive; nothing in the prior work challenges it, and nothing in it can be reused.

## 6. Gate enforcement: hooks, not prompts

> **Status 2026-09-19 (Astra review ENG1):** the repository registers only a `SessionStart` environment hook; no deny hook enforces a stage gate or the authority policy, and reviewer agents' write limits are prompt-level. Every gate in this framework is therefore **advisory** until a deny test (an attempted out-of-scope Edit, shell and connector call, each refused) is checked in. A `gate_status: passed` written by a model is a claim, not a credential; the human decision record (`harness-council decide`) is the credential.

A prompt-level gate ("WAIT for human approval") asks the model to decide both the action and whether to ask first. Both are negotiable, including by prompt injection. Gating after the side effect is not approval, it is incident documentation.

The same conclusion was reached independently from the Open-SWE post-mortem in the 2026-04 proposal: **"Deterministic middleware (force PR, error recovery) — Open-SWE pattern, don't trust LLM to remember."**

`PreToolUse` hooks are real enforcement: they fire before the permission-mode check, `exit 2` blocks and overrides any model-issued allow, they fire even under `bypassPermissions`, and they cost zero context.

Implementation shape: a `PreToolUse` hook refuses `Edit`/`Write` unless an approval record for the current stage exists on disk.

Two caveats to encode, not discover later:

- A **timed-out** `PreToolUse` does **not** block. Timeouts must fail closed.
- A `Stop` hook is auto-overridden after 8 consecutive blocks.

### 6.1 Blast-radius scope gate (second, orthogonal axis)

Stage gates are sequential. They say nothing about *how much* a diff touches. This table is lifted from the earlier proposal and is directly implementable as a `PreToolUse` path allowlist:

| Scope level | What the agent may touch | Auto-approve eligible | Example |
|---|---|---|---|
| Single pack | Files within one `packs/` directory | Yes, once track record exists | `packs/plays/spec/workers/` |
| Pack + shared | Pack files plus related `assets/app/` components | With human review | Refactoring a pack that uses shared utils |
| Cross-pack | Multiple `packs/` directories | Never auto-approve | Migration affecting billing + plays |
| Infrastructure | `config/`, `db/migrate/`, `.github/` | Never; blocked by default | Schema migrations, CI changes |

Two related defaults from the same source, both adopted: **draft-PR-only, no auto-merge** until a track record exists, and **no raw shell access, typed tools only**.

### 6.2 Human gates degrade, and this is measured

Across 400 repeat reviewers and 11,429 agent-authored reviews: approval rate +14.5pp, review latency +3.5x, inline comments -22%. The effect was agent-specific (human-PR approval in the same repos did not move), so it is habituation, not laziness.

Mitigations: gates present a structured findings diff rather than prose; approval rate is tracked as a harness health metric; prefer fewer, sharper gates over more.

## 7. Evidence base and its limits

Findings in §5 and §6.2 come from (a) Anthropic's published engineering guidance, and (b) a literature sweep conducted via search-result summaries, **not** full paper reads. Several sources are 2026 preprints and not peer reviewed, and attribution of specific numbers could be wrong. Treat the direction as sound and any individual figure as unverified.

Two positions worth reading in tension: Anthropic's multi-agent research write-up (reports +90.2% over single-agent, at ~15x tokens, and explicitly notes most coding tasks have fewer parallelisable subtasks than research) and Cognition's "Don't Build Multi-Agents" (single-threaded agent plus compression; "actions carry implicit decisions, and conflicting decisions carry bad results"). They converge more than the titles suggest: read-only fan-out good, parallel writes need filesystem isolation, shared context beats message passing.

**Fan-out must degrade, not fail.** Adopted verbatim as a design rule from the earlier proposal: parallelism is *"an optimizer, not a dependency."* Every fan-out stage (F, G) must run correctly in single-session mode, with fan-out as a runtime optimisation. A platform change to teams or batching should make the harness slower, not broken.

## 8. Token budget

Cost is a first-class gate, not a postmortem. Per-stage caps with **auto-pause at 100% requiring owner acknowledgement**, reusing the `wo-oncall` pattern and the existing [cost-attribution-schema.md](./cost-attribution-schema.md).

Efficiency and reliability are the same lever here, which is the design's most useful property:

| Mechanism | Token cost | Reliability tier |
|---|---|---|
| Hooks as gates | zero context | deterministic |
| Schema / lint / grep checks | near zero | highest (per Anthropic's hierarchy) |
| LLM persona panel | ~15x baseline | lowest |

Levers, in rough order of impact:

1. **Prompt caching.** Reported 90-96% cache hit rates across 3,007 sessions internally. This is the main argument for staying Claude Code-native rather than building a custom loop that bypasses caching.
2. **Model routing.** Haiku 4.5 for mechanical stages, Opus only for adversarial and synthesis work. The earlier proposal's ladder, reusable as a starting point: simple single-file task ~$0.30-0.60; medium 3-5 file task with a small team ~$1.50-3.00; complex cross-cutting task with an Opus lead ~$5.00-15.00. Claimed saving of 60-80% versus always using Opus.
3. **Tool-loading discipline.** Load only the tools a stage needs. A curated 6-tool set is ~500 tokens of schema; several MCP servers loaded indiscriminately cost thousands of tokens on *every* turn. This is a cost axis the capped-return lever does not address.
4. **Capped sub-agent returns** at 1,000-2,000 tokens, and progressive disclosure in skills.
5. **MCP-as-code-execution** where applicable (one reported case: 150k to 2k tokens).

Reference targets to argue about, not adopt: `<$5` average per PR on Sonnet, `<$15` on Opus.

**Counter-position, recorded because it came from the harness owners.** The same 2026-04 discussion concluded that *"token burning is acceptable for development phase"*, citing a single session at ~$80 that produced higher-quality results and a `$300/day` external reference point. That is in direct tension with cost-as-a-gate. The reconciliation this doc proposes: caps exist and auto-pause, but the cap is a *conversation trigger* requiring owner acknowledgement, not a hard kill. If reviewers prefer no caps during a build-out phase, that is a legitimate position and should be settled explicitly rather than by default.

## 9. Conflicts with existing binding decisions

These need resolution before implementation. Per 01-decisions.md, reversal of a D-decision requires a written ADR with the named owner's sign-off.

| # | Conflict | Options |
|---|---|---|
| **C1** | **D5** states Notion is a read-only export and `${CLAUDE_PLUGIN_ROOT}/framework/` is master. This doc is being reviewed in Notion. | Keep this file as source and publish a Notion mirror (current approach, no ADR needed), or amend D5 |
| **C2** | **D3** assigns harnesses and agent descriptors to the Platform team, reviewed by Platform. A team-authored harness collides with this. | Ship as skills (LAYER 0) plus sub-agents (LAYER 1), which pack owners may ship, and escalate to Platform only if a stage needs Pantheon (recommended), or get Platform to co-own |
| **C3** | **D4** requires replay-eval green (>=90% activation precision, <=15% FPR over 50 historical PRs) before a skill lands. "50 historical PRs" does not map to a document auditor. | Define the document-artifact analogue of a replay corpus. Unresolved; see Q1 |
| **C4** | **D2** names the dapi supervisor plus Pydantic plan schema as canonical orchestration. Claude Code stages are markdown skills. | D2 already anticipates this ("the *pattern* is the same"). Document the mapping explicitly rather than inventing a second shape |
| **C5** | **Repo naming.** D5's table routes shared skills to `apolloio/claude-plugins`; the 2026-04 meeting recorded "put custom knowledge in plugins in the `apolloio/skills` repo". Either a rename happened or these are two repos. | Confirm before citing D5's table as settled |

**Evidence for C2's recommended option, from the harness authors themselves.** The 2026-04 proposal states the boundary this doc relies on, pre-D3:

> Teams add skills without forking harness · Skills encode: conventions, test cmds, arch patterns

> **Skills are the right extension model** — teams author skill files that encode domain knowledge, test commands, and architectural conventions. The harness loads them automatically. No code changes needed to add a new team's context.

and, in its requirements table, *"Teams produce skills, harness consumes them"* at P0. Note the asymmetry: that document never says Platform must own harnesses, and never names a skill reviewer. So it supports the recommended C2 resolution but does not settle Q5.

## 10. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q1 | What is the replay-eval corpus for a document auditor? Candidate: N historical artifact sets with known contradictions, scored on contradiction recall and false-positive rate. Needs a labelled corpus that does not exist. | AI Tooling + author | Stage A landing in `claude-plugins` (C3) |
| Q2 | Does the design persona need a Figma MCP path, or is evaluating an existing prototype against constraints sufficient for v1? | author + Design | Stage D |
| Q3 | Cross-family quorum dispatch. **Resolved 2026-09-19 via shunt (doc 37).** Historical text: No path exists today: no LLM-provider MCP, no provider CLI, no keys. Options are an MCP wrapper around one non-Claude provider, a CLI with a scoped key, or keeping a permanent manual step. Needs a data-handling review, which is a security question rather than a procurement one. | AI Tooling + Security | Stage E entirely |
| Q12 | Portability. What ports cheaply is the taxonomies, skills, knowledge files and configs — `claude-plugins` already does dual Claude/Codex distribution. What may not port is the **enforcement layer**: without a deny-semantics pre-execution hook, every gate degrades to a prompt, which the design explicitly rejects. See 13-model-routing.md §7. | AI Tooling | Any decision to run the harness on another agent tool |
| Q4 | Per-stage token caps. **First real datum: Stage A costs ~78k tokens per edge**, so the 10-edge Ads config projects to ~780k for a full run. That is expensive enough that edges want triaging rather than running wholesale. Open: what the cap should be, and whether caps are wanted at all during build-out (see §8 counter-position). | author + AI Tooling | Stage A at full config size |
| Q5 | Ownership. The prior proposal's RACI matrix exists with 8 rows and **zero filled cells**; the rows are reusable, the answers are not. Needs owners for: per-team skill authoring, auto-approve policy changes, eval/golden-task maintenance, cost budget, task-type approval, and harness code itself. | Eng leadership + Platform | Anything beyond Stage A |
| Q6 | Does Stage H's ledger reuse the `.ai/wo-oncall/` record shape verbatim, or does artifact-level learning need a different schema? | author | Stage H |
| Q7 | Where does the middleware axis (§3) live in the 5-layer model? | AI Tooling | Framework consistency, not this build |
| Q8 | What is the work decomposition for Research (B)? Stages C, D, E, F and compliance are defined in §4.1-§4.5; Research is not. Decompose by work produced, not by seniority. | author | Stage B |
| Q10 | **Resolved: Playwright MCP is installed (doc 39) and Fabric Studio previews plus the Storyboard render every page.** Historical: Design review needs rendering (Playwright MCP or `agent-browser`) and neither is installed. Without it, variants are code-only, which is a weak substitute for looking at a design. Also: `use_figma` write path is untested. | author + AI Tooling | Stage D |
| Q11 | `WebFetch` is denied, so external acquisition (§4.5b) can only reach search summaries. That caps claims at tier [S], below the primary-source bar required for platform API, policy and compliance knowledge. Enable it, or accept that every platform claim needs human verification against primary docs before use. | AI Tooling | Trustworthy architect / backend / compliance external knowledge |
| Q9 | Function teams multiply cost: 3 stages x ~3 specialists plus arbiters is 12+ agents per run before Build and Verify. Does the per-stage cap survive that, or does Stage C need its own budget? | author + AI Tooling | Stage C |

## 11. Deliberately not decided

- The pilot initiative and slice (tracked separately)
- Whether stages ever run fully unattended (default: no)
- Any per-agent prompt or file layout (out of scope for this doc by design; a wall of implementation detail invites rubber-stamping, which is the failure mode this document is partly about)

## 12. Proposed first step

Build **Stage A only**. One skill plus a document-graph config, deterministic, composing `end-to-end-bug-bash`'s existing link extraction. Run it against one real initiative.

**Exit criteria (numeric, following the earlier proposal's convention):**

- Runs end-to-end against one real initiative's full artifact set without manual intervention
- Finds >=80% of contradictions in a hand-labelled sample of that initiative's artifacts
- <=20% false-positive rate on those findings, human-adjudicated
- Total cost per run under the per-stage cap set in Q4
- Output is structured findings, adjudicable in under 15 minutes by the initiative's owner

Do not build Stage E (quorum) until Q3 is answered, because a single-family quorum is worse than no quorum: it produces confident unanimous approval at 15x the token cost.

## 13. Relationship to "Engineering Agentic Harness" (2026-04-07)

That document is a **proposal, not a shipped system**, and it **predates** 01-decisions.md and 02-architecture.md (both 2026-04-30). It is substantially superseded:

- Its central recommendation was to fork `vertical-agent` into a focused `eng-agent` repo. **D1 forbids this** (Pantheon is the sole runtime; `vertical-agent` is a consumer, not a platform). It never mentions Pantheon.
- It adopted Claude Agent Teams as the orchestration layer explicitly to avoid defining one, and separately floated a cross-vendor LLM router as orchestrator. **D2 sanctions neither.**
- Its skill convention was one flat file per *team*; D3/D5 use a per-capability directory. It has no sub-agent layer at all.

What survives and is merged above: the harness/skills/middleware separation (§3), the trigger and output-type axes (§4), the Open-SWE "don't trust the LLM to remember" lesson (§6), the monorepo scope-control table and draft-PR-only default (§6.1), the "optimizer, not a dependency" degradation rule (§7), the cost levers and reference targets (§8), the skills-vs-harness boundary quotes (§9, C2), the empty RACI row list (Q5), and the numeric-exit-gate convention (§12).

Deliberately not carried over: the platform comparison tables, the vertical-agent architecture and Slack-to-PR data flow, the fork strategy, and the meeting notes.

## 14a. Reference instance status

One instance exists, and its purpose is now to have validated the generic parts. It is **not** a live program this framework is responsible for.

| Generic artifact | Validated by | Location |
|---|---|---|
| Stage A skill | 3 of 10 edges run; 15 findings; 5 dropped | `${CLAUDE_PLUGIN_ROOT}/skills/artifact-audit/` |
| Document-graph schema | 8 artifacts, 10 edges, `as_of` field added after a real gap | `templates/document-graph.yml` |
| Slice-fit classifier | Applied once; returned ~15% agent-ownable, which was the useful uncomfortable number | `${CLAUDE_PLUGIN_ROOT}/skills/slice-fit/` |
| Contract keeper, integrator | Built, not exercised | `.claude/agents/slice-{contract-keeper,integrator}.md` |
| Domain-owner pattern | Trio built and seeded from real audit and research output | `templates/domain-owner-agent.md` |
| External acquisition + tiering | 3 passes run; caught its own internal contradiction | `templates/` plus the tier rules in §4.5b |
| Bootstrap | Generalised from the instance | `${CLAUDE_PLUGIN_ROOT}/skills/product-harness-init/` |
| Reconciliation-as-append | Performed once by hand, 13 deltas | Reference instance's `domain/reconciliation-*.md` |

**What the instance taught the framework**, each of which is now generic:

1. Recency cannot be auto-detected from a document fetch, so it must be config (`as_of`).
2. Pairwise edges cannot catch a document contradicting itself, so a self-consistency phase is needed (Phase 2.5).
3. Three artifacts covering one fact beat three model voters (§5.1).
4. The highest-value finding class is `unestimated-requirement`, not contradiction.
5. Codebase-reality research swings estimates between cheap and invasive, so it precedes commitment (§4.6).
6. Domain knowledge seeded only from internal artifacts is confidently parochial (§4.5b).
7. Acquisition passes disagree with each other, which is the tiering rule working rather than failing.

## 14. Stage A: built and first-run results (2026-09-01)

Built at `${CLAUDE_PLUGIN_ROOT}/skills/artifact-audit/` (SKILL.md, two references, a config template, an eval scaffold). First config: `.ai/ads-builder/document-graph.yml`, 8 artifacts, 10 edges. Report: `.ai/ads-builder/audit-2026-09-01.md`.

**Partial run: 3 of 10 edges.** 15 findings, 5 candidates dropped under the two-quote rule.

### What the run proved

- **The calibration edge came back clean.** `overview` to `est-sync` is a summary against its own source, so it should agree, and it did — every sourced number matched. The agent considered two discrepancies and dropped both with reasoning rather than reporting them. Over-reporting is the dominant failure mode for review-shaped agents, so a clean result on a clean set is the more important half of the test.
- **It corrected its own author.** A contradiction escalated earlier in design discussion (a platform spend tier versus the stated target segment) was dropped: the register files it as an open question and the PRD never asserts qualification, so a reasonable reader can hold both. Recorded in the report's dropped-candidates list.
- **The highest-value finding class was `unestimated-requirement`, not contradiction.** Six of thirteen milestone-gating constraint items were unpriced in the estimate, and the estimate's out-of-scope list excluded none of them, so they were assumed free rather than deferred. Schedule risk, not documentation debt.

### What the run changed in the design

- **Phase 2.5, self-consistency, added.** Pairwise edges structurally cannot catch a document that contradicts its own other section, and a summary that faithfully copies one of two conflicting internal figures reads correct on every edge. Found exactly this: one estimate stated its sprint total two ways, a week apart.
- **Recency moved to config (`as_of`).** The Notion fetch path returns only a retrieval timestamp, never `last_edited_time`, so automated staleness ranking would have marked every artifact equally fresh. For a constraint register the right value is its own stated verification date, which is usually older than its last edit and is the figure that matters.
- **§5.1 added** — artifact-topology quorum, the run's most useful discovery.

### Honest scoring against §12's exit criteria

| Criterion | Result |
|---|---|
| Runs end-to-end without manual intervention | **No.** 3 of 10 edges, manually orchestrated |
| >=80% contradiction recall on a labelled sample | **Unmeasurable.** No corpus exists (Q1) |
| <=20% false-positive rate | **Pending human adjudication** |
| Under per-stage token cap | **No cap set.** ~78k/edge actual |
| Adjudicable in under 15 minutes | Believed met, untested |

Two of five met, one pending, two blocked on things this doc already tracks as open questions. Stage A is useful but not yet gated, and must not be promoted to `claude-plugins` on this evidence (C3).
