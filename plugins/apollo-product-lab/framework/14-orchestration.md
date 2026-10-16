# 14 — Orchestration: agent resolution and the review cycle

> Companion to [12-product-harness.md](./12-product-harness.md) and [13-model-routing.md](./13-model-routing.md).
> **Status: draft for review. Nothing binding.**
> This is the top of the stack. Everything else in the framework is stages and workers; this is what routes.

> **Naming correction (2026-09-08).** This component is a **router**, not an orchestrator-workers pattern. The canonical distinction is that in orchestrator-workers *"subtasks aren't pre-defined, but determined by the orchestrator based on the specific input."* Ours routes to a **fixed roster** of existing agents and cannot create one without human approval — that is a classifier directing work to a specialised followup.
>
> The correction is worth making because every consequence is an improvement: routing is **testable as a labelling problem** against a fixed label set, it can run on a **cheap model** rather than Opus, and its failures are **legible** — it picked the wrong label and you can see which. Calling it an orchestrator invites reaching for dynamic decomposition we have deliberately forbidden.
>
> The one genuinely orchestrator-shaped decision it makes — proposing a *new* agent — is gated on a human, which is precisely why everything else is routing.

## 1. Why a router is structurally required

Sub-agents cannot talk to each other. A sub-agent's context is its own body plus the delegation prompt plus CLAUDE.md plus git status — no parent history, no sibling messages. Depth caps at 3, concurrency at 20.

So there is exactly one place where handoffs, consolidation and rejection-routing can happen, and it is the supervisor. This is not a design preference; it is the platform's shape. It also means the supervisor is the context bottleneck, which is why every worker's return is capped and why the supervisor never does work itself.

The role is played by `product-orchestrator`. In the vocabulary the team already uses, it is the engineering manager: it staffs, sequences, and unblocks. It does not build, review, or decide compliance.

## 2. The registry, and what is deterministically resolvable

Resolution should be config-driven first and model-driven only for the residue. Available today:

| Source | Answers |
|---|---|
| `.claude/agents/*.md` frontmatter | What agents exist and, in prose, what they cover |
| `surface-owners.yml` | Product surface → owning team |
| `apollo-dev-teams.yml` | Path → owning team; `.claude/` and `.ai/` are wholesale `@apolloio/agentic-engineering` |
| `.ai/<initiative>/document-graph.yml` | Which initiatives are registered, and their artifacts |
| `.ai/<initiative>/harness-manifest.md` | Archetype, therefore the legal surface set |
| `.claude/skills/` + `claude-plugins` inventory | What can be done without an agent at all |

**The gap: capability is declared in prose, not structure.** An agent's `description` is a sentence, so step 2 of resolution is an LLM match rather than a lookup. That is the difference between a resolver that is auditable and one that is plausible. See Q-O1.

## 3. Resolution order

Walk in order, stop at the first fit, and record which step resolved it.

1. **A skill covers it.** Cheapest unit, no registry entry, and per D3 the one engineers may ship freely.
2. **An existing domain agent's surface covers it.** Match on surface, not vocabulary.
3. **An adjacent initiative's agent covers it.** The highest-value reuse and the easiest to miss: a campaign-building feature inside a new initiative is still campaign-building, and belongs to whoever owns campaigns. Check `surface-owners.yml` before assuming novelty.
4. **A standing reviewer covers it.** Domain agents contribute *memory*, not review capability. Never create a domain reviewer that duplicates `backend-reviewer`, `frontend-reviewer`, `security-reviewer`, `db-perf` or `pr-tech-lead-synthesizer`.
5. **Propose a new agent** — a proposal, never an action.

## 4. Spawn policy, and the arithmetic behind it

This repo already carries ~123 skills and ~24 agents. An agent empowered to create agents will produce hundreds, each one context to load and maintain. **Sprawl is this role's default failure mode.**

Creating an agent requires all of:

- **Human approval.** A persisted bad agent is worse than no agent, because it will be trusted.
- **A registered initiative with an archetype**, so the surface set is principled rather than invented.
- **A surface from that archetype**, not a role title or a seniority level.
- **At least one seeded knowledge section.** An empty knowledge file makes a confident stranger; run Stage A or B first.
- **A second use, present or clearly imminent.** One-off work is a direct call.

