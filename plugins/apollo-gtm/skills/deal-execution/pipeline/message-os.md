---
name: message-os
description: >
  Layer 4 domain-agnostic message composition engine. Converts a routed action class
  from bounded-action-router into concrete, channel-appropriate, epistemically safe
  human-readable communication. Enforces constraint inheritance, single-ask discipline,
  commitment boundaries, and AI-pattern avoidance. Produces structurally correct,
  sendable messages for any professional context: email, Slack, formal letters, CRM notes,
  ticket comments, meeting follow-ups, escalations, and relationship maintenance.
  Use when bounded-action-router has selected an action class and the system needs to
  express that action as an actual message. Does not decide what to do. Does not parse
  input. Does not rewrite for voice. It renders decisions into language.
metadata:
  author: David Johnson-Hall
  version: '1.0'
  layer: 4-expression
  architecture: Apollo GTM Skill Library
---

# Message OS

Layer 4 domain-agnostic message composition engine. Converts a routed action class into concrete human-readable communication while staying inside epistemic and constraint boundaries.

## Purpose

message-os exists because routing and composition are different cognitive problems. Deciding what class of action is valid is not the same as expressing that action in language. If you collapse them, the model smuggles decisions into wording.

bounded-action-router answers: what class of action is valid?
message-os answers: given that valid action class, what is the safest, clearest, channel-appropriate expression of it?

Without a dedicated composition layer, direct generation from routing decisions creates four recurring failures:

1. **Decision leakage.** The model "helpfully" adds asks, commitments, promises, or recommendations that were not present in the routed action.
2. **Epistemic inflation.** The model states uncertain or inferred claims as facts.
3. **Constraint drift.** The model violates authority, reversibility, sensitivity, timing, or channel constraints through phrasing even when the action class itself was correct.
4. **Channel incoherence.** The model produces email-like text in Slack, overly formal updates in relational contexts, or vague acknowledgements when a structured response is needed.

A dedicated message composition layer prevents: overcommitting, multi-ask sprawl, tone mismatch, unsupported claims, accidental escalation, hidden advice when only acknowledgement was routed, structural incoherence across channels, and sterile or ambiguous messaging that creates downstream confusion.

## When to Use This Skill

Use message-os whenever bounded-action-router has selected an action class and the system needs to produce actual message text.

Run by default whenever:
- the router has emitted a routing decision with a selected action class
- the output must be a human-readable message (email, Slack, letter, note, comment)
- the message must respect upstream epistemic tags, constraints, and authority boundaries
- channel-specific formatting and conventions matter
- the communication is non-sales professional context

**Run message-os after:**
- bounded-action-router (which tells it WHAT to do)
- constraint-first-reasoner (whose constraint map it inherits)

**Run message-os before:**
- humanizer-compressor (optional polish pass for voice and compression)
- Any send/delivery mechanism

## When NOT to Use This Skill

- The routed action class is NO_ACTION. There is nothing to compose.
- The task is B2B sales communication. Use GEN-SE instead. GEN-SE has its own specialized message generation pipeline (GRRIPS compiler, claims gate, drift check) tuned for sales.
- The task is pure content generation with no upstream routing decision (blog posts, marketing copy, creative writing).
- Input is still unstructured. Run state-extractor first.
- No routing decision exists. Run bounded-action-router first.
- The only task is voice/style rewriting of an existing draft. Use humanizer-compressor.

## Core Principles

1. **Obey the routed action class.** The action class is the ceiling. ACKNOWLEDGE means acknowledge. RESPOND means respond. Do not upgrade, downgrade, or smuggle in behaviors from other action classes.
2. **Do not exceed verified knowledge.** Uncertain claims get caveated or omitted. Unknown claims do not appear. Fabricated claims are blocked.
3. **Do not exceed sender authority.** If the sender cannot approve, the message cannot promise approval. If the sender cannot commit resources, the message cannot imply commitment.
4. **One clear move per message.** Prefer a single well-executed action over multiple weak ones. The single-ask rule applies by default.
5. **Fit the channel.** Email has structure. Slack has brevity. Formal letters have ceremony. CRM notes have compactness. The same action class produces different surface text depending on medium.
6. **Escalate rather than fabricate.** If the message cannot be composed safely within constraints, escalate upstream rather than producing something that violates boundaries.
7. **Constraints are inherited, not reinterpreted.** message-os enforces constraints from upstream. It does not re-derive or second-guess them.
8. **Write like a human, not a language model.** Avoid AI-typical vocabulary, structural patterns, and tonal habits. The output should read as if a competent professional wrote it, not as if a chatbot generated it.

## Layer Role in the Stack

See `docs/archive/FOUNDATION.md` for the full layer stack. message-os sits at Layer 4.

message-os is the general-purpose expression engine at Layer 4. GEN-SE is the sales-specific expression engine at Layer 4. They are siblings, not parent-child. Both consume routing decisions. They serve different domains.

## Input Contract

message-os accepts one required input bundle and several optional enrichments.

### Required: Minimum Viable Input

```yaml
message_os_input:
  action_class: NO_ACTION | ACKNOWLEDGE | REQUEST_CLARIFICATION
               | RESPOND | EXECUTE | PROPOSE_NEXT_STEP
               | DEFER | ESCALATE | LOG | CLOSE
  selected_goal: string  # what this message should accomplish
  state_summary: string  # condensed situation context
  key_claims:
    - text: string
      epistemic_status: verified | inferred | assumed | disputed | unknown
  key_constraints:
    - string  # active constraints that affect expression
  medium: email | slack | sms | chat | formal_letter | memo
          | ticket_comment | crm_note
  audience: string  # who receives this message
```

