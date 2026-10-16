# Harness ledger and the `surfaces:` convention

Two small conventions that everything in [14-orchestration.md](../14-orchestration.md) §8 depends on. Both are cheap now and expensive to retrofit.

## The ledger

One append-only `.jsonl` per initiative: `.ai/<initiative>/ledger.jsonl`. One record per delegation, schema in [`schema.json`](./schema.json).

**Record from the first delegation, before anything needs it.** Outcome history cannot be reconstructed retroactively. Every other part of the orchestration design can be added later; this one cannot.

It serves three purposes at once, which is why it is worth the discipline:

| Purpose | Fields that carry it |
|---|---|
| Outcome-weighted agent selection | `task_class`, `surface`, `agent`, `outcome`, `attribution_confidence` |
| Replay-eval corpus (answers Q1) | `task_class`, `eval_candidate`, `outcome` |
| Cost attribution and gate health | `tokens`, `model`, `human`, `cycle` |

### Three fields that exist because something is unsolved

**`attribution_confidence`.** Blame attribution across a chain is not solved. A rejection at G3 might be a scope defect Specify produced and Design carried forward; the routing table picks the producing stage, but that is a judgment. Mis-attributed rejections poison the selection signal, which is the one thing the ledger exists to feed. So: mark `shared` or `unknown` honestly, and **exclude anything that is not `sole` from the weighting** until attribution has a real answer. Recording it as `sole` because the field defaults that way is the failure mode.

**`exploration`.** Without it, a deliberate second-best pick that goes badly reads as a regression, and the next person removes the exploration budget — which is exactly what stops the index correcting an early mistake.

**`eval_candidate`.** Set it when an earlier stage should have caught the defect. A spec gap surfaced at Verify that Audit missed is worth more as an eval case than as a bug report, and these are the only cases that arrive pre-labelled.

### Never read the ledger within a run

Write to it during a run. Read it **between** runs, to weight agent selection.

**Never read it mid-run to influence that run's behaviour.** That creates a feedback loop where a run's own log shapes its decisions — which is unauditable, makes replay non-deterministic, and means two identical inputs can produce different outputs for reasons nobody can reconstruct.

The temptation becomes obvious once outcome weighting exists ("this agent has been failing, let me try another"), which is exactly why it is written down. Listeners only watch.

### Two health signals to watch

- **Rising share of `resolution_step: 5`** — new agents being proposed instead of existing ones reused. The sprawl warning.
- **Rising per-`human` approval rate** — the measured habituation effect (+14.5pp, inline comments −22% across 11,429 agent-authored reviews). Rising is the warning sign, not a success signal.

## The `surfaces:` convention

Agent capability was declared in prose, so resolution was an LLM match rather than a lookup. `surfaces:` makes the common case deterministic and auditable.

```yaml
---
name: ads-backend
description: <prose, still needed for activation>
surfaces:
  - ads.backend
  - ads.audience-sync
  - ads.attribution
  - ads.compliance-enforcement
initiative: ads-builder
---
```

**Dotted, so prefixes match.** An agent declaring `ads` covers `ads.audience-sync`; one declaring `ads.audience-sync` does not cover `ads.campaign-builder`. That gives the resolver a cheap specificity ordering: prefer the longest matching prefix, which is the most specific agent that covers the surface.

Rules:

- **Surfaces are product areas, never role titles or seniority.** `ads.backend` is a surface; `senior-backend` is not. This is the same rule that governs function-team decomposition, applied to the registry.
- **One initiative per agent** (`initiative:`), because the archetype's surface list is what caps agent count per initiative.
- **Cross-cutting harness agents use the `harness.` prefix** — `harness.orchestration`, `harness.contracts`, `harness.integration`. They belong to no product initiative.
- **A surface that appears in no agent's list is a coverage gap**, and enumerating those is the point of having the field at all.
- **A surface claimed by three agents is a smell.** Either the surface is too coarse or two of the agents are redundant, and the outcome weights will eventually say which.

`skills:` is already a supported sub-agent frontmatter field, so the agent-to-skill edge needs no new convention — declare it where an agent composes skills.

## Current state

Applied to the six agents that exist: `ads-architect`, `ads-backend`, `ads-frontend`, `product-orchestrator`, `slice-contract-keeper`, `slice-integrator`. The remaining ~18 agents in this repo predate the convention and are unannotated, so the resolver falls back to prose matching for them — which is exactly the situation `surfaces:` exists to remove. Annotating them is mechanical and worth doing before the index is built.
