---
name: constraint-first-reasoner
description: >
  Layer 2B cognitive parser that maps the constraint landscape before any downstream
  skill decides what to do. Consumes structured state from state-extractor and epistemic
  tags from reality-filter, then identifies, classifies, ranks, and composes all active
  constraints into a structured constraint map. Surfaces hard blocks, soft limits,
  dependencies, resource caps, timing windows, competing priorities, epistemic restrictions,
  authority boundaries, policy boundaries, and reversibility constraints. Analyzes
  constraint interactions, detects tradeoffs, and emits downstream handling guidance
  so bounded-action-router chooses only from action classes that remain valid under
  current reality. Use when downstream behavior depends on feasibility, safety, timing,
  dependencies, limited authority, scarce resources, incomplete knowledge, or competing
  objectives.
metadata:
  author: David Johnson-Hall
  version: '1.1'
  layer: 2B-cognitive-parser
  architecture: Apollo GTM Skill Library
---

# Constraint-First Reasoner

Layer 2B cognitive parser. Maps the constraint landscape before any downstream skill decides what to do. It is a boundary-setter, not a planner.

## Purpose

constraint-first-reasoner exists because action selection is corrupted when the model evaluates options before it has explicitly modeled the boundaries. Without a dedicated constraint pass, models tend to:

- treat all theoretically available actions as equally available
- collapse uncertainty into false permission
- silently optimize for apparent usefulness instead of actual feasibility
- ignore tradeoffs unless prompted directly
- over-index on goal completion while underweighting resource, timing, dependency, and epistemic limits

This skill forces elimination before selection. It makes the system reason about what cannot be done, what should not be done, and what may only be done conditionally before considering what action is attractive.

The architectural separation is deliberate:

- reality-filter says how well-grounded each claim is
- state-extractor says what is true in structured form
- constraint-first-reasoner says what those truths and uncertainties prohibit or limit
- bounded-action-router chooses from the surviving action classes

## When to Use This Skill

Use constraint-first-reasoner whenever downstream behavior depends on feasibility, safety, timing, dependencies, limited authority, scarce resources, incomplete knowledge, or competing objectives.

Run by default whenever:
- the system may take or recommend actions
- multiple candidate actions are possible
- upstream state contains uncertainty or incomplete information
- there are explicit or implicit dependencies
- there are deadlines, budgets, permissions, capacity limits, or policy boundaries
- the task involves prioritization, tradeoffs, or escalation decisions

It is especially important when the system might otherwise confidently act on partial truth.

**Run constraint-first-reasoner before:**
- bounded-action-router when action selection depends on feasibility constraints
- execution skills when actions have external side effects or irreversible consequences
- message generation when response framing depends on what the system is allowed to assert

## When NOT to Use This Skill

- Input is a single atomic instruction with no constraints, dependencies, or competing objectives
- The task is purely creative or exploratory with no downstream action dependency
- All constraints are already mapped by a trusted upstream system and the receiving layer is configured to trust that mapping
- The action space is a single option with no elimination needed

## Core Principles

1. **Eliminate before selecting.** Map what cannot, should not, or may only conditionally be done before considering what is attractive. Action spaces shrink before scoring begins.
2. **Constraints are not obstacles to work around.** They are the real decision surface. The router should inherit a mechanically reduced action space, not an aspirational one.
3. **Epistemic weakness is a constraint.** When upstream claims are tagged asserted, assumed, disputed, or unknown, those truth conditions restrict what actions are safe. Truth status without behavioral consequence is not enough.
4. **Do not silently collapse tradeoffs.** When two valid objectives cannot both be fully satisfied, surface the tension. The router or human should see what is in conflict and why.
5. **Split before classifying.** Compound constraints get decomposed into atomic units before weighting. Bottlenecks and tradeoffs only become visible after decomposition.
6. **Hard blocks outrank soft optimization.** Policy, authority, and impossibility constraints dominate all ordinary utility reasoning.
7. **Be conservative about commitment, not conservative about motion.** Block final commitment, definitive factual framing, and irreversible execution. Allow clarification, verification, acknowledgment, and caveated options.
8. **Constraint origin survives.** Whether a constraint is explicit, inferred, or epistemic-derived must persist through the map so downstream layers can audit why actions were eliminated.
9. **Interaction analysis is mandatory.** Constraints do not operate in isolation. Amplification, conflict, bottlenecks, cascades, and narrowing effects must be analyzed and reported.

## Layer Role in the Stack

See `docs/archive/FOUNDATION.md` for the full layer stack. constraint-first-reasoner sits at Layer 2B.

Layer 2B is the bridge between "what the situation is" and "what classes of behavior remain valid."

No downstream skill should commit to consequential action if the constraint landscape has not been explicitly mapped. If constraint-first-reasoner has not run, the router should treat that as a meta-constraint: `constraint_landscape_unmapped = true`. Router effect: do not select high-commitment actions. Either run constraint mapping first or route to low-risk holding behavior.

## Input Contract

constraint-first-reasoner accepts one required input, one conditionally required input, and three optional inputs.

### Required

```yaml
structured_state:
  # Normalized state object from state-extractor.
  # At minimum must contain enough to recover:
  objective: string  # requested outcome or goal
  current_status: string  # stage, phase, or state marker
  actors: []  # roles and participants
  available_information: {}  # what is known
  dependencies: {}  # prerequisites, approvals, sequencing
  time_context: {}  # deadlines, windows, scheduling
  resources: {}  # budget, bandwidth, tool availability, capacity
  risk_indicators: {}  # sensitivity, consequence severity, reversibility
```

