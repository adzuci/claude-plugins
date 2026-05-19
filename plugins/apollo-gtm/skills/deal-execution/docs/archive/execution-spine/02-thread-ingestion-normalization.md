GEN-SE Thread Ingestion &
Normalization
Module:
02_Thread_Ingestion_Normalization
Version: 1.2.2 PATCHED
Status: READY TO LOCK
Date: January 20, 2026
Purpose: Convert a raw email thread into deterministic, structured turns with
speaker attribution, and block if attribution is ambiguous (confidence  0.70 or
required configuration is missing, while returning top-2 candidate interpretations
or specifying missing config fields.
AUDIT SUMMARY
Document Lineage
Version Date Status Changes
Initial consolidated MASTER from
1.0 20260119 SUPERSEDED
duplicate sources
Architecture audit fixes: header email
1.1 20260119 SUPERSEDED override, multi-domain config
validation
Stress-test gap resolution:
1.2 20260119 SUPERSEDED known_participants exemption,
deterministic frequency metric
Patch: known_participant evidence
1.2.1 20260119 SUPERSEDED guard—prevents 0.50 weight
stacking with conflicts
1.2.2 20260120 CURRENT Patch: Added buyer_role_confidence to
output schema for Policy Engine
GENSE Thread Ingestion & Normalization 1

Version Date Status Changes
v1.1.1 integration
V1.2.2 Patch Summary
This version adds the buyer_role_confidence field required by Policy Engine v1.1.1
 Buyer Role Confidence Output GAP09 Added buyer_role_confidence to success
output schema Section 5.1 and blocked output schemas Sections 5.2, 5.3.
This enables Policy Engine HB_002b to gate on role identification reliability,
not just speaker attribution.
 Buyer Role Confidence Calculation Section 6.11 Added deterministic
scoring rule for buyer_role_confidence based on how the buyer role was assigned
(known_participants, single-domain, crm_account_domain, etc.).
 Buyer Role Confidence Gating Section 6.12 Added module-level gate at
0.70 threshold, parallel to attribution_confidence gate.
Contract Alignment: Policy Engine v1.1.1 requires buyer_role_confidence from Module
02. This patch provides it. No other downstream changes required.
1. Purpose
This module parses raw email thread text (forwarded or scraped) into a canonical
structure: ordered turns, participant list, latest actionable buyer turn, and an
attribution confidence score. It is deliberately conservative: if the module cannot
reliably identify who said what (especially for the latest buyer turn), it blocks and
returns ambiguity candidates instead of guessing. If required configuration (such
as buyer domain) is missing, it blocks and specifies the missing fields so upstream
can provide them.
2. Scope
In Scope
Turn boundary detection and splitting (messy reply chains, forwarded blocks,
mixed quoting)
GENSE Thread Ingestion & Normalization 2

Quote stripping (quoted reply history) using deterministic rules
Signature removal using conservative heuristics
Footer and legal disclaimer stripping using deterministic patterns
Speaker attribution per turn with confidence scoring
Participant extraction and role inference (buyer, seller, unknown)
Required configuration validation V1.1
known_participants role exemption V1.2
Buyer role confidence scoring V1.2.2
Out of Scope
Open loop detection (handled by Module 03
Deal stage and intent classification Module 04
Action selection, message generation, drift logic Modules 06, 07, 09
Any probabilistic or model-based inference (no LLM use here)
3. Definitions
Term Definition
Untrusted input string representing the email thread, often
Raw thread
containing reply history and forwarding artifacts
Turn One discrete message in the thread (one sender at one time)
A deterministic indicator that a new message begins (e.g., "From:"
Boundary marker
header, "On ... wrote:", "Original Message-----")
Reply history repeated inside newer messages (often prefixed by >
Quoted content
or delimited by "On ... wrote:" sections)
Signature block Sender sign-off and contact info at the end of a turn
Legal disclaimers, confidentiality notices, unsubscribe text,
Footer
automated system footers
Attribution A 0.0 to 1.0 score for speaker attribution reliability (especially for
confidence latest buyer turn)
GENSE Thread Ingestion & Normalization 3

Term Definition
Buyer role
A 0.0 to 1.0 score for buyer role assignment reliability V1.2.2
confidence
Most recent buyer-authored turn requiring response (question,
Latest actionable
request, objection, scheduling, or decision signal), excluding auto-
buyer turn
replies
Required config Flag indicating that configuration necessary for buyer identification
missing is not provided V1.1
Known participant When known_participants contains explicit buyer role, skip domain-
exemption based config validation V1.2
4. Inputs
4.1 Required Inputs
raw_thread: string // The raw email thread content
thread_id: string // Unique identifier
4.2 Optional Inputs
known_participants: [{email, name?, role? // Pre-known participants with op
tional role
config.seller_emails: string[] // Seller email addresses
config.seller_domains: string[] // Seller domains
config.internal_domains: string[] // Internal domains
crm_account_domain: string // Buyer's company domain
V1.2 Note on known_participants: The role field accepts values "buyer" , "seller" , or
"unknown" . When a participant has role == "buyer" , this takes precedence over
domain-based inference and exempts the thread from requiring crm_account_domain .
See Section 6.7.1.
5. Outputs
GENSE Thread Ingestion & Normalization 4

5.1 Success Output (V1.2.2 AMENDED)
{
"status": "success",
"thread_id": "string",
"turns": [{
"turn_number" 1,
"speaker_email": "string|null",
"speaker_name": "string|null",
"speaker_role": "buyer|seller|unknown",
"timestamp": "ISO8601|null",
"timestamp_source": "header|wrote_line|inferred|null",
"content": "cleaned string",
"raw_content": "string",
"content_type": "original|forwarded|quoted|administrative",
"attribution": {
"method": "header_from|from_block|wrote_line|signature_email|signature_
name|known_participant|unknown",
"confidence" 0.01.0,
"evidence": ["string"]
}
}],
"participants": [{"email", "name", "role"}],
"latest_buyer_turn" 5,
"latest_buyer_content": "string",
"attribution_confidence" 0.92,
"buyer_role_confidence" 0.85, // V1.2.2 ADDITION
"required_config_missing": false,
"missing_config_fields": [],
"parsing_warnings": [{"code", "severity", "detail"}],
"ingestion_trace": {...}
}
5.2 Blocked Output (Ambiguity) — V1.2.2 AMENDED
GENSE Thread Ingestion & Normalization 5

{
"status": "blocked",
"thread_id": "string",
"reason": "speaker_attribution_ambiguous",
"attribution_confidence" 0.63,
"buyer_role_confidence": null, // V1.2.2 ADDITION  null when blocked for
attribution
"required_config_missing": false,
"missing_config_fields": [],
"candidates": [
{"candidate_id": "C1", "latest_buyer_turn" 4, "confidence" 0.63, "why":
[...]},
{"candidate_id": "C2", "latest_buyer_turn" 5, "confidence" 0.58, "why":
[...]}
],
"turns_partial": [],
"parsing_warnings": []
}
5.3 Blocked Output (Missing Config) — V1.2.2 AMENDED
{
"status": "blocked",
"thread_id": "string",
"reason": "required_config_missing",
"attribution_confidence": null,
"buyer_role_confidence": null, // V1.2.2 ADDITION  null when blocked for
config
"required_config_missing": true,
"missing_config_fields": ["crm_account_domain"],
"candidate_buyer_domains": [
{
"domain": "acme.com",
"email_count" 2,
GENSE Thread Ingestion & Normalization 6

"participant_emails": ["jane@acme.com", "bob@acme.com"],
"attributed_turn_count" 3
},
{
"domain": "partner.io",
"email_count" 1,
"participant_emails": ["bob@partner.io"],
"attributed_turn_count" 1
}
],
"parsing_warnings": [{"code": "W014", "severity": "high", "detail": "..."}]
}
5.4 Blocked Output (Buyer Role Ambiguous) — V1.2.2 ADDITION
{
"status": "blocked",
"thread_id": "string",
"reason": "buyer_role_ambiguous",
"attribution_confidence" 0.85,
"buyer_role_confidence" 0.58, // Below 0.70 threshold
"required_config_missing": false,
"missing_config_fields": [],
"role_ambiguity_detail": {
"latest_buyer_turn" 5,
"assigned_role": "buyer",
"role_assignment_method": "multi_domain_frequency",
"confidence_factors": [
{"factor": "multi_domain_no_config", "impact": 0.30,
{"factor": "frequency_heuristic", "impact": 0.12
]
},
"parsing_warnings": [{"code": "W016", "severity": "high", "detail": "..."}]
}
GENSE Thread Ingestion & Normalization 7

6. Processing Rules
6.1 Processing Sequence
1. VALIDATE INPUT  Reject empty/non-text
2. DETECT BOUNDARIES  Split into candidate turns
3. STRIP QUOTES  Remove quoted reply history
4. STRIP SIGNATURES  Remove signature blocks
5. STRIP FOOTERS  Remove legal/system footers
6. ATTRIBUTE SPEAKERS  Assign speaker per turn with confidence
7. EXTRACT PARTICIPANTS  Build participant list with roles
8. VALIDATE CONFIG  Check if crm_account_domain needed V1.1/V1.
2
9. SELECT LATEST BUYER  Find most recent actionable buyer turn
10. CALCULATE ATTRIBUTION  Module-level attribution_confidence
11. CALCULATE ROLE CONFIDENCE  Module-level buyer_role_confidence V
1.2.2
12. GATE CHECK  Block if either confidence  0.70
13. EMIT OUTPUT  Success or blocked with candidates/config reque
st
6.2 Turn Boundary Detection
[... existing content unchanged ...]
6.3 Quote Stripping
[... existing content unchanged ...]
6.4 Signature Stripping
[... existing content unchanged ...]
6.5 Footer Stripping
[... existing content unchanged ...]
6.6 Speaker Attribution Per Turn
GENSE Thread Ingestion & Normalization 8

Attribution is evidence-based and deterministic. For each turn, collect evidence in
order of reliability:
Evidence Sources and Weights:
Evidence Source Weight
Header email extracted from From: line 0.60
Header name that maps to known participant email 0.45
"On ... wrote:" name maps to known participant 0.35
Signature contains explicit email 0.25
Signature contains name that maps to known participant 0.15
known_participants explicit role match V1.2 0.50
V1.2 Guard for known_participant Evidence:
The known_participants explicit role match 0.50 weight may ONLY be applied
when ALL conditions are met:
 Turn speaker is being resolved via known_participants mapping (email or
name match to a known_participants entry)
 No W005_SPEAKER_CONFLICT penalty is present for this turn
 No explicit header_from email has already been captured for this turn
(attribution.method ≠ "header_from")
Penalties:
Conflicting emails found in same turn: 0.30
Only a name, no email, and name matches multiple participants: 0.25
No evidence beyond heuristics: cap at 0.49
Turn attribution confidence formula:
turn_confidence = clamp(0, 1, sum(weights) - sum(penalties))
6.6.1 Header Email Sufficiency Override (V1.1 AMENDMENT)
Rule: If ALL of the following conditions are met:
GENSE Thread Ingestion & Normalization 9

 attribution.method == "header_from"
 speaker_email is a valid, fully-qualified email address (contains @ and valid
domain)
 Email was extracted directly from a parsed From: header line
 No W005_SPEAKER_CONFLICT penalty is present for this turn V1.1 safety
guard)
Then: Set turn_confidence floor to 0.70 (sufficient for gate passage).
if attribution.method == "header_from"
AND is_valid_email(speaker_email)
AND NOT has_conflict_penalty(turn):
turn_confidence = max(turn_confidence, 0.70
6.7 Participant Extraction and Role Inference
Participants extracted from: parsed header emails, signature emails, optional
known_participants.
Role inference rules (evaluate in order):
 If email in known_participants with role == "buyer" → buyer V1.2 priority)
 If email in known_participants with role == "seller" → seller V1.2 priority)
 If email in config.seller_emails → seller
 Else if domain in config.seller_domains or config.internal_domains → seller
 Else if domain equals crm_account_domain → buyer
 Else → unknown
6.7.1 Required Config Validation for Buyer Identification (V1.2
AMENDED)
EXEMPTION RULE V1.2  evaluate FIRST
If ANY of the following conditions are true, SKIP the required_config_missing
check for crm_account_domain:
GENSE Thread Ingestion & Normalization 10

 known_participants contains at least one entry with role == "buyer"
 Only ONE non-seller domain exists (unambiguous buyer domain)
BLOCKING RULE (evaluate if exemption does not apply):
If BOTH conditions are true:
 crm_account_domain is not provided (null or empty)
 Thread contains 2 or more distinct non-seller domains
 No participant in known_participants has role == "buyer" V1.2 guard)
Then:
 Set status = "blocked"
 Set reason = "required_config_missing"
 Set required_config_missing = true
 Set missing_config_fields = ["crm_account_domain"]
 Emit W014_BUYER_DOMAIN_REQUIRED
 Return candidate_buyer_domains array listing each non-seller domain with
metrics
6.8 Latest Actionable Buyer Turn Selection
Scan turns from newest to oldest and choose first turn where:
speaker_role == buyer
content_type ! administrative
content length  12 characters
Actionability score  1
Actionability score (deterministic):
Contains ?  1
Contains request verbs (share, send, provide, confirm, review, approve, sign,
schedule) → 1
GENSE Thread Ingestion & Normalization 11

Contains scheduling tokens (times, dates, "calendar", "Monday", "tomorrow")
→ 1
Contains objection tokens (concern, problem, cannot, won't, too expensive,
competitor) → 1
If none meet actionability, fall back to newest buyer turn meeting length  12 and
emit W015_NO_ACTIONABLE_BUYER_TURN.
6.9 Attribution Confidence Gating (Module Gate)
Define module-level attribution_confidence as the turn_confidence of the selected latest
actionable buyer turn.
If attribution_confidence  0.70  proceed to role confidence check V1.2.2
If attribution_confidence  0.70  blocked with reason =
"speaker_attribution_ambiguous", return top-2 candidates
Note: The required_config_missing check Section 6.7.1 and the
known_participants exemption check occur BEFORE this gate.
6.10 Top-2 Ambiguity Output Generation
When blocked due to speaker_attribution_ambiguous:
 Generate candidate interpretations by varying attribution source priority for
newest two buyer-likely turns
 Score each candidate using the same confidence formula
 Return the top-2 by confidence
Tie-breakers:
Candidate with explicit email evidence wins
If still tied: choose candidate whose speaker domain matches
crm_account_domain
If still tied: choose candidate with fewer parsing warnings
6.11 Buyer Role Confidence Calculation (V1.2.2 ADDITION)
GENSE Thread Ingestion & Normalization 12

Define module-level buyer_role_confidence as the confidence that the speaker
identified as "buyer" in the latest actionable buyer turn is actually on the buyer
side (not a partner, consultant, or misattributed seller).
Scoring Rules (evaluate in order, take first match):
Role Assignment Method buyer_role_confidence Rationale
known_participants with role == Explicit upstream label,
1.00
"buyer" highest trust
Single non-seller domain Only one external party,
0.90
(unambiguous) must be buyer
crm_account_domain match Config explicitly identifies
0.85
(config-confirmed) buyer domain
known_participants email match Known participant but role
0.75
(no role) inferred
Multi-domain with Config present but multiple
0.80
crm_account_domain externals
Multi-domain frequency heuristic Below threshold, triggers
0.55
DEPRECATED block
No basis for role
Unknown/unresolved 0.00
assignment
Penalties (applied after base score):
Condition Penalty
W016_ROLE_CONFLICT present 0.25
speaker_role changed during thread 0.15
Multiple emails from "buyer" domain with different roles 0.20
Formula:
def calculate_buyer_role_confidence(latest_buyer_turn, role_assignment_meth
od, warnings):
# Base score from assignment method
base_scores = {
"known_participant_explicit" 1.00,
"single_domain_unambiguous" 0.90,
GENSE Thread Ingestion & Normalization 13

"crm_account_domain_match" 0.85,
"known_participant_inferred" 0.75,
"multi_domain_with_config" 0.80,
"multi_domain_frequency" 0.55, # DEPRECATED  below threshold
"unknown" 0.00
}
confidence = base_scores.get(role_assignment_method, 0.00
# Apply penalties
if "W016_ROLE_CONFLICT" in warnings:
confidence  0.25
if role_changed_during_thread(latest_buyer_turn):
confidence  0.15
if multiple_roles_same_domain(latest_buyer_turn):
confidence  0.20
return clamp(0.0, 1.0, confidence)
6.12 Buyer Role Confidence Gating (V1.2.2 ADDITION)
After attribution confidence passes  0.70, evaluate buyer role confidence:
If buyer_role_confidence  0.70  success
If buyer_role_confidence  0.70  blocked with reason =
"buyer_role_ambiguous"
Note: This gate runs AFTER attribution confidence gate. A thread can pass
attribution (we know WHO spoke) but fail role confidence (we don't know WHICH
SIDE they're on).
# Gate sequence
if attribution_confidence  0.70
return blocked("speaker_attribution_ambiguous", ...)
if buyer_role_confidence  0.70
GENSE Thread Ingestion & Normalization 14

return blocked("buyer_role_ambiguous", ...) # V1.2.2
return success(...)
7. Priority Locks and Constraints
Fail-safe over completeness: if boundaries or speakers are unclear, block
rather than infer
Fail-safe over guessing: if buyer domain is ambiguous (multiple candidates,
no config, no known_participants exemption), block and request config rather
than inferring V1.1, refined V1.2
Trust explicit role labels: if known_participants contains explicit buyer/seller
roles, trust those over domain inference V1.2
Deterministic output: same input must always produce same turns, warnings,
and confidence
No semantic reasoning: do not interpret intent, stage, or commitments here
Preserve auditability: include raw_content per turn and input_hash in trace
No hidden memory: all participant knowledge must come from input config
and thread content
Gate on both confidences: block if attribution_confidence  0.70 OR
buyer_role_confidence  0.70 V1.2.2
8. Failure Modes
Code Trigger Response
status=blocked,
FM_001 Empty or non-text thread
reason=invalid_input_empty
Attempt single-turn parse; emit W001;
FM_002 No boundaries found
block only if attribution  0.70
Conflicting attribution Emit W005_SPEAKER_CONFLICT, likely
FM_003
evidence block
GENSE Thread Ingestion & Normalization 15

Code Trigger Response
Allow timestamp=null, emit
FM_004 Timestamp extraction failure
W003_TIMESTAMP_INFERRED
Thread is purely administrative status=blocked,
FM_005
OOO, bounce) reason=no_actionable_buyer_turn
HTML-only and stripping status=blocked,
FM_006
yields near-empty reason=content_unparseable
Multiple non-seller domains, status=blocked,
FM_007 no crm_account_domain, no reason=required_config_missing, emit
known_participants exemption W014 V1.1, refined V1.2
status=blocked,
FM_008 Buyer role confidence  0.70 reason=buyer_role_ambiguous, emit
W016 V1.2.2
9. Validation Checks
On Success
turn_count  1
Turns are ordered oldest to newest
latest_buyer_turn exists and references a buyer turn
attribution_confidence  0.70
buyer_role_confidence  0.70 V1.2.2
required_config_missing == false
latest_buyer_content equals the content of latest_buyer_turn
All warning codes are in the known taxonomy set
On Blocked (Attribution Ambiguous)
reason == "speaker_attribution_ambiguous"
candidates.length  2
GENSE Thread Ingestion & Normalization 16

Candidates are distinct interpretations (different latest turn number or different
speaker attribution)
buyer_role_confidence == null V1.2.2
draft is not emitted by this module (downstream pipeline blocks)
On Blocked (Missing Config) — V1.1/V1.2
reason == "required_config_missing"
required_config_missing == true
missing_config_fields contains at least one field name
candidate_buyer_domains.length  2 (otherwise single-domain exception or
known_participants exemption would apply)
candidate_buyer_domains is sorted by email_count DESC V1.2
attribution_confidence == null
buyer_role_confidence == null V1.2.2
draft is not emitted by this module (downstream routes to Action 2
On Blocked (Buyer Role Ambiguous) — V1.2.2 ADDITION
reason == "buyer_role_ambiguous"
attribution_confidence  0.70 (attribution passed)
buyer_role_confidence  0.70 (role failed)
role_ambiguity_detail is populated
W016_ROLE_AMBIGUOUS warning present
draft is not emitted by this module (downstream routes to Action 1 via
HB_002b)
10. Postconditions
Success Guarantees
GENSE Thread Ingestion & Normalization 17

Cleaned content excludes obvious quoted history, signatures, and footers
within conservative rules
Participants list includes all discovered emails plus known participants
Latest actionable buyer turn is identified deterministically
Attribution confidence meets or exceeds the 0.70 gate
Buyer role confidence meets or exceeds the 0.70 gate V1.2.2
Buyer domain is either: provided via config, unambiguous (single non-seller
domain), or resolved via known_participants V1.2
Blocked Guarantees
No downstream state extraction or message generation should proceed
Human or upstream resolver can select between top-2 candidates without
reading full raw thread (attribution ambiguity)
Upstream system can provide missing config and retry (missing config) (V1.1
Upstream system providing known_participants with explicit buyer role will not
trigger missing config block V1.2
Policy Engine will receive buyer_role_confidence and gate via HB_002b
V1.2.2
11. Examples (Fixtures)
Example 1: Simple Gmail Thread (Happy Path)
[... existing content unchanged ...]
Example 2: Outlook Thread with Signature
[... existing content unchanged ...]
Example 3: Ambiguous Speaker (Blocked)
[... existing content unchanged ...]
Example 4: HTML-Only Thread
GENSE Thread Ingestion & Normalization 18

[... existing content unchanged ...]
Example 5: Single External Domain (No Config Needed)
[... existing content unchanged ...]
Example 6: Header Email with Conflict (V1.1)
[... existing content unchanged ...]
Example 7: Multi-Domain Thread with known_participants Buyer
(V1.2)
[... existing content unchanged ...]
Example 8: Partial Attribution with Multiple Domains (V1.2)
[... existing content unchanged ...]
Example 9: High Attribution, Low Role Confidence (V1.2.2)
Input: Thread with 3 external domains (acme.com, partner.io, consultant.co),
crm_account_domain not provided, no known_participants buyer. Latest turn
attributed to alice@acme.com with high confidence (explicit From: header).
Expected:
attribution_confidence  0.85 (header email floor applied)
buyer_role_confidence  0.55 (multi_domain_frequency heuristic)
status = "blocked"
reason = "buyer_role_ambiguous"
W016_ROLE_AMBIGUOUS warning present
role_ambiguity_detail populated with confidence factors
Trace Summary:
Attribution passed: we KNOW alice@acme.com sent the message
Role failed: we DON'T KNOW if acme.com is the buyer (could be partner or
consultant)
GENSE Thread Ingestion & Normalization 19

System blocks and routes to human review via Policy Engine HB_002b
Example 10: Explicit Buyer in known_participants (V1.2.2)
Input: Thread with 2 external domains, known_participants includes {"email":
"jane@acme.com", "role": "buyer"}
Expected:
attribution_confidence  0.70
buyer_role_confidence  1.00 (known_participant_explicit)
status = "success"
No W016 warning
12. Test Vectors
Test Vector ID Expected Outcome
Success, turns=2, confidence  0.70,
TV_02_simple_gmail_wrote_line
buyer_role_confidence  0.70
Success, turns split correctly, signature
TV_02_edge_outlook_original_message
stripped, timestamps parsed
Blocked,
TV_02_failure_ambiguous_speaker_no_emails reason=speaker_attribution_ambiguous,
top-2 candidates, confidence  0.70, W004
Success if stripping yields content, else
TV_02_edge_html_only blocked with content_unparseable and
W009
Blocked, reason=no_actionable_buyer_turn,
TV_02_edge_auto_reply
W007_AUTO_REPLY_DETECTED
Success if new text exists, else blocked;
TV_02_edge_quote_strip_aggressive
W012_QUOTE_STRIP_AGGRESSIVE
Success, confidence=0.70 (floor applied),
TV_02_success_header_email_only attribution.method=header_from, no W005
(V1.1
TV_02_failure_header_email_with_conflict Blocked, confidence=0.55,
W005_SPEAKER_CONFLICT, floor NOT
GENSE Thread Ingestion & Normalization 20

Test Vector ID Expected Outcome
applied V1.1
Blocked, reason=required_config_missing,
TV_02_failure_multi_domain_no_config W014, candidate_buyer_domains.length >=
2 V1.1
Success, buyer domain assigned to single
TV_02_success_single_domain_no_config
non-seller domain, no W014 V1.1
Success, multi-domain thread with
known_participants buyer exemption, no
TV_02_success_known_participant_buyer
W014, no required_config_missing block
V1.2
Blocked, reason=required_config_missing,
candidate_buyer_domains sorted by
TV_02_missing_config_partial_attribution
email_count, attributed_turn_count excludes
null-attribution turns V1.2
Success, buyer_role_confidence  0.85
TV_02_success_high_role_confidence (known_participant or single_domain), no
W016 V1.2.2
Blocked, reason=buyer_role_ambiguous,
attribution_confidence  0.70,
TV_02_failure_low_role_confidence
buyer_role_confidence  0.70, W016
present V1.2.2
13. Version and Changelog
Version Date Changes
MASTER Consolidated from duplicate source
documents. Complete specification for implementation:
1.0 20260119 deterministic splitting, stripping, attribution scoring,
latest actionable buyer selection, and top-2 ambiguity
output with 0.70 gating.
1.1 20260119 AMENDMENT Architecture audit fixes. 1 Added
header email sufficiency override with conflict guard—
explicit From: header floors confidence at 0.70 unless
W005 conflict present 6.6.1. 2 Multi-domain threads
without crm_account_domain now block with
GENSE Thread Ingestion & Normalization 21

Version Date Changes
required_config_missing instead of inferring buyer
domain 6.7.1. 3 Single non-seller domain treated as
unambiguous buyer (no config required). (4) Added
candidate_buyer_domains to blocked output for
missing config. 5 Added FM_007 failure mode. 6
Updated W014 meaning. 7 Added test vectors for
new scenarios. Contract-aligned: routes to existing
Action 2 path, no Build Contract changes required.
AMENDMENT Stress-test gap resolution. 1 Added
known_participants exemption—if any participant has
role=="buyer" in known_participants, skip
required_config_missing check for
crm_account_domain 6.7.1. 2 Clarified
candidate_buyer_domains metrics—replaced
ambiguous "frequency" with deterministic
"email_count" (count of distinct emails) and added
"attributed_turn_count" for secondary signal 5.3. 3
1.2 20260119 Added sort specification for candidate_buyer_domains
(email_count DESC, then attributed_turn_count DESC.
4 Added attribution.method="known_participant" for
explicit role assignment 6.6. 5 Updated role
inference priority to check known_participants first
6.7. 6 Added two test vectors for new scenarios
12. 7 Added two examples for new scenarios 11.
Contract-aligned: no downstream changes required—
exemption reduces blocks, metric clarification is
internal.
PATCH Added deterministic guard for
known_participant evidence weight—+0.50 may only
apply when 1 resolving via known_participants
1.2.1 20260119 mapping, 2 no W005_SPEAKER_CONFLICT present,
3 no header_from already captured. Prevents weight
stacking from overriding conflict guard. No contract
changes.
1.2.2 20260120 PATCH Added buyer_role_confidence to output schema
and processing rules. 1 Added buyer_role_confidence
field to success output 5.1 and blocked outputs 5.2,
5.3. 2 Added new blocked output for
GENSE Thread Ingestion & Normalization 22

Version Date Changes
buyer_role_ambiguous 5.4. 3 Added Section 6.11
(Buyer Role Confidence Calculation) with deterministic
scoring rules. 4 Added Section 6.12 Buyer Role
Confidence Gating) at 0.70 threshold. 5 Added
FM_008 failure mode. 6 Added
W016_ROLE_AMBIGUOUS warning. 7 Added two
examples 9, 10 and two test vectors for role
confidence. Contract-aligned: Fulfills Policy Engine
v1.1.1 requirement for buyer_role_confidence field.
Routes to existing Action 1 path via HB_002b.
Appendix A: Parsing Warnings Taxonomy
Code Severity Meaning
No turn boundaries detected;
W001_NO_BOUNDARIES_FOUND Medium
single-turn parse attempted
Timestamp could not be
W003_TIMESTAMP_INFERRED Low extracted; using inferred
order
No email found for speaker;
W004_SPEAKER_EMAIL_MISSING Medium
using name-based attribution
Conflicting attribution
W005_SPEAKER_CONFLICT High
evidence in same turn
Internal forward detected and
W006_INTERNAL_FORWARD_EXCLUDED Low
excluded from analysis
Out-of-office or auto-reply
W007_AUTO_REPLY_DETECTED Medium
detected
HTML-to-text conversion may
W009_HTML_STRIPPED_LOSSY Low
have lost formatting
Quote stripping removed
W012_QUOTE_STRIP_AGGRESSIVE Medium
60% of turn content
Footer removed by legalese
W013_FOOTER_HEURISTIC_STRIP Low
density heuristic
GENSE Thread Ingestion & Normalization 23

Code Severity Meaning
Multiple non-seller domains
detected;
crm_account_domain required
to identify buyer; module
W014_BUYER_DOMAIN_REQUIRED High blocked with
required_config_missing V1.1
updated meaning); does not
trigger if known_participants
contains buyer V1.2
No turn met actionability
W015_NO_ACTIONABLE_BUYER_TURN Medium
criteria; using fallback
Buyer role could not be
determined with sufficient
W016_ROLE_AMBIGUOUS High confidence;
buyer_role_confidence 
0.70 V1.2.2
Appendix B: Implementation Notes
[... existing content unchanged ...]
Appendix C: Contract Alignment Verification (V1.2.2
AMENDED)
This amendment adds ONE new field to success output:
Module Impact Reason
buyer_role_confidence is a Module 02  Policy
Build Contract 01 None
Engine contract, not Build Contract
V1.1.1 requires buyer_role_confidence; this patch
Policy Engine 06 ALIGNED
provides it; HB_002b gates at 0.70
Module 02 requirements unchanged at interface
Build Index (01b) None
level
Module 03 State Expects turns[] array—no schema change; passes
None
Extractor) through buyer_role_confidence
GENSE Thread Ingestion & Normalization 24

Routing verification for buyer_role_ambiguous:
Module 02 output: {
"status": "blocked",
"reason": "buyer_role_ambiguous",
"attribution_confidence" 0.85,
"buyer_role_confidence" 0.58,
...
}
Orchestrator behavior:
Module 02 blocks  Pipeline stops
If orchestrator allows blocked threads to reach Policy Engine (defense-in-
depth):
Policy Engine HB_002b evaluates: buyer_role_confidence 0.58  0.70
Result: Action 1 (escalate_to_human_review)
V1.2.2 success behavior:
Module 02 output: {
"status": "success",
"attribution_confidence" 0.92,
"buyer_role_confidence" 0.85,
...
}
Policy Engine evaluation:
HB_002 attribution_confidence 0.92  0.70  PASS
HB_002b: buyer_role_confidence 0.85  0.70  PASS
Proceed to priority locks
Document Control
GENSE Thread Ingestion & Normalization 25

Version Date Author Changes
1.0 20260119 System Initial consolidated specification
1.1 20260119 Claude Architecture audit fixes
1.2 20260119 Claude Stress-test gap resolution
1.2.1 20260119 Claude known_participant evidence guard
Added buyer_role_confidence field
1.2.2 20260120 Claude and gating. Closes Policy Engine
v1.1.1 integration gap.
End of Thread Ingestion & Normalization Specification v1.2.2
GENSE Thread Ingestion & Normalization 26