Internal Directory
GEN-SE (Generic Sales Engine) Master Architecture
Version: 1.0
Status: Foundation Complete
Purpose: Canonical reference for the inbound → close "Next Safe Email" engine. This document
defines system structure, module relationships, execution flow, and audit framework.
Part I: System Overview
1. What This System Is
GENSE is a stateless, metadata-driven email response engine that:
 Ingests an email thread
 Extracts structured state
 Classifies deal stage and buyer intent
 Selects the safest next action from a bounded set
 Generates a GRRIPS-compliant message
 Returns the message + updated state row
The system never improvises. Every decision is:
Driven by explicit state fields
Routed through enumerated actions
Validated against safety constraints
Logged for audit replay
2. Design Principles (Load-Bearing Invariants)
These principles are inherited from the proven outbound ForgeSales architecture and must not be
violated in any implementation.
Principle Meaning Enforcement
No persistent memory; external store is source of
Stateless execution State passed in/out every turn
truth
Validation gates before
Fail-safe behavior Never guess; fail explicitly if data missing
generation
Internal Directory 1

Principle Meaning Enforcement
Bounded action Command Tree with
Finite enumerated actions only
space preconditions
Two-part output Every response = message + updated state row Output validation requires both
One CTA or one question per message, never
Single ask rule Global constraint on all actions
both
Priority lock on progression
Open loops first Must resolve buyer questions before advancing
actions
Drift governance Continuous monitoring for degradation patterns Drift flags trigger repair routing
Audit trail Every decision reconstructable from logs Decision trace in output package
3. System Boundary
In Scope
Email thread → next safe response
State extraction and classification
Action selection and message generation
Drift detection and repair routing
Out of Scope
Email sending/receiving (handled by integration layer)
CRM sync (handled by external automation)
Meeting scheduling (handled by calendar tools)
Human escalation workflow (handled by ticketing system)
Part II: Module Architecture
4. Module Map
┌─────────────────────────────────────────────────────────────
────────┐
│ GENSE System │
├─────────────────────────────────────────────────────────────
────────┤
│ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│ │ INGEST │───▶│ EXTRACT │───▶│ CLASSIFY │ │
Internal Directory 2

│ │ │ │ │ │ │ │
│ │ Thread │ │ Thread State │ │ Deal Stage + │ │
│ │ Ingestion │ │ Schema │ │ Intent Classifier │ │
│ └──────────────┘ └──────────────┘ └──────────────────────┘ │
│ │ │
│ ▼ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│ │ OUTPUT │◀───│ GENERATE │◀───│ ROUTE │ │
│ │ │ │ │ │ │ │
│ │ Message + │ │ Message OS │ │ Policy Engine + │ │
│ │ State Row │ │ GRRIPS │ │ Action Set │ │
│ └──────────────┘ └──────────────┘ └──────────────────────┘ │
│ │ │ │ │
│ │ ▼ │ │
│ │ ┌──────────────┐ │ │
│ │ │ VALIDATE │◀─────────────┘ │
│ │ │ │ │
│ │ │ Claims + │ │
│ │ │ Drift Monitor│ │
│ │ └──────────────┘ │
│ │ │ │
│ │ ▼ │
│ │ ┌──────────────┐ │
│ └────────────│ REPAIR │ │
│ │ │ │
│ │ Repair Stack │ │
│ └──────────────┘ │
│ │
├─────────────────────────────────────────────────────────────
────────┤
│ REFERENCE MODULES Lookup, not execution) │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────
─┐ │
│ │ Core │ │ Enablement │ │ Industry │ │ Buyer Role │ │
│ │ Identity │ │ Asset │ │ Packs │ │ Profiles │ │
│ │ │ │ Library │ │ │ │ │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────
─┘ │
└─────────────────────────────────────────────────────────────
────────┘
5. Module Specifications Index
Internal Directory 3

