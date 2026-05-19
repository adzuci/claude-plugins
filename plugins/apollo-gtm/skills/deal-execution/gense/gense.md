---
name: gense
description: >-
  Execute the GEN-SE (Generative Sales Engine) pipeline. Given a raw B2B sales email thread,
  run a deterministic pipeline that produces a safe reply draft or human escalation with a
  complete decision trace. Load when the user provides an email thread for GEN-SE processing,
  asks you to run the sales engine, or wants to generate a response using the GRRIPS framework.
  Also load for architecture questions, spec patches, or any work within GEN-SE constraints.
metadata:
  author: David Johnson-Hall
  version: '2.3'
---

# GEN-SE -- Generative Sales Engine

**Purpose:** This file enables a Claude instance to execute the GEN-SE pipeline. Given a raw email thread and minimal configuration, you will produce either a safe reply draft or a human escalation, with a complete decision trace.

**Self-contained:** When loaded as the active execution skill, this file governs. If conversation memory conflicts with this file, this file wins. In the bundled Apollo GTM System, `gense-runtime.md` is the default load; this full file is loaded for edge cases, architecture review, or debugging. The execution-spine modules are architecture documentation only — they are never loaded at runtime.

**Owner:** David Johnson-Hall. Independently developed IP. No employer context applies.

**Companion system:**
- **GRRIPS** -- David's sales communication methodology (G-R-R-I-P-S), refined across 100,000+ sales conversations. Powers message generation inside GEN-SE.

**When NOT to use this skill:**
- Outbound prospecting or cold outreach
- Audit/scoring of past sales conversations
- Writing marketing copy, website content, or non-email sales assets
- Threads with no buyer message (nothing to respond to)
- Non-B2B contexts (consumer support, personal email)

---

# PART 1: EXECUTION PROTOCOL

---

## How to Run GEN-SE

When a user provides an email thread, execute the following steps in strict order. Produce intermediate state at each step. Never skip a module. If any module blocks, stop and emit a block output.

### What the User Must Provide

**Required:**
- Raw email thread (the full thread text, including all replies)
- Seller identity (at minimum: seller email address or domain)

**Optional but improves accuracy:**
- `seller_emails[]` -- list of all seller email addresses
- `seller_domains[]` -- seller company domains
- `internal_domains[]` -- domains to treat as internal/seller-side
- `product_context` -- what the seller sells (product/service name, category)
- `account_tier` -- importance level of this account
- `vertical` -- buyer's industry
- `product_config` -- verified product facts (pricing, features, capabilities)
- `enablement_assets` -- approved documents, case studies, data sheets with asset_ids
- `persisted_state` -- ThreadState from a prior run (if this is a continuation)
- `sending_identity` -- email address the reply will be sent FROM (if different from primary seller)
- `account_context` -- signals from other threads at the same company (e.g., other contacts engaged, referral chains, parallel deals). Structured as: `{related_threads: [{thread_id, contact_name, contact_role, deal_stage, last_activity, notes}]}`

If the user provides only a raw thread and seller email, proceed with available information. Set `required_config_missing = true` and `missing_config_fields[]` for anything you cannot infer, but do not block unless the missing data prevents safe execution.

---

## Step 1: INGEST (Module 02)

**What you are doing:** Parsing raw email text into structured turns with speaker attribution.

**This step uses LLM reasoning** to parse unstructured email text. The output must be structured and deterministic.

### Procedure

1. **Split the thread into turns.** Each distinct message in the thread is one turn. Identify boundaries by reply headers, quoted text markers, timestamps, or signature blocks.

2. **For each turn, extract:**
   - `turn_number` -- assign sequentially, 1-based, oldest first
   - `speaker_email` -- the sender's email address
   - `speaker` -- classify as `"seller"`, `"buyer"`, or `"unknown"` using the seller identity provided by the user. If the sender email matches `seller_emails[]` or `seller_domains[]` or `internal_domains[]`, they are `"seller"`. Otherwise, `"buyer"`. If you cannot determine, mark `"unknown"`.
   - `body` -- the message content, stripped of signatures, quoted reply text, and email footers. Preserve only the original content the sender wrote in that turn.
   - `raw_body` -- the full unprocessed message text
   - `timestamp` -- ISO8601 if available, otherwise `null`

3. **Score attribution confidence:**
   - `attribution_confidence` -- how confident you are that the speaker classification is correct. Score 0.0-1.0.
   - `buyer_role_confidence` -- how confident you are about the buyer's organizational role. Score 0.0-1.0.

4. **Determine parse status:**
   - `"success"` -- all turns parsed, all speakers attributed
   - `"partial"` -- some turns parsed but gaps exist
   - `"blocked"` -- thread is unparseable (garbled, too short, no clear structure)

5. **Detect auto-replies and out-of-office messages.** Check the latest buyer turn for OOO patterns: "out of office", "automatic reply", "I am currently away", "will return on", "limited access to email", vacation auto-responders, or any system-generated non-human message. If detected:
   - Set `auto_reply_detected: true`
   - Extract `return_date` (ISO8601) if a return date is mentioned, otherwise `null`
   - Set `defer_until` to `return_date + 1 day` if available, otherwise `null`
   - The pipeline will still complete Step 1 but will be routed to deferral via HB_006 in Step 4.

### Gate Check (MECHANICAL -- do not reason through this, apply the rule)

```
IF attribution_confidence < 0.70  --> BLOCK. Go to Block Output.
IF buyer_role_confidence < 0.70   --> BLOCK. Go to Block Output.
IF parse_status == "blocked"      --> BLOCK. Go to Block Output.
```

### Step 1 Output

```
turns: [Turn, Turn, ...]
attribution_confidence: float
buyer_role_confidence: float
parse_status: "success" | "partial" | "blocked"
auto_reply_detected: bool
return_date: ISO8601 | null
defer_until: ISO8601 | null
```

---

## Step 2: EXTRACT (Module 03)

**What you are doing:** Reading the parsed turns and populating the full ThreadState.

**This step uses LLM reasoning** to detect open loops, commitments, stakeholders, and patterns from conversation text.

### Procedure

Scan all turns and extract the following. Be conservative -- only flag what is clearly present in the text.

**1. Open Loops** -- Questions or requests from the buyer that the seller has not yet answered.

For each open loop, create an OpenLoop object:
- `loop_id` -- unique identifier (e.g., `"OL_001"`)
- `type` -- classify as:
  - `"explicit_question"` -- buyer asked a direct question
  - `"artifact_request"` -- buyer asked for a document, proposal, pricing, demo, etc.
  - `"process_blocker"` -- buyer raised a procedural issue (legal review, procurement step, etc.)
- `priority` -- `"high"` (blocks deal progress), `"medium"` (important but not blocking), `"low"` (nice to address)
- `resolution_status` -- `"open"` if unanswered, `"resolved"` if addressed in a later turn, `"deferred"` if explicitly pushed to later
- `created_at_turn` -- turn number where the loop was created
- `resolved_at_turn` -- turn number where it was resolved, or `null`

**2. Commitments** -- Promises made by either seller or buyer.

For each commitment, create a Commitment object:
- `commitment_id` -- unique (e.g., `"CMT_001"`)
- `type` -- `"deliverable"` | `"follow_up"` | `"meeting"`
- `status` -- `"pending"` (not yet fulfilled), `"delivered"` (fulfilled), `"missed"` (deadline passed or clearly not done)
- `maker_role` -- `"seller"` or `"buyer"`
- `deadline_at` -- if a date/time was mentioned, ISO8601. Otherwise `null`.
- `description` -- what was promised

Seller promises go in `commitments_made[]`. Buyer promises go in `commitments_received[]`.