This is enough to compose a basic message. The skill will use safe defaults for anything not provided.

### Full Input Contract

```yaml
message_os_input:
  version: "1.0"

  routing_decision:
    action_class: string
    action_rationale: string
    confidence: 0.0-1.0
    selected_goal: string
    rejected_action_classes:
      - class: string
        reason: string
    risk_flags:
      - string
    urgency: low | medium | high | critical
    reversibility: reversible | semi_reversible | irreversible
    authority_level_required: none | low | medium | high | restricted

  state_object:
    context_id: string
    summary: string
    actors:
      sender:
        role: string
        relationship_to_recipient: string
      recipient:
        role: string
        relationship_to_sender: string
    conversation_state:
      current_topic: string
      open_loops:
        - string
      prior_commitments:
        - string
      pending_questions:
        - string
    requested_outcome: string
    message_trigger: string
    salient_facts:
      - claim_id: string
        text: string
        epistemic_status: verified | inferred | assumed | disputed | unknown
        confidence: 0.0-1.0
    sensitive_content_flags:
      - string

  epistemic_map:
    claims:
      - claim_id: string
        text: string
        status: verified | inferred | assumed | disputed
                | fabricated | unknown
        source_quality: authoritative | direct_evidence | self_reported
                        | secondhand | unsourced
        confidence: 0.0-1.0
        usable_for_assertion: boolean
        usable_with_caveat: boolean
        prohibited_for_assertion: boolean

  constraint_map:
    hard_constraints:
      - id: string
        type: hard_block | authority | legal | policy | privacy
              | resource_cap | timing_window | dependency | epistemic
        description: string
        effect_on_expression: string
    soft_constraints:
      - id: string
        type: tone | brevity | relationship | preference | channel_norm
        description: string
        weight: 1-5
    tradeoffs:
      - between: [string, string]
        resolution_rule: string
    commitment_limits:
      can_commit_to:
        - string
      cannot_commit_to:
        - string
      requires_approval_for:
        - string

  channel_context:
    medium: email | slack | sms | chat | formal_letter | memo
            | ticket_comment | crm_note
    formatting_rules:
      subject_required: boolean
      greeting_required: boolean
      signoff_required: boolean
      bullets_allowed: boolean
      max_length_hint: short | medium | long
    audience_expectation:
      formality: low | medium | high
      speed_priority: low | medium | high
      relationship_temperature: cold | neutral | warm

  user_preferences:
    voice_profile:
      directness: low | medium | high
      warmth: low | medium | high
      verbosity: low | medium | high
      formality: low | medium | high
    style_constraints:
      avoid:
        - string
      prefer:
        - string
    single_ask_rule: boolean  # default true

  optional_context:
    thread_history:
      - speaker: string
        timestamp: string
        text: string
    draft_seed: string  # pre-existing draft to refine
    required_inclusions:
      - string
    required_exclusions:
      - string
    deadline: string
```

### Input Sufficiency Check

If the minimum viable fields (action_class, selected_goal, state_summary, medium, audience) are not present, message-os should:
1. Emit composition failure with reason
2. Return to upstream for missing input
3. Do not attempt to compose from insufficient context

## Process

### Step 1: Lock Action Envelope

Load the routed action class and treat it as the behavioral ceiling for this message.

The action class determines what the message is allowed to do:
- ACKNOWLEDGE: confirm receipt or awareness only
- REQUEST_CLARIFICATION: ask for one missing piece of information
- RESPOND: answer within known bounds
- EXECUTE: confirm action taken or carry out a permitted operational step
- PROPOSE_NEXT_STEP: suggest a concrete next move without overcommitting
- DEFER: explain delay or dependency without fabricating certainty
- ESCALATE: transfer issue upward or sideways with scoped rationale
- LOG: produce a structured record, not a conversational message
- CLOSE: end the loop cleanly
- NO_ACTION: emit null output. Composition halts.

If the action class is NO_ACTION, stop. Do not compose. Return null output.

Verify that the selected_goal is compatible with the action class. If the goal implies behavior outside the action envelope (e.g., goal says "convince them to sign" but action class is ACKNOWLEDGE), flag the mismatch and escalate rather than composing.

### Step 2: Build Allowable Claim Pool

Filter all available claims through epistemic eligibility:

| Epistemic Status | Assertion Rule |
|---|---|
| verified | May state directly as fact |
| inferred | May state with interpretive framing ("Based on X..." / "It appears that...") |
| assumed | State only if necessary for message coherence. Must label as assumption. |
| disputed | Attribute explicitly. Do not endorse. ("There are conflicting accounts...") |
| unknown | Do not assert. Route toward clarification or omit. |
| fabricated | Block. Do not include in any form. Escalate internally if this is the only available support for a required message element. |

Build a claim pool with three categories:
- **Direct-use claims:** verified, usable without caveat
- **Caveated claims:** inferred or assumed, usable with framing
- **Blocked claims:** disputed, unknown, fabricated, not usable for assertion

If the message requires a claim that is blocked, the message cannot make that assertion. Either reframe without it or escalate.

