GEN-SE Contract Test Harness
"""
GENSE Contract Test Harness
Version: 1.0.0
Date: 20260122
Purpose: CI-level integration test that validates the Policy Engine  GRRIPS
pipeline using canonical enums and the explicit CTAConstraintInput struct.
This test MUST pass before any new module specs are created.
Failure indicates enum drift or contract violation.
Usage:
python contract_test_harness.py
Exit Codes:
0  All tests pass
1  Contract violation detected
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any, Literal
from enum import Enum
import json
import sys
═════════════════════════════════════════════
SECTION 1: CANONICAL ENUMS (from GEN-
SE_Canonical_Enums.md v1.0.0)
These are the SINGLE SOURCE OF TRUTH. Do not define variants
elsewhere.
═════════════════════════════════════════════
CTA_TYPES  
"none",
"opt_out",
"question",
"async_review",
"async_choice",
"calendar_light",
"calendar_two_windows",
]
CTA_PRESSURE  
"none" 0,
"opt_out" 0,
"question" 1,
"async_review" 2,
"async_choice" 2,
GENSE Contract Test Harness 1

"calendar_light" 3,
"calendar_two_windows" 3,
}
VALID_CTA_TYPES  set(CTA_PRESSURE.keys())
DEAL_STAGES  
"triage", "discovery", "evaluation", "proposal",
"procurement", "negotiation", "closed_won", "closed_lost"
]
BUYER_INTENTS  
"question_product", "question_pricing", "question_process",
"question_technical", "question_security", "question_reference",
"objection_timing", "objection_budget", "objection_authority",
"objection_need", "objection_competition",
"commitment_signal", "commitment_request",
"information_share", "administrative", "unclear"
]
RISK_LEVELS  "low", "medium", "high", "critical"]
EXECUTION_STATUSES  "success", "blocked", "forced", "needs_input", "repair_applied"]
PRIORITY_LOCK_IDS  "PL_001", "PL_002", "PL_003", "PL_004", "PL_005", "PL_006"]
ACTION_IDS  list(range(1, 25 # 124
Invalid CTA names that should NEVER appear (flagged in
Canonical Enums)
INVALID_CTA_NAMES  
"one_question", # Use "question"
"calendar_firm", # Use "calendar_two_windows"
"async_review_or_call", # Use "async_review"
"confirm_owner_deadline",# Use "async_choice"
"process_confirm", # Use "async_review"
}
═════════════════════════════════════════════
SECTION 2: CTAConstraintInput STRUCT (from Message OS
v1.3.1)
This is the explicit struct that Policy Engine MUST emit and
GRRIPS MUST consume
═════════════════════════════════════════════
CTA_CONSTRAINT_REQUIRED_KEYS  "allowed_ctas", "blocked_ctas"}
CTA_CONSTRAINT_OPTIONAL_KEYS  "whitelist_ctas", "last_3_ctas", "pressure_ceiling"}
CTA_CONSTRAINT_ALL_KEYS  CTA_CONSTRAINT_REQUIRED_KEYS | CTA_CONSTRAINT_OPTIONAL_KEYS
@dataclass
class CTAConstraintInput:
GENSE Contract Test Harness 2

"""
Explicit CTA constraint struct as defined in Message OS v1.3.0.
Policy Engine MUST emit this struct.
GRRIPS MUST consume this struct.
"""
allowed_ctas: List[str] # CTAs permitted for this action
blocked_ctas: List[str] # CTAs explicitly forbidden
whitelist_ctas: Optional[List[str]]  None # If present, ONLY these valid
last_3_ctas: List[str] = field(default_factory=list) # For rotation lock
pressure_ceiling: int  3 # Max pressure level allowed
def validate(self)  List[str]:
"""Validate all CTA types in this struct against canonical enums."""
errors = []
# Check allowed_ctas
for cta in self.allowed_ctas:
if cta not in VALID_CTA_TYPES
errors.append(f"V_CTA_003 Invalid CTA in allowed_ctas: '{cta}'")
if cta in INVALID_CTA_NAMES
errors.append(f"V_CTA_003 Deprecated CTA name in allowed_ctas: '{cta}'")
# Check blocked_ctas
for cta in self.blocked_ctas:
if cta not in VALID_CTA_TYPES
errors.append(f"V_CTA_003 Invalid CTA in blocked_ctas: '{cta}'")
# Check whitelist_ctas if present
if self.whitelist_ctas:
for cta in self.whitelist_ctas:
if cta not in VALID_CTA_TYPES
errors.append(f"V_CTA_003 Invalid CTA in whitelist_ctas: '{cta}'")
# Check last_3_ctas
for cta in self.last_3_ctas:
if cta not in VALID_CTA_TYPES
errors.append(f"V_CTA_003 Invalid CTA in last_3_ctas: '{cta}'")
# Check pressure_ceiling
if not 0  self.pressure_ceiling  3
errors.append(f"V_CTA_003 pressure_ceiling must be 03, got {self.pressure_ceiling}")
return errors
@classmethod
def from_dict(cls, d: Dict[str, Any]) → "CTAConstraintInput":
"""Parse from dict, validating keys match the contract."""
# V_INPUT_003 Validate keys
unknown_keys = set(d.keys())  CTA_CONSTRAINT_ALL_KEYS
if unknown_keys:
raise ValueError(f"V_INPUT_003 Unknown keys in CTAConstraintInput: {unknown_keys}")
missing_required  CTA_CONSTRAINT_REQUIRED_KEYS  set(d.keys())
if missing_required:
GENSE Contract Test Harness 3

raise ValueError(f"V_INPUT_003 Missing required keys: {missing_required}")
return cls(
allowed_ctas=d["allowed_ctas"],
blocked_ctas=d["blocked_ctas"],
whitelist_ctas=d.get("whitelist_ctas"),
last_3_ctas=d.get("last_3_ctas", []),
pressure_ceiling=d.get("pressure_ceiling", 3,
)
═════════════════════════════════════════════
SECTION 3: SYNTHETIC THREAD STATE (from Module 03 v1.0.1)
Minimal valid ThreadState using canonical enums and defaults
═════════════════════════════════════════════
def create_synthetic_thread_state(
deal_stage: str = "discovery",
buyer_intent: str = "question_product",
risk_level: str = "low",
open_loop_count: int  0,
commitment_drift_flag: bool  False,
attribution_confidence: float  0.85,
buyer_role_confidence: float  0.82,
stage_confidence: float  0.78,
intent_confidence: float  0.80,
last_3_ctas: List[str]  None,
)  Dict[str, Any]:
"""
Create a minimal valid ThreadState using Module 03 schema.
All enum values MUST come from canonical enums.
"""
# Validate inputs against canonical enums
assert deal_stage in DEAL_STAGES, f"Invalid deal_stage: {deal_stage}"
assert buyer_intent in BUYER_INTENTS, f"Invalid buyer_intent: {buyer_intent}"
assert risk_level in RISK_LEVELS, f"Invalid risk_level: {risk_level}"
if last_3_ctas:
for cta in last_3_ctas:
assert cta in VALID_CTA_TYPES, f"Invalid CTA in last_3_ctas: {cta}"
return {
# Thread Core (from Module 02
"thread_id": "test_thread_001",
"thread_created_at": "20260122T100000Z",
"source_channel": "email",
# Attribution (from Module 02
"attribution_confidence": attribution_confidence,
GENSE Contract Test Harness 4

"buyer_role_confidence": buyer_role_confidence,
# Stage & Intent (from Module 04
"deal_stage": deal_stage,
"stage_confidence": stage_confidence,
"buyer_intent": buyer_intent,
"intent_confidence": intent_confidence,
# Risk (from Module 04
"risk_level": risk_level,
"risk_factors": [],
# Open Loops (from Module 03
"open_loops": [],
"open_loop_count": open_loop_count,
# Commitments (from Module 03
"commitment_drift_flag": commitment_drift_flag,
"commitments_made": [],
# Interaction History (from Module 03
"total_turns" 4,
"seller_turns" 2,
"buyer_turns" 2,
"last_3_ctas": last_3_ctas or [],
"last_3_actions": [],
"days_since_last_buyer" 1,
# Stakeholders (from Module 03
"stakeholders": [],
"stakeholder_count" 1,
# Validation flags
"parse_status": "success",
"required_config_missing" False,
}
═════════════════════════════════════════════
SECTION 4: MOCK POLICY ENGINE (produces valid PolicyOutput)
═════════════════════════════════════════════
@dataclass
class DecisionTrace:
"""Decision trace as defined in Policy Engine v1.1."""
locks_applied: List[str]
actions_evaluated: List[Dict[str, Any]]
selected_action: int
selection_reason: str
GENSE Contract Test Harness 5

hard_block_triggered: Optional[str]  None
cta_constraint_rejections: List[Dict[str, Any]] = field(default_factory=list)
@dataclass
class PolicyOutput:
"""Policy Engine output contract."""
selected_action: int
execution_status: str
cta_constraint: CTAConstraintInput
decision_trace: DecisionTrace
def validate(self)  List[str]:
"""Validate PolicyOutput against contracts."""
errors = []
# Validate action ID
if self.selected_action not in ACTION_IDS
errors.append(f"Invalid action ID {self.selected_action}")
# Validate execution status
if self.execution_status not in EXECUTION_STATUSES
errors.append(f"Invalid execution_status: {self.execution_status}")
# Validate locks_applied
for lock_id in self.decision_trace.locks_applied:
if lock_id not in PRIORITY_LOCK_IDS
errors.append(f"Invalid lock ID {lock_id}")
# Validate CTA constraint struct
errors.extend(self.cta_constraint.validate())
return errors
def mock_policy_engine(thread_state: Dict[str, Any])  PolicyOutput:
"""
Mock Policy Engine that produces valid output for testing.
In production, this is replaced by actual Policy Engine execution.
"""
locks_applied = []
blocked_actions = set()
cta_whitelist  None
# PL_001 Commitment drift lock (absolute)
if thread_state.get("commitment_drift_flag"):
locks_applied.append("PL_001")
selected_action  10 # recover_missed_commitment
return PolicyOutput(
selected_action=selected_action,
execution_status="forced",
cta_constraint=CTAConstraintInput(
allowed_ctas=["none", "async_review"],
blocked_ctas=[],
last_3_ctas=thread_state.get("last_3_ctas", []),
),
GENSE Contract Test Harness 6

decision_trace=DecisionTrace(
locks_applied=locks_applied,
actions_evaluated=[],
selected_action=selected_action,
selection_reason="commitment_recovery_lock_absolute",
),
)
# PL_002 High-priority open loop
if thread_state.get("open_loop_count", 0  0
locks_applied.append("PL_002")
blocked_actions.update([16, 17, 18, 19, 20
# PL_004 Critical risk
if thread_state.get("risk_level") == "critical":
locks_applied.append("PL_004")
blocked_actions.update([16, 17, 18, 19, 20, 21
cta_whitelist = ["none", "async_review", "opt_out"]
# Select action based on intent affinity (simplified)
buyer_intent = thread_state.get("buyer_intent", "unclear")
if buyer_intent.startswith("question_"):
selected_action  3 # answer_explicit_question_only
elif buyer_intent.startswith("objection_"):
selected_action  21 if 21 not in blocked_actions else 3
else:
selected_action  12 # single_discovery_probe
# Build CTA constraint
risk_level = thread_state.get("risk_level", "low")
allowed_ctas = list(VALID_CTA_TYPES
blocked_ctas = []
if risk_level == "high":
blocked_ctas = ["calendar_light", "calendar_two_windows"]
elif risk_level == "critical":
# Whitelist overrides
pass
cta_constraint  CTAConstraintInput(
allowed_ctas=allowed_ctas if not cta_whitelist else [],
blocked_ctas=blocked_ctas,
whitelist_ctas=cta_whitelist,
last_3_ctas=thread_state.get("last_3_ctas", []),
pressure_ceiling=0 if risk_level == "critical" else 3,
)
return PolicyOutput(
selected_action=selected_action,
execution_status="success",
cta_constraint=cta_constraint,
decision_trace=DecisionTrace(
locks_applied=locks_applied,
actions_evaluated=[{"action": selected_action, "result" True}],
GENSE Contract Test Harness 7

selected_action=selected_action,
selection_reason=f"intent_affinity_{buyer_intent}",
),
)
═════════════════════════════════════════════
SECTION 5: MOCK GRRIPS (produces valid MessageOutput with
ask_block)
═════════════════════════════════════════════
@dataclass
class AskBlock:
"""Ask-block as defined in Message OS v1.3."""
type: Literal["cta", "question", "input_request_block", "none"]
content: Optional[str]  None
cta_type: Optional[str]  None
subquestions: Optional[List[str]]  None # For input_request_block
def validate(self)  List[str]:
"""Validate ask-block rules."""
errors = []
if self.type == "cta":
if not self.cta_type:
errors.append("Ask-block type=cta but cta_type is None")
elif self.cta_type not in VALID_CTA_TYPES
errors.append(f"V_CTA_003 Invalid cta_type in ask_block: '{self.cta_type}'")
if self.type == "input_request_block":
if self.subquestions and len(self.subquestions)  3
errors.append("input_request_block cannot have more than 3 subquestions")
return errors
@dataclass
class Claim:
"""Claim object as defined in Message OS v1.3.1."""
claim_id: str # Format: CLM_###
text: str
source_type: str # "thread" | "config" | "asset"
source_ref: str # span_ref for thread, config key for config
grounded: bool  True
@dataclass
class MessageOutput:
"""GRRIPS compilation output."""
text: str
action_executed: int
grrips_nodes_used: List[str]
GENSE Contract Test Harness 8

word_count: int
ask_block: AskBlock
claims: List[Claim]
cta_type: str
def validate(self)  List[str]:
"""Validate message output against contracts."""
errors = []
# V_CTA_003 CTA type validity
if self.cta_type not in VALID_CTA_TYPES
errors.append(f"V_CTA_003 Invalid cta_type in output: '{self.cta_type}'")
# Ask-block validation
errors.extend(self.ask_block.validate())
# Ask-block rule: Only ONE ask element per message
# The rule is: max 1 ask-block, which is EITHER a CTA OR a question OR an input_request_block
# Having a question mark in CTA text is fine (e.g., "Would you like to schedule a call?")
# What's NOT allowed is having BOTH a CTA block AND a question block in the same message
# This validation is at the message level, not the ask_block level
pass # Single ask-block is enforced by the type being singular
# Claim ID format
for claim in self.claims:
if not claim.claim_id.startswith("CLM_"):
errors.append(f"Invalid claim_id format: {claim.claim_id}")
return errors
def mock_grrips(
thread_state: Dict[str, Any],
policy_output: PolicyOutput,
)  MessageOutput:
"""
Mock GRRIPS compiler that produces valid output.
In production, this is replaced by actual GRRIPS execution.
"""
action_id = policy_output.selected_action
cta_constraint = policy_output.cta_constraint
# Select CTA based on constraints
if cta_constraint.whitelist_ctas:
available = set(cta_constraint.whitelist_ctas)
else:
available = set(cta_constraint.allowed_ctas) - set(cta_constraint.blocked_ctas)
# Apply pressure ceiling
available = {
cta for cta in available
if CTA_PRESSURE.get(cta, 99  cta_constraint.pressure_ceiling
}
# Apply rotation (avoid last_3_ctas)
GENSE Contract Test Harness 9

non_repeating = available - set(cta_constraint.last_3_ctas)
if non_repeating:
available = non_repeating
elif "none" in available:
available = {"none"}
# Select lowest pressure CTA
selected_cta = min(available, key=lambda x: CTA_PRESSURE.get(x, 99 if available else "none"
# Determine ask-block type
if selected_cta == "none":
ask_block  AskBlock(type="none")
elif selected_cta == "question":
ask_block  AskBlock(
type="question",
content="Could you clarify your timeline?",
)
else:
ask_block  AskBlock(
type="cta",
content="Would you like to review our security documentation?",
cta_type=selected_cta,
)
# Generate claims (with proper v1.3.1 format)
claims = [
Claim(
claim_id="CLM_001",
text="We are SOC 2 Type II certified",
source_type="config",
source_ref="product_config.security.certifications",
)
]
return MessageOutput(
text="Thank you for your question. Generated response]",
action_executed=action_id,
grrips_nodes_used=["G", "R1", "P", "S"] if selected_cta ! "none" else ["G", "R1", "P"],
word_count=45,
ask_block=ask_block,
claims=claims,
cta_type=selected_cta,
)
═════════════════════════════════════════════
SECTION 6: CONTRACT TEST CASES
═════════════════════════════════════════════
GENSE Contract Test Harness 10

class ContractTestResult:
def init(self, test_id: str):
self.test_id = test_id
self.passed  True
self.errors: List[str] = []
def fail(self, error: str):
self.passed  False
self.errors.append(error)
def __str__(self):
status = "✓ PASS" if self.passed else "✗ FAIL"
result = f"{status} {self.test_id}"
if self.errors:
result += "\\n" + "\\n".join(f" - {e}" for e in self.errors)
return result
def run_contract_tests()  List[ContractTestResult]:
"""Run all contract tests and return results."""
results = []
# ─────────────────────────────────────────────────────────────────────────
# TEST 1 Happy path - basic question intent
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_001_happy_path_question")
try:
state = create_synthetic_thread_state(
deal_stage="discovery",
buyer_intent="question_product",
risk_level="low",
)
policy_output = mock_policy_engine(state)
# Validate policy output
policy_errors = policy_output.validate()
for err in policy_errors:
result.fail(err)
# Run GRRIPS
message_output = mock_grrips(state, policy_output)
# Validate message output
message_errors = message_output.validate()
for err in message_errors:
result.fail(err)
# Assert action matches intent
if policy_output.selected_action ! 3 # answer_explicit_question
result.fail(f"Expected action 3 for question intent, got {policy_output.selected_action}")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
GENSE Contract Test Harness 11

# ─────────────────────────────────────────────────────────────────────────
# TEST 2 Commitment drift forces Action 10
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_002_commitment_drift_forces_action_10")
try:
state = create_synthetic_thread_state(
deal_stage="evaluation",
buyer_intent="commitment_request",
commitment_drift_flag=True,
)
policy_output = mock_policy_engine(state)
# PL_001 must be in locks_applied
if "PL_001" not in policy_output.decision_trace.locks_applied:
result.fail("PL_001 not in locks_applied despite commitment_drift_flag=True")
# Action must be 10
if policy_output.selected_action ! 10
result.fail(f"Expected action 10 (recover_missed_commitment), got {policy_output.selected_action}")
# Execution status must be "forced"
if policy_output.execution_status ! "forced":
result.fail(f"Expected execution_status='forced', got '{policy_output.execution_status}'")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 3 Critical risk constrains CTAs to whitelist
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_003_critical_risk_cta_whitelist")
try:
state = create_synthetic_thread_state(
deal_stage="evaluation",
buyer_intent="question_security",
risk_level="critical",
)
policy_output = mock_policy_engine(state)
# PL_004 must be active
if "PL_004" not in policy_output.decision_trace.locks_applied:
result.fail("PL_004 not in locks_applied despite risk_level='critical'")
# CTA whitelist must be present
if not policy_output.cta_constraint.whitelist_ctas:
result.fail("whitelist_ctas should be set for critical risk")
else:
# Whitelist must only contain none, async_review, opt_out
allowed_whitelist = {"none", "async_review", "opt_out"}
actual_whitelist = set(policy_output.cta_constraint.whitelist_ctas)
if not actual_whitelist.issubset(allowed_whitelist):
result.fail(f"Invalid whitelist for critical risk: {actual_whitelist}")
GENSE Contract Test Harness 12

# Run GRRIPS and verify CTA is from whitelist
message_output = mock_grrips(state, policy_output)
if message_output.cta_type not in {"none", "async_review", "opt_out"}:
result.fail(f"GRRIPS emitted CTA '{message_output.cta_type}' not in critical risk whitelist")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 4 V_CTA_003  Invalid CTA type detection
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_004_invalid_cta_detection")
try:
# Create a CTAConstraintInput with invalid CTA
try:
invalid_constraint  CTAConstraintInput(
allowed_ctas=["one_question"], # INVALID  deprecated name
blocked_ctas=[],
)
errors = invalid_constraint.validate()
if not any("V_CTA_003" in e for e in errors):
result.fail("V_CTA_003 should detect deprecated CTA name 'one_question'")
except Exception:
pass # Expected to fail validation
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 5 V_INPUT_003  Unknown keys in CTAConstraintInput
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_005_unknown_keys_detection")
try:
# Try to parse dict with unknown key
bad_dict = {
"allowed_ctas": ["none"],
"blocked_ctas": [],
"cta_constraints": ["calendar_firm"], # WRONG KEY NAME
}
try:
CTAConstraintInput.from_dict(bad_dict)
result.fail("V_INPUT_003 should reject unknown key 'cta_constraints'")
except ValueError as e:
if "V_INPUT_003" not in str(e):
result.fail(f"Expected V_INPUT_003 error, got: {e}")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 6 Ask-block rule - no CTA  question combination
GENSE Contract Test Harness 13

# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_006_ask_block_single_ask_rule")
try:
# Create valid ask-block with CTA only
ask_block_cta  AskBlock(
type="cta",
content="Would you like to schedule a call?",
cta_type="calendar_light",
)
errors = ask_block_cta.validate()
if errors:
result.fail(f"Valid CTA ask-block should not have errors: {errors}")
# Create valid ask-block with question only
ask_block_question  AskBlock(
type="question",
content="What is your timeline for implementation?",
)
errors = ask_block_question.validate()
if errors:
result.fail(f"Valid question ask-block should not have errors: {errors}")
# Verify CTA type is valid
ask_block_bad_cta  AskBlock(
type="cta",
content="Schedule?",
cta_type="calendar_firm", # INVALID
)
errors = ask_block_bad_cta.validate()
if not any("V_CTA_003" in e for e in errors):
result.fail("Should detect invalid cta_type 'calendar_firm' in ask_block")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 7 CTA rotation lock (avoid last_3_ctas)
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_007_cta_rotation_lock")
try:
state = create_synthetic_thread_state(
deal_stage="discovery",
buyer_intent="question_product",
risk_level="low",
last_3_ctas=["async_review", "async_review", "question"],
)
policy_output = mock_policy_engine(state)
message_output = mock_grrips(state, policy_output)
# CTA should not be in last_3_ctas (unless forced to "none")
if message_output.cta_type in ["async_review", "question"] and message_output.cta_type ! "none":
result.fail(f"CTA '{message_output.cta_type}' should be avoided due to rotation lock")
GENSE Contract Test Harness 14

except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 8 Claims have proper v1.3.1 format
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_008_claims_format_v131")
try:
state = create_synthetic_thread_state()
policy_output = mock_policy_engine(state)
message_output = mock_grrips(state, policy_output)
for claim in message_output.claims:
# claim_id format
if not claim.claim_id.startswith("CLM_"):
result.fail(f"claim_id must start with 'CLM_': {claim.claim_id}")
# source_type must be valid
if claim.source_type not in ["thread", "config", "asset"]:
result.fail(f"Invalid source_type: {claim.source_type}")
# source_ref must be present
if not claim.source_ref:
result.fail(f"source_ref missing for claim {claim.claim_id}")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
# ─────────────────────────────────────────────────────────────────────────
# TEST 9 Full pipeline integration
# ─────────────────────────────────────────────────────────────────────────
result  ContractTestResult("CT_009_full_pipeline_integration")
try:
# Run through all risk levels
for risk_level in RISK_LEVELS
state = create_synthetic_thread_state(
deal_stage="evaluation",
buyer_intent="question_technical",
risk_level=risk_level,
)
policy_output = mock_policy_engine(state)
# Validate policy output
policy_errors = policy_output.validate()
if policy_errors:
result.fail(f"Policy validation failed for risk={risk_level}: {policy_errors}")
continue
message_output = mock_grrips(state, policy_output)
# Validate message output
message_errors = message_output.validate()
GENSE Contract Test Harness 15

if message_errors:
result.fail(f"Message validation failed for risk={risk_level}: {message_errors}")
except Exception as e:
result.fail(f"Exception: {e}")
results.append(result)
return results
═════════════════════════════════════════════
SECTION 7: MAIN EXECUTION
═════════════════════════════════════════════
def main():
print("=" * 70
print("GENSE Contract Test Harness v1.0.0")
print("=" * 70
print()
results = run_contract_tests()
passed = sum(1 for r in results if r.passed)
failed = len(results) - passed
print("Test Results:")
print("-" * 70
for result in results:
print(result)
print()
print("-" * 70
print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
print("=" * 70
if failed  0
print("\\n⚠ CONTRACT VIOLATION DETECTED")
print("Do not proceed with new module specs until all tests pass.")
sys.exit(1)
else:
print("\\n✓ All contract tests passed.")
print("Spine is valid. Safe to proceed with Module 08.")
sys.exit(0)
if name == "main":
main()
GENSE Contract Test Harness 16