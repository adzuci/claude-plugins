GEN-SE Thread State Schema
Module: 03_Thread_State_Schema
Version: 1.0.2
Status: LOCKED
Date: February 2, 2026
Author: Claude
Contract Reference: Build Contract B2 Step 2, Build Index Section 03
Document Control
Version Date Author Changes
Initial canonical specification.
Consolidated from embedded
references in Internal_Directory,
Deal_Stage_Intent_Classifier Section
1.0.0 20260121 Claude
2.1, Policy_Engine Section 2,
Message_OS_GRRIPS Section 4.2.
Formalized 48-field structure with
complete type definitions.
1.0.1 20260121 Claude PATCH per ChatGPT audit: 1
Clarified module naming—this is
schema contract, not extractor
implementation. 2 Fixed
latest_buyer_turn to explicitly be 1-
based turn_number, not 0-based
index. 3 Resolved objection_tags
split ownership—Module 03 extracts,
Module 04 reads only. 4 Changed
buyer_intent default from None to
"unclear" for pipeline safety. 5
Marked action ID references as
placeholders pending Module 05. 6
Added decision_trace_id and
message_artifact_id pointer fields for
replay support. 7 Added
GENSE Thread State Schema 1

Version Date Author Changes
resolution_method to OpenLoop
schema. 8 Added
stakeholder_delta_last_turn derived
field. Total fields now 51.
PATCH per System Hardening Plan:
1 Added upstream gating fields as
TOPLEVEL ThreadState fields
(required_config_missing,
missing_config_fields, parse_status).
2 Standardized field name to
parse_status (maps from Module 02
1.0.2 20260202 Claude status field). (3) Added propagation
contract for gating fields. 4
Updated field count from 51 to 54.
5 Updated Action ID placeholders
to stable enums per Module 05
v1.0.5. 6 Updated downstream
contract alignment for Module 04
v1.0.9 passthrough fields.
1. Purpose
This module defines the canonical ThreadState schema contract — the central
data structure that flows through the GENSE execution spine.
Naming Clarification: This document Module 03 is the schema specification.
The implementation logic that populates this schema (state extraction from turns)
is a separate concern. Build artifacts should reference this as "Thread State
Schema" not "State Extractor."
ThreadState is:
Produced by: Module 03 implementation (state extraction logic)
Consumed by: Modules 04, 06, and 07
The ThreadState schema serves as the single source of truth for:
What fields exist and their exact names
Field types and nullability
GENSE Thread State Schema 2

Which module owns (writes) each field
Which modules consume (read) each field
Nested object schemas OpenLoop, Commitment, Stakeholder, Turn)
Critical Principle: ThreadState is the contract that binds the execution spine. If
a field is not defined here, it cannot be referenced downstream.
Pipeline Execution Order: The system executes in strict order: 02  03  04
→ 06  07  08  09. Module 06 will never execute before Module 04 has
populated classification fields.
2. Scope
In Scope
Complete ThreadState field enumeration 54 fields as of v1.0.2
Three-tier structure definition Thread Core / Current State / Derived)
Nested object schemas: Turn, OpenLoop, Commitment, Stakeholder
Field ownership table (write responsibility)
Consumer table (read dependencies)
Type definitions with nullability rules
Enumeration values for all enum fields
Default values for optional fields
Upstream gating field propagation contract (v1.0.2
Out of Scope
State extraction logic (how fields are populated)  Module 03 implementation
concern
Turn parsing and attribution  Module 02 responsibility
Classification logic  Module 04 responsibility
Action selection logic  Module 06 responsibility
GENSE Thread State Schema 3

Message generation  Module 07 responsibility
3. Definitions
Term Definition
ThreadState The complete state object representing an email thread at a point in time
Thread Core Immutable fields set once at thread creation, carried from Module 02
Current State Mutable fields updated per-turn by Module 03
Computed fields derived from other state GRRIPS execution, action
Derived State
history)
Field Owner The module responsible for writing/updating a field
Field Consumer A module that reads a field (may not modify it)
Nullability Whether a field may be null ( None in Python, null in JSON
3.1 Deal Stage Enumeration
Authoritative Source: Deal Stage & Intent Classifier Module 04. Imported via
Canonical_Enumerations.pdf v1.0.0.
Value Description
triage Initial contact, no clear need articulated
discovery Buyer describes situation, asks general questions
evaluation Comparison questions, technical depth, proof requests
proposal Pricing questions, scope discussion
procurement Legal/security/procurement process
negotiation Terms discussion, final objections
closed_won Deal closed successfully
closed_lost Deal lost
3.2 Buyer Intent Enumeration
Authoritative Source: Deal Stage & Intent Classifier Module 04. Default: "unclear"
NEVER None).
GENSE Thread State Schema 4

