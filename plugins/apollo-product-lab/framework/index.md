# Apollo AI Engineering Framework

> **Status**: Proposal — Decisions made · **Author**: Eng Productivity · **Last updated**: 2026-09-18
>
> This is the canonical home for Apollo's Claude Code / agent strategy.
> All planning artifacts live in this folder and are versioned in `apolloio/leadgenie`.

______________________________________________________________________

> **What ships in the plugin.** Only the documents the skills and agents read at runtime: the product-harness
> contract (12–14, 16–22, 26) and the pilot-derived operating docs (30–43, `platform-rules.md`), plus `models/`, `templates/`,
> `ledger/`, `references/`, `reviews/`. The strategy, roadmap and phase-review documents that preceded them
> (00–11, 15, 23–25, 27–29, `authority/`, `harnesses/`, `pantheon-descriptors/`, `phase-reviews/`) stay in
> `apolloio/leadgenie` under `.ai/claude-skills-framework/` and will move to Notion; a link to one of them from a
> shipped doc is a pointer to that record, not a runtime dependency.

## Read this first

| Doc | What it answers |
|---|---|
| [32 — Model registry](./32-model-registry.md) | One harness, many model families, any host: `models/model-registry.yml`, shunt routes, independence rules, Glean's honest lane |
| [33 — Stage snapshots](./33-stage-snapshots.md) | The conversation is not the record: deterministic per-stage snapshots on disk as the only handoff (skill `harness-snapshot`) |
| [34 — The council](./34-harness-council.md) | Every change read by product, UX, architecture, backend, frontend, QA, research and an adversary in parallel on different families; one memo, one human (skill `harness-council`) |
| [35 — Run on any host](./35-run-on-any-host.md) | Claude Code, Codex, `claude -p`: what differs, the generated Codex view, advisory gates |
| [36 — Quickstart by role](./36-roles-quickstart.md) | What a PM, designer, engineer, or QA runs, what they get, which gate they own. Start with `/harness-onboard` |
| [37 — Model bridge and context budget](./37-model-bridge-and-context-budget.md) | OpenAI reviewers with repo access via shunt agents; model chosen by input size; three families: Anthropic, OpenAI (Astra xhigh, Sol by effort), Glean (research, images, publishing); hosts swap base and adversary |
| [38 — Skill reuse map](./38-skill-reuse-map.md) | The 135 repo skills and marketplace plugins mapped to stages and personas: use, wrap, or skip |
| [39 — Connectors setup](./39-connectors-setup.md) | Every connector and tool the harness uses, by persona, with one-time setup; read by `/harness-onboard` |
| [40 — Work sizes](./40-work-sizes.md) | Product vs feature vs fix: which stages fire, how the pod scales down, how each starts |
| [41 — Collaboration and distribution](./41-collaboration-and-distribution.md) | Framework lives in the `apollo-product-lab` plugin, product artifacts in the product repo; solo vs team onboarding question; git sync rules for a shared initiative |
| [42: AI opportunity lens](./42-ai-opportunity-lens.md) | Where an assist, score or automation would remove work for the user; a human go-ahead per proposed assist |
| [43: Learning loop and review defaults](./43-learning-loop-and-review-defaults.md) | Escapes (misses found after a gate) captured and adjudicated; current behaviour map before design; owning-team check; sizing; one cross-family review on medium and high work; plain-language check; no-repo mode |
| [44: Dispatch rule](./44-dispatch-rule.md) | Every lens runs through the agent whose model its role names, never `general-purpose`; `scripts/served-models.sh` reports which family actually answered |
| [45: Web mode and storage](./45-web-mode-and-storage.md) | Run records in `local` files or Notion record pages with one schema; detection per surface; profile on Notion for claude.ai; designer defaults; packaging for claude.ai/code and chat |
| [46: Build and review loop budget](./46-build-and-review-loop-budget.md) | Specs in the running container, affected specs while iterating and the full suite once, at most 10 mutants once at the end, two cross-family passes then a human, review prompts of 15,000 characters or fewer, and a loop report of minutes per stage |
| [47: Platform lens](./47-platform-lens.md) | When a capability has siblings elsewhere in Apollo: feature parity, shared flow and shared backend rows, each with a platformize now / do locally and record / never question and the owning team's answer; skipped with a recorded reason otherwise |
| [48: Reuse first and implementation models](./48-reuse-first-and-implementation-models.md) | A reuse scan on every slice and design (other callers of what you call first), duplicating a found candidate is a major; Fabric components strictly on the frontend; every failing check and review comment read before a PR is called ready; implementation on Sonnet 5.5 by default, Opus 5.5 on named triggers |
| [49: Autonomy, progress and context intake](./49-autonomy-progress-and-context-intake.md) | Independent local steps run in parallel without a go; a one-line progress pulse with a percentage every 5 to 10 minutes; intake reads the existing PRD, design or ERD first and asks only open decisions (grilling method) |
| [50: The pr-ready review gate](./50-review-gate.md) | Before a PR is ready, reviewed by a human or merged, the AI review must have run on the current head and its findings triaged; block or warn mode, Claude Code hook plus a standalone script |
| [51: Sub-agents: when to delegate, and the guards](./51-sub-agents.md) | Research, wide code lookups, lenses and per-slice builds go to sub-agents; depth 2, every brief states its depth, width bounded by budget (concurrency 20 is non-overridable), one retry, no self re-delegation, agent CLIs count as sub-agents with one cross-family-review leaf exception, harness agent types have no Agent tool |
| [52: Process scripts](./52-process-scripts.md) | Advisory checks for preview deployments, CI diagnosis, stacked-branch sync and evidence-backed status reports |
| [53: Tracker updates and the intake grill](./53-updates-and-grill.md) | Each persona chooses Jira, Notion or both for stage updates; every intake completes and validates a role-specific grill |
| [54: Rule registry and lifecycle](./54-rule-registry.md) | Evidence-bound review rules, candidate/shadow/active/retired states, paired removal probes, and human-approved promotion or retirement |
| [Apollo infra patterns](./apollo-infra-patterns.md) | IP1 to IP18: batching, fan-out, job args, Redis, embedded changes, paging, status filters, concurrency, reuse, shard keys, wiring and test gaps; each with a real example and the review check. Read by the architect, the infra lens and the backend, db-perf and security reviewers |
| [ERD template](./templates/erd.md) | Required Load model (§5) and cross-family review record (§8) for every design (doc 17 §6.2, §6.3) |
| [Platform rules](./platform-rules.md) | Apollo platform facts the architecture, backend and db-perf lenses check row by row, each with a source and an owner |
| [Escape records](./eval/escapes/) | One record per adjudicated escape; replay fixtures when the originals were archived |
| [Reviews](./reviews/) | Independent reviews of the framework and team feedback: Astra 2026-09-19 (+ status), team feedback 2026-09-21 |

