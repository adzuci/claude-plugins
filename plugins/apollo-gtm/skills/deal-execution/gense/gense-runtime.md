# GEN-SE Runtime Reference

Execution-only. For full spec see `gense.md`; for module details see `gense/modules/`.

## Pipeline Sequence

Seven steps, strict order. Never skip. Block at any step → emit Block Output.

| Step | Name | Gate / Key Output |
|------|------|-------------------|
| 1 | **INGEST** | Parse thread into turns with speaker attribution. Gate: `attribution_confidence ≥ 0.70`, `buyer_role_confidence ≥ 0.70`, `parse_status ≠ "blocked"`. Detect auto-replies → set `defer_until`. |
| 2 | **EXTRACT** | Populate ThreadState: open loops, commitments, stakeholders, objection tags, derived fields. Merge with `persisted_state` if provided. |
| 3 | **CLASSIFY** | Set `deal_stage`, `buyer_intent` (canonical enums). Gate: `stage_confidence ≥ 0.60`, `intent_confidence ≥ 0.60`. Multi-intent: ≤0.08 gap → −0.12 penalty, enum order tie-break. |
| 4 | **ROUTE** | Mechanical. HB → PL → preconditions → affinity → select action → channel validation (4.6) → CTA constraint → execution_status. |
| 5 | **GENERATE** | GRRIPS-informed draft. Select variant, compile, apply word limits, ask-block rule, tone calibration, tag claims. |
| 6 | **VALIDATE** | Mechanical. Check every claim source. Strip ungrounded, hedge derived. |
| 7 | **DRIFT CHECK** | Mechanical. 10 flags, max 2 repair attempts, then BLOCK with Action 1. |

## Hard Blocks (HB_001–HB_009)

Evaluate in order. First trigger wins. All force immediate action with no further evaluation.

| ID | Condition | Forced Action | Result |
|----|-----------|---------------|--------|
| HB_001 | `required_config_missing == true` | Action 2 (request config) | `execution_status = "needs_input"` |
| HB_002 | `attribution_confidence < 0.70` | Action 1 | `execution_status = "blocked"`, skip to 4.8 |
| HB_002b | `buyer_role_confidence < 0.70` | Action 1 | `execution_status = "blocked"`, skip to 4.8 |
| HB_003 | `parse_status == "blocked"` | Action 1 | `execution_status = "blocked"`, skip to 4.8 |
| HB_004 | `stage_confidence < 0.60` | Action 1 | `execution_status = "blocked"`, skip to 4.8 |
| HB_005 | `intent_confidence < 0.60` | Action 1 | `execution_status = "blocked"`, skip to 4.8 |
| HB_006 | `auto_reply_detected == true` | Action 1 | `execution_status = "deferred"`, set `defer_until` |
| HB_007 | `deal_stage == "closed_lost"` AND `deal_paused == false` | Action 1 | `execution_status = "blocked"` |
| HB_008 | `deal_stage == "closed_won"` | Action 1 | `execution_status = "blocked"` |
| HB_009 | `total_turns >= 100` | Action 1 | `execution_status = "blocked"` |

**HB_007 + deal_paused interaction:** When `deal_paused == true` (deal not dead, just stalled — e.g., budget freeze, reorg, timing), HB_007 does not fire. Instead, PL_008 activates (see Priority Locks below), restricting actions to {1, 23, 24} — the system can still nudge or escalate but cannot advance the deal.

Note: `commitment_drift_flag == true` is handled by PL_001 (absolute priority lock forcing Action 10), not a hard block. PL_001 forces Action 10 but continues through composition; hard blocks emit Block Output and skip.

## Priority Locks (PL_001–PL_008)

All applicable locks activate. They stack.

| ID | Condition | Effect | Type |
|----|-----------|--------|------|
| PL_001 | `commitment_drift_flag == true` | `allowed = {10}` | ABSOLUTE |
| PL_002 | High-priority open loop exists | `allowed ⊆ {1–11}` | restrictive |
| PL_003 | `open_loop_count > 0` | `blocked += {17,18,19,20}` | blocking |
| PL_004 | `risk_level == "critical"` | `blocked += {16–21}`, CTA whitelist: `{none, async_review, opt_out}` | blocking |
| PL_005 | `days_since_last_buyer ≥ 14` | Boost 23, 24 before non-boosted at equal tier | sort_boost |
| PL_006 | `last_3_ctas[0] == last_3_ctas[1]` | Block that CTA type | cta_constraint |
| PL_007 | `seller_sent_last == true` AND `hours_since_last_seller < 48` | `blocked += {15,16,17}` | blocking |
| PL_008 | `deal_paused == true` | `allowed = {1, 23, 24}` | restrictive |

