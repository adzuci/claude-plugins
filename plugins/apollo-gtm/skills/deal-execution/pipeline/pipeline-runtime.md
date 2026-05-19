# Pipeline Runtime — Consolidated Execution Reference

Compact runtime for L1 through L4+. Load this file instead of individual pipeline skills. For architecture review, debugging, or extending behavior, load the full skill files.

## Architecture

```
Input → [L1 Reality-Filter] → [L2A State-Extractor] → [Adapter] → [L2B Constraint-First-Reasoner]
      → [L3 Bounded-Action-Router] → [L4 Message-OS] → [L4+ Humanizer-Compressor]
```

Optional shaping pass: truth-speed-structure runs between L2B and L3.
Each layer narrows the action space. L1 eliminates unsafe claims, L2B eliminates infeasible actions, L3 eliminates invalid action classes, L4 eliminates unsafe expressions.

## L1: Reality-Filter

**Purpose:** Epistemic gatekeeper. Decomposes input into atomic claims, assigns truth status before any downstream reasoning.

**Process (13 steps):** Normalize input → extract content → decompose into atomic claims → classify claim type (factual, normative, predictive, procedural) → identify source provenance → assess source quality → check for supporting evidence → check for contradictions → detect model injection/unsupported specificity → assign truth_status → assess staleness → assign confidence_band → apply downstream handling flags.

**Truth Status Taxonomy (10 values):**

| Status | Definition | Downstream handling |
|---|---|---|
| verified | Confirmed by authoritative source | Pass through |
| probable | Strong evidence, not fully confirmed | Pass through |
| inferred | Derived from evidence by reasoning | Pass with hedge |
| asserted | Claimed by source, no independent verification | Hedge |
| assumed | Taken as given, no evidence | Strip or hedge |
| disputed | Contradicted by another source | Surface conflict |
| contradicted | Directly negated by authoritative source | Block |
| fabricated | No source, model-generated specificity | Block |
| unknown | Cannot determine status | Block or hedge |
| not_verifiable | Claim is unfalsifiable by nature | Label and pass |

**Confidence Bands:** very_high (0.90-1.00), high (0.75-0.89), medium (0.50-0.74), low (0.25-0.49), very_low (0.00-0.24)

**Source Quality Scale:** authoritative_record > official_document > expert_statement > reliable_reporting > self_report > indirect_inference > model_generated

**Threshold Matrix** (minimum truth_status + confidence for pass):

| Mode | Pass | Hedge | Block |
|---|---|---|---|
| strict | verified/probable + high | inferred + medium | everything else |
| balanced | verified/probable/inferred + medium | asserted + low | assumed, fabricated, contradicted |
| permissive | anything with medium+ | anything with low+ | fabricated, contradicted |

**Output:** Claim register: `{ claims[]: { claim_id, text, truth_status, confidence_band, source, source_quality, handling_directive } }`

## L2A: State-Extractor

**Purpose:** Parse ambiguity without resolving it. What is happening, who is involved, what is known/inferred/missing.

**Process (10 steps):** Classify input type → segment content boundaries → identify actors and roles → extract explicit facts → extract timeline → extract requests/decisions/open loops → extract constraints and dependencies → detect signals and risk factors → epistemic validation pass → assemble state object.

**Output Schema (state_object):**
```
input_type, domain, source_summary
actors: [{ id, name, role, authority_level }]
timeline: [{ event, timestamp, source }]
known_facts: [{ fact, source, epistemic_status }]
inferred_points: [{ inference, basis, confidence }]
unknowns: [{ question, impact, priority }]
requests: [{ from, to, content, deadline, status }]
decisions: [{ decision, maker, date, status }]
open_loops: [{ item, owner, status, deadline }]
constraints: [{ type, description, source }]
dependencies: [{ item, depends_on, status }]
signals: { urgency, sentiment, decision_stage, ambiguity_level, conflict_level }
risk_flags: [{ type, description, confidence }]
escalation_flags: [{ trigger, reason }]
candidate_action_classes: [classes]
parser_notes: [notes]
```

**Minimal Schema:** `{ input_type, domain, actors[], known_facts[], unknowns[], requests[], signals, risk_flags[], candidate_action_classes[] }`

## Adapter: State-to-Router

**Purpose:** Mechanical transform bridging SE output to BAR input contract. No interpretation, no routing.

