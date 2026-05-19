---
name: jhd-foundation
description: >
  Shared definitions for the Apollo GTM Skill Library. Contains the six-layer architecture
  diagram, epistemic tag sets (L1 and L2A), tag set mapping between layers,
  epistemic-to-constraint translation table, bounded action space (10 classes),
  constraint taxonomy (12 types), severity metadata, confidence bands, and source
  quality scale. Load this file once alongside any skill in the library.
metadata:
  author: David Johnson-Hall
  version: '1.0'
  architecture: Apollo GTM Skill Library
---

# Apollo GTM Skill Library -- Foundation

Shared definitions for all skills in the Apollo GTM Skill Library. Load this file once. Individual skills reference these definitions rather than redeclaring them.

## Architecture

```
raw input
  --> reality-filter (L1): what is true, how well-grounded, from what source
  --> state-extractor (L2A): structured state with epistemic tags preserved
  --> [state-to-router-adapter]: mechanical transform, SE output → BAR input schema
  --> constraint-first-reasoner (L2B): ranked constraint map, information gaps, tradeoffs
  --> [truth-speed-structure]: optional shaping pass — output mode selection
  --> bounded-action-router (L3): one action class selected from bounded space
  --> message-os (L4) or GEN-SE (L4-sales): message composed within constraints
  --> humanizer-compressor (L4+): optional voice polish and compression
  --> output
```

Each layer has one job. No layer does the job of another. Items in `[brackets]` are optional adapters/shaping passes, not full layers.

| Layer | Skill | Job |
|---|---|---|
| 1 | reality-filter | Evaluate truth status, confidence, source quality. Tag claims. |
| 2A | state-extractor | Convert unstructured input into structured, epistemically tagged state. |
| (adapter) | state-to-router-adapter | Deterministic transform: SE output schema → BAR input schema. Not a reasoning step. |
| 2B | constraint-first-reasoner | Map what cannot, should not, or may only conditionally be done. |
| (shaping) | truth-speed-structure | Optional. Select output mode (DIRECT, CAVEAT-FIRST, STRUCTURED-ANALYSIS, ESCALATE-TO-HUMAN). Binding when present. |
| 3 | bounded-action-router | Eliminate invalid action classes, select one from what remains. |
| 4 | message-os | Compose message within constraint and epistemic boundaries. |
| 4 (sales) | GEN-SE | Compose sales message using GRRIPS methodology. Sibling to message-os. |
| 4+ | humanizer-compressor | Post-process for voice, compression, naturalness. Cannot alter protected meaning. |

## Core Principle

Eliminate before selecting. Every layer narrows the space before the next layer acts.

- L1 eliminates unsafe claims
- L2B eliminates infeasible actions
- L3 eliminates invalid action classes
- L4 eliminates unsafe expressions
- L4+ eliminates AI-pattern residue

Conservative about commitment, not conservative about motion. Block final commitment, definitive factual framing, and irreversible execution. Allow clarification, verification, acknowledgment, and caveated options.

## Epistemic Tag Sets

### reality-filter truth_status (10 values)

The authoritative epistemic tag set. Produced by reality-filter (L1). Downstream skills preserve these tags.

| Tag | Definition |
|---|---|
| verified | Independently confirmed by authoritative or primary source |
| probable | Strong evidence, high confidence, not independently verified |
| inferred | Reasonable conclusion from multiple cues, not directly stated |
| asserted | Stated by a party but not independently confirmed |
| assumed | Structural assumption used to make sense of input, not confirmed |
| disputed | Claim exists but input shows disagreement or contradiction |
| contradicted | Directly contradicted by stronger evidence |
| fabricated | No basis in input; model-generated or hallucinated |
| unknown | Cannot be determined from available information |
| not_verifiable | Claim may be true but cannot be checked against available sources |

### state-extractor epistemic_status (7 values)

The parsing-level tag set. Used when reality-filter has not run upstream.

| Tag | Definition |
|---|---|
| explicit | Directly stated in the source |
| inferred | Reasonable conclusion based on multiple cues, not directly stated |
| implied | Strongly suggested by wording or context, still not direct |
| disputed | A claim exists, but the input shows disagreement or uncertainty |
| assumed | A structural assumption used to make sense of the input, not confirmed |
| missing | A field is expected but absent from the input |
| unknown | Cannot be determined from available text |

### Tag Set Mapping (L1 to L2A)

When reality-filter has run, its tags take precedence. When it has not, state-extractor's tags are authoritative.

| reality-filter tag | state-extractor equivalent | Notes |
|---|---|---|
| verified | explicit | Direct mapping |
| probable | explicit (high confidence) | Confidence distinguishes from verified |
| inferred | inferred | Direct mapping |
| asserted | explicit (lower confidence) | Asserted = stated but unverified |
| assumed | assumed | Direct mapping |
| disputed | disputed | Direct mapping |
| contradicted | (no equivalent) | Carry forward from reality-filter |
| fabricated | (no equivalent) | Carry forward from reality-filter |
| unknown | unknown | Direct mapping |
| not_verifiable | (no equivalent) | Carry forward from reality-filter |

