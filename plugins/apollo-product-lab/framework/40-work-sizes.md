# 40 — Not everything is a new product: product, feature, fix, and how the pod scales down

> The harness was designed around an MVP (Ads M1). Most work is a feature request inside an
> existing initiative, or a fix. The same pod (product, design, architecture, engineering, QA,
> research, adversary) still reads it; what changes is which stages fire, how many agents, and how
> many human gates.

## The three sizes

| Size | Examples | Stages that fire | Agents | Human gates | Record |
|---|---|---|---|---|---|
| **Product** (MVP, v1, new integration) | Ads Audience Sync M1 | A audit → B research → C specify → D design → E council → F build (slices) → G verify | new domain owners from `product-harness-init`, full council | G0, G1, G2a/b, G3, G4a/b, G5a/b | new `.ai/<initiative>/`, `runs/<initiative>-run1` |
| **Feature** (inside an existing initiative) | Members tab, status Check now, a LinkedIn destination | A-lite (PRD delta vs constraint register) → C gap-fill → D delta on the Fabric Studio branch → E council (prd or design kind) → F build (one or two slices) → G verify | the initiative's existing domain owners + standing reviewers; council on the delta | G2a (worth building) folded into the council memo, G3, G4a, G5a | `runs/<initiative>-<feature-slug>` under the same initiative |
| **Fix** (bug, copy, incident follow-up) | wrong pending copy, a flaky CI shard, an index that fails hygiene | F build → G verify, with `code-review`; council unless it is demonstrated low risk under doc 43 §6 | one slice owner + reviewers | G4a | one snapshot `runs/<run>/F.fix-<slug>.snapshot.md`, or none only when it is demonstrated low risk under doc 43 §6 (a one-file index or behaviour change is medium, not a fix) |

**A fourth case: a change to an existing Apollo product with no harness folder.** This is the most
common case (doc 43 §7). It is sized like any other change (doc 43 §6: high, medium or low, highest
trigger wins, the whole change including related PRs). Intake bootstraps a light initiative whose first
snapshot is the current behaviour map (doc 43 §4: the real code path end to end, with functions and
specs) plus the owning teams (doc 43 §5). It creates no new agents. Lenses are chosen by what the change
affects, not by whether users can see it, and medium or high work gets one cross-family review of the
design and one of the PR (doc 43 §6).

Several people on one feature share one run and follow doc 41's sync rules. The router (`product-orchestrator`) decides the size first and says which stages it skipped and why.
Skipping a stage is fine; skipping it silently is the defect.

## What a feature run reuses and what it adds

Reuses: the initiative's knowledge files and invariants, the Design source block (the designer adds
to the same prototype branch), the model routing, the ledger. Adds: one run directory, a council on
the PRD or design delta, and a snapshot per stage that fired. It never creates agents; if a feature
needs a surface the initiative lacks (a new provider adapter), that is a router escalation, not a
quiet new agent.

## How to start each size

- Product: `/product-harness-init <initiative>` then Stage A.
- Feature: `/product-harness-init <initiative> --feature <slug> "<one-line ask>"` (emits the run
  directory and a feature manifest; no new agents) then `/harness-council <initiative> prd|design "<ref>"`.
- Change to an existing product with no harness folder: `/harness-intake "<one-line ask>"`; it
  asks the three-way question and writes the behaviour map first (doc 43 §7).
- Fix: `/harness-snapshot read <initiative> <run>` to load the record, build with the slice owner,
  `/code-review`, and a snapshot if a decision was made.

Reuse first: doc 38 maps the 135 repo skills and the marketplace plugins to these stages; a fix that
matches an existing skill (`ci-speed-run`, `feature-flag-cleanup`, `oncall-triage`) uses it.
