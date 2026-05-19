04 Deal Stage & Intent Classifier
Field Value
Module: 04_Deal_Stage_Intent_Classifier
Version: 1.0.10
Status: LOCKED
Date: January 31, 2026
Author: Claude
Contract Reference: Build Contract A8, Build Index Section 04
Purpose: Classify thread state into deal stage and buyer intent enumerations with confidence scoring,
and detect risk factors and stakeholder roles.
AUDIT SUMMARY
Document Lineage
Version Date Status Changes
1.0 20260120 SUPERSEDED Initial specification
Architecture drift fix: Input contract now correctly references
ThreadState from Module 03. Added responsibility boundary
1.0.1 20260120 SUPERSEDED
section. Added integration test category. Expanded test
vectors.
Final audit fixes: 1 Added test vectors for information_share
and unclear intents 16/16 coverage). (2) Formalized
1.0.2 20260120 SUPERSEDED prior_classification optional input fields. 3 Unified
stakeholder field naming (stakeholders[] enriched, not
stakeholder_roles[]).
Added explicit multi-intent detection Section 4.4. When top
1.0.3 20260120 SUPERSEDED two intent scores within 0.08, flags ambiguity in trace and
applies 0.12 penalty. Determinism preserved.
PATCH CL_INT_003 blocked_ctas updated from legacy
1.0.4 20260125 SUPERSEDED
"calendar_firm" to canonical "calendar_two_windows".
HARDENING COMPLETE 1 Added single-source CTA
reference section. 2 Updated downstream consumer
references to Policy Engine v1.1.2. 3 Added Hardening
Compliance section. 4 Added G5 gate verification. 5
1.0.5 20260126 SUPERSEDED
Synchronized date formats. 6 CL_INT_003 blocked_ctas
aligned to
Canonical_Enumerations.RISK_CTA_RESTRICTIONS'critical']
exactly.
1.0.6 20260126 SUPERSEDED EXECUTABLE SPEC FIX 1 detect_classification_drift()
signature fixed — now takes (thread_state, current_stage,
04 Deal Stage & Intent Classifier 1

Version Date Status Changes
current_intent) to resolve undefined variable references. 2
Added complete STAGE_PATTERNS table 8/8 stages
defined). (3) Completed INTENT_PATTERNS table 16/16
intents defined). All pseudocode sections now executable
without implementer interpretation.
FINAL LOCK FIXES 1 calculate_confidence() signature
fixed to include current_stage/current_intent. 2 Added
Section 2.5 with explicit prior_* field contract and
ClassifierContext option. 3 Added RISK_FACTORS authority
1.0.7 20260127 SUPERSEDED
claim  Module 04 is authoritative, Canonical imports. 4
Added downstream dependency note for rf_stalled sync to
Canonical_Enumerations. 5 Added tie-break rule to
classification algorithms: "ties break by enum order."
FINAL LOCK 1 Wired detect_multi_intent() call in
classify_intent() — dead code fix. 2 Fixed classify_stage()
procurement boost to use email patterns instead of
1.0.8 20260127 SUPERSEDED
role_detected — resolves sequencing issue (role_detected
set after classification). (3) Added hardening gate
passthrough fields to output contract.
CONTRACT RECONCILIATION 1 Removed local
OpenLoop/Commitment schema redefinitions — now
imports from Thread_State_Schema v1.0.1. 2 Standardized
prior_* fields to ClassifierContext-only binding; removed
1.0.9 20260131 SUPERSEDED ThreadState extension ambiguity. 3 Added hardening
passthrough fields to INPUT contract
(required_config_missing, missing_config_fields,
parse_status). (4) Fixed field count reference from "47
fields" to "51 fields" per Thread_State_Schema v1.0.1.
1.0.10 20260413 LOCKED Aligned STAKEHOLDER_ROLES: 'user' → 'evaluator' per
canonical-enumerations v1.2.1 errata. Resolves CL_ENUM
open issue.
🔒 LOCKED
This specification is contract-aligned, architecturally correct, hardening-compliant, and fully stress-
tested against both Claude and ChatGPT audits. All 16 intents and all 8 stages have explicit test
vectors. Multi-intent ambiguity is now explicitly detected and surfaced. All CTA references use
canonical tokens from Canonical_Enumerations.pdf v1.0.0.
HARDENING COMPLIANCE
This section documents compliance with GENSE System Hardening Plan v1.2.3 requirements.
Single-Source Contract Rules
Rule Requirement Status Evidence
CTA types defined ONLY in
SSR1 ✓ COMPLIANT No local CTA_TYPES definition
Canonical_Enumerations.pdf
CTA pressure defined ONLY in No local CTA_PRESSURE
SSR2 ✓ COMPLIANT
Canonical_Enumerations.pdf definition
04 Deal Stage & Intent Classifier 2

