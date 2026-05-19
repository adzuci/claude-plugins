---
name: state-extractor
description: >
  Universal Layer 2 parsing skill that converts messy, unstructured input into structured,
  epistemically tagged state objects for downstream reasoning. Use when a user pastes an
  email thread, shares a conversation, uploads meeting notes, provides a document, or asks
  "what's going on here?" Also use when input is multi-actor, temporally ambiguous,
  emotionally charged, or operationally dense and another skill or process needs
  machine-readable state before it can reason, route, decide, or compose.
metadata:
  author: David Johnson-Hall
  version: '1.0'
  layer: 2-cognitive-parsers
  architecture: Apollo GTM Skill Library
---

# State Extractor

Universal parsing skill that converts messy human input into structured, epistemically tagged state objects so downstream systems can reason deterministically.

## Purpose

state-extractor is descriptive, not prescriptive.

It answers:
- What is happening here?
- Who is involved?
- What is known, what is inferred, what is missing?
- What constraints, risks, and open loops are present?

It does not answer:
- What should we do?
- What message should we send?
- Who is right?
- What strategy should we choose?

Core principle: parse ambiguity without pretending to resolve it.

## When to Use This Skill

Use state-extractor whenever downstream logic depends on turning raw text into structured state.

**Best-fit inputs:**
- Email threads
- Slack conversations
- Meeting notes
- Documents and document excerpts
- Chat logs
- CRM notes
- Legal or incident narratives
- Support tickets
- Sales call summaries
- Multi-party written exchanges
- Mixed-context pasted text

**Use when the input is:**
- Messy or fragmented
- Multi-actor
- Temporally ambiguous
- Emotionally charged
- Operationally dense
- Partially missing information
- Feeding another skill downstream

**Typical pipeline:**

```
raw input --> state-extractor --> downstream skill(s)
```

**Downstream consumers include:**
- bounded-action-router
- constraint-first-reasoner
- reality-filter
- message-os
- humanizer-compressor
- Any domain-specific planner, router, or composer

## When NOT to Use This Skill

- Input is already structured (JSON, CSV, database records). No parsing needed.
- The task is pure generation with no input to parse (writing from scratch, brainstorming).
- The user wants advice, strategy, or a draft. This skill produces state, not recommendations. Hand off to a downstream skill for action.
- Input is a single atomic fact or question. No extraction needed. Just answer it.

## Core Principles

1. **Observation before interpretation.** Extract what the text says before deriving what it may mean.
2. **Separate content layers.** Keep facts, reported claims, inferences, unknowns, risks, and action classes distinct. Never blend them.
3. **Preserve ambiguity.** If multiple interpretations are plausible, do not collapse them unless the source resolves them.
4. **Do not hallucinate missing structure.** Not every input will contain all fields. Empty is better than invented.
5. **Prefer atomicity.** Several small precise state entries are better than one blended paragraph.
6. **Preserve actor boundaries.** Do not flatten multiple people into "they."
7. **Preserve temporal boundaries.** Do not mix past events, present state, and future intent.
8. **Preserve source-local meaning.** Quoted text, forwarded content, and summaries may represent different layers of reality.
9. **Label uncertainty early.** Unknown is a valid and preferable output over false certainty.
10. **Downstream usability beats elegant prose.** The result should be machine-usable first. Human-readable second.

## Input Contract

**Required:**
- `raw_input` (string): The unstructured text to parse. Any length, any format.

**Optional:**
- `domain_hint` (string): If the caller knows the domain (sales, legal, operations, etc.), pass it to improve extraction accuracy.
- `schema_mode` (string): `full` (default) or `minimal`. Minimal returns a lighter-weight object for speed.
- `downstream_consumer` (string): Name of the skill that will use this output. Helps prioritize extraction focus.

## Process

### Step 1: Classify Input

Determine:
- `input_type`: email_thread, slack_thread, meeting_notes, document, legal_narrative, crm_note, support_ticket, mixed_paste, unknown
- `domain`: sales, legal, operations, support, hiring, finance, relationships, product, GTM, general, unknown
- Source format, number of actors, whether input is conversational, documentary, narrative, or hybrid