Value Description
question_product Feature/capability questions
question_pricing Cost/budget questions
question_process Next steps/process questions
question_technical API/integration/specs questions
question_security SOC2/compliance/data questions
question_reference Case study/reference requests
objection_timing "Not right now" / timing hedge
objection_budget Cost concerns
objection_authority "Need to check with..."
objection_need Fit questioning
objection_competition Competitor mentions
commitment_signal Positive buying signal
commitment_request Request for proposal/call
information_share Provides context without ask
administrative Scheduling/logistics
unclear Cannot determine DEFAULT
3.3 Friction Pattern Enumeration
Value Description
stall No response for extended period
ghosting Buyer stopped responding entirely
circular Same questions repeating
escalation New stakeholders entering with concerns
none No friction pattern detected
3.4 Risk Level Enumeration
Authoritative Source: Deal Stage & Intent Classifier Module 04 v1.0.3.
GENSE Thread State Schema 5

Value Order Description
low 0 No significant risk factors
medium 1 Minor concerns present
Significant risk factors (legal/security involved, blocker
high 2
detected)
critical 3 Deal at risk or escalation threat
3.5 Source Channel Enumeration
Authoritative Source: Thread Ingestion Module 02 v1.2.2.
Value Description
email Standard email thread
scrape Scraped/imported thread
forward Forwarded thread
4. Inputs
4.1 Primary Input: Module 02 Output
ThreadState is constructed from Module 02 Thread Ingestion & Normalization)
output:
python
Module02Output = {
"status": str, # "success" | "blocked" | "partial"
"thread_id": str,
"turns" List[Turn],
"participants" List[Participant],
"latest_buyer_turn": int, # 1-based turn_number
"latest_buyer_content": str,
"latest_buyer_name": str,
"attribution_confidence": float, # 0.01.0
"buyer_role_confidence": float, # 0.01.0 (v1.2.2
"parsing_warnings" List[Warning],
"required_config_missing": bool, # v1.0.2 gating field
"missing_config_fields" List[str], # v1.0.2 gating field
}
4.2 Configuration Input
GENSE Thread State Schema 6

python
ConfigInput = {
"seller_emails" List[str],
"seller_domains" List[str],
"internal_domains" List[str],
"crm_account_domain": str | None,
"account_id": str | None,
"account_tier": str | None,
"vertical": str | None,
"product_context": str | None,
"seller_assigned": str | None,
"known_participants" List[KnownParticipant]
}
5. Outputs
5.1 ThreadState (Complete Schema)
python
@dataclass
class ThreadState:
# ================================================================
# TIER 1 THREAD CORE (immutable, set once at thread creation)
# Owner: Module 02 (carried through), Module 03 (config enrichment)
# ================================================================
thread_id: str # Required, unique identifier
thread_created_at: str | None # ISO8601 timestamp or None
source_channel: str | None # "email" | "scrape" | "forward" | None
account_id: str | None # CRM account identifier
account_tier: str | None # "enterprise" | "mid_market" | "smb" | None
vertical: str | None # Industry vertical
product_context: str | None # Product/solution context
seller_assigned: str | None # Assigned seller email
# ================================================================
# TIER 2 CURRENT STATE (mutable, updated per-turn)
# ================================================================
#  Turns (from Module 02, carried through) ---
turns: List[Turn] # All turns in chronological order
participants: List[Participant] # All discovered participants
latest_buyer_turn: int # turn_number 1-based), NOT 0-based index
latest_buyer_content: str # Content of latest buyer turn
latest_buyer_name: str | None # Name of latest buyer
#  Attribution (from Module 02, carried through) ---
attribution_confidence: float # 0.01.0, speaker attribution reliability
buyer_role_confidence: float # 0.01.0, buyer role assignment reliability
GENSE Thread State Schema 7

