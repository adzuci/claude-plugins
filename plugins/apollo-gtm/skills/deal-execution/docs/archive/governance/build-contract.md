GEN-SE Architecture Contract
— Claude Build Instructions
Version: 1.1 FINAL
Status: LOCKED (change only via versioned changelog + review)
Last Updated: 20250118
Reconciliation: Claude audit  ChatGPT revision + final review
A1) Non-Negotiables (Load-Bearing Invariants)
# Principle Enforcement
1 Stateless execution State passed in/out every run; no implicit memory
2 Fail-safe behavior Block/escalate on ambiguity; never guess
Bounded action
3 Only actions 124 from enumerated set
space
4 Two-part output Draft + updated state row + trace (every run)
Exactly one ask-block per message; never
5 Single ask-block
CTA+question
6 Open loops first No progression while high-priority loops open
Detect → repair → escalate if persistent 2
7 Drift governance
attempts max)
8 Audit trail Every decision reconstructable from logs
A2) Canonical Execution Sequence
This is the only valid selection flow. Do not reorder.
STEP 1 — Input Validation
Check:
Schema compliance (all required fields present)
GENSE Architecture Contract  Claude Build Instructions 1

Consistency checks (turn counts match, timestamps ordered)
Confidence thresholds met:
attribution_confidence  0.70
stage_confidence  0.60
intent_confidence  0.60
On failure: execution_status = "blocked" with explicit reason. No draft emitted.
STEP 2 — Hard Blocks (absolute gates)
Evaluate in order:
Condition Result
commitment_drift_flag == true Constrain to 10 ONLY
attribution_confidence  0.70 Action 1 (escalate)
stage_confidence  0.60 Action 1 (escalate)
intent_confidence  0.60 Action 1 (escalate)
required_config_missing == true Action 2 (request context)
STEP 3 — Priority Locks
Locks constrain the action space BEFORE precondition evaluation.
Lock evaluation order: Lock 2  Lock 1  Lock 3 (most restrictive first)
LOCK 2: Commitment Drift Lock (ABSOLUTE)
TRIGGER commitment_drift_flag == true
EFFECT allowed_actions = 10
REASON Must repair trust before any other move
LOCK 1: Open Loop Priority Lock
TRIGGER open_loops.any(priority == "high" AND resolution_status == "ope
n")
GENSE Architecture Contract  Claude Build Instructions 2

EFFECT allowed_actions ⊆ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
REASON Cannot advance deal while high-priority buyer loop unresolved
Note: If only medium/low priority loops exist, progression actions 1224 remain
eligible, but the Policy Engine MUST prefer loop-resolution actions via affinity
scoring. This is a soft constraint, not a hard lock.
LOCK 3: CTA Repetition Lock
TRIGGER proposed_cta_type IN last_3_ctas[]
EFFECT Block the proposed action; force CTA variant OR select next-best ac
tion
REASON Prevent repetitive asks that degrade trust
STEP 4 — Precondition Evaluation
For each action in allowed_actions (post-lock):
Evaluate ALL preconditions against current state
Use fully parenthesized boolean logic (no implicit AND/OR precedence)
Mark each action: AVAILABLE or BLOCKED with explicit reason
STEP 5 — Action Selection
Condition Action
0 actions available Select Action 1 (escalate_to_human_review)
1 action available Select it
2 actions available Apply Intent-Action Affinity Scoring A3
STEP 6 — Decision Trace (mandatory)
Log the following for every execution:
locks_applied[] — which locks fired, in order
actions_evaluated[] — each action with pass/fail and reason
selected_action — final choice
GENSE Architecture Contract  Claude Build Instructions 3

selection_reason — why this action won
alternatives_rejected[] — other candidates and rejection reasons
A3) Intent-Action Affinity Scoring
When multiple actions pass preconditions, select by highest affinity to detected
buyer_intent .
Primary Affinity Table (V1)
Secondary
buyer_intent Primary Action(s) Notes
Action(s)
question_product 3 4, 6 Answer first
7 (inputs missing) / 19
question_pricing 3, 16 Stage-gated
(inputs ready)
question_process 8 3, 16
question_technical 3 4, 6
6 (asset exists) / 5
question_security 3
(external needed)
question_reference 6 3
objection_timing 21 15
Only if buyer
objection_budget 21 7, 19
asked
*See stakeholder
objection_authority 13 / 14* —
rule
objection_need 21 12
objection_competition 22 21
commitment_signal 18 16, 17 Stage-gated
commitment_request 17, 19, 20 18 Stage-gated
information_share 12 (early) / 16 (eval+) 3
administrative 3 18
unclear 1 — Escalate
GENSE Architecture Contract  Claude Build Instructions 4