**3. Stakeholders** -- People involved in the thread.

For each person, create a Stakeholder object:
- `email` -- their email address
- `name` -- if discernible from the thread
- `role_detected` -- classify using canonical roles: `champion`, `economic_buyer`, `evaluator`, `legal`, `security`, `procurement`, `executive`, `technical`, `referrer`, `gatekeeper`. Use the best fit based on context clues (title, department, what they ask about, how they're addressed). A `referrer` introduces but does not engage further. A `gatekeeper` controls access without evaluating.
- `first_appeared_turn` -- turn number

**4. Objection Tags** -- Classify any buyer resistance signals:
Scan for objections and tag with canonical values: `objection_timing`, `objection_budget`, `objection_authority`, `objection_need`, `objection_competition`. A turn can have multiple tags. Only tag what is clearly expressed.

**5. CTA & Action History** -- If `persisted_state` was provided:
- Carry forward `last_3_ctas[]`, `last_3_actions[]`, `last_seller_cta`, `last_seller_action`
- Compute `cta_repeat_flag` -- true if `last_3_ctas[0] == last_3_ctas[1]`
- Compute `action_diversity_score` -- count of unique actions in `last_3_actions[]` / 3

If no persisted state, initialize all history fields as empty.

**6. Handoff Detection** -- Scan turns for explicit seller-to-seller handoff signals. A handoff is detected when:
- A seller turn introduces another seller-side person by name AND uses delegation language ("I'll connect you with", "I'll let you two take it from here", "he/she will be reaching out", "[Name] handles [territory/area]"), AND
- A subsequent buyer turn acknowledges the handoff ("looking forward to hearing from [Name]", "sounds good", or similar acceptance)

If detected:
- `handoff_detected: true`
- `handoff_to: {name, email}` (the person the thread was handed to)
- `handoff_at_turn: int` (the seller turn where delegation occurred)

If not detected, set `handoff_detected: false`. This field is Tier 2 (mutable, set by Module 02).

**7. Compute derived fields:**
- `total_turns`, `seller_turns`, `buyer_turns` -- count from turns[]. `seller_turns` counts all turns where `speaker == "seller"`, regardless of which individual on the seller side sent the message. In multi-seller threads (e.g., AE and SE both active), all seller-side speakers are counted together.
- `latest_buyer_turn` -- the turn_number (1-based) of the most recent buyer turn
- `seller_sent_last` -- `true` if the most recent turn in the thread is a seller turn. `false` if the most recent turn is a buyer turn.
- `hours_since_last_seller` -- hours since the most recent seller turn timestamp to now. Set to `null` if no seller turns exist or no timestamp is available.
- `days_since_last_buyer` -- calendar days from the latest buyer turn timestamp to now. If no timestamp, estimate from context or set `null`.
- `open_loop_count` -- count of open loops where `resolution_status == "open"`
- `commitment_drift_flag` -- `true` if any seller commitment has `status == "missed"` or `status == "pending"` with `deadline_at` in the past
- `stakeholder_count` -- count of unique stakeholders
- `stakeholder_delta_last_turn` -- number of new stakeholders in the latest turn (0 if none)
- `friction_pattern` -- `"stall"` if `days_since_last_buyer >= 7`, `"ghosting"` if >= 14 with no buyer response to seller outreach, `null` otherwise
- `timeline_unknown` -- `true` if no timeline, deadline, or urgency signal has been mentioned by the buyer
- `risk_level` -- initial assessment: `"low"`, `"medium"`, `"high"`, `"critical"`. Consider: stall signals, competitor mentions, budget concerns, authority gaps, multiple blockers.
- `risk_factors[]` -- tag applicable factors: `rf_stalled`, `rf_competitor_mentioned`, `rf_budget_constraint`, `rf_authority_gap`, `rf_multiple_blockers`

**8. Incorporate account context (if provided).** If `account_context` was provided in the input:
- Note which other contacts at the same company are engaged and at what deal stage
- Flag if a referral chain exists (e.g., Contact A referred the seller to Contact B)
- Record any cross-thread signals that affect risk assessment (e.g., another thread at same account is in procurement = positive signal; another thread went closed_lost = caution signal)
- This context is supplementary evidence for Steps 2-3. It does not override routing logic or pipeline mechanics.

**9. Set gating fields:**
- `required_config_missing` -- `true` if the user did not provide enough config to safely generate a response
- `missing_config_fields[]` -- list what is missing
- Carry forward `parse_status` from Step 1

**10. If persisted_state was provided:** Merge fresh extraction with persisted state. Fresh extraction overrides mutable fields (Tier 2). Thread Core (Tier 1) is never overwritten. Gating fields (Tier 3) are never modified downstream.

### Step 2 Output

The complete ThreadState. Present it structured, grouped by tier.

---

## Step 3: CLASSIFY (Module 04)

**What you are doing:** Determining the deal stage and buyer intent from thread content.

**This step uses LLM reasoning** for classification, but outputs must map to canonical enumerations.

### Procedure

**1. Classify deal_stage.** Read the full thread and determine where this conversation sits:

| Stage | Signals |
|-------|---------|
| `triage` | First touch, no discovery yet, unclear if buyer is qualified |
| `discovery` | Buyer engaged, asking/answering questions, needs being explored |
| `evaluation` | Buyer comparing options, asking for specifics, technical/security review |
| `proposal` | Pricing/proposal requested or delivered, terms being discussed |
| `procurement` | Legal, security, procurement process underway |
| `negotiation` | Terms being negotiated, contracts in review |
| `closed_won` | Deal done |
| `closed_lost` | Buyer explicitly disengaged or chose competitor |

Default: `"triage"`. Never output `null`.

Assign `stage_confidence` (0.0-1.0). If the signals are ambiguous or mixed, lower the score.

**2. Classify buyer_intent.** Identify the primary intent of the buyer's most recent message:

| Intent | What It Looks Like |
|--------|-------------------|
| `question_product` | Asking what the product does, features, capabilities |
| `question_pricing` | Asking about cost, pricing tiers, discounts |
| `question_process` | Asking about next steps, how things work, timelines |
| `question_technical` | Asking about integrations, architecture, technical specs |
| `question_security` | Asking about compliance, security certifications, data handling |
| `question_reference` | Asking for case studies, references, customer examples |
| `objection_timing` | "Not now", "maybe next quarter", timing pushback |
| `objection_budget` | "Too expensive", "no budget", cost concerns |
| `objection_authority` | "Need to check with my boss", "not my decision" |
| `objection_need` | "We don't really need this", "not a priority" |
| `objection_competition` | "We're looking at [competitor]", "already have a solution" |
| `commitment_signal` | "This looks good", "let's move forward", positive signals |
| `commitment_request` | "Send me a proposal", "let's schedule a call", action request |
| `information_share` | Buyer sharing context, requirements, or internal details |
| `administrative` | Scheduling, logistics, out-of-office, forwarding |
| `unclear` | Cannot determine intent from the message |

Default: `"unclear"`. Never output `null`.

Assign `intent_confidence` (0.0-1.0).

**3. Multi-intent detection:** If the top two plausible intents are very close (within ~0.08 confidence), flag the ambiguity in your trace and apply a -0.12 penalty to `intent_confidence`. Use enum order as tie-break (earlier in the list wins).

**4. Prior classification comparison:** If `persisted_state` was provided, compare your classification against the prior `deal_stage` and `buyer_intent`. If either changed significantly (e.g., stage regressed, or intent shifted categories), flag this in your evidence_trace. Stage regression (e.g., evaluation back to discovery) is not invalid but should be noted.

**5. Assess risk:** Update `risk_level` and `risk_factors[]` based on classification results. If `objection_competition` is detected, add `rf_competitor_mentioned`. If `objection_budget`, add `rf_budget_constraint`. If `objection_authority`, add `rf_authority_gap`.

**6. Incorporate account context into classification (if available).** If `account_context` was provided and contains cross-thread signals, use them as supplementary evidence when assessing risk and stage. For example: if another thread at the same account is in `procurement`, this is a positive signal that may lower risk. If another thread went `closed_lost`, this is a caution signal that may raise risk. Note any cross-thread influence in `evidence_trace`. Account context informs classification but never overrides it.

### Gate Check (MECHANICAL)

```
IF stage_confidence < 0.60  --> ESCALATE. Set action = 1 (human review). Go to Output.
IF intent_confidence < 0.60 --> ESCALATE. Set action = 1 (human review). Go to Output.
```

### Step 3 Output

```
deal_stage: str (canonical)
buyer_intent: str (canonical)
stage_confidence: float
intent_confidence: float
risk_level: str
risk_factors: list
evidence_trace: str (brief explanation of classification reasoning)
```

---

## Step 4: ROUTE (Module 06 -- Policy Engine)

**What you are doing:** Selecting exactly one action from 24 using deterministic rules. No reasoning, no judgment. Apply rules mechanically.

**This entire step is MECHANICAL.** Do not use judgment. Follow the rules exactly.

### 4.1 Check Hard Blocks

Evaluate in order. First trigger wins:

| Code | Condition | Result |
|------|-----------|--------|
| HB_001 | `commitment_drift_flag == true` | Force Action 10 via PL_001 |
| HB_002 | `attribution_confidence < 0.70` | Force Action 1 |
| HB_002b | `buyer_role_confidence < 0.70` | Force Action 1 |
| HB_003 | `parse_status == "blocked"` | Force Action 1 |
| HB_004 | `stage_confidence < 0.60` | Force Action 1 |
| HB_005 | `intent_confidence < 0.60` | Force Action 1 |
| HB_006 | `auto_reply_detected == true` | Force Action 1 |

If HB_001 triggers: proceed through PL_001 (which forces Action 10), then continue to Step 4.6 (Validate Sending Channel) and Step 4.7 (Build CTA Constraint). Action 10 is sender-sensitive -- a trust-repair message sent from the wrong account undermines the repair.
If HB_002-HB_005 trigger: action is 1, CTA is `none`, `execution_status = "forced"`. Skip to Step 4.8.
If HB_006 triggers: action is 1, CTA is `none`, `execution_status = "deferred"`. Set `defer_until` from Step 1 output. Skip to Step 4.8. The output should recommend revisiting after the return date.

### 4.2 Apply Priority Locks

Evaluate PL_001 through PL_006 in order. All applicable locks activate. They stack.

| Lock | Condition | Effect | Type |
|------|-----------|--------|------|
| PL_001 | `commitment_drift_flag == true` | `allowed_actions = {10}` | ABSOLUTE |
| PL_002 | Any open loop with `priority == "high"` and `resolution_status == "open"` | `allowed_actions <= {1-11}` | restrictive |
| PL_003 | `open_loop_count > 0` | `blocked_actions += {17,18,19,20}` | blocking |
| PL_004 | `risk_level == "critical"` | `blocked_actions += {16-21}`, CTA whitelist: `{none, async_review, opt_out}` | blocking |
| PL_005 | `days_since_last_buyer >= 14` | Boost actions 23, 24: sort before non-boosted at equal affinity tier | sort_boost |
| PL_006 | `last_3_ctas[0] == last_3_ctas[1]` (same CTA twice in a row) | Block that CTA type | cta_constraint |
| PL_007 | `seller_sent_last == true` AND `hours_since_last_seller < 48` | `blocked_actions += {15, 16, 17}` | blocking |

**Stacking rules:**
- `allowed_actions` sets: take INTERSECTION (most restrictive wins)
- `blocked_actions` sets: take UNION (all blocks apply)
- `cta_constraints`: take UNION
- PL_001 is ABSOLUTE -- if it triggers, action is 10, stop evaluating.

Record which locks are active. You will need this for GRRIPS variant selection.

### 4.3 Evaluate Preconditions

For each action 1-24, check if its precondition is met AND it is not blocked by locks AND it is available at the current deal_stage. Build a candidate list.

**Key preconditions:**

| Action | Precondition |
|--------|-------------|
| 1 | Always available |
| 2 | `required_config_missing == true` |
| 3 | `open_loop_count > 0` AND any open loop has `type == "explicit_question"` |
| 4 | Same as 3 + `deal_stage IN (triage, discovery, evaluation)` + clarification would help |
| 5 | Open question requires external input the seller does not have |
| 6 | `artifact_request` open AND asset exists in `enablement_assets` |
| 7 | `buyer_intent == "question_pricing"` with missing inputs, OR reference criteria missing |
| 8 | `process_blocker` loop open |
| 9 | Seller commitment `status == "pending"` with no `deadline_at` |
| 10 | `commitment_drift_flag == true` |
| 11 | Buyer commitment `status == "pending"` needing confirmation |
| 12 | `open_loop_count == 0` AND `deal_stage IN (triage, discovery, evaluation)` AND `seller_turns < 5` |
| 13 | `open_loop_count == 0` AND `stakeholder_count == 1` AND `deal_stage IN (discovery, evaluation, proposal)` |
| 14 | New stakeholder entered thread OR `role_detected IN (legal, security, procurement)` |
| 15 | `open_loop_count == 0` AND `timeline_unknown == true` AND `deal_stage IN (evaluation, proposal)` |
| 16 | `open_loop_count == 0` AND no drift AND `risk_level IN (low, medium)` AND `deal_stage IN (discovery-proposal)` |
| 17 | `open_loop_count == 0` AND no drift AND `risk_level IN (low, medium)` AND `deal_stage IN (evaluation, proposal)` |
| 18 | `open_loop_count == 0` AND no drift AND pricing inputs available AND `deal_stage IN (proposal, procurement)` |
| 19 | `open_loop_count == 0` AND no drift AND `deal_stage IN (proposal, negotiation)` |
| 20 | `open_loop_count == 0` AND `deal_stage IN (proposal, procurement, negotiation)` |
| 21 | `objection_tags` present AND `buyer_intent` is an objection type |
| 22 | `buyer_intent == "objection_competition"` OR `rf_competitor_mentioned` in risk_factors |
| 23 | `days_since_last_buyer >= 7` AND `friction_pattern IN ("stall", "ghosting")` |
| 24 | `days_since_last_buyer >= 14` AND prior nudge was sent |

**Stage availability:**

| Stage | Available Actions |
|-------|------------------|
| triage | 1-12, 21, 23, 24 |
| discovery | 1-14, 16, 21, 23, 24 |
| evaluation | 1-17, 21-24 |
| proposal | 1-22, 23, 24 |
| procurement | 1-11, 18, 20, 23, 24 |
| negotiation | 1-11, 19, 20, 23, 24 |
| closed_won / closed_lost | 1 only |

### 4.4 Apply Intent-Action Affinity

If 2+ candidates remain, use the affinity table to rank them:

| buyer_intent | Primary | Secondary |
|-------------|---------|-----------|
| question_product | 3 | 4, 6 |
| question_pricing | 7 (inputs missing) / 19 (ready) | 3, 16 |
| question_process | 8 | 3, 16 |
| question_technical | 3 | 4, 6 |
| question_security | 6 (asset exists) / 5 (external) | 3 |
| question_reference | 6 | 3 |
| objection_timing | 21 | 15 |
| objection_budget | 21 | 7, 19 |
| objection_authority | 13 (default) / 14 (if legal/security/procurement) | -- |
| objection_need | 21 | 12 |
| objection_competition | 22 | 21 |
| commitment_signal | 18 | 16, 17 |
| commitment_request | 17, 19, 20 | 18 |
| information_share | 12 (early) / 16 (eval+) | 3 |
| administrative | 3 | 18 |
| unclear | 1 | -- |

### 4.5 Select Action

```
0 candidates --> Action 1
1 candidate  --> select it
2+ candidates --> sort by: primary over secondary, then sort_boost (PL_005 boosted
                  actions sort before non-boosted at equal tier), then lowest
                  action_id, then lowest CTA pressure
```

### 4.6 Validate Sending Channel

**This sub-step is MECHANICAL.** If `sending_identity` was provided in the input:

1. Compare `sending_identity` against `seller_emails[]`. If it matches, proceed.
2. **Determine sender sensitivity.** An action is sender-sensitive if ANY of the following are true:
   - The action references prior seller commitments (Action 10) or prior seller context (Actions 3, 4, 6)
   - `handoff_detected == true` AND `sending_identity` does not match `handoff_to.email`. When a seller has explicitly delegated the thread to another person and the buyer has acknowledged, ALL subsequent actions are sender-sensitive from the delegating seller's account. The thread now belongs to the handoff recipient.
3. If the action is sender-sensitive AND the sender conflict exists: set `execution_status = "channel_mismatch"`, `channel_mismatch_reason` describing the conflict (for handoffs: "Seller delegated thread to [handoff_to.name] at turn [N]. Buyer acknowledged. Replying from [sending_identity] would undermine the handoff."). Skip to Step 4.9 (Emit Decision Trace). The output should tell the human which account needs to send the reply and why.

If `sending_identity` was not provided, skip this check.

### 4.7 Build CTA Constraint

Based on the selected action and active locks, determine:

```
allowed_ctas: which CTAs this action can use
blocked_ctas: CTAs blocked by locks (PL_004, PL_006)
whitelist_ctas: if PL_004 active, only {none, async_review, opt_out}
pressure_ceiling: 3 (default)
```

**CTA restriction at critical risk:** `calendar_light` and `calendar_two_windows` are blocked.

### 4.8 Set Execution Status

```
IF action was forced by hard block or PL_001 --> execution_status = "forced"
IF HB_006 triggered (auto-reply) --> execution_status = "deferred"
IF no candidates remained and Action 1 was selected as fallback --> execution_status = "blocked"
IF action was selected normally --> execution_status = "success"
IF required_config_missing == true and Action 2 selected --> execution_status = "needs_input"
IF channel validation failed --> execution_status = "channel_mismatch"
IF after Step 4.5 the only remaining candidate is Action 1 AND days_since_last_buyer >= 7 AND days_since_last_buyer < 14 AND friction_pattern == "stall" --> execution_status = "parked", set park_reason (why no action fit) and revisit_after (days_since_last_buyer reaches 14)
```

### 4.9 Emit Decision Trace

Record:
- Which hard blocks were evaluated and whether any triggered
- Which priority locks are active
- The candidate list after locks
- The candidate list after preconditions
- The affinity ranking
- The selected action and why
- Alternatives that were rejected and why
- `execution_status`

---

## Step 5: GENERATE (Module 07 -- GRRIPS Compiler)

**What you are doing:** Writing the actual reply message informed by GRRIPS thinking, not shaped by GRRIPS structure.

**This step uses LLM reasoning** for prose generation, constrained by the action, CTA, and compile variant selected in Step 4. GRRIPS is the analytical framework that determines what to include. It is not a sentence template. The output should read like a natural email that happens to cover the right elements, not like a framework being executed.

### 5.1 Select Compile Variant

Check in order, first match wins:

```
IF PL_001 in active locks --> "trust-repair"
IF PL_002 in active locks --> "open-loop-priority"
IF total_turns <= 4
   AND open_loop_count <= 1
   AND risk_level IN (low, medium)
   AND action NOT IN (10, 17, 18, 19, 21, 22)
   AND buyer's most recent message is informal (short sentences, no formal
       structure, conversational vocabulary)
   --> "natural"
IF buyer_intent starts with "question_" --> "answer-first"
ELSE --> "standard"
```

The natural variant is checked before answer-first. A casual short thread with a question intent gets natural treatment, not answer-first. A buyer who writes "hey do you guys have sso" gets a conversational answer, not a structured answer-first arc.

High-stakes actions (10: commitment recovery, 17: call proposal, 18: proposal delivery, 19: trial close, 21: objection reframe, 22: competitive comparison) always get structured treatment regardless of thread length or register.

### 5.2 Compile Using GRRIPS Thinking

GRRIPS defines what the message must accomplish. It does not define sentence order or paragraph structure. Use the nodes as a checklist of elements to include, then write the email naturally.

**GRRIPS elements (include as needed, not as a rigid sequence):**

| Element | Purpose | Guidance |
|---------|---------|----------|
| G (Grab) | Earn attention | Reference something specific from the thread. Never generic. Never hype. Often the opening line, but can be woven in. |
| R1 (Relate) | Show understanding | Demonstrate you understand their situation or concern. Mirror their language. Do not lecture. |
| R2 (Reinforce) | Elevate stakes | Connect to a broader business impact. Only include if genuine and non-manufactured. Skip when it would feel forced. |
| I (Identify) | Name the need | Articulate the specific gap or problem. Must be grounded in what they said, not assumed. |
| P (Present) | Deliver value | The payload: answer their question, provide the asset, deliver the proposal. Length varies by action. |
| S (Suggest) | Propose next step | One clear, low-pressure next step. This is where the CTA lives. |

**Variant guidance (determines emphasis, not rigid arcs):**

| Variant | Emphasis | Key Rule |
|---------|----------|----------|
| standard | Cover G, R1, P, S at minimum. Include R2 and I only if they add value. | No specific order required. Write naturally. |
| answer-first | Lead with the answer (P), not with context. | Do not bury the answer below setup. Get to it fast. |
| open-loop-priority | Address the unresolved question before anything else. | R1 or opening line directly addresses the open loop. |
| trust-repair | Acknowledge the miss or lateness explicitly. | R1 must name what was missed. Do not gloss over it. |
| natural | Write a conversational reply informed by the GRRIPS analysis. | No node structure required. Use when the buyer's register is casual, the thread is short, or a structured approach would feel forced. The GRRIPS elements still inform what to include, but the email reads as a natural reply. |

A 40-word casual reply should not sound like a framework was executed to produce it.

**Implicit node omission:** If a node's purpose is already satisfied by the reply context, you may omit it.
- **G (Grab)** is implicitly satisfied when you are directly replying to the buyer's most recent message. You do not need to reference the thread to earn attention when the buyer is waiting for your reply.
- **R1 (Relate)** is implicitly satisfied in short threads (4 turns or fewer) where the buyer's concern is obvious from the most recent message. You do not need to restate what they said when there are only 2-3 messages.
- **R2 (Reinforce)** and **I (Identify)** remain optional per the guidance above. Include only when they add genuine value.
- **P (Present)** and **S (Suggest)** are never omittable. The email must deliver value and propose a next step.

Omission must be intentional. Note which nodes were omitted and why in `grrips_nodes_used` (list only the nodes actually addressed).

**Payload-first principle (applies within all variants):** For actions whose primary purpose is delivering something the buyer is waiting for (Actions 3, 6, 8, 18, 20), lead with the delivery even when the variant is not answer-first. The buyer knows what they asked for. Referencing the thread before delivering the answer adds latency to the email's purpose. A grab (G) that restates the buyer's question before answering it is throat-clearing (Pattern 3 in Section 5.5). The variant governs everything after the delivery.

### 5.3 Apply Word Limits

| Category | Ceiling | Actions |
|----------|---------|--------|
| Minimal | 60 | 1, 24 |
| Follow-up | 75 | 2, 23 |
| Discovery | 80 | 12, 13, 15 |
| Standard | 100 | 5, 6, 7, 8, 9, 11, 14, 16, 20 |
| Extended | 150 | 3*, 4, 10, 17, 18, 19 |
| Objection | 200 | 21, 22 |
| Technical | 250 | 3* (technical questions only) |

**Floors are removed.** A short message that covers the required elements is better than a padded message that hits a word count. If the reply naturally comes in at 35 words and addresses the action, the CTA, and the buyer's concern, that is correct output.

**Ceilings are enforced.** Exceeding the ceiling by more than 33% triggers `df_over_answering` in Step 7. Compress the P element first.

### 5.4 Apply Ask-Block Rule

**One ask-block per message. No exceptions.**

- If the action's CTA is not `none`: the ask-block is the CTA. Type = `"cta"`.
- If the action uses a question (e.g., Action 4, 12, 13, 15): the ask-block is the question. Type = `"question"`.
- If Action 7: the ask-block is an `"input_request_block"` with up to 3 sub-questions.
- NEVER include both a CTA and a question.

### 5.5 Tone Calibration

**Risk-register gate (evaluate first):**

| Risk Level | Tone Ceiling |
|---|---|
| low | Match the buyer's register fully, including casual, direct, or humorous |
| medium | Professional but conversational. Match the buyer's vocabulary level |
| high | Careful and measured. Lean formal regardless of buyer register |
| critical | Formal and minimal. No warmth markers, no humor, no personality |

This gate sets the ceiling, not the floor. At low risk you are permitted to be warm, not required to be. At high risk you are required to be formal. The buyer's casual register does not override this at high or critical risk.

After applying the risk gate, match the buyer's register within the permitted range. If they write formal corporate email, write formal. If they are casual and direct and risk is low or medium, be casual and direct. The reply should sound like the seller wrote it, not like a framework produced it. No em dashes.

Tone calibration is governed by pattern recognition, not phrase avoidance. The model must learn to recognize why certain approaches create sales resistance, not memorize a list of banned strings.

**Pattern 1: Framework artifacts in the output.**
The reply reads like a sequence of labeled nodes executed in order. Each paragraph serves exactly one framework function with predictable transitions between them. The buyer cannot tell a framework was used, but they can feel the mechanical rhythm. The fix: write the email as a single coherent message. The GRRIPS elements inform what to include. They do not dictate paragraph structure, sentence order, or transition patterns. Vary rhythm. Let sentences do double duty. A good sales email does not have visible seams between its analytical components.

**Pattern 2: Process language leaking into conversation.**
The seller's internal workflow becomes visible to the buyer. The buyer hears "I am managing a sales process" rather than "I am talking to you." This happens whenever the email references internal sequencing, pipeline stages, follow-up cadences, or organizational routing that the buyer has no reason to see. The fix: talk about the buyer's situation, not your workflow. Never reference what you are doing internally. The buyer should only see what is relevant to them.

**Pattern 3: Throat-clearing before the point.**
The message delays its reason for existing. The first 1-2 sentences contain no information the buyer needs. The buyer's attention is spent on warmup before they learn why the email was sent. The fix: the first sentence should contain the reason the email exists, or a direct reference to something the buyer said. If the email has no clear reason to exist, it should not be sent.

**Pattern 4: Performed emotions.**
The seller displays enthusiasm, gratitude, or excitement that is disproportionate to the situation. The buyer recognizes this as rapport manufacturing because the emotional register does not match the context. The fix: state intentions without performing feelings about them. If you want to schedule a call, say so. Do not announce that you are excited about the possibility of scheduling a call.

**Pattern 5: Asks that require nothing.**
The CTA is so soft that the buyer can acknowledge it without taking action. The email ends with a request that creates no commitment and no clear next step. The buyer files it as "responded to" without doing anything. The fix: every ask should require a specific answer or a specific action. If the buyer can respond with a nod and nothing changes, the ask is too weak.

**Pattern 6: Abstraction instead of specificity.**
The seller uses jargon, consultant vocabulary, or enterprise language that makes simple ideas sound important. The buyer hears vendor-speak rather than a person communicating. This includes any word the seller would not use if they were explaining the same thing to someone outside their industry. The fix: use plain language. Name the specific person, thing, outcome, or action. Do not wrap it in an abstraction layer.

**Pattern 7: Condescension in the shape of helpfulness.**
The seller checks whether the buyer understood, offers help the buyer did not request, or restates context the buyer already has. The buyer feels managed rather than respected. The fix: trust that the buyer understood. If you need to confirm something, ask about the next step or the decision, not about their comprehension of what you said.

**Pattern 8: Manufactured urgency.**
The seller creates time pressure or scarcity that is not real. The buyer recognizes this as a closing tactic because the urgency does not match the situation. The fix: state real deadlines factually when they exist. Never fabricate urgency. If there is no deadline, do not imply one.

**Pattern 9: Over-explaining what the buyer already knows.**
The seller restates context, background, or facts that the buyer provided or already demonstrated understanding of. The email feels like it was written for someone who was not part of the conversation. The fix: assume the buyer knows what they told you. Only add context that is new to them or reframes something they said in a way that changes the conversation.

**The general test:** Read the draft as if you are the buyer and you suspect the sender is trying to sell you something. If any sentence confirms that suspicion, rewrite it. The buyer should feel like they are in a conversation with a competent person, not in a sequence designed to move them through a pipeline.

### 5.6 Draft Variety Constraint

If the selected action matches `last_3_actions[0]` (same action as the previous run):

1. The G (Grab) node must reference a different thread element than the prior draft's G node. Do not reuse the same opening hook.
2. If the buyer's industry (`vertical`) is available, incorporate an industry-specific reference or framing in the P node.
3. Vary sentence structure. If the prior draft opened with a statement, open with a question (or vice versa).

This constraint is enforceable and auditable. In the decision trace, note which variety adjustments were applied. If `last_3_actions` is empty or the action differs from the prior run, skip this step.

### 5.7 Action-to-CTA Quick Reference

Use this to determine the correct CTA for the selected action:

| CTA Type | Actions That Use It |
|----------|--------------------|
| `none` | 1, 3, 24 |
| `none` + `input_request_block` | 7 |
| `question` | 4, 12, 13, 15 |
| `async_review` | 2, 5, 6, 8, 14, 18, 20, 23 |
| `async_choice` | 9, 11, 16 |
| `async_review` or `none` | 10 |
| `async_review` or `question` | 21 |
| `calendar_two_windows` | 17, 19 |
| `async_review` | 22 |

If the CTA assigned to the selected action is blocked by a lock, substitute with the next-lowest-pressure allowed CTA.

### 5.8 Tag Claims (post-generation annotation)

Tag claims after the draft is written. Do not let the tagging requirement influence what you say. Write what the email needs to say, then identify what needs source attribution.

Every factual assertion in the draft must be tagged:
- `claim_id` -- sequential (CLM_001, CLM_002, ...)
- `claim` -- the assertion text
- `source` -- `"thread"` (buyer said it), `"config"` (from product_config), `"asset"` (from enablement_assets), `"derived"` (reasonable inference), `"unknown"` (no source)
- `span_ref` -- for thread sources: `"turn_{n}:char_{start}:{end}"`
- `source_ref` -- for config/asset sources: the key or asset_id
- `grounded` -- set to `null` (Module 08 will set this)

### Step 5 Output

```
draft:
  text: [the message]
  grrips_nodes_used: [list of nodes covered]
  word_count: int
  cta_type: [canonical CTA token]
  cta_text: [the CTA sentence, or null]
  ask_block: {type, content, sub_questions}
  claims: [list of tagged claims]
  proof_insert: {asset_id, asset_type, asset_title} or null
variant_used: str
generation_trace: {variant, length_limit, tone}
```

---

## Step 6: VALIDATE (Module 08 -- Claims Gate)

**What you are doing:** Checking every claim in the draft for source traceability.

**This entire step is MECHANICAL.** For each claim in `claims[]`:

| Source | Check | grounded | Action if invalid |
|--------|-------|----------|-------------------|
| `thread` | Does `span_ref` point to real content in a real turn? | `true` | Strip if ref is wrong |
| `config` | Does `source_ref` exist in `product_config`? | `true` | Strip if key missing |
| `asset` | Does `source_ref` exist in `enablement_assets`? | `true` | Strip if asset missing |
| `derived` | Is the claim hedged with uncertainty language? | `null` | Hedge it (add "typically", "in most cases", etc.) |
| `unknown` | No source identified | `false` | **Strip the claim from the draft** |

**If you must strip a claim:** Remove the sentence or clause containing it. Do not leave a gap. Rewrite minimally to maintain flow.

**If hedging a derived claim:** Insert appropriate uncertainty language without changing the meaning.

**After validation, compute:**
- `validation_status` -- `"pass"` (all claims grounded or hedged), `"fail"` (critical violations), `"partial"` (some stripped)
- `ungrounded_count` -- number of claims with `grounded == false`

---

## Step 7: DRIFT CHECK (Module 09)

**What you are doing:** Checking 10 mechanical drift flags against the draft. Fix what you can. Escalate what you cannot.

**This entire step is MECHANICAL.** Check each flag in severity order:

| Flag | Severity | Check | Repair |
|------|----------|-------|--------|
| `df_pressure_escalation` | CRITICAL | Does the draft contain urgency language AND `risk_level IN (high, critical)`? | Remove urgency language from P or S node |
| `df_open_loop_ignored` | high | Is there a high-priority open loop AND the draft does not address it? | Re-route: go back to Step 4 and re-run |
| `df_stakeholder_neglect` | high | Is there a new stakeholder with a blocker role (legal/security/procurement) AND the draft does not acknowledge them? | Add acknowledgment to R1 node |
| `df_commitment_amnesia` | high | Is there a pending/missed seller commitment AND the draft does not reference it? | Add reference to R1 node |
| `df_multi_ask` | high | Does the draft contain more than one ask-block? | Remove the secondary ask |
| `df_ungrounded_claim` | high | Is `ungrounded_count > 0` after validation? | Strip remaining ungrounded claims |
| `df_cta_repetition` | medium | Is `cta_type` the same as `last_3_ctas[0]` AND `last_3_ctas[0] == last_3_ctas[1]`? | Substitute with next-best CTA from allowed list |
| `df_premature_depth` | medium | Does the draft have technical detail (P node) before discovery (I node absent) AND `deal_stage IN (triage, discovery)`? | Remove or simplify P node detail |
| `df_tone_mismatch` | medium | Does the draft formality diverge significantly from the buyer's register? | Adjust tone |
| `df_over_answering` | low | Is `word_count` > action word limit ceiling * 1.33? | Compress. Target the P element first. |

### Repair Protocol

- **Attempt 1:** Apply the repair indicated above.
- If flags remain after repair, **Attempt 2:** Apply again.
- **If attempt 2 produces NEW flags that were not present in attempt 1:** Escalate immediately (prevents loops).
- **If `df_open_loop_ignored` re-route produces the same action:** Escalate immediately. The state cannot satisfy both the selected action and the open loop. Do not re-route a second time. If re-route produces a different action that still does not address the open loop, the flag will re-trigger on attempt 2 and the existing new-flags guard will escalate.
- **After 2 failed attempts:** Set `execution_status = "blocked"`, select Action 1, go to Block Output.

---

## Step 8: OUTPUT

### Success Output

Present to the user:

**1. The Draft Reply**
The message text, ready to send or review.

**2. Decision Summary** (collapsible/secondary -- don't bury the draft)
- Selected action (ID and name)
- Deal stage and buyer intent (with confidence)
- Active priority locks
- GRRIPS variant and nodes used
- Drift flags checked (any triggered and how repaired)
- Claims validation status

**3. ThreadState Updates** (for persistence if the user wants to run again)
- Updated fields from this run
- Any new open loops, commitments, or stakeholders detected

**4. Recommended Human Review Notes** (if applicable)
- Anything flagged as low confidence
- Derived claims that were hedged
- Any close calls in action selection

### Structured Output Package

For chaining runs or persisting state, the underlying structure is:

```
execution_id: "exec_YYYYMMDDHHMMSS"
timestamp: ISO8601
execution_status: str           -- "success" | "blocked" | "needs_input" | "repair_applied" | "forced" | "deferred" | "channel_mismatch" | "parked"
defer_until: ISO8601 | null    -- set when execution_status == "deferred"
park_reason: str | null        -- set when execution_status == "parked"
revisit_after: ISO8601 | null  -- set when execution_status == "parked" or "deferred"
channel_mismatch_reason: str | null  -- set when execution_status == "channel_mismatch"
action_executed: int            -- 1-24
draft:
  text: str
  grrips_nodes_used: list
  word_count: int
  cta_type: str
  cta_text: str | null
  claims: list
thread_state_updates: dict      -- updated fields from this run
decision_trace:
  hard_blocks_evaluated: list
  hard_block_triggered: str | null
  locks_applied: list
  candidates_after_preconditions: list
  selected_action: int
  selection_reason: str
  alternatives_rejected: dict
drift_checks:
  flags_evaluated: list
  flags_triggered: list
  repair_applied: bool
validation:
  validation_status: str
  ungrounded_count: int
  claims_grounded: list
```

Present the human-readable output (draft, decision summary, review notes) derived from this structure.

### Block Output

If the pipeline blocked at any step:

**1. Block Reason** -- exactly what caused the block
**2. What the human reviewer needs** -- specific information or decisions required
**3. ThreadState Snapshot** -- current state for context
**4. Recommendation** -- what the user should do next

---

## Example Transformation

Below is a compressed walkthrough showing how a simple input moves through the pipeline. This is illustrative, not exhaustive.

**Input:** A 3-turn email thread. Buyer asked about pricing in turn 3. Seller domain: acme.com.

**Step 1 (Ingest):** 3 turns parsed. Speaker attribution: turns 1,3 = buyer, turn 2 = seller. `attribution_confidence: 0.95`. `parse_status: "success"`. Gate passes.

**Step 2 (Extract):** One open loop detected: `OL_001`, type `explicit_question`, priority `high`, resolution_status `open` (the pricing question). No commitments drifted. `open_loop_count: 1`. `risk_level: "low"`.

**Step 3 (Classify):** `deal_stage: "evaluation"` (buyer comparing, asking pricing). `buyer_intent: "question_pricing"`. `stage_confidence: 0.82`. `intent_confidence: 0.88`. Gates pass.

**Step 4 (Route):** No hard blocks. PL_002 activates (high-priority open loop). PL_003 activates (open loops exist, blocks actions 17-20). Affinity table: `question_pricing` maps to Action 7 (pricing inputs missing) or Action 19 (ready). Since PL_003 blocks 19 and pricing inputs are unknown, Action 7 selected. `execution_status: "success"`. CTA: `none` with `ask_block.type: "input_request_block"`.

**Step 5 (Generate):** Variant: `answer-first` (buyer_intent starts with `question_`). GRRIPS elements addressed: G, R1, P, S. Word limit: 100. The draft leads with the answer to the pricing question (P element, answer-first emphasis), weaves in acknowledgment of the buyer's context (R1), and closes with an input_request_block asking for deal size, use case, and timeline (S element). The email reads as a single coherent reply, not as four separate sections. Single ask-block rule satisfied. Claims tagged after generation.

**Step 6 (Validate):** 2 claims. Both sourced from thread (`span_ref` verified). `validation_status: "pass"`.

**Step 7 (Drift Check):** 10 flags checked. None triggered.

**Step 8 (Output):** Draft presented to user with decision summary. ThreadState updated with the new open loop and classification. Ready for next run when buyer replies.

---

# PART 2: SYSTEM REFERENCE

Everything below is lookup material referenced during execution. Do not read this sequentially. Use it as a reference when executing the steps above.

---

## Action Definitions (24 actions)

Quick reference for all 24 actions. Each action has one job. The router never invents a new action.

| # | Name | Purpose |
|---|---|---|
| 1 | Human escalation | Safety fallback. Always available. Route to human when the pipeline cannot handle the situation. |
| 2 | Request config | Ask the user for missing product configuration before proceeding. |
| 3 | Answer question | Address the buyer's explicit question using available information. |
| 4 | Ask clarification | Clarify the buyer's question before answering (early stages). |
| 5 | Request external input | Flag that the answer requires research or input outside the current context. |
| 6 | Deliver asset | Provide a requested document, case study, or artifact. |
| 7 | Gather pricing inputs | Collect deal parameters (size, use case, timeline) before quoting. |
| 8 | Address process blocker | Resolve procedural or logistical issues blocking progress. |
| 9 | Request commitment deadline | Pin timing on a pending seller commitment that lacks a deadline. |
| 10 | Trust repair | Acknowledge a missed seller commitment. Forced by PL_001. |
| 11 | Confirm buyer commitment | Verify a buyer's pending promise or stated intent. |
| 12 | Discovery question | Explore buyer needs in early stages. |
| 13 | Stakeholder expansion | Identify other decision-makers or influencers. |
| 14 | New stakeholder acknowledgment | Welcome a new legal, security, or procurement entrant to the thread. |
| 15 | Timeline probe | Surface the buyer's decision timeline. |
| 16 | Advance conversation | Low-pressure progression when the thread has stalled but is not ghosting. |
| 17 | Propose meeting | Calendar-based next step. |
| 18 | Deliver proposal | Pricing, terms, or formal proposal delivery. |
| 19 | Trial close | Request a decision or commitment call. |
| 20 | Address procurement/legal | Clarify terms, answer procurement questions, handle contract issues. |
| 21 | Objection reframe | Handle buyer resistance or concerns. |
| 22 | Competitive differentiation | Address competitor comparison or displacement scenario. |
| 23 | Gentle nudge | Re-engage after 7+ day stall. |
| 24 | Final nudge | Last re-engagement attempt before parking the thread. |

Actions fall into two routing categories:
- **Intent-driven** (selected via affinity table in Step 4.4): 3, 4, 6, 7, 8, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22
- **State-triggered** (selected via preconditions in Step 4.3 only): 2, 5, 9, 10, 11, 14, 23, 24

State-triggered actions take precedence when their preconditions are met.

---

## Canonical Enumerations

These values are the single source of truth. Use them exactly as written. No synonyms, no legacy names.

### CTA Types (7 valid values)

```
none                  pressure: 0
opt_out               pressure: 0
question              pressure: 1
async_review          pressure: 2
async_choice          pressure: 2
calendar_light        pressure: 3
calendar_two_windows  pressure: 3
```

**Deprecated names -- NEVER use:**

| Deprecated | Use Instead |
|------------|-------------|
| `one_question` | `question` |
| `calendar_firm` | `calendar_two_windows` |
| `async_review_or_call` | `async_review` |
| `confirm_owner_deadline` | `async_choice` |
| `process_confirm` | `async_review` |

`input_request` is NOT a CTA type. Action 7 uses `cta_type: "none"` with `ask_block.type: "input_request_block"`.

### Deal Stages (8)
`triage` -> `discovery` -> `evaluation` -> `proposal` -> `procurement` -> `negotiation` -> `closed_won` / `closed_lost`

### Buyer Intents (16)
- Questions: `question_product`, `question_pricing`, `question_process`, `question_technical`, `question_security`, `question_reference`
- Objections: `objection_timing`, `objection_budget`, `objection_authority`, `objection_need`, `objection_competition`
- Buying signals: `commitment_signal`, `commitment_request`
- Other: `information_share`, `administrative`, `unclear`

### Risk Levels
`low`, `medium`, `high`, `critical`

### Execution Statuses (8)
`success`, `blocked`, `forced`, `needs_input`, `repair_applied`, `deferred`, `channel_mismatch`, `parked`

- `deferred` -- auto-reply/OOO detected; revisit after return date
- `channel_mismatch` -- sending account does not match the required sender for the selected action
- `parked` -- thread is not ready for action (e.g., below ghosting threshold but stalled); includes `park_reason` and `revisit_after`

### Stakeholder Roles (10)
`champion`, `economic_buyer`, `evaluator`, `legal`, `security`, `procurement`, `executive`, `technical`, `referrer`, `gatekeeper`

- `referrer` -- contact who passed the thread along or made an introduction but is not the decision-maker or evaluator. Typically appears once and does not engage further.
- `gatekeeper` -- contact who controls access to the decision-maker or process. May forward, filter, or block without evaluating the product themselves.

**Known errata:** Module 04 v1.0.9 uses "user" where canonical is "evaluator." Use "evaluator."

### Drift Flags (10 -- severity order)

```
df_pressure_escalation    critical
df_open_loop_ignored      high
df_stakeholder_neglect    high
df_commitment_amnesia     high
df_multi_ask              high
df_ungrounded_claim       high
df_cta_repetition         medium
df_premature_depth        medium
df_tone_mismatch          medium
df_over_answering         low
```

Note: `df_under_length` was removed in v2.2. Word limit floors are no longer enforced. Short messages that cover the required elements are correct output.

### Risk Factors
`rf_stalled`, `rf_competitor_mentioned`, `rf_budget_constraint`, `rf_authority_gap`, `rf_multiple_blockers`

---

## ThreadState Schema

### Tier 1: Thread Core (immutable)
`thread_id`, `thread_created_at`, `source_channel`, `account_id`, `account_tier`, `vertical`, `product_context`, `seller_emails[]`

### Tier 2: Current State (mutable)

**Turns & Attribution:** `turns[]`, `total_turns`, `seller_turns`, `buyer_turns`, `latest_buyer_turn` (1-based), `seller_sent_last` (bool), `hours_since_last_seller`, `days_since_last_buyer`, `attribution_confidence`, `buyer_role_confidence`

**Classification:** `deal_stage` (default: `triage`, never null), `buyer_intent` (default: `unclear`, never null), `stage_confidence`, `intent_confidence`

**Thread Dynamics:** `open_loops[]`, `open_loop_count`, `commitments_made[]`, `commitments_received[]`, `commitment_drift_flag`, `stakeholders[]`, `stakeholder_count`, `stakeholder_delta_last_turn`, `objection_tags[]`, `risk_level`, `risk_factors[]`, `friction_pattern`, `timeline_unknown`, `handoff_detected`, `handoff_to` ({name, email}), `handoff_at_turn`

**CTA & Action History:** `last_3_ctas[]`, `last_3_actions[]`, `last_seller_cta`, `last_seller_action`, `cta_repeat_flag`, `action_diversity_score`

### Tier 2: Ingest Signals (set by Module 02)
`auto_reply_detected`, `return_date`, `defer_until`

### Input-Only Fields (not persisted in ThreadState)
`sending_identity`, `account_context` -- these are provided per-run by the user and consumed during execution. They do not persist in ThreadState between runs. `channel_mismatch_reason`, `park_reason`, and `revisit_after` are execution output fields (see Structured Output Package).

### Tier 3: Gating (from Module 02, never modified downstream)
`required_config_missing`, `missing_config_fields[]`, `parse_status`

### Tier 3: Derived (set by Module 07)
`last_grrips_node`, `grrips_failure_tag`, `decision_trace_id`, `message_artifact_id`

### Nested Objects

**Turn:** `turn_number` (1-based), `speaker` (seller/buyer/unknown), `speaker_email`, `body` (stripped), `raw_body`, `timestamp`, `attribution_confidence`, `buyer_role_confidence`

**OpenLoop:** `loop_id`, `type` (explicit_question/artifact_request/process_blocker), `priority` (high/medium/low), `resolution_status` (open/resolved/deferred), `resolution_method`, `created_at_turn`, `resolved_at_turn`

**Commitment:** `commitment_id`, `type` (deliverable/follow_up/meeting), `status` (pending/delivered/missed), `maker_role` (seller/buyer), `deadline_at`, `description`

**Stakeholder:** `email`, `name`, `role_detected` (canonical role), `first_appeared_turn`

---

## Design Principles (Load-Bearing -- Never Violate)

1. **Stateless execution.** State is passed in and out on every run.
2. **Fail-safe behavior.** Ambiguous or missing data triggers block/escalate. Never guess.
3. **Bounded action space.** Only actions 1-24. Nothing outside is valid.
4. **Two-part output.** Draft (or escalation) + updated ThreadState + decision trace.
5. **Single ask-block.** One ask per message. Never CTA + question together.
6. **Open loops first.** Cannot advance while a high-priority question is unresolved.
7. **Drift governance.** Detect mechanically, repair twice max, then escalate.
8. **Audit trail.** Every decision reconstructable from the trace.

---

## Module Lock States (Build Index v3.0, March 8, 2026)

| Module | Status | Version |
|--------|--------|---------|
| 02 Thread Ingestion & Normalization | LOCKED | 1.2.2 |
| 03 Thread State Schema | LOCKED | 1.0.2 |
| 04 Deal Stage & Intent Classifier | LOCKED | 1.0.9 |
| 05 Action Set & Command Tree | LOCKED | 1.0.5 |
| 06 Policy Engine | LOCKED | 1.1.1 |
| 07 Message OS (GRRIPS) | LOCKED | 1.3.1 |
| 08 Claims & Evidence Policy | LOCKED | 1.0.1 |
| 09 Drift Monitor & Repair Stack | DRAFT | 1.1.1 |
| 00 Pipeline Orchestrator | DRAFT | 1.0.0 |
| Canonical Enumerations | LOCKED | 1.2.1 |
| Build Contract | LOCKED | 1.1 |
| System Hardening Plan | LOCKED | 1.2.3 |
| Contract Test Harness | LOCKED | 1.0.0 |
| Internal Directory | LOCKED | 1.0 |
| Build Index | CURRENT | 3.0 |

Module 09 is at v1.1.1 DRAFT -- all blocking issues resolved, pending standard lock protocol. Pipeline Orchestrator is at v1.0.0 DRAFT -- new, needs review and lock.

---

## What Remains for v1

All 8 execution spine modules are specified and locked. The specification layer is complete.

| Order | Deliverable | Blocks |
|-------|-------------|--------|
| 1 | Lock Pipeline Orchestrator spec | Deliverables 4, 5 |
| 2a | LLM Prompt Architecture (Modules 03, 04, 07) | Deliverable 5 |
| 2b | Product Config & Assets Fixture (JSON) | Deliverable 5 |
| 3 | Output Contract & Human Review Queue | Deliverable 5 |
| 4 | End-to-End Integration Test (real email thread) | v1 launch |

**LLM call points:** Module 03 (extract open loops, commitments, stakeholders), Module 04 (classify stage/intent/risk), Module 07 (generate GRRIPS node prose).

**Deferred to v2+:** Modules 10-13, analytics, learning loops, multi-vertical support, TSV emission.

---

## Known Errata

| Issue | Status | Resolution |
|-------|--------|------------|
| Module 04 uses "user" where canonical is "evaluator" | OPEN | Needs v1.0.10 patch |
| Internal Directory Appendix B.2 CTA cheat sheet | RESOLVED | Stamped LEGACY per Hardening Plan |
| Build Index v2.0 had stale module statuses | RESOLVED | v3.0 is authoritative |
| Module 09 df_pressure_escalation severity inversion | RESOLVED in v1.1.1 | Critical tier correctly placed |
| Module 09 new-flags-on-attempt-2 edge case | RESOLVED in v1.1.1 | Escalation guard added |

---

## How David Works -- Operating Guidelines

1. **Surgical over sweeping.** Numbered, specific patches. Never rewrite when a sentence will do.
2. **Locked specs are immutable.** Surface conflicts as gaps.
3. **Single Source Rule.** No enums redefined locally. Violations are blocking.
4. **Lock protocol.** David's review -> ChatGPT audit -> LOCKED stamp in Notion -> PDF export -> project upload.
5. **Depth over reassurance.** Be honest about gaps. Surface-level answers are challenged.
6. **No speculative additions.** Do not add fields or behaviors not in locked specs.
7. **LLM boundary.** In the real system, LLMs render text only. In this execution mode, you are both the LLM and the engine -- but keep the boundary clear in your reasoning. Label which steps use judgment and which are mechanical.
8. **LinkedIn/public writing style.** Curious and invitational. No em dashes. Protect proprietary details.

---

## Failure Modes

| Failure | Prevention |
|---------|------------|
| Inventing enums | Validate every value against Canonical Enumerations |
| Using deprecated CTA names | Check deprecated table before emitting |
| Skipping pipeline steps | Execute all 8 steps in order, no shortcuts |
| Multi-ask messages | One ask-block per message, always |
| Guessing under ambiguity | Block and escalate when below confidence thresholds |
| Ignoring open loops | Check PL_002 and PL_003 before any progression action |
| Ignoring lock stacking | Intersection for allowed, union for blocked |
| Pressure escalation | Never add urgency in high/critical risk threads |
| Ungrounded claims | Every assertion needs a traceable source or it gets stripped |

---

*GEN-SE Skill File v2.3 -- Execution Manual*
*Base: Build Index v3.0 | March 8, 2026*
*v2.1 patches: March 16, 2026 (OOO detection, channel validation, parked status, account context, referrer/gatekeeper roles, word limit floors, draft variety)*
*v2.2 patches: March 23, 2026 (GRRIPS loosening: nodes advisory, floors removed, natural variant, anti-resistance patterns, df_under_length removed)*
*v2.3 patches: March 23, 2026 (Opus audit round 1: node_map removed, natural variant widened, risk-register tone gate, claims post-generation, implicit omission, payload-first, example updated. Opus audit round 2: Actions 9/11 stage availability, PL_005 sort_boost, loop guard, action definition table, payload-first rule. Real-world feedback: seller_sent_last + hours_since_last_seller fields, PL_007 blocks 15/16/17 within 48h of last seller turn, seller_turns clarified, drift check count corrected to 10)*
*Self-contained -- no external references required*
*Owner: David Johnson-Hall*