#  Stage & Intent (set by Module 04 
deal_stage: str # Enum: see Section 3.1. Default: "triage"
stage_confidence: float # 0.01.0. Default: 0.0
buyer_intent: str # Enum: see Section 3.2. Default: "unclear" NEVER None)
intent_confidence: float # 0.01.0. Default: 0.0
#  Open Loops (extracted by Module 03 
open_loops: List[OpenLoop] # Array of open loop objects
open_loop_count: int # len(open_loops) where resolution_status == "open"
oldest_open_loop_age: int | None # Turns since oldest open loop created
#  Commitments (extracted by Module 03 
commitments_made: List[Commitment] # Seller commitments to buyer
commitments_received: List[Commitment]# Buyer commitments to seller
commitment_drift_flag: bool # True if seller missed a commitment
#  Risk & Friction ---
risk_level: str # Enum: "low" | "medium" | "high" | "critical"
risk_factors: List[str] # Array of risk factor codes Module 04
objection_tags: List[str] # Array of objection type codes Module 03 extracts)
friction_pattern: str | None # Enum: see Section 3.3
#  Interaction History (computed by Module 03 
total_turns: int # Total turns in thread
seller_turns: int # Seller-authored turns
buyer_turns: int # Buyer-authored turns
last_seller_action: str | None # Last action ID executed 124
last_seller_cta: str | None # Last CTA type used
last_seller_timestamp: str | None # ISO8601 of last seller turn
last_3_actions: List[str] # Most recent 3 actions (newest first)
last_3_ctas: List[str] # Most recent 3 CTAs (newest first)
days_since_last_buyer: int # Days since last buyer response
response_velocity_avg: float | None # Average days between responses
#  Stakeholders (built by Module 03, enriched by Module 04 
stakeholders: List[Stakeholder] # Per-participant state
stakeholder_count: int # Count of non-seller stakeholders
# ================================================================
# TIER 2b: UPSTREAM GATING (v1.0.2 ADDITION
# From Module 02, carried forward unchanged. TOPLEVEL fields.
# ================================================================
required_config_missing: bool # True if config incomplete
missing_config_fields: List[str] # Which fields are missing
parse_status: str # "success" | "blocked" | "partial"
# ================================================================
# TIER 3 DERIVED STATE (computed fields, GRRIPS execution)
# ================================================================
#  GRRIPS Execution State (set by Module 07 
GENSE Thread State Schema 8

