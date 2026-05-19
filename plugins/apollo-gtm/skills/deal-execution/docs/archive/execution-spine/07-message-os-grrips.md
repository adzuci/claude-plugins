GEN-SE Message OS (GRRIPS)
Module: 07
Version: 1.3.1
Status: LOCKED
Last Updated: 20260121
Author: Claude
Contract Reference: Build Contract B2 Step 5, Build Index Section 07
Document Control
Version Date Author Changes
Initial specification with 13-section
template. Includes: GRRIPS node
definitions, arc mappings for all 24
actions, length limits, forbidden
1.0.0 20260120 Claude patterns, tone calibration, ask-block
rule, stakeholder addressing, open
loop integration, commitment
recovery, CTA constraint honoring,
test vectors.
1.1.0 20260120 Claude REFORGED as deterministic
compiler: 1 Reframed GRRIPS as
compile step, not writing guidance.
2 Added node-level validators with
compile-time failure. 3 Introduced 4
compile variants: standard, answer-
first, open-loop-priority, trust-repair.
4 Added node-addressable drift
tags for surgical repair (#break-R1,
#weak-P, etc.). 5 Tightened node
definitions with explicit constraints
and validators. 6 Added proof
primitive rules for P node. 7
Clarified auto-swap logic for CTA
failures. 8 Added node_map to
GENSE Message OS GRRIPS 1

Version Date Author Changes
output for drift repair. 9 Updated
failure codes from FM_MO_* to V_*
validator pattern.
BEHAVIORAL LAYER 1 Added
cognitive threshold model—each
node maps to a human decision gate
("Should I pay attention?" → "What's
the safest next step?"). 2 Added
"Human Question Being Answered"
column to node definitions table. 3
Formalized recursion principle:
resistance = broken/skipped node,
not need for pressure. 4 Added
1.2.0 20260120 Claude
Section 1.1 "Behavioral Foundation"
explaining psychological basis. 5
Added Section 1.3 "What GRRIPS
Does NOT Do" (boundary
clarification). (6) Added
advancement rule: conversation
advances ONLY when current
threshold is satisfied. 7 Updated
core terms with cognitive threshold
and recursion definitions.
1.3.0 20260120 Claude CONTRACT TIGHTENING Audit R2
Implementation): (1) Boundary
Amendment: Reworded Section 1
guarantees—compiler "enables"
validation, does not perform it;
added Section 1.0.2 Boundary
Clarification. 2 CTA Constraint
Struct: Replaced generic
cta_constraint blob with explicit
CTAConstraintInput struct Section
4.1; added validate_cta_constraint()
function; added V_INPUT_004 and
V_CTA_003 validators. 3 Lock-
Driven Variant Selection: Rewrote
select_compile_variant() to derive
GENSE Message OS GRRIPS 2

Version Date Author Changes
from locks_applied, not re-evaluate
from state Section 3.5; added
variant_derived_from to trace output.
4 Ask-Block Object: Added explicit
ask_block object to output schema
Section 5.1; added
build_ask_block() and
validate_ask_block() functions;
added V_ASK_002 validator. 5 Test
Vectors: Added lock→variant
mapping tests TV_VAR_), CTA
constraint struct tests TV_CTA_),
ask-block output tests TV_ASK_*).
6 Execution Sequence: Updated
pipeline diagram with v1.3.0 steps.
SCHEMA PATCH (no behavioral
changes): (1) Enriched draft.claims[]
with claim_id (deterministic CLM_###
sequence), span_ref (thread anchor
pointer), source_ref (config key or
asset_id). Backward compatible—
claim and source fields unchanged.
2 Added asset_id to proof_insert for
1.3.1 20260121 Claude
deterministic Module 08 validation.
3 Added test vectors
TV_CLAIM_001 and TV_PROOF_002
for enriched schemas. 4 Updated
downstream consumer table for
Module 08 contract. Required by
Module 08 for deterministic audit
replay.
Part I: Foundation
1. Purpose
GRRIPS is a deterministic message compiler—not writing guidance. It transforms:
GENSE Message OS GRRIPS 3

(selected_action, thread_state, cta_constraints)  GRRIPS-compliant draft
And emits an auditable artifact bundle:
draft.text  The compiled message text
draft.node_map  Line → node mapping for drift repair
draft.cta_type  For CTA repetition locks
draft.ask_block  Explicit ask structure for mechanical validation (v1.3.0
draft.claims[]  Claims with stable identifiers and source references for
Module 08 validation (v1.3.1
generation_trace  Node-by-node rationale + which locks/validators fired
Core Principle: "Compile, don't compose." Every node is a constraint to satisfy,
not prose to write. Generation either passes all validators and emits a draft, or fails
explicitly with blocked status and failure reasons.
1.0.1 Compiler Guarantees (v1.3.0 AMENDED)
The compiler guarantees:
Every message follows the correct arc for its action
All node-level validators pass (compile-time, not review-time)
Single ask-block rule is enforced
CTA pressure ceiling is honored
CTA rotation lock is respected
Proof primitives are emitted with source tags AND asset_ids, enabling Module
08 validation (v1.3.1 added asset_id)
Claims are emitted with stable identifiers (claim_id) and source references for
deterministic audit replay (v1.3.1 added)
Compiler obeys Policy Engine lock outputs; it does not independently evaluate
lock conditions (v1.3.0 added)
Open loop content is integrated per arc rules when PL_002 lock is active
GENSE Message OS GRRIPS 4

Commitment drift triggers trust-repair variant when PL_001 lock is present in
locks_applied
1.0.2 Boundary Clarification (v1.3.0 ADDITION)
What GRRIPS does:
Compiles selected_action into correctly structured message
Emits artifacts that enable downstream validation
Obeys constraints passed from Policy Engine
What GRRIPS does NOT do:
Validate claims Module 08's responsibility)
Detect drift patterns Module 09's responsibility)
Evaluate lock conditions Module 06's responsibility)
Perform attribution pass on claims Module 08's responsibility) (v1.3.1 added)
1.1 Behavioral Foundation
GRRIPS exists because sales conversations fail predictably when cognitive
thresholds are skipped.
Each node in GRRIPS maps to a question the human must answer affirmatively
before the conversation can advance:
Node Human Question
G Grab) "Should I pay attention to this?"
R1 Relate) "Does this person understand my situation?"
R2 Reinforce) "Is there something bigger at stake?"
I Identify) "Do they know what I actually need?"
P Present) "Can they actually help me?"
S Suggest) "What's the safest next step?"
GRRIPS is recursive by design. Advancement is not linear.
Key principle:
GENSE Message OS GRRIPS 5