### Conditionally Required

```yaml
epistemic_map:
  # Claim-level or field-level truth-status metadata from reality-filter.
  # Keyed by state field path.
  # REQUIRED when reality-filter has run upstream.
  # ABSENT when reality-filter has NOT run. See Degradation Mode below.
  "field.path":
    truth_status: verified | probable | inferred | asserted | assumed
                  | disputed | contradicted | fabricated | unknown
                  | not_verifiable
    confidence: 0.00 - 1.00
    confidence_band: very_low | low | medium | high | very_high
    source_quality: authoritative | primary_direct | primary_self_report
                    | secondary_reliable | secondary_unverified | hearsay
                    | unsourced | model_generated | conflicted
```

### Degradation Mode (epistemic_map absent)

When reality-filter has not run upstream, `epistemic_map` will be absent. The skill degrades as follows:

1. **Substitute source**: Use state-extractor's per-field `epistemic_status` tags as the epistemic signal. Map using the tag set mapping from `docs/archive/FOUNDATION.md`:
   - `explicit` → treat as `verified` (high confidence)
   - `inferred` → treat as `inferred` (medium confidence)
   - `implied` → treat as `assumed` (moderate restriction)
   - `disputed` → treat as `disputed` (major restriction)
   - `assumed` → treat as `assumed` (stronger restriction)
   - `missing` → treat as `unknown` (missing-information constraint)
   - `unknown` → treat as `unknown` (missing-information constraint)
2. **Emit meta-constraint**: `degraded_epistemic_input` with severity `moderate`, noting that epistemic analysis is based on state-extractor tags rather than reality-filter verification. This surfaces in the constraint map so downstream skills know the grounding is weaker.
3. **Behavioral impact**: All constraints derived from epistemic signals get `certainty: uncertain` (rather than `verified` or `likely`). This raises the threshold for high-commitment action classes at L3.
4. **Do NOT halt**: Unlike `insufficient_structured_state`, absent `epistemic_map` does not block analysis. The pipeline can proceed with degraded epistemic confidence.

### Optional

```yaml
domain_context:
  # Domain-specific weighting rules or norms that affect constraint interpretation.
  domain: general | legal | financial | medical | ops | sales | custom
  domain_rules: []  # domain-specific constraint escalation or relaxation rules

policy_context:
  # Safety, organizational, legal, or workflow rules.
  policies: []  # named policies with scope and effect

action_space_hint:
  # Optional list of candidate downstream action classes, if already known.
  # Helps bind constraints to affected actions.
  candidate_actions: []
```

### Input Sufficiency Check

If the structured state is too thin to perform constraint analysis, the skill should:
1. Generate a meta-constraint: `insufficient_structured_state`
2. Block substantive routing
3. Allow only clarification, retrieval, verification, or safe fallback action classes

## Process

### Step 1: Validate Input Sufficiency

Check whether structured_state is present enough to do constraint analysis. Verify that the minimum required fields (objective, current_status, actors, dependencies, time_context, resources, risk_indicators) are populated.

If structured_state is insufficient, emit meta-constraint `insufficient_structured_state` and halt substantive analysis. Allow only clarification and retrieval actions downstream.

Check whether epistemic_map is present. If absent, enter Degradation Mode (see Input Contract above): substitute state-extractor's epistemic tags, emit `degraded_epistemic_input` meta-constraint, and proceed with reduced epistemic confidence.

### Step 2: Extract Explicit Constraints

Pull directly stated limitations from state. These are constraints that appear as literal facts in the structured state.

Look for:
- budget amounts or caps
- deadlines or time windows
- stated prohibitions or restrictions
- missing attachments, inputs, or prerequisites
- approval requirements
- stated permissions or lack thereof
- explicitly mentioned risks or consequences

Mark each as `origin: explicit`.

### Step 3: Derive Implicit Constraints

Infer operational constraints from state structure, domain rules, and common patterns. These are constraints not directly stated but logically necessary.

Derivation patterns:
- if `approval_required = true` and `approval_status = missing`, derive dependency block
- if deadline has passed, derive hard timing block
- if `source_quality = weak` and action irreversibility is high, derive epistemic restriction
- if audience is external, derive elevated certainty threshold
- if action involves financial commitment, derive verification requirement
- if tool access is absent, derive environmental constraint

Mark each as `origin: inferred`. Inferred constraints must include the derivation logic that produced them.

### Step 4: Decompose Compound Constraints

Split compound constraints into atomic units before weighting.

Example input: "We need to reply today, but legal has not approved the statement, and the facts are still disputed."

Decompose into:
1. Timing window: response expected today
2. Dependency: legal approval missing
3. Epistemic restriction: facts disputed
4. Possible competing priority: responsiveness vs accuracy/compliance

Why decompose:
- the router needs atomic reasons for elimination
- tradeoff detection only works when distinct constraints are explicit
- bottlenecks become visible only after decomposition

After decomposition, the skill may also emit a higher-level composite interaction summary.

### Step 5: Apply Hard-Block Detection

