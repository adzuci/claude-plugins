---
name: product-harness-init
description: Bootstrap the product-development harness for a new or in-flight initiative. Classifies the product archetype, inventories existing artifacts to decide which stages fire, then emits a document-graph config, the domain-owner agent set, knowledge-file skeletons, and an external-acquisition plan with per-category source-tier requirements. Activate when the user says "set up the harness for PRODUCT", "bootstrap harness", "onboard INITIATIVE to the harness", "add a feature run to INITIATIVE", or runs `/product-harness-init [INITIATIVE] [--feature SLUG]`. Produces configuration and agents; it does not run any stage.
---

# Product Harness Init

You bootstrap the harness for one initiative. You **emit configuration and agents. You do not run stages.** Running is a separate, explicit act.

Read `${CLAUDE_PLUGIN_ROOT}/framework/12-product-harness.md` first for the stage model and the decomposition rule. This skill is its entry point.

**Storage first** (doc 45 §2). Before any read or write of the record, resolve the mode: a session with no Bash and no Write tool is `notion`; otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect` (with `--surface` from the profile's `surface:`, and `--profile <file>` when the profile came from Notion) and print its `say` line once. In `notion` mode every `.ai/<initiative>/...` path in this file names a record page under the initiative's records root (doc 45 §3): write with `storage.py to-notion` and the `notion-create-pages` call it prints, read with `notion-fetch` then `storage.py from-notion`, append ledger events with `storage.py ledger-entry`, and skip git, gh, local `shasum` and `record-sync.sh` (Notion is already shared). In `local` mode the rest of this file applies unchanged; on claude.ai/code, where the profile came from Notion, export `HARNESS_PROFILE=<the fetched profile file>` before any `record-sync.sh` call so team sync sees it (doc 45 §4). Notion mode emits no agent files (there is no `.claude/agents/` to write): list the domain-owner agents in the manifest record and emit them the next time the initiative is opened in a Code session.

**Repo state (local mode only).** In notion mode the initiative is a records root page `Harness record: <initiative>` under `notion_parent` (doc 45 §3): create it if missing, write every config and knowledge file below as record pages, and skip the git and repo rules in this paragraph. In local mode, an initiative lives in a product repo under `<repo root>/.ai/<initiative>/`. Resolve the repo root first with `git rev-parse --show-toplevel` (doc 43 §10); every `.ai/` path is relative to that root, not to the current subfolder. No git repo: say "no-repo mode: open the product repo (for example leadgenie) first; nothing written" in one line and stop. A repo with no `.ai/` at its root is the normal first run: create `<repo root>/.ai/` there. Never create `.ai/` in a subfolder or outside a repo.

## Step 0 — Size the work (product, feature, or fix)

Read `${CLAUDE_PLUGIN_ROOT}/framework/40-work-sizes.md`. If the ask is a **feature inside an existing
initiative** (`--feature <slug>` or the initiative already has `.ai/<initiative>/harness-manifest.md`):
do not classify an archetype and do not emit agents. Emit only `.ai/<initiative>/runs/<initiative>-<slug>/`
with an `index.md`, a `feature-manifest.md` (the one-line ask, the PRD or design delta to review, the
existing domain owners that will serve it, the stages that fire per doc 40, the council kind to run
first), and stop. If the ask is a **fix**, say the harness init is not needed and point to doc 40.
An existing manifest is not proof of feature size: if the ask adds a provider, a data class, consent
behaviour or an authority change, treat it as a **product** (new surfaces, research and readiness gates)
even though the initiative exists, and say so in the feature manifest you refuse to write. Only a
**product** continues to step 1.

## Step 1 — Classify the archetype

The archetype determines the domain surfaces, the external knowledge required, and whether compliance is load-bearing. **Getting this wrong produces a plausible but useless harness**, so do it before anything else and state the choice explicitly.

| Archetype | Domain surfaces | External knowledge | Compliance weight |
|---|---|---|---|
| **Third-party platform integration** | architect, backend, frontend | Platform API and policy — **primary source required** | High. Platform ToS plus regional law |
| **Internal workflow / tooling** | backend, frontend | Competitor UX only, secondary acceptable | Low |
| **Data / ML pipeline** | architect, backend, data | Vendor docs, papers; primary for model and licence terms | Medium. Data provenance and retention |
| **Developer / API product** | architect, backend | Competitor API design, secondary acceptable | Low to medium |
| **Pure UI surface on existing backend** | frontend | Design and UX patterns, secondary acceptable | Low |

Classify by asking what the product *depends on*, not what it looks like. A UI that talks to someone else's API is a platform integration, not a UI surface.

**Do not emit a three-surface domain trio by default.** A product with one meaningful surface gets one domain owner. Extra agents are coordination cost with no counterparty.

## Step 2 — Inventory artifacts, and derive which stages fire

Find what already exists: PRD, estimate, constraint or legal register, design artifact, tracker epic, prior research.

Then map each stage to `authoring` / `gap-fill` / `skip`:

- No PRD → Stage C authors
- PRD exists but has no metrics or acceptance criteria → Stage C gap-fills
- No design artifact → Stage D authors
- Design exists → Stage D evaluates options against constraints
- Constraint register exists → compliance is a cross-cutting source, and the invariant-extraction pass in step 5 runs
- No constraint register, high-compliance archetype → **flag it.** That absence is itself the first finding

**Never invent an artifact you could not find.** "No PRD located" is a valid inventory result and is more useful than a guess. If the user names an artifact you cannot reach (auth-gated, 403, permissions), record it as `known_unreachable` and say so — an artifact nobody can read has never been checked against anything.

## Step 3 — Emit the document graph

Write `.ai/<initiative>/document-graph.yml` from `${CLAUDE_PLUGIN_ROOT}/skills/artifact-audit/templates/document-graph.yml`.

Rules that decide whether Stage A is useful or noisy:

- **`as_of` on every artifact.** Recency cannot be detected automatically; a fetch returns only a retrieval timestamp. For a constraint register use its own stated verification date, not its last edit.
- **Edges are assertions, not associations.** Each edge means "these two should be consistent and I want to know when they aren't." Write a specific `reason`. "These are related" produces noise.
- **Keep edges under ten.** Each costs a sub-agent, and a real datum from the reference instance is ~78k tokens per edge.
- **Prefer three-way coverage on facts that matter.** When three artifacts cover one fact and one disagrees, the topology localises the error with no model voting at all. That is the cheapest verification in the whole harness — shape the graph to get it.

## Step 4 — Emit the domain-owner agents

For each surface from step 1, generate from `templates/domain-owner-agent.md`:

- `.claude/agents/<initiative>-<surface>.md` — thin, behaviour only
- `.ai/<initiative>/domain/<surface>.md` — the knowledge file, which is the actual asset

Substitute: initiative name, surface, the knowledge-file path, and the surface-specific review checks. Keep the three hard rules verbatim — never implement, never rewrite history, no decision entry without alternatives-rejected.

For the **architect** surface, `{{SURFACE_REVIEW_CHECKS}}` must include the roadmap lens from doc 17 §6.1, verbatim:

> **Data-model review, before the first external read of an ERD:** (1) if the PRD or decision log names more than one provider, platform, channel, or tenant type, every entity and field is neutral, the variant is an enum field, extras live in one metadata hash; the test is *does the second one land as an enum value plus an adapter?* (2) every table carries a why-it-is-a-table paragraph and what was considered instead; a 1:1 table needs a reason that survives *what makes this 1:N later?* (3) an obligation whose identity already exists on another row is a state plus an operation record, not a table; (4) the reviewed document carries one model, with baselines in the decision log. Report pass or fail per check with the field or table named.

## Step 5 — Seed the knowledge files

An empty knowledge file makes a useless agent, and a fabricated one makes a dangerous agent. Seed only from what exists.

**If a constraint register exists, run the invariant-extraction pass.** This is the highest-value seeding step. Convert each register item that gates a milestone into a **checkable assertion** with an ID and a source reference, and record which are pending versus settled. Prose obligations become code-review-able invariants.

Also seed, where the sources exist: undecided decisions with what each is blocked on; rejected approaches with reasons; enumerated enforcement points for the backend surface; enumerated required states for the frontend surface.

**Where a section has no source, write that the section is thin.** Every generated agent carries a standing instruction to say the record is thin rather than fill the gap with plausible domain knowledge. Honour it in the seed.

## Step 5b — Set the design source (any initiative with a frontend surface)

The harness's design workbench is **Fabric Studio** (`apolloio/fabric-studio`), for every
initiative, because a prototype there is real `@apolloio/fabric-core` code that ports to production
as a diff. Figma stays canonical; production stays production. Doc 17 §3 has the rationale.

Emit, in `.ai/<initiative>/domain/frontend.md`, a **Design source** block:

| Field | Value |
|---|---|
| Figma file / node | url + node id, or `none` |
| Figma approved revision | version or date; `pending` |
| Fabric Studio branch | `prototype/{owner}-{initiative}` (or `none yet`) |
| Prototype approved revision | sha; `pending` |
| Module path | `src/prototypes/{id}/` |
| Preview | `fabric-studio-{branch-slug}.staging.apollo-forge.io` (VPN) |
| Storyboard | `<preview>/storyboard` (all pages on one screen) |
| Components in scope | list; name any folders that are demo scaffolding, not spec |
| Designer | who updates the branch |

If no prototype exists yet, Stage D authors one there. The profile's `design_workbench` may name
Claude Design or Figma-only instead (doc 17 §3); record it in the block and note that `design-diff` then
reviews by screenshot and state, not by code diff.

Setup a designer or agent host needs once (from the Fabric Studio README): Apollo VPN, Node 22,
GitHub access to the Apollo org, Claude Code with the Figma connector enabled; clone
`https://github.com/apolloio/fabric-studio.git` and follow the paste-in prompt. Record in the
manifest whether the current host has it, because a surface owner without the clone cannot honour
the prototype-first rule below.