# Module PDF Name Status Purpose
System posture,
1 Core Identity GENSE_Core_Identity_Boundaries.pdf Stub constraints, non-
negotiables
Parse raw email
Thread GEN
2 Stub into structured
Ingestion SE_Thread_Ingestion_Normalization.pdf
turns
Thread State Canonical state
3 GENSE_Thread_State_Schema.pdf Complete
Schema representation
Deal Stage GEN Stage + intent
4 Stub
Classifier SE_Deal_Stage_Intent_Classifier.pdf detection rules
24 enumerated
GEN
5 Action Set Complete actions with
SE_Action_Set_Command_Tree.pdf
pre/postconditions
GEN Routing logic:
6 Policy Engine Skeleton
SE_Next_Safe_Action_Policy_Engine.pdf state → action
Message
7 Message OS GENSE_Message_OS_GRRIPS.pdf Stub
construction rules
Grounding rules
8 Claims Policy GENSE_Claims_Evidence_Policy.pdf Stub
for assertions
GEN Degradation
9 Drift Monitor Stub
SE_Drift_Monitor_Repair_Stack.pdf detection + repair
Enablement GEN Controlled artifact
10 Stub
Assets SE_Enablement_Asset_Library.pdf whitelist
Vertical
11 Industry Packs GENSE_Industry_Pack_Format.pdf Stub customization
format
Role-based
12 Buyer Profiles GENSE_Buyer_Role_Profiles.pdf Stub behavior
modulation
GEN How to audit the
13 Audit Guide Stub
SE_System_Trace_Audit_Guide.pdf system
Part III: Execution Flow
6. End-to-End Execution Chain
INPUT PROCESS OUTPUT
───── ─────── ──────
Internal Directory 4

┌─────────────────┐
│ Raw Email │
│ Thread │
│ (scrape/forward)│
└────────┬────────┘
│
▼
┌─────────────────┐ ┌─────────────────────────────────┐
│ Thread │────▶│ 1. NORMALIZE │
│ Ingestion │ │  Split into turns │
│ Spec │ │  Attribute speakers │
│ │ │  Strip signatures/footers │
│ │ │  Identify latest buyer turn │
│ │ │  Confidence gate 0.7 │
└─────────────────┘ └─────────────────────────────────┘
│
▼ FAIL if confidence < threshold
│
┌─────────────────┐ ┌─────────────────────────────────┐
│ Thread State │◀────│ 2. EXTRACT STATE │
│ Schema │ │  Populate thread_core │
│ │ │  Populate current_state │
│ │ │  Build stakeholder array │
│ │ │  Detect open loops │
│ │ │  Track commitments │
└─────────────────┘ └─────────────────────────────────┘
│
▼
┌─────────────────┐ ┌─────────────────────────────────┐
│ Deal Stage + │────▶│ 3. CLASSIFY │
│ Intent │ │  Map to deal_stage enum │
│ Classifier │ │  Detect buyer_intent │
│ │ │  Calculate confidence │
│ │ │  Apply risk_factors │
└─────────────────┘ └─────────────────────────────────┘
│
▼ FAIL if confidence < threshold
│
┌─────────────────┐ ┌─────────────────────────────────┐
│ Policy Engine │────▶│ 4. ROUTE │
│  Action Set │ │  Evaluate global constraints│
│ │ │  Check preconditions │
Internal Directory 5