Before anything else, find constraints that make actions invalid or prohibited with no balancing test:
- policy violations
- authority failures
- impossible preconditions
- passed deadlines for non-recoverable actions
- missing mandatory dependencies
- non-permitted action classes

These dominate the map. Mark as `severity: blocking`.

### Step 6: Evaluate Epistemic Restrictions

Translate upstream truth-status and source-quality signals into constraints. This must happen early because uncertainty changes what kinds of actions are safe.

**Epistemic-to-constraint translation rules:**

| Truth Status | Constraint Effect |
|---|---|
| verified | Usually no epistemic constraint unless action itself is high-risk for another reason |
| probable | Light restriction; may require caveated framing for external actions |
| inferred | Light to moderate restriction depending on whether the inference is central to the action |
| asserted | Moderate restriction if action would operationalize the claim as true |
| assumed | Stronger restriction; assumption is not evidence. Often blocks commitment-heavy actions |
| disputed | Major restriction. Prevents commit/publish/accuse/escalate until reconciliation or attributed framing |
| contradicted | Hard block against treating the claim as decision substrate |
| fabricated | Hard block against treating the claim as decision substrate |
| unknown | Missing-information constraint. Routes toward clarification, retrieval, verification, or scoped fallback |
| not_verifiable | Light restriction; flag that claim cannot anchor factual assertions |

**General rule:** The weaker the grounding and the higher the action consequence, the stronger the epistemic constraint.

Mark each as `origin: epistemic-derived` with source field reference.

### Step 7: Identify Resource and Timing Constraints

Map available time, tools, budget, bandwidth, token budget, scheduling windows, and availability constraints.

Check:
- time remaining against deadline
- budget remaining against action cost
- human bandwidth against task volume
- tool availability against action requirements
- capacity limits against scope

### Step 8: Detect Dependencies and Sequencing

Determine what must happen first and what actions are only conditionally allowed.

Look for:
- approval gates
- information prerequisites
- tool or access prerequisites
- sequencing requirements (A must complete before B)
- conditional permissions (allowed only if X is true)

### Step 9: Detect Competing Priorities and Tradeoffs

Identify goal pairs that cannot both be maximized under current limits.

Common tradeoff patterns:
- speed vs certainty
- helpfulness vs compliance
- personalization vs privacy
- cost control vs coverage
- throughput vs quality
- relationship preservation vs boundary enforcement

For each tradeoff:
- identify the two competing constraints
- name the tension clearly
- indicate whether policy already resolves it
- indicate whether silent resolution is allowed
- provide router guidance

A tradeoff exists when: two valid objectives cannot both be fully satisfied, satisfying one materially worsens the other, and no policy rule already determines precedence.

Tradeoffs can exist between individual constraints or between interaction clusters. When the most important tension is between two amplified groups of constraints (e.g., "acquisition path: certainty + cofounder damage" vs "independent path: upside + epistemic weakness + runway risk"), the tradeoff pair should reference the interaction IDs, not individual constraint IDs. Use `side_a_type: interaction` and `side_b_type: interaction` in the output schema.

### Step 10: Classify and Weight Constraints

Type each constraint using the taxonomy (defined below). Assign dominance metadata.

Each constraint gets the severity, certainty, immediacy, scope, reversibility_impact, and dependency_centrality metadata fields. See `docs/archive/FOUNDATION.md` for the Constraint Severity definitions and dominance hierarchy.

### Step 11: Analyze Interactions

Evaluate whether constraints reinforce, conflict, bottleneck, cascade, or jointly narrow the action space.

**Interaction types:**

**Amplifying:** Two or more constraints together become more restrictive than the sum of their parts.
Example: Moderate time pressure + incomplete data + irreversible action. Individually manageable, together they may force "verify first" or "do not act."

**Conflicting:** Two constraints push in opposite valid directions.
Example: Need fast response vs need high-confidence sourcing. The skill must not hide this. It should create a tradeoff pair.

**Bottleneck:** A single dependency or scarce resource is the chokepoint through which many options must pass.
Example: Need legal approval before any outbound communication. Mark as dominant bottleneck constraint.

**Cascading:** One constraint produces or activates another.
Example: Unknown recipient intent creates epistemic restriction, which then activates a policy against personalized commitment.

**Masked:** A seemingly minor fact hides a stronger limitation.
Example: "Can't confirm current pricing" is actually a sales/reputational/legal constraint if quoting price is consequential.

**False conflict:** Sometimes constraints only appear conflicting because the action set is too narrow.
Example: Accuracy vs speed may be resolvable by routing to a lightweight acknowledgment rather than full completion. The skill should note when conflict can be dissolved by action decomposition.

For each significant interaction, emit:
- participating constraint IDs
- interaction type
- combined effect
- whether the interaction creates a forced tradeoff, a bottleneck, or a higher-severity routing rule

### Step 12: Deduplicate by Root Cause

Check for constraints that share the same underlying limitation. The same root cause should not appear as multiple constraints inflating severity.

Allow multiple evidentiary anchors but emit one canonical constraint object per root cause.

### Step 13: Identify Information Gaps

After mapping constraints on what IS present, check what SHOULD be present but is not. Epistemic restrictions flag weakness in existing information. Information gaps flag absence of information a well-informed decision requires.

For each gap, assess:
- What specific information is missing
- How its absence degrades decision quality
- Whether it blocks responsible decision-making or only degrades it
- How to acquire it, if a path exists