**Stacking:** `allowed` → intersection; `blocked` → union; CTA constraints → union. PL_001 is absolute (stops evaluation). PL_008 is restrictive — when active, only escalation and re-engagement nudges are valid.

## Action Table (24 actions)

| # | Name | CTA Type | Stages |
|---|------|----------|--------|
| 1 | Human escalation | none | all |
| 2 | Request config | async_review | all |
| 3 | Answer question | none | all exc. closed |
| 4 | Ask clarification | question | tri/disc/eval |
| 5 | Request external input | async_review | all exc. closed |
| 6 | Deliver asset | async_review | all exc. closed |
| 7 | Gather pricing inputs | none + input_request_block | all exc. closed |
| 8 | Address process blocker | async_review | all exc. closed |
| 9 | Request commitment deadline | async_choice | all exc. closed |
| 10 | Trust repair | async_review or none | all exc. closed |
| 11 | Confirm buyer commitment | async_choice | all exc. closed |
| 12 | Discovery question | question | tri/disc/eval |
| 13 | Stakeholder expansion | question | disc/eval/prop |
| 14 | New stakeholder ack | async_review | disc–neg |
| 15 | Timeline probe | question | eval/prop |
| 16 | Advance conversation | async_choice | disc–prop |
| 17 | Propose meeting | calendar_two_windows | eval/prop |
| 18 | Deliver proposal | async_review | prop/proc |
| 19 | Trial close | calendar_two_windows | prop/neg |
| 20 | Address procurement/legal | async_review | prop/proc/neg |
| 21 | Objection reframe | async_review or question | tri–prop |
| 22 | Competitive differentiation | async_review | eval–neg |
| 23 | Gentle nudge | async_review | all exc. closed |
| 24 | Final nudge | none | all exc. closed |

Stage key: tri=triage, disc=discovery, eval=evaluation, prop=proposal, proc=procurement, neg=negotiation.

## Stage Availability Matrix

| Stage | Actions |
|-------|---------|
| triage | 1–12, 21, 23, 24 |
| discovery | 1–14, 16, 21, 23, 24 |
| evaluation | 1–17, 21–24 |
| proposal | 1–22, 23, 24 |
| procurement | 1–11, 18, 20, 23, 24 |
| negotiation | 1–11, 19, 20, 23, 24 |
| closed_won / closed_lost | 1 only |

## State-Triggered Preconditions

| Action | Precondition |
|--------|-------------|
| 2 | `required_config_missing == true` |
| 3 | `open_loop_count > 0` AND loop type `explicit_question` |
| 5 | Open question needs external input seller lacks |
| 6 | `artifact_request` open AND asset in `enablement_assets` |
| 7 | `buyer_intent == question_pricing` AND `pricing_inputs_sufficient == false` |
| 8 | `process_blocker` loop open |
| 9 | Seller commitment pending, no `deadline_at` |
| 10 | `commitment_drift_flag == true` |
| 11 | Buyer commitment pending, needs confirmation |
| 12 | `open_loop_count == 0` AND stage ∈ {tri,disc,eval} AND `seller_turns < 5` |
| 13 | `open_loop_count == 0` AND `stakeholder_count == 1` AND stage ∈ {disc,eval,prop} |
| 14 | New stakeholder OR `role_detected ∈ {legal,security,procurement}` |
| 15 | `open_loop_count == 0` AND `timeline_unknown` AND stage ∈ {eval,prop} |
| 16 | No loops, no drift, risk ∈ {low,med}, stage ∈ {disc–prop} |
| 17 | No loops, no drift, risk ∈ {low,med}, stage ∈ {eval,prop} |
| 18 | No loops, no drift, pricing inputs ready, stage ∈ {prop,proc} |
| 19 | No loops, no drift, stage ∈ {prop,neg} |
| 20 | `open_loop_count == 0`, stage ∈ {prop,proc,neg} |
| 21 | `objection_tags` present AND intent is objection type |
| 22 | `buyer_intent == objection_competition` OR `rf_competitor_mentioned` |
| 23 | `days_since_last_buyer ≥ 7` AND `friction_pattern ∈ {stall,ghosting}` |
| 24 | `days_since_last_buyer ≥ 14` AND prior nudge sent |