**Cap: agents per initiative = surfaces in its archetype.** Five archetypes × 1–3 surfaces bounds the whole system at a reviewable number. Without the cap, N initiatives × M plausible roles is unbounded.

And register what gets created — an unregistered agent is invisible to the next resolution pass, gets recreated, and that is exactly how sprawl compounds.

## 5. The cycle model

The stage list A–H reads as a pipeline. It is not one. **The feedback edges are the harness**, and until now they were undefined.

Route a rejection to the stage that **produced** the defect, not the stage that found it.

| Rejection surfaced at | Finding class | Routes to | Also |
|---|---|---|---|
| A. Audit | `mutually-exclusive-claim` | The artifact judged wrong; if authority and recency disagree, the human | — |
| A. Audit | `unestimated-requirement` | C (scope) and the estimate owner | Usually the highest schedule risk |
| A. Audit | `stale-relative-to-sibling` | Owner of the stale artifact | — |
| A. Audit | `unowned-decision` | B, whose arbiter assigns an owner | — |
| B. Research | Claim without a source | B, same specialist | Tier the claim or drop it |
| E. Panel | Seam or interface defect | `slice-contract-keeper`, then F | — |
| E. Panel | Scope or requirement defect | C | — |
| E. Panel | Design or constraint defect | D | — |
| E. Panel | Data-model or blast-radius defect | F, with the scope gate tightened | — |
| Human gate | Any | The producing stage | **Always** a Stage H ledger entry |
| F. Build | Semantic conflict across slices | `slice-integrator`, then the owning slice | — |
| G. Verify | Implementation bug | F | — |
| G. Verify | Spec gap | C | **A should have caught this — eval-case candidate** |
| G. Verify | Design divergence | D | — |
| G. Verify | Constraint violation | Compliance constraint-checker, human arbiter | Never auto-resolved |

Two rules make the loop converge rather than thrash:

**Every rejection produces a Stage H ledger entry.** A rejection nobody records is a lesson lost, and Stage H is the only mechanism by which this system improves. The entry routes into the relevant domain-owner knowledge file, because learning that lives somewhere nobody reads is not learning.

**Cycle budget: two iterations per gate, then escalate with the disagreement stated.** Unbounded retry looks like diligence and is thrash. Same reasoning as a `Stop` hook auto-overriding after 8 consecutive blocks: a loop that cannot terminate is not a safeguard.

## 6. Human gates across cycles

Gates sit at **cycle boundaries**, where an artifact becomes input to a different function:

| Gate | After | The human is judging |
|---|---|---|
| G1 | A + B | Are the findings real, and is the problem agreed? |
| G2 | C + D | Is the *what* agreed, including which design option survives? |
| G3 | E | Is the *how* agreed? The expensive gate — it authorises build |
| G4 | F | Is the diff acceptable? |
| G5 | G | Ship or not |

**The honest count is not five.** It is five plus one per rejection, because a rejection re-enters at the producing stage and re-runs its gate. So a contested initiative might see a dozen gate events.

That collides directly with the measured habituation effect — across 11,429 agent-authored reviews, approval rate rose 14.5pp and inline comments fell 22%, agent-specific. **More cycles means more gate events means faster habituation.** Which is the same constraint as the cycle budget, seen from the other side, and it yields three requirements:

1. **Gates present a structured findings diff, never prose.** A gate that costs ten minutes of reading gets rubber-stamped by the fourth iteration.
2. **Approval rate is tracked as a harness health metric.** A rising rate is the warning sign, not a success signal.
3. **Prefer fewer, sharper gates.** If a check can be deterministic, it should be a check and not a gate — that removes a human decision rather than automating one.

Enforcement is unchanged: gates are `PreToolUse` hooks, which fire before the permission check and cannot be overridden by the model. A gate the model can decline to honour is not a gate.

## 7. Worked shape

For a platform-integration initiative with an existing adjacent product:

