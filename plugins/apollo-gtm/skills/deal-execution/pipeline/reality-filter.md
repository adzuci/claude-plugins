---
name: reality-filter
description: >
  Layer 1 epistemic control skill that evaluates claims, statements, and assertions
  for truth status before any downstream skill reasons, routes, or acts on them.
  Decomposes input into atomic claims, identifies source provenance, assesses source
  quality, checks for support and contradiction, detects model-injected or unsupported
  specificity, and assigns each claim a truth-status tag, confidence score, and
  downstream handling flags. Use when downstream behavior depends on the truth status
  of claims, when input mixes fact and inference, when model-generated content must
  be grounded, or when the cost of acting on a false premise is non-trivial.
metadata:
  author: David Johnson-Hall
  version: '1.1'
  layer: 1-epistemic-control
  architecture: Apollo GTM Skill Library
---

# Reality Filter

Layer 1 epistemic control skill. Evaluates claims for truth status before any downstream skill is allowed to reason, route, plan, or act on them. It is a gatekeeper, not a generator.

## Purpose

reality-filter exists because most system failures happen before reasoning. They happen when false, weak, ambiguous, stale, or model-invented claims are treated as solid reality. Once bad claims enter the stack, every later layer compounds the error.

reality-filter prevents that by separating:
- what is known
- what is likely
- what is merely asserted
- what is assumed
- what is contradicted
- what is invented or unsupported
- what remains unknown

Its function is not to prove everything with certainty. Its function is to stop the system from silently collapsing assertions, guesses, and facts into the same category.

## When to Use This Skill

Use reality-filter whenever downstream behavior depends on the truth status of claims.

**Typical use cases:**
- Raw emails, Slack, docs, notes, transcripts, tickets, CRM entries
- User instructions containing factual premises
- Model-generated summaries or extractions that may contain drift
- Planning or routing tasks where bad assumptions create execution risk
- Legal, medical, financial, operational, or high-stakes contexts
- Any workflow where "the model probably meant" is not acceptable

**Run reality-filter before:**
- state-extractor when source material mixes fact, inference, rumor, and intent
- bounded-action-router when action selection depends on claim validity
- Message generation when outputs must avoid unsupported assertions
- Execution skills that would trigger external side effects

## When NOT to Use This Skill

- Input is already epistemically tagged by a trusted upstream system and the receiving layer is configured to trust that tagging
- The task is purely creative or exploratory with no downstream action dependency
- The input is a single atomic verified instruction with no embedded claims

## Core Principles

1. **Do not flatten epistemic status.** Facts, inferences, assertions, assumptions, and contradictions are different things. Never merge them.
2. **Uncertainty is signal, not failure.** Unknown and disputed are valid, useful classifications. They prevent bad downstream moves.
3. **Source quality and truth status are separate axes.** An authoritative person can assert something false. A weak source can report something true.
4. **Model output is never self-verifying.** Fluent text does not equal truth. Model-generated claims require grounding against source material.
5. **Prefer unknown over false certainty.** When evidence is insufficient, tag unknown rather than guessing.
6. **Prefer disputed over premature synthesis.** When credible contradiction exists, preserve both sides rather than choosing a winner.
7. **Split before classifying.** Compound claims get decomposed into atomic units before any truth-status assignment.
8. **Attribution survives.** Who said it, where it came from, and how it was sourced must persist through the entire pipeline.
9. **Downstream handling is explicit.** Every claim gets flags for what layers can safely use it and what layers cannot.

## Layer Role in the Stack

See `docs/archive/FOUNDATION.md` for the full layer stack. reality-filter sits at Layer 1.

Layer 1 decides what reality substrate is safe to use. Layer 2 structures it. Layer 3 decides what actions are valid. Layer 4 acts.

## Input Contract

reality-filter accepts three input modes.

### Mode 1: Raw Unstructured Input

Emails, Slack transcripts, meeting notes, pasted documents, freeform prompts, model-generated summaries.

```yaml
input_type: raw_text
content: "<full text>"
context:
  source_channel: email | slack | doc | meeting_notes | chat | model_output | other
  timestamp: optional
  speaker_map: optional
  provenance: optional
```

### Mode 2: Structured Claims List

Pre-extracted claims from another parser, assertions from a prior pass, checklist items.

```yaml
input_type: claims_list
claims:
  - id: "c1"
    text: "Customer signed contract on March 1."
    source_ref: "email_4"
    speaker: "Alice"
    timestamp: "2026-03-01T14:10:00Z"
```

### Mode 3: Mixed Structured + Raw

Claims are extracted but raw context is available for validation.