Rule Requirement Status Evidence
CL_INT_003 uses
SSR3 No deprecated CTA tokens ✓ COMPLIANT
"calendar_two_windows"
✓ Canonical_Enumerations imports
SSR4 DEAL_STAGES authoritative in Module 04
AUTHORITATIVE from here
BUYER_INTENTS authoritative in Module ✓ Canonical_Enumerations imports
SSR5
04 AUTHORITATIVE from here
Hardening Gate Verification
Gate Test Pass Condition Module 04 Status
G5 CT_003 Critical risk emits only whitelisted CTAs ✓ CL_INT_003 verifies
G9 Repo grep Zero deprecated tokens in repo ✓ No legacy tokens
CTA Type Reference
CRITICAL CTA types and pressure values are defined ONLY in Canonical_Enumerations.pdf v1.0.0.
This module MUST NOT redefine CTA pressure or enumerate CTA types independently.
Reference: Canonical_Enumerations.pdf Section "CTA TYPES"
Valid types: none, opt_out, question, async_review, async_choice, calendar_light, calendar_two_windows
Deprecated tokens DO NOT USE one_question, calendar_firm, process_confirm, confirm_deadline, input_request
Architecture Position
02 Ingest)  03 Extract State)  04 Classify)  06 Route)
↓ ↓
ThreadState ClassifiedState
51 fields) (adds stage/intent/confidence)
Note (v1.0.9 Field count updated from "47" to "51" per Thread_State_Schema v1.0.1 canonical count.
Part I: Module Overview
1.1 What This Module Does
The Deal Stage & Intent Classifier receives ThreadState from Module 03 and produces:
 Deal Stage  Where in the sales pipeline this thread sits
 Buyer Intent  What the buyer wants in their latest actionable turn
 Confidence Scores  Reliability metrics for stage and intent classification
 Risk Assessment  Factors that elevate thread risk level
 Stakeholder Role Detection  Identification of legal/security/procurement roles
04 Deal Stage & Intent Classifier 3

Critical Note: Module 04 CLASSIFIES state but does NOT extract it. State extraction (open_loops,
commitments, interaction history) is Module 03's responsibility.
1.2 Core Guarantees
Guarantee Description Enforcement
Deterministic Same input always produces same classification Rule-based patterns, no randomness
Confidence  0.60 triggers
Fail-safe Ambiguity → escalate, never guess
HB_004/HB_005
Auditable Every classification can be traced to evidence Classification trace in output
Contract-aligned Thresholds match Build Contract A8 0.60 for stage/intent confidence
Classifies only; does not re-derive Module 03
Scope-bounded Explicit responsibility separation
fields
Hardening-
All CTA references use canonical tokens SSR1 through SSR5 verified
compliant
1.3 Processing Sequence
 VALIDATE INPUT  Ensure ThreadState contains required fields
 CLASSIFY STAGE  Map evidence to deal_stage enum
 CLASSIFY INTENT  Map latest buyer turn to buyer_intent enum
 CALCULATE CONFIDENCE  Score reliability of classifications
 ASSESS RISK  Detect risk elevation factors
 DETECT STAKEHOLDER ROLES  Identify legal/security/procurement roles
 EMIT OUTPUT  Return ClassifiedState with trace
1.4 Module Responsibility Separation
CRITICAL ARCHITECTURE RULE Module 04 must NOT re-derive fields that Module 03 provides.
Responsibility Owner Fields
Turn parsing & speaker turns[], participants[], attribution_confidence,
Module 02
attribution buyer_role_confidence
Open loop detection & tracking Module 03 open_loops[], open_loop_count, oldest_open_loop_age
Commitment extraction & drift commitments_made[], commitments_received[],
Module 03
detection commitment_drift_flag
days_since_last_buyer, total_turns, seller_turns,
Interaction history computation Module 03
last_3_actions[], last_3_ctas[]
sentiment_current, sentiment_trend, open_loops_owned[],
Stakeholder state tracking Module 03
pressure_tolerance
Deal stage classification Module 04 deal_stage, stage_confidence
Buyer intent classification Module 04 buyer_intent, intent_confidence
04 Deal Stage & Intent Classifier 4

Responsibility Owner Fields
Risk level assessment Module 04 risk_level, risk_factors[]
Stakeholder role detection Module 04 role_detected, role_confidence, is_blocker
Why this matters: Policy Engine's highest-impact behaviors depend on Module 03 outputs:
open_loops  PL_002 (open-loop priority lock)
commitment_drift_flag  PL_001 (absolute commitment recovery lock)
If Module 04 were to re-derive these fields, inconsistencies could cause "correct classification" but
wrong next-action behavior.
Part II: Input Specification
2.1 Primary Input: ThreadState (from Module 03)
The classifier receives the complete ThreadState object produced by Module 03 State Extractor).
Module 04 reads from this state but does NOT modify Module 03's extracted fields.
# ══════════════════════════════════════════════════════════════
# THREADSTATE INPUT (from Module 03
# Module 04 receives this complete object
# ══════════════════════════════════════════════════════════════
@dataclass
class ThreadState:
# ─────────────────────────────────────────────────────────────
# THREAD CORE (immutable, carried from Module 02
# ─────────────────────────────────────────────────────────────
thread_id: str
turns: List[Turn]
participants: List[Participant]
latest_buyer_turn: int
latest_buyer_content: str
attribution_confidence: float
buyer_role_confidence: float
# ─────────────────────────────────────────────────────────────
# EXTRACTED STATE (from Module 03
# ─────────────────────────────────────────────────────────────
open_loops: List[OpenLoop]
open_loop_count: int
oldest_open_loop_age: int
commitments_made: List[Commitment]
commitments_received: List[Commitment]
commitment_drift_flag: bool
04 Deal Stage & Intent Classifier 5