Stakeholder Rule (objection_authority):
Default primary: Action 13 (stakeholder_expand)
If latest_author_role IN {legal, security, procurement}  Action 14 primary (redirect to asker)
Tie-Breakers (deterministic)
 Highest affinity score wins
 If tied: Lower action number (safer/simpler wins)
 If still tied: Lower CTA pressure (none < question < async_choice <
calendar_light)
A4) CTA History Tracking
Required fields in thread_state (updated as postconditions):
Field Type Purpose
last_3_ctas[] array Last 3 CTA types used (most recent first)
last_3_actions[] array Last 3 actions executed
cta_repeat_flag boolean True if proposed CTA in last_3_ctas
action_diversity_score float 0.01.0 Low 0.3 triggers drift
last_seller_cta string Single most recent CTA type
A5) Ask-Block Rule
System-level constraint replacing "one CTA or one question":
ask_blocks_per_message  1
Ask-block types:
cta  One call-to-action
question  One clarifying question
input_request_block  Up to 3 related sub-questions (counts as ONE ask-block)
GENSE Architecture Contract  Claude Build Instructions 5

NEVER combine CTA  question in the same message.
A6) Output Contract
Every execution MUST return:
{
"execution_id": "exec_YYYYMMDDHHMMSS###",
"timestamp": "ISO8601",
"execution_status": "success | blocked | needs_input | repair_applied",
"action_executed" 3,
"draft": {
"text": "...",
"grrips_nodes_used": ["G", "R", "P"],
"word_count" 67,
"cta_type": "none | question | async_review | calendar_light | ...",
"cta_text": null,
"claims": [
{"claim": "...", "source": "thread | config | asset | derived", "grounded": tru
e}
]
},
"thread_state_updates": {
"last_seller_action": "answer_explicit_question_only",
"last_seller_cta": "none",
"open_loops": [...],
"open_loop_count" 0
},
"decision_trace": {
"locks_applied": ["open_loop_priority_lock"],
"actions_evaluated": [
{"action" 3, "result": "pass", "reason": "..."},
GENSE Architecture Contract  Claude Build Instructions 6

{"action" 17, "result": "fail", "reason": "blocked by lock"}
],
"selected_action" 3,
"selection_reason": "Highest affinity for question_product intent",
"alternatives_rejected": {"4": "clarification not needed"}
},
"drift_checks": {
"flags_evaluated": ["df_cta_repetition", "df_open_loop_ignored"],
"flags_triggered": [],
"repair_applied": false
},
"validation": {
"output_valid": true,
"checks_passed": ["single_ask", "claims_grounded", "postconditions_applie
d"]
}
}
Also emit: TSV row per Master Architecture Section 17.
A7) Drift Flags (for Drift Monitor)
Flag Trigger Severity
df_cta_repetition Same CTA used 2x consecutively Medium
df_open_loop_ignored High-priority loop not addressed High
df_over_answering Response  200 words for simple question Low
df_premature_depth Technical detail before confirming need Medium
df_stakeholder_neglect CC'd blocker not addressed High
df_commitment_amnesia Prior promise not referenced High
df_tone_mismatch Formality diverging from buyer Medium
df_multi_ask More than one ask-block High
GENSE Architecture Contract  Claude Build Instructions 7

