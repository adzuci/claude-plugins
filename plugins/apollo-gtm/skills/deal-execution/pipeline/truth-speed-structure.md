---
name: truth-speed-structure
description: >
  L1 response shaping meta-skill that determines the correct form, pace, and
  epistemic register of output before any message is composed. Operates on the
  structured state and constraint map produced by upstream layers and selects
  one of four output modes: DIRECT, CAVEAT-FIRST, STRUCTURED-ANALYSIS, or
  ESCALATE-TO-HUMAN. Prevents the pipeline from composing confidently when
  grounding is weak, composing slowly when the answer is clear, or structuring
  elaborately when speed is the correct move. Sits between constraint-first-
  reasoner (L2B) and bounded-action-router (L3) as a shaping pass, or runs
  standalone as a triage gate. Load when you need to decide not just what to
  say but what form the response should take — and how fast.
metadata:
  author: David Johnson-Hall
  version: '2.1'
  layer: 2b-3-shaping-pass
  architecture: Apollo GTM Skill Library
  depends_on:
    - jhd-foundation
  optional_upstream:
    - reality-filter
    - state-extractor
    - constraint-first-reasoner
  downstream_consumers:
    - bounded-action-router
    - message-os
    - humanizer-compressor
---

# Truth Speed Structure

L1 response shaping meta-skill. Determines the correct **form**, **pace**, and **epistemic register** of output before any downstream layer composes content.

This skill does not write messages. It does not select action classes. It shapes the conditions under which composition is allowed to happen — and in what mode.

---

## The Principle

**Truth → Speed → Structure.**

The operator north star. The sequence that governs all output in the JHD pipeline.

1. **Truth first.** Is the grounding sufficient to make a claim, take an action, or compose a response? If not, the response must reflect that. It cannot assert more than the evidence supports. This is the validity filter. *"Separate verified facts from inferences and guesses, and state uncertainty plainly. Do not present speculation as fact."*

2. **Speed second.** Given what is true and what is constrained, what is the fastest correct move? Speed is not recklessness. It is low-latency delivery of the most decision-useful thing. Move once the constraint landscape is clear — not before, not after. *"Prioritize actionable analysis, leverage, tradeoffs, and next steps over reassurance or generic advice."*

3. **Structure third.** Structure is decision architecture, not presentation polish. It exists to make thought traceable and action easier — not to signal effort or intelligence. **Hidden structure, compressed surface.** The reasoning is ordered underneath. The visible output is as compressed as the situation allows. *"Write like a sharp human operator: calm, concise, specific, and natural. Avoid fluff, hype, corporate filler, and AI-sounding phrasing. Prefer clear over clever."*

Most AI systems invert this: structure first (formatting as performance), assert speed (verbose output pretending to be efficient), truth as decorative (hedges at the end of confident-sounding claims). This skill reverses that.

**The shortest faithful read: map reality honestly, move without drag, and show the reasoning only at the level needed to make the next correct move.**

---

## Purpose

Three failure modes this skill exists to prevent:

**Epistemic overreach.** The pipeline composes confidently on weak grounding. Output sounds authoritative about things it cannot actually know. Truth is not decorative.

**Speed miscalibration.** The pipeline elaborates when the answer is clear, or compresses when depth is required. "Too long before getting to the point" is a failure. So is compression that loses a load-bearing distinction.

**Structure mismatch.** Format, register, and scaffolding don't match actual complexity and urgency. Structure as intelligence-signaling is a failure.

truth-speed-structure resolves all three by making output mode an explicit, governed decision — not an implicit, stylistic one.

---

## When to Use This Skill

**Standalone use (triage gate):**
Run on raw input when a pipeline hasn't been engaged. You're working without upstream validation — bias harder toward CAVEAT-FIRST and apply conservative defaults throughout. The confidence in mode selection is lower than in pipeline mode. State this in the output.

**Pipeline use (shaping pass between L2B and L3):**
Run after constraint-first-reasoner has produced a constraint map. Mode selection confidence is high because epistemic state and constraints are structured. The directive locks before bounded-action-router runs.

The selection logic is the same in both contexts. The confidence in that selection is not.

---

## Pipeline Position

