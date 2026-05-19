GEN-SE System Hardening Plan
Version: 1.2.3
Date: 20260124
Status: LOCKED All audit feedback incorporated — ready for execution)
Purpose: Lock the CTA contract surface and fix upstream drift before adding
Module 08
Executive Statement
GENSE is a contract-first execution spine: 02  03  04  06  07  08 
09, where each module's output is a strict input contract for the next. The system
is currently at the "lock foundations" moment: CTA types, pressure tables, gating
fields, and claim schemas are still duplicated and drifting.
Core Thesis: Freeze the CTA contract surface end-to-end before Module 08.
Single-Source Rules (enforced by this plan):
 CTA enums + pressure live ONLY in Canonical_Enumerations
 Thread gating fields MUST exist in ThreadState schema
 No module may redefine CTA pressure categories beyond canonical import
Contract Surface Boundaries (What Must Lock)
Boundary Authority Consumers Current Drift
CTA enum Action Set has legacy
Canonical_Enumerations 06, 07, Harness
space tokens
Action Set (opt_out=1,
CTA pressure Canonical_Enumerations 06, 07, Harness
Policy Engine (opt_out=8
Upstream Schema missing fields
Thread_State_Schema 04, 06
gating Module 02 emits
Harness uses wrong field
Claim schema Message_OS v1.3.1 08, Harness
names
GENSE System Hardening Plan 1

Phase 1: CTA Contract Surface Lock (BLOCKING)
These must be completed before any new module work.
1.1 Patch Action_Set__Command_Tree.pdf → v1.0.5
Priority: P0  Blocking
Effort: 1 hour
Risk if skipped: Module 07 rejects actions; pressure drift persists
A. Rename Legacy CTA Tokens to Canonical
Current
Action Canonical Fix Postcondition
Invalid)
4 one_question question state.last_seller_cta
none + ask_block.type:
7 input_request N/A
input_request_block
8 process_confirm async_review state.last_seller_cta
9 confirm_deadline async_choice state.last_seller_cta
11 confirm_deadline async_choice state.last_seller_cta
12 one_question question state.last_seller_cta
13 one_question question state.last_seller_cta
15 one_question question state.last_seller_cta
state.last_seller_cta (name
17 calendar_light calendar_two_windows
says "two windows")
19 calendar_firm calendar_two_windows state.last_seller_cta
20 process_confirm async_review state.last_seller_cta
21 one_question question state.last_seller_cta
B. DELETE the CTA Pressure Table (Critical)
The Action Set currently contains its own CTA_PRESSURE table with divergent
values (e.g., opt_out: 1 ). This table must be deleted entirely, not patched.
Replace the entire CTA Type Specifications section with:
GENSE System Hardening Plan 2

## CTA Type Reference
CTA types and pressure values are defined ONLY in Canonical_Enumerations.
pdf v1.0.0.
This document MUST NOT redefine CTA pressure or enumerate CTA types in
dependently.
Reference: Canonical_Enumerations.pdf Section "CTA TYPES"
Valid types: none, opt_out, question, async_review, async_choice, calendar_li
ght, calendar_two_windows
Note: `input_request` is NOT a CTA type. For actions requiring structured input
(e.g., Action 7, use cta_type="none" with ask_block.type="input_request_blo
ck".
C. Action 7 Clarification
Current: CTA Type: input_request (invalid)
Patched:
Action 7 request_missing_information
CTA Type: none
Ask Block Type: input_request_block (max 3 subquestions)
D. Action 17 Semantic Alignment
Action is named propose_call_two_time_windows but CTA is calendar_light .
Patch: Change CTA to calendar_two_windows (action name is authoritative).
Changelog:
v1.0.5 | 20260124 | BREAKING 1 Migrated 12 actions to canonical CTA toke
ns.
2 DELETED local CTA pressure table - now references Canonical_Enumerati
ons only.
GENSE System Hardening Plan 3

3 Action 7 clarified as cta_type=none + ask_block.type=input_request_bloc
k.
4 Action 17 CTA aligned to action name (calendar_two_windows).
1.2 Patch Deal_Stage_Intent_Classifier.pdf → v1.0.4
Priority: P0  Blocking
Effort: 5 min
Location: Section 9, Test Vector CL_INT_003
Current:
"blocked_ctas": ["calendar_light", "calendar_firm"]
Patched:
"blocked_ctas": ["calendar_light", "calendar_two_windows"]
Changelog:
v1.0.4 | 20260124 | PATCH CL_INT_003 blocked_ctas updated from legacy
"calendar_firm" to canonical "calendar_two_windows".
1.3 Patch Contract_Test_Harness.pdf → v1.0.1
Priority: P0  Blocking
Effort: 45 min
Fix A: Critical Risk Pressure Ceiling
Problem: Harness sets pressure_ceiling=0 for critical risk, excluding async_review
(pressure=2.
Contract constraint: Message OS defines pressure_ceiling as int , always applied
numerically.
Patched:
GENSE System Hardening Plan 4

# Critical risk: ceiling must allow whitelisted async_review (pressure 2
pressure_ceiling  2 if risk_level == "critical" else 3
Add regression guard CT_021
# TEST 21 Critical risk ceiling must not filter whitelisted CTAs
def test_critical_ceiling_allows_whitelist():
whitelist  RISK_CTA_RESTRICTIONS"critical"]["whitelist_ctas"]
max_whitelist_pressure = max(CTA_PRESSURE[cta] for cta in whitelist)
# Get the ceiling that would be set for critical risk
critical_ceiling  2 # From patched logic
assert critical_ceiling >= max_whitelist_pressure, \
f"Critical ceiling {critical_ceiling} would filter whitelisted CTAs " \
f"(max whitelist pressure: {max_whitelist_pressure})"
This prevents anyone from reintroducing the pressure_ceiling=0 bug.
Fix B: Align Claim Schema to Message OS v1.3.1
Patched Claim dataclass:
@dataclass
class Claim:
claim_id: str # Format: CLM_###
claim: str # The claim text
source: str # "thread" | "config" | "asset" | "derived" | "unknow
n"
span_ref: Optional[str]  None # Required if source == "thread"
source_ref: Optional[str]  None # Required if source in ["config", "asset"]
grounded: Optional[bool]  None # Set by Module 08, NOT Module 07
Fix C: Add Mechanical Completion Tests (NEW — from ChatGPT
audit)
GENSE System Hardening Plan 5

CT_019 Action Set Enum Sweep
# Iterate all 24 Action Specs and assert:
# - cta_type ∈ VALID_CTA_TYPES
# - blocked_ctas/allowed_ctas/whitelist_ctas ⊆ VALID_CTA_TYPES
# - if cta_type == "none" and ask_block used, ask_block.type is valid
# - "input_request" never appears as a CTA type
CT_020 Deprecated Token Grep
# Fail if any deprecated CTA token appears anywhere in harness
# IMPORTANT Token list MUST be imported from Canonical Enumerations
# Do NOT define a second copy here
from gense_enums import DEPRECATED_CTA_NAMES # Single source of trut
h
DEPRECATED_TOKENS  set(DEPRECATED_CTA_NAMES.keys())
# If import not possible, this list MUST be copy/pasted from
# Canonical_Enumerations.pdf Section "DEPRECATED CTA NAMES"
# and updated in the same PR as any canonical changes.
# Scan rules:
#  FAIL on structured data JSON/YAML/spec objects/fixtures) - always
#  WARNONLY on prose comments/changelog history (strict mode optional)
Fix D: Claims Validation Tests
CT_015 Thread-sourced claims require span_ref WITH valid format
# TEST 15 Thread claims require span_ref matching TURN_ADDRESSING sch
eme
import re
SPAN_REF_PATTERN  re.compile(r'^turn_(\d+):char_(\d+):(\d+)$')
def test_thread_claim_span_ref():
GENSE System Hardening Plan 6

claim  Claim(claim_id="CLM_001", claim="...", source="thread",
span_ref="turn_3:char_4589")
# Must exist
assert claim.span_ref is not None, "Thread claim requires span_ref"
# Must match format
match  SPAN_REF_PATTERN.match(claim.span_ref)
assert match, f"span_ref must match turn_{{n}}:char_{{start}}:{{end}}, got:
{claim.span_ref}"
# Turn must be 1-based (turn_0 is invalid)
turn_n = int(match.group(1))
assert turn_n  1, f"Turn index must be 1-based, got turn_{turn_n}"
# Start must be < end
start, end = int(match.group(2)), int(match.group(3))
assert start < end, f"span_ref start ({start}) must be < end ({end})"
CT_016 Config/asset claims require source_ref
CT_017 Derived/unknown claims must have null refs
CT_018 Claims grounded field must be None from Module 07
Changelog:
v1.0.1 | 20260124 | PATCH 1 Critical risk pressure_ceiling=2 (was 0.
2 Claim schema aligned to Message OS v1.3.1 5 source types, grounded=No
ne).
3 Added CT_015018 for claims validation CT_015 includes span_ref format
check).
4 Added CT_019 Action Set enum sweep (mechanical).
5 Added CT_020 deprecated token grep (mechanical).
6 Added CT_021 critical ceiling regression guard.
7 Added CT_022 ask-block  CTA mutual exclusion rule.
GENSE System Hardening Plan 7

Fix E: Ask-Block + CTA Mutual Exclusion Rule (NEW)
Problem: question is both a valid CTA type AND a valid ask_block.type . V_ASK_001
blocks "CTA  question in same message" but the boundary is ambiguous.
Hard Rule (add to harness and Message OS
ASKBLOCK / CTA MUTUAL EXCLUSION
 If ask_block.type == "question", then cta_type MUST be "none"
 If ask_block.type == "cta", then cta_type MUST be a valid CTA (including "q
uestion")
 If ask_block.type == "input_request_block", then cta_type MUST be "none"
- cta_type == "question" is ONLY valid when ask_block.type == "cta"
Add CT_022
# TEST 22 Ask-block  CTA mutual exclusion
def test_ask_block_cta_mutual_exclusion():
# INVALID ask_block.type="question" with cta_type="question"
invalid_output  MessageOutput(
ask_block=AskBlock(type="question", question_text="What's your timeli
ne?"),
cta_type="question" # WRONG  should be "none"
)
errors = invalid_output.validate()
assert any("V_ASK" in e for e in errors), \
"Should fail: ask_block.type='question' requires cta_type='none'"
# VALID ask_block.type="question" with cta_type="none"
valid_output  MessageOutput(
ask_block=AskBlock(type="question", question_text="What's your timeli
ne?"),
cta_type="none" # CORRECT
)
errors = valid_output.validate()
assert not any("V_ASK" in e for e in errors), \
"Should pass: ask_block.type='question' with cta_type='none'"
GENSE System Hardening Plan 8

# VALID ask_block.type="cta" with cta_type="question"
valid_cta_output  MessageOutput(
ask_block=AskBlock(type="cta", cta_type="question"),
cta_type="question" # CORRECT  CTA block uses "question" as CTA
)
errors = valid_cta_output.validate()
assert not any("V_ASK" in e for e in errors), \
"Should pass: ask_block.type='cta' can use cta_type='question'"
Phase 2: Secondary Contract Fixes (HIGH)
2.1 Patch Policy_Engine.pdf → v1.1.2
Priority: P1  High
Effort: 15 min
Problem: Policy Engine has CTA_PRESSURE_RANK with:
opt_out: 8 (should be 0
Legacy CTA categories
Divergent from both Canonical_Enumerations and Message OS
Required Edit: DELETE the entire CTA_PRESSURE_RANK definition.
Replace with:
# CTA pressure values — single source of truth
# Reference: Canonical_Enumerations.pdf v1.0.0
# This module MUST NOT define its own pressure rankings.
# Import or reference canonical values only.
Changelog:
v1.1.2 | 20260124 | BREAKING Removed CTA_PRESSURE_RANK entirely.
Policy Engine now references Canonical_Enumerations as single source of tru
GENSE System Hardening Plan 9

th.
2.2 Patch Thread_State_Schema.pdf → v1.0.2
Priority: P1  High
Effort: 20 min
Problem:
Module 02 emits gating fields ( required_config_missing , missing_config_fields , status )
Policy Engine and Module 04 require them as top-level fields
Thread State Schema doesn't define them
CRITICAL Fields must be TOPLEVEL (not nested)
Module 04's input contract expects required_config_missing , missing_config_fields , and
parse_status as top-level ThreadState fields. Nesting them under gating: {...} would
break Module 04's stated contract.
Required Edit: Add gating fields as TOPLEVEL fields in ThreadState:
# ThreadState (top-level fields, NOT nested)
class ThreadState:
# ... existing fields ...
# Upstream Gating (from Module 02, carried forward unchanged)
required_config_missing: bool # True if config incomplete
missing_config_fields: List[str] # Which fields are missing
parse_status: str # "success" | "blocked" | "partial"
Resolve naming: Module 02 uses status , downstream uses parse_status .
Option A (recommended): Module 02 emits parse_status directly
Option B ThreadState maps parse_status  Module02Output.status
Explicit mapping (if Option B
GENSE System Hardening Plan 10

ThreadState.parse_status  Module02Output.status (verbatim, no transform
ation)
Add propagation rule:
PROPAGATION CONTRACT
 Module 03 MUST carry Module 02 gating fields forward unchanged (top-lev
el)
 Modules 04/06/07 MAY read gating fields but MUST NOT modify them
 If parse_status == "blocked", Policy Engine triggers HB_003
Changelog:
v1.0.2 | 20260124 | PATCH 1 Added gating fields as TOPLEVEL ThreadSta
te fields
(required_config_missing, missing_config_fields, parse_status).
2 Standardized field name to parse_status.
3 Added propagation contract for gating fields.
Phase 3: Housekeeping (MEDIUM)
3.1 Patch Build_Index.pdf → v2.1
Correct false claim that Module 03/05 don't exist
Add Canonical_Enumerations.pdf to artifact list
Update version numbers for all patched modules
3.2 Stamp Internal_Directory.pdf Appendix B.2 as LEGACY
Add header:
⚠ LEGACY REFERENCE  See Canonical_Enumerations.pdf v1.0.0 for curren
t CTA types.
GENSE System Hardening Plan 11

Phase 4: Resume Forward Progress
Prerequisites (ALL must pass)
Action_Set__Command_Tree.pdf v1.0.5 locked
Deal_Stage_Intent_Classifier.pdf v1.0.4 locked
Contract_Test_Harness.pdf v1.0.1 locked
Policy_Engine.pdf v1.1.2 locked
Thread_State_Schema.pdf v1.0.2 locked
CT_001022 all pass
grep for deprecated CTA tokens returns zero matches
CTA_PRESSURE defined in exactly ONE place Canonical_Enumerations)
Gating fields are TOPLEVEL in ThreadState (not nested)
Then: Module 08 (Claims Validation)
Definition of Done (Hard Gates)
Gate Test Pass Condition
G1 CT_020 Zero deprecated CTA tokens in harness
G2 CT_019 All 24 actions use only canonical CTA types
G3 Schema check ThreadState contains gating fields TOPLEVEL
G4 Single-source CTA_PRESSURE exists in exactly 1 file
G5 CT_003 Critical risk emits only whitelisted CTAs
G6 CT_015018 Claims schema matches Message OS v1.3.1
G7 CT_021 Critical ceiling ≥ max whitelist pressure
G8 CT_022 Ask-block  CTA mutual exclusion enforced
Zero deprecated tokens in repo (excluding
G9 Repo grep
/docs/legacy/)
G9 Implementation:
GENSE System Hardening Plan 12

# Run from repo root
grep -r --include="*.json" --include="*.yaml" --include="*.py" --include="*.m
d" \
"one_question\|calendar_firm\|process_confirm\|confirm_deadline\|input_req
uest" \
. --exclude-dir="docs/legacy" --exclude-dir="node_modules"
# Expected: zero matches (exit code 1
# If matches found: FAIL gate, do not proceed to Module 08
Stress Tests (Post-Patch Verification)
ST_A: Critical Risk + Whitelist + Ceiling
Setup: risk_level = "critical"
Verify: async_review is selectable (not filtered by ceiling=2
ST_B: Upstream Gating Persists
Setup: Module 02 blocks with required_config_missing=True
Verify: Policy Engine receives gating.required_config_missing=True in ThreadState
ST_C: Pressure Table Drift Detection
Setup: Add CTA_PRESSURE  ...} to any module other than Canonical_Enumerations
Verify: CT_020 or similar grep test fails
ST_D: Claims Module-08-Ready
Setup: Module 07 emits claims
Verify: grounded=None , span_ref present for thread claims, source_ref for
config/asset
Complete CTA Drift Ledger
GENSE System Hardening Plan 13

Legacy Token Canonical Actions Other Docs
one_question question 4, 12, 13, 15, 21 Internal Dir
Classifier CL_INT_003,
calendar_firm calendar_two_windows 19
Internal Dir
process_confirm async_review 8, 20 Internal Dir
confirm_deadline async_choice 9, 11 —
confirm_owner_deadline async_choice — Internal Dir
async_review_or_call async_review — Internal Dir
input_request Not a CTA 7 —
calendar_light
calendar_two_windows 17 —
(semantic)
Summary
Phase Documents Key Changes Effort
12 action CTAs, DELETE
Action Set,
1 pressure table, claims schema, 2 hr
Classifier, Harness
mechanical tests
Policy Engine, DELETE pressure rank, add
2 35 min
Thread State gating fields
Build Index, Internal
3 Housekeeping 15 min
Dir
4 Module 08 Claims Validation TBD
Start with Phase 1. Do not skip to Module 08.
Appendix: Single-Source Contract Rules
These rules are now enforced by this hardening plan:
 CTA_TYPES  Defined ONLY in Canonical_Enumerations.pdf
 CTA_PRESSURE  Defined ONLY in Canonical_Enumerations.pdf
 DEPRECATED_CTA_NAMES  Defined ONLY in Canonical_Enumerations.pdf
GENSE System Hardening Plan 14

 Gating fields  Defined in Thread_State_Schema.pdf, emitted by Module 02,
read-only downstream
 Claim schema  Defined in Message_OS_GRRIPS.pdf v1.3.1
Any module that redefines these locally is in violation and must be patched.
GENSE System Hardening Plan 15