last_grrips_node: str | None # Last GRRIPS node executed
grrips_failure_tag: str | None # If generation failed, which node
repair_node: str | None # Node targeted for drift repair
#  Action History (updated after each execution) ---
cta_repeat_flag: bool # True if same CTA used 2x consecutively
action_diversity_score: float | None # 0.01.0, variety in recent actions
#  Stakeholder Delta (v1.0.1 
stakeholder_delta_last_turn: int # New stakeholders added in most recent turn
#  Replay Support (v1.0.1 
decision_trace_id: str | None # Pointer to decision trace artifact
message_artifact_id: str | None # Pointer to compiled outbound message
#  Metadata ---
state_version: str # Schema version (e.g., "1.0.2")
state_updated_at: str # ISO8601 timestamp of last update
5.2 Field Count Verification
Tier Field Count
Thread Core 8
Current State  Turns & Attribution 7
Current State  Stage & Intent 4
Current State  Open Loops 3
Current State  Commitments 3
Current State  Risk & Friction 4
Current State  Interaction History 10
Current State  Stakeholders 2
Upstream Gating (v1.0.2 3
Derived State  GRRIPS 3
Derived State  Action History 2
Derived State  Stakeholder Delta (v1.0.1 1
Derived State  Replay Support (v1.0.1 2
Metadata 2
TOTAL 54
GENSE Thread State Schema 9

Note: The "47 fields" claim in older documents was approximate. v1.0.1
established 51 fields. v1.0.2 adds 3 upstream gating fields for a canonical count
of 54 fields. All downstream specs must reference this count.
6. Nested Object Schemas
6.1 Turn Object (from Module 02)
python
@dataclass
class Turn:
turn_number: int # 1-indexed position in thread
speaker_email: str | None # Email if identified
speaker_name: str | None # Name if identified
speaker_role: Literal["buyer", "seller", "unknown"]
timestamp: str | None # ISO8601 or None
timestamp_source: str | None # "header" | "wrote_line" | "inferred" | None
content: str # Cleaned content (signatures/footers stripped)
raw_content: str # Original content before cleaning
content_type: Literal["original", "forwarded", "quoted", "administrative"]
attribution: TurnAttribution # Attribution details
@dataclass
class TurnAttribution:
method: Literal["header_from", "from_block", "wrote_line",
"signature_email", "signature_name",
"known_participant", "unknown"]
confidence: float # 0.01.0
evidence: List[str] # Evidence strings
6.2 OpenLoop Object (extracted by Module 03)
python
@dataclass
class OpenLoop:
loop_id: str # Unique identifier (e.g., "ol_001")
type: Literal["explicit_question", "implicit_concern",
"process_blocker", "vague_signal"]
priority: Literal["high", "medium", "low"]
resolution_status: Literal["open", "answered", "acknowledged", "deferred"]
resolution_method: str | None # v1.0.1 "in_text" | "attachment" | "link" |
# "meeting" | "other" | None
content: str # The question/concern text
owner_email: str | None # Stakeholder who raised it
created_at_turn: int # Turn number 1-based)
age_turns: int # Turns since creation
GENSE Thread State Schema 10

resolved_at_turn: int | None # Turn number where resolved (if resolved)
resolved_at: str | None # ISO8601 timestamp of resolution
follow_up_commitment_id: str | None # v1.0.1 Linked commitment if deferred
Priority Assignment Rules:
high: Explicit questions requiring direct answer, blocking concerns
medium: Implicit concerns, non-blocking questions
low: Vague signals, nice-to-have clarifications
Resolution Status Transitions:
open → answered: Direct answer provided
open → acknowledged: Concern noted but not resolved
open → deferred: Explicitly postponed with reason
6.3 Commitment Object (extracted by Module 03)
python
@dataclass
class Commitment:
commitment_id: str # Unique identifier (e.g., "cmt_001")
type: Literal["deliverable", "meeting", "follow_up", "information", "decision"]
description: str # What was committed
maker_email: str # Who made the commitment
maker_role: Literal["buyer", "seller"]
recipient_email: str | None # Who receives the commitment
created_at_turn: int # Turn number where commitment made
deadline_at: str | None # ISO8601 deadline (if specified)
deadline_type: Literal["explicit", "implicit", "none"]
status: Literal["pending", "fulfilled", "missed", "cancelled"]
fulfilled_at_turn: int | None # Turn number where fulfilled
missed_reason: str | None # If missed, why
Commitment Drift Flag Logic:
python
commitment_drift_flag = any(
c.maker_role == "seller" and c.status == "missed"
for c in commitments_made
)
6.4 Stakeholder Object (built by Module 03, enriched by Module
04)
GENSE Thread State Schema 11

python
@dataclass
class Stakeholder:
#  Identity (set by Module 03 
stakeholder_id: str # Unique identifier
email: str # Email address
name: str | None # Display name
speaker_role: Literal["buyer", "seller", "unknown"]
#  Role Detection (set by Module 04 
role_detected: str | None # "champion" | "decision_maker" | "influencer" |
# "evaluator" | "legal" | "security" |
# "procurement" | "blocker" | "unknown" | None
role_confidence: float # 0.01.0
is_blocker: bool # True if detected as blocker
detection_evidence: List[str] # Evidence for role detection
#  State Tracking (set by Module 03 
sentiment_current: str | None # "positive" | "neutral" | "negative" | None
sentiment_trend: str | None # "improving" | "stable" | "declining" | None
open_loops_owned: List[str] # loop_ids this stakeholder raised
objections_raised: List[str] # objection_tags from this stakeholder
pressure_tolerance: str | None # "high" | "medium" | "low" | None
#  Contact Flags ---
is_primary_contact: bool # Primary point of contact
turn_count: int # Number of turns from this stakeholder
last_turn: int | None # Most recent turn number
6.5 Participant Object (from Module 02)
python
@dataclass
class Participant:
email: str
name: str | None
role: Literal["buyer", "seller", "unknown"]
7. Field Ownership Table
Field Owner Write) Consumers Read)
Thread Core
thread_id Module 02 04, 06, 07
thread_created_at Module 02 04
GENSE Thread State Schema 12

Field Owner Write) Consumers Read)
source_channel Module 03 (config) —
account_id Module 03 (config) —
account_tier Module 03 (config) 06
vertical Module 03 (config) 07
product_context Module 03 (config) 07
seller_assigned Module 03 (config) —
Turns & Attribution
turns Module 02 03, 04, 07
participants Module 02 03, 04
latest_buyer_turn Module 02 04, 06, 07
latest_buyer_content Module 02 04, 07
latest_buyer_name Module 02 07
attribution_confidence Module 02 04, 06
buyer_role_confidence Module 02 06
Stage & Intent
deal_stage Module 04 06, 07
stage_confidence Module 04 06
buyer_intent Module 04 06, 07
intent_confidence Module 04 06
Open Loops
open_loops Module 03 04, 06, 07
open_loop_count Module 03 04, 06
oldest_open_loop_age Module 03 06
Commitments
commitments_made Module 03 06, 07
commitments_received Module 03 06
commitment_drift_flag Module 03 06, 07
Risk & Friction
GENSE Thread State Schema 13