```yaml
input_type: mixed
content: "<raw text>"
claims:
  - id: "c1"
    text: "Budget was approved."
    source_ref: "message_3"
context:
  source_channel: slack
```

### Optional Control Parameters

```yaml
mode: strict | balanced | permissive
domain: general | legal | financial | medical | ops | sales | custom
require_source_for_verified: true | false
staleness_window_days: optional
block_on_disputed_high_risk: true | false
treat_model_output_as_claim_source: true | false
```

### Mode 4: Prior Claims (Cross-Invocation)

When processing a continuation of previously evaluated input (follow-up messages, multi-turn threads, updated documents), the caller may pass prior claim evaluations to avoid redundant re-evaluation and enable cumulative evidence tracking.

```yaml
prior_claims:
  - claim_id: string
    normalized_claim: string
    truth_status: string
    confidence_band: string
    source_quality: string
    handling: {}
    last_evaluated: timestamp
```

When prior_claims is present:
1. Match new claims against prior claims by semantic similarity (not exact text match)
2. For matched claims with no new evidence: carry forward the prior evaluation unchanged
3. For matched claims with new evidence: re-evaluate and note the status change in reasoning_trace with `prior_status` and `upgrade_reason` or `downgrade_reason`
4. For unmatched new claims: evaluate from scratch using the standard pipeline
5. Never silently drop a prior claim. If a prior claim is absent from the new input, carry it forward with a `not_in_current_input` flag

The caller is responsible for passing prior output. The skill does not persist state between invocations.

## Process

### Step 1: Normalize Input

Determine whether input is raw, structured claims, or mixed. Preserve provenance metadata. Identify source channel and any speaker attribution present in the input.

### Step 2: Extract Candidate Claims

Identify discrete claim units in the input. A claim is any statement that asserts something about the world that could be true or false, or that downstream layers might act on.

Not claims: greetings, formatting, meta-commentary about the conversation itself (unless it contains embedded factual assertions).

### Step 3: Decompose Compound Claims

Split compound statements into atomic claims where one clause could change status independently from another.

Example input: "Finance approved the budget and legal signed off last week."

Decomposed:
1. Finance approved the budget.
2. Legal signed off.
3. The sign-off happened last week.

Rule: if one part could be true while another is false, split them. Never assign a single truth tag to a compound claim unless the entire compound is supported as a unit.

### Step 4: Classify Claim Type

Tag each atomic claim with its type. Different claim types have different verification standards.

| Claim Type | Description | Verification Standard |
|---|---|---|
| factual | Asserts something about the world | Requires evidence or source |
| quantitative | Contains numbers, metrics, amounts | Requires source data |
| temporal | Contains dates, times, sequences | Requires timeline evidence |
| causal | Asserts cause and effect | Requires supporting chain |
| identity | Asserts who someone is or their role | Requires identification evidence |
| intent | Asserts what someone plans or wants | Requires speaker attribution |
| completion_status | Asserts something is done or not done | Requires confirmation evidence |
| interpretation | Infers meaning from behavior or text | Must be tagged as derived |
| normative | Asserts value judgment or should/ought | Not verifiable as fact |
| predictive | Asserts future outcome | Not verifiable as fact |
| instructional | Directs action | Assessed for authority, not truth |
| policy | States a rule or policy | Requires policy source |
| preference | Asserts a personal preference | Verified by attribution only |

### Step 5: Identify Source and Attribution

For each claim, determine:
- Who said it (speaker attribution)
- Where it came from (source reference)
- Whether it is raw human input or model-generated
- Whether it is firsthand or secondhand
- Whether attached evidence exists

### Step 6: Assess Source Quality

Evaluate the source using the source quality taxonomy. Do not conflate speaker authority with evidentiary support.

See `docs/archive/FOUNDATION.md` for the Source Quality Scale definitions.

### Step 7: Check Explicit Support

For each claim, look for:
- Direct evidence (documents, records, artifacts)
- Quoted source text that matches the claim
- Cross-reference support from independent sources
- System records that confirm or contradict
- Corroborating artifacts

### Step 8: Check Contradiction