### Step 3: Load Commitment Boundaries

From the constraint map and routing decision, determine:

**What the message may do:**
- commit to (from commitment_limits.can_commit_to)
- assert (from claim pool, direct-use only without caveat)
- request (within single-ask rule)
- suggest (within action envelope)

**What the message may not do:**
- promise anything in cannot_commit_to
- approve anything in requires_approval_for
- assert blocked claims
- imply authority the sender does not have
- imply finality when reversibility is low and approval is missing

**Constraint-to-wording translation:**

| Constraint Type | Effect on Expression |
|---|---|
| Epistemic restriction | Limits what can be asserted. Forces caveats or omission. |
| Authority constraint | Limits what can be promised, approved, or instructed. Forces recommendation/relay framing. |
| Reversibility constraint | Limits finality of wording. Forces conditional language for irreversible actions. |
| Timing constraint | Shapes urgency phrasing and scope. |
| Dependency constraint | Forces conditional framing ("once X is confirmed..."). |
| Relationship constraint | Tunes tone and directness. |
| Policy/legal constraint | Forces precise wording and attribution. |

**Wording shifts by constraint pressure:**

High epistemic uncertainty:
- Prefer: "appears," "based on current information," "I can confirm X but not yet Y"
- Avoid: "definitely," "clearly," "this proves"

Low authority:
- Prefer: "recommend," "flag," "suggest," "can coordinate"
- Avoid: "authorize," "approve," "guarantee"

Dependency present:
- Prefer: "once," "pending," "after," "subject to"
- Avoid: "immediately," "done," "final"

Sensitive relationship:
- Prefer: "wanted to flag," "sharing for awareness"
- Avoid: "you failed," "obviously," "as I said"

### Step 4: Select Message Skeleton

Choose the structural template for the action class and channel combination.

**Universal message structure:**

```yaml
message_structure:
  opening:
    function: orient the recipient
  body_core:
    function: deliver the routed action
  support:
    function: include only necessary evidence or context
  ask_or_next_step:
    function: single ask or single next step if permitted
  close:
    function: end at appropriate commitment level
```

Not all components are required for every action class. See Section: Action Class Templates for mandatory and optional components per class.

### Step 5: Populate Content Slots

Fill the skeleton using the claim pool, commitment boundaries, and state context.

**Rules:**
- Body core must directly execute the action class. No preamble that delays the point.
- Support material is optional and should be minimal. Include only what the recipient needs to understand or act on the core.
- Ask or next step appears only if the action class permits it and the single-ask rule is satisfied.
- Close matches the commitment level. Do not close with finality language when the situation is open.

**Single-ask rule (default: enforced):**

One ask per outbound message unless the action class is LOG or CLOSE (which typically have no ask).

If more than one ask is present:
1. Preserve the highest-priority ask
2. Convert others into future placeholders or remove them
3. If multiple asks are operationally inseparable, bundle under one decision request

Bad: "Can you review this, confirm timing, and send legal approval?"
Good: "Can you confirm whether legal approval is needed? Once that is clear, I can handle timing and review sequencing."

### Step 6: Apply Tone and Register Calibration

Tone is a controlled post-fill pass, not the starting point.

**Calibration dimensions:**

| Dimension | Definition |
|---|---|
| directness | How explicitly the point is stated |
| warmth | How relationally present the language is |
| formality | Degree of professional ceremony |
| confidence_display | How firmly the message states claims |
| deference | How much hierarchy-respect is encoded |

**Default calibration logic:**
- Higher uncertainty lowers confidence display
- Higher legal/policy risk raises precision, lowers warmth
- Slack lowers formality, shortens openings, lightens closure
- Email adds structure, explicit ask/next step
- Formal escalation raises precision, reduces rhetoric, uses traceable claims only
- Warm relationship raises warmth, allows lighter formality

**Domain default profiles:**

| Domain | Directness | Warmth | Formality |
|---|---|---|---|
| internal_ops | high | medium | medium |
| client_service | medium | medium | medium |
| executive_update | high | low | high |
| compliance_legal | high | low | high |
| relationship_maintenance | medium | high | low |

If user voice preferences are provided, they override domain defaults. If user voice is unknown, default to: clear, calm, medium-formality, medium-directness, minimal flourish.

**AI-Pattern Avoidance Rules:**

This pass must also strip AI-typical language patterns. The output should read as if a competent human professional wrote it without AI assistance.

**Banned vocabulary.** Do not use these words in composed messages. They are statistically over-represented in AI-generated text and signal machine authorship:

| Category | Banned Terms |
|---|---|
| Emphasis words | pivotal, crucial, vital, key (as adjective), intricate, meticulous, vibrant, enduring |
| Analysis verbs | delve, underscore, bolster, garner, foster, showcase, highlight (as verb), emphasize (prefer "stress" or rephrase) |
| Abstraction nouns | tapestry, landscape (metaphorical), interplay, testament, intricacies |
| Connectors | additionally (prefer "also" or restructure), furthermore (prefer "and" or restructure) |
| Filler hedges | it's important to note that, it's worth noting that, it should be noted that (just state the thing) |
| Promotional | nestled, rich history, rich cultural heritage, fascinating, remarkable, innovative (unless quoting) |

**Banned structural patterns:**