Choose correct parsing expectations without overfitting to any single domain.

### Step 2: Segment Content

Break raw material into meaningful units. Possible units:
- Message or speaker turn
- Paragraph or bullet cluster
- Quoted reply block
- Document section
- Timestamped event
- Note fragment

**Segmentation rules:**
- Preserve order
- Preserve speaker/source attribution when available
- Preserve quoted or forwarded content boundaries
- Distinguish current message from quoted history where possible
- Do not merge unrelated segments just because they are adjacent
- After segmentation, deduplicate: if the same fact, request, or commitment appears in multiple quoted layers (common in email threads), keep only the most recent version unless a later message updates or contradicts an earlier one

### Step 3: Identify Actors and Roles

Extract all identifiable actors. For each, capture:

| Field | Description |
|---|---|
| name | As stated or identifiable |
| role | sender, recipient, decision-maker, approver, customer, vendor, manager, legal party, observer, unknown |
| relationship_context | How they relate to other actors |
| apparent_intent | Conservative. Only assign when sufficiently supported. |
| epistemic_status | explicit, inferred, implied, unknown |
| confidence | high, medium, low |

**Good intent labels:** requests update, seeks approval, expresses concern, resists change, asks for clarification, escalates issue

**Bad intent labels:** manipulative, malicious, lying. These are conclusions, not observations. If the source explicitly alleges such things, capture them under reported claims, not asserted fact.

### Step 4: Extract Explicit Facts

Explicit facts are statements directly supported by the input text.

**Rules:**
- Facts must be text-grounded
- Facts should be atomic where possible
- Avoid bundling several claims into one
- Attach source segment reference when possible
- Prefer concrete over interpretive phrasing

### Step 5: Extract Timeline and Chronology

Build an ordered timeline. For each event:

| Field | Values |
|---|---|
| description | What happened |
| actors_involved | Who was part of it |
| date_or_time | If available |
| temporal_status | past, present, future, unknown |
| event_status | confirmed, reported, disputed, unknown |
| epistemic_status | explicit, inferred, implied, unknown |
| confidence | high, medium, low |

**Rules:**
- Preserve event order even when timestamps are partial
- Distinguish stated dates from inferred sequence
- If chronology is ambiguous, mark it ambiguous
- Separate event occurrence from event reporting. Someone mentioning an event is not proof the event occurred exactly as described.

### Step 6: Extract Requests, Decisions, and Open Loops

**Requests:**
- What is being asked
- By whom, of whom
- Status: open, fulfilled, declined, unclear

**Decisions:**
- What has been decided
- By whom
- Status: final, tentative, disputed, unknown

**Open loops:**
- Unresolved questions
- Missing approvals
- Pending documents
- Unanswered asks
- Unclear ownership
- Deferred actions

This is one of the most important outputs. Downstream planners and routers often depend on unresolved items, not just facts.

### Step 7: Extract Constraints and Dependencies

**Constraints** are conditions that limit valid action space:
- Time deadline
- Legal requirement
- Budget limit
- Policy restriction
- Approval dependency
- Technical dependency
- Relationship sensitivity
- Custody/logistics constraints
- Compliance requirements
- Data availability limits

**Dependencies** are linked conditions:
- Cannot proceed until X
- Requires sign-off from Y
- Blocked by missing document
- Depends on customer response

**Rules:**
- Frame constraints as limits, not advice
- Make dependencies directional where possible

### Step 8: Detect Signals and Risk Factors

**Signals** are structured indicators useful for downstream routing. They are not facts:
- urgency (low, medium, high, unknown)
- emotional_tone (neutral, tense, conflicted, urgent, positive, negative, mixed, unknown)
- conflict_level (low, medium, high, unknown)
- ambiguity_level (low, medium, high, unknown)
- decision_stage (discovery, evaluation, negotiation, pending_approval, execution, post_decision, unknown)

**Risk flags:**
- legal, safety, compliance, operational, relational, reputational, deadline, factual_uncertainty, unknown
- Each with description and confidence

These should not be overclaimed. They are structured warnings, not conclusions.

### Step 9: Epistemic Validation Pass

Epistemic tagging happens inline during Steps 3-8 as each item is extracted. This step is a validation audit: review all tagged items and verify consistency.