```
raw input
  --> reality-filter (L1): what is true
  --> state-extractor (L2A): structured state
  --> constraint-first-reasoner (L2B): constraint map
  --> [truth-speed-structure]: output mode selected   ← THIS SKILL
  --> bounded-action-router (L3): action class selected
  --> message-os / GEN-SE (L4): message composed
  --> humanizer-compressor (L4+): voice polish
  --> output
```

Shaping pass, not a full pipeline layer. Can also run standalone as triage gate before pipeline engagement.

---

## Output Modes

Four modes. Exactly one is selected. No blending.

### DIRECT

**When:** Grounding is strong, the answer is clear, constraints allow assertion, speed is appropriate.

**Characteristics:**
- No preamble
- Answer first
- Short unless depth is genuinely required by the content
- Preferred form: one tight paragraph, or the answer followed only by what's needed to act on it
- Caveats only when they change the decision — not as ritual, not as performance

**Suppressed:** Elaboration for appearance of thoroughness. Qualifications not grounded in actual uncertainty. Scaffolding the reader doesn't need. Generic enthusiasm. Decorative alternatives instead of a judgment.

**Bad-news flag:** When grounding is strong and constraints are low but the correct answer is unwelcome, DIRECT is still the correct mode. Set `bad_news: true` in the routing directive. message-os uses this to apply appropriate framing without softening the substance. This is not a mode change — it is a composition flag.

---

### CAVEAT-FIRST

**When:** Grounding is mixed, key claims are asserted or assumed, or action is high-stakes relative to epistemic certainty.

**Characteristics:**
- Lead with the uncertainty or constraint, not the answer
- State what is known and what is not before making any recommendation
- One clean caveat, then proceed. Not ten.
- Hedges are structural — they mark where evidence runs out

**Suppressed:** Leading with the answer before disclosing uncertainty. Burying caveats at the end of confident framing. Treating assumed claims as verified ones. Timid output that labels everything uncertain and commits to nothing.

**The hard rule:** A caveat is real or it isn't. A caveat that does not change the action or truth status of a central claim does not belong. A caveat that does change it is mandatory.

---

### STRUCTURED-ANALYSIS

**When:** The situation is complex, multi-actor, temporally extended, or constraint-dense — and the operator needs to see the reasoning, not just the conclusion.

**Characteristics:**
- Claims separated from inferences separated from recommendations
- Constraints surfaced before recommendations
- Typical order: state → constraints → options → recommendation → next steps
- Structure in visible output permitted and expected — but only as much as the situation requires
- Appropriate for: call debrief, contract review, strategic decision, GTM architecture, offer evaluation, escalation package

**Suppressed:** Premature conclusions. Blending analysis with recommendation without separation. Over-scaffolded output that shows too much skeleton and not enough answer. Structure as performance when the situation is simple.

**Key distinction from DIRECT:** STRUCTURED-ANALYSIS makes the reasoning visible. DIRECT delivers the conclusion. The operator's situation determines which — not the AI's preference for appearing thorough.

---

### ESCALATE-TO-HUMAN

**When:** The pipeline cannot safely proceed — grounding is too weak, authority boundary is hit, or the risk of composing output exceeds the risk of pausing.

**Characteristics:**
- Output is a structured handoff, not a message
- States what is known, what is not, and why the system cannot proceed safely
- Recommends specific human action
- Does not produce a draft that looks like a response

**Suppressed:** Composing output anyway under the guise of "a draft to review." Treating ESCALATE-TO-HUMAN as a polite CAVEAT-FIRST. Any content that could be mistaken for a usable response.

**Reserve for:** Hard blocks that eliminate all action classes. Not for any constraint being present.

---

## Selection Process

Four steps. Compress, gate, select, calibrate.

### Step 1: Assess Inputs

Read whatever upstream state is available. Produce three assessments:

**Epistemic floor** — the weakest-grounded claim the action depends on most heavily.

| If reality-filter ran | Use `truth_status` tags |
| If state-extractor ran without reality-filter | Use `epistemic_status` tags |
| Neither ran (standalone) | Apply conservative defaults; treat unknown as assumed |

```
epistemic_floor: strong | mixed | weak | unknown
  strong  = central claims are verified or probable
  mixed   = central claims include asserted or inferred
  weak    = central claims include assumed or disputed
  unknown = standalone mode, no upstream validation
```