Substitute the frontend agent's `{{SURFACE_HARD_RULES}}` with, verbatim:

> **Prototype-first.** The design source is the Fabric Studio branch named in the knowledge file's
> Design source block. Before proposing or coding a UI change, read the corresponding prototype
> component and state (a) what the prototype does, (b) what production does, (c) whether the gap is a
> port, a compliance override (the constraint register wins), or an engineering constraint. Never
> invent layout the prototype already answers. When production and prototype diverge, the gap list
> goes to the designer; production does not become a second design source.

## Step 6 — Emit the external acquisition plan

Greenfield domains seeded only from internal artifacts inherit the organisation's blind spots. Emit `.ai/<initiative>/domain/external/README.md` listing what to acquire, at what tier, with what decay:

| Category | Tier required | Decay |
|---|---|---|
| Platform API contract, quota, deprecation | **Primary** | Weeks |
| Platform or regional policy | **Primary** | Weeks |
| Competitor feature, pricing, positioning | Secondary acceptable | Quarterly |
| UX flow, state vocabulary | Secondary acceptable | Yearly |

Every claim carries a tier (`[P]`/`[S]`/`[U]`), a URL, and a retrieval date. **An unsourced claim is deleted, not hedged.**

State the tooling reality plainly: if `WebFetch` is unavailable, acquisition can only reach search summaries, which caps everything at `[S]` — below the bar for API, policy and compliance categories. In that case mark those files provisional and list the claims a human must verify against primary docs.