**Key Transforms:**
- **Object Metadata:** state_id (generate), source_type (map input_type), freshness (compute from age), parser_confidence (weighted aggregate of SE confidences)
- **Intent/Interaction:** primary_intent (map primary_question_or_problem), intent_explicitness (derive from requests epistemic tags), response_expected (derive from open requests), decision_ready (derive from unknowns/deps/ambiguity), thread_stage (map from signals.decision_stage)
- **Actors/Authority:** sender (search actors for sender/author/requester role), recipient (search for recipient/responder/assignee), authority_level (inject from system context)
- **Open Items:** unresolved_questions (map from unknowns), unresolved_dependencies (merge dependencies + open_loops with blocker)
- **Constraints:** Reshape SE constraints to BAR format. Inject synthetic constraints from: dependencies, low parser_confidence, high unknown count
- **Risk:** overall_risk = max confidence across risk_flags. compliance_risk = filter legal/safety/compliance. relationship_risk = filter relational/reputational. contradiction_present = check for factual_uncertainty or disputed decisions
- **Epistemic Tags:** Passthrough with enum extension (add disputed, assumed, missing)
- **Signals:** Direct map + renames (ambiguity_level→ambiguity, conflict_level→tension). Derived signals:

| Signal | Derivation | Default |
|---|---|---|
| task_density | count(requests + open_loops + active decisions): ≤2→low, 3-5→medium, ≥6→high | low |
| decision_readiness | from decision_ready: ready→ready, partial→partial, not_ready→not_ready | not_ready |
| expectation_of_response | if response_expected FALSE→none. If TRUE: 1 open request→low, 2-3→medium, ≥4→high. Urgency high upgrades one level. | none |
| interaction_frame | emotional_tone tense/conflicted/negative→relational. All requests explicit + neutral tone→transactional. Otherwise→ambiguous. | ambiguous |

**Constraint Type Mapping (SE → BAR):**

| SE Constraint | BAR Type | Notes |
|---|---|---|
| time | time | Direct map |
| policy | policy | Direct map |
| legal | legal | Preserved (was: collapsed to policy) |
| budget | budget | Preserved (was: collapsed to scope) |
| technical | technical | Preserved (was: collapsed to dependency) |
| relationship | relationship | Preserved (was: collapsed to reversibility) |
| logistical | logistical | Preserved (was: collapsed to scope) |
| unknown | unknown | Preserved (was: collapsed to scope) |

**_se_passthrough block:** Carries SE fields BAR ignores but L4 needs (full actors, timeline, known_facts, inferred_points, decisions, open_loops, escalation_flags, parser_notes, signals_raw).

## L2B: Constraint-First-Reasoner

**Purpose:** Map constraint landscape before action selection. Eliminate before selecting.

**Process (14 steps):** Validate input → extract explicit constraints → derive implicit constraints → decompose compound constraints → hard-block detection → evaluate epistemic restrictions → resource/timing constraints → dependencies/sequencing → competing priorities/tradeoffs → classify and weight → analyze interactions → deduplicate → identify information gaps → rank, partition, emit.

**12 Constraint Types:** hard_block, soft_limit, resource_cap, timing_window, dependency, competing_priority, epistemic_restriction, authority_boundary, policy_boundary, reversibility_constraint, consistency_constraint, environmental_constraint

**Epistemic-to-Constraint Translation:**

| Truth Status | Constraint Effect |
|---|---|
| verified, probable | No constraint |
| inferred | epistemic_restriction (medium) |
| asserted | epistemic_restriction (medium-high) |
| assumed | epistemic_restriction (high) |
| disputed | hard_block or epistemic_restriction (high) |
| contradicted, fabricated | hard_block |
| unknown | epistemic_restriction (high) |

**Degradation Mode:** When reality-filter hasn't run and epistemic_map is absent, substitute SE's per-field epistemic_status tags using the tag set mapping below. Emit `degraded_epistemic_input` meta-constraint. Set all derived constraints to `certainty: uncertain`.

**Tag Set Mapping (L1 → L2A):** When reality-filter has run, its tags take precedence. When it has not, state-extractor's tags are authoritative.

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

**Constraint Severity Metadata:**