**Constraint density** — read the L2B constraint map if available; infer from situation if not.

```
constraint_density: low | medium | high | blocking
  low      = 0-1 constraints, no hard blocks
  medium   = 2-3 constraints, no hard blocks
  high     = 4+ constraints, no hard blocks
  blocking = any hard_block present, or authority_boundary eliminates all action classes
```

**Operator calibration** — read any available signal about how this operator works.

```
operator_calibration:
  domain_context: legal | sales | executive | ops | personal | system-design | unknown
  operator_mode:  action | analysis | triage | draft | unknown
  speed_signal:   high | normal | low | unknown
  known_defaults: []   # e.g. "prefers DIRECT in ops", "wants STRUCTURED-ANALYSIS for GTM"
```

Note operator calibration in the output directive. A mode that is technically correct but wrong for how this operator works is still a failure.

---

### Step 2: Escalation Gate

Check before any mode selection. If any condition is met, select ESCALATE-TO-HUMAN and skip Steps 3-4.

**Escalate if:**
- A fabricated or contradicted claim is a central decision dependency
- `constraint_density = blocking` AND the blocking constraint eliminates all action classes
- Authority boundary is present AND operator cannot resolve it
- Composing output creates liability or deception risk regardless of how it's framed

**If none of the above:** proceed to Step 3.

> Note on the decision table: `constraint_density = blocking` is caught here at the gate, before the table is reached. The table in Step 3 does not include a blocking row — it would be dead. If you see a situation where blocking constraints don't trigger escalation, the gap is here at Step 2, not in the table.

---

### Step 3: Mode Selection

Apply the decision table. Standalone mode adds one rule: when epistemic floor is unknown, treat it as weak.

| Epistemic Floor | Speed Signal | Constraint Density | Selected Mode |
|---|---|---|---|
| Strong | High | Low | DIRECT |
| Strong | High | Medium | DIRECT (note constraints inline) |
| Strong | Normal / Low | High | STRUCTURED-ANALYSIS |
| Mixed | Any | Any | CAVEAT-FIRST |
| Weak | Any | Low / Medium | CAVEAT-FIRST |
| Weak | Any | High | STRUCTURED-ANALYSIS |
| Unknown (standalone) | Any | Any | CAVEAT-FIRST |

**Ambiguity rule:** When the table is genuinely ambiguous between DIRECT and CAVEAT-FIRST, default to CAVEAT-FIRST. Conservative about commitment.

**Bad-news check:** After mode selection, assess whether the answer is unwelcome regardless of grounding strength. If yes, set `bad_news: true`. This is a composition flag for message-os — it does not change the mode.

**Operator calibration check:** After mode selection, check against known operator defaults. If the selected mode conflicts with a known operator preference, note the conflict in the output directive. Do not silently override — surface the tension and let the operator resolve it.

**Weak floor + STRUCTURED-ANALYSIS contract check:** If `epistemic_floor = weak` and `selected_mode = STRUCTURED-ANALYSIS`, `claims_to_caveat` must be non-empty before the routing directive is emitted. If it is empty, the directive is malformed — either populate it from the central claims identified in Step 1, or downgrade the mode to CAVEAT-FIRST. Do not emit a STRUCTURED-ANALYSIS directive on weak grounding without explicit caveat targets. Trusting downstream discipline on this is not sufficient.

---

### Step 4: Calibrate Format

Set the structural format for the selected mode. Style signals (voice, register, warmth) are not set here — they belong in message-os and humanizer-compressor.

| Mode | Format | Lead Element | Length Signal | Scaffolding |
|---|---|---|---|---|
| DIRECT | Prose | Answer | Tight | No |
| CAVEAT-FIRST | Prose | Caveat | Normal | Minimal |
| STRUCTURED-ANALYSIS | Sections | State summary | Extended | Yes |
| ESCALATE-TO-HUMAN | Handoff block | Handoff statement | Normal | Required |

Domain defaults for format calibration only (not style):