### Skill specs (examples authored as part of this proposal)

______________________________________________________________________

## TL;DR

Apollo already has 5 parallel agent/skill efforts — `claude-plugins` marketplace, `agent-swarm-workshop`, `agent-platform` (Pantheon), `vertical-agent`, and `dapi/agent_framework`. **The decision is not "skills vs sub-agents" — it is which existing piece owns which layer, and what we stop building twice.**

We commit to a **3-layer architecture**:

```
Layer 4 — Distribution      apolloio/claude-plugins (marketplace)
Layer 3 — Runtime           apolloio/agent-platform (Pantheon · K8s/Argo)
Layer 2 — Orchestration     dapi/agent_framework pattern (supervisor + Pydantic plan)
Layer 1 — Sub-agents        .claude/agents/*.md (scoped tools, narrow prompts)
Layer 0 — Skills            .claude/skills/*/SKILL.md (knowledge + workflow)
```

**Year-1 outcomes** (committed):

- ≥60% AI-assisted PR first-pass approval (matches AITOOL-41 OKR)
- 25% cycle-time reduction on golden-harness teams
- 40% drop in DB-related incidents
- All 50+ leadgenie skills consolidated to ≤25, with ≥90% activation precision
- Every team has a named **harness maintainer** + replay eval suite green on `master`

______________________________________________________________________

## What this folder is NOT

- Not a place for individual skill READMEs — those live in `.claude/skills/<name>/`
- Not a replacement for JIRA — links to AITOOL-\* tickets where work is tracked
- Not where shared skills are distributed — that's `apolloio/claude-plugins`

The contents here are **strategy + audit + proposal**. Once approved, individual skill code lives in the codebase and is governed by the marketplace.