Common gap patterns:
- No independent verification of a key claim (only self-reported data)
- No valuation, assessment, or audit where one would be standard
- No input from a stakeholder whose interests are materially affected
- No legal, compliance, or regulatory review where domain norms require one
- No customer, market, or operational data where the decision depends on it
- No formal advisor engagement where the stakes warrant it

Severity:
- **blocking:** The decision cannot be responsibly made without this information. Example: accepting an acquisition offer with no independent valuation.
- **degrading:** The decision can be made but quality suffers materially. Example: publishing a case study without verifying the metrics with the customer.
- **informational:** Would improve the decision but is not strictly required. Example: employee sentiment data when the core decision is financial.

Do not inflate gaps. Not every conceivable piece of missing information is a gap. A gap exists only when the absence materially affects the quality of the decision or the safety of downstream action.

### Step 14: Rank, Partition, and Emit Constraint Map

Assign an explicit integer priority rank to each constraint (1 = highest) based on dominance metadata.

**Partition constraints into two tiers:**

- **decision_defining:** The top constraints that define the actual decision landscape. These are the ones the router must understand to make a correct choice. Typically 3-5 constraints. Criteria: blocking or strong severity, bottleneck centrality, global or class-wide scope, or participation in the dominant tradeoff.
- **contextual:** Valid constraints that provide relevant context but are secondary to the core decision. The router should be aware of them but they do not drive action class selection. Criteria: moderate or light severity, peripheral centrality, action-specific scope, or low immediacy.

The partition is a signal to the router, not a permission to ignore. Contextual constraints still appear in the map and can be promoted if conditions change.

Emit the full constraint map with:
- ranked and partitioned constraints with type, weight, origin, and handling guidance
- interaction analysis
- tradeoff pairs
- information gaps
- downstream routing guidance (eliminated actions, gated actions, preferred actions, escalation flags)

## Constraint Taxonomy

These are the valid constraint types. The skill never invents a new type.

### 1. hard_block
A condition that makes one or more actions invalid or prohibited. No balancing test allowed. Examples: legal prohibition, policy prohibition, lack of authority, impossible deadline, missing required credential, direct contradiction with non-overridable requirement.
Router effect: Eliminate affected actions immediately.

### 2. soft_limit
A real pressure or downside that should shape decision-making but does not fully forbid action. Examples: user preference, cost sensitivity, reputational risk, moderate uncertainty, quality degradation under speed pressure.
Router effect: Down-rank affected actions or require tradeoff surfacing.

### 3. resource_cap
A limit on available resources. Examples: time available, token budget, human bandwidth, budget dollars, tool quota, staffing capacity, compute or memory limit.
Router effect: Filter out actions exceeding available capacity or prefer minimal-resource actions.

### 4. timing_window
A temporal constraint that shapes when action can or cannot occur. Examples: deadline, business hours, waiting period, too early to act, too late to recover, sequencing window tied to another event.
Router effect: Gate, delay, accelerate, or eliminate actions based on temporal validity.

### 5. dependency
A prerequisite relationship where one fact, action, approval, or artifact must exist before another can be validly chosen. Examples: must verify before sending, must read before summarizing, must receive approval before committing, must obtain missing input before routing.
Router effect: Block downstream action until dependency is satisfied, or route to prerequisite acquisition.

### 6. competing_priority
A constraint produced by another objective that is also valid and cannot be fully satisfied simultaneously. Examples: speed vs accuracy, budget vs coverage, relationship preservation vs boundary enforcement.
Router effect: Surface tradeoff explicitly. Do not silently collapse unless policy says one objective dominates.

### 7. epistemic_restriction
A limit produced by uncertainty, dispute, poor sourcing, or insufficient grounding. Examples: fact unknown, claim asserted but unverified, source weak, conflicting evidence, confidence too low for action class.
Router effect: Prevent high-commitment actions. Allow only safe, reversible, or verification-seeking actions.

### 8. authority_boundary
A constraint based on role, access, ownership, or allowed scope of action. Examples: assistant cannot send without explicit ask, no access to connected source, user lacks decision rights, tool access absent.
Router effect: Eliminate unauthorized actions, prefer advisory or escalation actions.

### 9. policy_boundary
A normative or system-level rule that constrains permissible action. Examples: privacy restrictions, safety policy, legal sensitivity, anti-harassment boundary, regulated advice boundary.
Router effect: Immediate elimination or forced safe redirection.

### 10. reversibility_constraint
A constraint based on consequence severity if action is wrong. Examples: irreversible send, public publication, legal filing, high-cost deletion, social or contractual damage.
Router effect: Raise threshold for certainty. Require verification or human confirmation.

### 11. consistency_constraint
A requirement that the system not take actions inconsistent with prior accepted state or commitments. Examples: proposed action contradicts established timeline, message conflicts with prior position, recommendation breaks user-stated rule.
Router effect: Force reconciliation or escalation before action.

### 12. environmental_constraint
A real-world situational limit not reducible to preferences or formal policy. Examples: no internet access, user's local time, physical location, unavailable tool, offline mode, missing attachment.
Router effect: Constrain feasible execution paths.

## Output Contract

constraint-first-reasoner outputs a structured constraint map with routing guidance.