| Pattern | Description | Fix |
|---|---|---|
| Rule of three | "adjective, adjective, and adjective" or "phrase, phrase, and phrase" used for superficial emphasis | Use one or two descriptors. If three are genuinely needed, restructure. |
| Negative parallelism | "Not just X, but also Y" / "Not X, but Y" as rhetorical framing | State the point directly. |
| Elegant variation | Cycling synonyms for the same subject to avoid repetition (e.g., "the platform," "the solution," "the tool" for the same thing) | Use the same term. Repetition is fine. Clarity beats variety. |
| Copula avoidance | Replacing "is" or "are" with "serves as," "marks," "represents," "features," "offers" | Prefer plain copulatives. "X is Y" is almost always better than "X serves as Y." |
| Present-participle analysis | Trailing "-ing" phrases that add fake depth ("...emphasizing the importance of," "...highlighting the need for," "...showcasing their commitment to") | Cut the trailing phrase. If the point matters, give it its own sentence. |
| Didactic disclaimers | "It's important to note that," "It should be noted that," "It's worth mentioning that" | Delete. State the content directly. |
| Em dash overuse | Using em dashes as default punctuation where commas, periods, or parentheses work | Use commas, periods, or parentheses. Reserve em dashes for genuine interruptions. |

**Tone check:** After applying tone calibration, re-read the draft for any of the above patterns. If present, rewrite the offending sentences before proceeding.

### Step 7: Apply Length Calibration

Compress or expand the draft to fit channel norms.

**Default length targets:**

| Channel | Target |
|---|---|
| slack | 1-5 sentences |
| email (short) | 80-180 words |
| email (standard) | 120-250 words |
| escalation (formal) | 150-300 words |
| log or note | 1-6 bullets or 2-8 lines |
| sms | 1-3 sentences |
| formal_letter | 150-400 words |

**Channel-specific formatting rules:**

**Email:**
- Subject line if initiating or materially updating
- Greeting usually required
- Body structured into 1-4 paragraphs
- Explicit ask or next step near end
- Signoff typically included

**Slack:**
- No subject
- Omit ceremonial greeting unless high-formality channel
- First line should do the work
- Shorter sentences
- One action or acknowledgement
- Optional bullets for clarity

**Formal letter / legal / compliance:**
- Explicit framing
- Verified claims only unless clearly tagged
- No idioms, no soft speculation, no emotional leakage
- Higher traceability

**CRM note / ticket comment:**
- Informational, compact, legible
- Factual and timestamp-friendly
- No social padding unless required

**SMS / chat:**
- Ultra-concise
- No heavy structure
- Core point in first sentence

If the draft exceeds the target range, compress body_core and support first. Do not compress the ask or close.

If the draft falls below the target floor, check whether mandatory components are present. Do not pad with filler.

### Step 8: Run Validation Gates

Post-composition validation runs in this order:

#### Gate 1: Claims Gate

Every factual or commitment-bearing statement must trace to one of:
- A verified claim from the claim pool (direct assertion)
- An allowable inferred claim with caveat (caveated assertion)
- Approved template language
- An explicit unknown/dependency statement

**Fail triggers:**
- Unsupported fact in draft
- Inferred claim presented as verified
- Commitment outside authority scope
- False deadline certainty
- Fabricated rationale

If claims gate fails: rewrite the offending sentences. If the required content cannot be stated safely, escalate.

#### Gate 2: Action Drift Gate

Does the draft still match the routed action class?

**Drift detection tests:**
- ACKNOWLEDGE draft that starts solving the issue: drift
- RESPOND draft that asks three questions: drift
- PROPOSE_NEXT_STEP draft that escalates implicitly: drift
- DEFER draft that promises a timeline not supported by constraints: drift
- ESCALATE draft that assigns blame or makes a compliance determination: drift
- LOG draft that contains persuasive language: drift

If drift detected: strip the drifted content. Re-anchor to the action envelope. If stripping breaks the message, recompose from Step 4.

#### Gate 3: Single-Ask Gate

Count the number of distinct asks, requests, or decision points in the draft.

If count > 1: preserve the priority ask, remove or defer the rest.

Exception: LOG and CLOSE action classes typically have zero asks. If an ask appears in a LOG or CLOSE draft, it is likely drift.

#### Gate 4: Constraint Compliance Gate

Check the draft against all hard constraints from the constraint map:
- Authority: does the message promise anything the sender cannot authorize?
- Legal/policy: does the message make claims that require legal review?
- Privacy: does the message disclose information flagged as sensitive?
- Timing: does the message imply urgency or deadlines not supported by constraints?
- Reversibility: does the message use final language for irreversible actions without required approval?

If any hard constraint is violated: rewrite. If rewrite cannot resolve without changing the action class, escalate upstream.

#### Gate 5: AI-Pattern Gate

Scan the draft for:
- Any word from the banned vocabulary list
- Rule-of-three constructions
- Present-participle analysis phrases
- Didactic disclaimers
- Elegant variation (same referent called by 3+ different names)
- Em dash used more than once in the draft

If any pattern detected: rewrite the offending sentences. This gate should catch what Step 6 missed.

#### Gate 6: Channel Fit Gate

Verify formatting matches the medium:
- Email has subject if required
- Slack is within brevity target
- Formal letter has appropriate ceremony
- CRM note is compact and factual

If mismatch: adjust formatting without changing content.

#### Gate 7: Ambiguity Gate

Check whether the recipient can determine:
- What is being communicated (the core action)
- Who does what next (ownership)
- When (if timing is relevant and known)