Flag Trigger Severity
df_pressure_escalation Urgency language in high-risk thread Critical
Repair limit: 2 attempts. If drift persists after 2 repairs → escalate to human.
A8) Configuration Defaults (overridable via Industry
Pack)
Parameter Default Override Location
attribution_confidence_threshold 0.70 Industry Pack
stage_confidence_threshold 0.60 Industry Pack
intent_confidence_threshold 0.60 Industry Pack
stall_threshold_days 14 Industry Pack
repair_attempt_limit 2 Industry Pack
max_word_count_default 150 Industry Pack
max_word_count_technical 250 Industry Pack
Stall detection basis: Days since last buyer response (not last activity).
Document B: Implementation Playbook
Version: 1.0
Status: ACTIVE (update as build progresses)
B1) Already Complete — DO NOT RE-SPECIFY
Module Status Document
Master Architecture Complete 00_Master_Architecture.pdf
Thread State Schema Complete 03_Thread_State_Schema.pdf
Action Set  Command Tree Complete 05_Action_Set_Command_Tree.pdf
Policy Engine Spec Complete 06_Policy_Engine.pdf
GENSE Architecture Contract  Claude Build Instructions 8

B2) Phase 1: Core Engine Implementation
Build in this order:
Confidence
# Module Key Deliverables
Gate
Turn split, attribution,
1 Thread Ingestion 0.70 or block
quote/sig/footer strip
Open loops, commitments,
2 State Extractor —
stakeholders, timestamps
Stage/Intent 0.60 or
3 Rule-based + confidence score
Classifier escalate
Policy Engine Locks → preconditions → affinity
4 —
Router → trace
Message GRRIPS arcs + forbidden patterns
5 —
Generator + length
6 Claims Validator Source check + hedge insertion —
9 flags + repair routing 2
7 Drift Monitor —
attempts)
8 Output Packager JSON  TSV  audit entry —
B3) Module Completion Criteria
Every module must have:
Inputs/Outputs defined
Failure modes + fail-safe behavior documented
3 test vectors (simple / edge / failure)
Version number + changelog entry
Integration with decision trace format
B4) Test Vector Schema
GENSE Architecture Contract  Claude Build Instructions 9

{
"test_id": "MODULE_###_type",
"test_type": "simple | edge | failure",
"description": "Human-readable intent",
"input": {
"thread_state": {},
"thread_content": "",
"config": {}
},
"expected_output": {
"execution_status": "success | blocked | needs_input | repair_applied",
"action_selected" 3,
"cta_type": "none",
"locks_applied": [],
"preconditions_passed": 3, 4,
"selection_reason": "...",
"state_updates": {
"open_loop_count_delta": 1
}
},
"assertions": [
"action_selected  3",
"cta_type == 'none'",
"execution_status == 'success'"
]
}
B5) Phase 2: Safety & Governance
# Module Deliverables
9 Confidence gating All classification steps gated
GENSE Architecture Contract  Claude Build Instructions 10

# Module Deliverables
10 Repair stack 2-attempt limit + escalation
11 Human escalation queue Integration spec
B6) Phase 3: Vertical Customization
# Module Deliverables
12 Industry Pack loader Config override system
13 Buyer Role Profiles Tone/depth modulation
14 Vertical thresholds Enterprise vs SMB defaults
Changelog
Version Date Author Changes
1.0 20250117 Drew Initial architecture foundation
Added: Priority locks, evaluation
sequence, intent-action affinity, CTA
1.1 20250118 Claude/ChatGPT history, ask-block rule, drift flags
enumeration. Fixed: Lock 1 action
set (restored 9, 11.
Ready for Implementation
First task: Thread Ingestion module with:
Turn splitting
Speaker attribution with confidence scoring
Quote/signature/footer stripping
Top-2 ambiguity output when confidence  0.70
GENSE Architecture Contract  Claude Build Instructions 11