```yaml
constraint_map_output:
  skill: constraint-first-reasoner
  version: "1.1"

  summary:
    global_status: blocked | constrained | partially_feasible | feasible
    dominant_constraints: []  # IDs of highest-priority constraints
    action_space_narrowing: high | medium | low
    requires_human_tradeoff: true | false
    requires_verification_before_commitment: true | false

  constraints:
    - id: string
      rank: integer  # explicit priority rank, 1 = highest. Assigned in Step 14.
      tier: decision_defining | contextual  # see Step 14 partitioning
      label: string  # human-readable constraint name
      type: hard_block | soft_limit | resource_cap | timing_window
            | dependency | competing_priority | epistemic_restriction
            | authority_boundary | policy_boundary | reversibility_constraint
            | consistency_constraint | environmental_constraint
      origin: explicit | inferred | epistemic-derived
      source_constraint_type: string | null  # original SE/BAR constraint type (e.g., "budget", "technical") preserved for audit trail. Populated when L2B reclassifies an Adapter constraint into the 12-type taxonomy.
      source_fields: []  # state or epistemic_map fields that produced this constraint
      description: string

      severity: blocking | strong | moderate | light
      certainty: verified | likely | uncertain
      immediacy: active_now | upcoming | latent
      scope: action-specific | class-wide | global
      reversibility_impact: irreversible | costly | reversible
      dependency_centrality: bottleneck | important | peripheral

      affects_action_classes: []  # which downstream actions this constraint impacts

      handling:
        effect: eliminate | gate | down-rank | surface_tradeoff | require_verification | escalate
        router_guidance: string  # specific instruction for the router
        verification_needed: true | false
        escalation_needed: true | false

      derivation_notes: []  # for inferred and epistemic-derived constraints, the logic chain

  interactions:
    - id: string
      constraint_ids: []
      interaction_type: amplifying | conflicting | bottleneck | cascading | masked | false_conflict
      description: string
      combined_effect: string

  tradeoff_pairs:
    - id: string
      side_a: string  # constraint ID or interaction ID
      side_b: string  # constraint ID or interaction ID
      side_a_type: constraint | interaction  # what side_a references
      side_b_type: constraint | interaction  # what side_b references
      tension: string  # named tension (e.g., speed_vs_accuracy)
      description: string
      default_resolution: surface_to_router_or_human | policy_resolved | decompose_action
      silent_resolution_allowed: true | false

  information_gaps:
    # Structured surfacing of what SHOULD be present but ISN'T.
    # Epistemic restrictions flag weakness in what IS present.
    # Information gaps flag absence of what a well-informed decision REQUIRES.
    - id: string
      label: string  # human-readable gap name
      description: string  # what is missing and why it matters
      impact_on_decision: string  # how this gap degrades decision quality
      acquisition_path: string | null  # how to obtain it, if known
      severity: blocking | degrading | informational
        # blocking: decision cannot be responsibly made without this
        # degrading: decision can be made but quality suffers materially
        # informational: would improve decision but not strictly required

  downstream_guidance:
    eliminated_action_classes: []
    gated_action_classes:
      - action_class: string
        requires: []  # prerequisites before this action becomes valid
    preferred_action_classes: []
    escalation_recommended: true | false
    meta_constraints: []  # e.g., insufficient_structured_state, constraint_landscape_unmapped

  required_downstream_fields:
    # Minimum fields downstream layers MUST preserve and propagate.
    - id
    - rank
    - tier
    - type
    - severity
    - affects_action_classes
    - handling
```

## Handoff Contracts

### From reality-filter (Layer 1)

constraint-first-reasoner receives claim-level epistemic metadata including truth_status, confidence, confidence_band, source_quality, epistemic_flags, and handling flags. These are consumed as inputs to Step 6 (Evaluate Epistemic Restrictions).

When reality-filter's `rf_truth_status` field is present on state fields, use it as the authoritative epistemic signal. When absent, use state-extractor's epistemic tags with the mapping defined in reality-filter's handoff contract.

### From state-extractor (Layer 2A)

constraint-first-reasoner receives the normalized structured state object. The quality of constraint analysis depends directly on the quality of state extraction. If state-extractor has not separated explicit facts from inferred facts, unknowns, actors, goals, deadlines, dependencies, and resources, constraint reasoning degrades.

### To bounded-action-router (Layer 3)

The router should consume the constraint map, not reinvent constraints. The router uses:
- `eliminated_action_classes` to remove actions from consideration
- `gated_action_classes` to apply prerequisites before allowing actions
- `preferred_action_classes` to bias toward safe options
- `tradeoff_pairs` to surface decisions requiring human input or policy resolution
- `dominant_constraints` to understand the primary reasons for action space narrowing
- verification and escalation flags to determine workflow routing

**Constraint consumption pattern for the router:**
1. Remove eliminated action classes
2. Apply gates and prerequisites
3. Honor policy/authority boundaries
4. Inspect tradeoff pairs
5. Choose among remaining valid classes
6. If no valid class remains, escalate or request missing info

### To execution skills (Layer 4)

Execution skills should receive constraint context so they can:
- frame assertions with appropriate hedging when epistemic constraints are active
- avoid committing to facts that are gated behind verification
- respect authority boundaries in language and action
- honor timing constraints in scheduling and response framing

## Calibration Notes

### When to Be Stricter

Increase constraint weight when:
- action is irreversible
- safety or legal stakes are high
- user may rely on the output as factual
- upstream truth-status is weak
- permissions are unclear
- public or external communication is involved
- accusation, pricing, compliance, or health/legal advice is involved
- audience is external or senior