**Minimum standard:** explicit, inferred, unknown

**Recommended extended tagging:** See `docs/archive/FOUNDATION.md` for the state-extractor epistemic_status tag set definitions.

**Core rule:** Never present inferred content as explicit fact.

**Confidence is separate from epistemic status.** A claim can be inferred with high confidence or explicit with low reliability in context.

| Pattern | Confidence |
|---|---|
| explicit + concrete + unambiguous | high |
| explicit but vague or context-fragmented | medium |
| inferred from weak cues | low |
| conflicting evidence | low (even if explicit) |
| missing information | unknown or null |

### Step 10: Assemble State Object

Package all extracted data into the output schema. Include `parser_notes` documenting:
- Assumptions made during extraction
- Ambiguities that could not be resolved
- Noise that was intentionally dropped

## Output Contract

### Full Schema

```yaml
state_object:
  schema_name: state_extractor_v1
  input_type: email_thread | slack_thread | meeting_notes | document
              | legal_narrative | crm_note | support_ticket | mixed_paste | unknown
  domain: sales | legal | operations | support | hiring | finance
          | relationships | product | GTM | general | unknown
  source_summary: string
  primary_question_or_problem: string | null

  actors:
    - id: string
      name: string
      role: string | null
      relationship_context: string | null
      apparent_intent: string | null
      epistemic_status: explicit | inferred | implied | unknown
      confidence: high | medium | low

  timeline:
    - event_id: string
      description: string
      actors_involved: [string]
      date_or_time: string | null
      temporal_status: past | present | future | unknown
      event_status: confirmed | reported | disputed | unknown
      epistemic_status: explicit | inferred | implied | unknown
      confidence: high | medium | low

  known_facts:
    - claim: string
      epistemic_status: explicit
      confidence: high | medium | low

  inferred_points:
    - claim: string
      basis: string
      epistemic_status: inferred | implied
      confidence: high | medium | low

  unknowns:
    - field_or_question: string
      reason: string | null

  requests:
    - request: string
      requested_by: string | null
      requested_of: string | null
      status: open | fulfilled | declined | unclear
      epistemic_status: explicit | inferred | implied | unknown
      confidence: high | medium | low

  decisions:
    - decision: string
      decided_by: string | null
      status: final | tentative | disputed | unknown
      epistemic_status: explicit | inferred | implied | unknown
      confidence: high | medium | low

  open_loops:
    - item: string
      owner: string | null
      blocker: string | null
      due_date: string | null
      confidence: high | medium | low

  constraints:
    - constraint: string
      type: time | legal | budget | policy | technical
            | relationship | logistical | unknown
      source_or_basis: string | null
      epistemic_status: explicit | inferred | implied | unknown
      confidence: high | medium | low

  dependencies:
    - dependency: string
      blocks: string | null
      depends_on: string | null
      confidence: high | medium | low

  signals:
    urgency: low | medium | high | unknown
    emotional_tone: neutral | tense | conflicted | urgent
                    | positive | negative | mixed | unknown
    conflict_level: low | medium | high | unknown
    ambiguity_level: low | medium | high | unknown
    decision_stage: discovery | evaluation | negotiation
                    | pending_approval | execution | post_decision | unknown

  risk_flags:
    - type: legal | safety | compliance | operational | relational
            | reputational | deadline | factual_uncertainty | unknown
      description: string
      confidence: high | medium | low

  escalation_flags:
    - flag: string
      reason: string | null
      confidence: high | medium | low

  candidate_action_classes:
    - clarify | respond | escalate | verify | route
      | wait | schedule | review | document | unknown

  parser_notes:
    assumptions:
      - string
    ambiguities:
      - string
    dropped_noise:
      - string
```

### Minimal Schema

For speed or lightweight use when `schema_mode: minimal`:

```yaml
state_object:
  input_type: string
  source_summary: string
  actors: []
  timeline: []
  known_facts: []
  inferred_points: []
  unknowns: []
  requests: []
  decisions: []
  constraints: []
  open_loops: []
  signals: {}
  risk_flags: []
```