## Intent-Action Affinity

| Intent | Primary | Secondary |
|--------|---------|-----------|
| question_product | 3 | 4, 6 |
| question_pricing | 7 (`pricing_inputs_sufficient == false`) / 3 (`pricing_inputs_sufficient == true`) / 19 (proposal-ready) | 16 |
| question_process | 8 | 3, 16 |
| question_technical | 3 | 4, 6 |
| question_security | 6 (asset) / 5 (external) | 3 |
| question_reference | 6 | 3 |
| objection_timing | 21 | 15 |
| objection_budget | 21 | 7, 19 |
| objection_authority | 13 / 14 (legal/sec/proc) | — |
| objection_need | 21 | 12 |
| objection_competition | 22 | 21 |
| commitment_signal | 18 | 16, 17 |
| commitment_request | 17, 19, 20 | 18 |
| information_share | 12 (early) / 16 (eval+) | 3 |
| administrative | 3 | 18 |
| unclear | 1 | — |

**Selection:** 0 candidates → Action 1. 1 → select. 2+ → sort: primary > secondary, sort_boost (PL_005), lowest ID, lowest CTA pressure.

## Channel Validation (Step 4.6)

If `sending_identity` was provided in the input:

1. Compare `sending_identity` against `seller_emails[]`. If it matches, proceed.
2. **Determine sender sensitivity.** An action is sender-sensitive if ANY of:
   - The action references prior seller commitments (Action 10) or prior seller context (Actions 3, 4, 6)
   - `handoff_detected == true` AND `sending_identity` does not match `handoff_to.email` — when a seller has explicitly delegated the thread and the buyer has acknowledged, ALL subsequent actions are sender-sensitive from the delegating seller's account
3. If the action is sender-sensitive AND the sender conflict exists: set `execution_status = "channel_mismatch"`, populate `channel_mismatch_reason` (for handoffs: "Seller delegated thread to [handoff_to.name] at turn [N]. Buyer acknowledged. Replying from [sending_identity] would undermine the handoff."). Skip to Step 4.9 (Emit Decision Trace). Output must tell the human which account needs to send the reply and why.

If `sending_identity` was not provided, skip this check.

## GRRIPS Composition

**Nodes:** G=Grab (thread-specific attention hook), R1=Relate (mirror understanding), R2=Reinforce (broader business impact — only if genuine), I=Identify (name the gap), P=Present (deliver value payload), S=Suggest (one clear next step with CTA).

Rules: P and S never omittable. G implicit when replying to latest message. R1 implicit in short threads (≤4 turns). One ask-block per message — never CTA + question together. Payload-first for Actions 3, 6, 8, 18, 20.

### Compile Variants

| Variant | Trigger (first match wins) | Key Rule |
|---------|---------------------------|----------|
| trust-repair | PL_001 active | R1 must name what was missed |
| open-loop-priority | PL_002 active | Address unresolved question first |
| natural | `total_turns ≤ 4` AND `open_loop_count ≤ 1` AND risk low/med AND action ∉ {10,17,18,19,21,22} AND buyer register informal | No node structure; conversational reply |
| answer-first | `buyer_intent` starts with `question_` | Lead with P, not context |
| standard | else | Cover G, R1, P, S minimum |

### Tone Calibration

**Risk-register gate:**

| Risk Level | Tone Ceiling |
|---|---|
| low | Match buyer's register fully, including casual or humorous |
| medium | Professional but conversational. Match buyer's vocabulary level |
| high | Careful and measured. Lean formal regardless of buyer register |
| critical | Formal and minimal. No warmth markers, no humor, no personality |

The gate sets the ceiling, not the floor. The buyer's casual register does not override this at high or critical risk. After applying the gate, match the buyer's register within the permitted range. No em dashes.

**9 Anti-Patterns (detect and eliminate):**