### When to Be More Permissive

Relax constraint weight when:
- action is reversible and low-cost
- action can be explicitly caveated
- the goal is exploration, brainstorming, or internal drafting
- uncertainty can be contained without misleading downstream actors
- router can choose a low-commitment action class
- all actions available are information-seeking or clarifying

### Domain Context Shifts Weight

- In legal contexts, disputed facts and missing evidence should quickly become blocking or escalation constraints
- In brainstorming contexts, inferred and assumed information may only create light constraints
- In outbound communication, unknown recipient intent should constrain personalization more than neutral acknowledgment
- In operational execution, missing tool access is often a hard environmental constraint, while stylistic preference is soft
- In financial contexts, unverified numbers should block commitment actions but allow caveated estimates

### Practical Calibration Principle

The skill should be conservative about commitment, not conservative about motion.

Allow:
- clarify
- verify
- acknowledge
- request missing input
- produce caveated options

Block:
- final commitment
- definitive factual framing
- irreversible execution
- high-risk escalation

## Failure Modes

### 1. Constraint inflation
The skill labels every fact as a constraint and overconstrains the system. Everything becomes "blocked," the action space collapses too aggressively, and the router becomes clarification-only too often. Fix: require that a constraint must actually restrict, gate, or shape action. Separate descriptive context from limiting context. Lower weight on non-binding preferences and weak inferences.

### 2. False dependencies
The skill invents prerequisites that are not real. Unnecessary holds, excessive sequencing requirements, brittle execution. Fix: distinguish required dependency from nice-to-have dependency. Require domain rule or explicit logic link for dependency creation. Mark inferred dependencies separately from explicit ones.

### 3. Missing implicit constraints
The skill only reads explicit constraints and misses operational reality. Unsafe routing, overly broad action space, accidental permission from silence. Fix: derive standard implicit constraints from domain patterns. Always check authority, timing, reversibility, and epistemic sufficiency even if not explicitly mentioned in the state.

### 4. Over-restriction
Uncertainty blocks all meaningful progress. Endless clarification loops, refusal to take reversible low-risk actions. Fix: distinguish between high-commitment and low-commitment actions. Let uncertainty constrain commitment level, not necessarily all motion. Allow safe fallback actions that preserve progress.

### 5. Under-restriction
Weakly grounded claims are allowed to drive consequential action. Confident but unsafe recommendations, hidden assumptions operationalized as fact. Fix: increase epistemic restriction weight when irreversibility or legal/social risk is high. Require verification before commitment-heavy actions.

### 6. Hidden tradeoffs
The skill emits weights but never surfaces tensions between competing constraints. The router appears arbitrary, humans cannot inspect why one objective lost. Fix: explicitly detect and emit tradeoff pairs whenever constraints push in opposite valid directions. Never silently resolve a tradeoff unless policy explicitly determines precedence.

### 7. Constraint duplication
The same underlying limitation appears multiple times and distorts ranking. Artificially inflated severity, repeated reasons for the same block. Fix: deduplicate by root cause (Step 12). Allow multiple evidentiary anchors but emit one canonical constraint object per root cause.

### 8. Poor domain calibration
A generic weighting scheme misreads domain-specific seriousness. Overreacts in casual domains, underreacts in legal/medical/financial domains. Fix: use domain_context to shift thresholds. Increase epistemic strictness and reversibility sensitivity in high-stakes domains.

### 9. Epistemic-to-constraint translation failure
Upstream truth-status tags are present but not converted into behavioral constraints. Claims tagged "disputed" or "unknown" pass through without generating action restrictions. Fix: Step 6 must always run. Every non-verified epistemic tag on a state field that could influence action must produce at least a light constraint.

### 10. Interaction blindness
Constraints are evaluated in isolation and their combined effect is missed. Three moderate constraints that jointly collapse the action space are treated as three independent moderate pressures. Fix: Step 11 (interaction analysis) is mandatory, not optional. Check every combination of active constraints with severity >= moderate for amplification and bottleneck effects.

## Example Transformations

Examples are condensed for readability. In production, all constraints should include full output schema fields.

### Example 1: Simple Hard Constraint Blocks an Action

**Input structured state:**
```yaml
objective: "Send final customer refund approval email"
current_status: awaiting_manager_approval
approvals:
  manager_required: true
  manager_received: false
deadline: today_5pm
resources:
  time_available_minutes: 30
```

**Input epistemic map:**
```yaml
"approvals.manager_required":
  truth_status: verified
  confidence: 0.98
"approvals.manager_received":
  truth_status: verified
  confidence: 0.98
```

**Output (condensed):**
```yaml
summary:
  global_status: blocked
  dominant_constraints: ["C1"]
  action_space_narrowing: high

constraints:
  - id: C1
    label: "Manager approval missing"
    type: dependency
    origin: explicit
    source_fields: ["approvals.manager_required", "approvals.manager_received"]
    description: "Manager approval is required but not yet obtained."
    severity: blocking
    certainty: verified
    immediacy: active_now
    scope: class-wide
    reversibility_impact: irreversible
    dependency_centrality: bottleneck
    affects_action_classes: ["send_final", "commit_refund"]
    handling:
      effect: gate
      router_guidance: "Do not select send or commit actions. Route to approval acquisition or hold."
      verification_needed: false
      escalation_needed: false

downstream_guidance:
  eliminated_action_classes: ["send_final", "commit_refund"]
  gated_action_classes:
    - action_class: "send_final"
      requires: ["manager_approval"]
  preferred_action_classes: ["request_approval", "prepare_draft", "hold"]
```