Note: requests and decisions are included in minimal mode because open_loops lose actionable context without them. Downstream consumers need to know who asked for what and what has been decided to make open loops useful.

## Input-Type-Specific Handling

### Email Threads
- Detect sender/recipient structure
- Separate current reply from quoted history
- Extract asks, approvals, blockers, next steps
- Detect decision stage
- Identify champions, approvers, stakeholders when possible
- Avoid duplicating facts from repeated quoted material unless an update changes state

### Slack Conversations
- Handle fragmented messages, informal language, reactions, short replies, incomplete grammar
- Focus on active asks, commitments, blockers, decisions, unresolved thread branches
- Watch for urgency and tone shifts
- Mark implied items carefully. Slack often implies context that was never fully stated.

### Meeting Notes
- Handle bullet fragments, shorthand, missing speaker attribution, mixed action items and commentary
- Focus on decisions made, ownership, deadlines, unresolved questions, constraints surfaced
- Do not assume every bullet is a finalized decision

### Documents
- Handle section hierarchy, narrative vs instruction, policy language, mixed descriptive and normative content
- Focus on stated requirements, definitions, timelines, responsibilities, dependencies, formal constraints
- Distinguish what the document requires from what someone later claims it means

### Legal or Incident Narratives
- Chronology matters significantly
- Separate reported vs observed events
- Actors may have conflicting accounts
- Emotional or adversarial language may distort clarity
- Use disputed_event or reported_claim structures when necessary

### Mixed Pasted Input
- Input may include chunks from different sources with broken time order and partial attribution
- First normalize source fragments
- Group by likely source type if possible
- Avoid false unification
- If normalization is weak, document it in parser_notes

## Failure Modes

### 1. Over-interpretation
Assigning motives or conclusions that are not text-grounded.
- Bad: "Manager is trying to sideline employee."
- Better: "Manager excluded employee from the meeting" (fact), then optionally "possible exclusion dynamic" (inferred, low confidence).

### 2. Fact/inference collapse
Blending stated content and interpretation into one claim. Fix: always separate known_facts and inferred_points.

### 3. Chronology flattening
Turning a multi-step sequence into one summary blob. Fix: represent timeline events individually.

### 4. Actor flattening
Collapsing multiple people into "they." Fix: track actors distinctly with individual IDs.

### 5. Quoted-thread duplication
Repeating the same fact multiple times because it appears in nested email quotes. Fix: deduplicate while preserving updates.

### 6. Missing-source certainty inflation
Acting certain when the input is fragmentary. Fix: increase unknowns, lower confidence, add parser_notes.

### 7. Treating allegations as facts
Common in legal, HR, and conflict narratives. Fix: use reported_claim, disputed_event, unknown.

### 8. Mistaking tone for truth
Reading confidence, anger, or polish as evidence of accuracy. Fix: tone informs signals, not facts.

### 9. Producing prose instead of state
Writing a nice summary but not a reusable object. Fix: structured output first. Optional summary only after the state object.

### 10. Premature action selection
Starting to recommend what to do. Fix: output candidate_action_classes at most, and keep them high-level.

### 11. Recency bias
Over-weighting the most recent message in a thread and under-extracting from earlier messages that contain critical context. In a 15-message email thread, the latest reply is not necessarily the most important. Fix: scan the full thread during segmentation. Explicitly check whether earlier messages contain constraints, decisions, or commitments that the latest reply does not repeat.

### 12. Sender authority inflation
Treating messages from people with senior titles or confident tone as more factual than messages from junior participants. Confidence and authority are not the same as accuracy. Fix: treat all claims equally during extraction. Use epistemic tagging to distinguish certainty from authority. Tone informs signals, not facts.

### 13. Schema pressure
When the output schema has many fields, there is pressure to fill them all even when the input does not support it. This is a specific manifestation of Principle #4 but common enough to warrant its own entry. Fix: empty arrays and null values are correct output when the input does not contain relevant data. A 3-message Slack thread should not produce the same field density as a 20-message email chain.

## Calibration Notes

### Relationship to GEN-SE ThreadState

GEN-SE ThreadState is a specialized state model for email-thread decisioning and response generation. state-extractor is the generalized upstream parser.