1. **Framework artifacts:** The reply reads like labeled nodes executed in order. Fix: write as one coherent message. GRRIPS informs content, not paragraph structure.
2. **Process language:** Internal workflow visible to buyer (pipeline stages, follow-up cadences, routing). Fix: talk about the buyer's situation, not your workflow.
3. **Throat-clearing:** First 1-2 sentences contain nothing the buyer needs. Fix: first sentence states why the email exists.
4. **Performed emotions:** Disproportionate enthusiasm, gratitude, or excitement. Fix: state intentions without performing feelings about them.
5. **Asks that require nothing:** CTA so soft the buyer can nod without acting. Fix: every ask requires a specific answer or action.
6. **Abstraction instead of specificity:** Jargon, consultant vocabulary, enterprise language. Fix: use plain language. Name the specific person, thing, outcome.
7. **Condescension as helpfulness:** Checking comprehension, offering unrequested help, restating known context. Fix: trust the buyer understood.
8. **Manufactured urgency:** Time pressure or scarcity that isn't real. Fix: state real deadlines factually. Never fabricate urgency.
9. **Over-explaining what the buyer knows:** Restating context the buyer provided. Fix: assume the buyer knows what they told you.

**General test:** Read the draft as if you are the buyer and suspect the sender is selling. If any sentence confirms that suspicion, rewrite it.

### Word Limits (ceilings — no floors)

| Category | Ceiling | Actions |
|----------|---------|---------|
| Minimal | 60 | 1, 24 |
| Follow-up | 75 | 2, 23 |
| Discovery | 80 | 12, 13, 15 |
| Standard | 100 | 5, 6, 7, 8, 9, 11, 14, 16, 20 |
| Extended | 150 | 3*, 4, 10, 17, 18, 19 |
| Objection | 200 | 21, 22 |
| Technical | 250 | 3* (technical questions only) |

Exceeding ceiling by >33% triggers `df_over_answering`.

### Draft Variety Constraint (Step 5.6)

If the selected action matches `last_3_actions[0]` (same action as the previous run):

1. The G (Grab) node must reference a different thread element than the prior draft's G node. Do not reuse the same opening hook.
2. If the buyer's industry (`vertical`) is available, incorporate an industry-specific reference or framing in the P node.
3. Vary sentence structure. If the prior draft opened with a statement, open with a question (or vice versa).

Enforceable and auditable. In the decision trace, note which variety adjustments were applied. If `last_3_actions` is empty or the action differs from the prior run, skip this step.

## CTA Types

| CTA | Pressure |
|-----|----------|
| none | 0 |
| opt_out | 0 |
| question | 1 |
| async_review | 2 |
| async_choice | 2 |
| calendar_light | 3 |
| calendar_two_windows | 3 |

At `risk_level == critical`: block `calendar_light` and `calendar_two_windows`.

## Claim Validation (Step 6)

| Source | Check | grounded | On Fail |
|--------|-------|----------|---------|
| thread | `span_ref` → real turn content | true | Strip if ref wrong |
| config | `source_ref` → `product_config` key | true | Strip if missing |
| asset | `source_ref` → `enablement_assets` | true | Strip if missing |
| derived | Hedged with uncertainty language? | null | Hedge it |
| unknown | No source | false | **Strip from draft** |

`validation_status`: pass (all grounded/hedged), fail (critical violations), partial (some stripped).

## Drift Detection (Step 7)

| Flag | Sev | Check | Repair |
|------|-----|-------|--------|
| df_pressure_escalation | CRIT | Urgency lang + risk high/critical | Remove urgency from P/S |
| df_open_loop_ignored | high | High-priority loop unaddressed | Re-route via Step 4 |
| df_stakeholder_neglect | high | New blocker-role stakeholder ignored | Add ack to R1 |
| df_commitment_amnesia | high | Pending/missed seller commitment not referenced | Add ref to R1 |
| df_multi_ask | high | >1 ask-block | Remove secondary ask |
| df_ungrounded_claim | high | `ungrounded_count > 0` after validation | Strip remaining |
| df_cta_repetition | med | CTA same as last 2 runs | Substitute next-best CTA |
| df_premature_depth | med | Technical depth before discovery | Simplify P node |
| df_tone_mismatch | med | Formality diverges from buyer register | Adjust tone |
| df_over_answering | low | `word_count > ceiling × 1.33` | Compress P first |

**Repair loop:** Attempt 1 → if flags remain → Attempt 2 → if new flags appear on attempt 2 that weren't in attempt 1 → ESCALATE immediately. If `df_open_loop_ignored` re-route returns same action → ESCALATE immediately. After 2 failed attempts → `execution_status = "blocked"`, Action 1, Block Output.

## Output Schemas

