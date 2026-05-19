---
name: humanizer-compressor
description: >
  Layer 4+ post-processing skill that takes structurally correct, constraint-compliant
  draft messages from message-os or GEN-SE and makes them sound more human, more
  sender-native, and more compressed without altering protected meaning. Operates
  within locked upstream constraints: action class, approved claims, single ask,
  commitment boundaries, and required caveats are never changed. Handles voice
  matching, compression, subtle AI-pattern remediation, and channel-native register
  calibration. Use when message-os or GEN-SE output is sendable but sounds assembled
  rather than written, when sender voice alignment matters, or when the draft needs
  tightening for channel fit.
metadata:
  author: David Johnson-Hall
  version: '1.1'
  layer: 4-plus-post-processing
  architecture: Apollo GTM Skill Library
---

# Humanizer-Compressor

Layer 4+ post-processing skill. Takes structurally correct output and makes it sound written, not assembled. Conservative transformer with a verifier loop, not a one-shot rewriter.

## Purpose

humanizer-compressor exists to solve the gap between structurally correct, constraint-safe, epistemically compliant text and text that actually sounds like a real person in a real channel.

message-os produces correct output. humanizer-compressor makes it feel written rather than assembled.

message-os is optimized for correctness under constraints: right action class, right claims, right ask count, right caveats, right channel format. That optimization pushes toward safe, explicit, template-shaped prose. Safe prose often becomes sterile prose.

Correctness and naturalness are different optimization targets. humanizer-compressor handles naturalness without compromising correctness.

The skill does three things:
1. Removes sterile assembly artifacts
2. Matches or approximates sender voice without parroting
3. Compresses excess wording without deleting protected meaning

## When to Use This Skill

Use humanizer-compressor when:
- message-os or GEN-SE output is technically sendable but sounds robotic or over-polished
- sender voice alignment matters for the channel or relationship
- the draft needs tightening for channel fit (email too wordy for Slack, Slack too formal, etc.)
- subtle AI-pattern residue survived message-os's AI-Pattern Gate
- compression is requested without meaning loss

## When NOT to Use This Skill