│ │ │  Select action 124 │
│ │ │  Log decision trace │
└─────────────────┘ └─────────────────────────────────┘
│
▼ ESCALATE if no action valid
│
┌─────────────────┐ ┌─────────────────────────────────┐
│ Message OS │────▶│ 5. GENERATE │
│ GRRIPS │ │  Construct via GRRIPS arc │
│ │ │  Apply action constraints │
│ │ │  Enforce single ask rule │
│ │ │  Check word/line limits │
└─────────────────┘ └─────────────────────────────────┘
│
▼
┌─────────────────┐ ┌─────────────────────────────────┐
│ Claims Policy │────▶│ 6. VALIDATE CLAIMS │
│ │ │  Every claim has source │
│ │ │  Hedge if uncertain │
│ │ │  Reject invented facts │
└─────────────────┘ └─────────────────────────────────┘
│
▼ REPAIR if claim fails
│
┌─────────────────┐ ┌─────────────────────────────────┐
│ Drift Monitor │────▶│ 7. CHECK DRIFT │
│ │ │  CTA repetition │
│ │ │  Open loop ignored │
│ │ │  Tone mismatch │
│ │ │  Over-answering │
└─────────────────┘ └─────────────────────────────────┘
│
▼ REPAIR if drift detected
│
┌─────────────────┐ ┌─────────────────────────────────┐
│ Repair Stack │────▶│ 8. REPAIR (if needed) │
│ │ │  Re-route to safe action │
│ │ │  Regenerate message │
│ │ │  Log repair reason │
└─────────────────┘ └─────────────────────────────────┘
│
▼
Internal Directory 6

┌─────────────────────────────────┐
│ 9. APPLY POSTCONDITIONS │
│  Update state fields │
│  Resolve/create open loops │
│  Log commitments │
│  Increment turn counters │
└─────────────────────────────────┘
│
▼
┌─────────────────────────────────┐
│ 10. EMIT OUTPUT PACKAGE │
│  Draft text │
│  Updated thread_state │
│  Decision trace │
│  Audit log entry │
└─────────────────────────────────┘
│
▼
┌─────────────────┐
│ OUTPUT │
│ Message + │
│ State Row + │
│ Trace │
└─────────────────┘
7. Failure Modes & Handling
Failure Point Trigger System Response
Ingestion Speaker attribution  0.7 confidence Return execution_status: blocked, escalate to human
Ingestion Latest actionable turn ambiguous Return top-2 candidates for human selection
Classification Stage confidence  0.6 Action 1 escalate_to_human_review
Classification Intent confidence  0.6 Action 1 escalate_to_human_review
Routing No action preconditions satisfied Action 1 escalate_to_human_review
Routing Missing required config Action 2 request_missing_context
Generation Claims grounding fails Repair: hedge or remove claim
Validation Drift flag triggered Repair: re-route to corrective action
Validation Output validation fails Do not emit; log error; escalate
Part IV: Data Schemas (Summary)
Internal Directory 7

8. Thread State Schema (Reference: Full Spec)
8.1 Three-Tier Structure
THREAD STATE
├── Thread Core (immutable)
│ ├── thread_id
│ ├── thread_created_at
│ ├── source_channel
│ ├── account_id / account_tier
│ ├── vertical
│ ├── product_context
│ └── seller_assigned
│
├── Current State (mutable per-turn)
│ ├── Stage & Intent
│ │ ├── deal_stage (enum)
│ │ ├── buyer_intent (enum)
│ │ └── confidence scores
│ │
│ ├── Open Loops
│ │ ├── open_loops[] (array of loop objects)
│ │ ├── open_loop_count
│ │ └── oldest_open_loop_age
│ │
│ ├── Commitments
│ │ ├── commitments_made[]
│ │ ├── commitments_received[]
│ │ └── commitment_drift_flag
│ │
│ ├── Risk & Friction
│ │ ├── risk_level (enum)
│ │ ├── risk_factors[]
│ │ ├── objection_tags[]
│ │ └── friction_pattern (enum)
│ │
│ ├── Interaction History
│ │ ├── total_turns / seller_turns / buyer_turns
│ │ ├── last_seller_action / last_seller_cta
│ │ ├── timestamps
│ │ └── response_velocity_avg
│ │
Internal Directory 8