## Step 6b — Emit the run scaffold and the initiative's model routing

- Create `.ai/<initiative>/runs/` with an empty `README.md` stating the snapshot rule (doc 33): every
  stage writes `runs/<run-id>/<stage>.snapshot.md` from `templates/stage-snapshot.md` and starts by
  reading the previous one. The first run id is `<initiative>-run1`.
- Write `.ai/<initiative>/model-routing.md` by resolving each surface's roles in
  `${CLAUDE_PLUGIN_ROOT}/framework/models/model-registry.yml`, and set `model:` in each emitted agent's
  frontmatter to the resolved id. State which routes need shunt and whether it is running on this host.
  Never leave a model id only in prose.
- Append the ledger file `.ai/<initiative>/ledger.jsonl` (empty) so the first delegation can be recorded.
- For a team profile the new `.ai/<initiative>/` must be tracked before `record-sync.sh` can push it: `git add .ai/<initiative> && git commit -m "<initiative>: harness init"` on the feature or `<ticket>/harness-artifacts` branch, then `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-sync.sh" push <initiative>`. Say which branch it landed on.

## Step 7 — Emit the manifest

One file, `.ai/<initiative>/harness-manifest.md`:

1. Archetype, and why
   1b. `notion_parent`: the Notion page every human-facing record of this initiative publishes under (doc 33). Create it if the person names none.
   1b2. `escape_maintainer`: who adjudicates escapes for this initiative (doc 43 §2.3). Ask once: "Who adjudicates escapes for this work? Usually the EM." Write the name, or `unowned` and list it under item 5.
   1c. PR plan: the stamp line `Harness run: <initiative>/<run-id>` on every PR (doc 20 §8c); the feature-flag name that lets new surfaces merge dark, and the FE/BE split (doc 20 §8b)
1. Artifact inventory, including anything unreachable
1. Per-stage disposition (authoring / gap-fill / skip) with the reason
1. What was created, by path
1. **What needs a human before any stage runs** — unreachable artifacts, absent constraint register in a high-compliance archetype, unresolved decisions that block Stage F, any claim capped below its required tier, and a missing Fabric Studio clone or prototype branch when a frontend surface exists
1. Suggested first stage, which is almost always Stage A, because it is deterministic, cheapest, and its output seeds everything else
1. **Entry points by role** (doc 36): the `/harness-council <initiative> <kind>` commands a PM, designer, engineer and QA will use, and which gate each owns

## Hard rules

- **You emit; you do not run.** Not Stage A, not acquisition, nothing. The manifest ends with a recommendation, not a result.
- **Never fabricate an invariant.** A wrong invariant is worse than a missing one: it will be enforced in review and nobody will re-check it.
- **Archetype drives surfaces.** Do not emit agents for surfaces the product does not have.
- **Refuse politely when the initiative is too small.** A single-slice change does not need a harness. Say so and stop; the overhead exceeds the work.
- **No silent caps.** If you skip an edge, a surface, or a knowledge section, say which and why in the manifest.