- message-os output already matches sender voice and channel conventions
- the message is legally or operationally sensitive and near-verbatim preservation matters
- the channel rewards precision over tone polish (compliance filings, legal escalations where exact wording is load-bearing)
- the draft is already very short (under 2 sentences)
- sender profile is weak and the risk of mis-voicing outweighs the benefit
- the task is message composition from scratch (that is message-os's job)
- the task is deciding what action to take (that is bounded-action-router's job)

## Core Principles

1. **Locked elements always win.** Action class, approved claims, single ask, commitment boundaries, and required caveats are never changed. When voice matching or compression conflicts with a locked element, the locked element wins.
2. **Voice is not decoration.** Voice is the final delivery mechanism of intent. A message can be logically right and socially wrong if it sounds robotic, over-smoothed, or unlike the sender.
3. **Match patterns, not phrases.** Voice matching targets stable stylistic tendencies (directness, warmth, cadence, formality), not specific phrases copied from samples. Mimicry is a failure mode.
4. **Compression preserves, it does not generalize.** Compression removes redundancy and excess framing. It never broadens a specific claim, softens a hard boundary, or generalizes a precise condition.
5. **Do not inject fake imperfection.** The goal is natural prose, not synthetic messiness. No intentional typos, no sloppy logic, no forced colloquialisms that the sender would not use.
6. **Generate, verify, then emit.** First produce a candidate. Then mechanically test it against the protected map. Then either accept, revise, or return the original draft unchanged. This is a constrained transformer, not a vibe-based rewrite pass.

## Layer Role in the Stack

See `docs/archive/FOUNDATION.md` for the full layer stack. humanizer-compressor sits at Layer 4+.

humanizer-compressor is the last skill in the pipeline before delivery. It receives already-safe, already-routed, already-structured text and returns polished text with the same safety properties.

## Input Contract

### Minimum Viable Input

```yaml
humanizer_compressor_input:
  draft_message: string
  locked_elements:
    action_class: string
    approved_claims:
      - string
    single_ask: string | null
    commitment_boundaries:
      - string
    required_caveats:
      - string
  style_goal:
    sound_more_human: boolean
    compress_if_possible: boolean
    preserve_meaning: boolean
  channel: email | slack | sms | linkedin | chat | formal_letter
           | memo | ticket_comment | crm_note
```

This is enough to operate. The skill uses safe defaults for voice profile when none is provided.

### Full Input Contract

```yaml
humanizer_compressor_input:
  version: "1.0"

  draft_message: string

  locked_elements:
    action_class: string
    approved_claims:
      - claim_id: string
        text: string
        epistemic_status: verified | inferred | assumed | disputed | unknown
        certainty_floor: exact | bounded | tentative
    single_ask:
      text: string | null
      required: boolean
    commitment_boundaries:
      - type: promise | timeline | deliverable | availability | escalation_scope
        value: string
    required_caveats:
      - caveat_id: string
        text: string
        must_preserve: boolean
    forbidden_changes:
      - no_new_asks
      - no_certainty_upgrade
      - no_commitment_upgrade
      - no_caveat_removal
      - no_action_class_change

  style_goal:
    sound_more_human: boolean
    compress_if_possible: boolean
    preserve_meaning: boolean
    target_register: formal | neutral | casual | sender_native
    compression_aggressiveness: none | low | medium | high

  sender_profile:
    available: boolean
    source_quality: none | weak | moderate | strong
    profile:
      directness: low | medium | high
      warmth: low | medium | high
      formality: low | medium | high
      verbosity: low | medium | high
      sentence_variance: low | medium | high
      idiom_tolerance: low | medium | high
      hedge_tendency: low | medium | high
      fragment_tolerance: low | medium | high
      signature_patterns:
        - string
      anti_patterns:
        - string

  sender_samples:
    - text: string
      channel: string
      recency: recent | old
      quality: low | medium | high

  channel_context:
    channel: email | slack | sms | linkedin | chat | formal_letter
             | memo | ticket_comment | crm_note
    audience_relationship: internal_peer | manager | client | prospect
                           | friend | mixed
    urgency: low | medium | high
    stakes: low | medium | high

  diagnostics_requested: boolean
```

### Input from GEN-SE

When post-processing GEN-SE output, the locked_elements include an additional `persuasion_structure` block:

```yaml
locked_elements_gense_extension:
  persuasion_structure:
    grrips_stage: string
    tension_level: low | medium | high
    objection_handling_present: boolean
    cta_type: soft | direct | close
```

GEN-SE output should use low-to-medium compression aggressiveness unless explicitly configured otherwise. Persuasion structure is load-bearing in sales messages and must be preserved.

## Process

### Step 1: Parse Input and Build Protected Map

Extract all locked elements and build a protected span map against the draft:

```yaml
protected_span_map:
  claim_spans: []    # text regions containing approved claims
  ask_span: []       # text region containing the single ask
  caveat_spans: []   # text regions containing required caveats
  commitment_spans: [] # text regions containing commitment boundaries
```

Identify which sentences or phrases in the draft correspond to each locked element. These spans are the constraint boundary for all downstream editing.

**Unmappable locked element rule:** If any locked element cannot be located in the draft, return the original draft unchanged. Log the failure with the specific element that could not be mapped. Do not attempt to edit a draft where the constraint boundary is blind. "Proceed with caution" is not a constraint. Either the protected map is complete or the skill does not run.

### Step 2: Profile the Draft

Measure the current draft across voice dimensions:

| Dimension | Question |
|---|---|
| directness | Does the draft get to the point fast or circle in? |
| warmth | How much relational cushioning is present? |
| formality | How polished vs. conversational is the wording? |
| cadence | Short clipped lines or smoother developed sentences? |
| sentence_length_variance | Uniform sentence size or mixed rhythm? |
| lexical_density | Plain words or more abstract vocabulary? |
| hedge_tendency | How often does the draft soften certainty? |
| fragment_tolerance | Are fragments present or is everything complete? |
| transition_style | Explicit transitions or abrupt progression? |
| paragraph_density | Compact blocks or more air between ideas? |

This profile becomes the "current state" to compare against the target.

### Step 3: Estimate Target Voice

**If sender_profile is available:** Use it directly. The profile dimensions map to the same voice dimensions.

**If sender_samples are available but no profile:** Infer a profile from samples. Prefer recent over old. Prefer same-channel samples over cross-channel. Mark voice_match_confidence as medium at best.

**If neither is available:** Use channel-native defaults:

| Channel | Directness | Warmth | Formality | Verbosity |
|---|---|---|---|---|
| email | medium | medium | medium | medium |
| slack | high | medium | low | low |
| sms | high | medium | low | low |
| linkedin | medium | medium | medium | medium |
| formal_letter | medium | low | high | medium |
| ticket_comment | high | low | medium | low |

### Step 4: Identify Mismatch

Compare draft profile against target voice. Flag dimensions where the gap is significant enough to warrant adjustment.

Common mismatches:
- Email to peer is too formal
- Slack note is too complete and polished
- Escalation message got softened too much in message-os's tone pass
- Client message is too clipped for external delivery
- Draft has uniform sentence rhythm where sender naturally varies

**Skip threshold:** If fewer than 2 voice dimensions differ by more than one level between draft profile and target voice, and compression is not requested, and no AI-pattern residue is detected, the skill should return the original draft unchanged. Not every draft needs polish. Unnecessary transformation adds risk without value.

**Language scope:** This skill is designed for English-language drafts. Multi-language or code-switched text requires different voice baselines, fragment tolerance norms, and AI-pattern detection that are not covered in this version. If the draft is not primarily English, return it unchanged.

### Step 5: Generate Candidate Edits

Apply edits targeting identified mismatches. Edits fall into three categories:

**Voice adjustments (allowed):**
- Shorten or merge sentences
- Swap wording for more natural equivalents
- Vary paragraph shape
- Reduce transition smoothness
- Introduce controlled fragments where channel tolerates them
- Reduce over-explanation
- Add minor channel-native connectors ("just," "quick note," "one thing") only when they do not alter certainty or ask structure

**Compression adjustments (when requested):**
- Remove redundant framing
- Collapse repeated qualifiers
- Replace multi-clause phrasing with simpler equivalents
- Merge sentences with identical subject/object
- Delete throat-clearing openers ("I wanted to reach out and...")
- Convert explicit transitions into implicit flow
- Shorten signoffs where channel permits
- Remove duplicate context restatement
- Remove explanatory text that does not change the action outcome

**Not allowed (ever):**
- Adding new content, asks, or claims
- Changing protected claims to broader or stronger versions
- Adding emotional framing that shifts meaning
- Softening or intensifying commitments
- Removing required caveats
- Altering the action class behavior
- Copying rare phrases from sender samples
- Introducing intentional typos or artificial messiness

### Step 6: Remediate Subtle AI Patterns

After voice and compression edits, scan for subtle AI-pattern residue that message-os's gate may have missed:

| Pattern | Detection | Remediation |
|---|---|---|
| Repeated sentence template across paragraph openings | First words of consecutive paragraphs follow same structure | Vary sentence openings |
| Every paragraph same size | All paragraphs within 1-2 sentences of each other | Allow one shorter, one longer |
| Mechanically smooth transitions | Every paragraph linked by explicit connector | Remove unnecessary transitions, let flow be implicit |
| Zero fragments in fragment-tolerant channels | Every sentence is grammatically complete in Slack/SMS | Allow one controlled fragment where natural |
| Overuse of balanced contrast framing | Multiple "X, but Y" or "while X, Y" constructions | Break some into separate sentences |
| Excessive topic restatement | Same point paraphrased across multiple sentences | Cut the weaker restatement |
| Uniform confidence tone | Every sentence at the same certainty register | Let certainty flex by sentence function (context vs. claim vs. ask) |
| Sterile closure lines | "Please let me know if you have any questions" | Replace with channel-native close or omit |

Do not over-correct. The goal is natural prose, not deliberately rough prose. If the draft reads well as-is, leave it.

### Step 7: Verify Locked Elements

After generating the candidate output, mechanically verify every locked element:

**Action class preserved:** Does the final message still perform the same abstract act? A REQUEST must still request. An ESCALATE must still escalate. A DEFER must still defer.

**Approved claims preserved:** Extract each approved claim from the candidate. Compare semantically. Each must be equivalent or narrower (more conservative). Never broader or stronger.

**Single ask preserved:** Count asks in the candidate. Must match the original count (0 or 1). No compound asks. No implied second ask added in the closing line.

**Commitment boundaries preserved:** No new promises. No stronger timeline. No widened ownership. No implied availability that was not in the original.

**Required caveats preserved:** Each caveat must be present and materially intact. "I believe" cannot become "I know." "Based on current information" cannot be dropped.

**For GEN-SE output:** Additionally verify persuasion structure with mechanical checks:

1. **GRRIPS stage intent:** Identify which GRRIPS node (G, R, R, I, P, S) carries the primary weight in the draft. Verify the candidate preserves that node's content and position. If the draft leads with a recognition node (R1), the candidate must still lead with recognition.
2. **Tension level:** If the original draft uses direct language to create urgency or consequence framing, the candidate must preserve that directness. Compression cannot soften tension. If tension_level is medium or high, do not add warmth padding.
3. **Objection handling:** If the draft contains a sentence that addresses a buyer concern or reframes a resistance point, that sentence is a protected span. It may be compressed but not removed or reframed.
4. **CTA type:** If the CTA is "direct" (asking for a meeting, commitment, or next step), the candidate cannot soften it to "soft" (suggesting rather than asking). The ask verb and specificity must survive.

If any locked element fails verification: revert that specific edit. If reverting breaks coherence, return the original draft unchanged and note the conflict in the transformation log.

### Step 8: Verify Meaning Preservation

Do not rely on holistic semantic judgment. Run mechanical checks against specific linguistic features:

**For each approved claim, verify:**
1. **No noun dropped or generalized.** If the original says "Revenue grew 12% in Q3," the candidate must retain "12%" and "Q3." "Revenue grew significantly" is a failure.
2. **No number, date, or time reference dropped.** Specific quantities, dates, and deadlines must survive compression.
3. **No conditional removed or weakened.** "If we receive approval by 3 PM" cannot become "once we receive approval." The conditional structure and any time-bound must persist.
4. **No hedging language removed.** "I believe," "based on current information," "it appears that" are epistemic markers. Equivalent substitutions are allowed ("I think" for "I believe"). Deletion is not.
5. **No scope broadened.** "Two fields are incomplete" cannot become "the spreadsheet has issues." The specific scope must survive.

**For the single ask, verify:**
1. Ask count unchanged (0 or 1)
2. The core request is the same (asking for the same thing, of the same person)
3. No implied second ask added in closing

**For commitment boundaries, verify:**
1. No new promise verb introduced ("will," "guarantee," "commit to" where original had "can," "may," "hope to")
2. No timeline tightened ("by end of week" cannot become "by Wednesday" unless that is what end of week means)
3. No ownership expanded ("I can look into it" cannot become "I'll handle it")

**For required caveats, verify:**
1. Each caveat text is present in the candidate
2. Equivalent substitutions are acceptable ("I think" for "I believe") but deletion is not

**Decision rule:** The candidate may be slightly more conservative than the original (narrower claims, softer promises) but never broader, stronger, or more committal.

If any check fails, revert that specific change. If reverting breaks coherence, return the original draft unchanged and log the failure.

### Step 9: Check Channel Fit

Verify the candidate matches channel expectations:
- Email: appropriate structure, greeting/signoff if expected, ask near end
- Slack: concise, no ceremonial greeting unless warranted, first line does the work
- SMS/chat: ultra-concise, no heavy structure
- Formal letter: appropriate ceremony, verified claims only
- Ticket/CRM: compact, factual, timestamp-friendly

If channel fit degraded from the original (e.g., compression made an email feel like a text message), adjust.

### Step 10: Emit Final Output

If all verification passes: emit the candidate as final_message.

If any verification fails and cannot be repaired: return the original draft unchanged with a note explaining why the transformation was not applied.

Maximum revision cycles: 2. If the candidate still fails verification after two revisions, return the original.

## Output Contract

### Full Output

```yaml
humanizer_compressor_output:
  version: "1.1"

  final_message: string

  compliance_report:
    action_class_preserved: boolean
    approved_claims_preserved: boolean
    single_ask_preserved: boolean
    commitment_boundaries_preserved: boolean
    required_caveats_preserved: boolean
    persuasion_structure_preserved: boolean | null  # null when not GEN-SE input

  transformation_log:
    voice_adjustments:
      - type: lexical_shift | cadence_shift | register_shift
              | paragraph_shift | fragment_introduction
        description: string
    compression_adjustments:
      - type: redundancy_removed | sentence_merged | opener_trimmed
              | qualifier_collapsed | transition_removed | signoff_shortened
        description: string
    ai_pattern_adjustments:
      - type: opening_varied | paragraph_resized | transition_trimmed
              | fragment_added | contrast_broken | restatement_cut
              | confidence_varied | closure_replaced
        description: string
    blocked_adjustments:
      - desired_change: string
        blocked_by: locked_element | channel_constraint | meaning_preservation

  metrics:
    input_word_count: integer
    output_word_count: integer
    compression_ratio: float  # output / input
    voice_match_confidence: low | medium | high
    channel_fit_confidence: low | medium | high

  warnings:
    - string
```

### Minimal Output

When diagnostics are not requested:

```yaml
humanizer_compressor_output:
  final_message: string
  compliance_report:
    all_locked_elements_preserved: boolean
```

## Relationship to message-os

**message-os owns:**
- Action class realization
- Structural correctness
- Channel template selection
- Approved claim selection and epistemic framing
- Ask count enforcement
- Caveat inclusion
- Commitment boundary enforcement
- AI-Pattern Gate (banned vocabulary and gross structural tells)
- Initial draft generation

**humanizer-compressor owns:**
- Voice alignment
- Naturalness tuning
- Wording compression
- Subtle AI-pattern cleanup
- Cadence and paragraph shape adjustments
- Channel-native register polish within locked bounds

**Bright-line rule:** If a change would alter what the message is doing, message-os owns it. If a change only alters how the same message sounds, humanizer-compressor owns it.

message-os output should be sendable as-is. humanizer-compressor is a quality-of-life upgrade, not a required step.

## Relationship to GEN-SE

humanizer-compressor can post-process GEN-SE output with stricter rules.

GEN-SE composes sales messages through a domain-specific engine (GRRIPS compiler, claims gate, drift check). humanizer-compressor can help with:
- Reducing robotic sales cadence
- Matching rep voice
- Trimming over-explanation
- Removing generic AI polish

**What changes for GEN-SE output:**

Sales copy is more sensitive because persuasion structure is load-bearing. The compressor must additionally preserve:
- GRRIPS stage intent
- Objection sequencing
- CTA singularity
- Calibrated tension level
- Offer framing boundaries

Use low-to-medium compression aggressiveness on GEN-SE output unless explicitly configured otherwise.

**When to use which:**
- message-os output: humanizer-compressor is the standard post-processor
- GEN-SE output: humanizer-compressor is optional and should be conservative
- GEN-SE output that will go through human review: humanizer-compressor may be skipped entirely

## Failure Modes

### 1. Caveat Loss
Compression deletes a necessary qualifier or limitation.
**Detection:** Required caveat missing from candidate protected map.
**Fix:** Restore caveat verbatim or near-verbatim.

### 2. Certainty Inflation
"I think" becomes "I know." Tentative language becomes declarative.
**Detection:** Certainty comparison shows candidate stronger than source.
**Fix:** Revert to same or lower certainty wording.

### 3. Commitment Drift
"I can take a look" becomes "I'll handle it today."
**Detection:** Commitment boundary parser flags stronger promise.
**Fix:** Revert promise language.

### 4. Ask Multiplication
One request becomes two through closing additions ("Let me know if you have questions" added after a different ask).
**Detection:** Ask counter > 1 when original had 1.
**Fix:** Remove the added ask.

### 5. Overcompression
Message becomes abrupt, ambiguous, or socially off. High word reduction plus loss in channel-fit score.
**Detection:** Channel-fit confidence drops from original.
**Fix:** Restore minimum framing. Compress less aggressively.

### 6. Voice Caricature
Output sounds like an exaggerated imitation of the sender. Excessive use of copied lexical quirks or sample phrases.
**Detection:** Multiple rare phrases from sender samples appear in output.
**Fix:** Back off to pattern-level matching only. Remove copied phrases.

### 7. Formality Mismatch
Slack output still sounds email-like, or executive email gets over-casual.
**Detection:** Channel-fit model mismatch.
**Fix:** Recalibrate register to channel defaults.

### 8. Softening of Hard Boundary
Escalation or refusal gets humanized into ambiguity. "I cannot approve this" becomes "I'm not sure this is the right move."
**Detection:** Action class verification fails. Polarity check on boundary language weakened.
**Fix:** Preserve exact boundary sentence. Do not humanize hard edges.

### 9. Tone Flattening
All sentences carry the same social weight. Uniform rhythm, uniform certainty display.
**Detection:** Low variance in sentence function and rhythm.
**Fix:** Introduce controlled cadence variation. Let one sentence be short, another developed.

### 10. Residual AI Smoothness
Prose is technically fine but too frictionless. Repeated transitions, uniform paragraphing, balanced clause overuse.
**Detection:** Pattern scan for uniform paragraph size, excessive connectors, repeated "X, but Y" structures.
**Fix:** Trim transitions, vary sentence openings, allow asymmetry.

### 11. Hidden Semantic Broadening
Compressed wording generalizes a specific claim. "Revenue grew 12% in Q3" becomes "Revenue grew significantly."
**Detection:** Claim comparison shows broader scope.
**Fix:** Restore specific noun, time, or condition.

### 12. Diagnostic Opacity
Changed text cannot be audited. No changelog, no protected map comparison.
**Detection:** Transformation log is empty or absent.
**Fix:** Require transformation log when diagnostics_requested is true. In minimal mode, at minimum confirm all locked elements preserved.

## Calibration Notes

### Compression Thresholds by Channel

| Channel | Recommended Aggressiveness |
|---|---|
| email | low to medium |
| slack | medium |
| sms | medium to high |
| linkedin | low to medium |
| formal_letter | none to low |
| escalation / legal | none to low |
| ticket_comment | medium |
| crm_note | medium |

### Voice Profile Bootstrapping

**Sample count to confidence mapping:**

| Samples Available | Conditions | voice_match_confidence | Matching Scope |
|---|---|---|---|
| 0 | No profile, no samples | low | Channel-native defaults only. Pattern matching disabled. |
| 1 | Any single sample | low | Stable dimensions only (directness, warmth, formality). No lexical mimicry. |
| 2-3 | Same channel, recent | medium | Stable dimensions + cadence + paragraph density. Light pattern matching. |
| 2-3 | Mixed channel or old | low | Stable dimensions only. Cross-channel samples degrade reliability. |
| 4+ | Same channel, recent, consistent | high | Full voice profile. Pattern matching active. |
| 4+ | Inconsistent across samples | medium | Stable dimensions + conservative midpoint on conflicting dimensions. |

With limited samples:
- Infer only stable dimensions (directness, warmth, formality)
- Avoid lexical mimicry
- Prefer channel-native defaults over weak inferences
- Never claim high confidence from fewer than 4 consistent same-channel samples

### Conflicting Voice Signals

When samples disagree:
1. Prefer recent over old
2. Prefer same-channel over different-channel
3. Prefer high-quality authored text over rushed fragments
4. Collapse to conservative midpoint if still unresolved

### Priority Order

```yaml
priority_order:
  1: locked_elements
  2: preserve_meaning
  3: channel_fit
  4: sender_voice_match
  5: compression
```

This is absolute. When any lower priority conflicts with a higher one, the higher priority wins.

## Example Transformations

### Example 1: Professional Email, Correct but Robotic

**Input draft:**
```
Hi Sarah,

I wanted to follow up regarding the timeline for the revised deck. Based on
the current status, I believe I can send an updated version by Thursday
afternoon. Please let me know if that timing still works for you.

Best,
David
```

**Locked elements:**
- action_class: RESPOND
- approved_claims: "I believe I can send an updated version by Thursday afternoon"
- single_ask: "Please let me know if that timing still works for you"
- commitment_boundaries: "by Thursday afternoon"
- required_caveats: "I believe"

**Process:** Remove throat-clearing opener. Tighten follow-up framing. Keep tentative commitment language. Make cadence less template-like.

**Output:**
```
Hi Sarah,

Following up on the revised deck. I think I can get you the updated version
by Thursday afternoon. Let me know if that timing still works.

Best,
David
```

**Changelog:**
- opener_trimmed: "I wanted to follow up regarding" to "Following up on"
- lexical_shift: "I believe" to "I think" (same certainty band, more natural)
- compression: removed excess wording without changing ask
- compliance: all locked elements preserved

### Example 2: Slack Message Too Formal

**Input draft:**
```
Hi team, I wanted to let you know that I reviewed the spreadsheet and there
are two fields that still appear to be incomplete. Please update those when
you have a chance.
```

**Locked elements:**
- action_class: REQUEST_CLARIFICATION
- approved_claims: "there are two fields that still appear to be incomplete"
- single_ask: "Please update those when you have a chance"
- required_caveats: "still appear to be"

**Process:** Remove email-style opener. Casualize to Slack-native register. Preserve tentativeness. Compress.

**Output:**
```
Reviewed the sheet. Two fields still look incomplete. Update those when you can.
```

**Changelog:**
- register_shift: formal to slack-native
- compression: removed greeting and filler
- certainty_preserved: "still appear to be" to "still look" (equivalent tentativeness)
- compliance: all locked elements preserved

### Example 3: Escalation Where Polish Must Not Soften

**Input draft:**
```
Hi Mark,

I am escalating this because we still do not have the signed approval, and
I cannot move this forward without it. If we do not receive approval by
3 PM today, the launch will need to move.

Thanks,
David
```

**Locked elements:**
- action_class: ESCALATE
- approved_claims: "we still do not have the signed approval," "I cannot move this forward without it," "If we do not receive approval by 3 PM today, the launch will need to move"
- commitment_boundaries: "cannot move this forward without it," "by 3 PM today"

**Process:** Very light polish only. Preserve hard edge. Do not add warmth that weakens escalation.

**Output:**
```
Hi Mark,

Escalating this because we still do not have signed approval, and I can't
move it forward without that. If approval does not come in by 3 PM today,
the launch will need to move.

Thanks,
David
```

**Changelog:**
- compression: "the signed approval" to "signed approval"
- cadence_shift: "cannot" to "can't" (meaning unchanged, channel tolerates contraction)
- blocked: "add softer relational framing" blocked by action_class (ESCALATE)
- compliance: all locked elements preserved

### Example 4: Known Sender Voice (Direct, Low-Warmth, Minimal)

**Sender profile:**
```yaml
directness: high
warmth: low
formality: medium
verbosity: low
fragment_tolerance: medium
signature_patterns: ["gets to point quickly", "avoids extra cushioning"]
anti_patterns: ["long setup", "overly polished transitions"]
```

**Input draft:**
```
Hi James,

I wanted to reach out and ask whether you would be available for a
20-minute call sometime next week to review the current implementation
and identify any blockers that may exist.

Best,
David
```

**Locked elements:**
- action_class: REQUEST_CLARIFICATION
- approved_claims: "review the current implementation," "identify any blockers that may exist"
- single_ask: "whether you would be available for a 20-minute call sometime next week"
- commitment_boundaries: "20-minute call," "next week"

**Process:** Strip politeness padding to match high-directness profile. Reduce clause nesting. Keep neutral professionalism. Maintain single ask.

**Output:**
```
Hi James,

Are you available for a 20-minute call next week to review the current
implementation and identify any blockers?

Best,
David
```

**Changelog:**
- compression: removed throat-clearing opener
- voice_match: increased directness, reduced warmth padding (matches sender profile)
- syntax_simplification: collapsed nested clause
- voice_match_confidence: high
- compliance: all locked elements preserved

## Anti-Patterns Summary

| Anti-Pattern | What It Looks Like | Why It Breaks |
|---|---|---|
| Caveat deletion | "I think" disappears in compression | Upstream epistemic safety violated |
| Certainty upgrade | "It appears" becomes "It is" | Epistemic inflation, constraint violation |
| Commitment creep | "I can look into this" becomes "I'll have it done by Friday" | Unauthorized promise |
| Ask injection | Closing line adds "Let me know your thoughts" to a LOG message | Action class violation |
| Voice caricature | Output uses three rare phrases from sender samples | Sounds performative, not natural |
| Boundary softening | "I cannot approve" becomes "I'm not sure about this" | Escalation or refusal weakened |
| Over-smoothing | Every paragraph starts with a transition, every sentence is balanced | Still sounds AI-generated |
| Channel mismatch | Email structure in Slack, casual tone in legal escalation | Wrong register for context |