If ownership is unclear or the next step is ambiguous, rewrite with explicit actor and trigger.

### Step 9: Finalize or Escalate

If all gates pass: proceed to output.

If gates fail and the issue is wording-level (claim needs caveat, tone needs adjustment, extra ask needs removal, channel format needs fixing): rewrite and re-validate. Maximum two rewrite cycles.

If gates fail and the issue is structural (required content cannot be stated safely, objective conflicts with authority constraints, facts needed are unknown and non-optional, policy/legal risk exceeds allowed messaging scope): escalate upstream. Do not force a message that violates boundaries.

## Action Class Templates

### NO_ACTION

```yaml
no_action:
  output: null
  mandatory_components: []
  optional_components: []
  anti_patterns:
    - sending a courtesy message when none was routed
    - inventing acknowledgement when silence is correct
```

### ACKNOWLEDGE

```yaml
acknowledge:
  mandatory_components:
    - explicit acknowledgement of receipt or awareness
  optional_components:
    - brief thanks if appropriate
    - timing marker if known ("will follow up by X")
  anti_patterns:
    - answering substantive questions
    - adding new asks
    - implying completion or resolution
    - expanding scope beyond receipt confirmation
```

### REQUEST_CLARIFICATION

```yaml
request_clarification:
  mandatory_components:
    - brief context for why clarification is needed
    - single specific question targeting the missing information
  optional_components:
    - why this information matters for next steps
  anti_patterns:
    - asking multiple unrelated questions
    - pretending enough is known to proceed
    - burying the question in explanation
```

### RESPOND

```yaml
respond:
  mandatory_components:
    - direct answer to the explicit ask
  optional_components:
    - supporting fact(s) from verified claim pool
    - uncertainty framing for caveated claims
    - single follow-up ask or next step
  anti_patterns:
    - burying the answer below context
    - asserting unknown claims as facts
    - turning the response into advice or sales pitch
    - answering a question that was not asked
```

### EXECUTE

```yaml
execute:
  mandatory_components:
    - statement of action taken or being taken
    - scope of what was done
  optional_components:
    - result or expected result
    - handoff to next owner
    - timestamp
  anti_patterns:
    - claiming action was completed when it was only initiated
    - implying full completion when partial
    - executing beyond authorized scope
```

### PROPOSE_NEXT_STEP

```yaml
propose_next_step:
  mandatory_components:
    - one concrete proposed next move
  optional_components:
    - current state summary (brief)
    - reason this step makes sense
    - timing suggestion
    - single confirmation ask
  anti_patterns:
    - multiple competing proposals
    - hidden escalation disguised as a suggestion
    - overcommitting before approval
    - proposing steps that depend on unresolved constraints
```

### DEFER

```yaml
defer:
  mandatory_components:
    - statement that action is being held
    - cause of deferment
  optional_components:
    - what will unlock movement
    - next review point or check-in timing (only if authorized to commit)
  anti_patterns:
    - vague delay with no reason
    - false certainty about when deferment ends
    - apologizing excessively for a structurally correct pause
```

### ESCALATE

```yaml
escalate:
  mandatory_components:
    - issue summary (factual)
    - reason escalation is required
    - what decision or review is needed
  optional_components:
    - verified supporting facts
    - risk statement
    - urgency marker
  anti_patterns:
    - emotional accusation
    - unsupported legal or compliance claims
    - declaring a violation (the escalation recipient makes that determination)
    - burying the actual decision needed in background
```

### LOG

```yaml
log:
  mandatory_components:
    - factual event summary
    - current status
  optional_components:
    - timestamp or reference
    - next owner or checkpoint
    - evidence reference
  anti_patterns:
    - persuasive language
    - unlabeled speculation
    - social or relational padding
    - asks or recommendations (LOG records, it does not request)
```

### CLOSE

```yaml
close:
  mandatory_components:
    - explicit closure statement
    - final status
  optional_components:
    - brief appreciation if appropriate
    - reopen condition if applicable
  anti_patterns:
    - reopening new asks in the closing message
    - ambiguous ending that leaves the loop half-open
    - excessive ceremony for a simple closure
```

## Output Contract

```yaml
message_os_output:
  version: "1.0"

  draft_message:
    subject: string | null  # null for channels that do not use subjects
    body: string
    channel_formatting:
      greeting: string | null
      signoff: string | null
      bullets_used: boolean
      markdown_used: boolean

  composition_metadata:
    action_class: string
    template_used: string
    tone_profile_applied:
      directness: low | medium | high
      warmth: low | medium | high
      formality: low | medium | high
    length_profile_applied: string
    included_claim_ids:
      - string
    caveated_claim_ids:
      - string
    omitted_claim_ids:
      - string
    omitted_elements:
      - element: string
        reason: string

  constraint_compliance_report:
    passed: boolean
    checks:
      claims_gate: pass | fail
      action_drift_gate: pass | fail
      single_ask_gate: pass | fail
      constraint_compliance_gate: pass | fail
      ai_pattern_gate: pass | fail
      channel_fit_gate: pass | fail
      ambiguity_gate: pass | fail
    residual_risks:
      - string

  confidence_assessment:
    composition_confidence: high | medium | low
    reasons:
      - string

  handoff_recommendation:
    humanizer_compressor_recommended: boolean
    reason: string | null
```