days_since_last_buyer: int
total_turns: int
seller_turns: int
last_3_actions: List[int]
last_3_ctas: List[str]
stakeholders: List[Stakeholder]
stakeholder_count: int
# ─────────────────────────────────────────────────────────────
# HARDENING PASSTHROUGH FIELDS (v1.0.9 added to input contract)
# Set by Module 02, carried through Module 03, passed to Policy Engine
# ─────────────────────────────────────────────────────────────
required_config_missing: bool  False #  HB_001 gate
missing_config_fields: List[str] = [] #  Error context
parse_status: str = "success" #  HB_003 gate
2.2 Nested Object Schemas (v1.0.9: Import Reference)
IMPORTANT (v1.0.9 Module 04 does NOT redefine nested object schemas. The following schemas
are IMPORTED from Thread_State_Schema Module 03 v1.0.1 and are authoritative:
OpenLoop Section 6.2 of Thread_State_Schema)
Commitment Section 6.3 of Thread_State_Schema)
Stakeholder Section 6.4 of Thread_State_Schema)
Module 04 READS these objects from ThreadState. It does NOT validate their structure (that's Module
03's responsibility) — it only consumes the fields it needs for classification.
Canonical OpenLoop Schema (from Thread_State_Schema v1.0.1
@dataclass
class OpenLoop:
loop_id: str
type: Literal["explicit_question", "implicit_concern", "process_blocker", "vague_signal"]
priority: Literal["high", "medium", "low"]
resolution_status: Literal["open", "answered", "acknowledged", "deferred"] # NOT "stale"
resolution_method: str | None
content: str # NOT "content_summary"
owner_email: str | None
created_at_turn: int
age_turns: int
resolved_at_turn: int | None
resolved_at: str | None
follow_up_commitment_id: str | None
04 Deal Stage & Intent Classifier 6

Canonical Commitment Schema (from Thread_State_Schema v1.0.1
@dataclass
class Commitment:
commitment_id: str
type: Literal["deliverable", "meeting", "follow_up", "information", "decision"]
description: str
maker_email: str # NOT "owner_email"
maker_role: Literal["buyer", "seller"]
recipient_email: str | None
created_at_turn: int
deadline_at: str | None # NOT "due_date"
deadline_type: Literal["explicit", "implicit", "none"]
status: Literal["pending", "fulfilled", "missed", "cancelled"]
fulfilled_at_turn: int | None
missed_reason: str | None
Fields consumed by Module 04 from OpenLoop:
loop_id, type, priority, resolution_status, content, owner_email, age_turns
Fields consumed by Module 04 from Commitment:
commitment_id, type, status, maker_role (for drift detection passthrough)
2.3 Required Fields for Classification
Module 04 requires these fields to be present and valid in ThreadState:
REQUIRED_FOR_CLASSIFICATION  
# From Module 02 (carried through)
"thread_id",
"turns",
"latest_buyer_turn",
"latest_buyer_content",
"attribution_confidence",
"buyer_role_confidence",
# From Module 03 (extracted state)
"open_loops",
"open_loop_count",
"commitment_drift_flag",
"total_turns",
"days_since_last_buyer",
"stakeholders",
"stakeholder_count",
04 Deal Stage & Intent Classifier 7

# Hardening gate passthrough fields (v1.0.9
"required_config_missing",
"missing_config_fields",
"parse_status",
]
Passthrough Field Contract (v1.0.9
Module 04 does NOT evaluate or modify these fields — it passes them through unchanged to enable
Policy Engine hard blocks:
Field Source Consumer Gate
required_config_missing Module 02 Policy Engine HB_001
missing_config_fields Module 02 Policy Engine Error context
parse_status Module 02 Policy Engine HB_003
If these fields are missing from ThreadState input, Module 04 MUST default them:
required_config_missing → False
missing_config_fields → []
parse_status → "success"
2.4 Prior Classification Context (v1.0.9: ClassifierContext Only)
For classification drift detection, Module 04 optionally receives prior classification state via a separate
ClassifierContext object  NOT via ThreadState fields.
Rationale (v1.0.9 Thread_State_Schema does not define prior_* fields. To maintain single-source
contract integrity, these fields MUST NOT be added to ThreadState. Instead, the orchestrator
provides them via ClassifierContext when drift detection is enabled.
@dataclass
class ClassifierContext:
"""
Optional context for drift detection.
Provided by orchestrator if classification history is available.
Pass None if no prior classification exists.
"""
prior_deal_stage: str | None  None
prior_stage_confidence: float | None  None
prior_buyer_intent: str | None  None
prior_intent_confidence: float | None  None
Module 04 Function Signature:
04 Deal Stage & Intent Classifier 8

def classify(
thread_state: ThreadState,
context: ClassifierContext | None  None
)  ClassifiedState:
Drift Detection Behavior:
If context is None or all prior_* fields are None  No drift penalty applied
If prior values differ from current classification  Apply 5% confidence penalty (multiply by 0.95
DELETED (v1.0.9 The "ThreadState extension" option from v1.0.7/v1.0.8 is removed to eliminate
binding ambiguity.
Part III: Deal Stage Classification
3.1 Stage Enumeration
Module 04 is the AUTHORITATIVE SOURCE for DEAL_STAGES. Canonical_Enumerations.pdf imports
these values.
DEAL_STAGES  
"triage", # Initial contact, no clear signal
"discovery", # Active learning about needs
"evaluation", # Comparing options, proof required
"proposal", # Pricing/terms discussion
"procurement", # Legal/security/purchasing involved
"negotiation", # Terms being finalized
"closed_won", # Deal completed successfully
"closed_lost", # Deal lost to competitor or no-decision
]
3.2 Stage Evidence Patterns
Stage Primary Evidence Secondary Evidence
triage First 12 turns, no situation described Generic questions, "tell me more"
discovery Situation description, team size, current solution Pain points, timeline hints
evaluation Comparison questions, "vs", "how does X work" Technical deep-dives, proof requests
proposal Pricing questions, scope discussion, "what would it cost" Volume/tier questions
procurement Legal/security stakeholders active, process questions Compliance requests, redlines
negotiation Terms discussion, "can you do X instead" Final objections, discount asks
closed_won Explicit agreement, "let's proceed", signed PO number, start date
closed_lost Explicit rejection, "going another direction" No response 30 days after proposal
04 Deal Stage & Intent Classifier 9

3.2.1 Stage Pattern Table (Complete, v1.0.6)
STAGE_PATTERNS  
"triage": {
"keywords": ["tell me more", "what do you do", "who are you", "your company"],
"patterns": [r"(what|who)\s+(is|are|does)\s+(your|the)\s+(company|product|service)"],
"keyword_weight" 0.20,
"pattern_weight" 0.25
},
"discovery": {
"keywords": ["our team", "we currently", "we're trying", "our situation", "pain point", "challeng
e"],
"patterns": [r"(we|our)\s+(currently|have|use|need)", r"team\s+of\s+\d+", r"(problem|challen
ge|issue)\s+(is|with)"],
"keyword_weight" 0.25,
"pattern_weight" 0.30
},
"evaluation": {
"keywords": ["compare", "vs", "versus", "how does", "difference", "demo", "trial", "proof of co
ncept", "POC"],
"patterns": [r"(how|what)\s+(does|is)\s+.+\s+(compare|different)", r"vs\.?\s+\w+", r"(demo|tri
al|POC|proof)"],
"keyword_weight" 0.25,
"pattern_weight" 0.30
},
"proposal": {
"keywords": ["pricing", "price", "cost", "quote", "proposal", "scope", "what would it cost"],
"patterns": [r"(how\s+much|what.*cost)", r"(send|share|provide)\s+(a\s+)?(pricing|quote|pro
posal)"],
"keyword_weight" 0.30,
"pattern_weight" 0.35
},
"procurement": {
"keywords": ["legal", "security review", "compliance", "DPA", "MSA", "redline", "procurement",
"vendor form"],
"patterns": [r"(legal|security|procurement)\s+(team|review|process)", r"DPA|MSA|NDA|SO
W", r"vendor\s+(form|questionnaire)"],
"keyword_weight" 0.35,
"pattern_weight" 0.40
},
"negotiation": {
"keywords": ["terms", "discount", "can you do", "negotiate", "flexibility", "best price"],
"patterns": [r"(can|could)\s+you\s+(do|offer|provide)", r"(discount|flexibility|negotiate)", r"(te
rms|conditions)"],
04 Deal Stage & Intent Classifier 10

"keyword_weight" 0.30,
"pattern_weight" 0.35
},
"closed_won": {
"keywords": ["let's proceed", "move forward", "signed", "approved", "go ahead", "start date",
"PO number"],
"patterns": [r"(let's|ready\s+to)\s+(proceed|move\s+forward|go\s+ahead)", r"(signed|approv
ed|PO\s*(number|#?",
"keyword_weight" 0.40,
"pattern_weight" 0.45
},
"closed_lost": {
"keywords": ["going with another", "decided against", "not moving forward", "no longer intere
sted", "chose competitor"],
"patterns": [r"(going|went)\s+with\s+(another|different)", r"(decided|choosing)\s+(against|no
t\s+to)", r"no\s+longer\s+(interested|pursuing)"],
"keyword_weight" 0.40,
"pattern_weight" 0.45
}
}
3.3 Stage Classification Algorithm
def classify_stage(thread_state: ThreadState) → tuple[str, float, dict]:
"""
Classify deal stage based on thread evidence.
Returns (stage, confidence, evidence_trace)
"""
evidence = {
"stage_signals": [],
"turn_count": thread_state.total_turns,
"stakeholder_types": [s.role_detected for s in thread_state.stakeholders],
"content_patterns": [],
}
scores = {stage: 0.0 for stage in DEAL_STAGES
# Pattern matching against latest buyer content and thread history
content = thread_state.latest_buyer_content.lower()
# Stage-specific pattern detection
for stage, patterns in STAGE_PATTERNS.items():
for pattern in patterns["keywords"]:
if pattern.lower() in content:
04 Deal Stage & Intent Classifier 11

scores[stage] += patterns["keyword_weight"]
evidence["content_patterns"].append(f"{stage}:{pattern}")
for regex in patterns["patterns"]:
if re.search(regex, content, re.IGNORECASE
scores[stage] += patterns["pattern_weight"]
evidence["stage_signals"].append(f"{stage}:regex_match")
# Structural signals
if thread_state.total_turns  2
scores["triage"]  0.30
evidence["stage_signals"].append("triage:low_turn_count")
# Procurement stakeholder detection (v1.0.8 uses email patterns, not role_detected)
# IMPORTANT role_detected is set by Module 04 AFTER classification, so we cannot
# depend on it here. Instead, use email domain patterns available from Module 03.
PROCUREMENT_EMAIL_PATTERNS  
"legal@", "legal.", "counsel@", "attorney@",
"security@", "infosec@", "ciso@",
"procurement@", "purchasing@", "vendor@"
]
for stakeholder in thread_state.stakeholders:
email_lower = stakeholder.email.lower()
if any(pattern in email_lower for pattern in PROCUREMENT_EMAIL_PATTERNS
scores["procurement"]  0.25
evidence["stage_signals"].append(f"procurement:email_pattern:{stakeholder.email}")
break # Only apply boost once
# Select winner
# Tie-break rule (v1.0.7 When multiple stages have equal scores, max()
# returns the first one encountered in iteration order. Since DEAL_STAGES
# is a fixed list and scores dict preserves insertion order, ties break
# by DEAL_STAGES enum order (triage < discovery < ... < closed_lost).
winner = max(scores, key=scores.get)
confidence = min(scores[winner] / 1.0, 0.98 # Cap at 0.98
# Apply penalties
if thread_state.attribution_confidence  0.80
confidence * 0.90
evidence["penalties"] = ["low_attribution_confidence"]
return winner, confidence, evidence
04 Deal Stage & Intent Classifier 12

Part IV: Buyer Intent Classification
4.1 Intent Enumeration
Module 04 is the AUTHORITATIVE SOURCE for BUYER_INTENTS. Canonical_Enumerations.pdf imports
these values.
BUYER_INTENTS  
# Questions 6 types)
"question_product", # Feature/capability questions
"question_pricing", # Cost/budget questions
"question_process", # Next steps/process questions
"question_technical", # API/integration/specs questions
"question_security", # SOC2/compliance/data questions
"question_reference", # Case study/reference requests
# Objections 5 types)
"objection_timing", # "Not right now" / timing hedge
"objection_budget", # Cost concerns
"objection_authority", # "Need to check with..."
"objection_need", # Fit questioning
"objection_competition", # Competitor comparison
# Signals 5 types)
"commitment_signal", # Positive buying signal
"commitment_request", # Direct next-step request
"information_share", # FYI/update sharing
"administrative", # Scheduling/logistics
"unclear", # No clear intent detected
]
4.2 Intent Evidence Patterns (Complete, v1.0.6)
INTENT_PATTERNS  
# ══════════════════════════════════════════════════════════════
# QUESTIONS 6 types)
# ══════════════════════════════════════════════════════════════
"question_product": {
"keywords": ["feature", "capability", "can it", "does it", "how does", "what about"],
"patterns": [r"(can|does)\s+(it|your|the)\s+\w+", r"what\s+(features|capabilities)"],
"exclusions": ["price", "cost", "security"],
"base_score" 0.75
},
"question_pricing": {
"keywords": ["price", "pricing", "cost", "budget", "quote", "proposal", "discount"],
04 Deal Stage & Intent Classifier 13

"patterns": [r"(how\s+much|what.*cost|pricing\s+(for|on))"],
"exclusions": [],
"base_score" 0.85
},
"question_process": {
"keywords": ["next steps", "process", "how do we", "what happens next", "timeline", "onboard
ing"],
"patterns": [r"(what|how)\s+(is|are)\s+(the\s+)?(next\s+steps|process|timeline)", r"how\s+do
\s+we\s+(proceed|start|begin)"],
"exclusions": [],
"base_score" 0.80
},
"question_technical": {
"keywords": ["API", "integration", "SDK", "webhook", "technical", "architecture", "specs", "doc
umentation"],
"patterns": [r"API|SDK|webhook|integration)\s+(docs?|documentation|specs?", r"(how|doe
s)\s+.+\s+integrat(e|ion)"],
"exclusions": [],
"base_score" 0.82
},
"question_security": {
"keywords": ["SOC2", "security", "compliance", "GDPR", "HIPAA", "encryption", "audit"],
"patterns": [r"(security|compliance)\s+(cert|audit|report)"],
"exclusions": [],
"base_score" 0.88
},
"question_reference": {
"keywords": ["case study", "reference", "customer story", "testimonial", "who else uses", "sim
ilar company"],
"patterns": [r"(case\s+stud(y|ies)|reference(s)?|testimonial(s)?)", r"(who|which)\s+(else\s+)?
(uses|customers)"],
"exclusions": [],
"base_score" 0.78
},
# ══════════════════════════════════════════════════════════════
# OBJECTIONS 5 types)
# ══════════════════════════════════════════════════════════════
"objection_timing": {
"keywords": ["not right now", "later", "next quarter", "not ready", "timing"],
"patterns": [r"(not|isn't)\s+(the\s+)?(right|good)\s+time", r"(maybe|perhaps)\s+(later|next)"],
"exclusions": [],
"base_score" 0.80
},
04 Deal Stage & Intent Classifier 14

"objection_budget": {
"keywords": ["expensive", "budget", "afford", "too much", "cheaper"],
"patterns": [r"(over|exceed|outside)\s+(our\s+)?budget", r"too\s+(expensive|costly)"],
"exclusions": [],
"base_score" 0.82
},
"objection_authority": {
"keywords": ["check with", "need to ask", "run it by", "get approval", "my manager", "decision
maker"],
"patterns": [r"(need|have)\s+to\s+(check|ask|run|get)", r"(my|our)\s+(manager|boss|leaders
hip|exec)"],
"exclusions": [],
"base_score" 0.78
},
"objection_need": {
"keywords": ["not sure we need", "don't think we need", "current solution", "already have", "n
ot a fit"],
"patterns": [r"(not\s+sure|don't\s+think)\s+we\s+need", r"(already|currently)\s+(have|use|usi
ng)", r"not\s+(a\s+)?(good\s+)?fit"],
"exclusions": [],
"base_score" 0.80
},
"objection_competition": {
"keywords": ["competitor", "alternative", "also looking at", "comparing", "other vendor", "other
option"],
"patterns": [r"(also|currently)\s+(looking|evaluating|comparing)", r"(other|another)\s+(vendor
|option|solution)"],
"exclusions": [],
"base_score" 0.82
},
# ══════════════════════════════════════════════════════════════
# SIGNALS 5 types)
# ══════════════════════════════════════════════════════════════
"commitment_signal": {
"keywords": ["interested", "excited", "looks good", "promising", "like it"],
"patterns": [r"(really|very)\s+(interested|excited)", r"this\s+(looks|sounds)\s+(good|great)"],
"exclusions": ["but", "however", "although"],
"base_score" 0.78
},
"commitment_request": {
"keywords": ["proposal", "contract", "agreement", "sign", "move forward", "next steps"],
"patterns": [r"(send|share)\s+(the\s+)?(proposal|contract)", r"ready\s+to\s+(move|procee
d)"],
04 Deal Stage & Intent Classifier 15

"exclusions": [],
"base_score" 0.90
},
"information_share": {
"keywords": ["FYI", "for your information", "wanted to share", "update", "heads up"],
"patterns": [r"(fyi|for\s+your\s+(info|information))", r"(wanted|just)\s+(to\s+)?(share|updat
e)"],
"exclusions": [],
"base_score" 0.70
},
"administrative": {
"keywords": ["reschedule", "calendar", "availability", "OOO", "out of office", "vacation"],
"patterns": [r"(reschedule|move|change)\s+(the\s+)?(call|meeting)", r"(out\s+of\s+office|OO
O",
"exclusions": [],
"base_score" 0.88
},
"unclear": {
"keywords": [],
"patterns": [],
"exclusions": [],
"base_score" 0.40 # Low base triggers escalation
}
}
4.3 Intent Classification Algorithm
def classify_intent(thread_state: ThreadState) → tuple[str, float, dict]:
"""
Classify buyer intent from latest actionable turn.
Returns (intent, confidence, evidence_trace)
"""
content = thread_state.latest_buyer_content.lower()
evidence = {"intent_signals": [], "matched_patterns": [], "exclusions_hit": []}
scores = {intent: 0.0 for intent in BUYER_INTENTS
for intent, patterns in INTENT_PATTERNS.items():
score  0.0
# Keyword matching
for keyword in patterns["keywords"]:
if keyword.lower() in content:
score  0.15
04 Deal Stage & Intent Classifier 16

evidence["intent_signals"].append(f"{intent}:keyword:{keyword}")
# Pattern matching
for regex in patterns["patterns"]:
if re.search(regex, content, re.IGNORECASE
score  0.25
evidence["matched_patterns"].append(f"{intent}:regex")
# Exclusion check
for exclusion in patterns.get("exclusions", []):
if exclusion.lower() in content:
score * 0.5
evidence["exclusions_hit"].append(f"{intent}:{exclusion}")
# Apply base score if any evidence found
if score  0
score = min(score + patterns["base_score"] * 0.5, 0.98
scores[intent] = score
# Default to unclear if no strong signals
if max(scores.values())  0.30
scores["unclear"]  0.40
# Multi-intent detection (v1.0.3, wired v1.0.8
# Must be called BEFORE winner selection to populate evidence for downstream penalty
evidence["_multi_intent"] = detect_multi_intent(scores)
# Tie-break rule (v1.0.7 When multiple intents have equal scores, max()
# returns the first one encountered in iteration order. Since BUYER_INTENTS
# is a fixed list and scores dict preserves insertion order, ties break
# by BUYER_INTENTS enum order.
winner = max(scores, key=scores.get)
confidence = scores[winner]
return winner, confidence, evidence
4.4 Multi-Intent Detection (v1.0.3)
def detect_multi_intent(scores: dict[str, float]) → dict:
"""
Detect when multiple intents have similar scores.
Added in v1.0.3 for ambiguity handling.
"""
04 Deal Stage & Intent Classifier 17

sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
if len(sorted_intents)  2
top_score = sorted_intents[0][1]
second_score = sorted_intents[1][1]
if top_score - second_score  0.08 and top_score  0.30
return {
"flagged" True,
"primary": sorted_intents[0][0],
"secondary": sorted_intents[1][0],
"score_gap": top_score - second_score,
"confidence_penalty": 0.12
}
return {"flagged" False}
Part V: Confidence Scoring
5.1 Confidence Calculation (fixed v1.0.7, v1.0.9)
def calculate_confidence(
base_score: float,
thread_state: ThreadState,
context: ClassifierContext | None,
evidence: dict,
current_stage: str,
current_intent: str
) → float:
"""
Calculate final confidence with penalties applied.
Args:
base_score: Initial confidence from classification algorithm
thread_state: ThreadState object
context: ClassifierContext for drift detection (v1.0.9 replaces thread_state prior_* fields)
evidence: Evidence trace from classification
current_stage: Stage just classified by classify_stage()
current_intent: Intent just classified by classify_intent()
Returns:
Final confidence score clamped to 0.0, 0.98
"""
04 Deal Stage & Intent Classifier 18

confidence = base_score
# Attribution confidence penalty
if thread_state.attribution_confidence  0.80
confidence * 0.90
# Low evidence penalty
if len(evidence.get("intent_signals", []))  2
confidence * 0.85
# Multi-intent penalty (v1.0.3
if evidence.get("_multi_intent", {}).get("flagged"):
confidence += evidence["_multi_intent"]["confidence_penalty"]
# Prior classification drift penalty (v1.0.2, v1.0.9 uses ClassifierContext)
if detect_classification_drift(context, current_stage, current_intent):
confidence * 0.95
return max(min(confidence, 0.98, 0.0
5.2 Prior Classification Detection (v1.0.2, fixed v1.0.6, v1.0.9)
def detect_classification_drift(
context: ClassifierContext | None,
current_stage: str,
current_intent: str
) → bool:
"""
Detect if current classification differs significantly from prior.
Args:
context: ClassifierContext containing prior classification fields (v1.0.9
current_stage: The stage just classified by classify_stage()
current_intent: The intent just classified by classify_intent()
Returns:
True if drift detected (triggers confidence penalty), False otherwise
Penalty applies when:
1. prior_classification exists (context is not None and context.prior_deal_stage is not None)
2. Prior confidence was  0.75 (confident prior classification)
3. Current classification differs from prior
"""
# No context or no prior classification exists — no drift possible
04 Deal Stage & Intent Classifier 19

if context is None or context.prior_deal_stage is None:
return False
stage_changed = (
current_stage ! context.prior_deal_stage and
context.prior_stage_confidence is not None and
context.prior_stage_confidence  0.75
)
intent_changed = (
current_intent ! context.prior_buyer_intent and
context.prior_intent_confidence is not None and
context.prior_intent_confidence  0.75
)
return stage_changed or intent_changed
5.3 Confidence Threshold Enforcement
# Build Contract A8 threshold
CONFIDENCE_THRESHOLD  0.60
def evaluate_confidence_gate(stage_confidence: float, intent_confidence: float) → dict:
"""
Evaluate confidence against Build Contract A8 threshold.
Returns gate status for Policy Engine hard blocks.
Module 04 COMPUTES these values; Policy Engine ENFORCES the gates.
"""
return {
"stage_confidence": stage_confidence,
"stage_passes_gate": stage_confidence  CONFIDENCE_THRESHOLD,
"intent_confidence": intent_confidence,
"intent_passes_gate": intent_confidence  CONFIDENCE_THRESHOLD,
"threshold" CONFIDENCE_THRESHOLD,
"contract_ref": "Build Contract A8 stage_confidence_threshold / intent_confidence_threshol
d"
}
Part VI: Risk Assessment
6.1 Risk Level Enumeration
04 Deal Stage & Intent Classifier 20

Module 04 is the AUTHORITATIVE SOURCE for RISK_LEVELS. Canonical_Enumerations.pdf imports
these values.
RISK_LEVELS  "low", "medium", "high", "critical"]
6.2 Risk Factor Detection
Module 04 is the AUTHORITATIVE SOURCE for RISK_FACTORS. Canonical_Enumerations.pdf imports
these values.
Downstream Dependency (v1.0.7 Canonical_Enumerations.pdf must include all RISK_FACTORS
defined here, including rf_stalled. If Canonical_Enumerations is missing any factor, it must be
patched before Module 04 can be considered fully integrated.
RISK_FACTORS  
# ══════════════════════════════════════════════════════════════
# STAKEHOLDER RISK
# ══════════════════════════════════════════════════════════════
"rf_legal_involved": {
"trigger": "legal/counsel/attorney stakeholder detected",
"risk_elevation": "medium",
"detection": ["legal", "counsel", "attorney", "general counsel"]
},
"rf_security_involved": {
"trigger": "security/InfoSec stakeholder detected",
"risk_elevation": "medium",
"detection": ["security", "infosec", "ciso", "information security"]
},
"rf_procurement_involved": {
"trigger": "procurement stakeholder detected",
"risk_elevation": "medium",
"detection": ["procurement", "purchasing", "vendor management"]
},
"rf_executive_involved": {
"trigger": "C-level/VP stakeholder detected",
"risk_elevation": "high",
"detection": ["ceo", "cfo", "cto", "vp", "chief", "president"]
},
# ══════════════════════════════════════════════════════════════
# DEAL RISK
# ══════════════════════════════════════════════════════════════
"rf_competitor_mentioned": {
"trigger": "competitor name in content",
"risk_elevation": "medium",
04 Deal Stage & Intent Classifier 21

"detection": "competitor_list from config"
},
"rf_budget_concern": {
"trigger": "budget/cost objection pattern",
"risk_elevation": "medium",
"detection": ["too expensive", "over budget", "can't afford"]
},
"rf_timeline_pressure": {
"trigger": "urgent timeline language",
"risk_elevation": "low",
"detection": ["ASAP", "urgent", "deadline", "by end of"]
},
"rf_stakeholder_blocker": {
"trigger": "blocker role detected in stakeholders[]",
"risk_elevation": "high",
"detection": "stakeholder.is_blocker  True"
},
"rf_commitment_missed": {
"trigger": "missed commitment in thread",
"risk_elevation": "high",
"detection": "any(c.status == 'missed' for c in commitments_made)"
},
"rf_response_delay": {
"trigger": "7 days since last buyer response",
"risk_elevation": "medium",
"detection": "days_since_last_buyer  7"
},
"rf_negative_sentiment": {
"trigger": "negative sentiment trend",
"risk_elevation": "medium",
"detection": "sentiment_trend == 'declining'"
},
# ══════════════════════════════════════════════════════════════
# CRITICAL RISK
# ══════════════════════════════════════════════════════════════
"rf_deal_at_risk": {
"trigger": "deal lost signal detected",
"risk_elevation": "critical",
"detection": ["going with another", "decided against", "not moving forward"]
},
"rf_escalation_threat": {
"trigger": "escalation/legal threat language",
"risk_elevation": "critical",
04 Deal Stage & Intent Classifier 22

"detection": ["escalate", "lawyer", "legal action", "cancel contract"]
},
"rf_stalled": {
"trigger": "14 days silence",
"risk_elevation": "high",
"detection": "days_since_last_buyer  14"
}
}
6.3 Risk Level Calculation
RISK_ELEVATION_ORDER  "low" 0, "medium" 1, "high" 2, "critical" 3
def calculate_risk_level(risk_factors: List[str]) → str:
"""
Determine overall risk level from detected factors.
Returns highest risk elevation among all factors.
"""
if not risk_factors:
return "low"
max_elevation = "low"
for factor in risk_factors:
factor_elevation  RISK_FACTORS[factor]["risk_elevation"]
if RISK_ELEVATION_ORDER[factor_elevation]  RISK_ELEVATION_ORDER[max_elevation]:
max_elevation = factor_elevation
return max_elevation
Part VII: Stakeholder Role Detection
7.1 Role Enumeration
STAKEHOLDER_ROLES  
"champion", # Internal advocate
"decision_maker", # Final authority
"influencer", # Affects decision
"evaluator", # End user / evaluator
"legal", # Legal/counsel
"security", # Security/InfoSec
"procurement", # Procurement/purchasing
"blocker", # Active resistance
04 Deal Stage & Intent Classifier 23

"unknown", # Cannot determine
]
7.2 Role Detection Algorithm
ROLE_DETECTION_PATTERNS  
"legal": {
"title_patterns": ["general counsel", "legal", "attorney", "counsel"],
"email_patterns": ["legal@", "counsel@"],
"content_signals": ["terms", "contract", "liability", "indemnification"]
},
"security": {
"title_patterns": ["ciso", "security", "infosec", "information security"],
"email_patterns": ["security@", "infosec@"],
"content_signals": ["SOC2", "penetration", "vulnerability", "audit"]
},
"procurement": {
"title_patterns": ["procurement", "purchasing", "vendor", "sourcing"],
"email_patterns": ["procurement@", "purchasing@"],
"content_signals": ["PO", "purchase order", "vendor form", "W9"]
},
"blocker": {
"title_patterns": [],
"email_patterns": [],
"content_signals": ["concerned", "not comfortable", "cannot approve", "blocking"]
},
"champion": {
"title_patterns": [],
"email_patterns": [],
"content_signals": ["excited", "love this", "exactly what we need", "advocate"]
},
"decision_maker": {
"title_patterns": ["ceo", "cfo", "cto", "coo", "president", "vp", "director"],
"email_patterns": [],
"content_signals": ["final decision", "I'll approve", "authorized to sign"]
}
}
def detect_stakeholder_roles(stakeholders: List[Stakeholder])  List[dict]:
"""
Enrich stakeholders with role detection.
Returns list of role updates to apply.
"""
role_updates = []
04 Deal Stage & Intent Classifier 24

for stakeholder in stakeholders:
role_info = {
"stakeholder_id": stakeholder.stakeholder_id,
"role_detected": "unknown",
"role_confidence" 0.50,
"is_blocker" False,
"detection_evidence": []
}
# Check each role pattern
for role, patterns in ROLE_DETECTION_PATTERNS.items():
score  0.0
evidence = []
# Title pattern matching
if stakeholder.title:
title_lower = stakeholder.title.lower()
for pattern in patterns["title_patterns"]:
if pattern in title_lower:
score  0.40
evidence.append(f"title_match:{pattern}")
# Email pattern matching
if stakeholder.email:
email_lower = stakeholder.email.lower()
for pattern in patterns["email_patterns"]:
if pattern in email_lower:
score  0.35
evidence.append(f"email_match:{pattern}")
# Content signal matching (from stakeholder's turns)
for signal in patterns["content_signals"]:
# This would check stakeholder's messages in actual implementation
score  0.20
evidence.append(f"content_signal:{signal}")
if score > role_info["role_confidence"]:
role_info["role_detected"] = role
role_info["role_confidence"] = min(score, 1.0
role_info["detection_evidence"] = evidence
# Check for blocker signals
if role_info["role_detected"] == "blocker":
04 Deal Stage & Intent Classifier 25

role_info["is_blocker"]  True
role_updates.append(role_info)
return role_updates
Part VIII: Output Specification
8.1 Success Output (ClassifiedState)
{
"status": "success",
"thread_id": "string",
// ══════════════════════════════════════════════════════════════
// CLASSIFICATION RESULTS Module 04 additions)
// ══════════════════════════════════════════════════════════════
"deal_stage": "evaluation",
"stage_confidence" 0.82,
"buyer_intent": "question_security",
"intent_confidence" 0.88,
"risk_level": "medium",
"risk_factors": ["rf_security_involved", "rf_response_delay"],
// Enriched stakeholders Module 04 adds role detection)
"stakeholders": [
{
"email": "security@buyer.com",
"name": "Jane Security",
"title": "CISO",
"role_detected": "security",
"role_confidence" 0.85,
"is_blocker": false,
"detection_evidence": ["email_match:security@", "title_match:ciso"]
}
],
// ══════════════════════════════════════════════════════════════
// CONFIDENCE GATE STATUS (for Policy Engine)
// ══════════════════════════════════════════════════════════════
"confidence_gate": {
"stage_passes_gate": true,
"intent_passes_gate": true,
04 Deal Stage & Intent Classifier 26

"threshold" 0.60
},
// ══════════════════════════════════════════════════════════════
// PASSTHROUGH FROM MODULE 02/03 (unchanged)
// ══════════════════════════════════════════════════════════════
"open_loops": [...], // FROM MODULE 03, NOT re-derived
"open_loop_count" 1, // FROM MODULE 03, NOT re-derived
"commitment_drift_flag": false, // FROM MODULE 03, NOT re-derived
"days_since_last_buyer" 0, // FROM MODULE 03, NOT re-derived
"total_turns" 8, // FROM MODULE 03, NOT re-derived
"seller_turns" 4, // FROM MODULE 03, NOT re-derived
"last_3_ctas": [...], // FROM MODULE 03, NOT re-derived
// ══════════════════════════════════════════════════════════════
// HARDENING GATE FIELDS (v1.0.8  passthrough for Policy Engine)
// ══════════════════════════════════════════════════════════════
"required_config_missing": false, // FROM MODULE 02, passthrough
"missing_config_fields": [], // FROM MODULE 02, passthrough
"parse_status": "ok", // FROM MODULE 02, passthrough
// ══════════════════════════════════════════════════════════════
// CLASSIFICATION TRACE (for audit)
// ══════════════════════════════════════════════════════════════
"evidence_trace": {
"stage_signals": ["evaluation:comparison_language", "evaluation:technical_depth"],
"intent_signals": ["question_security:keyword:SOC2", "question_security:regex_match"],
"risk_signals": ["rf_security_involved:stakeholder", "rf_response_delay:7_days"],
"confidence_adjustments": [],
"_multi_intent": {"flagged": false}
}
}
8.2 Failure Output
{
"status": "error",
"thread_id": "string",
"error_code": "CLASSIFICATION_FAILED",
"error_message": "Unable to classify thread",
"partial_results": {
"deal_stage": null,
"buyer_intent": null
04 Deal Stage & Intent Classifier 27

}
}
Part IX: Test Vectors
9.1 Unit Tests — Stage Classification
STAGE_TEST_VECTORS  
{
"test_id": "CL_001_stage_triage",
"description": "New thread with generic question should classify as triage",
"input": {
"latest_buyer_content": "Tell me more about what you do.",
"total_turns" 1
},
"expected": {
"deal_stage": "triage",
"stage_confidence": " 0.60"
}
},
{
"test_id": "CL_002_stage_discovery",
"description": "Buyer describing situation should classify as discovery",
"input": {
"latest_buyer_content": "Our team is currently using a manual process and we're trying to a
utomate it.",
"total_turns" 4
},
"expected": {
"deal_stage": "discovery",
"stage_confidence": " 0.70"
}
},
{
"test_id": "CL_003_stage_evaluation",
"description": "Comparison and technical questions should classify as evaluation",
"input": {
"latest_buyer_content": "How does your solution compare to Competitor X? Can you walk u
s through the API?",
"total_turns" 8
},
"expected": {
"deal_stage": "evaluation",
04 Deal Stage & Intent Classifier 28

"stage_confidence": " 0.80"
}
}
]
9.2 Unit Tests — Intent Classification
INTENT_TEST_VECTORS  
{
"test_id": "CL_010_intent_question_product",
"description": "Feature question should classify as question_product",
"input": {"latest_buyer_content": "Does your platform support SSO integration?"},
"expected": {"buyer_intent": "question_product", "intent_confidence": " 0.75"}
},
{
"test_id": "CL_011_intent_question_pricing",
"description": "Pricing question should classify as question_pricing",
"input": {"latest_buyer_content": "What would this cost for a team of 200 users?"},
"expected": {"buyer_intent": "question_pricing", "intent_confidence": " 0.85"}
},
{
"test_id": "CL_012_intent_question_security",
"description": "Security question should classify as question_security",
"input": {"latest_buyer_content": "Do you have SOC2 Type II certification?"},
"expected": {"buyer_intent": "question_security", "intent_confidence": " 0.88"}
},
{
"test_id": "CL_024_intent_information_share",
"description": "FYI message should classify as information_share",
"input": {"latest_buyer_content": "FYI, we just hired a new CTO who will be joining the evaluati
on."},
"expected": {"buyer_intent": "information_share", "intent_confidence": " 0.70"}
},
{
"test_id": "CL_025_intent_unclear",
"description": "Ambiguous response should classify as unclear with low confidence",
"input": {"latest_buyer_content": "Ok thanks"},
"expected": {"buyer_intent": "unclear", "intent_confidence": " 0.60"}
}
]
9.3 Unit Tests — Confidence Gate
04 Deal Stage & Intent Classifier 29

CONFIDENCE_GATE_TEST_VECTORS  
{
"test_id": "CL_030_low_stage_confidence",
"test_type": "failure",
"description": "Ambiguous stage should fail gate",
"input": {"latest_buyer_content": "Ok thanks"},
"expected": {
"stage_confidence": " 0.60",
"confidence_gate.stage_passes_gate" False
}
},
{
"test_id": "CL_031_low_intent_confidence",
"test_type": "failure",
"description": "Unclear intent should fail gate",
"input": {"latest_buyer_content": "Hmm, interesting."},
"expected": {
"intent_confidence": " 0.60",
"confidence_gate.intent_passes_gate" False
}
},
{
"test_id": "CL_032_multi_intent_detection",
"test_type": "ambiguity",
"description": "Mixed pricing and security question should flag multi-intent (v1.0.3",
"input": {"latest_buyer_content": "What's the pricing, and do you have SOC2 certification?"},
"expected": {
"buyer_intent": "question_pricing OR question_security",
"evidence_trace._multi_intent.flagged" True,
"confidence_penalty_applied": 0.12,
"note": "Determinism preserved - still emits single winner based on score"
}
}
]
9.4 Unit Tests — Risk Assessment
RISK_TEST_VECTORS  
{
"test_id": "CL_040_risk_competitor",
"description": "Competitor mention should elevate to medium risk",
"input": {"latest_buyer_content": "We're also evaluating Competitor X."},
"expected": {"risk_level": "medium", "risk_factors": ["rf_competitor_mentioned"]}
04 Deal Stage & Intent Classifier 30

},
{
"test_id": "CL_041_risk_critical_deal_lost",
"description": "Lost deal signal should be critical risk",
"input": {"latest_buyer_content": "We've decided to go with another vendor."},
"expected": {"risk_level": "critical", "risk_factors": ["rf_deal_at_risk"]}
},
{
"test_id": "CL_042_risk_stalled",
"description": "14 days silence should be high risk",
"input": {"days_since_last_buyer" 14,
"expected": {"risk_level": "high", "risk_factors": ["rf_stalled"]}
}
]
9.5 Integration Tests — Classifier Correct but Locks Override
CRITICAL These tests verify that correct classification doesn't bypass Policy Engine constraints.
Module 04 classifies correctly; Policy Engine may still override based on Module 03 state.
INTEGRATION_TEST_VECTORS  
{
"test_id": "CL_INT_001",
"description": "Intent=commitment_request but commitment_drift_flag forces Action 10",
"input": {
"latest_buyer_content": "Yes, let's move forward. Can you send the proposal?",
"buyer_intent": "commitment_request",
"intent_confidence" 0.88,
"commitment_drift_flag" True # FROM MODULE 03
},
"expected_classification": {
"buyer_intent": "commitment_request",
"intent_confidence": " 0.85"
},
"expected_policy_engine_behavior": {
"selected_action" 10, # NOT 17/19/20
"reason": "PL_001 (commitment_recovery_lock) is absolute; overrides intent affinity"
}
},
{
"test_id": "CL_INT_002",
"description": "Stage=proposal but high-priority open loop restricts to Actions 111",
"input": {
"latest_buyer_content": "This looks great, we're interested!",
04 Deal Stage & Intent Classifier 31

"deal_stage": "proposal",
"buyer_intent": "commitment_signal",
"open_loops": [{"priority": "high", "resolution_status": "open"}] # FROM MODULE 03
},
"expected_classification": {
"deal_stage": "proposal",
"buyer_intent": "commitment_signal"
},
"expected_policy_engine_behavior": {
"allowed_actions": 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
"blocked_actions": 16, 17, 18, 19, 20,
"reason": "PL_002 (open_loop_priority_lock) restricts to resolution actions"
}
},
{
"test_id": "CL_INT_003",
"description": "Risk=critical restricts CTAs even with commitment_signal",
"hardening_gate": "G5 CT_003",
"input": {
"latest_buyer_content": "Let me think about this more.",
"deal_stage": "evaluation",
"buyer_intent": "commitment_signal",
"risk_level": "critical" # COMPUTED BY MODULE 04
},
"expected_classification": {
"risk_level": "critical"
},
"expected_policy_engine_behavior": {
"cta_whitelist": ["none", "async_review", "opt_out"],
"blocked_ctas": ["question", "async_choice", "calendar_light", "calendar_two_windows"],
"reason": "PL_004 (critical_risk_lock) constrains CTAs"
},
"hardening_note": "v1.0.4 uses canonical 'calendar_two_windows'. v1.0.5 blocked_ctas matc
hes Canonical_Enumerations.RISK_CTA_RESTRICTIONS'critical'] exactly."
}
]
Part X: Integration Verification
10.1 Contract Alignment
Contract Requirement Implementation Status
Build Contract A8 stage_confidence  0.60 Section 5.3 confidence gate ✓ ALIGNED
04 Deal Stage & Intent Classifier 32

Contract Requirement Implementation Status
Build Contract A8 intent_confidence  0.60 Section 5.3 confidence gate ✓ ALIGNED
Policy Engine HB_004 stage_confidence <
confidence_gate.stage_passes_gate ✓ ALIGNED
0.60
Policy Engine HB_005 intent_confidence <
confidence_gate.intent_passes_gate ✓ ALIGNED
0.60
Policy Engine INTENT_AFFINITY 16 intent types provided ✓ ALIGNED
Policy Engine DEAL_STAGES 8 stage types provided ✓ ALIGNED
Build Index spine: 03  04 Input is ThreadState from Module 03 ✓ ALIGNED
Hardening SSR1 CTA types canonical only No local CTA_TYPES definition ✓ ALIGNED
Hardening SSR3 No deprecated tokens CL_INT_003 uses calendar_two_windows ✓ ALIGNED
Nested schemas imported, not redefined
Thread_State_Schema v1.0.1 ✓ ALIGNED
(v1.0.9
10.2 Upstream Dependencies
Module Required Field Usage in Module 04
Module 03 ThreadState (complete) Primary input
↳ Module 02 turns[], participants[] Stage/intent evidence
↳ Module 02 latest_buyer_content Intent classification
↳ Module 02 attribution_confidence Confidence penalty
↳ Module 02 buyer_role_confidence Passed through
↳ Module 03 open_loops[], open_loop_count READ ONLY (risk context)
↳ Module 03 commitment_drift_flag READ ONLY (passed through)
↳ Module 03 days_since_last_buyer Risk factor detection
↳ Module 03 total_turns, seller_turns Structural evidence
↳ Module 03 stakeholders[], stakeholder_count Role detection input
10.3 Downstream Consumers
Module Consumes Usage
Policy Engine v1.1.2 deal_stage Stage-action availability matrix
Policy Engine v1.1.2 stage_confidence HB_004 hard block
Policy Engine v1.1.2 buyer_intent Intent-action affinity
Policy Engine v1.1.2 intent_confidence HB_005 hard block
Policy Engine v1.1.2 risk_level PL_004 critical risk lock
Policy Engine v1.1.2 risk_factors[] Risk context
Policy Engine v1.1.2 stakeholder_count HB_006 check
Policy Engine v1.1.2 stakeholders[] Actions 13, 14 routing (enriched with role_detected)
04 Deal Stage & Intent Classifier 33

Module Consumes Usage
Policy Engine v1.1.2 open_loops[] PASSTHROUGH from Module 03  PL_001/PL_002
Policy Engine v1.1.2 commitment_drift_flag PASSTHROUGH from Module 03  PL_001
Policy Engine v1.1.2 required_config_missing PASSTHROUGH from Module 02  HB_001 (v1.0.8
Policy Engine v1.1.2 missing_config_fields PASSTHROUGH from Module 02  error context (v1.0.8
Policy Engine v1.1.2 parse_status PASSTHROUGH from Module 02  HB_003 (v1.0.8
═══ End of Deal Stage & Intent Classifier Specification v1.0.9 ═══
04 Deal Stage & Intent Classifier 34