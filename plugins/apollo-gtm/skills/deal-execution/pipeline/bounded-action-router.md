---
name: bounded-action-router
description: >
  Layer 3 decision-control skill that receives structured state from state-extractor,
  applies hard blocks, constraints, risk flags, and confidence thresholds to eliminate
  invalid actions, then selects one action class from a finite bounded action space.
  Use when a system must choose what type of move is appropriate next, when action
  selection should be explicit and reviewable, when the cost of a wrong move is
  non-trivial, or when downstream execution should be constrained to a known mode.
  Does not generate content. Outputs a routing decision only.
metadata:
  author: David Johnson-Hall
  version: '1.4'
  layer: 3-decision-control
  architecture: Apollo GTM Skill Library
---

# Bounded Action Router

Layer 3 decision-control skill that takes structured state and determines what class of action is valid, safe, and appropriate next. It does not generate content. It outputs a routing decision.

## Purpose

bounded-action-router exists because the safest systems are the ones where the model does the least discretionary decision-making.

Given a structured state object from state-extractor, the router:
1. Eliminates impossible and prohibited actions (hard blocks)
2. Narrows the remaining action space using constraints and risk flags
3. Selects the most appropriate action class from what remains
4. Passes a routing decision with full rationale to the downstream skill

The core question it answers: which of the few valid action classes remains legal after blocks, constraints, and risk checks?

This is constraint-first elimination, not best-guess generation.

## When to Use This Skill

Use bounded-action-router whenever:
- Input has already been parsed into structured state (by state-extractor or equivalent)
- A system must choose what type of move is appropriate next
- Action selection should be explicit, reviewable, and deterministic
- The cost of a wrong move is non-trivial
- Downstream execution should be constrained to a known mode

**Typical use cases:**
- Email triage and response systems
- Slack and messaging assistants
- Meeting follow-up workflows
- Task delegation systems
- Workflow orchestration
- Agentic systems where open-ended reasoning is too risky
- Any system where "do nothing," "ask," "respond," "escalate," or "defer" are materially different outcomes

## When NOT to Use This Skill

- Input is still unstructured or ambiguous. Run state-extractor first.
- The task is purely descriptive and no action selection is needed (summarize this, explain that).
- The downstream system truly requires unconstrained planning rather than bounded routing.
- The input is a single atomic request with an obvious action (no routing decision needed).

## Core Principles

1. **Constraints outrank preferences.** Hard limits eliminate options before signals rank them.
2. **Risk outranks convenience.** A safe non-action beats a risky action.
3. **Finite action space only.** The router never invents a custom action class.
4. **Eliminate before selecting.** Narrow first, choose second.
5. **Uncertainty surfaces, never hides.** If the correct move cannot be selected with sufficient confidence, the system escalates or clarifies rather than guessing.
6. **Mechanical over creative.** The router behaves like a gate, not a strategist.
7. **Audit trail mandatory.** Every routing decision includes what was eliminated and why.
8. **Domain stays downstream.** The router selects abstract action classes. Domain-specific tactics belong in the executing skill.
9. **One input, one route.** The router produces a single routing decision per input state object. If the input contains multiple sub-items that require different action classes (multi-party threads, meeting notes with separate action items, emails with distinct asks), the upstream system should decompose the input into separate state objects before routing. The router does not internally decompose or multi-route.

## Input Contract

bounded-action-router expects structured input from state-extractor. It does not accept raw text.

**Required fields:**

### 1. Object Metadata

| Field | Description |
|---|---|
| state_id | Unique identifier for this state object |
| source_type | email_thread, slack_thread, meeting_notes, document, etc. |
| timestamp | When the state was extracted |
| freshness | current, recent, stale, unknown |
| parser_confidence | Overall confidence from state-extractor (high, medium, low or 0.0-1.0) |

### 2. Intent and Interaction State

| Field | Description |
|---|---|
| primary_intent | What is being asked or what situation requires action |
| intent_explicitness | explicit, inferred, implied, unknown |
| response_expected | Whether a reply or action is expected by another party |
| decision_ready | Whether enough information exists to make a decision |
| thread_stage | early, midstream, late, complete, unknown |
| requested_outcome | What the sender or situation calls for, if identifiable |

### 3. Actors and Authority

| Field | Description |
|---|---|
| sender | Who initiated or owns the current ask |
| recipient | Who is expected to act |
| authority_level | What the system/user is authorized to do (full, limited, none, unknown) |

### 4. Open Items

| Field | Description |
|---|---|
| unresolved_questions | Questions that remain unanswered |
| unresolved_dependencies | External conditions not yet met |

### 5. Constraints

Constraints that limit valid action space. Common types:

- time (deadline passed, window closing)
- policy (do not reply, hold, FYI only)
- legal (legal or compliance constraint)
- budget (budget cap or financial limit)
- technical (technical infeasibility or prerequisite)
- relationship (relationship sensitivity or damage risk)
- logistical (logistical blocker or feasibility limit)
- unknown (unclassified constraint, conservative default)
- authority (cannot commit, cannot approve)
- dependency (waiting on external input)
- confidence (key fields are inferred or unknown)
- channel (restricted to email only, no phone)
- data completeness (missing required fields)