**Confidence calibration:**
- **high:** All gates passed on first draft. Single viable way to express the action. No competing framings.
- **medium:** One or more gates required rewrite. Or multiple viable framings existed and the skill chose based on defaults rather than explicit user preference.
- **low:** Multiple rewrites needed. Or the message required significant constraint negotiation. Or user voice preferences were unknown and the domain was relationship-sensitive.

## Relationship to GEN-SE

GEN-SE and message-os are sibling Layer 4 skills, not parent-child.

**What message-os shares with GEN-SE:**
- One bounded action per message
- Claims must be source-traceable
- Drift detection after drafting
- Output must fit objective and context
- Structural composition before style polish

**What stays sales-specific in GEN-SE:**
- GRRIPS persuasion logic (G-R-R-I-P-S node structure)
- Objection handling patterns
- Offer positioning and CTA sequencing
- Pipeline stage awareness and commercial framing
- Sales-specific risk gates and drift flags
- Prospect psychology heuristics

**When to use which:**
- message-os: any non-sales professional communication
- GEN-SE: B2B sales email threads where revenue movement, objection handling, or commercial progression is central

## Relationship to humanizer-compressor

message-os produces structurally correct, constraint-compliant, sendable output. It is optimized for correctness first, naturalness second.

humanizer-compressor takes that output and improves readability, naturalness, and voice fit without altering the action class, factual posture, or commitment level.

**Division of labor:**
- message-os owns: correct action expression, structural completeness, epistemic safety, channel fit, commitment discipline, AI-pattern avoidance
- humanizer-compressor owns: voice matching, compression without semantic loss, reducing remaining robotic phrasing, making text sound more like the specific sender

**Handoff contract:**

```yaml
handoff_to_humanizer_compressor:
  input:
    draft_message: string
    locked_elements:
      - action_class
      - approved_claims
      - single_ask
      - commitment_boundaries
      - required_caveats
    style_goal:
      sound_more_human: boolean
      compress_if_possible: boolean
      preserve_meaning: boolean
  rules:
    - may not add new asks
    - may not upgrade certainty of any claim
    - may not change commitment level
    - may not remove required caveats
    - may not alter the action class behavior
```

message-os output should be sendable as-is. humanizer-compressor is a quality-of-life upgrade, not a required step.

## Failure Modes

### 1. Action Drift
Draft stops matching the routed action class. Content introduces behaviors not permitted by the template. Multiple new actions appear.
**Detection:** Compare draft behavior against action class template. Look for asks in ACKNOWLEDGE, answers in REQUEST_CLARIFICATION, escalation cues in RESPOND.
**Fix:** Re-anchor to action envelope. Strip non-permitted content. Recompose from Step 4 if stripping breaks coherence.

### 2. Epistemic Inflation
Inferred or unknown material gets stated as fact. Sentence lacks supporting claim_id or caveat. Certainty language exceeds claim status.
**Detection:** Claims gate. Check every assertion against the claim pool.
**Fix:** Downgrade to caveated language or remove the unsupported claim.

### 3. Authority Overreach
Message promises decisions or actions the sender cannot authorize. Contains approval, guarantee, or commitment verbs outside authority scope.
**Detection:** Constraint compliance gate. Check against commitment_limits.
**Fix:** Convert to recommendation, relay, or conditional language.

### 4. Multi-Ask Sprawl
Message contains more than one decision request or action item for the recipient.
**Detection:** Single-ask gate. Count interrogative clauses and request patterns.
**Fix:** Preserve priority ask. Defer secondary asks to future messages.

### 5. Channel Mismatch
Message format does not fit the medium. Long structured email in Slack. No subject where subject is required. Legal tone in casual chat.
**Detection:** Channel fit gate.
**Fix:** Swap to channel-specific formatting variant.

### 6. Tone Miscalibration
Message is too cold, too soft, too formal, or too blunt for the audience and context.
**Detection:** Compare tone profile against audience_expectation and relationship_temperature.
**Fix:** Run tone adjustment pass using calibrated defaults.

### 7. Ambiguous Ownership
Recipient cannot tell who does what next. Next step lacks actor or timing. Passive language obscures owner.
**Detection:** Ambiguity gate.
**Fix:** Rewrite with explicit owner and trigger condition.

### 8. Unsupported Closure
Message implies the issue is resolved when it is only acknowledged or partially handled. Finality phrases appear without completion evidence.
**Detection:** Action drift gate (CLOSE behavior in non-CLOSE class).
**Fix:** Convert to status framing. Remove finality language.

### 9. Constraint Collision Leakage
Competing constraints are both partially honored but neither fully enforced. Urgent tone plus privacy-sensitive detail in same sentence. High-relationship warmth undermines compliance precision.
**Detection:** Constraint compliance gate cross-check.
**Fix:** Prioritize hard constraints over soft. Split content or reduce scope.

### 10. Overcompression
Message is so short it drops necessary caveats, context, or structural components.
**Detection:** Length gate floor check plus mandatory component audit.
**Fix:** Restore mandatory template components before re-shortening.

### 11. AI-Pattern Contamination
Draft contains AI-typical vocabulary, structural patterns, or tonal habits that signal machine authorship.
**Detection:** AI-pattern gate. Scan for banned vocabulary, rule-of-three, present-participle analysis phrases, didactic disclaimers, elegant variation.
**Fix:** Rewrite offending sentences with plain, direct language.