## Epistemic-to-Constraint Translation

How epistemic tags become behavioral constraints (used by constraint-first-reasoner, L2B):

| Truth Status | Constraint Effect |
|---|---|
| verified | Usually no epistemic constraint unless action is independently high-risk |
| probable | Light restriction; may require caveated framing for external actions |
| inferred | Light to moderate restriction depending on centrality to action |
| asserted | Moderate restriction if action would operationalize the claim as true |
| assumed | Stronger restriction; assumption is not evidence. Often blocks commitment-heavy actions |
| disputed | Major restriction. Prevents commit/publish/accuse/escalate until reconciliation |
| contradicted | Hard block against treating the claim as decision substrate |
| fabricated | Hard block against treating the claim as decision substrate |
| unknown | Missing-information constraint. Routes toward clarification or verification |
| not_verifiable | Light restriction; claim cannot anchor factual assertions |

General rule: the weaker the grounding and the higher the action consequence, the stronger the epistemic constraint.

## Bounded Action Space

The 10 valid action classes. Used by bounded-action-router (L3), message-os (L4), and humanizer-compressor (L4+). No skill invents a new class.

| Action Class | Definition |
|---|---|
| NO_ACTION | No outward move. Thread is informational, issue resolved, or all valid actions blocked. Intentional terminal route. |
| ACKNOWLEDGE | Confirm receipt or awareness without substantive progress. Use when sender needs confirmation and no meaningful answer is yet possible. |
| REQUEST_CLARIFICATION | Ask for missing information necessary to proceed safely. Use when key fields are unknown or ambiguity blocks confident selection. |
| RESPOND | Provide a substantive reply to the explicit ask using available state. Use when an answer is requested, information suffices, and constraints allow response. |
| EXECUTE | Carry out an operational action rather than merely respond. Use when the system has authority, the action is clear, and dependencies are satisfied. |
| PROPOSE_NEXT_STEP | Suggest a concrete next move when progression is possible but not yet authorized. Use when forward motion is useful but explicit execution authority is absent. |
| DEFER | Hold action until an external condition or dependency is met. Use when waiting is structurally correct. Different from NO_ACTION because it is explicitly pending. |
| ESCALATE | Route to a higher-trust actor or specialized review path. Use when risk is high, authority is missing, or conflict cannot be safely resolved at this layer. |
| LOG | Produce a record rather than an interactive response. Use when documentation is the correct move. |
| CLOSE | Intentionally terminate the workflow segment. Distinct from NO_ACTION because it implies a state transition. |

## Constraint Taxonomy

The 12 valid constraint types. Used by constraint-first-reasoner (L2B). The skill never invents a new type.

| Type | Definition | Router Effect |
|---|---|---|
| hard_block | Makes actions invalid or prohibited. No balancing test. | Eliminate affected actions immediately |
| soft_limit | Real pressure that should shape decisions but does not fully forbid. | Down-rank or require tradeoff surfacing |
| resource_cap | Limit on available time, budget, bandwidth, tools, capacity. | Filter out actions exceeding capacity |
| timing_window | Temporal constraint on when action can occur. | Gate, delay, accelerate, or eliminate |
| dependency | Prerequisite that must exist before another action is valid. | Block until dependency satisfied |
| competing_priority | Another valid objective that cannot be fully satisfied simultaneously. | Surface tradeoff explicitly |
| epistemic_restriction | Limit from uncertainty, dispute, poor sourcing, or insufficient grounding. | Prevent high-commitment actions |
| authority_boundary | Constraint based on role, access, ownership, or allowed scope. | Eliminate unauthorized actions |
| policy_boundary | Normative or system-level rule constraining permissible action. | Immediate elimination or forced redirection |
| reversibility_constraint | Constraint based on consequence severity if action is wrong. | Raise certainty threshold |
| consistency_constraint | Requirement not to contradict prior accepted state or commitments. | Force reconciliation or escalation |
| environmental_constraint | Real-world situational limit not reducible to policy. | Constrain feasible execution paths |

## BAR Constraint Type Enum

The types that appear in the Adapter → BAR constraint pipeline. These are distinct from L2B's 12-type classification above. BAR receives constraints with these type labels; L2B then classifies them into its own taxonomy while preserving the original type in `source_constraint_type`.

**8 SE passthrough types** (1:1 from State-Extractor):
`time`, `policy`, `legal`, `budget`, `technical`, `relationship`, `logistical`, `unknown`

**5 synthetic types** (injected by Adapter from non-constraint SE fields):
`authority`, `dependency`, `confidence`, `channel`, `data_completeness`

`scope`, `reversibility` are NOT valid BAR constraint types. They were removed in v3.0.3 when the SE→BAR mapping became 1:1.

## Constraint Severity

```yaml
severity: blocking | strong | moderate | light
certainty: verified | likely | uncertain
immediacy: active_now | upcoming | latent
scope: action-specific | class-wide | global
reversibility_impact: irreversible | costly | reversible
dependency_centrality: bottleneck | important | peripheral
```