Field Owner Write) Consumers Read)
risk_level Module 04 06, 07
risk_factors Module 04 06
objection_tags Module 03 (v1.0.1 single owner) 04, 06
friction_pattern Module 03 06
Interaction History
total_turns Module 03 04, 06
seller_turns Module 03 04, 06
buyer_turns Module 03 04
last_seller_action Module 03 (post-exec) 06
last_seller_cta Module 03 (post-exec) 06, 07
last_seller_timestamp Module 03 (post-exec) —
last_3_actions Module 03 (post-exec) 06
last_3_ctas Module 03 (post-exec) 06, 07
days_since_last_buyer Module 03 04, 06
response_velocity_avg Module 03 —
Stakeholders
Module 03 (built), Module 04 (enriches
stakeholders 06, 07
role fields)
stakeholder_count Module 03 04, 06
Upstream Gating (v1.0.2
required_config_missing Module 02 (carried through) 04, 06 HB_001
04, 06 (error
missing_config_fields Module 02 (carried through)
context)
parse_status Module 02 (carried through) 04, 06 HB_003
GRRIPS Execution
last_grrips_node Module 07 09
grrips_failure_tag Module 07 09
repair_node Module 09 07
Action History
GENSE Thread State Schema 14

Field Owner Write) Consumers Read)
cta_repeat_flag Module 03 (computed) 06, 09
action_diversity_score Module 03 (computed) —
Stakeholder Delta (v1.0.1
stakeholder_delta_last_turn Module 03 (computed) 04, 06
Replay Support (v1.0.1
decision_trace_id Module 06 / Orchestrator 09, 13
message_artifact_id Module 07 / Orchestrator 09, 13
Metadata
state_version Module 03 —
state_updated_at Module 03 —
8. Enumeration Values
All enumerations are defined in Canonical_Enumerations.pdf v1.0.0 as the single
source of truth. This section lists values for quick reference. Module-level code
MUST import from Canonical_Enumerations.
8.1 Deal Stages
python
DEAL_STAGES  "triage", "discovery", "evaluation", "proposal", "procurement", "negotiation", "closed_won",
"closed_lost"]
8.2 Buyer Intents
python
BUYER_INTENTS  
"question_product", "question_pricing", "question_process",
"question_technical", "question_security", "question_reference",
"objection_timing", "objection_budget", "objection_authority",
"objection_need", "objection_competition",
"commitment_signal", "commitment_request",
"information_share", "administrative", "unclear"
]
8.3 Risk Levels
python
GENSE Thread State Schema 15

RISK_LEVELS  "low", "medium", "high", "critical"]
8.4 Risk Factors
python
RISK_FACTORS  
"rf_legal_involved", "rf_security_involved", "rf_procurement_involved",
"rf_executive_involved", "rf_competitor_mentioned", "rf_budget_concern",
"rf_timeline_pressure", "rf_stakeholder_blocker", "rf_commitment_missed",
"rf_response_delay", "rf_negative_sentiment", "rf_deal_at_risk",
"rf_escalation_threat"
]
8.5 Friction Patterns
python
FRICTION_PATTERNS  "stall", "ghosting", "circular", "escalation", "none"]
8.6 Open Loop Types
python
OPEN_LOOP_TYPES  "explicit_question", "implicit_concern", "process_blocker", "vague_signal"]
OPEN_LOOP_PRIORITIES  "high", "medium", "low"]
OPEN_LOOP_RESOLUTION_STATUSES  "open", "answered", "deferred", "stale"]
8.7 Commitment Types
python
COMMITMENT_TYPES  "deliverable", "meeting", "follow_up", "information", "decision"]
COMMITMENT_STATUSES  "pending", "fulfilled", "missed", "cancelled"]
8.8 CTA Types
Authoritative Source: Message OS GRRIPS Module 07 v1.3.1.
python
CTA_TYPES  "none", "opt_out", "question", "async_review", "async_choice", "calendar_light",
"calendar_two_windows"]
CTA_PRESSURE  
"none" 0,
"opt_out" 0,
"question" 1,
"async_review" 2,
"async_choice" 2,
"calendar_light" 3,
GENSE Thread State Schema 16