### 12. Hidden Escalation
Message to a peer implies threat, compliance concern, or hierarchy move that was not routed as ESCALATE. References policy, legal, or leadership without the escalation action class.
**Detection:** Action drift gate. Look for escalation markers in non-ESCALATE drafts.
**Fix:** Remove escalatory cues or flag that the routing decision may need revision.

## Calibration Notes

### Tuning Guidance

- If recipients report messages feel robotic or generic, either tune user_preferences.voice_profile or enable humanizer-compressor as a post-processing step.
- If messages are too long for the channel, tighten length targets. The default ranges are ceilings, not goals.
- If messages violate constraints that were correctly mapped upstream, the fix is in Step 3 (commitment boundary loading), not in the validation gates.
- If the single-ask rule is creating messages that feel incomplete, check whether the upstream routing decision should have been a different action class. The ask rule is a symptom check, not the problem.
- If AI-pattern gate fires frequently, the composition steps are relying on default LLM phrasing. Tighten the tone pass or add specific style_constraints.avoid entries.

### Unknown User Voice

When user voice preferences are not provided:
- Default to clear, calm, medium-formality, medium-directness
- Minimize flourish and stylistic risk
- Favor traceable language over personality
- Do not imitate a specific personality
- Do not insert humor, idioms, or cultural references unless they appear in the thread history

### When to Clarify vs. Use Safe Defaults

Clarify only when:
- Missing information prevents safe composition (no audience, no medium, no goal)
- Recipient identity materially changes tone or authority framing
- Multiple possible asks compete and the routing decision did not resolve them

Otherwise use safe defaults and preserve forward motion. Do not block composition for preference questions.

## Example Transformations

### Example 1: Professional Email RESPOND with Epistemic Constraints

**Input:**
```yaml
action_class: RESPOND
selected_goal: "Answer client question about launch timing without overcommitting"
confidence: 0.86
urgency: medium
reversibility: semi_reversible
authority_level_required: medium

salient_facts:
  - claim_id: c1
    text: "Engineering completed core build."
    epistemic_status: verified
  - claim_id: c2
    text: "QA is expected to finish next week."
    epistemic_status: inferred
    confidence: 0.67
  - claim_id: c3
    text: "Launch approval has not yet been granted."
    epistemic_status: verified

hard_constraints:
  - type: authority
    description: "Sender cannot promise launch date before approval."
    effect_on_expression: "No date commitment."
  - type: epistemic
    description: "QA completion timing is not fully confirmed."
    effect_on_expression: "Must caveat timeline."

soft_constraints:
  - type: relationship
    description: "Client expects responsive, confidence-building communication."
    weight: 4

medium: email
audience: external client
```

**Composition trace:**
1. Lock RESPOND. Goal is compatible: answering a question within known bounds.
2. Claim pool: c1 direct-use, c3 direct-use, c2 caveated only.
3. Authority constraint: cannot promise April 15. Epistemic constraint: QA timeline must be caveated.
4. Email respond template: answer first, supporting facts, caveat, optional next step.
5. Populate: lead with "cannot lock the date yet," explain why (approval pending), add caveated QA status, close with update promise.
6. Tone: medium directness, medium warmth (relationship constraint weight 4), medium formality. AI-pattern check: clean.
7. Length: email short target, 80-180 words.
8. Gates: claims pass (c2 properly caveated), drift pass, single-ask pass (no ask, just an update promise), constraints pass, AI-pattern pass, channel pass, ambiguity pass.

**Output:**
```
Subject: Re: Launch timing

Hi [Client Name],

The core build is complete, but I can't lock the rollout to April 15 yet
because final approval is still pending. Based on current progress, QA
looks on track to wrap next week, though I want that confirmed before
giving you a firm date.

As soon as approval comes through, I'll send you a clean timing update.

Best,
[Name]
```

**composition_confidence:** high
**humanizer_compressor_recommended:** false (output is clean and sendable)

### Example 2: Slack ACKNOWLEDGE of a Team Update

**Input:**
```yaml
action_class: ACKNOWLEDGE
selected_goal: "Acknowledge team update without opening a new workstream"
confidence: 0.97

salient_facts:
  - claim_id: c1
    text: "Migration completed successfully."
    epistemic_status: self_reported
    confidence: 0.84

soft_constraints:
  - type: channel_norm
    description: "Slack acknowledgement should be lightweight."
    weight: 5

medium: slack
audience: internal teammate
```

**Composition trace:**
1. Lock ACKNOWLEDGE. No substantive response permitted.
2. Claim pool: c1 is self-reported. Not asserting it as verified. Acknowledgement does not require claim validation since we are not restating the fact.
3. No commitment boundaries relevant.
4. Slack acknowledge template: receipt confirmation, optional thanks.
5. Populate: confirm awareness, brief thanks.
6. Tone: high directness, medium warmth, low formality (Slack norms). AI-pattern check: clean.
7. Length: 1-2 sentences.
8. Gates: all pass.

**Output:**
```
Got it. Thanks for getting that done.
```

**composition_confidence:** high
**humanizer_compressor_recommended:** false

### Example 3: ESCALATE to Legal on Compliance Issue