Resistance is a signal of a broken or skipped node, not a call to push harder.
When resistance, confusion, or disengagement appears, the system loops back to
the last node that restores attention, relevance, necessity, or clarity. This is why
drift repair is node-addressable—we don't rewrite the whole message, we rebuild
from the broken threshold.
1.3 What GRRIPS Does NOT Do
GRRIPS never decides what to do. That's the Policy Engine's job.
GRRIPS only decides how the selected action is expressed safely and
correctly.
GRRIPS is not a script. It's a behavioral constraint system.
GRRIPS does not validate claims—it emits claims with source tags for Module
08 to validate. (v1.3.0
GRRIPS does not evaluate lock conditions—it derives variant from
locks_applied. (v1.3.0
2. Scope
2.1 In Scope
Variant selection: Derive compile path from locks_applied (standard / answer-
first / open-loop / trust-repair) (v1.3.0 "derive from locks" not "choose")
Node compilation: Compile each node per variant rules
Node validation: Run compile-time validators (fail fast, not warn)
CTA compilation: Select CTA honoring explicit constraint struct, pressure
ceiling, rotation lock
Auto-swap logic: One retry with swapped CTA if CTA fails validation
Proof primitive insertion: Exactly one proof in P node if allowed; emit with
source tags AND asset_ids (v1.3.1
Claim extraction: Extract claims with stable identifiers, source references, and
span pointers (v1.3.1
GENSE Message OS GRRIPS 6

Node map emission: Line → node mapping for drift repair
Ask-block emission: Explicit ask_block object for mechanical validation
(v1.3.0
Generation trace: Full audit trail of compilation decisions
2.2 Out of Scope
Action selection (handled by Module 06  Policy Engine)
Open loop extraction (handled by Module 03  State Extractor)
Commitment drift detection (handled by Module 03
Claims grounding validation (handled by Module 08  Claims Policy) (v1.3.0
emphasized)
Claims attribution pass (handled by Module 08  Claims Policy) (v1.3.1 added)
Drift detection and repair execution (handled by Module 09  Drift Monitor)
(v1.3.0 emphasized)
Final output packaging (handled by orchestrator)
Lock condition evaluation (handled by Module 06  Policy Engine) (v1.3.0
added)
2.3 Module Responsibility Separation
Concern Module 07 Responsibility Other Module
Open loops INTEGRATE in P node per arc rules Module 03 EXTRACTS
TRIGGER trust-repair variant when PL_001
Commitments Module 03 DETECTS drift
in locks_applied
COMPILE with explicit constraint struct + Module 06 PROVIDES
CTA selection
auto-swap constraints
EMIT with claim_id, source, span_ref, Module 08 VALIDATES
Claims
source_ref (v1.3.1 grounding
Module 09 TAGS broken
Drift repair EMIT node_map for surgical repair
node
GENSE Message OS GRRIPS 7

Concern Module 07 Responsibility Other Module
Module 06 EVALUATES
Lock evaluation OBEY locks_applied
conditions
3. Definitions
3.1 Core Terms
Term Definition
Recursive behavioral operating system for sales conversations.
GRRIPS Compiles actions into messages that satisfy cognitive thresholds: Grab
 Relate  Reinforce  Identify  Present  Suggest.
A cognitive threshold + compiled constraint. Each node answers a
Node
specific human question.
Arc The sequence of nodes required for a given action type
Cognitive
The human decision gate that must be satisfied before advancement
Threshold
A single request element: one CTA, one question, OR one input request
Ask-block
block
CTA Call to action—the single ask in a message
Input request
Up to 3 related sub-questions that count as ONE ask-block
block
When resistance occurs, loop back to the broken node rather than
Recursion
pushing forward
locks_applied List of Policy Engine lock IDs that fired during action selection (v1.3.0
Stable identifier for a claim, format CLM_### generated in compile order
claim_id
(v1.3.1
Pointer to thread span for thread-sourced claims, format
span_ref
turn_{n}:char_{start}:{end} (v1.3.1
source_ref Config key or asset_id for config/asset-sourced claims (v1.3.1
3.2 GRRIPS Node Definitions (Behavioral + Compiled)
GENSE Message OS GRRIPS 8

Each node is both a cognitive threshold (behavioral) and a compiled constraint
(operational).
Human
Node Name Constraint Validator
Question
Must contain
"Should I pay Earn attention concrete
G Grab
attention?" without hype reference to
buyer's situation
"Do they Must reference
Demonstrate
R1 Relate understand specific buyer
understanding
me?" context
"Is this worth Elevate stakes Must connect to
R2 Reinforce
my time?" appropriately business impact
Must articulate
"Do they know Name the
I Identify buyer's actual
what I need?" specific need
requirement
"Can they Offer relevant Must match offer
P Present
help?" value to identified need
Must be single,
"What should I Propose safe
S Suggest clear, low-friction
do?" next step
ask
3.3 Claim Extraction (v1.3.1 ADDITION)
Claims are extracted during node compilation with stable identifiers:
def extract_claim(
claim_text: str,
source: str,
compile_index: int,
thread_state: dict,
product_config: dict,
enablement_assets: list
) → dict:
"""
Extract a claim with stable identifier and source reference.
GENSE Message OS GRRIPS 9

v1.3.1 Deterministic claim_id generation for audit replay.
"""
claim = {
"claim_id": f"CLM_{compile_index:03d}", # Deterministic sequence
"claim": claim_text,
"source": source, # "thread" | "config" | "asset" | "derived" | "unknown"
"span_ref" None,
"source_ref" None,
"grounded" None # Set by Module 08
}
# Add span_ref for thread-sourced claims
if source == "thread":
span = find_thread_span(claim_text, thread_state.get("turns", []))
if span:
claim["span_ref"] = f"turn_{span['turn']}:char_{span['start']}:{span['en
d']}"
# Add source_ref for config-sourced claims
elif source == "config":
config_key = find_config_key(claim_text, product_config)
if config_key:
claim["source_ref"] = config_key
# Add source_ref for asset-sourced claims
elif source == "asset":
asset = find_asset_match(claim_text, enablement_assets)
if asset:
claim["source_ref"] = asset.get("asset_id")
return claim
3.4 Proof Insert with Asset ID (v1.3.1 ADDITION)
Proof inserts now include explicit asset_id for deterministic validation:
GENSE Message OS GRRIPS 10

def build_proof_insert(
proof_class: str,
proof_content: str,
buyer_role: str,
enablement_assets: list
) → dict | None:
"""
Build proof insert with asset_id for Module 08 validation.
v1.3.1 Added asset_id for deterministic lookup.
"""
# Find matching asset
matching_asset  None
for asset in enablement_assets:
if asset.get("type") == proof_class:
if buyer_role in asset.get("personas", []):
matching_asset = asset
break
if not matching_asset:
return None
return {
"proof_class": proof_class,
"proof_content": proof_content,
"persona_match": buyer_role in matching_asset.get("personas", []),
"source_tag": matching_asset.get("source_tag"),
"asset_id": matching_asset.get("asset_id") # v1.3.1 Required
}
3.5 Variant Selection (v1.3.0: LOCK-DRIVEN)
def select_compile_variant(policy_output: dict, thread_state: dict) → str:
"""
Variant selection is a PURE FUNCTION of Policy Engine outputs.
GENSE Message OS GRRIPS 11

This ensures GRRIPS does not re-evaluate conditions upstream has resolve
d.
Priority order: trust-repair > open-loop-priority > answer-first > standard
"""
locks_applied = set(policy_output.get("decision_trace", {}).get("locks_applie
d", []))
# Priority 1 Trust repair (commitment drift lock was active)
if "PL_001" in locks_applied:
return "trust-repair"
# Priority 2 Open loop priority (open loop lock was active)
if "PL_002" in locks_applied:
return "open-loop-priority"
# Priority 3 Answer-first (question intent, no special locks)
buyer_intent = thread_state.get("buyer_intent", "")
if buyer_intent.startswith("question_"):
return "answer-first"
# Default: Standard compilation
return "standard"
4. Inputs
4.1 CTA Constraint Input (v1.3.0: EXPLICIT STRUCT)
CTAConstraintInput = {
"allowed_ctas": list[str], # CTAs permitted for this action
"blocked_ctas": list[str], # CTAs explicitly forbidden
"whitelist_ctas": list[str] | None, # If present, ONLY these CTAs valid (overri
des allowed/blocked)
"last_3_ctas": list[str], # Previous 3 CTAs for rotation lock
GENSE Message OS GRRIPS 12

"pressure_ceiling": int # 0=none, 1=question, 2=async, 3=calendar
}
4.2 Thread State Input
ThreadStateInput = {
# Identity context
"latest_buyer_name": str,
"latest_buyer_content": str,
"buyer_intent": str,
"buyer_role": str,
"risk_level": str,
# Thread context
"turns": list[dict], # For span_ref extraction (v1.3.1
"open_loops": list[dict],
"commitment_drift_flag": bool,
"stakeholders": list[dict],
# Content context
"product_config": dict, # For config claim source_ref (v1.3.1
"enablement_assets": list, # For asset claim source_ref and proof asset_i
d (v1.3.1
# Recovery context
"missed_commitment_content": str | None,
"latest_buyer_question": str | None
}
4.3 Policy Output Input
PolicyOutputInput = {
"selected_action": int, # 124
"cta_constraint" CTAConstraintInput,
"decision_trace": {
GENSE Message OS GRRIPS 13

"locks_applied": list[str] # Required for variant selection (v1.3.0
}
}
4.4 Input Validation (v1.3.0: AMENDED)
def validate_input(policy_output: dict, thread_state: dict)  ValidationResult:
"""
Validate all inputs before processing.
v1.3.0 Added locks_applied and CTA constraint struct validation.
"""
errors = []
warnings = []
# Required Policy Engine fields
if "selected_action" not in policy_output:
errors.append("MISSING policy_output.selected_action")
elif not isinstance(policy_output["selected_action"], int):
errors.append("INVALID selected_action must be integer")
elif not 1  policy_output["selected_action"]  24
errors.append("INVALID selected_action must be 124")
# v1.3.0 Require decision_trace with locks_applied
decision_trace = policy_output.get("decision_trace", {})
if "locks_applied" not in decision_trace:
errors.append("MISSING policy_output.decision_trace.locks_applied V_I
NPUT_003"
# v1.3.0 Validate CTA constraint struct
cta_errors = validate_cta_constraint(policy_output.get("cta_constraint", {}))
errors.extend(cta_errors)
# v1.3.1 Warn if enablement_assets missing (needed for proof asset_id)
if not thread_state.get("enablement_assets"):
warnings.append("WARNING thread_state.enablement_assets empty—p
GENSE Message OS GRRIPS 14

roof inserts disabled")
if errors:
return ValidationResult(valid=False, errors=errors, warnings=warnings)
return ValidationResult(valid=True, errors=[], warnings=warnings)
5. Outputs
5.1 Success Output Schema (v1.3.1: AMENDED)
OUTPUT_SCHEMA  
"draft": {
"text": str, # Full compiled message text
"nodes_used": list[str], # ["G", "R1", "P", "S"]
"node_content": { # Individual node text for debugging
"G": str | None,
"R1": str | None,
"R2": str | None,
"I": str | None,
"P": str | None,
"S": str | None
},
"node_map": { # Line → node mapping for drift repair
1 "G",
2 "R1",
3 "P",
# ... etc
},
"word_count": int,
"cta_type": str, # The CTA type used (or "none")
"cta_text": str | None, # The actual CTA sentence
"ask_block_count": int, # Must be  1
GENSE Message OS GRRIPS 15

# v1.3.0 Explicit ask_block object for mechanical validation
"ask_block": {
"type": str, # "cta" | "question" | "input_request_block" | "non
e"
"cta_type": str | None, # If type == "cta", the CTA type
"question_text": str | None, # If type == "question", the question
"subquestions": list[str] | None, # If type == "input_request_block" (m
ax 3
"node": str # Which GRRIPS node contains the ask ("S" typic
ally)
},
# v1.3.1 Enriched claims schema for Module 08 deterministic validation
"claims": [
{
"claim_id": str, # Stable identifier: "CLM_001", "CLM_002", etc.
# Generated deterministically in compile order
"claim": str, # The claim text
"source": str, # "thread" | "config" | "asset" | "derived" | "unkn
own"
"span_ref": str | None, # Thread span pointer (if thread-sourced)
# Format: "turn_{n}:char_{start}:{end}" or None
"source_ref": str | None, # Required for config (config key) and asse
t (asset_id)
# Null for thread/derived/unknown
"grounded": bool | None # Set by Module 08, not Module 07
}
],
# v1.3.1 Enriched proof_insert with asset_id
"proof_insert": {
"proof_class": str, # "case_study" | "metric" | "testimonial" | None
"proof_content": str | None,
"persona_match": bool,
"source_tag": str, # v1.3.0 Required source tag
"asset_id": str # v1.3.1 Canonical asset identifier for Module 08
GENSE Message OS GRRIPS 16

validation
 | None
},
"generation_trace": {
"action_executed": int,
"variant_selected": str, # "standard" | "answer-first" | "open-loop-pri
ority" | "trust-repair"
"variant_derived_from": list[str], # v1.3.0 Which locks drove variant sele
ction
"arc_selected": str, # e.g., "GR1PS"
"length_category": str, # "default" | "technical" | "procurement" | "di
scovery" | "follow-up"
"length_limit": int,
"tone_calibration": str, # "warm" | "helpful" | "careful" | "minimal"
"validators_passed": list[str], # ["V_NODE_001", "V_ASK_001", ...]
"auto_swap_triggered": bool, # True if CTA was auto-swapped
"auto_swap_from": str | None, # Original CTA if swapped
"auto_swap_to": str | None, # New CTA if swapped
"forbidden_patterns_checked": int,
"cta_constraint_applied": bool,
"cta_constraint_struct": dict, # v1.3.0 Echo back the constraint struct for
audit
"open_loops_addressed": int,
"stakeholders_acknowledged": list[str],
"claims_extracted": int # v1.3.1 Count of claims extracted
},
"status": "success"
}
5.2 Failure Output Schema
FAILURE_OUTPUT  
"draft" None,
GENSE Message OS GRRIPS 17

"generation_trace": {
"action_attempted": int,
"variant_attempted": str,
"variant_derived_from": list[str], # v1.3.0
"failure_point": str, # Which step/validator failed
"failure_code": str, # "V_ASK_001", "V_CTA_001", etc.
"failure_reason": str,
"auto_swap_attempted": bool,
"auto_swap_failed_reason": str | None,
"cta_constraint_struct": dict # v1.3.0 For debugging constraint failures
},
"status": "blocked",
"failure_reasons": list[str], # All reasons for audit
"fallback_action" 1 # escalate_to_human_review
}
Part III: Deterministic Rules
6. Execution Sequence
┌───────────────────────────────────────────────────
──────────────────────┐
│ GRRIPS COMPILER PIPELINE │
│ v1.3.1 │
├───────────────────────────────────────────────────
──────────────────────┤
│ │
│ STEP 1 VALIDATE INPUT │
│ ├── Check required fields present │
│ ├── Verify selected_action in range 124 │
│ ├── Validate decision_trace.locks_applied present (v1.3.0 │
│ ├── Validate CTA constraint struct (v1.3.0 │
│ └── IF validation fails  EMIT blocked + fallback_action: 1 │
│ │
GENSE Message OS GRRIPS 18

│ STEP 2 SELECT COMPILE VARIANT (v1.3.0 LOCKDRIVEN │
│ ├── Extract locks_applied from decision_trace │
│ ├── IF "PL_001" in locks_applied → trust-repair │
│ ├── ELIF "PL_002" in locks_applied → open-loop-priority │
│ ├── ELIF intent IN question_* → answer-first │
│ └── ELSE  standard │
│ └── Log variant_derived_from to trace │
│ │
│ STEP 3 SELECT ARC (modified by variant) │
│ ├── Look up action in ARC_MAPPINGS │
│ ├── Apply variant arc modifications │
│ └── Log variant_selected, arc_selected to trace │
│ │
│ STEP 4 DETERMINE CONSTRAINTS │
│ ├── Length category (default/technical/procurement/discovery) │
│ ├── Tone calibration (warm/helpful/careful/minimal) │
│ ├── CTA pressure ceiling from cta_constraint.pressure_ceiling │
│ └── CTA rotation exclusions from cta_constraint.last_3_ctas │
│ │
│ STEP 5 COMPILE NODES │
│ ├── Initialize claim_index  1 │
│ ├── For each node in arc: │
│ │ ├── Apply variant-specific node behavior │
│ │ ├── Run node validator FAIL FAST if invalid) │
│ │ ├── Build node_map (line → node) │
│ │ └── Extract claims with claim_id, span_ref, source_ref (v1.3.1 │
│ │ └── claim_id = f"CLM_{claim_index:03d}"; claim_index++ │
│ ├── If P node: apply proof primitive rules │
│ │ └── Exactly ONE proof insert if allowed, WITH source tag + asset_id│
│ └── Assemble node_content dictionary │
│ │
│ STEP 6 COMPILE CTA S node) │
│ ├── IF arc includes S node: │
│ │ ├── IF whitelist_ctas present → use whitelist only │
│ │ ├── ELSE  Select from (allowed ∩ ¬blocked ∩ ¬pressure_exceeded)
│
GENSE Message OS GRRIPS 19

│ │ ├── Apply rotation lock (avoid last_3_ctas if possible) │
│ │ ├── IF no valid CTA AND auto_swap available → swap + retry │
│ │ ├── IF still no valid CTA  EMIT blocked │
│ │ └── Construct cta_text │
│ └── ELSE  cta_type: "none" │
│ │
│ STEP 7 BUILD ASK_BLOCK (v1.3.0 │
│ ├── Construct ask_block object from compiled S node │
│ ├── Validate ask_block (type, subquestions count) │
│ └── IF validation fails  EMIT blocked │
│ │
│ STEP 8 RUN SCAFFOLD VALIDATORS │
│ ├── V_NODE_001 Required nodes present │
│ ├── V_ASK_001 Single ask rule (no CTA  question) │
│ ├── V_CTA_001 CTA rotation lock │
│ ├── V_CTA_002 CTA pressure ceiling │
│ ├── V_CTA_003 CTA type validity (v1.3.0 │
│ ├── V_PROOF_001003 Proof primitive rules │
│ ├── V_CLAIM_001 All claims have claim_id (v1.3.1 │
│ ├── V_CLAIM_002 Config/asset claims have source_ref (v1.3.1 │
│ ├── IF any validator FAILS │
│ │ ├── IF CTA failure AND auto_swap available → swap + recompile │
│ │ └── ELSE  EMIT blocked + failure_reasons │
│ └── Log validators_passed to trace │
│ │
│ STEP 9 ASSEMBLE DRAFT │
│ ├── Concatenate nodes in arc order │
│ ├── Build final node_map │
│ ├── Calculate word_count │
│ ├── Attach ask_block (v1.3.0 │
│ ├── Attach claims with stable identifiers (v1.3.1 │
│ └── Verify word_count <= length_limit (compress if needed) │
│ │
│ STEP 10 EMIT OUTPUT │
│ ├── Populate OUTPUT_SCHEMA with draft + node_map + ask_block + trac
e │
GENSE Message OS GRRIPS 20

│ ├── Include all claims for Module 08 (with claim_id/source_ref) (v1.3.1│
│ ├── Echo cta_constraint_struct in trace for audit │
│ └── Return with status: "success" │
│ │
└───────────────────────────────────────────────────
──────────────────────┘
6.1 Arc Selection Rules
ARC_MAPPINGS  
# CONTROL 12
1 "arc": ["G", "P"], "notes": "Minimal—escalation message"},
2 "arc": ["G", "P", "S"], "notes": "Request missing context"},
# OPEN LOOP RESOLUTION 38
3 "arc": ["G", "R1", "P"], "notes": "Answer only, no ask"},
4 "arc": ["G", "R1", "P", "S"], "notes": "Answer + clarifier question"},
5 "arc": ["G", "R1", "P", "S"], "notes": "Defer + request owner"},
6 "arc": ["G", "P", "S"], "notes": "Provide artifact, minimal framing"},
7 "arc": ["G", "R1", "I", "S"], "notes": "Request info to prepare artifact"},
8 "arc": ["G", "R1", "P", "S"], "notes": "Resolve process blocker"},
# COMMITMENT INTEGRITY 911
9 "arc": ["G", "R1", "P", "S"], "notes": "Confirm delivery time"},
10 "arc": ["G", "R1", "P", "S"], "notes": "Recover missed commitment—MU
ST reference commitment"},
11 "arc": ["G", "R1", "P", "S"], "notes": "Confirm buyer commitment"},
# DISCOVERY & ALIGNMENT 1215
12 "arc": ["G", "R1", "I", "S"], "notes": "Single discovery probe—S is questi
on"},
13 "arc": ["G", "R1", "I", "S"], "notes": "Stakeholder expand—S asks who el
se"},
14 "arc": ["G", "R1", "P", "S"], "notes": "Redirect to CC'd stakeholder"},
15 "arc": ["G", "R1", "I", "S"], "notes": "Timeline alignment—S asks about ti
GENSE Message OS GRRIPS 21

ming"},
# PROGRESSION 1620
16 "arc": ["G", "R1", "P", "S"], "notes": "Offer async options—S is async_ch
oice"},
17 "arc": ["G", "R1", "R2", "P", "S"], "notes": "Propose call—full arc for valu
e prop"},
18 "arc": ["G", "R1", "P", "S"], "notes": "Deliver proposal/pricing"},
19 "arc": ["G", "R1", "R2", "I", "P", "S"], "notes": "Trial close—full arc"},
20 "arc": ["G", "R1", "P", "S"], "notes": "Next step proposal"},
# OBJECTION & COMPETITION 2122
21 "arc": ["G", "R1", "R2", "I", "P", "S"], "notes": "Objection reframe—full ar
c for trust repair"},
22 "arc": ["G", "R1", "P", "S"], "notes": "Competitive comparison"},
# EXIT 2324
23 "arc": ["G", "R1", "P", "S"], "notes": "Gentle nudge after stall"},
24 "arc": ["G", "R1", "P"], "notes": "Close, no S (leave door open)"}
}
6.2 Length Limits
LENGTH_CATEGORIES  
"default" 150,
"technical" 250,
"procurement" 300,
"discovery" 100,
"follow-up" 75
}
6.3 Tone Calibration
TONE_CALIBRATION  
"low": {
GENSE Message OS GRRIPS 22

"style": "warm",
"allow_humor" True,
"formality": "conversational",
"avoid": []
},
"medium": {
"style": "helpful",
"allow_humor" False,
"formality": "professional",
"avoid": ["calendar_two_windows"]
},
"high": {
"style": "careful",
"allow_humor" False,
"formality": "formal",
"avoid": ["calendar_light", "calendar_two_windows"]
},
"critical": {
"style": "minimal",
"allow_humor" False,
"formality": "formal",
"avoid": ["calendar_light", "calendar_two_windows", "async_choice"]
}
}
6.4 CTA Selection with Explicit Constraints (v1.3.0: AMENDED)
CTA_PRESSURE  
"none" 0,
"opt_out" 0,
"question" 1,
"async_review" 2,
"async_choice" 2,
"calendar_light" 3,
"calendar_two_windows" 3
GENSE Message OS GRRIPS 23

}
VALID_CTA_TYPES  set(CTA_PRESSURE.keys())
def select_cta(
selected_action: int,
cta_constraint: CTAConstraintInput,
risk_level: str
) → tuple[str | None, str]:
"""
Select CTA honoring explicit constraint struct.
Returns (cta_text, cta_type) or (None, "none") if no S node.
v1.3.0 Uses explicit CTAConstraintInput struct instead of generic blob.
"""
# If whitelist present, ONLY those CTAs are valid (overrides allowed/blocke
d)
if cta_constraint.get("whitelist_ctas"):
available = set(cta_constraint["whitelist_ctas"])
else:
available = set(cta_constraint["allowed_ctas"]) - set(cta_constraint["bloc
ked_ctas"])
# Apply pressure ceiling
pressure_ceiling = cta_constraint.get("pressure_ceiling", 3
available = {cta for cta in available if CTA_PRESSURE.get(cta, 99  pressu
re_ceiling}
# Apply rotation lock (avoid last_3_ctas if possible)
last_3  set(cta_constraint.get("last_3_ctas", []))
non_repeating = available - last_3
if non_repeating:
available = non_repeating
elif "none" in available:
available = {"none"}
# Apply tone-based restrictions
GENSE Message OS GRRIPS 24

tone  TONE_CALIBRATION.get(risk_level, {})
avoid = set(tone.get("avoid", []))
available = available - avoid
# Select lowest pressure CTA from remaining
if not available:
return None, "none")
selected = min(available, key=lambda x: CTA_PRESSURE.get(x, 99
return (generate_cta_text(selected), selected)
6.5 Forbidden Patterns
FORBIDDEN_PATTERNS  
"Just following up",
"I wanted to reach out",
"Hope this finds you well",
"As per my last email",
"Circling back",
"Touching base",
"Let me know if you have any questions",
"Please don't hesitate to",
"At your earliest convenience",
"Per our conversation",
"Going forward",
"Synergy", "synergize",
"Low-hanging fruit",
"Move the needle",
"Circle back",
"Take this offline",
"Ping me",
"Loop in",
"Deep dive",
"Bandwidth",
"Best practices",
GENSE Message OS GRRIPS 25

"Value-add",
"Leverage",
"Optimize",
"Actionable",
"Drill down"
]
def check_forbidden_patterns(text: str) → list[str]:
"""Returns list of forbidden patterns found in text."""
found = []
text_lower = text.lower()
for pattern in FORBIDDEN_PATTERNS
if pattern.lower() in text_lower:
found.append(pattern)
return found
6.6 Ask-Block Rule Enforcement (v1.3.0: AMENDED)
def enforce_single_ask_block(draft: dict)  ValidationResult:
"""
Enforce Build Contract A5 ask_blocks_per_message  1
v1.3.0 Validates ask_block object structure.
"""
errors = []
ask_block = draft.get("ask_block", {})
ask_type = ask_block.get("type", "none")
cta_type = draft.get("cta_type", "none")
# Cannot have both CTA and question
if ask_type == "question" and cta_type not in None, "none"]:
errors.append("VIOLATION CTA  question in same message")
# Input request block cannot exceed 3 subquestions
if ask_type == "input_request_block":
subq = ask_block.get("subquestions", [])
GENSE Message OS GRRIPS 26

if len(subq)  3
errors.append("VIOLATION input_request_block exceeds 3 subquestio
ns")
return ValidationResult(valid=len(errors)  0, errors=errors)
6.7 Claim Validation (v1.3.1: ADDITION)
def validate_claims(claims: list[dict])  ValidationResult:
"""
Validate all claims have required fields for Module 08.
v1.3.1 Ensures deterministic audit replay.
"""
errors = []
for i, claim in enumerate(claims):
# V_CLAIM_001 All claims must have claim_id
if not claim.get("claim_id"):
errors.append(f"V_CLAIM_001 Claim {i} missing claim_id")
# V_CLAIM_002 Config/asset claims must have source_ref
source = claim.get("source")
if source in ["config", "asset"] and not claim.get("source_ref"):
errors.append(f"V_CLAIM_002 Claim {claim.get('claim_id', i)} source=
{source} missing source_ref")
return ValidationResult(valid=len(errors)  0, errors=errors)
Part IX: Test Vectors
12. Test Vectors
12.1 Lock-Driven Variant Selection Tests (v1.3.0: ADDITION)
GENSE Message OS GRRIPS 27

Expected
ID locks_applied buyer_intent Notes
Variant
Commitment
TV_VAR_001 ["PL_001"] any trust-repair
drift lock active
open-loop- Open loop lock
TV_VAR_002 ["PL_002"] any
priority active
["PL_001", PL_001 takes
TV_VAR_003 any trust-repair
"PL_002"] priority
No locks,
TV_VAR_004 [] question_product answer-first
question intent
No locks, non-
TV_VAR_005 [] objection_budget standard
question intent
PL_004 (critical
TV_VAR_006 ["PL_004"] question_technical answer-first risk) doesn't
affect variant
12.2 CTA Constraint Struct Tests (v1.3.0: ADDITION)
ID CTA Constraint Expected CTA Notes
whitelist: ["none", "opt_out" or Whitelist overrides
TV_CTA_001
"opt_out"] "none" allowed/blocked
allowed:
Pressure ceiling blocks
TV_CTA_002 ["calendar_light"], "none"
calendar_light (level 3
pressure_ceiling: 1
last_3_ctas:
NOT
TV_CTA_003 ["async_review", Rotation lock
"async_review"
"async_review"]
allowed: ["question"], Blocked overrides
TV_CTA_004 "none"
blocked: ["question"] allowed
12.3 Ask-Block Output Tests (v1.3.0: ADDITION)
Expected
ID Scenario Notes
ask_block.type
Action 12 (discovery S node contains
TV_ASK_001 "question"
probe) question
GENSE Message OS GRRIPS 28

Expected
ID Scenario Notes
ask_block.type
TV_ASK_002 Action 3 (answer only) "none" No S node in arc
TV_ASK_003 Action 17 (propose call) "cta" S node contains CTA
S node with 2 related
TV_ASK_004 "input_request_block" Subquestions  3
questions
12.4 Arc Selection Tests
ID Action Expected Arc Notes
TV_ARC_001 1 GP Escalation, minimal
TV_ARC_002 3 GR1P Answer only, no S
TV_ARC_003 12 GR1IS Discovery, S is question
TV_ARC_004 21 GR1R2IPS Objection, full arc
TV_ARC_005 24 GR1P Close, no S (leave door open)
12.5 Constraint Enforcement Tests
ID Scenario Expected Behavior
TV_ENF_001 Multiple questions in draft Remove all but S node question
TV_ENF_002 Word count 180, limit 150 Compress or truncate P node
TV_ENF_003 "Hope this finds you well" in G Rewrite G node
TV_ENF_004 Action 10, no commitment reference Force commitment language
TV_ENF_005 Open loop exists, action 3 P node addresses loop
12.6 Failure Mode Tests
ID Input Condition Expected Result
TV_FAIL_001 selected_action missing status: blocked, fallback_action: 1
TV_FAIL_002 selected_action: 25 status: blocked, fallback_action: 1
TV_FAIL_003 locks_applied missing (v1.3.0 status: blocked, V_INPUT_003
TV_FAIL_004 CTA type "invalid_cta" (v1.3.0 status: blocked, V_CTA_003
TV_FAIL_005 CTA  question in same message status: blocked, V_ASK_001
GENSE Message OS GRRIPS 29

12.7 Claims Schema Tests (v1.3.1: ADDITION)
ID Scenario Expected Output Notes
Two claims from claims[0].claim_id="CLM_001", Deterministic
TV_CLAIM_001
thread and config claims[1].claim_id="CLM_002" sequence
Thread-sourced Thread anchor
TV_CLAIM_002 span_ref="turn_1:char_031"
claim present
Config-sourced Config key
TV_CLAIM_003 source_ref="compliance.soc2"
claim present
Asset-sourced
TV_CLAIM_004 source_ref="CS_SEC_001" Asset ID present
claim
No references
TV_CLAIM_005 Derived claim span_ref=null, source_ref=null
for inferences
TV_CLAIM_001 Full Example:
{
"name": "claims_list_with_ids",
"input": {
"selected_action" 6,
"thread_state": {
"latest_buyer_content": "We need SOC 2 compliance. What's your sec
urity posture?",
"turns": [
{"turn_index" 1, "speaker": "buyer", "content": "We need SOC 2 co
mpliance. What's your security posture?"}
],
"product_config": {"compliance": {"soc2" True, "iso27001" True}}
},
"policy_output": {
"selected_action" 6,
"decision_trace": {"locks_applied": []},
"cta_constraint": {"allowed_ctas": ["async_review"], "blocked_ctas": [],
"last_3_ctas": [], "pressure_ceiling" 2
}
},
GENSE Message OS GRRIPS 30

"expected_output": {
"draft": {
"claims": [
{
"claim_id": "CLM_001",
"claim": "We're SOC 2 Type II certified",
"source": "config",
"span_ref" None,
"source_ref": "compliance.soc2",
"grounded" None
},
{
"claim_id": "CLM_002",
"claim": "You mentioned needing SOC 2 compliance",
"source": "thread",
"span_ref": "turn_1:char_031",
"source_ref" None,
"grounded" None
}
]
}
}
}
12.8 Proof Insert Tests (v1.3.1: ADDITION)
ID Scenario Expected Output Notes
Proof insert with asset Asset ID present for
TV_PROOF_002 asset_id="CS_SEC_001"
lookup validation
TV_PROOF_002 Full Example:
{
"name": "proof_insert_with_asset_id",
"input": {
"selected_action" 15,
GENSE Message OS GRRIPS 31

"thread_state": {
"buyer_role": "security",
"enablement_assets": [
{
"asset_id": "CS_SEC_001",
"source_tag": "acme_security_case_study",
"type": "case_study",
"personas": ["security", "it"]
}
]
}
},
"expected_output": {
"draft": {
"proof_insert": {
"proof_class": "case_study",
"proof_content": "Acme Corp reduced security incidents by 40% wit
hin 6 months...",
"persona_match" True,
"source_tag": "acme_security_case_study",
"asset_id": "CS_SEC_001"
}
}
}
}
Part X: Integration
13. Upstream/Downstream Dependencies
13.1 Upstream Dependencies (v1.3.0: AMENDED)
Module Required Fields Failure Behavior
Module 06 Policy selected_action, cta_constraint (struct), Cannot proceed—fail
Engine) decision_trace.locks_applied with fallback_action: 1
GENSE Message OS GRRIPS 32

Module Required Fields Failure Behavior
Module 04
deal_stage, buyer_intent, risk_level Use defaults if missing
(Classifier)
Module 02
latest_buyer_content, latest_buyer_name Use generic content
(Ingestion)
Module 03 State
open_loops, commitments, turns (v1.3.1 Use empty arrays
Extractor)
13.2 Downstream Consumers (v1.3.1: AMENDED)
Module Consumed Fields Purpose
draft.claims[] (with claim_id, span_ref, Validate grounding with
Module 08 Claims
source_ref), draft.proof_insert (with deterministic audit trail
Policy)
asset_id) (v1.3.1
Module 09 Drift draft.text, word_count, cta_type,
Check for drift patterns
Monitor) node_map, ask_block
Orchestrator draft.text, generation_trace Package output
Module 13 Audit
generation_trace, cta_constraint_struct Replay and verification
Guide)
13.3 Contract Alignment Verification (v1.3.1: AMENDED)
Contract Requirement Module 07 Implementation Status
Build Contract A5 ask_blocks enforce_single_ask_block() +
✓ ALIGNED
 1 ask_block object
Build Contract A6 Output OUTPUT_SCHEMA matches (with
✓ ALIGNED
schema v1.3.1 additions)
Build Contract A8 LENGTH_CATEGORIES"default"] =
✓ ALIGNED
max_word_count_default 150 150
Build Contract A8 LENGTH_CATEGORIES"technical"] =
✓ ALIGNED
max_word_count_technical 250 250
Build Index 07 Node definitions Section 3.2 ✓ ALIGNED
Build Index 07 Arc mappings Section 6.1 ✓ ALIGNED
Build Index 07 Forbidden
Section 6.5 ✓ ALIGNED
patterns
GENSE Message OS GRRIPS 33

Contract Requirement Module 07 Implementation Status
Build Index 07 Tone calibration Section 6.3 ✓ ALIGNED
Policy Engine: locks_applied ✓ ALIGNED
Section 3.5 variant selection
contract (v1.3.0
Policy Engine: CTA constraint ✓ ALIGNED
Section 4.1 CTAConstraintInput
output (v1.3.0
Module 08 claim_id/source_ref ✓ ALIGNED
Section 5.1 claims schema
contract (v1.3.1
Module 08 proof asset_id ✓ ALIGNED
Section 5.1 proof_insert schema
contract (v1.3.1
8. Validators
Code Validator Trigger Severity Response
V_INPUT_001 selected_action Missing or invalid High BLOCK
Missing or
V_INPUT_002 cta_constraint High BLOCK
malformed
Missing from
V_INPUT_003 locks_applied decision_trace High BLOCK
(v1.3.0
Invalid CTA type in
cta_constraint
V_INPUT_004 allowed/blocked High BLOCK
struct
(v1.3.0
V_NODE_001 Required nodes Arc node missing High BLOCK
CTA  question in
V_ASK_001 Single ask rule High BLOCK
same message
Invalid type or 3
ask_block
V_ASK_002 subquestions High BLOCK
structure
(v1.3.0
Same CTA 3x WARNING,
V_CTA_001 CTA rotation Medium
consecutively select alternate
Exceeds BLOCK, try
V_CTA_002 CTA pressure High
pressure_ceiling auto-swap
GENSE Message OS GRRIPS 34

Code Validator Trigger Severity Response
cta_type not in
CTA type
V_CTA_003 VALID_CTA_TYPES High BLOCK
validity
(v1.3.0
1 proof insert in P
V_PROOF_001 Proof primitive Medium BLOCK
node
Proof class Wrong proof class WARNING,
V_PROOF_002 Low
match for persona continue
Claim emitted
Claim source
V_PROOF_003 without source tag Medium BLOCK
tag
(v1.3.0
proof_insert
V_PROOF_004 Proof asset_id missing asset_id Medium BLOCK
(v1.3.1
Claim missing
V_CLAIM_001 Claim ID Medium BLOCK
claim_id (v1.3.1
Config/asset claim
Source
V_CLAIM_002 missing source_ref Medium BLOCK
reference
(v1.3.1
Final Framing
GRRIPS is not how we write messages.
GRRIPS is how the system knows a conversation is safe to advance.
End of Module 07  Message OS GRRIPS Specification v1.3.1
GENSE Message OS GRRIPS 35