### Normal Output
```yaml
execution_id: "exec_YYYYMMDDHHMMSS"
timestamp: ISO8601
execution_status: success|blocked|forced|needs_input|repair_applied|deferred|channel_mismatch|parked
action_executed: 1-24
draft: {text, grrips_nodes_used, word_count, cta_type, cta_text, claims}
draft_notes: null  # populated when system defers part of response; contains what AE should consider adding
thread_state_updates: {}
decision_trace: {hard_blocks_evaluated, hard_block_triggered, locks_applied,
  candidates_after_preconditions, selected_action, selection_reason, alternatives_rejected}
drift_checks: {flags_evaluated, flags_triggered, repair_applied}
validation: {validation_status, ungrounded_count, claims_grounded}
defer_until: null  # set when deferred
park_reason: null  # set when parked
revisit_after: null
channel_mismatch_reason: null
```

### Block Output
```yaml
block_reason: str
what_reviewer_needs: str
thread_state_snapshot: {}
recommendation: str
```

## ThreadState Quick Reference

**Tier 1 — Thread Core (immutable):** `thread_id`, `thread_created_at`, `source_channel`, `account_id`, `account_tier`, `vertical`, `product_context`, `seller_emails[]`

**Tier 2 — Current State (mutable):**
- Turns: `turns[]`, `total_turns`, `seller_turns`, `buyer_turns`, `latest_buyer_turn`, `seller_sent_last`, `hours_since_last_seller`, `days_since_last_buyer`, `attribution_confidence`, `buyer_role_confidence`
- Classification: `deal_stage`, `buyer_intent`, `stage_confidence`, `intent_confidence`
- Dynamics: `open_loops[]`, `open_loop_count`, `commitments_made[]`, `commitments_received[]`, `commitment_drift_flag`, `stakeholders[]`, `stakeholder_count`, `stakeholder_delta_last_turn`, `objection_tags[]`, `risk_level`, `risk_factors[]`, `friction_pattern`, `timeline_unknown`, `handoff_detected`, `handoff_to`, `handoff_at_turn`, `deal_paused`
- Derived: `pricing_inputs_sufficient` (boolean — true when buyer has provided enough scoping data for a pricing conversation: use case, seat count or volume, and timeline)
- History: `last_3_ctas[]`, `last_3_actions[]`, `last_seller_cta`, `last_seller_action`, `cta_repeat_flag`, `action_diversity_score`
- Ingest: `auto_reply_detected`, `return_date`, `defer_until`

**Tier 3 — Gating (never modified downstream):** `required_config_missing`, `missing_config_fields[]`, `parse_status`

**Tier 3 — Derived (set by Module 07):** `last_grrips_node`, `grrips_failure_tag`, `decision_trace_id`, `message_artifact_id`

**Input-only (not persisted):** `sending_identity`, `account_context`

## FOUNDATION 10→24 Action Map

| FOUNDATION Class | GEN-SE Actions |
|------------------|---------------|
| ACKNOWLEDGE | 11, 14 |
| REQUEST_CLARIFICATION | 2, 4, 5, 7 |
| RESPOND | 3, 6, 8, 20, 21, 22 |
| EXECUTE | 18 |
| PROPOSE_NEXT_STEP | 12, 13, 15, 16, 17, 19 |
| ESCALATE | 1 |
| Straddle (state-triggered) | 9, 10, 23, 24 |

NO_ACTION, DEFER, LOG, CLOSE → GEN-SE not invoked (falls back to message-os).

## Execution Status Values

`success` — normal selection. `blocked` — no candidates / repair exhausted. `forced` — hard block or PL_001. `needs_input` — config missing, Action 2. `repair_applied` — drift repaired. `deferred` — auto-reply detected. `channel_mismatch` — wrong sending account. `parked` — stalled but below ghosting threshold; includes `park_reason` + `revisit_after`.

## Canonical Enums (Quick Ref)

**Deal Stages (8):** triage, discovery, evaluation, proposal, procurement, negotiation, closed_won, closed_lost. Default: `"triage"`. Never null.

**Buyer Intents (16):** question_product, question_pricing, question_process, question_technical, question_security, question_reference, objection_timing, objection_budget, objection_authority, objection_need, objection_competition, commitment_signal, commitment_request, information_share, administrative, unclear. Default: `"unclear"`. Never null.

**Open Loop Types (3):** explicit_question, artifact_request, process_blocker

**Stakeholder Roles (10):** champion, economic_buyer, evaluator, legal, security, procurement, executive, technical, referrer, gatekeeper

**Risk Factors:** rf_stalled, rf_competitor_mentioned, rf_budget_constraint, rf_authority_gap, rf_multiple_blockers