**Input:**
```yaml
action_class: ESCALATE
selected_goal: "Escalate possible policy exposure to legal for review"
confidence: 0.91
urgency: high
reversibility: irreversible
authority_level_required: restricted

salient_facts:
  - claim_id: c1
    text: "Draft includes an unapproved guarantee statement."
    epistemic_status: verified
    confidence: 0.96
  - claim_id: c2
    text: "Campaign is scheduled for release tomorrow."
    epistemic_status: verified
    confidence: 0.94
  - claim_id: c3
    text: "This may conflict with internal policy."
    epistemic_status: inferred
    confidence: 0.71

hard_constraints:
  - type: legal
    description: "Do not independently interpret compliance outcome."
    effect_on_expression: "Request review, do not declare violation."
  - type: timing_window
    description: "Release is imminent."
    effect_on_expression: "Mark urgency explicitly."

medium: email
audience: legal team (internal)
formality: high
```

**Composition trace:**
1. Lock ESCALATE. Goal is compatible: transferring issue to appropriate authority.
2. Claim pool: c1 direct-use, c2 direct-use, c3 caveated only (inferred, 0.71).
3. Legal constraint: cannot declare a violation. Only request review. Timing constraint: must mark urgency.
4. Email escalation template: issue summary, escalation reason, verified facts, requested decision.
5. Populate: lead with the issue (unapproved guarantee language), explain urgency (release tomorrow), frame policy concern as possible exposure not declared breach, ask for review and guidance.
6. Tone: high directness, low warmth, high formality. AI-pattern check: verify no "it's important to note" or promotional language.
7. Length: escalation formal, 150-300 words.
8. Gates: claims pass (c3 properly framed as possible exposure), drift pass, single-ask pass (one request: advise whether wording is acceptable), constraints pass (no violation declaration), AI-pattern pass, channel pass, ambiguity pass.

**Output:**
```
Subject: Legal review requested -- customer-facing guarantee language in scheduled campaign

Hi Legal Team,

I am flagging a customer-facing draft for review. The current version includes
an unapproved guarantee statement, and the campaign is scheduled to go live
tomorrow.

I am not making a compliance determination. The language appears close enough
to policy-sensitive territory that I do not want it released without legal
review.

Could you advise whether this wording is acceptable as written, or whether it
needs revision before launch?

Best,
[Name]
```

**composition_confidence:** high
**humanizer_compressor_recommended:** false

### Example 4: PROPOSE_NEXT_STEP After a Meeting

**Input:**
```yaml
action_class: PROPOSE_NEXT_STEP
selected_goal: "Propose one concrete follow-up step after exploratory meeting"
confidence: 0.89

state_object:
  summary: "Meeting ended with interest but several open loops."
  open_loops:
    - "final scope"
    - "owner for implementation"
    - "timeline"
  salient_facts:
    - claim_id: c1
      text: "Both sides want to keep momentum."
      epistemic_status: inferred
      confidence: 0.76
    - claim_id: c2
      text: "Scope is not yet finalized."
      epistemic_status: verified
      confidence: 0.92

hard_constraints:
  - type: dependency
    description: "Timeline depends on scope confirmation."
    effect_on_expression: "Do not propose full timeline yet."

soft_constraints:
  - type: relationship
    description: "Follow-up should feel collaborative, not pushy."
    weight: 4

medium: email
audience: external partner
```

**Composition trace:**
1. Lock PROPOSE_NEXT_STEP. One suggestion, no overcommitment.
2. Claim pool: c1 caveated (inferred), c2 direct-use. c1 is usable as implicit framing ("good talking today" conveys mutual interest without asserting it as fact).
3. Dependency constraint: cannot propose timeline. Must focus on scope first.
4. Email propose template: current state, recommended move, reason, confirmation ask.
5. Populate: reference the meeting, note that scope drives everything else, propose a focused working session on scope, ask if they are open to it.
6. Tone: medium directness, medium-high warmth (relationship weight 4), medium formality. AI-pattern check: clean.
7. Length: email short, 80-180 words.
8. Gates: all pass. Single ask (one proposal). Constraints respected (no timeline commitment).

**Output:**
```
Subject: Next step from today's conversation

Hi [Name],

Good talking today. Since timing and ownership both depend on final scope,
the cleanest next step is to align on scope first and build from there.

Would you be open to a short working session focused on locking the scope?
Once that is clear, the implementation owner and timeline should be
straightforward to pin down.

Best,
[Name]
```

**composition_confidence:** high
**humanizer_compressor_recommended:** false (output is warm enough for the context)

## Anti-Patterns Summary

| Anti-Pattern | What It Looks Like | Why It Breaks |
|---|---|---|
| Action class violation | ACKNOWLEDGE that answers questions | Undermines routing discipline |
| Epistemic inflation | Inferred claim stated as fact | Creates false certainty downstream |
| Authority overreach | Promising what sender cannot authorize | Creates commitments that may need to be walked back |
| Multi-ask sprawl | Three questions in one message | Dilutes recipient attention, creates ambiguous response obligations |
| AI-pattern contamination | "It's important to note that this pivotal development underscores..." | Signals machine authorship, reduces trust |
| Constraint bypass | Final language when approval is pending | Violates upstream safety boundaries |
| Channel mismatch | Email structure in Slack | Wastes recipient time, feels off |
| Vague ownership | "This should be followed up on" | No one acts because no one is named |
| Hidden escalation | Peer message that references policy and leadership | Creates political dynamics the routing decision did not authorize |
| Premature closure | "This is resolved" when it is only acknowledged | Closes loops that are still open |