```yaml
severity: blocking | strong | moderate | light
certainty: verified | likely | uncertain
immediacy: active_now | upcoming | latent
scope: action-specific | class-wide | global
reversibility_impact: irreversible | costly | reversible
dependency_centrality: bottleneck | important | peripheral
```

**Dominance Hierarchy:**
1. Hard blocks outrank soft optimization
2. Uncertainty constraints outrank generative usefulness when action is irreversible
3. Bottleneck dependencies outrank local preferences
4. Timing constraints outrank ideal sequencing if window collapse is imminent
5. Policy and authority constraints dominate all ordinary utility reasoning

**Output:** `{ constraints[]: { id, rank, tier, type, severity, certainty, affects_action_classes[], handling }, interactions[], tradeoff_pairs[], information_gaps[], downstream_guidance }`

## [Optional] Truth-Speed-Structure Shaping Pass

**4 Output Modes** (exactly one, no blending):
- **DIRECT:** Strong grounding, clear answer, constraints allow. Answer first, short.
- **CAVEAT-FIRST:** Mixed grounding or asserted/assumed claims. Lead with uncertainty.
- **STRUCTURED-ANALYSIS:** Complex, multi-actor, constraint-dense. Claims separated from inferences from recommendations.
- **ESCALATE-TO-HUMAN:** Cannot safely proceed. Structured handoff, not message.

**Selection:** Strong + high speed + low constraints → DIRECT. Mixed + any → CAVEAT-FIRST. Any + low speed + high constraints → STRUCTURED-ANALYSIS. Weak/unknown + blocking constraints → ESCALATE-TO-HUMAN.

## L3: Bounded-Action-Router

**Purpose:** Eliminate impossible/prohibited actions, select one action class from 10 valid types.

**Process (4 steps):** Validate input completeness → apply hard blocks (eliminate classes blocked by constraints) → apply constraint checks (narrow remaining) → signal-based selection from survivors.

**10 Action Classes:**

| Class | Definition |
|---|---|
| NO_ACTION | Nothing to do |
| ACKNOWLEDGE | Receipt/awareness only |
| REQUEST_CLARIFICATION | Missing info blocks action |
| RESPOND | Answer a question or request |
| EXECUTE | Carry out a clear, authorized task |
| PROPOSE_NEXT_STEP | Suggest forward movement |
| DEFER | Delay with reason |
| ESCALATE | Route to human/authority |
| LOG | Document for record |
| CLOSE | Finalize/conclude |

**Selection Hierarchy:** ESCALATE if risk flags → REQUEST_CLARIFICATION if missing info → EXECUTE if safe + complete → RESPOND if answerable → PROPOSE_NEXT_STEP if clear path → ACKNOWLEDGE if low urgency → DEFER if timing constraint → LOG if informational → NO_ACTION if nothing needed → CLOSE if concluded.

**Output:** `{ selected_action_class, routing_confidence, rationale, eliminated_actions[], active_constraints[], active_risks[], downstream_contract, uncertainty_notes }`

## L4: Message-OS

**Purpose:** Convert routed action class into concrete, channel-appropriate, epistemically safe message.

**Process (9 steps):** Lock action envelope → build allowable claim pool → load commitment boundaries → select message skeleton → populate content slots → apply tone/register calibration → apply length calibration → run validation gates → finalize or escalate.