| Domain | Default Speed Signal | Default Mode if Uncertain |
|---|---|---|
| Legal / contractual | Low | CAVEAT-FIRST |
| Sales / B2B | High | DIRECT or CAVEAT-FIRST |
| Executive comms | Normal | CAVEAT-FIRST |
| Operations / execution | High | DIRECT |
| Personal / family | Normal | CAVEAT-FIRST |
| System design / analysis | Low | STRUCTURED-ANALYSIS |

Style signals for each domain belong in message-os and humanizer-compressor — not here.

---

## Output Contract

Split into two blocks. Downstream consumers (L3, L4) read the routing directive. The audit block is optional — used for traceability when reviewing pipeline decisions.

### Routing Directive (required)

What bounded-action-router, message-os, and humanizer-compressor actually consume.

```yaml
routing_directive:
  selected_mode: null           # DIRECT | CAVEAT-FIRST | STRUCTURED-ANALYSIS | ESCALATE-TO-HUMAN
  mode_confidence: null         # high (pipeline) | medium | low (standalone)
  format: null                  # prose | sections | handoff-block
  lead_element: null            # answer | caveat | state-summary | handoff-statement
  length_signal: null           # tight | normal | extended
  scaffolding_permitted: false
  bad_news: false               # true = correct answer is unwelcome; message-os applies framing
  constraints_to_surface: []    # constraints that MUST appear in output
  claims_to_caveat: []          # claims that MUST be hedged
  assertions_blocked: []        # claims that CANNOT be asserted regardless of phrasing
  operator_calibration_conflict: null  # null = no conflict; string = describe the tension
  composition_target: message-os        # message-os | gense — which L4 skill composes the output
```

**composition_target selection rules:**

truth-speed-structure emits before bounded-action-router runs. The action class is not yet known at emission time. Selection is therefore based on domain + input_type alone. bounded-action-router overrides this field if the selected action class is incompatible with the preliminary target.

```
# Preliminary selection (truth-speed-structure, based on domain + input_type)
if domain = sales AND input_type = email_thread:
  composition_target = gense   # preliminary; L3 may override
default:
  composition_target = message-os

# L3 override (bounded-action-router, after action class is selected)
if composition_target = gense AND selected_action_class in [ESCALATE, DEFER, NO_ACTION, LOG, CLOSE]:
  composition_target = message-os   # GEN-SE does not handle these action classes
```

The preliminary target ships with the routing directive. bounded-action-router reads it, selects the action class, and applies the override check before passing the final directive to L4. Without this field, the fork between message-os and gense depends on operator memory rather than pipeline state.

**Mode → L3 mapping:**
- DIRECT → bounded-action-router may select RESPOND or EXECUTE without additional gates
- CAVEAT-FIRST → bounded-action-router restricted to RESPOND; EXECUTE blocked
- STRUCTURED-ANALYSIS → bounded-action-router selects RESPOND or LOG with full structure expectation
- ESCALATE-TO-HUMAN → bounded-action-router restricted to ESCALATE or LOG

### Audit Block (optional)

For traceability. Not required for runtime decisions.

```yaml
audit:
  skill: truth-speed-structure
  version: '2.1'
  operating_context: null       # pipeline | standalone
  upstream_layers_run: []
  epistemic_floor: null
  constraint_density: null
  escalation_triggered: false
  escalation_reason: null
  suppressed_modes: []          # modes eliminated and why
  mode_rationale: null          # one sentence
  operator_calibration_applied: null
```

---

## Input Contract

truth-speed-structure accepts input at multiple levels of completeness. Degrades gracefully when upstream layers have not run.

```yaml
input:
  # Required minimum
  situation_description: null       # Raw text or operator description

  # Optional upstream outputs
  reality_filter_output: null       # From L1 reality-filter
  state_extractor_output: null      # From L2A state-extractor
  constraint_map_output: null       # From L2B constraint-first-reasoner

  # Optional operator signals
  operator_mode: null               # action | analysis | triage | draft | unknown
  speed_requirement: null           # high | normal | low | unknown
  stakes: null                      # high | medium | low | unknown
  domain_context: null              # legal | sales | executive | ops | personal | system-design | unknown
  operator_calibration: null        # Known operator defaults, if any
```