| Dimension | GEN-SE ThreadState | state-extractor |
|---|---|---|
| Scope | Email workflows only | Any unstructured input |
| Output | Sales-specific fields (lead temp, buying signals, reply obligation) | Domain-agnostic structured state |
| Downstream | Feeds GEN-SE reply engine | Feeds any skill in the library |
| Schema | Fixed to email domain | Adapts to input type |
| Design question | "What is the state of this thread so the system can handle it?" | "What structured state exists so any system can operate on it?" |

**What generalizes well from ThreadState:**
- Actor extraction, chronology extraction, request extraction
- Decision/open-loop mapping, constraint detection
- Uncertainty labeling, signal detection, conflict/escalation markers

**What stays domain-specific:**
- Reply obligation, email action classes, thread progression state
- Message drafting posture, sender-specific response rules, thread ownership logic

**Possible architecture for email inputs:**

```
raw email --> state-extractor --> email-domain adapter --> ThreadState --> GEN-SE
```

### Tuning Guidance

- If downstream skills report weak state, the fix is usually here, not downstream.
- If the parser is producing too many unknowns, the input may genuinely be low-information. Do not compensate by inflating confidence.
- If the parser is producing too few unknowns, it is probably over-interpreting. Audit inferred_points for text grounding.
- The parser should feel conservative. Downstream skills can always ask for more aggressive interpretation. The parser should not volunteer it.

## Example Transformations

### Example 1: Email Thread

**Input:**
```
Sarah: Hey, circling back on pricing. We need something before Friday
because legal wants to review this before quarter-end.

Tom: I think procurement also has to sign off. Not sure if Jill already
looped them in.

Jill: I can send the latest deck. We are still deciding between team
and enterprise.
```

**Output:**
```yaml
state_object:
  schema_name: state_extractor_v1
  input_type: email_thread
  domain: sales
  source_summary: >
    Buyer-side stakeholders are trying to evaluate pricing and complete
    internal review before quarter-end.
  primary_question_or_problem: >
    Pricing and internal approval path are not yet fully resolved.

  actors:
    - id: a1
      name: Sarah
      role: buyer_stakeholder
      relationship_context: internal champion or coordinator
      apparent_intent: obtain pricing for review
      epistemic_status: inferred
      confidence: medium
    - id: a2
      name: Tom
      role: stakeholder
      relationship_context: procurement-aware participant
      apparent_intent: surface approval dependency
      epistemic_status: inferred
      confidence: medium
    - id: a3
      name: Jill
      role: stakeholder
      relationship_context: internal coordinator
      apparent_intent: provide deck and continue evaluation
      epistemic_status: explicit
      confidence: high

  timeline:
    - event_id: e1
      description: Pricing requested before Friday
      actors_involved: [a1]
      date_or_time: "before Friday"
      temporal_status: future
      event_status: confirmed
      epistemic_status: explicit
      confidence: high
    - event_id: e2
      description: Legal review needed before quarter-end
      actors_involved: [a1]
      date_or_time: "before quarter-end"
      temporal_status: future
      event_status: confirmed
      epistemic_status: explicit
      confidence: high
    - event_id: e3
      description: Procurement sign-off may be required
      actors_involved: [a2]
      date_or_time: null
      temporal_status: unknown
      event_status: reported
      epistemic_status: inferred
      confidence: medium

  known_facts:
    - claim: Pricing is being requested
      epistemic_status: explicit
      confidence: high
    - claim: Legal review is required before quarter-end
      epistemic_status: explicit
      confidence: high
    - claim: Team and enterprise options are both under consideration
      epistemic_status: explicit
      confidence: high

  inferred_points:
    - claim: Sarah may be acting as internal champion
      basis: She is driving follow-up and coordinating timing
      epistemic_status: inferred
      confidence: medium

  unknowns:
    - field_or_question: Whether procurement sign-off is actually required
      reason: Tom states uncertainty
    - field_or_question: Whether Jill already looped in procurement
      reason: Not confirmed
    - field_or_question: Final package selection (team vs enterprise)
      reason: Still deciding

  open_loops:
    - item: Provide pricing
      owner: unknown
      blocker: none stated
      due_date: before Friday
      confidence: high
    - item: Confirm procurement process
      owner: unknown
      blocker: unclear ownership
      due_date: null
      confidence: medium

  constraints:
    - constraint: Legal review must occur before quarter-end
      type: time
      source_or_basis: Sarah message
      epistemic_status: explicit
      confidence: high

  dependencies:
    - dependency: Purchase path may depend on procurement sign-off
      blocks: deal progression
      depends_on: procurement review
      confidence: medium

  signals:
    urgency: high
    emotional_tone: neutral
    conflict_level: low
    ambiguity_level: medium
    decision_stage: evaluation

  risk_flags:
    - type: deadline
      description: Internal review timeline may create delay risk
      confidence: high
    - type: factual_uncertainty
      description: Approval path not fully confirmed
      confidence: medium

  candidate_action_classes:
    - clarify
    - respond
    - verify

  parser_notes:
    assumptions:
      - Sarah is buyer-side based on her coordinating behavior
    ambiguities:
      - Procurement involvement is uncertain
    dropped_noise: []
```