│ ├── GRRIPS Execution State
│ │ ├── last_grrips_node
│ │ ├── grrips_failure_tag
│ │ └── repair_node
│ │
│ └── Action History
│ ├── last_3_actions[]
│ ├── last_3_ctas[]
│ ├── cta_repeat_flag
│ └── action_diversity_score
│
└── Stakeholder Array (per-participant)
├── stakeholder_id / email / name
├── role_detected / role_confidence
├── sentiment_current / sentiment_trend
├── open_loops_owned[]
├── objections_raised[]
├── pressure_tolerance
└── is_primary_contact / is_blocker
8.2 Key Enumerations
Deal Stage:
triage → discovery → evaluation → proposal → procurement → negotiation → closed_won/clo
sed_lost
Buyer Intent:
question_product | question_pricing | question_process | question_technical | question_securi
ty | question_reference
objection_timing | objection_budget | objection_authority | objection_need | objection_competi
tion
commitment_signal | commitment_request | information_share | administrative | unclear
Risk Level:
low → medium → high → critical
Open Loop Type:
explicit_question | implicit_concern | process_blocker | vague_signal
Internal Directory 9

9. Action Set (Reference: Full Spec)
9.1 Action Categories
Category Actions Purpose
A. Control 12 System halt/escalation
B. Open Loop Resolution 38 Answer buyer questions
C. Commitment Integrity 911 Maintain trust
D. Discovery & Alignment 1215 Qualify and expand
E. Progression 1620 Advance deal
F. Objection & Competition 2122 Reduce friction
G. Stall & Closure 2324 Handle non-response
9.2 Action List (Quick Reference)
CONTROL
1. escalate_to_human_review
2. request_missing_context
OPEN LOOP RESOLUTION
3. answer_explicit_question_only
4. answer_question_plus_one_clarifier
5. defer_answer_request_owner
6. provide_requested_artifact
7. request_info_to_prepare_artifact
8. resolve_process_blocker
COMMITMENT INTEGRITY
9. confirm_commitment_delivery_time
10. recover_missed_commitment
11. confirm_buyer_commitment
DISCOVERY & ALIGNMENT
12. single_discovery_probe
13. stakeholder_expand
14. stakeholder_redirect_acknowledge_cc
15. timeline_alignment_probe
PROGRESSION
16. offer_async_next_step_options
17. propose_call_two_time_windows
Internal Directory 10

18. confirm_next_step_and_owner
19. send_proposal_or_pricing_frame
20. procurement_enablement_packet
OBJECTION & COMPETITION
21. objection_reframe_reduce_risk
22. competition_comparison_neutral
STALL & CLOSURE
23. nudge_open_loop_opt_out
24. close_thread_graceful
9.3 Global Constraints
IF open_loops.any(priority == "high")
 ONLY actions 311 allowed (no progression)
IF commitment_drift_flag == true
 ONLY action 10 allowed (must recover)
FOR ALL actions:
 Max 1 CTA OR 1 question (never both)
 All claims must be grounded
 No CTA repetition (same CTA twice blocked)
Part V: Module Stubs (To Be Completed)
10. Core Identity & Boundaries
Purpose: Define what the system is, what it may do, and what it must never do.
10.1 System Identity
I am GENSE, a Next Safe Email engine for inbound sales threads.
I help sales teams respond to prospects in a way that:
 Answers their questions first
 Maintains commitments made
 Advances deals at appropriate pace
Internal Directory 11

 Never pressures or manipulates
 Never invents facts
10.2 Hard Constraints
Constraint Rule
Every factual claim must source from thread content, product config, or approved
No invented facts
assets
No pushy CTAs Never guilt, create artificial urgency, or pressure
Answer first If buyer asked a question, answer before any new CTA
One ask maximum Single CTA or single question per message
Respect process Never skip or rush buyer's stated requirements
Acknowledge
If commitment missed, own it without excuses
mistakes
Professional exit Close threads gracefully without burning bridges
10.3 Voice Constraints
 Conversational, not corporate
 Concise (typically 50150 words unless depth required)
 No jargon unless buyer uses it first
 No exclamation points unless matching buyer's energy
 No "just following up" / "circling back" / "touching base"
 No "I hope this email finds you well"