```
G1 ──────────── G2 ──────────── G3 ──────────── G4 ── G5
 │               │               │               │     │
 A ── B          C ── D          E               F     G
 │    │          │    │          │               │     │
 │    ├ codebase ├ competitive   ├ seam          ├ slice owners (N = independent slices)
 │    ├ external ├ business case ├ data-model    ├ contract keeper
 │    └ precedent├ scope slicing ├ failure-mode  └ integrator
 │               └ arbiter       ├ blast-radius
 │                               └ arbiter (cross-family voter when M2 clears)
 │
 └ deterministic: schema, self-consistency, freshness, coverage

 Compliance: not a stage. Validates against every box above. Human arbiter.
 Domain owners: not a stage. Consulted before each box, appended after.
 Rejections: route per §5. Every one writes to Stage H.
```

The orchestrator resolves each box against §3 before instantiating anything, and most boxes on a brownfield initiative resolve to an existing agent or a skill.

## 8. Selection at scale: the registry must be queried, not read

The design above assumes the orchestrator can read the registry. **At hundreds of agents that stops being true, and the failure is arithmetic rather than architectural.**

An agent's `description` truncates at 1,536 characters. Three hundred agents at even 200 characters each is ~60k tokens spent listing candidates before any reasoning happens — on every routing decision. The orchestrator is already the context bottleneck; this would consume it.

So beyond a certain node count, **resolution is a retrieval problem, not a prompt problem.** The registry becomes a queryable index; the orchestrator queries it deterministically and reasons only over the top handful of candidates. This is the same shape as exposing MCP as a code interface rather than loading every tool definition — one reported case went from 150k tokens to 2k.

### Three tiers, and the edges between them

| Tier | Cardinality | Unit of specialisation |
|---|---|---|
| Orchestrator | 1 | Routing. Holds the index; owns every handoff |
| Agents | hundreds | One domain surface each. Carries accumulated memory |
| Skills | hundreds | One capability each. Composed by agents |

An ads-builder agent uses an audience-sync skill and a Google-Ads skill; the agent is *where the domain memory lives*, the skills are *what it can do*. That separation is why agent count grows with surfaces (bounded) while skill count grows with capabilities (unbounded but cheap).

### Node and edge model

| Edge | From → To | Source |
|---|---|---|
| `covers` | agent → surface | Agent frontmatter `surfaces:` (Q-O1) |
| `uses` | agent → skill | Agent frontmatter **`skills:`** — already a supported field |
| `owns` | agent → initiative | `.ai/<initiative>/harness-manifest.md` |
| `touches` | skill → path or pack | Skill frontmatter `paths:` |
| `owned_by` | surface → team | `surface-owners.yml` |
| `resolved` | task class → agent | **The Stage H ledger** |
| `rejected` | task class → agent | The Stage H ledger |

The structural edges come **free from frontmatter** once `surfaces:` exists — `skills:` is already a real sub-agent field, so the agent-to-skill binding is expressible today without any new mechanism.

### Weight by outcome, not usage

This is the part worth getting right, because "choose agents based on usage" has a specific failure mode.

**Frequency-weighted routing is rich-get-richer.** Whatever got picked early gets picked again, and a better-fitting agent introduced later never accumulates the usage needed to be selected. Classic explore/exploit trap, and in this setting it silently locks in an early accident.

**And usage is not success.** An agent invoked 100 times whose output was rejected 40 times is worse than one invoked 5 times with zero rejections. Frequency cannot distinguish them; outcome can.

So the edge weight is **outcome-derived**: resolved-without-rejection, minus rejections routed back to that agent, per task class. Three consequences:

1. **The Stage H ledger is the training signal.** Every rejection already records the producing stage and routes to a domain-owner knowledge file (§5). That is exactly the negative signal the index needs, which closes a loop the framework had left open — Stage H stops being only a memory and becomes the thing that improves routing.
2. **Structural match is the prior; outcome is the update.** A newly created agent has no history, so pure usage-based selection could never select it. Declared `surfaces:` gives it a starting score; outcome adjusts from there.
3. **Reserve a small exploration budget.** Occasionally route to the second-best candidate and record the outcome. Without it the index cannot correct an early mistake. Keep it small and log it as exploration, so a worse result is attributed rather than mysterious.

### Generated, never hand-maintained