### Example 2: Slack Thread

**Input:**
```
alex: can someone confirm if launch is still monday
maria: only if eng fixes the auth issue today
devin: legal still hasn't approved the updated copy btw
alex: okay so definitely not locked then
```

**Output:**
```yaml
state_object:
  schema_name: state_extractor_v1
  input_type: slack_thread
  domain: operations
  source_summary: >
    Launch timing remains uncertain due to engineering and legal blockers.
  primary_question_or_problem: Monday launch is not locked.

  actors:
    - id: a1
      name: Alex
      role: coordinator
      apparent_intent: confirm launch readiness
      epistemic_status: inferred
      confidence: medium
    - id: a2
      name: Maria
      role: engineering liaison
      apparent_intent: surface technical blocker
      epistemic_status: inferred
      confidence: medium
    - id: a3
      name: Devin
      role: stakeholder
      apparent_intent: surface legal blocker
      epistemic_status: explicit
      confidence: high

  known_facts:
    - claim: Monday launch timing was questioned
      epistemic_status: explicit
      confidence: high
    - claim: Auth issue must be fixed today for Monday launch
      epistemic_status: explicit
      confidence: high
    - claim: Legal has not approved updated copy
      epistemic_status: explicit
      confidence: high

  inferred_points:
    - claim: Launch readiness is at risk
      basis: Two blockers remain unresolved
      epistemic_status: inferred
      confidence: high

  constraints:
    - constraint: Engineering auth fix must happen today
      type: technical
      source_or_basis: Maria message
      epistemic_status: explicit
      confidence: high
    - constraint: Legal approval on updated copy is pending
      type: legal
      source_or_basis: Devin message
      epistemic_status: explicit
      confidence: high

  open_loops:
    - item: Resolve auth issue
      owner: engineering
      blocker: unresolved bug
      due_date: today
      confidence: medium
    - item: Obtain legal approval on updated copy
      owner: legal
      blocker: approval pending
      due_date: null
      confidence: high

  signals:
    urgency: high
    emotional_tone: tense
    conflict_level: low
    ambiguity_level: medium
    decision_stage: pending_approval

  candidate_action_classes:
    - clarify
    - verify
    - wait

  parser_notes:
    assumptions:
      - Alex is a coordinator based on asking the status question
    ambiguities:
      - Whether auth issue and legal approval are related blockers or independent
    dropped_noise: []
```

### Example 3: Conflicting Accounts (Legal/HR Narrative)

**Input:**
```
From: Rachel (HR)
To: Outside Counsel

Here is the summary you requested.

On March 3, James reported to me that his manager Dan made comments about
his age during a team meeting on Feb 28. James says Dan said "we need
younger energy on this team" in front of 4 colleagues.

I spoke with Dan on March 5. Dan denies making the comment. He says he
said "we need fresh energy" and that James misheard him. Dan also noted
that James received a positive performance review in January.

I interviewed two attendees. One (Lisa) confirms hearing "younger energy."
The other (Mark) says he doesn't remember the exact words but recalls
Dan talking about team composition.

James filed a formal complaint on March 7. He is requesting a transfer
to another team. Dan's position is that no discriminatory comment was made.
```