10.4 Tone Calibration by Risk Level
Risk Level Tone Adjustment
Low Warm, forward-leaning, can propose next steps
Medium Helpful, patient, ask before assuming
High Careful, low-pressure, offer opt-outs
Critical Minimal, apologetic if warranted, preserve relationship
11. Thread Ingestion & Normalization
Purpose: Parse raw email thread into structured turns with speaker attribution.
11.1 Input Format
Internal Directory 12

Raw email thread (forwarded or scraped)
 May contain quoted reply chains
 May have multiple participants
 May include signatures, disclaimers, auto-replies
11.2 Output Format
{
"turns": [
{
"turn_number" 1,
"speaker_email": "buyer@company.com",
"speaker_name": "Jane Doe",
"speaker_role": "buyer",
"timestamp": "20250115T093000Z",
"content": "...",
"content_type": "original"
},
...
],
"participants": [
{"email": "...", "name": "...", "role": "buyer|seller|unknown"}
],
"latest_buyer_turn" 5,
"latest_buyer_content": "...",
"attribution_confidence" 0.92,
"parsing_warnings": []
}
11.3 Normalization Rules
 Quote stripping: Remove > prefixed lines and "On [date], [person] wrote:" headers
 Signature removal: Strip content after common signature markers (-, Best,, etc.)
 Footer removal: Remove legal disclaimers, confidentiality notices
 Turn splitting: Each distinct message becomes a turn
 Speaker attribution: Match by email header, "From:" line, or pattern recognition
 Timestamp extraction: Parse date from headers or infer from order
11.4 Confidence Gating
Internal Directory 13

IF attribution_confidence  0.7
RETURN 
"status": "blocked",
"reason": "speaker_attribution_ambiguous",
"candidates": [...], // Top-2 interpretations for human selection
"draft": null
}
11.5 Ambiguity Handling
Ambiguity Type Resolution
Unknown speaker Flag for human review
Multiple possible "latest buyer turn" Return top-2 with confidence
Forwarded internal thread mixed in Exclude internal turns, flag if unclear
Auto-reply detected Mark as administrative, don't treat as engagement
12. Deal Stage & Intent Classifier
Purpose: Map thread evidence to deal stage and buyer intent enumerations.
12.1 Stage Classification Rules
Stage Evidence Patterns
triage Initial contact, no clear need articulated
discovery Buyer describes situation, asks general questions
evaluation Comparison questions, technical depth, proof requests
proposal Pricing questions, "what would it cost", scope discussion
procurement Legal/security/compliance mentioned, contract language
negotiation Term discussion, redlines, final approvals
closed_won Agreement confirmed, contract signed
closed_lost Explicit rejection, "went with competitor", disqualified
stalled No activity > threshold 14 days default)
12.2 Intent Classification Rules
Intent Evidence Patterns
question_product "How does X work?", "Can you do Y?", feature questions
question_pricing "How much?", "What's the cost?", "Pricing?"
question_process "What are next steps?", "How does this work?"
Internal Directory 14

Intent Evidence Patterns
question_technical API questions, integration depth, specs
question_security SOC2, compliance, encryption, data handling
question_reference "Case studies?", "References?", "Who else uses?"
objection_timing "Not right now", "Maybe next quarter", timing hedge
objection_budget "Too expensive", "Not in budget", cost concern
objection_authority "Need to check with...", "Not my decision"
objection_need "Not sure we need this", fit questioning
objection_competition Mentions competitor, comparison request
commitment_signal "This looks good", "We're interested", positive indicator
commitment_request "Send proposal", "Let's schedule", explicit forward motion
information_share Provides context without explicit ask
administrative Scheduling, logistics, OOO
unclear Cannot determine intent with confidence
12.3 Confidence Calculation
confidence = base_score
+ keyword_match_boost
+ context_consistency_boost
- ambiguity_penalty
IF confidence  0.6
trigger escalate_to_human_review
13. Message OS (GRRIPS)
Purpose: Define message construction rules and the GRRIPS execution arc.
13.1 GRRIPS Node Definitions
Node Name Purpose Typical Length
G Greet/Ground Acknowledge, connect to context 1 sentence
R Restate/Reflect Show understanding of their situation 12 sentences
Show understanding of the personas unique
R Relate/Reinforce pain/friction, reinforce what happens if emotional 12 sentences
state is not shifted
I Identify/Insight Surface the core issue or opportunity 12 sentences
P Package/Provide Deliver the value (answer, artifact, information) 25 sentences
Internal Directory 15

