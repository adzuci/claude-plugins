GEN-SE Policy Engine
Module: 06_Next_Safe_Action_Policy_Engine
Version: 1.1.1 REFORGED  PATCHED
Status: READY TO LOCK
Date: January 20, 2026
Purpose: Routing logic that maps thread state → safest next action from the
bounded set of 24, with complete decision trace for audit.
AUDIT SUMMARY
Document Lineage
Version Date Status Changes
1.0 20250117 SUPERSEDED Initial specification
Reforged: threshold alignment, lock
stacking semantics, upstream gating
1.1 20260120 SUPERSEDED
fields, deterministic tie-breakers,
failure modes, worked examples
Patch: Added buyer_role_confidence to
1.1.1 20260120 CURRENT required fields and hard block
HB_002b to close identity gating hole
V1.1 Amendment Summary
This version addresses stress-test findings from architecture audit:
 Threshold Alignment GAP01 Unified confidence thresholds—validation is
structural only, hard blocks own all threshold enforcement at contract-
specified values 0.70 attribution, 0.60 stage/intent)
 Lock Stacking Semantics GAP02 Clarified that locks STACK (intersect
allowed, union blocked, accumulate CTA constraints) with explicit precedence
rules
GENSE Policy Engine 1

 Upstream Gating Fields GAP03 Added attribution_confidence ,
required_config_missing , parse_status to required fields for end-to-end identity gating
 Deterministic Tie-Breakers GAP04 Formalized selection tie-breakers:
affinity → action_id ASC  CTA pressure ASC
 Precondition Field Defaults GAP05 All precondition-dependent fields now
have explicit defaults to prevent silent failures
 Failure Modes GAP06 Added explicit failure mode enumeration
FM_PE_001 to FM_PE_007
 Worked Examples GAP07 Added 5 complete input→output examples
V1.1.1 Patch Summary
 Identity Gating Hole Closure GAP08 Added buyer_role_confidence to