**Claim Pool Categories:**
- **Direct-use:** verified — assert without caveat
- **Caveated:** inferred — state with interpretive framing ("Based on X..."). Assumed — state only if necessary, label as assumption. Asserted — hedge ("According to..."), never endorse as fact.
- **Blocked:** disputed (attribute, don't endorse), unknown (omit or clarify), fabricated (block entirely)

**7 Validation Gates:**
1. **Claims gate:** Every direct assertion traces to source tagged verified/probable/inferred. Strip fabricated/contradicted. Assumed/asserted allowed only with caveat framing.
2. **Action drift gate:** Message matches selected action class, no scope creep.
3. **Single-ask gate:** ONE ask per message. No secondary questions.
4. **Constraint compliance gate:** All active constraints respected in wording.
5. **AI-pattern gate:** No banned vocabulary or structural patterns.
6. **Channel fit gate:** Format matches channel.
7. **Ambiguity gate:** No unintended ambiguity in commitments or asks.

**AI-Pattern Avoidance — Banned Vocabulary:** pivotal, crucial, vital, delve, underscore, bolster, garner, foster, showcase, additionally, furthermore, "it's important to note," nestled, rich history, fascinating, remarkable, innovative

**AI-Pattern Avoidance — Banned Structures:** rule of three, negative parallelism, elegant variation, copula avoidance, present-participle analysis, didactic disclaimers, em dash overuse

**Length Targets:** Slack 1-5 sentences. Email short 80-180 words. Escalation 150-300 words. Log 1-6 bullets. SMS 1-3 sentences.

**Action Class Skeletons:**
- NO_ACTION: no output
- ACKNOWLEDGE: receipt + timeline if relevant
- REQUEST_CLARIFICATION: what's missing + why it matters + single question
- RESPOND: answer + supporting evidence + single CTA if needed
- EXECUTE: confirmation of action taken + result + next step
- PROPOSE_NEXT_STEP: recommendation + rationale + single ask
- DEFER: reason for delay + expected timeline + what happens next
- ESCALATE: situation summary + why escalation needed + specific request
- LOG: structured record (who, what, when, status, next)
- CLOSE: summary + any final items + closure signal

## L4+: Humanizer-Compressor

**Purpose:** Make structurally correct drafts sound human and sender-native without altering protected meaning.

**Locked Elements (NEVER changed):** action_class, approved_claims, single_ask, commitment_boundaries, required_caveats. For GEN-SE: persuasion_structure.

**Process (10 steps):** Parse input + build protected span map → profile draft → estimate target voice → identify mismatches → generate candidate edits → remediate subtle AI patterns → verify locked elements preserved → verify meaning preservation → check channel fit → emit.

**AI Pattern Remediation:**

| Pattern | Fix |
|---|---|
| Repeated template across messages | Vary sentence openings and structure |
| Uniform paragraph size | Mix short and long |
| Mechanical transitions | Remove or replace with natural connectives |
| Zero fragments | Allow occasional fragment |
| Overuse of contrast | Reduce, vary |
| Excessive restatement | Compress to single expression |
| Uniform confidence | Match confidence to claim strength |
| Sterile closures | Match sender's natural sign-off |

**Compression Targets:** Email: low-medium. Slack: medium. SMS: medium-high. Formal/legal: none-low.

**Priority Order:** Locked elements > preserve meaning > channel fit > sender voice > compression.

**Output:** `{ final_message, compliance_report: { action_class_preserved, claims_preserved, single_ask_preserved, commitments_preserved, caveats_preserved }, transformation_log, metrics: { word_count_in, word_count_out, compression_ratio, voice_match_confidence } }`

## Cross-Layer Contracts

- L1 → L2A: Claim register (truth_status, confidence per claim). L2A uses as epistemic overlay.
- L2A → Adapter → L3: State object transformed to BAR input contract. Adapter is mechanical.
- L2B → L3: Constraint map. L3 uses to eliminate invalid action classes.
- L3 → L4: Routing decision (selected_action_class + downstream_contract). L4 composes within envelope.
- L4 → L4+: Draft message + locked elements. L4+ polishes without altering protected content.

## Failure and Degradation Paths

When any pipeline layer cannot produce valid output, the failure must be surfaced explicitly. Silent failures, empty results, and skipped layers are prohibited. Every failure emits a structured error state that orchestrators consume.

**Failure state schema:**
```
{
  pipeline_status: "failure",
  failure_layer: "<layer identifier>",
  failure_code: "<code>",
  last_valid_state: <output from previous successful layer>,
  failure_detail: "<human-readable explanation>",
  recommended_action_class: ESCALATE | REQUEST_CLARIFICATION,
  recommended_tier: "ACT"
}
```

**Per-layer failure conditions and behavior:**

### L1: Reality-Filter Failure

**Condition:** All claims tagged fabricated/contradicted, OR zero grounded claims survive filtering, OR input is unparseable.

**Behavior:**
- Do not proceed to L2A.
- Emit failure state: `failure_layer: L1_reality_filter`, `failure_code: RF_NO_GROUNDED_CLAIMS`.
- `recommended_action_class: ESCALATE`.
- Orchestrator routes to ACT tier with note: "Input claims could not be grounded. Review source material manually."

### L2A: State-Extractor Failure

**Condition:** Cannot extract minimum viable state (actors + at least one of: requests, decisions, open_loops, known_facts) with parser_confidence above `very_low`, OR critical schema violations.

**Behavior:**
- Do not proceed to Adapter.
- Emit failure state: `failure_layer: L2A_state_extractor`, `failure_code: SE_INSUFFICIENT_STATE`.
- Include partial state in `last_valid_state` (whatever was extractable).
- `recommended_action_class: REQUEST_CLARIFICATION` if input was ambiguous, `ESCALATE` if input was unparseable.
- Orchestrator routes to ACT tier with note: "Pipeline could not parse this input. [Missing fields]. Review manually."

### Adapter Failure

**Condition:** Required fields for BAR input contract missing and cannot be derived (no actors with sender role, no primary_intent derivable, no signals).

**Behavior:**
- Do not proceed to L2B.
- Emit failure state: `failure_layer: ADAPTER`, `failure_code: ADAPT_CONTRACT_VIOLATION`.
- Include SE state_object in `last_valid_state`.
- `recommended_action_class: ESCALATE`.
- Orchestrator routes to ACT tier with note: "State-to-router transform failed. [Missing contract fields]. Review SE output manually."

### L2B: Constraint-First-Reasoner Failure

**Condition:** Cannot produce constraint map due to insufficient structured state or epistemic coverage. Distinct from "constraints reduce action space to zero" (which is a valid L2B output consumed by L3).

**Behavior:**
- Do not proceed to L3.
- Emit failure state: `failure_layer: L2B_constraint_reasoner`, `failure_code: CFR_NO_CONSTRAINT_MAP`.
- `recommended_action_class: ESCALATE`.
- Orchestrator routes to ACT tier with note: "Insufficient context for constraint analysis. [Missing fields]. Review manually."

### L3: Bounded-Action-Router Failure (No Valid Actions)

**Condition:** All 10 action classes eliminated by constraints. Action space is empty.

**Behavior:**
- Do not proceed to L4.
- Emit failure state: `failure_layer: L3_action_router`, `failure_code: BAR_NO_VALID_ACTIONS`.
- Include constraint map and elimination log in `last_valid_state`.
- `recommended_action_class: ESCALATE`.
- Orchestrator routes to ACT tier with note: "No valid action class survived constraint elimination. [Top 3 elimination reasons]. AE must choose override or adjust constraints."

### L4: Message-OS Failure

**Condition:** Cannot compose a message that satisfies all active constraints (claim pool depleted, all content blocked by epistemic gates, constraint conflict makes composition impossible).

**Behavior:**
- Do not proceed to L4+.
- Emit failure state: `failure_layer: L4_message_os`, `failure_code: MOS_COMPOSITION_BLOCKED`.
- Include routing decision + partial draft skeleton (subject + bullet outline) in `last_valid_state`.
- `recommended_action_class: ESCALATE`.
- Orchestrator routes to ACT tier with note: "Draft composition failed. [Reason]. Thread state and partial skeleton preserved for manual drafting."

### L4+: Humanizer-Compressor Failure

**Condition:** Cannot compress without violating locked elements, or repeated retries fail voice-match or length targets.

**Behavior:**
- Return the uncompressed L4 draft as final output with `compression_failed: true` flag.
- Do NOT emit pipeline failure. The L4 draft is structurally valid and safe to use.
- Attach note: "Compression failed. Draft is uncompressed but constraint-compliant. AE may manually trim."
- Orchestrator treats as normal output (WATCH or FYI tier, not ACT) with the compression flag noted.

### General Rules

1. When any layer emits `pipeline_status: failure`, the orchestrator must treat this as a hard escalation to ACT tier. Never silently drop, skip, or default past a failure.
2. The `last_valid_state` field preserves the output from the last successful layer so the AE has maximum context for manual handling.
3. L4+ failure is the only non-escalating failure because the L4 draft is already safe. All other layer failures block downstream processing.
4. Multiple failures across threads in a single triage run are each reported independently in the ACT tier. They do not aggregate or cancel each other.

## Hard Rules (invariant)

1. No message without full pipeline (L1 through L4+).
2. Single-ask discipline. One ask per message.
3. Claims must be source-traceable. Strip anything tagged assumed/fabricated/contradicted/unknown.
4. No emails sent. Gmail drafts only.
5. No emails marked as read.