Node Name Purpose Typical Length
S Suggest/Seal Single CTA or close 1 sentence
13.2 Arc Variations by Action Type
Action Type GRRIPS Arc Notes
Answer only 3 G  R  P No S node (no ask)
Answer + clarifier 4 G  R  P  S S is clarifying question
Provide artifact 6 G  P  S(optional) Minimal framing
Discovery probe 12 G  R  I  S S is single question
Propose call 17 G  R  P  S P is value prop, S is calendar CTA
Objection reframe 21 G  R  I  P  S Full arc for trust repair
Close graceful 24 G  R  P No S, leave door open
13.3 Length Constraints
Default: 50150 words
Technical answer: up to 250 words
Procurement packet: up to 300 words (mostly asset list)
Discovery/probe: 3080 words
Follow-up nudge: 3060 words
13.4 Forbidden Patterns
- "Just following up..."
- "I wanted to reach out..."
- "Hope this finds you well"
- "As per my last email"
- "Circling back"
- "Touching base"
 Multiple CTAs
 Multiple questions
 Rhetorical questions that are actually CTAs
- "Let me know if you have any questions" (lazy close)
14. Claims & Evidence Policy
Purpose: Rules for what can be asserted and how.
14.1 Claim Categories
Internal Directory 16

Category Rule Example
Thread-sourced Can assert directly "You mentioned you're using Salesforce"
Product config Can assert directly "We're SOC 2 Type II certified"
Approved assets Can reference "Our case study with Company] shows..."
Derived/inferred Must hedge "It sounds like timeline is a priority"
Unknown Must not assert ❌ "Most companies in your industry..."
14.2 Hedging Language
When uncertain, use:
- "Based on what you've shared..."
- "If I'm understanding correctly..."
- "I can confirm that..." (only if you actually can)
- "I'll need to check on that and get back to you"
14.3 Forbidden Claims
 Invented statistics
 Competitor disparagement without source
 Promises beyond your authority
 Pricing without policy approval
 Timelines you can't commit to
15. Drift Monitor & Repair Stack
Purpose: Detect degradation patterns and route to corrective actions.
15.1 Drift Flags (Inbound-Specific)
Flag Trigger Severity
df_cta_repetition Same CTA used 2x consecutively Medium
df_open_loop_ignored High-priority loop not addressed High
df_over_answering Response  200 words for simple question Low
df_premature_depth Technical detail before confirming need Medium
df_stakeholder_neglect CC'd blocker not addressed High
df_commitment_amnesia Prior promise not referenced High
df_tone_mismatch Formality diverging from buyer Medium
df_multi_ask More than one CTA or question High
df_pressure_escalation Urgency language in high-risk thread Critical
Internal Directory 17