**Why this matters:** This is a classic hard dependency. The approval requirement is verified with high confidence. The system should not "be helpful" by bypassing it. The router receives a clean elimination and a redirect to prerequisite acquisition.

### Example 2: Competing Soft Constraints Create a Tradeoff

**Input structured state:**
```yaml
objective: "Respond to prospect email"
user_preferences:
  be_fast: true
  be_highly_personalized: true
account_context:
  research_depth: low
resources:
  time_available_minutes: 4
risk:
  wrong_personalization_cost: moderate
```

**Input epistemic map:**
```yaml
"account_context.research_depth":
  truth_status: verified
  confidence: 0.95
```

**Output (condensed):**
```yaml
summary:
  global_status: constrained
  dominant_constraints: ["C1", "C2"]
  action_space_narrowing: medium
  requires_human_tradeoff: true

constraints:
  - id: C1
    label: "Low research depth limits safe personalization"
    type: soft_limit
    origin: inferred
    source_fields: ["account_context.research_depth"]
    description: "Account research is shallow. Highly personalized messaging risks inaccuracy."
    severity: moderate
    certainty: verified
    immediacy: active_now
    scope: action-specific
    reversibility_impact: costly
    affects_action_classes: ["send_personalized"]
    handling:
      effect: down-rank
      router_guidance: "Prefer generic or lightly personalized response over deep personalization."
    derivation_notes:
      - "Verified low research depth + moderate wrong-personalization cost = unsafe to personalize deeply."

  - id: C2
    label: "4-minute time cap"
    type: resource_cap
    origin: explicit
    source_fields: ["resources.time_available_minutes"]
    description: "Only 4 minutes available. Deep research or elaborate drafting not feasible."
    severity: strong
    certainty: verified
    immediacy: active_now
    scope: class-wide
    affects_action_classes: ["deep_research", "elaborate_draft"]
    handling:
      effect: eliminate
      router_guidance: "Eliminate actions requiring more than 4 minutes."

tradeoff_pairs:
  - id: T1
    side_a: C1
    side_b: C2
    side_a_type: constraint
    side_b_type: constraint
    tension: speed_vs_personalization
    description: "User wants both speed and deep personalization, but low research depth and 4-minute cap make both impossible."
    default_resolution: surface_to_router_or_human
    silent_resolution_allowed: false

downstream_guidance:
  eliminated_action_classes: ["deep_research", "elaborate_draft"]
  preferred_action_classes: ["quick_neutral_response", "acknowledgment", "lightweight_clarification"]
```

**Why this matters:** Neither constraint fully blocks action. Together they create a real tradeoff that the system should not pretend it can resolve by maximizing both. The router sees the tension explicitly and can choose a response class that respects both pressures.

### Example 3: Epistemic Uncertainty Becomes a Routing Constraint

**Input structured state:**
```yaml
objective: "Draft public summary of incident"
claims:
  - text: "Vendor intentionally breached contract"
    field_ref: "claims[0]"
  - text: "Customer was notified on Friday"
    field_ref: "claims[1]"
audience: external
reversibility: low
```

**Input epistemic map:**
```yaml
"claims[0]":
  truth_status: disputed
  source_quality: secondary_unverified
  confidence: 0.42
  confidence_band: low
"claims[1]":
  truth_status: asserted
  source_quality: unsourced
  confidence: 0.51
  confidence_band: low
```

**Output (condensed):**
```yaml
summary:
  global_status: constrained
  dominant_constraints: ["C1", "C2", "C3"]
  action_space_narrowing: high
  requires_verification_before_commitment: true

constraints:
  - id: C1
    label: "Disputed breach allegation cannot anchor public statement"
    type: epistemic_restriction
    origin: epistemic-derived
    source_fields: ["claims[0]"]
    description: "Breach claim is disputed with low confidence and secondhand sourcing. Cannot be framed as established fact in external communication."
    severity: blocking
    certainty: likely
    immediacy: active_now
    scope: action-specific
    reversibility_impact: irreversible
    affects_action_classes: ["publish_definitive_summary", "accuse_vendor"]
    handling:
      effect: eliminate
      router_guidance: "Do not publish summary treating breach as fact. Allow attributed framing or evidence request only."
    derivation_notes:
      - "truth_status=disputed + source_quality=secondary_unverified + audience=external + reversibility=low = hard epistemic block on definitive framing."

  - id: C2
    label: "Notification timing insufficiently verified"
    type: epistemic_restriction
    origin: epistemic-derived
    source_fields: ["claims[1]"]
    description: "Notification timing is asserted without source. Cannot be stated as confirmed fact externally."
    severity: strong
    certainty: likely
    immediacy: active_now
    affects_action_classes: ["publish_definitive_summary"]
    handling:
      effect: gate
      router_guidance: "Require source verification before including notification timing in public statement."
      verification_needed: true

  - id: C3
    label: "External audience raises certainty threshold"
    type: reversibility_constraint
    origin: inferred
    source_fields: ["audience", "reversibility"]
    description: "Public external summary is low-reversibility. All claims require higher verification threshold."
    severity: strong
    certainty: verified
    immediacy: active_now
    scope: global
    affects_action_classes: ["publish_definitive_summary", "send_external"]
    handling:
      effect: require_verification
      router_guidance: "Raise certainty threshold for all claims before external publication."

interactions:
  - id: I1
    constraint_ids: ["C1", "C3"]
    interaction_type: amplifying
    description: "Disputed claim + low-reversibility external audience = stronger block than either alone."
    combined_effect: "Definitive summary is fully eliminated, not just down-ranked."

downstream_guidance:
  eliminated_action_classes: ["publish_definitive_summary", "accuse_vendor"]
  preferred_action_classes: ["attributed_summary", "internal_hold", "verification_request", "legal_review_request"]
  escalation_recommended: false
```