REQUIRED_FIELDS and HB_002b hard block to ensure role inference is gated
at 0.70, not just speaker attribution. This closes the hole where we could know
WHO spoke but not WHICH SIDE they're on.
Contract Alignment: All V1.1/V1.1.1 changes align with Build Contract A2
(Canonical Execution Sequence) and A8 Configuration Defaults). Module 02 must
now emit buyer_role_confidence in its output.
Part I: Engine Overview
1.1 What the Policy Engine Does
The Policy Engine is the decision core of GENSE. It receives extracted thread
state and returns exactly one action from the bounded set of 24, along with a
complete decision trace.
INPUT thread_state (structured JSON from Module 03
OUTPUT 
selected_action: 124,
execution_status: "success" | "blocked" | "forced",
cta_constraint: {...},
GENSE Policy Engine 2

decision_trace: {...}
}
1.2 Core Guarantees
Guarantee Description Enforcement
Same input state always produces same Explicit tie-breakers, no
Deterministic
action selection randomness
Every decision can be reconstructed Complete decision_trace in
Auditable
from logged trace output
Ambiguity or missing data → escalate, Hard blocks + validation
Fail-safe
never guess gates
Safety constraints evaluated before Lock evaluation order is
Priority-ordered
progression fixed
Contract- Thresholds match Build Contract A8
Single source of truth
aligned exactly
1.3 Evaluation Sequence
The engine evaluates in strict order. No step can be skipped.
1. VALIDATE INPUT  Reject malformed state (structural only)
2. CHECK HARD BLOCKS  Immediate escalation/routing conditions
3. APPLY PRIORITY LOCKS  Constrain action space (locks STACK
4. EVALUATE PRECONDITIONS  Build candidate action set
5. APPLY SOFT CONSTRAINTS  Filter and rank candidates
6. SELECT ACTION  Pick highest-priority valid action (deterministic)
7. ENFORCE CTA UNIQUENESS  Verify CTA won't repeat
8. EMIT DECISION TRACE  Log complete reasoning
Part II: Input Validation
2.1 Required Fields (V1.1 AMENDED)
GENSE Policy Engine 3

The Policy Engine requires these fields to be present and valid. All fields listed
here MUST be provided by upstream modules.
REQUIRED_FIELDS  
# ═════════════════════════════════════════════════
══════════
# THREAD CORE (immutable, from Module 02/03
# ═════════════════════════════════════════════════
══════════
"thread_id": str,
"deal_stage" Enum[DEAL_STAGES,
"vertical": str,
# ═════════════════════════════════════════════════
══════════
# UPSTREAM GATING FIELDS V1.1 ADDITION, V1.1.1 PATCH
# These enable end-to-end identity/classification gating
# ═════════════════════════════════════════════════
══════════
"attribution_confidence": float, # From Module 02, 0.01.0 (speaker ident
ity)
"buyer_role_confidence": float, # From Module 02, 0.01.0 (buyer vs sell
er) [V1.1.1
"required_config_missing": bool, # From Module 02
"missing_config_fields" List[str], # From Module 02, may be empty
"parse_status": str, # "success" | "blocked" | "partial"
# ═════════════════════════════════════════════════
══════════
# CLASSIFICATION CONFIDENCE (from Module 04
# ═════════════════════════════════════════════════
══════════
"buyer_intent" Enum[BUYER_INTENTS,
"stage_confidence": float, # 0.01.0
"intent_confidence": float, # 0.01.0
GENSE Policy Engine 4

# ═════════════════════════════════════════════════
══════════
# CURRENT STATE (mutable, from Module 03
# ═════════════════════════════════════════════════
══════════
"open_loops" List[OpenLoop],
"open_loop_count": int,
"risk_level" Enum["low", "medium", "high", "critical"],
"commitment_drift_flag": bool,
"objection_tags" List[str], # May be empty
# ═════════════════════════════════════════════════
══════════
# INTERACTION HISTORY
# ═════════════════════════════════════════════════
══════════
"total_turns": int,
"seller_turns": int,
"last_seller_action": str | None,
"last_seller_cta": str | None,
"last_3_actions" List[str], # Most recent first, may be empty
"last_3_ctas" List[str], # Most recent first, may be empty
"days_since_last_buyer": int,
# ═════════════════════════════════════════════════
══════════
# STAKEHOLDERS
# ═════════════════════════════════════════════════
══════════
"stakeholder_count": int,
"stakeholders" List[Stakeholder] # May be empty
}
2.2 Optional Fields with Defaults (V1.1 ADDITION)
GENSE Policy Engine 5

Fields used in preconditions that may not always be present. If missing, use
default.
OPTIONAL_FIELDS_WITH_DEFAULTS  
# Precondition support fields
"answer_available_in_knowledge_base": (bool, False),
"enablement_packet_available": (bool, False),
"procurement_signals_detected": (bool, False),
"discovery_questions_remaining": (int, 0,
"timeline_known": (bool, False),
"expansion_signal_detected": (bool, False),
"new_stakeholder_in_thread": (bool, False),
"cc_added_this_turn": (bool, False),
"nudge_count": (int, 0,
"expected_stakeholder_count": (int, 1,
"product_context": (str, None),
"seller_assigned": (str, None),
# CTA tracking
"cta_repeat_flag": (bool, False),
"action_diversity_score": (float, 1.0,
}
2.3 Validation Gates (V1.1 AMENDED)
Validation is structural only. Threshold enforcement happens in Hard Blocks.
def validate_input(state: ThreadState)  ValidationResult:
errors = []
# ═════════════════════════════════════════════════
══════════
# STRUCTURAL VALIDATION ONLY
# Threshold checks moved to Hard Blocks for single source of truth
# ═════════════════════════════════════════════════
══════════
GENSE Policy Engine 6

# Check required fields exist
for field, expected_type in REQUIRED_FIELDS.items():
if field not in state:
errors.append(f"missing_field:{field}")
elif not isinstance(state[field], expected_type):
errors.append(f"invalid_type:{field}")
# Apply defaults for optional fields
for field, (expected_type, default) in OPTIONAL_FIELDS_WITH_DEFAULTS.it
ems():
if field not in state:
state[field] = default
# Check enum validity
if state.get("deal_stage") not in DEAL_STAGES
errors.append("invalid_deal_stage")
if state.get("buyer_intent") not in BUYER_INTENTS
errors.append("invalid_buyer_intent")
if state.get("risk_level") not in ["low", "medium", "high", "critical"]:
errors.append("invalid_risk_level")
if state.get("parse_status") not in ["success", "blocked", "partial"]:
errors.append("invalid_parse_status")
# Consistency checks
if state.get("open_loop_count", 0 ! len(state.get("open_loops", [])):
errors.append("open_loop_count_mismatch")
if errors:
return ValidationResult(
valid=False,
errors=errors,
forced_action=1, # escalate_to_human_review
reason="input_validation_failed"
)
GENSE Policy Engine 7

return ValidationResult(valid=True)
Part III: Hard Blocks
3.1 Hard Block Conditions (V1.1 AMENDED)
Hard blocks immediately force an action with no further evaluation. Thresholds
here are the single source of truth, matching Build Contract A8.
HARD_BLOCKS  
# ═════════════════════════════════════════════════
══════════
# UPSTREAM GATING BLOCKS V1.1 ADDITION
# These enforce end-to-end identity/classification contracts
# ═════════════════════════════════════════════════
══════════
{
"block_code": "HB_001",
"condition": "required_config_missing  True",
"forced_action" 2, # request_missing_context
"reason": "upstream_config_missing",
"contract_ref": "Build Contract STEP 2"
},
{
"block_code": "HB_002",
"condition": "attribution_confidence  0.70",
"forced_action" 1, # escalate_to_human_review
"reason": "speaker_attribution_unreliable",
"contract_ref": "Build Contract A8 attribution_confidence_threshold"
},
{
"block_code": "HB_002b", # V1.1.1 PATCH
"condition": "buyer_role_confidence  0.70",
"forced_action" 1, # escalate_to_human_review
GENSE Policy Engine 8

"reason": "buyer_role_identification_unreliable",
"contract_ref": "Module 02 role gating: buyer_role_confidence_threshold"
},
{
"block_code": "HB_003",
"condition": "parse_status == 'blocked'",
"forced_action" 1, # escalate_to_human_review
"reason": "upstream_parse_blocked",
"contract_ref": "Module 02 blocking contract"
},
# ═════════════════════════════════════════════════
══════════
# CLASSIFICATION CONFIDENCE BLOCKS
# Thresholds per Build Contract A8 0.60
# ═════════════════════════════════════════════════
══════════
{
"block_code": "HB_004",
"condition": "stage_confidence  0.60",
"forced_action" 1, # escalate_to_human_review
"reason": "stage_classification_unreliable",
"contract_ref": "Build Contract A8 stage_confidence_threshold"
},
{
"block_code": "HB_005",
"condition": "intent_confidence  0.60",
"forced_action" 1, # escalate_to_human_review
"reason": "intent_classification_unreliable",
"contract_ref": "Build Contract A8 intent_confidence_threshold"
},
# ═════════════════════════════════════════════════
══════════
# STRUCTURAL BLOCKS
# ═════════════════════════════════════════════════
GENSE Policy Engine 9

══════════
{
"block_code": "HB_006",
"condition": "stakeholder_count  0",
"forced_action" 1,
"reason": "no_addressable_stakeholder"
},
{
"block_code": "HB_007",
"condition": "deal_stage == 'closed_lost'",
"forced_action" 1,
"reason": "deal_already_lost"
},
{
"block_code": "HB_008",
"condition": "deal_stage == 'closed_won'",
"forced_action" 1,
"reason": "deal_already_won"
},
{
"block_code": "HB_009",
"condition": "total_turns  100",
"forced_action" 1,
"reason": "thread_exceeds_complexity_limit"
}
]
3.2 Hard Block Evaluation
def evaluate_hard_blocks(state: ThreadState, trace: DecisionTrace)  Optiona
l[PolicyResult]:
for block in HARD_BLOCKS
trace.hard_blocks_evaluated.append(block["block_code"])
if evaluate_condition(block["condition"], state):
GENSE Policy Engine 10

trace.hard_block_triggered = block["block_code"]
trace.hard_block_reason = block["reason"]
return PolicyResult(
action=block["forced_action"],
execution_status="blocked",
reason=block["reason"],
contract_ref=block.get("contract_ref"),
trace=trace
)
return None # No hard block triggered
Part IV: Priority Locks
4.1 Lock Stacking Semantics (V1.1 CLARIFIED)
Locks STACK. Multiple locks can be active simultaneously. Their effects combine
as follows:
Effect Type Combination Rule
allowed_actions INTERSECTION (most restrictive wins)
blocked_actions UNION (all blocks apply)
cta_constraints UNION (all constraints apply)
preferred_actions Applied during selection ranking, not lock phase
Evaluation order: Locks are evaluated in lock_id order PL_001  PL_002  ...).
Order matters for tracing but not for final effect since locks stack.
4.2 Priority Lock Definitions
PRIORITY_LOCKS  
# ═════════════════════════════════════════════════
══════════
# LOCK 1 Commitment Recovery ABSOLUTE  Highest Priority)
GENSE Policy Engine 11

# ═════════════════════════════════════════════════
══════════
{
"lock_id": "PL_001",
"name": "commitment_recovery_lock",
"condition": "commitment_drift_flag  True",
"allowed_actions": 10, # recover_missed_commitment ONLY
"effect_type": "absolute", # Overrides all other locks
"reason": "must_recover_broken_commitment_before_any_other_action",
"contract_ref": "Build Contract LOCK 2"
},
# ═════════════════════════════════════════════════
══════════
# LOCK 2 High-Priority Open Loop Resolution
# ═════════════════════════════════════════════════
══════════
{
"lock_id": "PL_002",
"name": "open_loop_priority_lock",
"condition": "any(loop.priority == 'high' and loop.resolution_status == 'op
en' for loop in open_loops)",
"allowed_actions": 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
"effect_type": "restrictive",
"reason": "high_priority_buyer_question_blocks_progression",
"contract_ref": "Build Contract LOCK 1"
},
# ═════════════════════════════════════════════════
══════════
# LOCK 3 Any Open Loop Blocks Hard Progression
# ═════════════════════════════════════════════════
══════════
{
"lock_id": "PL_003",
"name": "open_loop_soft_lock",
GENSE Policy Engine 12

"condition": "open_loop_count  0",
"blocked_actions": 17, 18, 19, 20, # No calls, confirmations, proposals
"effect_type": "blocking",
"reason": "cannot_propose_calls_with_unresolved_questions"
},
# ═════════════════════════════════════════════════
══════════
# LOCK 4 Critical Risk Constraint
# ═════════════════════════════════════════════════
══════════
{
"lock_id": "PL_004",
"name": "critical_risk_lock",
"condition": "risk_level == 'critical'",
"blocked_actions": 16, 17, 18, 19, 20, 21, # No progression or pressure
"cta_constraints": ["none", "async_review", "opt_out"], # Whitelist
"effect_type": "blocking",
"reason": "critical_risk_requires_low_pressure_only"
},
# ═════════════════════════════════════════════════
══════════
# LOCK 5 Stalled Thread Preference, not hard lock)
# ═════════════════════════════════════════════════
══════════
{
"lock_id": "PL_005",
"name": "stalled_thread_lock",
"condition": "days_since_last_buyer  14",
"preferred_actions": 23, 24, # nudge or close
"effect_type": "preference", # Applied during selection, not here
"reason": "thread_stalled_requires_reengagement_or_closure"
},
# ═════════════════════════════════════════════════
GENSE Policy Engine 13

══════════
# LOCK 6 CTA Repetition Prevention
# ═════════════════════════════════════════════════
══════════
{
"lock_id": "PL_006",
"name": "cta_repetition_lock",
"condition": "len(last_3_ctas)  2 and last_3_ctas[0] == last_3_ctas[1]",
"cta_constraints_exclude": [last_3_ctas[0]], # Block repeated CTA type
"effect_type": "cta_constraint",
"reason": "same_cta_used_twice_consecutively",
"contract_ref": "Build Contract LOCK 3"
}
]
4.3 Lock Application Algorithm (V1.1 CLARIFIED)
def apply_priority_locks(state: ThreadState, trace: DecisionTrace)  LockResu
lt:
# Start with all actions allowed
allowed_actions = set(range(1, 25 # Actions 124
blocked_actions = set()
cta_constraints = []
cta_exclusions = []
active_locks = []
preferred_actions = []
for lock in PRIORITY_LOCKS
trace.priority_locks_evaluated.append(lock["lock_id"])
if not evaluate_condition(lock["condition"], state):
continue
active_locks.append(lock["lock_id"])
GENSE Policy Engine 14

# ═══════════════════════════════════════════════
════════
# ABSOLUTE LOCK Overrides everything
# ═══════════════════════════════════════════════
════════
if lock.get("effect_type") == "absolute":
return LockResult(
allowed_actions=lock["allowed_actions"],
blocked_actions=set(range(1, 25  set(lock["allowed_actions"]),
cta_constraints=lock.get("cta_constraints", []),
active_locks=active_locks,
forced=True,
forced_reason=lock["reason"]
)
# ═══════════════════════════════════════════════
════════
# RESTRICTIVE LOCK Intersect allowed actions
# ═══════════════════════════════════════════════
════════
if "allowed_actions" in lock and lock.get("effect_type") == "restrictive":
allowed_actions = allowed_actions.intersection(set(lock["allowed_actio
ns"]))
# ═══════════════════════════════════════════════
════════
# BLOCKING LOCK Union blocked actions
# ═══════════════════════════════════════════════
════════
if "blocked_actions" in lock:
blocked_actions = blocked_actions.union(set(lock["blocked_actions"]))
# ═══════════════════════════════════════════════
════════
# CTA CONSTRAINTS Accumulate
# ═══════════════════════════════════════════════
GENSE Policy Engine 15

════════
if "cta_constraints" in lock:
cta_constraints.extend(lock["cta_constraints"])
if "cta_constraints_exclude" in lock:
cta_exclusions.extend(lock["cta_constraints_exclude"])
# ═══════════════════════════════════════════════
════════
# PREFERENCE Store for selection phase
# ═══════════════════════════════════════════════
════════
if "preferred_actions" in lock:
preferred_actions.extend(lock["preferred_actions"])
# Apply blocked to allowed
final_allowed = allowed_actions - blocked_actions
trace.priority_locks_active = active_locks
trace.actions_after_locks = list(final_allowed)
return LockResult(
allowed_actions=list(final_allowed),
blocked_actions=list(blocked_actions),
cta_constraints=list(set(cta_constraints)) if cta_constraints else None,
cta_exclusions=list(set(cta_exclusions)),
preferred_actions=preferred_actions,
active_locks=active_locks,
forced=False
)
Part V: Action Selection
5.1 Canonical Enumerations
GENSE Policy Engine 16

DEAL_STAGES  
"triage", "discovery", "evaluation", "proposal",
"procurement", "negotiation", "closed_won", "closed_lost"
]
BUYER_INTENTS  
# Questions
"question_product", "question_pricing", "question_process",
"question_technical", "question_security", "question_reference",
# Objections
"objection_timing", "objection_budget", "objection_authority",
"objection_need", "objection_competition",
# Signals
"commitment_signal", "commitment_request",
"information_share", "administrative", "unclear"
]
PROGRESSION_ACTIONS  16, 17, 18, 19, 20
CONTROL_ACTIONS  1, 2
OPEN_LOOP_ACTIONS  3, 4, 5, 6, 7, 8
COMMITMENT_ACTIONS  9, 10, 11
5.2 Priority Tiers
PRIORITY_TIERS  
# Tier 0 Control (always available)
"control": 1, 2,
# Tier 1 Open Loop Resolution (highest after control)
"open_loop_resolution": 3, 4, 5, 6, 7, 8,
# Tier 2 Commitment Integrity
"commitment_integrity": 9, 10, 11,
GENSE Policy Engine 17

# Tier 3 Stakeholder Management
"stakeholder_management": 13, 14,
# Tier 4 Objection Handling
"objection_handling": 21, 22,
# Tier 5 Discovery
"discovery": 12, 15,
# Tier 6 Soft Progression
"progression_soft": 16,
# Tier 7 Call Progression
"progression_call": 17, 18,
# Tier 8 Formal Progression
"progression_formal": 19, 20,
# Tier 9 Re-engagement
"reengagement": 23, 24
}
# Map action → tier number for sorting
ACTION_TO_TIER  
for tier_num, (tier_name, actions) in enumerate(PRIORITY_TIERS.items()):
for action in actions:
ACTION_TO_TIER[action] = tier_num
5.3 Intent-Action Affinity Table
INTENT_AFFINITY  
# Questions  Answer first
"question_product": {"primary": 3, "secondary": 4, 6,
"question_pricing": {"primary": 7, 19, "secondary": 3, 16, # 7 if inputs
missing, 19 if ready
GENSE Policy Engine 18

"question_process": {"primary": 8, "secondary": 3, 16,
"question_technical": {"primary": 3, "secondary": 4, 6,
"question_security": {"primary": 6, 5, "secondary": 3, # 6 if asset exist
s, 5 if external needed
"question_reference": {"primary": 6, "secondary": 3,
# Objections  Address concern
"objection_timing": {"primary": 21, "secondary": 15,
"objection_budget": {"primary": 21, "secondary": 7, 19,
"objection_authority": {"primary": 13, 14, "secondary": []}, # 13 default, 1
4 if blocker role
"objection_need": {"primary": 21, "secondary": 12,
"objection_competition": {"primary": 22, "secondary": 21,
# Signals  Progress appropriately
"commitment_signal": {"primary": 18, "secondary": 16, 17,
"commitment_request": {"primary": 17, 19, 20, "secondary": 18,
"information_share": {"primary": 12, 16, "secondary": 3, # 12 early, 16 e
val+
"administrative": {"primary": 3, "secondary": 18,
"unclear": {"primary": 1, "secondary": []} # Escalate
}
5.4 Deterministic Tie-Breakers (V1.1 ADDITION)
When multiple candidates have equal ranking after affinity scoring:
TIE_BREAKER_ORDER  
# 1. Intent affinity (primary > secondary > none)
lambda c, state: -get_affinity_score(c["action_id"], state.buyer_intent),
# 2. Lower action number (safer/simpler)
lambda c, state: c["action_id"],
# 3. Lower CTA pressure
lambda c, state: CTA_PRESSURE_RANK.get(get_lowest_pressure_cta(c["act
GENSE Policy Engine 19

ion_id"]), 99,
# 4. Higher precondition confidence
lambda c, state: -c.get("confidence", 0
]
CTA_PRESSURE_RANK  
"none" 0,
"one_question" 1,
"async_review" 2,
"async_choice" 3,
"confirm_owner_deadline" 4,
"calendar_light" 5,
"calendar_specific" 6,
"process_confirm" 7,
"opt_out" 8
}
5.5 Selection Algorithm (V1.1 AMENDED)
def select_action(
state: ThreadState,
lock_result: LockResult,
trace: DecisionTrace
)  ActionSelection:
# ═════════════════════════════════════════════════
══════════
# STEP 1 Evaluate preconditions for all allowed actions
# ═════════════════════════════════════════════════
══════════
candidates = []
for action_id in lock_result.allowed_actions:
spec  ACTION_SPECS[action_id]
eval_result = evaluate_preconditions(spec.preconditions, state)
GENSE Policy Engine 20

trace.preconditions_evaluated.append({
"action": action_id,
"satisfied": eval_result.satisfied,
"confidence": eval_result.confidence,
"reason": eval_result.reason
})
if eval_result.satisfied:
candidates.append({
"action_id": action_id,
"confidence": eval_result.confidence,
"tier" ACTION_TO_TIER.get(action_id, 99,
"affinity": get_affinity_score(action_id, state.buyer_intent)
})
trace.candidates_after_preconditions = [c["action_id"] for c in candidates]
# ═════════════════════════════════════════════════
══════════
# STEP 2 No candidates = escalate
# ═════════════════════════════════════════════════
══════════
if not candidates:
trace.selection_reason = "no_action_preconditions_satisfied"
return ActionSelection(
action_id=1,
reason="no_candidates_available",
fallback=True
)
# ═════════════════════════════════════════════════
══════════
# STEP 3 Apply stall preference boost (if PL_005 active)
# ═════════════════════════════════════════════════
══════════
GENSE Policy Engine 21

if lock_result.preferred_actions:
for candidate in candidates:
if candidate["action_id"] in lock_result.preferred_actions:
candidate["tier"] = 1 # Boost to top
trace.stall_preference_applied  True
# ═════════════════════════════════════════════════
══════════
# STEP 4 Sort by tier, then affinity, then tie-breakers
# ═════════════════════════════════════════════════
══════════
def sort_key(c):
return (
c["tier"], # Lower tier = higher priority
-c["affinity"], # Higher affinity = higher priority
c["action_id"], # Lower action_id wins ties
CTA_PRESSURE_RANK.get(
get_lowest_pressure_cta(c["action_id"]), 99
), # Lower CTA pressure wins
-c["confidence"] # Higher confidence wins
)
ranked = sorted(candidates, key=sort_key)
trace.selection_ranking = [(c["action_id"], sort_key(c)) for c in ranked]
# ═════════════════════════════════════════════════
══════════
# STEP 5 CTA uniqueness enforcement
# ═════════════════════════════════════════════════
══════════
selected  None
for candidate in ranked:
spec  ACTION_SPECS[candidate["action_id"]]
# Check CTA whitelist constraint (from critical risk lock)
if lock_result.cta_constraints:
GENSE Policy Engine 22

valid_ctas = [cta for cta in spec.allowed_ctas
if cta in lock_result.cta_constraints]
if not valid_ctas:
trace.cta_constraint_rejections.append({
"action": candidate["action_id"],
"reason": "no_allowed_cta_in_whitelist"
})
continue
# Check CTA exclusion (from repetition lock)
if lock_result.cta_exclusions:
valid_ctas = [cta for cta in spec.allowed_ctas
if cta not in lock_result.cta_exclusions]
if not valid_ctas and "none" not in spec.allowed_ctas:
trace.cta_constraint_rejections.append({
"action": candidate["action_id"],
"reason": "all_ctas_excluded_by_repetition"
})
continue
# Check against last_3_ctas
if not validate_cta_uniqueness(spec.allowed_ctas, state.last_3_ctas):
# Try to find a non-repeating CTA for this action
non_repeating = [cta for cta in spec.allowed_ctas
if cta not in state.last_3_ctas or cta == "none"]
if not non_repeating:
trace.cta_constraint_rejections.append({
"action": candidate["action_id"],
"reason": "would_repeat_cta"
})
continue
selected = candidate
break
# ═════════════════════════════════════════════════
GENSE Policy Engine 23

══════════
# STEP 6 Fallback if all CTAs would repeat
# ═════════════════════════════════════════════════
══════════
if selected is None:
# Find any action with "none" CTA
for candidate in ranked:
spec  ACTION_SPECS[candidate["action_id"]]
if "none" in spec.allowed_ctas:
selected = candidate
trace.selection_reason = "fallback_to_no_cta_action"
break
# Ultimate fallback
if selected is None:
selected = ranked[0]
trace.selection_reason = "forced_despite_cta_repeat"
# ═════════════════════════════════════════════════
══════════
# STEP 7 Build result
# ═════════════════════════════════════════════════
══════════
trace.selected_action = selected["action_id"]
trace.selection_confidence = selected["confidence"]
if not trace.selection_reason:
trace.selection_reason = f"highest_ranked_candidate_tier_{selected['tie
r']}"
# Record alternatives
trace.alternatives_considered = [c["action_id"] for c in ranked[15]]
trace.alternatives_rejection_reasons = {
c["action_id"]: "lower_priority" for c in ranked[15]
}
return ActionSelection(
GENSE Policy Engine 24

action_id=selected["action_id"],
confidence=selected["confidence"],
reason=trace.selection_reason,
cta_constraint=determine_cta_constraint(selected["action_id"], lock_resu
lt),
fallback=False
)
Part VI: Failure Modes (V1.1 ADDITION)
6.1 Failure Mode Enumeration
Code Trigger Response Escalation Path
Input validation fails execution_status: Human review
FM_PE_001
(missing/invalid fields) "blocked" , Action 1 queue
Hard block triggered
execution_status: Human review or
FM_PE_002 (confidence
"blocked" , Action 1 or 2 config request
thresholds)
No candidates after
execution_status: Human review
FM_PE_003 precondition
"blocked" , Action 1 queue
evaluation
execution_status: "forced" ,
All candidates rejected Log warning,
FM_PE_004 first ranked with "none"
by CTA constraints proceed
CTA
Commitment drift lock execution_status: "forced" , N/A (correct
FM_PE_005
forces Action 10 Action 10 behavior)
execution_status:
Critical risk constrains N/A (correct
FM_PE_006 "success" with CTA
all CTAs behavior)
whitelist
Thread exceeds
execution_status: Human review,
FM_PE_007 complexity limit 100
"blocked" , Action 1 thread compression
turns)
6.2 Failure Response Contract
GENSE Policy Engine 25

def handle_failure(failure_code: str, state: ThreadState, trace: DecisionTrace) -
 PolicyResult:
"""All failures return a valid PolicyResult with complete trace."""
FAILURE_RESPONSES  
"FM_PE_001" PolicyResult(
action=1,
execution_status="blocked",
reason="input_validation_failed",
human_review_required=True
),
"FM_PE_002" PolicyResult(
action=trace.hard_block_triggered_action or 1,
execution_status="blocked",
reason=trace.hard_block_reason,
human_review_required=(trace.hard_block_triggered_action  1
),
"FM_PE_003" PolicyResult(
action=1,
execution_status="blocked",
reason="no_action_preconditions_satisfied",
human_review_required=True
),
"FM_PE_004" PolicyResult(
action=trace.fallback_action,
execution_status="forced",
reason="cta_constraint_forced_fallback",
human_review_required=False,
warning="all_preferred_ctas_exhausted"
),
# FM_PE_005 and FM_PE_006 are not failures, they're correct lock behav
ior
}
result  FAILURE_RESPONSES.get(failure_code)
GENSE Policy Engine 26

result.trace = trace
return result
Part VII: Decision Trace Output
7.1 Trace Schema
Every execution emits a complete decision trace:
@dataclass
class DecisionTrace:
# ═════════════════════════════════════════════════
══════════
# INPUT SUMMARY
# ═════════════════════════════════════════════════
══════════
input_state_hash: str
thread_id: str
deal_stage: str
buyer_intent: str
open_loop_count: int
risk_level: str
attribution_confidence: float # V1.1 addition
buyer_role_confidence: float # V1.1.1 addition
stage_confidence: float
intent_confidence: float
# ═════════════════════════════════════════════════
══════════
# VALIDATION
# ═════════════════════════════════════════════════
══════════
validation_passed: bool
validation_errors: List[str]
defaults_applied: List[str] # V1.1 addition
GENSE Policy Engine 27

# ═════════════════════════════════════════════════
══════════
# HARD BLOCKS
# ═════════════════════════════════════════════════
══════════
hard_blocks_evaluated: List[str]
hard_block_triggered: Optional[str]
hard_block_reason: Optional[str]
hard_block_contract_ref: Optional[str] # V1.1 addition
# ═════════════════════════════════════════════════
══════════
# PRIORITY LOCKS
# ═════════════════════════════════════════════════
══════════
priority_locks_evaluated: List[str]
priority_locks_active: List[str]
lock_stacking_applied: bool # V1.1 addition
actions_after_locks: List[int]
cta_constraints_from_locks: List[str]
cta_exclusions_from_locks: List[str] # V1.1 addition
# ═════════════════════════════════════════════════
══════════
# PRECONDITION EVALUATION
# ═════════════════════════════════════════════════
══════════
preconditions_evaluated: List[PreconditionResult]
candidates_after_preconditions: List[int]
# ═════════════════════════════════════════════════
══════════
# SELECTION
# ═════════════════════════════════════════════════
══════════
GENSE Policy Engine 28

selection_ranking: List[Tuple[int, Tuple]] # V1.1 addition: full sort keys
stall_preference_applied: bool
cta_constraint_rejections: List[Dict] # V1.1 addition
# ═════════════════════════════════════════════════
══════════
# FINAL SELECTION
# ═════════════════════════════════════════════════
══════════
selected_action: int
selection_confidence: float
selection_reason: str
alternatives_considered: List[int]
alternatives_rejection_reasons: Dict[int, str]
# ═════════════════════════════════════════════════
══════════
# TIMESTAMPS
# ═════════════════════════════════════════════════
══════════
evaluation_started_at: str
evaluation_completed_at: str
evaluation_duration_ms: int
7.2 Example Decision Trace
{
"input_state_hash": "a3f2c1e9...",
"thread_id": "thr_2026_0142",
"deal_stage": "evaluation",
"buyer_intent": "question_security",
"open_loop_count" 1,
"risk_level": "medium",
"attribution_confidence" 0.92,
"buyer_role_confidence" 0.88,
GENSE Policy Engine 29

"stage_confidence" 0.85,
"intent_confidence" 0.88,
"validation_passed": true,
"validation_errors": [],
"defaults_applied": ["discovery_questions_remaining", "timeline_known"],
"hard_blocks_evaluated": ["HB_001", "HB_002", "HB_002b", "HB_003", "HB_0
04", "HB_005", "HB_006", "HB_007", "HB_008", "HB_009"],
"hard_block_triggered": null,
"priority_locks_evaluated": ["PL_001", "PL_002", "PL_003", "PL_004", "PL_00
5", "PL_006"],
"priority_locks_active": ["PL_002", "PL_003"],
"lock_stacking_applied": true,
"actions_after_locks": 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
"cta_constraints_from_locks": [],
"cta_exclusions_from_locks": [],
"preconditions_evaluated": [
{"action" 3, "satisfied": true, "confidence" 0.95, "reason": "explicit securit
y question exists"},
{"action" 4, "satisfied": true, "confidence" 0.88, "reason": "can add clarifie
r"},
{"action" 5, "satisfied": false, "reason": "answer available in knowledge ba
se"},
{"action" 6, "satisfied": true, "confidence" 0.92, "reason": "SOC2 report in
asset library"}
],
"candidates_after_preconditions": 3, 4, 6,
"selection_ranking": [
6, 1, 2, 6, 2, 0.92,
3, 1, 2, 3, 0, 0.95,
4, 1, 1, 4, 1, 0.88
],
GENSE Policy Engine 30

"stall_preference_applied": false,
"cta_constraint_rejections": [],
"selected_action" 6,
"selection_confidence" 0.92,
"selection_reason": "highest_ranked_candidate_tier_1",
"alternatives_considered": 3, 4,
"alternatives_rejection_reasons": {
"3": "lower_affinity_for_question_security",
"4": "lower_priority_adds_unnecessary_clarifier"
},
"evaluation_started_at": "20260120T103000.000Z",
"evaluation_completed_at": "20260120T103000.015Z",
"evaluation_duration_ms" 15
}
Part VIII: Worked Examples (V1.1 ADDITION)
Example 1: Simple Discovery Thread (Happy Path)
Input State:
{
"thread_id": "thr_simple_001",
"deal_stage": "discovery",
"attribution_confidence" 0.85,
"buyer_role_confidence" 0.82,
"required_config_missing": false,
"parse_status": "success",
"buyer_intent": "question_product",
"stage_confidence" 0.78,
"intent_confidence" 0.82,
"open_loops": [],
"open_loop_count" 0,
GENSE Policy Engine 31

"risk_level": "low",
"commitment_drift_flag": false,
"total_turns" 4,
"seller_turns" 2,
"days_since_last_buyer" 1,
"last_3_ctas": ["one_question"],
"stakeholder_count" 1
}
Expected Output:
{
"selected_action" 12,
"execution_status": "success",
"selection_reason": "discovery_probe_appropriate_for_stage"
}
Trace Summary:
No hard blocks (all confidences above threshold)
No priority locks active (no open loops, no commitment drift)
Action 12 (single_discovery_probe) selected via intent affinity + stage match
Example 2: High-Priority Open Loop
Input State:
{
"thread_id": "thr_openloop_002",
"deal_stage": "evaluation",
"attribution_confidence" 0.91,
"buyer_role_confidence" 0.89,
"required_config_missing": false,
"parse_status": "success",
"buyer_intent": "question_security",
"stage_confidence" 0.85,
GENSE Policy Engine 32

"intent_confidence" 0.90,
"open_loops": [
{"loop_id": "ol_001", "type": "explicit_question", "priority": "high", "resolutio
n_status": "open", "content": "Do you have SOC2?"}
],
"open_loop_count" 1,
"risk_level": "medium",
"commitment_drift_flag": false,
"answer_available_in_knowledge_base": false,
"enablement_packet_available": true,
"total_turns" 8,
"seller_turns" 4,
"days_since_last_buyer" 0,
"last_3_ctas": ["async_review"],
"stakeholder_count" 2
}
Expected Output:
{
"selected_action" 6,
"execution_status": "success",
"selection_reason": "provide_requested_artifact_for_security_question"
}
Trace Summary:
No hard blocks
PL_002 (open_loop_priority_lock) active → restricts to actions 111
PL_003 (open_loop_soft_lock) active → blocks 1720
Action 6 (provide_requested_artifact) selected: SOC2 is in asset library,
matches question_security intent
Example 3: Commitment Drift (Forced Action)
GENSE Policy Engine 33

Input State:
{
"thread_id": "thr_drift_003",
"deal_stage": "proposal",
"attribution_confidence" 0.88,
"buyer_role_confidence" 0.85,
"required_config_missing": false,
"parse_status": "success",
"buyer_intent": "commitment_request",
"stage_confidence" 0.92,
"intent_confidence" 0.85,
"open_loops": [],
"open_loop_count" 0,
"risk_level": "high",
"commitment_drift_flag": true,
"total_turns" 15,
"seller_turns" 7,
"days_since_last_buyer" 3,
"last_3_ctas": ["calendar_light", "async_review"],
"stakeholder_count" 3
}
Expected Output:
{
"selected_action" 10,
"execution_status": "forced",
"selection_reason": "commitment_recovery_lock_absolute"
}
Trace Summary:
No hard blocks
PL_001 (commitment_recovery_lock) active with effect_type: "absolute"
GENSE Policy Engine 34

Immediately forces Action 10 (recover_missed_commitment)
No further evaluation needed
Example 4: Critical Risk with CTA Constraint
Input State:
{
"thread_id": "thr_critical_004",
"deal_stage": "evaluation",
"attribution_confidence" 0.94,
"buyer_role_confidence" 0.91,
"required_config_missing": false,
"parse_status": "success",
"buyer_intent": "objection_budget",
"stage_confidence" 0.80,
"intent_confidence" 0.88,
"open_loops": [],
"open_loop_count" 0,
"risk_level": "critical",
"commitment_drift_flag": false,
"objection_tags": ["budget_concern", "competitor_mentioned"],
"total_turns" 12,
"seller_turns" 6,
"days_since_last_buyer" 2,
"last_3_ctas": ["none", "async_review"],
"stakeholder_count" 2
}
Expected Output:
{
"selected_action" 3,
"execution_status": "success",
"cta_constraint": {
GENSE Policy Engine 35

"whitelist": ["none", "async_review", "opt_out"]
},
"selection_reason": "answer_question_with_critical_risk_cta_constraint"
}
Trace Summary:
No hard blocks
PL_004 (critical_risk_lock) active → blocks actions 1621, constrains CTAs to
whitelist
Action 21 (objection_reframe) would be primary affinity but is BLOCKED by
critical risk
Falls back to Action 3 (answer_explicit_question) with CTA constrained to
whitelist
Example 5: Hard Block - Low Attribution Confidence
Input State:
{
"thread_id": "thr_blocked_005",
"deal_stage": "discovery",
"attribution_confidence" 0.55,
"buyer_role_confidence" 0.72,
"required_config_missing": false,
"parse_status": "success",
"buyer_intent": "question_product",
"stage_confidence" 0.75,
"intent_confidence" 0.80,
"open_loops": [],
"open_loop_count" 0,
"risk_level": "low",
"commitment_drift_flag": false,
"total_turns" 3,
"seller_turns" 1,
GENSE Policy Engine 36

"stakeholder_count" 1
}
Expected Output:
{
"selected_action" 1,
"execution_status": "blocked",
"reason": "speaker_attribution_unreliable",
"hard_block_triggered": "HB_002",
"contract_ref": "Build Contract A8 attribution_confidence_threshold"
}
Trace Summary:
HB_002 triggered: attribution_confidence 0.55  0.70
Immediately returns Action 1 (escalate_to_human_review)
No lock or precondition evaluation performed
Example 6: Hard Block - Low Buyer Role Confidence (V1.1.1)
Input State:
{
"thread_id": "thr_role_006",
"deal_stage": "evaluation",
"attribution_confidence" 0.85,
"buyer_role_confidence" 0.58,
"required_config_missing": false,
"parse_status": "success",
"buyer_intent": "question_pricing",
"stage_confidence" 0.78,
"intent_confidence" 0.82,
"open_loops": [],
"open_loop_count" 0,
"risk_level": "low",
GENSE Policy Engine 37

"commitment_drift_flag": false,
"total_turns" 6,
"seller_turns" 3,
"stakeholder_count" 2
}
Expected Output:
{
"selected_action" 1,
"execution_status": "blocked",
"reason": "buyer_role_identification_unreliable",
"hard_block_triggered": "HB_002b",
"contract_ref": "Module 02 role gating: buyer_role_confidence_threshold"
}
Trace Summary:
HB_002b triggered: buyer_role_confidence 0.58  0.70
Attribution was fine 0.85 but role inference uncertain
Immediately returns Action 1 (escalate_to_human_review)
This closes the identity gating hole where we know WHO spoke but not
WHICH SIDE they're on
Part IX: Testing Requirements
9.1 Unit Test Cases
Test ID Scenario Expected Action Key Assertion
Empty open loops, low risk,
PE_001 12 No locks active
discovery stage
High-priority open loop PL_002 restricts to
PE_002 3, 4, 5, 6, 7, or 8
exists resolution
GENSE Policy Engine 38

Test ID Scenario Expected Action Key Assertion
PL_001 forces
PE_003 Commitment drift flag true 10 ONLY
absolutely
PL_004 blocks
PE_004 Critical risk level No 1621
progression
PL_006 excludes
PE_005 Same CTA used twice Different CTA
repeated
PE_006 Stage confidence  0.55 1 (escalate) HB_004 triggers
Attribution confidence =
PE_007 1 (escalate) HB_002 triggers
0.65
Buyer role confidence =
PE_007b 1 (escalate) HB_002b triggers
0.65
PL_005 preference
PE_008 14 days no response 23 preferred
applied
PE_009 21 days no response 24 preferred Stall close
PE_010 New stakeholder CC'd 14 stakeholder_redirect
required_config_missing = HB_001 routes to
PE_011 2
true request_context
PE_012 parse_status = "blocked" 1 HB_003 triggers
Multi-lock: PL_002  Intersection of
PE_013 Lock stacking verified
PL_004 allowed
All candidates fail CTA First with "none"
PE_014 Fallback mechanism
check CTA
Gray-zone confidence
PE_015 NOT blocked Above 0.60 threshold
0.62
9.2 Integration Test Scenarios
INTEGRATION_TESTS  
{
"name": "full_happy_path",
"description": "Complete deal progression from triage to close",
"sequence": [
("triage", "question_product", 3,
GENSE Policy Engine 39

("discovery", "information_share", 12,
("discovery", "question_pricing", 3,
("evaluation", "commitment_signal", 16,
("evaluation", "commitment_request", 17,
("proposal", "question_security", 6,
("procurement", "administrative", 18,
]
},
{
"name": "objection_recovery_path",
"description": "Handle budget objection then proceed",
"sequence": [
("evaluation", "objection_budget", 21,
("evaluation", "question_product", 3,
("evaluation", "commitment_signal", 16,
]
},
{
"name": "commitment_recovery_path",
"description": "Miss commitment, recover, then proceed",
"sequence": [
("evaluation", "commitment_request", 17,
# commitment_drift_flag set
("evaluation", "administrative", 10, # Forced recovery
("evaluation", "commitment_signal", 16,
]
},
{
"name": "stall_and_close_path",
"description": "Thread stalls and eventually closes",
"sequence": [
("evaluation", "unclear", 12, # Day 0
# 14 days pass
("evaluation", "unclear", 23, # Nudge
# 7 days pass
("evaluation", "unclear", 23, # Nudge 2
GENSE Policy Engine 40

# 7 days pass
("evaluation", "unclear", 24, # Close
]
},
{
"name": "multi_lock_stacking",
"description": "Multiple locks active simultaneously",
"sequence": [
# High-priority loop + critical risk
("evaluation", "question_security", 6, # Restricted by both locks
]
}
]
Part X: Configuration & Tuning
10.1 Configurable Parameters
ENGINE_CONFIG  
# ═════════════════════════════════════════════════
══════════
# CONFIDENCE THRESHOLDS (per Build Contract A8
# These are the SINGLE SOURCE OF TRUTH
# ═════════════════════════════════════════════════
══════════
"attribution_confidence_threshold" 0.70,
"buyer_role_confidence_threshold" 0.70, # V1.1.1 addition
"stage_confidence_threshold" 0.60,
"intent_confidence_threshold" 0.60,
"precondition_confidence_threshold" 0.70,
# ═════════════════════════════════════════════════
══════════
# TIMING THRESHOLDS
GENSE Policy Engine 41

# ═════════════════════════════════════════════════
══════════
"stall_nudge_days" 14,
"stall_close_days" 21,
"max_nudge_count" 2,
"commitment_warning_hours" 48,
# ═════════════════════════════════════════════════
══════════
# COMPLEXITY LIMITS
# ═════════════════════════════════════════════════
══════════
"max_thread_turns" 100,
"max_open_loops" 5,
"max_stakeholders" 10,
# ═════════════════════════════════════════════════
══════════
# CTA CONSTRAINTS
# ═════════════════════════════════════════════════
══════════
"cta_lookback_count" 3,
"allow_cta_repeat_after_turns" 5,
# ═════════════════════════════════════════════════
══════════
# RISK MODIFIERS
# ═════════════════════════════════════════════════
══════════
"critical_risk_cta_whitelist": ["none", "async_review", "opt_out"],
"high_risk_progression_block" True
}
10.2 Vertical Overrides
Industry packs can override default parameters:
GENSE Policy Engine 42

VERTICAL_OVERRIDES  
"enterprise_software": {
"stall_nudge_days" 10,
"stall_close_days" 30,
"max_stakeholders" 15
},
"smb_saas": {
"stall_nudge_days" 5,
"stall_close_days" 14,
"max_stakeholders" 3
},
"regulated_industry": {
"stage_confidence_threshold" 0.70, # Higher bar
"critical_risk_cta_whitelist": ["none"],
"high_risk_progression_block" True
}
}
Part XI: Integration Verification (V1.1 ADDITION)
11.1 Contract Alignment
Contract Requirement Policy Engine Implementation Status
Build Contract STEP 1 Input
Section 2.3 validate_input() ✓ ALIGNED
Validation
Section 3.1 HARD_BLOCKS with
Build Contract STEP 2 Hard Blocks ✓ ALIGNED
contract thresholds
Build Contract STEP 3 Priority Section 4.2 PRIORITY_LOCKS with
✓ ALIGNED
Locks stacking
Build Contract STEP 4 Precondition
Section 5.5 select_action() step 1 ✓ ALIGNED
Eval
Build Contract STEP 5 Action Section 5.5 select_action() steps
✓ ALIGNED
Selection 35
GENSE Policy Engine 43

Contract Requirement Policy Engine Implementation Status
Build Contract STEP 6 Decision
Section 7.1 DecisionTrace schema ✓ ALIGNED
Trace
Build Contract A8
HB_002 ✓ ALIGNED
attribution_confidence  0.70
Module 02 contract:
HB_002b ✓ ALIGNED
buyer_role_confidence  0.70
Build Contract A8 stage_confidence
HB_004 ✓ ALIGNED
 0.60
Build Contract A8 intent_confidence
HB_005 ✓ ALIGNED
 0.60
Build Contract LOCK 1 Open Loop
PL_002 ✓ ALIGNED
Priority
Build Contract LOCK 2 Commitment
PL_001 (absolute) ✓ ALIGNED
Drift
Build Contract LOCK 3 CTA
PL_006  selection step 5 ✓ ALIGNED
Repetition
11.2 Upstream Module Dependencies
Upstream Module Required Field Default if Missing
Module 02 Thread Ingestion) attribution_confidence FAIL (required)
Module 02 Thread Ingestion) buyer_role_confidence FAIL (required)
Module 02 Thread Ingestion) required_config_missing FAIL (required)
Module 02 Thread Ingestion) parse_status FAIL (required)
Module 03 State Extractor) open_loops[] FAIL (required)
Module 03 State Extractor) commitment_drift_flag FAIL (required)
Module 04 Classifier) stage_confidence FAIL (required)
Module 04 Classifier) intent_confidence FAIL (required)
11.3 Downstream Module Outputs
GENSE Policy Engine 44

Output Field Consumer Module Usage
selected_action Module 07 Message OS Determines GRRIPS arc
cta_constraint Module 07 Message OS Limits CTA selection
decision_trace Module 13 Audit Guide) Replay and verification
execution_status Orchestrator Routing decision
Document Control
Version Date Author Changes
1.0 20250117 System Initial specification
REFORGED 1 Unified confidence
thresholds—validation structural
only, hard blocks own thresholds at
contract values. 2 Clarified lock
stacking semantics with explicit
precedence. 3 Added upstream
gating fields (attribution_confidence,
required_config_missing,
1.1 20260120 Claude
parse_status). (4) Formalized
deterministic tie-breakers. 5 Added
optional fields with defaults to
prevent precondition failures. 6
Added failure mode enumeration
FM_PE_001007. 7 Added 5
worked examples. 8 Added
integration verification section.
PATCH Added buyer_role_confidence
to REQUIRED_FIELDS and HB_002b
hard block ( buyer_role_confidence <
0.70  Action 1 ). Closes identity gating
1.1.1 20260120 Claude
hole where role inference could be
uncertain even with valid attribution.
Contract-aligned, stress-tested,
ready to lock.
End of Policy Engine Specification v1.1
GENSE Policy Engine 45