15.2 Repair Actions
Drift Flag Repair Action
df_cta_repetition Force CTA variant selection
df_open_loop_ignored Re-route to actions 38
df_over_answering Compress to 35 sentences
df_premature_depth Prepend clarifying question
df_stakeholder_neglect Add direct acknowledgment
df_commitment_amnesia Prepend commitment reference
df_tone_mismatch Recalibrate to buyer's register
df_multi_ask Remove all but primary ask
df_pressure_escalation Soften language, add opt-out
15.3 Repair Escalation
IF repair_attempts  2 AND drift_flag persists:
trigger escalate_to_human_review
log repair_failure
Part VI: Output Specifications
16. Output Package Format
Every execution returns this structure:
{
"execution_id": "exec_2025011714300001",
"timestamp": "20250117T143000Z",
"execution_status": "success | blocked | needs_input | repair_applied",
"action_executed": "answer_explicit_question_only",
"draft": {
"text": "...",
"grips_nodes_used": ["G", "R", "P"],
"word_count" 67,
"cta_type": "none",
"cta_text": null,
"claims": [
{
Internal Directory 18

"claim": "SOC 2 Type II certified",
"source": "product_config.security",
"grounded": true
}
]
},
"thread_state_input_hash": "a3f2c1...",
"thread_state_updates": {
"last_seller_action": "answer_explicit_question_only",
"last_seller_cta": "none",
"last_seller_timestamp": "20250117T143000Z",
"last_seller_turn" 10,
"seller_turns" 5,
"total_turns" 10,
"open_loops": [
{"loop_id": "ol_001", "resolution_status": "answered", "resolved_at": "..."}
],
"open_loop_count" 0,
"state_updated_at": "20250117T143000Z"
},
"decision_trace": {
"preconditions_evaluated": [
{"action" 3, "result": true, "reason": "high-priority explicit question exists"},
{"action" 17, "result": false, "reason": "blocked by open_loop_priority_lock"}
],
"global_constraints_applied": ["open_loop_priority_lock", "single_ask_rule"],
"selected_action" 3,
"selection_reason": "Open loop resolution required before progression",
"alternative_actions_considered": ["4", "5"],
"alternative_rejection_reasons": {
"4": "clarification not needed, answer is complete",
"5": "external input not required"
}
},
"drift_checks": {
"flags_evaluated": ["df_cta_repetition", "df_open_loop_ignored", "df_over_answering"],
"flags_triggered": [],
"repair_applied": false
},
Internal Directory 19

"validation": {
"output_valid": true,
"checks_passed": ["single_ask", "claims_grounded", "postconditions_applied"]
}
}
17. TSV Row Format (Sheet-Friendly)
For external state storage, emit single-line tab-delimited row:
thread_id deal_stage stage_confidence buyer_intent intent_confidence open_loop_count
commitment_drift_flag risk_level risk_factorslast_seller_action last_seller_ctalast_seller_ti
mestamp days_since_last_buyer cta_repeat_flag stakeholder_count primary_stakeholder_e
mail schema_version state_updated_at
Example:
thr_2024_0892 evaluation 0.85question_security 0.92 0 false medium rf_legal_involve
d answer_explicit_question_only none 20250117T143000Z 0 false 2 sarah.chen@acm
e.com 1.0 20250117T143000Z
Part VII: Audit Framework
18. Audit Principles
 Every decision is traceable: Input state + routing logic → selected action
 Every claim is sourced: No output text without provenance
 Every constraint is checkable: Boolean evaluation against state
 Every failure is logged: Blocked executions include reason
 Every repair is documented: Drift flag + correction action
19. Pass/Fail Audit Checks
Check Pass Condition
Action validity action_executed ∈ 124
Precondition satisfaction All preconditions for selected action evaluate true
Global constraint compliance No constraint violated (open loop lock, commitment drift, single ask)
Internal Directory 20

Check Pass Condition
Claims grounding All claims have valid source
Postcondition application All required state updates present
CTA appropriateness CTA type matches action spec; no repetition
Word count compliance Within action-specific limits
Drift check execution All applicable drift flags evaluated
20. Audit Log Schema
{
"audit_entry": {
"execution_id": "...",
"timestamp": "...",
"thread_id": "...",
"input_state_hash": "...",
"output_state_hash": "...",
"checks": [
{"check": "action_validity", "result": "pass"},
{"check": "precondition_satisfaction", "result": "pass"},
{"check": "global_constraints", "result": "pass"},
{"check": "claims_grounding", "result": "pass"},
{"check": "postconditions", "result": "pass"},
{"check": "cta_appropriateness", "result": "pass"},
{"check": "drift_checks", "result": "pass"}
],
"overall_result": "pass",
"human_review_required": false,
"notes": null
}
}
Part VIII: Implementation Roadmap
21. Phase 1: Core Engine (MVP)
Deliverables:
Thread State Schema implementation
Internal Directory 21