Dominance hierarchy:
1. Hard blocks outrank soft optimization
2. Uncertainty constraints outrank generative usefulness when action is irreversible
3. Bottleneck dependencies outrank local preferences
4. Timing constraints outrank ideal sequencing if window collapse is imminent
5. Policy and authority constraints dominate all ordinary utility reasoning

## Confidence Bands

| Band | Range | Meaning |
|---|---|---|
| very_high | 0.90-1.00 | Near-certain given available evidence |
| high | 0.75-0.89 | Strong evidence, minor residual uncertainty |
| medium | 0.50-0.74 | Mixed evidence or moderate uncertainty |
| low | 0.25-0.49 | Weak evidence, significant uncertainty |
| very_low | 0.00-0.24 | Minimal evidence, high uncertainty |

## Source Quality Scale

7-level scale, highest to lowest. This is the canonical scale used by pipeline-runtime.md and all downstream consumers.

| Quality | Definition |
|---|---|
| authoritative_record | Official record, legal document, verified database, institutional source |
| official_document | Formal document from a known organization (contracts, filings, published policies) |
| expert_statement | First-party account from a domain expert or direct participant |
| reliable_reporting | Reported by a generally trustworthy intermediary with editorial standards |
| self_report | First-party account that may have bias or incomplete view |
| indirect_inference | Derived from circumstantial evidence, not directly sourced |
| model_generated | Produced by an AI model, not grounded in input |

## GEN-SE Action Space Mapping

GEN-SE (the sales email engine) uses a domain-specific 24-action vocabulary for email thread decisioning. When the pipeline routes to GEN-SE via bounded-action-router, the abstract 10-class action space maps to GEN-SE's concrete sales actions. This mapping is reference material — the router and GEN-SE use it to ensure handoff integrity.

### 10-Class → GEN-SE Action Map

| FOUNDATION Class | GEN-SE Actions | Notes |
|---|---|---|
| NO_ACTION | — | GEN-SE does not select no-action. If BAR selects NO_ACTION, GEN-SE is not invoked. |
| ACKNOWLEDGE | 11 (confirm buyer commitment), 14 (new stakeholder acknowledgment) | |
| REQUEST_CLARIFICATION | 2 (request config), 4 (ask clarification), 5 (request external input), 7 (gather pricing inputs) | |
| RESPOND | 3 (answer question), 6 (deliver asset), 8 (address process blocker), 20 (address procurement/legal), 21 (objection reframe), 22 (competitive differentiation) | Core response actions — differ by what is being responded to |
| EXECUTE | 18 (deliver proposal) | Only proposal delivery maps cleanly to execute |
| PROPOSE_NEXT_STEP | 12 (discovery question), 13 (stakeholder expansion), 15 (timeline probe), 16 (advance conversation), 17 (propose meeting), 19 (trial close) | Sales progression actions |
| DEFER | — | GEN-SE does not defer. If BAR selects DEFER, GEN-SE is not invoked. |
| ESCALATE | 1 (human escalation) | GEN-SE's internal escalation — see control flow note below |
| LOG | — | GEN-SE does not log. If BAR selects LOG, GEN-SE is not invoked. |
| CLOSE | — | GEN-SE does not close threads. If BAR selects CLOSE, GEN-SE is not invoked. |

### Straddle Actions

Actions 9 (request commitment deadline), 10 (trust repair), 23 (gentle nudge), and 24 (final nudge) straddle multiple abstract classes:

- **9, 10** — Commitment management. Crosses RESPOND / PROPOSE_NEXT_STEP.
- **23, 24** — Re-engagement. Crosses PROPOSE_NEXT_STEP / RESPOND.

GEN-SE's policy engine handles these via precondition triggers, not via the abstract class mapping. They are state-triggered actions that activate when their preconditions are met, regardless of which abstract class BAR selected.

### Routing Rule

When BAR selects an action class that GEN-SE does not handle (NO_ACTION, DEFER, LOG, CLOSE), BAR's `composition_target` falls back to message-os. This is enforced in BAR's output contract:

```
if composition_target = gense AND selected_action_class in [ESCALATE, DEFER, NO_ACTION, LOG, CLOSE]:
    composition_target = message-os
```

ESCALATE is included in the fallback set because when BAR determines escalation is needed, message-os handles the routing — not GEN-SE. GEN-SE's Action 1 is a separate internal mechanism (see below).

### GEN-SE BLOCK Control Flow

When GEN-SE internally blocks — via gate check failure (Step 1/3), drift repair exhaustion (Step 7), or policy hard block (Step 4) — it selects Action 1 and emits a Block Output. This is a **terminal state**: the block output is presented directly to the human operator with a structured recommendation (block reason, what the reviewer needs, ThreadState snapshot, next-step recommendation).

There is no re-entry into the pipeline's bounded-action-router. The block IS the escalation. Control does not return to BAR or message-os — it terminates at the human operator.