**Output:**
```yaml
state_object:
  schema_name: state_extractor_v1
  input_type: email_thread
  domain: legal
  source_summary: >
    HR summary of an age discrimination complaint with conflicting
    accounts from the complainant, the accused manager, and two witnesses.
  primary_question_or_problem: >
    Whether a discriminatory comment was made during a Feb 28 team meeting.

  actors:
    - id: a1
      name: Rachel
      role: HR representative
      relationship_context: investigator, author of summary
      apparent_intent: provide factual summary to counsel
      epistemic_status: explicit
      confidence: high
    - id: a2
      name: James
      role: complainant
      relationship_context: reports to Dan
      apparent_intent: report discrimination, request transfer
      epistemic_status: explicit
      confidence: high
    - id: a3
      name: Dan
      role: accused manager
      relationship_context: James's manager
      apparent_intent: deny allegation
      epistemic_status: explicit
      confidence: high
    - id: a4
      name: Lisa
      role: witness
      relationship_context: meeting attendee
      apparent_intent: provide account
      epistemic_status: explicit
      confidence: high
    - id: a5
      name: Mark
      role: witness
      relationship_context: meeting attendee
      apparent_intent: provide account
      epistemic_status: explicit
      confidence: high

  timeline:
    - event_id: e1
      description: James received positive performance review
      actors_involved: [a2, a3]
      date_or_time: January (exact date unknown)
      temporal_status: past
      event_status: reported
      epistemic_status: explicit
      confidence: medium
    - event_id: e2
      description: Team meeting where disputed comment occurred
      actors_involved: [a2, a3, a4, a5]
      date_or_time: "Feb 28"
      temporal_status: past
      event_status: confirmed
      epistemic_status: explicit
      confidence: high
    - event_id: e3
      description: James reported incident to HR
      actors_involved: [a2, a1]
      date_or_time: "March 3"
      temporal_status: past
      event_status: confirmed
      epistemic_status: explicit
      confidence: high
    - event_id: e4
      description: Rachel interviewed Dan
      actors_involved: [a1, a3]
      date_or_time: "March 5"
      temporal_status: past
      event_status: confirmed
      epistemic_status: explicit
      confidence: high
    - event_id: e5
      description: James filed formal complaint
      actors_involved: [a2]
      date_or_time: "March 7"
      temporal_status: past
      event_status: confirmed
      epistemic_status: explicit
      confidence: high

  known_facts:
    - claim: A team meeting occurred on Feb 28
      epistemic_status: explicit
      confidence: high
    - claim: James reported the incident to HR on March 3
      epistemic_status: explicit
      confidence: high
    - claim: Dan was interviewed by HR on March 5
      epistemic_status: explicit
      confidence: high
    - claim: James filed a formal complaint on March 7
      epistemic_status: explicit
      confidence: high
    - claim: James is requesting a transfer
      epistemic_status: explicit
      confidence: high
    - claim: James received a positive performance review in January
      epistemic_status: explicit
      confidence: medium

  inferred_points:
    - claim: The exact wording of Dan's comment is disputed and unresolvable from this input alone
      basis: James says "younger energy," Dan says "fresh energy," Lisa corroborates James, Mark is uncertain
      epistemic_status: inferred
      confidence: high
    - claim: There is at least partial witness corroboration of James's account
      basis: Lisa confirms hearing "younger energy"
      epistemic_status: inferred
      confidence: medium

  unknowns:
    - field_or_question: Exact words Dan used during the meeting
      reason: Conflicting accounts between James and Dan
    - field_or_question: Whether other attendees (beyond Lisa and Mark) were interviewed
      reason: Rachel mentions 4 colleagues present but only 2 interviewed
    - field_or_question: Dan's intent behind the comment regardless of exact wording
      reason: Cannot be determined from text

  requests:
    - request: James requests transfer to another team
      requested_by: a2
      requested_of: HR / management
      status: open
      epistemic_status: explicit
      confidence: high

  decisions:
    - decision: No resolution decision documented yet
      decided_by: null
      status: unknown
      epistemic_status: missing
      confidence: high

  open_loops:
    - item: Formal complaint resolution
      owner: HR / outside counsel
      blocker: investigation ongoing
      due_date: null
      confidence: high
    - item: Transfer request disposition
      owner: HR / management
      blocker: pending complaint resolution
      due_date: null
      confidence: medium
    - item: 2 additional meeting attendees not yet interviewed
      owner: Rachel / HR
      blocker: none stated
      due_date: null
      confidence: medium

  constraints:
    - constraint: Formal complaint has been filed, creating legal documentation trail
      type: legal
      source_or_basis: Rachel's summary
      epistemic_status: explicit
      confidence: high

  dependencies:
    - dependency: Transfer request likely depends on complaint resolution
      blocks: James's transfer
      depends_on: investigation outcome
      confidence: medium

  signals:
    urgency: high
    emotional_tone: conflicted
    conflict_level: high
    ambiguity_level: high
    decision_stage: evaluation

  risk_flags:
    - type: legal
      description: Age discrimination allegation with partial witness corroboration
      confidence: high
    - type: relational
      description: Manager-report relationship is adversarial
      confidence: high
    - type: factual_uncertainty
      description: Core disputed fact (exact wording) cannot be resolved from available evidence
      confidence: high

  escalation_flags:
    - flag: Outside counsel already involved
      reason: Rachel is writing to outside counsel
      confidence: high
    - flag: Formal complaint filed
      reason: Moves from informal to documented process
      confidence: high

  candidate_action_classes:
    - verify
    - document
    - escalate
    - review

  parser_notes:
    assumptions:
      - Rachel's summary is taken at face value as an HR professional's account
      - "4 colleagues" includes Lisa and Mark plus 2 unidentified attendees
    ambiguities:
      - Exact wording of Dan's comment is the central disputed fact
      - Mark's account is ambiguous and does not clearly support either version
      - Performance review mention by Dan may be contextual defense or relevant fact
    dropped_noise: []
```