Action Set with precondition evaluation
Policy Engine routing logic
Basic GRRIPS message generation
Output package formatting
TSV row emission
Success Criteria:
Can process a simple thread and emit valid output
All global constraints enforced
Audit trail complete
22. Phase 2: Safety & Governance
Deliverables:
Claims grounding validation
Drift monitor implementation
Repair stack routing
Confidence gating on ingestion/classification
Success Criteria:
No ungrounded claims in output
Drift patterns detected and repaired
Ambiguous inputs escalate correctly
23. Phase 3: Vertical Customization
Deliverables:
Industry pack format specification
Enablement asset library integration
Buyer role profile modulation
Vertical-specific stage/intent rules
Success Criteria:
Can load and apply industry-specific rules
Assets pulled from controlled library
Tone/depth adjusted by buyer role
Internal Directory 22

24. Phase 4: Scale & Optimization
Deliverables:
Thread compression for long threads
Batch processing capability
Performance optimization
A/B testing framework for message variants
Success Criteria:
Handles threads with 50 turns
Sub-second routing decisions
Variant testing produces measurable lift
Appendices
Appendix A: Notion PDF Library Structure
Recommended folder structure for Notion:
GENSE Architecture/
├── 00_Master_Architecture.pdf  This document
├── 01_Core_Identity_Boundaries.pdf
├── 02_Thread_Ingestion_Normalization.pdf
├── 03_Thread_State_Schema.pdf  Complete
├── 04_Deal_Stage_Intent_Classifier.pdf
├── 05_Action_Set_Command_Tree.pdf  Complete
├── 06_Policy_Engine.pdf
├── 07_Message_OS_GRRIPS.pdf
├── 08_Claims_Evidence_Policy.pdf
├── 09_Drift_Monitor_Repair_Stack.pdf
├── 10_Enablement_Asset_Library.pdf
├── 11_Industry_Pack_Format.pdf
├── 12_Buyer_Role_Profiles.pdf
├── 13_Audit_Guide.pdf
└── Reference/
├── Enum_Definitions.pdf
├── Example_Threads.pdf
└── Test_Cases.pdf
Internal Directory 23

Appendix B: Quick Reference Cards
B.1 Action Selection Cheat Sheet
Q Does buyer have an unanswered question?
YES  Actions 38 (open loop resolution)
Q Did we miss a commitment?
YES  Action 10 (recover)
Q Is there an active objection?
YES  Action 21 (reframe)
Q Is competitor mentioned?
YES  Action 22 (compare)
Q No response in 7 days?
YES  Action 23 (nudge) or 24 (close)
Q All clear, deal is progressing?
 Actions 1220 based on stage
B.2 CTA Selection Cheat Sheet
NEVER
 Multiple CTAs
 Urgent language in high-risk threads
 Same CTA twice in a row
LOW PRESSURE (use freely):
- none, async_review, one_question
MEDIUM PRESSURE (when loops clear):
- calendar_light, confirm_owner_deadline
STAGEMATCHED
 Procurement → process_confirm (never "let's chat")
 Evaluation → async_choice (offer options)
 Proposal → async_review_or_call
Appendix C: Glossary
Internal Directory 24

Term Definition
Action A bounded "sales move" from the enumerated set 124
CTA Call to action; the single ask in a message
Deal Stage Current position in the sales pipeline
Drift Degradation pattern in system output
GRRIPS Message construction framework Greet, Restate, Reinforce, Identify, Package, Suggest)
Open Loop Unresolved buyer question or concern
Policy Engine Routing logic that maps state → action
Postcondition Required state update after action execution
Precondition Boolean expression that must be true for action to be available
Thread State Structured representation of an email thread's current status
Document Control
Version Date Author Changes
1.0 20250117 System Initial architecture foundation
End of Master Architecture Document
Internal Directory 25