Note: `scope` and `reversibility` are no longer valid constraint types (v3.0.3). Use the specific type that describes the constraint.

### 6. Risk Indicators

| Field | Description |
|---|---|
| overall_risk | low, medium, high |
| compliance_risk | low, medium, high |
| relationship_risk | low, medium, high |
| contradiction_present | Whether conflicting information exists in state |

### 7. Epistemic Tags

For major fields, the epistemic status from state-extractor:
- explicit, inferred, implied, disputed, assumed, missing, unknown

The router depends heavily on epistemic status because it uses confidence to gate action classes.

### 8. Signals

| Signal | Values |
|---|---|
| urgency | low, medium, high, unknown |
| ambiguity | low, medium, high |
| tension | low, medium, high |
| task_density | low, medium, high |
| decision_readiness | ready, partial, not_ready |
| expectation_of_response | none, low, medium, high |
| interaction_frame | transactional, relational, ambiguous |

interaction_frame is ideally provided by state-extractor (it is a Layer 2 parsing task). If absent from the input state, the router determines it during Step 4 using the frame detection heuristics defined there. When the router must determine the frame itself, it should note this in uncertainty_notes as a self-extracted field.

## Process

### Step 1: Validate Input State

Before routing, verify the state object meets minimum requirements:
- Required metadata fields are present
- Parser confidence is above minimum threshold
- No critical schema violations

If validation fails, return ESCALATE or REQUEST_CLARIFICATION with rationale noting state quality issues. Do not attempt to route on malformed state.

### Step 2: Apply Hard Blocks

Hard blocks are absolute disqualifiers. If triggered, certain or all action classes are removed immediately.

**Hard block triggers:**

| Trigger | Effect |
|---|---|
| Missing critical state fields needed for safe routing | Block all action classes except ESCALATE and REQUEST_CLARIFICATION |
| Policy prohibition (explicit "do not act" instruction) | Remove all active action classes; select NO_ACTION or LOG |
| High-severity contradiction in extracted state | Block EXECUTE and RESPOND; prefer ESCALATE |
| Safety or legal risk threshold exceeded | Block EXECUTE and unreviewed RESPOND; prefer ESCALATE |
| External dependency unresolved and required for any action | Block EXECUTE; preserve DEFER and ACKNOWLEDGE |
| Thread closed or issue already resolved | Block RESPOND and EXECUTE; allow CLOSE or NO_ACTION |
| Insufficient identity resolution for recipient | Block RESPOND and EXECUTE; prefer REQUEST_CLARIFICATION |
| State freshness too low for action | Block EXECUTE; prefer ESCALATE or REQUEST_CLARIFICATION |
| System lacks authority entirely | Block EXECUTE, CLOSE, and commitment-bearing RESPOND |

If a global hard block invalidates the entire action space, the router selects from the prescribed safe routes only (ESCALATE, REQUEST_CLARIFICATION, NO_ACTION, or LOG) and does not proceed to Steps 3-4.

### Step 3: Apply Constraint Checks

If no hard block fully stops action, evaluate constraints to shrink the remaining action space.

Constraints are not always total blockers. They often eliminate specific classes while leaving others valid.

**Constraint-driven vs. value-judgment elimination:**

Every elimination in Step 3 must be constraint-driven: a specific, identifiable hard or soft constraint makes the action class invalid or unsafe. If the only reason to remove an action class is that it seems low-value, unnecessary, or suboptimal, that is a value judgment, not a constraint elimination. Value judgments belong in Step 4 (signal-based selection), not Step 3.

Test: can you name the specific constraint that blocks this action class? If the answer is "it just doesn't add much" or "it's not needed," the elimination is a value judgment. Move it to Step 4 and let signal-based selection handle it.