**Why this matters:** Weak upstream truth tags directly narrow safe routing. The disputed breach claim and unsourced notification timing, combined with an external audience and low reversibility, collapse the action space to attributed framing or verification-seeking actions only. This is exactly the epistemic-to-constraint translation the skill exists to perform.

### Example 4: Multiple Interacting Constraints Narrow More Than Any Single One Alone

**Input structured state:**
```yaml
objective: "Send revised contract today"
deadline: today_3pm
current_time: today_2:20pm
dependencies:
  legal_review_required: true
  legal_review_complete: false
resources:
  time_available_minutes: 40
facts:
  pricing_term_confirmed: false
action_consequence: high
```

**Input epistemic map:**
```yaml
"facts.pricing_term_confirmed":
  truth_status: unknown
  confidence: 0.20
  confidence_band: very_low
"dependencies.legal_review_complete":
  truth_status: verified
  confidence: 0.97
  confidence_band: very_high
```

**Output (condensed):**
```yaml
summary:
  global_status: blocked
  dominant_constraints: ["C1", "C2", "C3", "C4"]
  action_space_narrowing: high
  requires_human_tradeoff: false
  requires_verification_before_commitment: true

constraints:
  - id: C1
    label: "Legal review incomplete"
    type: dependency
    origin: explicit
    source_fields: ["dependencies.legal_review_required", "dependencies.legal_review_complete"]
    severity: blocking
    certainty: verified
    immediacy: active_now
    dependency_centrality: bottleneck
    affects_action_classes: ["send_final_contract"]
    handling:
      effect: gate
      router_guidance: "Do not send contract without legal review. Route to legal review request."

  - id: C2
    label: "40 minutes to deadline"
    type: timing_window
    origin: explicit
    source_fields: ["deadline", "current_time"]
    severity: strong
    certainty: verified
    immediacy: active_now
    affects_action_classes: ["send_final_contract", "complete_legal_review", "confirm_pricing"]
    handling:
      effect: gate
      router_guidance: "Time-constrained. Only fast-track actions are feasible."

  - id: C3
    label: "Pricing term unknown"
    type: epistemic_restriction
    origin: epistemic-derived
    source_fields: ["facts.pricing_term_confirmed"]
    severity: strong
    certainty: verified
    immediacy: active_now
    affects_action_classes: ["send_final_contract"]
    handling:
      effect: eliminate
      router_guidance: "Cannot send contract with unconfirmed pricing. Verify pricing first."
      verification_needed: true

  - id: C4
    label: "High-consequence action"
    type: reversibility_constraint
    origin: inferred
    source_fields: ["action_consequence"]
    severity: strong
    certainty: verified
    scope: global
    reversibility_impact: irreversible
    affects_action_classes: ["send_final_contract"]
    handling:
      effect: require_verification
      router_guidance: "Contract send is high-consequence. All inputs must be verified before execution."

interactions:
  - id: I1
    constraint_ids: ["C1", "C2"]
    interaction_type: bottleneck
    description: "Legal review is blocking and only 40 minutes remain. Legal review may not complete in time."
    combined_effect: "Sending contract today may be infeasible. Escalate or request deadline extension."

  - id: I2
    constraint_ids: ["C3", "C4"]
    interaction_type: amplifying
    description: "Unknown pricing + high-consequence action = elevated certainty threshold. Cannot send with unconfirmed terms."
    combined_effect: "Contract send is fully blocked until pricing is confirmed."

downstream_guidance:
  eliminated_action_classes: ["send_final_contract"]
  preferred_action_classes: ["request_deadline_extension", "escalate_to_manager", "obtain_pricing_confirmation", "request_legal_review"]
  escalation_recommended: true
```

**Why this matters:** Any one of these constraints might be manageable alone. Together they collapse the action space sharply. Legal review is a bottleneck under time pressure (I1). Unknown pricing plus high consequence amplifies the block (I2). The router inherits a clear picture: sending today is not feasible, and the system should escalate or acquire prerequisites rather than push through. This is precisely why interaction analysis is required.

## Anti-Patterns

These are the behaviors constraint-first-reasoner is designed to prevent:

- "The action seems helpful, so the constraints probably don't matter."
- "I'll mention the risk but proceed anyway."
- "Speed is important, so I'll skip verification."
- "The user wants it done, so I'll treat assumptions as facts."
- "There's a tradeoff, but one side is obviously better."
- "I don't see any explicit constraints, so everything is allowed."
- "The upstream tags say 'uncertain' but I'm pretty sure it's fine."