For each claim, look for:
- Direct conflicts with other claims in the input
- Silent mismatch between summary and source
- Timeline collisions (dates that don't align)
- Incompatible numbers, names, or states
- Prior claims in the same thread that contradict current claims

**Asymmetric evidence rule:** When two claims contradict but their evidentiary support is materially different, do not tag both as disputed. If one side has authoritative or primary_direct source quality with supporting evidence, and the other is secondary_unverified or weaker with no supporting evidence, tag the stronger claim as probable (not disputed) and the weaker claim as contradicted. Preserve both in the output with cross-references. This prevents over-tagging disputes when evidence clearly favors one side, reducing unnecessary human review bottlenecks.

When evidence is roughly symmetric (both sides have comparable source quality and support), tag both as disputed per the default behavior.

### Step 9: Detect Model or Narrator Injection

Flag when the text contains:
- Unsupported bridging language ("therefore," "as a result" without causal evidence)
- Extra specificity not present in source (precise dates, names, numbers added)
- Invented causal links
- Implied facts absent from raw source
- Certainty upgrades between source and summary
- Merged speakers or merged timelines
- Normative judgments phrased as facts

### Step 10: Assign Truth Status

Apply the epistemic classification taxonomy (defined below) to each atomic claim.

### Step 10.5: Assess Staleness

For each claim with a timestamp or datable reference, evaluate temporal freshness against the staleness window.

When staleness_window_days is set: compare the claim's timestamp to the current date. If the claim's age exceeds the window, append the `stale_possible` epistemic flag.

When staleness_window_days is not set, apply domain defaults:

| Domain | Default Staleness Window |
|---|---|
| sales | 7 days |
| ops | 7 days |
| financial | 30 days |
| legal | 90 days |
| medical | 30 days |
| general | 14 days |

Staleness does not change truth_status. A claim can be verified and stale simultaneously. Staleness affects handling: a stale verified claim should have safe_for_action_routing set to false unless re-confirmed, because historical truth does not guarantee current operational validity.

When a claim is flagged stale_possible, add a recommended_next_check entry: "Re-verify [claim] -- last evidence is [age] days old, exceeds [domain] staleness window."

### Step 11: Assign Confidence

Rate confidence in the classification itself (how certain you are about the tag you assigned), not confidence in the claim being true.

See `docs/archive/FOUNDATION.md` for the Confidence Bands definition. Note: reality-filter's low band is 0.35-0.54 and very_low is 0.00-0.34 (slightly different from FOUNDATION.md general bands, which reflect classification certainty rather than claim certainty).

Confidence should reflect: clarity of claim boundaries, source strength, corroboration level, contradiction presence, ambiguity, temporal freshness, and decomposition quality.

### Step 12: Apply Downstream Handling Flags

For each claim, determine:
- safe_for_state_extraction: can Layer 2 use this as structured state?
- safe_for_action_routing: can Layer 3 route actions based on this?
- requires_human_review: should a human verify before downstream use?
- downgrade_to_assertion: should this be treated as assertion regardless of surface presentation?
- exclude_from_downstream_facts: should this be blocked from entering operative state?

### Step 13: Summarize Unresolved Risk

Emit summary metadata: contradiction summaries, missing evidence, disputed high-impact claims, fabrication risk level, and recommended next verification steps.

## Epistemic Classification Taxonomy

These are the valid truth-status tags. The skill never invents a new tag.

### verified
Directly supported by strong evidence, authoritative record, direct source artifact, or reliable corroboration. Use when explicit documentary support exists, authoritative system record confirms it, direct quote plus corroborating artifact matches, or multiple independent reliable sources converge.

### probable
Not fully proven, but strongly supported by reliable signals or converging evidence. Use when evidence is strong but not definitive, source is credible and context strongly aligns, but small uncertainty remains.

### inferred
Not directly stated, but logically derived from supported evidence. Use when inference is reasonable and traceable, raw evidence supports the inference, and the claim is not explicitly asserted by the source. Important: inferred is not fact. It is a derived interpretation.

### asserted
A person or system said it, but the system does not have enough support to upgrade it. Use when someone claims it directly but there is no supporting evidence yet. It should remain attributable, not accepted as truth.

### assumed
The claim is not present as evidence but appears to have been inserted as a working premise. Use when the system or user is relying on an unstated premise, or the claim is necessary for a plan but unsupported.

### disputed
The claim is actively challenged by another source or participant and cannot currently be resolved. Use when credible contradiction exists, two sources disagree, and no decisive evidence is available yet.

### contradicted
Available evidence directly conflicts with the claim strongly enough that the claim should not be used as true. Use when record evidence disproves the assertion, or direct contradiction is strong and specific.

### fabricated
The claim appears invented, unsupported, or inserted without basis, especially when it includes unjustified specificity. Use when model invented details absent from source, summary contains events, names, dates, or metrics never present in input, or claim presents false precision without support. This is the critical tag for catching hallucinations.

### unknown
There is not enough information to determine truth status. Use when the claim may be important but evidence is missing and no reliable support or contradiction exists.

### not_verifiable
The claim is inherently subjective, normative, speculative, or otherwise outside factual verification. Use for value judgments, preferences, future predictions without factual anchor, or moral framing statements.

## Output Contract

reality-filter outputs a structured claim register plus summary metadata.

```yaml
reality_filter_output:
  skill: reality-filter
  version: "1.1"

  overall_assessment:
    input_reliability: high | medium | low
    contradiction_detected: true | false
    fabrication_risk: low | medium | high
    escalation_recommended: true | false
    notes: []

  claims:
    - claim_id: string
      text: string  # original claim text
      normalized_claim: string  # cleaned, atomic version
      claim_type: factual | quantitative | temporal | causal | identity
                  | intent | completion_status | interpretation | normative
                  | predictive | instructional | policy | preference | other
      subject: string
      predicate: string
      object: string

      truth_status: verified | probable | inferred | asserted | assumed
                    | disputed | contradicted | fabricated | unknown
                    | not_verifiable
      confidence: 0.00 - 1.00
      confidence_band: very_low | low | medium | high | very_high

      source_quality: authoritative | primary_direct | primary_self_report
                      | secondary_reliable | secondary_unverified | hearsay
                      | unsourced | model_generated | conflicted
      source_ref: string | null
      provenance_type: external | human_statement | model_output
                       | system_record | derived
      attribution:
        speaker: string | null
        timestamp: string | null
        channel: string | null

      support:
        evidence_present: true | false
        evidence_type: document | system_record | direct_observation
                       | quote | cross_source_match | none | other
        supporting_refs: []
        corroboration_count: 0
        contradiction_refs: []

      epistemic_flags: []
        # Valid flags:
        # self_reported, secondhand, unsourced, model_injected,
        # inferred_from_context, temporal_ambiguity, stale_possible,
        # contradiction_present, disputed_by_source,
        # unsupported_specificity, compound_claim,
        # high_impact_if_false, requires_external_verification,
        # subjective_claim, scope_ambiguity, attribution_unclear

      handling:
        safe_for_state_extraction: true | false
        safe_for_action_routing: true | false
        requires_human_review: true | false
        downgrade_to_assertion: true | false
        exclude_from_downstream_facts: true | false

      reasoning_trace:
        decomposition_notes: []
        classification_notes: []
        confidence_notes: []

  summary:
    verified_claim_ids: []
    disputed_claim_ids: []
    blocked_claim_ids: []
    uncertain_claim_ids: []
    assumptions_detected: []
    missing_evidence: []
    recommended_next_checks: []

  output_mode: full | minimal  # minimal omits reasoning_trace and full support blocks

  required_downstream_fields:
    # Minimum fields downstream layers MUST preserve and propagate.
    # Stripping any of these is an architectural violation.
    - claim_id
    - truth_status
    - confidence_band
    - source_quality
    - epistemic_flags
    - handling

  epistemic_audit_trail: []
    # Append-only log. Each downstream layer adds an entry recording
    # how it consumed the epistemic tags. Reality-filter seeds the first entry.
    # Format per entry:
    #   - layer: string (e.g., "reality-filter", "state-extractor")
    #   - version: string
    #   - action: string (e.g., "assigned", "consumed", "preserved", "overridden")
    #   - claim_ids_affected: []
    #   - notes: string
```

## Handoff Contracts

### To state-extractor (Layer 2)

state-extractor should receive claims plus tags, not a flattened "facts only" blob.

How Layer 2 should use epistemic tags:
- verified and probable claims can populate core state fields
- inferred claims can populate derived fields with explicit epistemic tag preserved
- asserted/assumed/unknown claims should populate optional or quarantined fields
- disputed/contradicted/fabricated claims should not populate operative state as accepted fact

Layer 1 preserves epistemic color. Layer 2 structures it without bleaching it.

**Tag Taxonomy Mapping:** See `docs/archive/FOUNDATION.md` for the Tag Set Mapping (L1 to L2A) table. When reality-filter has run upstream, state-extractor should preserve reality-filter's tags in a `rf_truth_status` field and not overwrite them with its own epistemic labels.

### To bounded-action-router (Layer 3)

Router should treat epistemic status as a routing variable, not just metadata.

Default blocks for high-risk actions:
- fabricated, contradicted, disputed, unknown, assumed

May allow low-risk info-gathering or clarifying actions on:
- asserted, inferred, probable

May allow state-committing or external actions only on:
- verified, sometimes probable with corroboration depending on domain

### To execution skills (Layer 4)

Execution skills should use tags to constrain language and action:
- Message composer should say "it appears" or "you mentioned" for asserted claims
- Planner should request confirmation for assumed claims
- Updater should refuse to write contradicted claims into a system of record
- Summarizer should preserve "reported" vs "confirmed"

## Calibration Notes

### Mode Guidance

**Strict mode** (legal, medical, financial, security, identity resolution, system-of-record updates, external commitments):
- Verified threshold higher
- Probable used sparingly
- Asserted does not propagate far
- Model-generated claims treated as high risk
- Disputed high-impact claims trigger escalation

**Balanced mode** (normal business ops, planning, workflow routing, research synthesis):
- Probable and inferred allowed with clear tags
- Action router may proceed with bounded low-risk actions
- Unknown prompts clarifying or evidence-gathering steps

**Permissive mode** (brainstorming, exploratory sensemaking, early drafts, low-stakes summarization):
- More inferred/probable classifications tolerated
- More tolerance for weakly grounded working hypotheses
- Still no silent upgrading to verified

### Threshold Matrix

This matrix defines the minimum truth_status and confidence_band required for each handling flag under each mode. Downstream layers should use this as a deterministic gate, not a suggestion.

| Handling Flag | Strict | Balanced | Permissive |
|---|---|---|---|
| safe_for_state_extraction | verified or probable (high+) | verified, probable, or inferred (medium+) | verified, probable, inferred, or asserted (medium+) |
| safe_for_action_routing | verified (high+) | verified or probable (medium+) | verified, probable, or inferred (medium+) |
| requires_human_review | anything below verified | disputed, contradicted, fabricated, unknown, assumed | fabricated, contradicted, disputed |
| exclude_from_downstream_facts | fabricated, contradicted, disputed, assumed, unknown | fabricated, contradicted | fabricated |

Confidence_band minimum notation: "high+" means high or very_high. "medium+" means medium, high, or very_high.

When a claim's truth_status qualifies but its confidence_band is below the mode threshold, downgrade the handling flag to the next more conservative setting. For example, a probable claim at low confidence in balanced mode should be treated as if safe_for_action_routing is false.

### When to Be Stricter

Increase strictness when:
- Action has external side effects
- Harm if false is high
- User asked for certainty
- Domain is regulated
- Source is model-generated
- Contradictions exist
- Stale information may matter

### When to Be More Permissive

Relax slightly when:
- Task is exploratory
- No external action will occur
- Goal is hypothesis generation
- Outputs remain explicitly provisional

### Evidence Hierarchy

Strongest to weakest:
1. Authoritative record (system of record, signed document, database)
2. Direct artifact / primary document
3. Firsthand direct statement with attributable source
4. Corroborated secondary source
5. Uncorroborated secondary source
6. Hearsay
7. Unsourced
8. Model-generated unsupported statement

## Failure Modes

### 1. Claim bundling
Multiple subclaims get one status tag. One verified fragment makes the whole sentence look verified. Fix: split into atomic claims before classification (Step 3).

### 2. Attribution collapse
A person says something and the system records it as fact. Assertion becomes reality. Fix: preserve speaker attribution and source type. "Alice reported X" is not equal to "X is true."

### 3. Inference laundering
Model or operator converts implication into fact. "Asked for revised quote" becomes "unhappy customer." Fix: tag as inferred, preserve supporting evidence, keep the original factual claim separate.

### 4. Unsupported specificity
Model inserts names, dates, numbers, or causes not present in source. Fabrication looks authoritative. Fix: compare against source. If unsupported, tag fabricated or assumed.

### 5. Staleness blindness
Old verified claim treated as current. Outdated state drives action. Fix: add freshness/staleness checks. Truth status may remain verified historically but unsafe operationally.

### 6. Contradiction smoothing
Summary reconciles conflicting claims into a single neat story. Dispute disappears. Fix: preserve contradiction explicitly. Tag disputed or contradicted. Never merge.

### 7. Normative claims treated as factual
Opinion or interpretation gets verified-like handling. Biased narrative enters state. Fix: use claim_type classification and tag not_verifiable or asserted interpretation.

### 8. Intent over-upgrade
Speaker says "I'll do it" and system treats action as completed. Promise becomes completion. Fix: separate intent claims from completion_status claims. "Plans to send" is not "sent."

### 9. Source authority over-weighting
High-status speaker is treated as always correct. Confident but wrong assertions upgrade too far. Fix: authority influences source quality, not automatic truth status.

### 10. Model summary trust leakage
Downstream layers trust extracted summaries more than raw source. Hallucinated state propagates. Fix: treat model output as a distinct provenance type requiring grounding against source material.

### 11. Confidence-truth conflation
High confidence in the classification gets interpreted as high confidence the claim is true. Fix: confidence measures certainty in the tag assignment, not certainty in the world. A claim can be tagged asserted with very_high confidence (the system is very sure it should remain an assertion, not be upgraded).

### 12. Epistemic tag decay
Tags are assigned in Layer 1 but silently dropped or ignored by Layer 2/3/4. The audit trail exists but no one reads it. Fix: handoff contracts explicitly require downstream layers to consume and preserve epistemic tags. Layers that strip tags should be treated as architectural violations.

## Example Transformations

Examples are condensed for readability. In production, all claims should include full output schema fields.

### Example 1: Direct Assertion Without Proof

**Input:**
```yaml
input_type: raw_text
content: |
  Alice: Finance approved the budget yesterday.
  Bob: Great, then let's notify the vendor.
context:
  source_channel: slack
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1
    text: "Finance approved the budget yesterday."
    normalized_claim: "Finance approved the budget on the prior day."
    claim_type: factual
    truth_status: asserted
    confidence: 0.87
    confidence_band: high
    source_quality: primary_self_report
    provenance_type: human_statement
    attribution:
      speaker: Alice
      channel: slack
    support:
      evidence_present: false
      evidence_type: none
      corroboration_count: 0
    epistemic_flags:
      - self_reported
      - requires_external_verification
      - high_impact_if_false
    handling:
      safe_for_state_extraction: true
      safe_for_action_routing: false
      requires_human_review: true
      exclude_from_downstream_facts: false

summary:
  recommended_next_checks:
    - "Check finance system or approval email before notifying vendor."
```

**Why this matters:** The claim is not false. It is just not verified. The router should block action that depends on approval being confirmed until verification occurs.

### Example 2: Inferred Claim Separated from Fact

**Input:**
```yaml
input_type: raw_text
content: |
  Customer replied: "Can you revise the pricing and remove onboarding fees?"
context:
  source_channel: email
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1
    text: "Customer asked for revised pricing."
    normalized_claim: "Customer requested pricing revision."
    claim_type: factual
    truth_status: verified
    confidence: 0.96
    confidence_band: very_high
    source_quality: primary_direct
    provenance_type: external
    attribution:
      speaker: customer
      channel: email
    support:
      evidence_present: true
      evidence_type: quote
      supporting_refs: ["email_1"]
    epistemic_flags: []
    handling:
      safe_for_state_extraction: true
      safe_for_action_routing: true

  - claim_id: c2
    text: "Customer is unhappy with the offer."
    normalized_claim: "Customer is dissatisfied with current pricing."
    claim_type: interpretation
    truth_status: inferred
    confidence: 0.61
    confidence_band: medium
    source_quality: derived
    provenance_type: derived
    support:
      evidence_present: true
      evidence_type: quote
      supporting_refs: ["email_1"]
    epistemic_flags:
      - inferred_from_context
    handling:
      safe_for_state_extraction: true
      safe_for_action_routing: false
```

**Why this matters:** The factual request is verified (the customer literally said it). The emotional interpretation ("unhappy") is inference. Downstream layers can act on the request but should not treat dissatisfaction as confirmed state.

### Example 3: Fabricated Model Summary Caught

**Input:**
```yaml
input_type: mixed
content: |
  Raw source:
  "We should probably revisit the contract next week."
claims:
  - id: c1
    text: "The customer confirmed they will sign the contract next Tuesday."
    source_ref: "model_summary_1"
context:
  source_channel: model_output
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1
    text: "The customer confirmed they will sign the contract next Tuesday."
    normalized_claim: "Customer confirmed signature will occur next Tuesday."
    claim_type: temporal
    truth_status: fabricated
    confidence: 0.94
    confidence_band: very_high
    source_quality: model_generated
    provenance_type: model_output
    support:
      evidence_present: false
      evidence_type: none
      contradiction_refs: ["raw_source_1"]
    epistemic_flags:
      - model_injected
      - unsupported_specificity
      - high_impact_if_false
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      requires_human_review: true
      exclude_from_downstream_facts: true

summary:
  fabrication_risk: high
  recommended_next_checks:
    - "Do not treat model summary as source of truth."
    - "Re-extract claims from raw source."
```

**Why this matters:** Raw source says "probably revisit next week." Model summary upgraded this to "confirmed signing next Tuesday." The filter catches the unsupported specificity: "confirmed" was never said, "signing" was never stated, "Tuesday" was invented. This is exactly the kind of hallucinated precision the filter exists to prevent.

### Example 4: Disputed Claim with Unresolved Contradiction

**Input:**
```yaml
input_type: raw_text
content: |
  Alice: Legal approved the language.
  Mark: Legal has not reviewed it yet.
context:
  source_channel: slack
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1
    text: "Legal approved the language."
    truth_status: disputed
    confidence: 0.89
    confidence_band: high
    source_quality: secondary_unverified
    attribution:
      speaker: Alice
    support:
      evidence_present: false
      contradiction_refs: ["c2"]
    epistemic_flags:
      - disputed_by_source
      - requires_external_verification
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      requires_human_review: true

  - claim_id: c2
    text: "Legal has not reviewed it yet."
    truth_status: disputed
    confidence: 0.89
    confidence_band: high
    source_quality: primary_self_report
    attribution:
      speaker: Mark
    support:
      evidence_present: false
      contradiction_refs: ["c1"]
    epistemic_flags:
      - disputed_by_source
      - requires_external_verification
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      requires_human_review: true

summary:
  contradiction_detected: true
  disputed_claim_ids: ["c1", "c2"]
  recommended_next_checks:
    - "Verify directly with legal department before proceeding."
```

**Why this matters:** The filter does not collapse the contradiction. It does not pick a winner. Both claims are tagged disputed with cross-references. The router should select "verify with legal" rather than "proceed."

### Example 5: Multi-Source Corroboration Upgrades Status

**Input:**
```yaml
input_type: raw_text
content: |
  Alice (sales): Customer confirmed they're moving forward with the annual plan.
  CRM note (March 15): Opportunity moved to "Verbal Commit" by Alice.
  Customer email (March 14): "We've decided to go with the annual option. Please send the contract."
context:
  source_channel: mixed
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1
    text: "Customer confirmed they are moving forward with the annual plan."
    normalized_claim: "Customer committed to annual plan."
    claim_type: intent
    truth_status: verified
    confidence: 0.92
    confidence_band: very_high
    source_quality: primary_direct
    provenance_type: external
    attribution:
      speaker: customer
      channel: email
    support:
      evidence_present: true
      evidence_type: cross_source_match
      supporting_refs: ["customer_email_march_14", "crm_note_march_15", "alice_report"]
      corroboration_count: 3
    epistemic_flags: []
    handling:
      safe_for_state_extraction: true
      safe_for_action_routing: true
      requires_human_review: false
```

**Why this matters:** Three independent sources converge: the customer's own words, a CRM system update, and a sales rep report. The customer email is the primary evidence. The CRM note and Alice's statement corroborate. This is what justified upgrade from asserted to verified looks like: not because someone said it confidently, but because independent sources align.

### Example 6: Normative Claim Tagged Not Verifiable

**Input:**
```yaml
input_type: raw_text
content: |
  Team lead in Slack: "This is the best product roadmap we've ever had.
  Engineering velocity is up 30% this quarter."
context:
  source_channel: slack
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1
    text: "This is the best product roadmap we've ever had."
    normalized_claim: "Current product roadmap is the best in company history."
    claim_type: normative
    truth_status: not_verifiable
    confidence: 0.93
    confidence_band: very_high
    source_quality: primary_self_report
    provenance_type: human_statement
    attribution:
      speaker: team_lead
      channel: slack
    support:
      evidence_present: false
      evidence_type: none
    epistemic_flags:
      - subjective_claim
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      requires_human_review: false
      exclude_from_downstream_facts: true

  - claim_id: c2
    text: "Engineering velocity is up 30% this quarter."
    normalized_claim: "Engineering velocity increased 30% in current quarter."
    claim_type: quantitative
    truth_status: asserted
    confidence: 0.82
    confidence_band: high
    source_quality: primary_self_report
    provenance_type: human_statement
    attribution:
      speaker: team_lead
      channel: slack
    support:
      evidence_present: false
      evidence_type: none
    epistemic_flags:
      - requires_external_verification
      - self_reported
    handling:
      safe_for_state_extraction: true
      safe_for_action_routing: false
      requires_human_review: false

summary:
  recommended_next_checks:
    - "Verify 30% velocity claim against sprint metrics or engineering dashboard."
```

**Why this matters:** The two sentences look similar but are epistemically different. "Best roadmap ever" is a value judgment with no verification path. "30% velocity increase" is a quantitative claim that could be checked against data but has no supporting evidence yet. The filter separates them: one gets excluded from downstream facts entirely, the other stays as an asserted claim awaiting verification.

### Example 7: Partial Fabrication in Model Summary

**Input:**
```yaml
input_type: mixed
content: |
  Raw source (email thread):
  Customer: "We need to discuss the pricing before we can commit.
  Can we set up a call next week?"
  Sales rep: "Absolutely, I'll send some times."
claims:
  - id: c1
    text: "Customer expressed concerns about pricing and requested a discount call for next Tuesday at 2pm. The sales team has already prepared a revised proposal with 15% reduction."
    source_ref: "model_summary_1"
context:
  source_channel: model_output
```

**Output (condensed):**
```yaml
claims:
  - claim_id: c1a
    text: "Customer expressed concerns about pricing."
    normalized_claim: "Customer indicated pricing discussion is needed before commitment."
    claim_type: factual
    truth_status: verified
    confidence: 0.91
    confidence_band: very_high
    source_quality: primary_direct
    provenance_type: external
    support:
      evidence_present: true
      evidence_type: quote
      supporting_refs: ["raw_email_customer"]
    epistemic_flags: []
    handling:
      safe_for_state_extraction: true
      safe_for_action_routing: true

  - claim_id: c1b
    text: "Customer requested a call for next Tuesday at 2pm."
    normalized_claim: "Customer requested call scheduled for Tuesday at 2pm."
    claim_type: temporal
    truth_status: fabricated
    confidence: 0.95
    confidence_band: very_high
    source_quality: model_generated
    provenance_type: model_output
    support:
      evidence_present: false
      evidence_type: none
      contradiction_refs: ["raw_email_customer"]
    epistemic_flags:
      - model_injected
      - unsupported_specificity
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      exclude_from_downstream_facts: true
    reasoning_trace:
      classification_notes:
        - "Raw source says 'next week' with no day or time specified. Model inserted 'Tuesday at 2pm' without basis."

  - claim_id: c1c
    text: "Customer requested a discount."
    normalized_claim: "Customer asked for a discount."
    claim_type: factual
    truth_status: fabricated
    confidence: 0.93
    confidence_band: very_high
    source_quality: model_generated
    provenance_type: model_output
    support:
      evidence_present: false
      contradiction_refs: ["raw_email_customer"]
    epistemic_flags:
      - model_injected
      - unsupported_specificity
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      exclude_from_downstream_facts: true
    reasoning_trace:
      classification_notes:
        - "Raw source says 'discuss the pricing.' Model upgraded to 'discount call.' Customer never used the word discount."

  - claim_id: c1d
    text: "The sales team has already prepared a revised proposal with 15% reduction."
    normalized_claim: "Sales team prepared revised proposal with 15% price reduction."
    claim_type: completion_status
    truth_status: fabricated
    confidence: 0.97
    confidence_band: very_high
    source_quality: model_generated
    provenance_type: model_output
    support:
      evidence_present: false
      evidence_type: none
    epistemic_flags:
      - model_injected
      - unsupported_specificity
      - high_impact_if_false
    handling:
      safe_for_state_extraction: false
      safe_for_action_routing: false
      requires_human_review: true
      exclude_from_downstream_facts: true
    reasoning_trace:
      classification_notes:
        - "No mention of revised proposal or 15% in raw source. Entirely invented by model."

summary:
  fabrication_risk: high
  notes:
    - "Model summary contains 1 verified element and 3 fabricated elements within a single sentence. This is partial fabrication -- the most dangerous form because the verified fragment lends false credibility to the fabricated fragments."
  recommended_next_checks:
    - "Discard model summary. Re-extract claims from raw source only."
    - "Verify whether any revised proposal exists via CRM or sales team."
```

**Why this matters:** This is the hardest case for downstream layers: a single model-generated sentence that is partly true and partly invented. The customer did mention pricing. The model then fabricated a specific day and time, inserted the word "discount" (never said), and invented an entire revised proposal with a specific percentage. Without decomposition, the whole sentence might pass as plausible because its first clause is true. The filter breaks it apart, verifies the real fragment, and flags each fabrication independently.

## Scale and Degradation

### Claim Count Limits

Maximum recommended claims per invocation: 50 atomic claims. Inputs producing more than 50 claims after decomposition should be batched.

### Batching Strategy

When input exceeds the claim limit:
1. Split input by natural document boundaries (messages, paragraphs, sections)
2. Process each batch through the full 13-step pipeline independently
3. Merge batch outputs by concatenating claim registers and re-running Step 8 (Check Contradiction) across batches to catch cross-batch conflicts
4. Regenerate summary metadata from merged output

### Priority Ordering

When context budget is constrained, evaluate claims in this order:
1. Claims that downstream layers will act on (action-triggering claims first)
2. Claims with high_impact_if_false potential
3. Claims involving quantitative, temporal, or completion_status types
4. Claims from model_generated or unsourced provenance
5. Remaining claims in document order

### Minimal Output Mode

When full reasoning traces are not feasible, produce a reduced output containing only: claim_id, normalized_claim, truth_status, confidence_band, source_quality, and all five handling flags. Omit reasoning_trace, decomposition_notes, and full support blocks. Mark the output with `output_mode: minimal` so downstream layers know reduced metadata is present.

## Anti-Patterns

These are the behaviors reality-filter is designed to prevent:

- "The model said it confidently, so it must be true."
- "A user mentioned it, so write it into state."
- "A summary implied it, so route on it."
- "A senior stakeholder said it, so no need to verify."
- "The contradiction is annoying, so smooth it out."
- "We need to move fast, so treat likely as confirmed."