At hundreds of nodes hand-curation fails silently — the index drifts from reality and routing degrades without anyone noticing. So the index is a **build artifact**: a step reads agent and skill frontmatter, the ownership YAMLs, the initiative manifests and the ledger, and emits it. Stale index becomes a CI failure rather than a mystery.

### Deprecation is the automatic anti-sprawl mechanism

The orchestrator's spawn gate (§4) resists sprawl at creation time, which is necessary but manual. An outcome-weighted index gives the other half for free: it can enumerate agents that are **never selected**, or **always rejected**, or whose surface is now covered by a better-scoring sibling.

That converts anti-sprawl from a judgment call into a report. Retirement still needs a human, but the candidate list stops requiring anyone to notice.

### Build it now, or later?

**Later, deliberately.** At ~24 agents a five-step ordered walk over frontmatter is correct and a graph is over-engineering. The threshold where retrieval starts to pay is roughly **50 agents**, or the first time listing candidates costs more than reasoning over them.

What to do **now**, because it is cheap and blocks nothing:

- Add `surfaces:` to agent frontmatter (Q-O1) and use `skills:` where an agent composes skills. That makes the structural edges exist before anything needs to query them.
- Have the Stage H ledger record `{task class, agent, outcome}` from the start. Outcome history cannot be reconstructed retroactively, so not recording it now is the one decision here that is expensive to reverse.

## 9. Hierarchy: a pipeline DRI over domain orchestrators

The intended shape: one high-level orchestrator per project acting as **pipeline DRI**, with a per-domain orchestrator owning that domain's agents, and orchestrators exchanging information while keeping the DRI in the loop.

That is the right shape. Two platform limits determine how it can actually be built, and both are hard rather than negotiable.

### Limit 1 — depth caps at 3, and nesting exhausts it immediately

Sub-agent spawn depth is capped at 3. So an in-session hierarchy spends its entire budget on the org chart:

```
main session        depth 0
└─ DRI orchestrator depth 1
   └─ domain orch.  depth 2
      └─ worker     depth 3   ← cannot spawn anything
```

A function team survives this only because its specialists and arbiter are **siblings at depth 3**, not nested. But Stage F does not survive it: a slice owner at depth 3 that needs to run `auto-pr` — which itself dispatches reviewers — is trying to reach depth 4.

**Conclusion: in-session nesting supports two orchestrator tiers only if the leaf workers never fan out.** That is too fragile to build on.

**The fix is separate runs, not nested sub-agents.** Each domain orchestrator becomes its own Pantheon run, triggered by the DRI rather than spawned inside it. Depth resets per run, so each tier gets a full budget. This also buys three things for free: an audit record per run, retries, and per-run `provider`/`model` selection — the descriptor schema already carries both fields, and 16 descriptors already exist. Q-O3 now has an answer: **the DRI may be interactive in-session; domain orchestrators should be runs.**

### Limit 2 — orchestrators cannot talk to each other

Sub-agents cannot message each other, at all. So "orchestrator talks to orchestrator" is not implementable as messaging. Two alternatives:

| Approach | Mechanism | Cost |
|---|---|---|
| Star topology | Everything relays through the DRI | The DRI is already the context bottleneck; relaying routine exchange consumes exactly the context it needs to route |
| **Shared artifact** | Peers write to a versioned file; the DRI is notified | Async, auditable, survives session boundaries |

**Take the second, and recognise what it already is: a cross-domain handoff is a contract, not a message.**

That is not a workaround, it is better than messaging on three counts. A message is ephemeral and unauditable; a contract is a diffable artifact with a named owner. A message needs both parties live simultaneously; a contract does not. And the design already has an owner for it — `slice-contract-keeper`, whose surfaces now include `harness.cross-domain-handoff`.

So the exchange protocol is:

1. Domain A needs something from domain B. A writes a **handoff request** into the shared contract, stating what it needs and why.
2. The contract keeper adjudicates the interface — signature, error semantics, ownership, retry ownership — exactly as it does for slice seams.
3. Domain B consumes the contract read-only. It may **request** a change; it does not edit.
4. The DRI is **notified** of the contract and its consumers, and **adjudicates only conflicts**.

### Keeping the DRI in the loop without making it a bottleneck