Common disguised value judgments:
- "adds no value" (this is preference, not constraint)
- "not needed" (absence of need is not a blocking constraint)
- "silence is appropriate" (may be true, but it's a judgment about appropriateness)

Constraint eliminations should cite a named constraint type from the input contract (time, policy, legal, budget, technical, relationship, logistical, unknown, authority, dependency, confidence, channel, data_completeness).

**Constraint elimination logic:**

**Authority constraints** (cannot commit, approve, or execute):
- Remove EXECUTE
- Remove CLOSE if closure implies commitment
- Sometimes remove RESPOND if response would implicitly commit

**Confidence constraints** (key routing fields are inferred or unknown):
- Remove EXECUTE
- Remove CLOSE
- Sometimes remove RESPOND
- Preserve REQUEST_CLARIFICATION and ESCALATE

**Dependency constraints** (external data or approval pending):
- Remove EXECUTE
- Remove CLOSE
- Possibly remove PROPOSE_NEXT_STEP if premature
- Preserve DEFER and ACKNOWLEDGE

**Risk flag constraints** (legal, safety, compliance, relationship risk exceeds threshold):
- Remove EXECUTE
- Remove unreviewed RESPOND if sensitive
- Prefer ESCALATE
- Sometimes allow ACKNOWLEDGE only

**Scope constraints** (ask is outside system's domain):
- Remove domain-specific response classes
- Prefer ESCALATE or REQUEST_CLARIFICATION

**Explicit user instruction** (do not reply, hold, wait, FYI only):
- Remove RESPOND and EXECUTE
- Select NO_ACTION or LOG

**Time/freshness constraints** (state is stale or deadlines passed):
- Remove any action requiring current validity
- Prefer ESCALATE, DEFER, or REQUEST_CLARIFICATION

**Reversibility constraints** (action cannot be undone):
- Require higher confidence threshold for EXECUTE
- Prefer PROPOSE_NEXT_STEP over EXECUTE when relationship risk is high or action consequences are costly to reverse

### Step 4: Signal-Based Selection

Only after blocks and constraints are applied, use state signals to determine which remaining class is best.

**Relevant signals for selection:**
- Explicit ask present and answerable
- Urgency level
- Ambiguity level
- Pending question count
- Unresolved dependency count
- Decision readiness
- Expectation of response
- Thread/workflow stage
- Tension level
- Confidence profile from state-extractor
- Interaction frame (transactional vs relational)

**Transactional vs. relational framing:**

Before ranking surviving actions, determine whether the interaction is primarily transactional (task completion, information exchange, workflow progression) or relational (relationship maintenance, professional networking, social rapport, ongoing partnership).

**Frame detection heuristics:**

Signals that suggest relational framing:
- Sender is a named individual (not a system, bot, or organization)
- Prior interaction history exists or is implied (follow-ups, "circling back")
- Message includes social language (greetings, well-wishes, personal references)
- Sender's role involves ongoing relationship (recruiter, partner, client, colleague)
- Content is low-stakes and sender is voluntarily reaching out
- Sender invested visible effort across multiple touchpoints

Signals that suggest transactional framing:
- Sender is a system, automated notification, or organizational account
- Message is task-oriented with no social markers
- Interaction is one-shot with no implied continuity
- Content is FYI, status update, or informational delivery

If signals point in both directions or none are strong, tag the frame as ambiguous.

This distinction matters because the threshold for ACKNOWLEDGE and RESPOND shifts:
- In transactional frames, ACKNOWLEDGE has value only when the sender needs confirmation to proceed. If no one is waiting, NO_ACTION is clean.
- In relational frames, ACKNOWLEDGE has independent value as a relationship-maintenance signal even when no one is waiting. The bar for choosing it over NO_ACTION is lower.

**Where framing actually operates:** The constraint/value-judgment gate in Step 3 prevents ACKNOWLEDGE from being eliminated on preference grounds regardless of frame ("adds no value" is never a valid Step 3 elimination). The frame's actual work happens in Step 4, where it influences signal-based ranking between survivors. In relational frames, ACKNOWLEDGE gets stronger signal fit against NO_ACTION because relationship maintenance registers as a positive signal. In transactional frames, ACKNOWLEDGE's signal fit is weaker unless the sender is actively waiting. When signals clearly favor a lower-ranked class (like NO_ACTION over ACKNOWLEDGE), the hierarchy override mechanism applies and confidence drops to medium.

If the frame is ambiguous or the user's relational preferences are unknown, note this in uncertainty_notes rather than defaulting to transactional. The transactional default systematically undervalues courtesy, which compounds over time in professional contexts.

Signal-based selection is bounded comparison across remaining legal options, not open-ended reasoning.

**Confidence calibration rule:**

After elimination, count how many action classes remain viable (not eliminated by constraints or hard blocks). If two or more classes survived and the selection between them depends on signal interpretation, value judgment, or unknown user preferences rather than constraint logic, routing_confidence cannot be high. Set it to medium. If three or more classes survived with comparable signal fit, set it to low.

High confidence is reserved for cases where constraint elimination left exactly one viable class, or where signal fit for the selected class decisively outranks all survivors on multiple independent dimensions.

**Selection hierarchy (default preference order):**

When multiple valid action classes remain after elimination, apply this ordering as the default. Each position includes a conditional qualifier; the class is preferred only when its qualifier is met.

1. If hard-blocked globally: choose the prescribed safe route
2. If only one action remains: choose it
3. ESCALATE if risk threshold exceeded
4. REQUEST_CLARIFICATION if critical information is missing and obtainable
5. EXECUTE if explicit, safe, complete, and authorized
6. RESPOND if answerable and allowed
7. PROPOSE_NEXT_STEP if forward motion is helpful but not executable
8. DEFER if waiting is structurally correct
9. ACKNOWLEDGE if presence matters more than substance
10. LOG if documentation is the correct move
11. CLOSE if complete and state transition needed
12. NO_ACTION if nothing should happen

**Hierarchy override on signal strength:** The hierarchy is the default when signal fit is comparable across survivors. When signals clearly favor a lower-ranked class over a higher-ranked one, the signal-favored class wins. Any hierarchy override automatically sets routing_confidence to medium or low, because the decision required judgment beyond the default ordering. Document the override reasoning in the decision_path.

Override threshold test: can you name two or more independent signals that favor the lower-ranked class, with no signal of comparable weight favoring the higher-ranked class? If yes, override is justified. If the signals are mixed or only one signal favors the override, the hierarchy default holds. Example: expectation_of_response: low AND policy: optional both favor NO_ACTION over ACKNOWLEDGE, with no signal favoring ACKNOWLEDGE. Two independent signals, no counter-signal. Override justified.

This hierarchy can be tuned by domain, but the generic logic should stay abstract.

### Step 5: Assemble Routing Decision

Package the selected action class with full rationale, eliminated actions, active constraints, and downstream contract into the output schema.

## Bounded Action Space

These are the valid action classes. The router never invents a new class.

### NO_ACTION
No outward move should be taken. The thread is informational, the issue is resolved, action would create noise, or all valid actions are blocked and silent non-action is correct. This is not failure. It is an intentional terminal route.

### ACKNOWLEDGE
Respond minimally to confirm receipt, awareness, or presence without adding substantive progress. Use when sender needs confirmation, no meaningful answer is yet possible, politeness/continuity matters, or a stronger move is blocked by dependencies.

### REQUEST_CLARIFICATION
Ask for missing information necessary to proceed safely or correctly. Use when key fields are unknown, ambiguity blocks confident selection, assumptions would materially change the action, or multiple interpretations remain live. This is the main uncertainty-elevation route.

### RESPOND
Provide a substantive reply to the explicit ask using currently available state. Use when an answer is requested, information suffices, constraints allow response, and no blocking ambiguity remains. This is general response generation, not necessarily persuasive or domain-specific.

### EXECUTE
Carry out the requested or appropriate operational action rather than merely respond. Use when the system has authority, the action is clear, dependencies are satisfied, and doing is better than talking. Examples: create task, update record, trigger workflow, send handoff, schedule something, generate artifact, mark status.

### PROPOSE_NEXT_STEP
Suggest a concrete next move when the state indicates progression is possible but not yet authorized or finalized. Use when the system sees a likely next step, commitment is not yet justified, forward motion is useful, but explicit execution authority is absent.

### DEFER
Hold action until an external condition, dependency, or time gate is met. Use when waiting is the correct action, an external party response is needed, a prerequisite event has not occurred, or the state is not stale enough to escalate but not ready enough to move. Different from NO_ACTION because it is explicitly pending.

### ESCALATE
Route to a higher-trust actor, specialized system, or human review path. Use when risk is high, policy requires review, confidence is too low, authority is missing, exception handling is needed, or conflict cannot be safely resolved at this layer. This is the main fail-safe route.

### LOG
Produce a state-preserving or record-preserving action rather than an interactive response. Use when the correct move is documentation, information should be recorded, a digest or handoff summary is needed, or downstream systems need normalized output but not immediate external communication.

### CLOSE
Intentionally terminate the workflow segment. Use when the issue is complete, no further response is needed, closure is the right action, or the thread should be marked done. Distinct from NO_ACTION because it implies a state transition.

## Output Contract

The router outputs a routing decision, not final content.

```yaml
routing_decision:
  selected_action_class: NO_ACTION | ACKNOWLEDGE | REQUEST_CLARIFICATION
                         | RESPOND | EXECUTE | PROPOSE_NEXT_STEP
                         | DEFER | ESCALATE | LOG | CLOSE
  routing_confidence: high | medium | low

  rationale:
    summary: string
    decision_path:
      - string  # ordered list of elimination and selection steps

  eliminated_actions:
    ACTION_CLASS:
      reason: string
      elimination_type: hard_block | constraint | signal
      # hard_block = removed in Step 2 by absolute disqualifier
      # constraint = removed in Step 3 by named constraint
      # signal = not eliminated, but outranked in Step 4 signal-based selection

  active_constraints:
    - string  # constraints that influenced selection

  active_risks:
    - string  # risk factors that influenced selection

  downstream_contract:
    goal: string  # what the executing skill should accomplish
    required_fields_for_execution: [string]  # what data is needed
    tone_guidance: string | null  # suggested tone if relevant
    target_actor: string | null  # who the action is directed at
    scope_limit: string | null  # boundaries for execution

  uncertainty_notes:
    - string  # unresolved ambiguity that did not block routing
    # REQUIRED when routing_confidence is medium or low:
    # - Name the runner-up action class and what would tip the decision toward it
    # - Name any unknown user-preference variables that affect the choice
    #   (e.g., "unknown whether user values relationship maintenance with this contact")

  # composition_target override (applied after action class is selected)
  # Read composition_target from truth-speed-structure's routing directive if present.
  # Apply this override before passing the directive to L4:
  #   if composition_target = gense AND selected_action_class in [ESCALATE, DEFER, NO_ACTION, LOG, CLOSE]:
  #     composition_target = message-os   # GEN-SE does not handle these action classes
  # If truth-speed-structure has not run, composition_target defaults to message-os.
  composition_target: message-os | gense  # final value after override check
```

## How This Differs from GEN-SE Step 4

GEN-SE Step 4 is a specialized routing layer for email-sales thread processing. bounded-action-router is the generalized parent skill.

| Dimension | GEN-SE Step 4 | bounded-action-router |
|---|---|---|
| Scope | Email/sales/thread specific | Any parsed state from any domain |
| Action granularity | Behaviorally specific sales moves (24 action types) | Abstract action classes only (10 types) |
| Domain assumptions | Prospect stage, objection handling, CTA patterns, pipeline progression | None. Domain-agnostic. |
| Constraint model | Sales-specific (reply timing, persona fit, funnel stage, claim safety) | Abstract (authority, ambiguity, dependency, risk, completeness) |
| Architecture role | Part of one system (GEN-SE) | Reusable Layer 3 primitive for any system |
| Downstream | Feeds GEN-SE Steps 5-8 (sales reply generation) | Feeds any Layer 4 skill (message-os, legal-narrative-tightener, etc.) |

**Inheritance relationship:**
- bounded-action-router is the parent skill (general-purpose routing)
- GEN-SE Step 4 is a specialized child implementation (sales-specific routing)
- Domain-specific routers can override or extend the base action space while preserving the elimination-first logic

## Input-Type-Specific Guidance

### Email Threads
- Check for explicit reply expectation
- Evaluate thread stage (is this a first message, a follow-up, a resolution?)
- Watch for "FYI" or "no reply needed" signals that route to NO_ACTION or LOG
- Multi-party threads may have different action classes per actor

### Slack Conversations
- Higher tolerance for ACKNOWLEDGE (Slack norms expect lighter responses)
- Lower threshold for DEFER (async communication has natural pauses)
- Watch for cross-talk: the action class may differ per sub-thread

### Meeting Notes
- Primary action classes are usually EXECUTE (create tasks), LOG (document decisions), or REQUEST_CLARIFICATION (unclear ownership)
- RESPOND is rarely appropriate for meeting notes since there's no sender expecting a reply

### Support Tickets
- ESCALATE threshold should be lower than in conversational contexts
- CLOSE requires explicit resolution confirmation
- DEFER is common when waiting on customer input

### Legal/Compliance Content
- ESCALATE threshold should be significantly lower
- EXECUTE should require higher confidence and explicit authority
- RESPOND should be gated on legal review unless low-risk
- LOG is frequently the correct action for evidence preservation

## Failure Modes

### 1. Parser garbage in, router garbage out
If state-extractor produced a weak or malformed state, the router may appear deterministic while being wrong. Fix: require minimum schema validation and parser confidence thresholds. Fail into REQUEST_CLARIFICATION or ESCALATE when state quality is poor.

### 2. Over-routing from inferred state
Too many key fields are inferred rather than explicit, leading the router to choose an action class that feels more certain than the source warrants. Fix: confidence-gate high-impact routes (EXECUTE, CLOSE, RESPOND). Require explicit or high-confidence evidence for commitment-bearing actions.

### 3. Action-space mismatch
The real next move may not exist in the bounded inventory. Fix: ESCALATE serves as catch-all. Review logs for repeated forced escalations, which signal the action space needs expansion.

### 4. False clarification loops
System repeatedly chooses REQUEST_CLARIFICATION when it could have acknowledged, deferred, or partially responded. Fix: distinguish critical missing info from non-critical. Allow ACKNOWLEDGE or PROPOSE_NEXT_STEP when partial progress is valid.

### 5. Excessive escalation
Thresholds are too strict, routing too many cases to ESCALATE. The system becomes brittle and unhelpful. Fix: calibrate risk and confidence thresholds by action class. Allow low-risk actions (ACKNOWLEDGE, LOG) under lower certainty.

### 6. CLOSE vs NO_ACTION confusion
A resolved thread may need formal closure or may simply need silence. Fix: define CLOSE as a state transition (marks something as done). Define NO_ACTION as silent non-movement (nothing changes).

### 7. Competing valid actions
Both RESPOND and EXECUTE are valid, or both ACKNOWLEDGE and DEFER. Fix: apply the stable preference ordering from Step 4. Preserve audit trace of why the winner was chosen.

### 8. Latent domain leakage
A supposedly general router inherits hidden assumptions from GEN-SE or sales workflows. Fix: keep routing labels abstract. Avoid funnel-stage language in the generic skill. Push domain specifics into downstream executors.

### 9. Confidence inflation on routing decision
The router reports high routing_confidence even when the selection was a close call between two classes. Fix: if two or more classes survived elimination with similar signal fit, report medium or low confidence and include both candidates in uncertainty_notes.

### 10. Stale state routing
State was extracted hours or days ago. Routing decisions based on stale state may be invalid. Fix: check freshness field. If stale, block EXECUTE and RESPOND. Prefer REQUEST_CLARIFICATION or ESCALATE with note about state age.

### 11. Frame mismatch (transactional vs relational)
The router applies a transactional frame (is a response required?) when the interaction is actually relational (is a response valuable for the relationship?). This causes systematic under-selection of ACKNOWLEDGE and RESPOND in professional networking, recruiter outreach, partnership maintenance, and social-rapport contexts. The result looks correct mechanically but feels wrong relationally. Fix: explicitly identify the interaction frame before signal-based selection. When the frame is relational, lower the bar for ACKNOWLEDGE. When the frame is ambiguous, flag the unknown preference variable in uncertainty_notes rather than defaulting to transactional.

## Calibration Notes

### Tuning Guidance

- If downstream skills report receiving the wrong action class, the fix is usually in the constraint logic or the preference ordering, not in the downstream skill.
- If the router is producing too many ESCALATEs, thresholds are too tight. Loosen risk or confidence gates for low-impact action classes.
- If the router is producing too few ESCALATEs, thresholds are too loose. Audit recent RESPOND and EXECUTE decisions for cases that should have been escalated.
- If REQUEST_CLARIFICATION is dominating, check whether the state-extractor is under-extracting (too many unknowns) or whether the router's "critical missing info" definition is too broad.
- The router should feel conservative. It is cheaper to acknowledge and wait than to execute incorrectly.

### Implementation Modes

**Mode A: Rule-dominant deterministic.** Best for high-trust, auditable systems. Pure if/then elimination rules, threshold checks, priority ordering. Zero or minimal latent judgment.

**Mode B: Rule-bounded scoring.** Still bounded, but allows scoring signals among remaining actions. Elimination is still deterministic. Remaining actions are scored on fit. Tie broken mechanically.

Default to Mode A. Use Mode B only when the post-elimination space frequently has 3+ surviving classes with no clear deterministic winner.

## Example Transformations

Examples below are condensed for readability. In production, eliminated_actions should list all non-selected action classes with reason and elimination_type. If an action class was not eliminated by a hard block or constraint, it was outranked in signal-based selection (elimination_type: signal).

### Example 1: Missing Info Blocks Response

**Input state (condensed):**
```yaml
intent: request_update (explicit)
response_expected: true
decision_ready: false
dependencies: [awaiting vendor ETA]
constraints: {requires_external_input: true}
risk: {overall: low}
epistemics: {vendor_eta: unknown}
signals: {urgency: medium, ambiguity: medium}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: ACKNOWLEDGE
  routing_confidence: high
  rationale:
    summary: >
      A response is expected, but substantive update is blocked by
      missing external input that the sender cannot supply.
    decision_path:
      - No global hard block
      - EXECUTE removed: requires external input not yet available
      - RESPOND removed: cannot provide meaningful update without vendor ETA
      - REQUEST_CLARIFICATION not appropriate: missing info is external, not obtainable from sender
      - ACKNOWLEDGE selected: sender expectation is active, minimal confirmation is appropriate
  eliminated_actions:
    EXECUTE:
      reason: missing external dependency (vendor ETA)
      elimination_type: constraint
    RESPOND:
      reason: cannot provide meaningful update without vendor ETA
      elimination_type: constraint
    REQUEST_CLARIFICATION:
      reason: sender cannot supply the missing information (dependency is external)
      elimination_type: constraint
    CLOSE:
      reason: issue unresolved
      elimination_type: constraint
  active_constraints:
    - requires_external_input
  active_risks: []
  downstream_contract:
    goal: confirm receipt and set expectation that update depends on external input
    tone_guidance: direct_neutral
    target_actor: sender
  uncertainty_notes:
    - vendor ETA unknown, no timeline for resolution
```

### Example 2: Ambiguous Ask Requires Clarification

**Input state (condensed):**
```yaml
intent: ambiguous_request (inferred)
response_expected: true
decision_ready: false
open_questions: [unclear deliverable]
constraints: {}
risk: {overall: low}
epistemics: {requested_outcome: unknown}
signals: {ambiguity: high, urgency: low}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: REQUEST_CLARIFICATION
  routing_confidence: high
  rationale:
    summary: >
      The ask is not sufficiently specified to answer or execute safely.
    decision_path:
      - No hard block
      - EXECUTE removed: no defined action target
      - RESPOND removed: requested outcome is unknown
      - REQUEST_CLARIFICATION selected: ambiguity is resolvable by asking sender
  eliminated_actions:
    EXECUTE:
      reason: undefined action target
      elimination_type: constraint
    RESPOND:
      reason: cannot answer without knowing requested outcome
      elimination_type: constraint
    CLOSE:
      reason: issue not resolved
      elimination_type: constraint
  active_constraints: []
  active_risks: []
  downstream_contract:
    goal: obtain clarity on what the sender is actually requesting
    required_fields_for_execution: [requested_outcome]
    tone_guidance: direct_neutral
    target_actor: sender
  uncertainty_notes:
    - requested outcome is unknown
```

### Example 3: Clear Executable Request

**Input state (condensed):**
```yaml
intent: create_task (explicit)
response_expected: false
decision_ready: true
open_questions: []
dependencies: []
constraints: {authority_present: true}
risk: {overall: low}
epistemics: {task_owner: explicit, deadline: explicit}
signals: {urgency: medium, ambiguity: low}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: EXECUTE
  routing_confidence: high
  rationale:
    summary: >
      Explicit operational request is fully specified and within authority.
    decision_path:
      - No hard block
      - No disqualifying constraints
      - EXECUTE remains valid and outranks RESPOND for operational requests
  eliminated_actions:
    CLOSE:
      reason: issue not yet complete (task needs creation)
      elimination_type: constraint
  active_constraints: []
  active_risks: []
  downstream_contract:
    goal: create the specified task with stated owner and deadline
    required_fields_for_execution: [task_owner, deadline, task_description]
    target_actor: null
  uncertainty_notes: []
```

### Example 4: High-Risk Escalation

**Input state (condensed):**
```yaml
intent: respond_to_sensitive_issue (explicit)
response_expected: true
decision_ready: false
constraints: {}
risk: {overall: high, compliance: high}
epistemics: {facts: partially_inferred}
signals: {urgency: high, ambiguity: medium}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: ESCALATE
  routing_confidence: high
  rationale:
    summary: >
      Sensitive issue exceeds safe autonomous response threshold.
    decision_path:
      - High-risk flag triggered (compliance: high)
      - EXECUTE removed: authority/risk mismatch
      - RESPOND removed: compliance exposure on partially inferred facts
      - ESCALATE selected as prescribed safe route for high-risk state
  eliminated_actions:
    EXECUTE:
      reason: risk exceeds autonomous authority
      elimination_type: hard_block
    RESPOND:
      reason: compliance risk on partially inferred facts
      elimination_type: hard_block
    CLOSE:
      reason: issue unresolved
      elimination_type: constraint
  active_constraints: []
  active_risks:
    - compliance risk: high
    - facts partially inferred
  downstream_contract:
    goal: route to human review or specialized compliance handler
    scope_limit: do not generate external-facing content
  uncertainty_notes:
    - key facts are partially inferred, not fully explicit
```

### Example 5: Resolved Thread

**Input state (condensed):**
```yaml
intent: resolved_confirmation (explicit)
response_expected: false
decision_ready: true
thread_stage: complete
open_questions: []
dependencies: []
risk: {overall: low}
signals: {urgency: low, ambiguity: low}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: CLOSE
  routing_confidence: high
  rationale:
    summary: >
      Thread is confirmed complete with no outstanding items.
    decision_path:
      - No hard block
      - No remaining open items or dependencies
      - Thread stage is complete
      - CLOSE selected as state transition to mark resolution
  eliminated_actions:
    RESPOND:
      reason: no response expected, thread is complete
      elimination_type: hard_block
    EXECUTE:
      reason: no action requested, issue already resolved
      elimination_type: hard_block
  active_constraints: []
  active_risks: []
  downstream_contract:
    goal: mark thread or workflow segment as closed
  uncertainty_notes: []
```

### Example 6: Co-parenting Communication with Mixed Signals

**Input state (condensed):**
```yaml
intent: schedule_change_request (explicit)
response_expected: true
decision_ready: false
open_questions: [whether change conflicts with existing commitment]
dependencies: [need to check personal calendar]
constraints: {requires_verification: true, relationship_sensitivity: high}
risk: {overall: medium, relationship: high}
epistemics: {proposed_date: explicit, conflict_status: unknown}
signals: {urgency: medium, ambiguity: medium, tension: high}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: DEFER
  routing_confidence: medium
  rationale:
    summary: >
      Schedule change request requires calendar verification before
      any substantive response. Relationship sensitivity makes
      premature commitment or rejection risky. ACKNOWLEDGE survived
      as a viable alternative but DEFER is more precise.
    decision_path:
      - No global hard block
      - EXECUTE removed (constraint): cannot commit without verifying conflict
      - RESPOND removed (constraint): cannot commit or decline without calendar verification
      - REQUEST_CLARIFICATION removed (constraint): missing info is internal, not obtainable from sender
      - CLOSE removed (constraint): issue unresolved
      - ACKNOWLEDGE survived elimination: no constraint blocks receipt confirmation
      - DEFER survived elimination: no constraint blocks holding for internal check
      - Two survivors. DEFER selected over ACKNOWLEDGE: action is pending internal verification, not just receipt. DEFER captures the structural state (waiting on a specific condition) more precisely than ACKNOWLEDGE (which only confirms awareness).
  eliminated_actions:
    EXECUTE:
      reason: conflict status unknown, cannot commit
      elimination_type: constraint
    RESPOND:
      reason: cannot commit or decline without calendar verification
      elimination_type: constraint
    REQUEST_CLARIFICATION:
      reason: information needed is internal, not obtainable from sender
      elimination_type: constraint
    CLOSE:
      reason: issue unresolved
      elimination_type: constraint
    ACKNOWLEDGE:
      reason: DEFER is more precise for this state (pending internal verification, not just receipt)
      elimination_type: signal
  active_constraints:
    - requires calendar verification
    - relationship sensitivity: high
  active_risks:
    - relationship risk from premature or careless response
  downstream_contract:
    goal: verify calendar availability, then re-route for substantive response
    required_fields_for_execution: [conflict_status]
    tone_guidance: careful_neutral
    target_actor: co-parent
    scope_limit: do not commit or decline until conflict is verified
  uncertainty_notes:
    - "Runner-up: ACKNOWLEDGE. If calendar check will take significant time, an immediate acknowledgment ('Got it, let me check my schedule') followed by DEFER may be the better compound move."
    - conflict status unknown pending internal check
    - tension level is high, which may affect tone requirements downstream
```

### Example 7: Contested Path with Relational Framing (Recruiter Close-Out)

**Input state (condensed):**
```yaml
intent: recruiter_follow_up_with_graceful_exit (explicit)
response_expected: false (inferred)
decision_ready: true
thread_stage: late (inferred from subject line; only one message visible)
open_questions: []
dependencies: []
constraints:
  - {type: authority, detail: "referral request requires personal judgment outside system authority"}
  - {type: policy, detail: "sender explicitly framed response as optional"}
risk: {overall: low, relationship: low}
epistemics:
  primary_intent: explicit
  response_expected: inferred
  sender_identity: explicit
  thread_stage: inferred
signals:
  urgency: low
  ambiguity: low
  tension: low
  task_density: low
  expectation_of_response: low
  interaction_frame: relational
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: NO_ACTION
  routing_confidence: medium
  rationale:
    summary: >
      Graceful-exit recruiter email with soft referral ask. Sender
      released recipient from obligation. No constraint blocks
      NO_ACTION. However, relational frame means ACKNOWLEDGE
      survived elimination and remains a viable alternative.
    decision_path:
      - No global hard block
      - EXECUTE removed (constraint): authority — referral decision requires personal judgment
      - RESPOND removed (constraint): authority — no substantive content within system authority
      - REQUEST_CLARIFICATION removed (constraint): no ambiguity present
      - CLOSE removed (constraint): no formal workflow to terminate
      - DEFER removed (signal): nothing is pending, thread is terminal
      - LOG removed (signal): no record-keeping value identified
      - PROPOSE_NEXT_STEP removed (signal): no forward motion warranted
      - ESCALATE removed (signal): no risk or authority concern
      - ACKNOWLEDGE survived elimination — relational frame prevents value-judgment removal
      - NO_ACTION survived elimination — no constraint blocks it
      - Two survivors: ACKNOWLEDGE (rank 9) and NO_ACTION (rank 12). Default hierarchy favors ACKNOWLEDGE.
      - Hierarchy override applied: expectation_of_response is low, policy constraint marks response as optional, and sender signaled closure. Signals clearly favor NO_ACTION over ACKNOWLEDGE despite lower hierarchy rank.
      - Override triggers medium confidence. Selection depends on unknown user preference for relationship maintenance.
  eliminated_actions:
    EXECUTE:
      reason: referral decision requires personal judgment outside system authority
      elimination_type: constraint
    RESPOND:
      reason: no substantive content within system authority
      elimination_type: constraint
    REQUEST_CLARIFICATION:
      reason: no ambiguity present
      elimination_type: constraint
    CLOSE:
      reason: no formal workflow to terminate
      elimination_type: constraint
    DEFER:
      reason: nothing pending, thread is terminal
      elimination_type: signal
    LOG:
      reason: no record-keeping value identified
      elimination_type: signal
    PROPOSE_NEXT_STEP:
      reason: no forward motion warranted
      elimination_type: signal
    ESCALATE:
      reason: no risk or authority concern
      elimination_type: signal
    ACKNOWLEDGE:
      reason: hierarchy override — signals (low expectation, optional policy, sender closure) favor NO_ACTION despite ACKNOWLEDGE ranking higher by default
      elimination_type: signal
  active_constraints:
    - "sender explicitly framed response as optional"
    - "referral decision requires personal judgment outside system authority"
  active_risks: []
  downstream_contract:
    goal: null
    required_fields_for_execution: []
    tone_guidance: null
    target_actor: null
    scope_limit: null
  uncertainty_notes:
    - "Runner-up: ACKNOWLEDGE. A brief courtesy reply ('Thanks Erin, I'll keep you in mind') has relationship-maintenance value. Tips toward ACKNOWLEDGE if user values professional networking courtesy."
    - "Unknown preference variable: whether user prioritizes recruiter relationship maintenance. This is a personal-preference input the router cannot resolve."
    - "Subject line 'One last attempt!' implies prior thread history not visible. Prior context could change routing if it contained commitments or open questions."
    - "If user knows a potential referral, correct route shifts from NO_ACTION to RESPOND."
```

### Example 8: Hard Block on Contradictory State

**Input state (condensed):**
```yaml
intent: approve_vendor_contract (explicit)
response_expected: true
decision_ready: true
open_questions: []
dependencies: []
constraints: {authority_present: true}
risk: {overall: medium, compliance: medium}
epistemics: {contract_value: explicit, approval_authority: explicit, vendor_status: disputed}
contradiction_present: true
contradiction_detail: "Finance flagged vendor as suspended, but procurement says vendor is active. Both sources are authoritative."
signals: {urgency: high, ambiguity: medium, tension: medium}
```

**Routing decision:**
```yaml
routing_decision:
  selected_action_class: ESCALATE
  routing_confidence: high
  rationale:
    summary: >
      High-severity contradiction between two authoritative sources
      on vendor status blocks safe execution or commitment.
    decision_path:
      - Hard block triggered: high-severity contradiction in extracted state
      - EXECUTE blocked: cannot approve contract when vendor status is disputed between authoritative sources
      - RESPOND blocked: any substantive response risks implicitly siding with one source
      - ESCALATE selected as prescribed safe route for contradictory state
  eliminated_actions:
    EXECUTE:
      reason: high-severity contradiction on vendor status blocks safe approval
      elimination_type: hard_block
    RESPOND:
      reason: substantive response risks implicit commitment on disputed facts
      elimination_type: hard_block
    CLOSE:
      reason: issue unresolved
      elimination_type: constraint
    PROPOSE_NEXT_STEP:
      reason: cannot propose direction without resolving contradiction
      elimination_type: constraint
  active_constraints: []
  active_risks:
    - vendor status disputed between finance and procurement
    - compliance risk on acting with contradictory authoritative inputs
  downstream_contract:
    goal: route to human reviewer who can resolve the finance/procurement contradiction
    required_fields_for_execution: [resolved_vendor_status]
    scope_limit: do not approve, reject, or imply position on vendor status
  uncertainty_notes:
    - "Contradiction source: finance says suspended, procurement says active. Resolution requires cross-department verification."
```