**Degradation rules:**
- No upstream layers (standalone): conservative defaults throughout; epistemic floor = unknown; bias toward CAVEAT-FIRST; flag `mode_confidence: low`
- reality-filter only: use truth_status for epistemic floor; infer constraint density from situation
- state-extractor only: use epistemic_status tags; infer constraints from open loops and ambiguities
- All three layers (full pipeline): full mode selection; `mode_confidence: high`

---

## Anti-Patterns

**False DIRECT.** Composing in DIRECT mode when epistemic floor is mixed. Symptoms: no caveats, confident framing, asserted claims treated as verified. Truth is not decorative.

**Performative STRUCTURED-ANALYSIS.** Using STRUCTURED-ANALYSIS when the situation is simple and speed matters. Output that spends too many words before arriving at the leverage point.

**Decorative CAVEAT-FIRST.** A hedge at the top as ritual disclaimer, then asserting as if grounding is strong. The caveat is real or it isn't.

**Uncertainty theater.** Labeling everything uncertain and committing to nothing. Epistemic honesty must be compact. Truth labeling should improve decisions, not become performance art. *"State uncertainty plainly"* — not elaborately.

**Passive epistemic rigor.** Asking clarifying questions or pausing to verify when missing context does not materially change the answer. Default to best-effort execution. Only escalate when uncertainty creates real risk of the wrong action. Epistemic caution is not a substitute for execution.

**AI smell.** Corporate filler, generic enthusiasm, synthetic warmth, flattering nonsense. Blocked in all modes. *"Prefer clear over clever."*

**Premature ESCALATE.** Routing to human review because a constraint is present, not because all action classes are blocked. ESCALATE-TO-HUMAN is not defensive caution. Reserve it for when the system genuinely cannot proceed safely.

**Style signals in mode selection.** Voice, register, warmth calibration do not belong here. They are set in message-os and humanizer-compressor. truth-speed-structure sets mode and format. Downstream layers set style.

---

## Failure Modes

| Failure | Cause | Remedy |
|---|---|---|
| Mode selected but not respected downstream | L4 treats routing_directive as a suggestion | routing_directive is a hard constraint for L3 and L4 |
| DIRECT used for assumed central claim | Epistemic floor assessed too high | Audit weakest central claim before selecting DIRECT |
| STRUCTURED-ANALYSIS when timing is active | Speed signal not read from constraint map | Read timing_window constraints before Step 3 |
| Escalation triggered for non-blocking constraint | Step 2 gate applied too broadly | Gate checks: hard block eliminates ALL action classes, not just some |
| Mode correct but wrong for operator | Operator calibration not applied | Check known_defaults before finalizing; surface conflict if present |
| Style signals set here instead of L4 | Domain defaults column creep | Domain table contains speed and mode defaults only; no voice or register |

---

## Known Gaps (v2.1)

1. **No multi-mode sequencing.** Some situations call for a fast DIRECT acknowledgment followed by a STRUCTURED-ANALYSIS. This skill selects one mode. A future v3 could support a two-phase directive.

2. **No intra-session recalibration.** If the operator pushes back on CAVEAT-FIRST mid-session, the skill does not update. The `operator_calibration_conflict` field surfaces the tension but does not resolve it.

3. **Operator calibration is input-driven, not learned.** Known operator defaults must be passed in as a signal. There is no mechanism for this skill to observe and accumulate operator behavior across sessions.

4. **Decision table not empirically validated.** Built from first principles and operator behavior mining. Should be validated against real pipeline runs before being treated as settled.

5. **Weak floor + STRUCTURED-ANALYSIS: enforcement layer is Step 3, not output contract.** Step 3 already enforces this at runtime — if `epistemic_floor = weak` and `selected_mode = STRUCTURED-ANALYSIS`, `claims_to_caveat` must be non-empty or the mode downgrades to CAVEAT-FIRST. The check currently lives in the selection step. A v2.1 improvement would elevate it to output contract validation: the routing directive itself is rejected as malformed if the constraint is violated, regardless of how Step 3 ran. Stronger enforcement boundary, same rule.

6. **Sub-domain splits not yet defined.** Legal (contract review vs. employment vs. litigation-adjacent) and executive comms (board vs. internal skip-level vs. customer negotiation) may warrant different defaults. Will need sub-domain rows as real use surfaces the distinctions.