The failure mode is specific and worth naming: **a DRI in the path of every exchange either fills its context or becomes a rubber stamp.** The habituation effect applies to an agent DRI as much as a human one — and if the DRI is human, it applies literally and is measured.

So the DRI's involvement is tiered:

| Event | DRI involvement |
|---|---|
| Routine cross-domain read of an existing contract | None. Logged, not surfaced |
| New contract created, or a consumer added | **Notified.** No approval needed |
| Contract change request | **Adjudicates**, or delegates to the contract keeper |
| Two domains disagree on ownership or semantics | **Decides.** This is the DRI's actual job |
| A domain exhausts its cycle budget | **Escalated to**, with the disagreement stated |
| Any spawn-gate request | **Approves or declines** (§4) |

### DRI is a role, not only an agent

Keep these distinct or accountability blurs: **the pipeline DRI is a named human**, recorded in `.ai/<initiative>/harness-manifest.md`; `product-orchestrator` carries `role: dri` and acts *for* that human. Every gate escalation resolves to the named person, not to the agent.

Domain orchestrators inherit the same split: the domain has a human owner (from `surface-owners.yml`) and an agent that routes within it.

### What this needs before it works

- A **domain-orchestrator template** — same resolution order and spawn gate as the DRI, scoped to one initiative's surfaces, with no authority to create agents (that stays with the DRI's gate).
- A **handoff-contract format**, which is the existing contract format plus `requested_by` and `consumers`.
- **Pantheon descriptors** for domain orchestrators, so the tiering is runs rather than nesting.
- The `initiative:` frontmatter field, so a domain orchestrator can enumerate its own agents deterministically. Now present on the annotated agents.

Nothing here is blocked; it is all mechanical once the DRI tier has run once in anger.

## 9b. Dispatch rules a past Ads M1 build paid for

- **Trust the artifact, not the report.** A slice owner reported a fix applied while the file still held
  the code it claimed to remove; only an independent re-read caught the mismatch, and investigating it showed the surviving code was
  correct in its context. Every dispatch result is reconciled against disk (doc 33) before it counts, and a
  mismatch is investigated, neither trusted nor rejected blindly.
- **Narrow context for side tasks.** A background agent that inherited the whole conversation, asked to do
  one narrow job, re-ran owned work and built a second implementation of the product in another folder.
  Give an independent side task a fresh agent with a tight brief; reserve full-context forks for work that
  needs the whole thread.
- **One product, one home.** A greenfield product's package or folder is decided before any slice is
  dispatched, so parallel slices cannot pick different locations.

## 10. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q-O1 | ~~Should agent frontmatter carry structured `surfaces:`?~~ **Done.** Convention and rationale in [ledger/README.md](./ledger/README.md); applied to the six harness agents. **Remaining: the ~18 pre-existing agents are unannotated**, so the resolver still falls back to prose for them. Mechanical, worth finishing before the index is built | author | Full deterministic resolution |
| Q-O2 | Where does the initiative registry live? Today it is implied by the existence of `.ai/<initiative>/document-graph.yml` — works, but not enumerable without a directory scan | author | Multi-initiative use |
| Q-O3 | ~~Sub-agent or Pantheon descriptor?~~ **Answered by the depth limit (§9): the DRI may be interactive in-session, but domain orchestrators must be separate runs.** In-session nesting spends the depth-3 budget on the org chart and breaks any leaf worker that itself fans out. Remaining: write the descriptors | AI Tooling + Platform | Hierarchy beyond one tier |
| Q-O6 | **Blame attribution across a chain is unsolved.** A rejection at G3 may be a scope defect Specify produced and Design carried forward. The routing table picks a producing stage, but that is a judgment, and mis-attribution poisons the selection signal. Mitigated for now by `attribution_confidence` in the ledger, with non-`sole` records excluded from weighting — a workaround, not an answer | author | Outcome-weighted selection going live |
| Q-O4 | Cycle budget of two — is that right? It is asserted from the thrash argument, not measured. First real initiative should record actual iteration counts per gate | author | Nothing; tune later |
| Q-O5 | Who owns the orchestrator's staffing decisions when it declines to create an agent someone wants? This is a real org question, not a technical one | Eng leadership | Adoption beyond one team |