### Example 4: Meeting Notes

**Input:**
```
pricing too high for smb
maybe test annual discount
john to check margin impact
enterprise team wants security one-pager
legal review next week?
no decision yet
```

**Output:**
```yaml
state_object:
  schema_name: state_extractor_v1
  input_type: meeting_notes
  domain: GTM
  source_summary: >
    Team discussed pricing concerns, a possible discount experiment,
    margin review, and enterprise collateral needs. No final decision made.
  primary_question_or_problem: Pricing and supporting materials unresolved.

  actors:
    - id: a1
      name: John
      role: unknown
      apparent_intent: assigned to check margin impact
      epistemic_status: explicit
      confidence: high

  known_facts:
    - claim: SMB pricing concern was raised
      epistemic_status: explicit
      confidence: medium
    - claim: John is expected to check margin impact
      epistemic_status: explicit
      confidence: high
    - claim: Enterprise team wants a security one-pager
      epistemic_status: explicit
      confidence: high
    - claim: No decision has been made yet
      epistemic_status: explicit
      confidence: high

  inferred_points:
    - claim: Annual discount is under consideration as an experiment
      basis: "maybe test annual discount"
      epistemic_status: implied
      confidence: medium

  unknowns:
    - field_or_question: Whether legal review is scheduled for next week
      reason: Phrased as a question in the notes
    - field_or_question: Final pricing decision
      reason: Explicitly unresolved

  open_loops:
    - item: John checks margin impact
      owner: John
      blocker: none stated
      due_date: null
      confidence: high
    - item: Create enterprise security one-pager
      owner: unknown
      blocker: unclear owner
      due_date: null
      confidence: medium
    - item: Confirm legal review timing
      owner: unknown
      blocker: not yet scheduled
      due_date: possibly next week
      confidence: low

  signals:
    urgency: medium
    emotional_tone: neutral
    conflict_level: low
    ambiguity_level: high
    decision_stage: evaluation

  candidate_action_classes:
    - clarify
    - review
    - document

  parser_notes:
    assumptions:
      - Notes are from a single meeting
      - Bullets are separate discussion items, not a connected narrative
    ambiguities:
      - No speaker attribution for most items
      - Legal review phrased as question, not confirmed action
    dropped_noise: []
```