"calendar_two_windows" 3,
}
8.9 Source Channels
python
SOURCE_CHANNELS  "email", "scrape", "forward"]
9. Priority Locks / Global Constraints
ThreadState fields directly drive Policy Engine priority locks:
Lock ThreadState Field Condition Effect
PL_001
Force Action 10
(Commitment commitment_drift_flag  True
ONLY
Recovery)
Any with priority=="high"
PL_002 Open Restrict to
open_loops AND
Loop Priority) Actions 111
resolution_status=="open"
PL_003 Open Any with Block Actions 17
open_loops
Loop Soft) resolution_status=="open" 20
Pressure ceiling =
0; whitelist CTAs:
PL_004 Critical
risk_level == "critical" none,
Risk)
async_review,
opt_out
PL_005 Stall Prefer Actions 23,
days_since_last_buyer >= stall_threshold
Preference) 24
PL_006 CTA Block repeated
last_3_ctas Same CTA 2x consecutively
Repetition) CTA type
Action IDs reference Module 05 Action Set & Command Tree) v1.0.5 canonical
action registry.
10. Failure Modes
GENSE Thread State Schema 17

Code Trigger Response
Module 02 output missing
FM_TS_001 Block, return validation errors
required fields
FM_TS_002 turns array empty Block, reason = "no_turns"
latest_buyer_turn index out of Block, reason =
FM_TS_003
bounds "invalid_buyer_turn_index"
Block, return field path and expected
FM_TS_004 Type mismatch in nested object
type
FM_TS_005 Unknown enum value Block, return field and invalid value
11. Validation Checks
On Construction
thread_id is non-empty string
turns is non-empty array
latest_buyer_turn is valid turn_number 1-based) that exists in turns array
attribution_confidence is in range 0.0, 1.0
buyer_role_confidence is in range 0.0, 1.0
All enum fields contain valid values (per Canonical_Enumerations.pdf)
buyer_intent defaults to "unclear" NEVER None/null)
deal_stage defaults to "triage" NEVER None/null)
All open_loops have unique loop_id
All commitments_made have unique commitment_id
All stakeholders have unique stakeholder_id
parse_status is one of: "success", "blocked", "partial" (v1.0.2
required_config_missing is bool (v1.0.2
On Update
state_updated_at is updated to current timestamp
GENSE Thread State Schema 18

state_version matches schema version
Immutable fields Thread Core) are not modified
open_loop_count equals count of loops where resolution_status == "open"
commitment_drift_flag is consistent with commitments_made statuses
Gating fields (required_config_missing, missing_config_fields, parse_status)
are never modified by Module 03 (v1.0.2
12. Worked Examples
Example 1: Simple Valid ThreadState (First Inbound)
json
{
"thread_id": "thr_test_001",
"thread_created_at": "20260120T090000Z",
"source_channel": "email",
"account_id": null,
"account_tier": null,
"vertical": null,
"product_context": null,
"seller_assigned": null,
"turns": [
{
"turn_number" 1,
"speaker_email": "buyer@acme.com",
"speaker_name": "Sarah Chen",
"speaker_role": "buyer",
"timestamp": "20260120T090000Z",
"timestamp_source": "header",
"content": "Hi, I saw your product and have a question about integrations.",
"raw_content": "Hi, I saw your product...[signature stripped]",
"content_type": "original",
"attribution": {
"method": "header_from",
"confidence" 0.95,
"evidence": ["From header match"]
}
}
],
"participants": [
{"email": "buyer@acme.com", "name": "Sarah Chen", "role": "buyer"}
],
"latest_buyer_turn" 1,
"latest_buyer_content": "Hi, I saw your product and have a question about integrations.",
GENSE Thread State Schema 19

"latest_buyer_name": "Sarah Chen",
"attribution_confidence" 0.95,
"buyer_role_confidence" 0.90,
"deal_stage": "triage",
"stage_confidence" 0.0,
"buyer_intent": "unclear",
"intent_confidence" 0.0,
"open_loops": [
{
"loop_id": "ol_001",
"type": "explicit_question",
"priority": "high",
"resolution_status": "open",
"resolution_method": null,
"content": "question about integrations",
"owner_email": "buyer@acme.com",
"created_at_turn" 1,
"age_turns" 0,
"resolved_at_turn": null,
"resolved_at": null,
"follow_up_commitment_id": null
}
],
"open_loop_count" 1,
"oldest_open_loop_age" 0,
"commitments_made": [],
"commitments_received": [],
"commitment_drift_flag": false,
"risk_level": "low",
"risk_factors": [],
"objection_tags": [],
"friction_pattern": "none",
"total_turns" 1,
"seller_turns" 0,
"buyer_turns" 1,
"last_seller_action": null,
"last_seller_cta": null,
"last_seller_timestamp": null,
"last_3_actions": [],
"last_3_ctas": [],
"days_since_last_buyer" 0,
"response_velocity_avg": null,
"stakeholders": [
{
"stakeholder_id": "sh_001",
"email": "buyer@acme.com",
"name": "Sarah Chen",
"speaker_role": "buyer",
"role_detected": null,
"role_confidence" 0.0,
"is_blocker": false,
"detection_evidence": [],
GENSE Thread State Schema 20

"sentiment_current": "neutral",
"sentiment_trend": null,
"open_loops_owned": ["ol_001"],
"objections_raised": [],
"pressure_tolerance": null,
"is_primary_contact": true,
"turn_count" 1,
"last_turn" 1
}
],
"stakeholder_count" 1,
"required_config_missing": false,
"missing_config_fields": [],
"parse_status": "success",
"last_grrips_node": null,
"grrips_failure_tag": null,
"repair_node": null,
"cta_repeat_flag": false,
"action_diversity_score": null,
"stakeholder_delta_last_turn" 1,
"decision_trace_id": null,
"message_artifact_id": null,
"state_version": "1.0.2",
"state_updated_at": "20260120T100000Z"
}
Example 2: Commitment Drift Scenario
json
{
"thread_id": "thr_drift_002",
"commitment_drift_flag": true,
"commitments_made": [
{
"commitment_id": "cmt_001",
"type": "deliverable",
"description": "Send security whitepaper by Friday",
"maker_email": "seller@ourco.com",
"maker_role": "seller",
"recipient_email": "buyer@acme.com",
"created_at_turn" 3,
"deadline_at": "20260117T170000Z",
"deadline_type": "explicit",
"status": "missed",
"fulfilled_at_turn": null,
"missed_reason": "Deadline passed without delivery"
}
],
"required_config_missing": false,
"missing_config_fields": [],
GENSE Thread State Schema 21

"parse_status": "success"
}
When commitment_drift_flag == true, Policy Engine triggers PL_001
(Commitment Recovery Lock), forcing Action 10 only.
Example 3: Multi-Stakeholder with Risk Elevation
json
{
"thread_id": "thr_multi_003",
"stakeholders": [
{
"stakeholder_id": "sh_001",
"email": "buyer@acme.com",
"role_detected": "champion",
"role_confidence" 0.88,
"is_blocker": false,
"is_primary_contact": true
},
{
"stakeholder_id": "sh_002",
"email": "legal@acme.com",
"role_detected": "legal",
"role_confidence" 0.90,
"is_blocker": false,
"is_primary_contact": false
},
{
"stakeholder_id": "sh_003",
"email": "ciso@acme.com",
"role_detected": "security",
"role_confidence" 0.85,
"is_blocker": true,
"is_primary_contact": false
}
],
"risk_level": "high",
"risk_factors": ["rf_legal_involved", "rf_security_involved", "rf_stakeholder_blocker"],
"required_config_missing": false,
"missing_config_fields": [],
"parse_status": "success"
}
13. Test Vectors
TV_TS_001: Simple Valid ThreadState
GENSE Thread State Schema 22

json
{
"test_id": "TV_TS_001",
"test_type": "simple",
"description": "Minimal valid ThreadState construction",
"input": {
"module_02_output": {
"status": "success",
"thread_id": "thr_test_001",
"turns": [{"turn_number" 1, "speaker_role": "buyer", "content": "Hello"}],
"participants": [{"email": "test@test.com", "role": "buyer"}],
"latest_buyer_turn" 1,
"latest_buyer_content": "Hello",
"attribution_confidence" 0.85,
"buyer_role_confidence" 0.80,
"required_config_missing": false,
"missing_config_fields": []
}
},
"expected_output": {
"validation_passed": true,
"thread_state": {
"thread_id": "thr_test_001",
"open_loop_count" 0,
"commitment_drift_flag": false,
"parse_status": "success",
"required_config_missing": false,
"state_version": "1.0.2"
}
},
"assertions": [
"validation_passed == true",
"thread_state.thread_id == 'thr_test_001'",
"thread_state.commitment_drift_flag == false",
"thread_state.parse_status == 'success'",
"thread_state.required_config_missing == false"
]
}
TV_TS_002: Edge Case — Commitment Drift Detection
json
{
"test_id": "TV_TS_002",
"test_type": "edge",
"description": "Commitment drift flag triggers correctly when seller commitment missed",
"input": {
"commitments_made": [
{
"commitment_id": "cmt_001",
GENSE Thread State Schema 23

"maker_role": "seller",
"status": "missed"
}
]
},
"expected_output": {
"commitment_drift_flag": true
},
"assertions": [
"commitment_drift_flag == true"
]
}
TV_TS_003: Failure — Invalid Enum Value
json
{
"test_id": "TV_TS_003",
"test_type": "failure",
"description": "Invalid deal_stage enum value rejected",
"input": {
"deal_stage": "invalid_stage"
},
"expected_output": {
"validation_passed": false,
"error_code": "FM_TS_005",
"error_detail": "Invalid enum value 'invalid_stage' for field 'deal_stage'"
},
"assertions": [
"validation_passed == false",
"error_code == 'FM_TS_005'"
]
}
TV_TS_004: Gating Field Propagation (v1.0.2)
json
{
"test_id": "TV_TS_004",
"test_type": "simple",
"description": "Upstream gating fields carried through unchanged",
"input": {
"module_02_output": {
"status": "success",
"required_config_missing": true,
"missing_config_fields": ["vertical", "product_context"]
}
},
"expected_output": {
"parse_status": "success",
GENSE Thread State Schema 24

"required_config_missing": true,
"missing_config_fields": ["vertical", "product_context"]
},
"assertions": [
"thread_state.parse_status == 'success'",
"thread_state.required_config_missing == true",
"thread_state.missing_config_fields == ['vertical', 'product_context']",
"gating fields are top-level, not nested"
]
}
14. Contract Alignment
14.1 Upstream Contract (Module 02 → Module 03)
Module 02 Output Field ThreadState Field Transform
thread_id thread_id Direct copy
turns turns Direct copy
participants participants Direct copy
latest_buyer_turn latest_buyer_turn Direct copy
latest_buyer_content latest_buyer_content Direct copy
attribution_confidence attribution_confidence Direct copy
buyer_role_confidence buyer_role_confidence Direct copy
Rename: status → parse_status
status parse_status
(v1.0.2
required_config_missing required_config_missing Direct copy (v1.0.2
missing_config_fields missing_config_fields Direct copy (v1.0.2
⚠ Propagation Contract (v1.0.2 Module 03 MUST carry Module 02 gating
fields forward unchanged (top-level). Modules 04/06/07 MAY read gating fields
but MUST NOT modify them. If parse_status == "blocked", Policy Engine
triggers HB_003.
14.2 Downstream Contracts
Module 04 Required Fields:
python
GENSE Thread State Schema 25

REQUIRED_BY_MODULE_04  
"thread_id", "turns", "latest_buyer_turn", "latest_buyer_content",
"attribution_confidence", "buyer_role_confidence",
"open_loops", "open_loop_count", "commitment_drift_flag",
"total_turns", "days_since_last_buyer", "stakeholders", "stakeholder_count",
"required_config_missing", "missing_config_fields", "parse_status" # v1.0.2
]
Module 06 Required Fields:
python
REQUIRED_BY_MODULE_06  
"thread_id", "deal_stage", "stage_confidence", "buyer_intent", "intent_confidence",
"open_loops", "open_loop_count", "risk_level", "commitment_drift_flag",
"attribution_confidence", "buyer_role_confidence",
"total_turns", "seller_turns", "days_since_last_buyer",
"last_seller_action", "last_seller_cta", "last_3_actions", "last_3_ctas",
"stakeholder_count", "stakeholders",
"required_config_missing", "missing_config_fields", "parse_status" # v1.0.2
]
Module 07 Required Fields:
python
REQUIRED_BY_MODULE_07  
"latest_buyer_name", "latest_buyer_content", "buyer_intent", "risk_level",
"turns", "open_loops", "commitment_drift_flag", "stakeholders",
"deal_stage", "last_3_ctas"
]
End of Module 03 Specification v1.0.2
GENSE Thread State Schema 26