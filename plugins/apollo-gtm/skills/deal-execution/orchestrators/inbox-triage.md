# Inbox Triage Orchestrator

Coordinates the pipeline skills and GEN-SE to triage an email inbox. This skill
does not parse, reason, route, compose, or polish. It tells the skills that do those
things when to run, what to feed them, and where to send the output.

---

## Configuration

All user-specific configuration (identity, triage preferences, connector status) is
read from the local config file at `~/Documents/apollo-gtm/config.yaml`. See
`utilities/local-config.md` for the full schema and read/write protocol.

**On triage start:**
1. Read the local config file (ROUTER.md should have already loaded it into session state).
2. Use `identity` for seller context (email, domains, Slack ID).
3. Use `triage_config` for volume bounds and filtering mode.
4. If the local config file is missing or unreadable, fall back to the inline defaults below.

```yaml
# Inline fallback — only used if local config file is missing.
# After first preflight, the local config file is authoritative.
seller_emails: ["{{YOUR_EMAIL}}"]
seller_domains: ["{{YOUR_SELLER_DOMAINS}}"]
internal_domains: ["{{YOUR_INTERNAL_DOMAINS}}"]
slack_user_id: "{{YOUR_SLACK_USER_ID}}"
fallback_email: "{{YOUR_EMAIL}}"

# Product context for GEN-SE (not user-specific, stays inline)
product_context: >
  Apollo.io — B2B sales intelligence and engagement platform.
  See references/ for full product context.

# Run mode (auto-detected or passed by caller)
mode: "am" | "pm"
```

---

## What This Skill Does

1. Gathers context across all available MCP connections
2. Classifies each email thread into the correct pipeline path
3. Correlates threads that reference the same deal, person, or account
4. Routes each thread through either GEN-SE (B2B sales) or the full pipeline stack
5. Enforces the message pipeline on every outgoing Slack message and Gmail draft
6. Compiles results into a structured triage summary
7. Delivers the summary via Slack DM (itself pipelined through L1-L4+)

## What This Skill Does NOT Do

- Parse email threads (that's state-extractor)
- Validate claims (that's reality-filter)
- Decide what action to take (that's bounded-action-router)
- Write messages (that's message-os)
- Polish output (that's humanizer-compressor)
- Handle B2B sales responses (that's GEN-SE)

If you find yourself doing any of those things inside this orchestrator, stop.
Load the correct skill and let it do its job.

## Run Modes

The orchestrator supports two modes. The mode determines the time window
scanned and the summary format used.

| Mode | Trigger | Window | Summary Style |
|------|---------|--------|---------------|
| AM | Cron 7:00 AM M-F or "morning triage" | ~6pm prior day to now | AM format (no "tomorrow's first 3") |
| PM | Cron 5:00 PM M-F or "evening triage" / "EOD triage" | 7:00 AM today to now | EOD format (includes "tomorrow's first 3") |

If invoked outside these windows or without a mode hint, default to PM mode
(it's the more comprehensive format).

---

## Phase 0: Read Triage Config

Before gathering any context, read the AE's triage preferences from the local
config file (already loaded into session state by ROUTER.md).

```yaml
# Values used from triage_config:
mode:                   # "all" | "sales_focused" | "b2b_only"
max_threads:            # int, default 25
max_turns_per_thread:   # int, default 10
lookback_hours_am:      # int or null (default: 13)
lookback_hours_pm:      # int or null (default: 10)
priority:               # "recency" | "apollo" | "starred"
```

If triage_config is missing or incomplete, use defaults for all missing fields.
Never prompt the AE for these values during a triage run — they are set during
preflight and changeable via "change settings."

---

## Phase 1: Context Gather

Before triaging any thread, assemble the full picture. Run these in parallel
where the tools allow it.

### 1.1 Gmail

Search for threads matching the run mode's time window. Use `lookback_hours_am`
or `lookback_hours_pm` from triage_config if set; otherwise use defaults.

**AM mode** (default lookback: 13h):
```
is:unread newer_than:{lookback_hours_am or 13}h
is:important is:unread newer_than:2d
```

**PM mode** (default lookback: 10h):
```
is:unread after:{today minus lookback_hours_pm or 10 hours}
is:important is:unread newer_than:2d
in:inbox -is:read newer_than:48h
```

Use `gmail_read_thread` to get full content for each result. For each thread,
pull only the last `max_turns_per_thread` turns (default 10). If a thread has
more turns, include the first turn (for original context) plus the last
`max_turns_per_thread - 1` turns.

Cap total threads at `max_threads` (default 25). If results exceed the cap,
apply the `priority` ordering:
- `"recency"` (default): most recent threads first.
- `"apollo"`: threads where sender appears in Apollo enrichment (Phase 1.4) first,
  then recency for the rest. Run Phase 1.4 before applying this filter.
- `"starred"`: starred/important threads first, then recency.

### 1.1.1 Triage Mode Filtering

After collecting threads, apply the `triage_config.mode` filter:

**`"all"`** — No filtering. All threads proceed to Phase 2.

**`"sales_focused"`** — Classify each thread into two tiers:
- **Full processing:** Sender/domain matches Apollo enrichment data (Phase 1.4),
  sender domain is external and not in the known vendor/notification list, or
  thread is starred/important. These get the full pipeline (Phase 2 → 4).
- **Quick scan:** Everything else. Run Phase 2 classification only (GEN-SE gate +
  SIMPLE/COMPLEX). If classified as GEN-SE or COMPLEX, promote to full processing.
  If SIMPLE, generate a one-line summary and slot into the FYI tier of the triage
  summary. No pipeline execution, no draft.

**`"b2b_only"`** — Drop threads that match ALL of these:
- All participants are on internal domains (seller_domains + internal_domains)
- OR sender is a known no-reply/system address (contains "noreply", "no-reply",
  "notifications", "mailer-daemon", or "autonotify" in the address)
- OR sender domain matches a known automated notification pattern (e.g.,
  notifications.google.com, calendar-notification, jira@, github.com)

Dropped threads do not appear in the triage summary at all. Everything else
proceeds to Phase 2 normally.

**Write triage timestamp:** After Phase 1 completes, write `state.last_triage_am`
or `state.last_triage_pm` to the local config file.

### 1.2 Google Calendar

Query `gcal_list_events` for today + next 7 days. Two purposes:

1. **Overlap detection:** Flag any meetings with people who appear in the inbox
   (match by name or email domain). These become soft constraints in L2B
   against drafting replies when a live conversation is imminent.

2. **Timing context:** Note any deadlines, demos, or deal-related meetings that
   inform urgency scoring during state extraction.

### 1.3 Slack

For any sender, deal name, or company that appears in the inbox:
- Search for their Slack channel (`slack_search_channels`)
- Read recent messages (`slack_read_channel`) for relationship context
- Check DM history if the sender is internal

This context feeds L2A (state-extractor) and L2B (constraint-first-reasoner).

### 1.4 Apollo (Optional)

> **Note:** Apollo MCP tools (`apollo_people_match`, `apollo_contacts_search`)
> are optional. Use them if Apollo is available as an MCP source in your setup.
> If not connected, skip this step — context from Gmail, Slack, and Calendar
> is sufficient to run the pipeline.

For any external sender not obviously internal:
- Use `apollo_people_match` or `apollo_contacts_search` to retrieve role,
  company, seniority, deal stage, and account context.
- If a B2B thread, this data feeds GEN-SE's `account_context` input.

### 1.5 Notion (Optional)

> **Note:** Notion MCP is optional. If not connected, skip this step.
> If connected, Notion can provide deal context, competitive intel, and
> enablement content that enriches pipeline and GEN-SE processing.

For any deal, account, or competitor that appears in the inbox:

1. **Search for deal pages:** Use `notion_search` with the account name or deal name.
   Pull deal notes, stage history, stakeholder maps, or internal commentary.
2. **Search for competitive intel:** If a competitor is mentioned in a thread,
   search Notion for battlecards, takeout slides, or competitive positioning pages.
3. **Search for enablement content:** If the thread references a product area
   (e.g., enrichment, sequences, inbound), search Notion for relevant playbooks,
   one-pagers, or talk tracks.

Notion context feeds the pipeline at two points:
- **L2A (state-extractor):** Deal notes and stakeholder maps augment the state object.
- **GEN-SE:** Competitive intel and enablement content feed the `account_context` and
  `enablement_assets` inputs, enabling grounded claims with proof points.

Do not block triage on Notion. If search returns no results or the connection
is slow, proceed without it. Notion enriches — it is never required.

### 1.6 Cross-Thread Correlation

After gathering all threads, scan for overlap before processing:

- Group threads by sender email domain
- Group threads by deal name (match against Slack channel names and calendar events)
- If multiple threads reference the same deal or person, merge their context
  into a single state object before running the pipeline. Process the most
  recent thread as primary; treat earlier threads as supplementary context.

This prevents the pipeline from giving contradictory advice on threads about
the same deal.

---

## Phase 2: Classify

For each email thread, determine which pipeline processes it.

### GEN-SE Gate

Route to GEN-SE if ALL three conditions are true:

1. **External sender** — sender domain is NOT in `seller_domains`
2. **Buyer message exists** — at least one message in the thread was written
   by someone outside the seller organization (not just outbound from the AE)
3. **B2B sales context** — any of these signals are present:
   - Subject or body contains: demo, trial, pricing, proposal, contract,
     evaluation, POC, proof of concept, ROI, decision, renewal, expansion,
     onboarding, champion, executive sponsor
   - Sender appears in Apollo as a prospect, customer, or deal contact
   - Thread originated from an Apollo sequence or outbound campaign
   - A Slack deal channel exists for the sender's company

See `orchestrators/references/classification-gate.md` for the full decision
tree and edge case table.

### Pipeline Gate

Route to the full pipeline if ANY of these are true:

- Sender is internal (domain matches `seller_domains` or `internal_domains`)
- Thread is personal, administrative, or non-sales (receipts, calendar invites,
  HR, legal, vendor notifications, newsletters, promotional)
- Thread is cold outbound with no buyer reply (GEN-SE requires a buyer message)
- Thread is consumer/personal context (not B2B)

### Edge Cases

- **Calendar invites** with external attendees: classify as pipeline unless the
  thread contains actual email replies (not just RSVP notifications).
- **Gong/call recording notifications:** classify as pipeline/document. These are
  deal intel, not threads requiring replies.
- **Auto-forwarded emails** (AE to themselves): classify as pipeline/document.
- **Notification emails** (Zoom, Miro, etc.): classify as pipeline. Check if the
  notification implies a missed event or action needed.

---

## Phase 2.5: Complexity Classification (Non-Sales Threads Only)

For each thread classified as non-GEN-SE in Phase 2, assess complexity to determine which pipeline tier to use.

**SIMPLE** — all of these must be true:
- Single actor (one sender, one recipient, no CC stakeholders)
- ≤3 turns in the thread
- No risk signals from Phase 1 context (no Slack deal channel activity, no calendar overlap with sender in next 48hrs, no competitive mentions)
- Thread type is clearly low-stakes: receipts (non-contractual), notifications, newsletters, vendor emails (non-legal, non-contractual, non-pricing), internal FYI, calendar confirmations, simple administrative requests
- No legal, compliance, financial, HR, negotiation, pricing ultimatum, competitive mention, or deadline-driven decision content in the thread body. Content exclusions and type qualifiers apply to body content only — not to footers, signatures, automated subject lines, or boilerplate text
- Sender/sender domain does not appear in Phase 1 Apollo enrichment (1.4) as a prospect, customer, or deal contact — if Apollo is not connected, this criterion is skipped

**COMPLEX** — any of these:
- Multi-actor thread (3+ participants or CC stakeholders)
- >3 turns (extended back-and-forth = accumulated nuance)
- Risk signals present from Phase 1 context
- Thread involves negotiation, conflict, sensitive topics, decision-making, or authority dynamics
- Legal, compliance, financial, or HR content detected
- Internal thread with relationship or political sensitivity
- Thread correlated with other threads in Phase 1.6 (cross-thread context = higher complexity)

**Default: COMPLEX.** When uncertain, use the full pipeline. Over-classifying wastes tokens. Under-classifying misses reasoning depth on a thread that needed it.

---

## Phase 3: Process

### 3A: GEN-SE Pipeline (B2B Sales Threads)

Load the `gense/gense.md` skill and execute the full pipeline per its instructions.

**Required config:**
```yaml
seller_emails: ["{{YOUR_EMAIL}}"]
seller_domains: ["{{YOUR_SELLER_DOMAINS}}"]
internal_domains: ["{{YOUR_INTERNAL_DOMAINS}}"]
product_context: >
  Apollo.io — B2B sales intelligence and engagement platform.
  See references/ for full product context.
```

**Optional config (pass when available from Phase 1 context gather):**
- `account_context` — cross-thread signals from Apollo (if connected) and Slack
  about other contacts at the same company
- `vertical` — buyer's industry from Apollo enrichment (if available)
- `account_tier` — from CRM/Apollo deal data (if available)

**Output handling:**
- GEN-SE produces a draft → pass through `pipeline/humanizer-compressor.md` → `gmail_create_draft`
- GEN-SE escalates → flag as ACT-tier in the summary with the stated reason
- GEN-SE emits a BLOCK → respect it, never override, flag for the AE's review

### 3B: Pipeline (Everything Else)

This pipeline applies to:
- Every non-GEN-SE email thread
- Every outgoing Slack message (DMs, channel posts, nudges)
- The triage summary itself

No Slack message or Gmail draft may be created without completing L1 through L4+.

Route to the correct tier based on Phase 2.5 classification:

#### 3B-Light: Simple Threads (Phase 2.5 = SIMPLE)

Load `pipeline/pipeline-runtime.md`. Execute L1 through L4+ per the runtime's consolidated sequence. The runtime contains all layer definitions, output schemas, truth status taxonomy, action classes, validation gates, AI-pattern lists, and failure paths.

This tier is appropriate for low-stakes threads where the runtime's reference-level instruction is sufficient: receipts, notifications, simple admin, single-actor FYI threads.

#### 3B-Full: Complex Threads (Phase 2.5 = COMPLEX)

Load the full pipeline specs for each layer. These provide the complete reasoning discipline: worked examples, failure mode taxonomies, input-type-specific handling, and detailed gate walkthroughs.

##### L1: reality-filter

Load `pipeline/reality-filter.md`. Decompose all claims from the thread and
gathered context into atomic assertions. Tag each with a truth-status from the
L1 tag set:

- `verified`, `probable`, `inferred` — safe to proceed
- `asserted`, `assumed` — hedge before proceeding
- `disputed`, `contradicted`, `fabricated` — strip before proceeding
- `unknown`, `not_verifiable` — flag, do not assert as fact

Strip or hedge unsafe claims before they reach L2A.

##### L2A: state-extractor

Load `pipeline/state-extractor.md`. Parse the full context (thread + calendar +
Slack history + Apollo data if available) into a structured state object per the
skill's output contract. Key fields for triage:

- Actors and roles
- Open requests, decisions, open loops
- Timeline and deadlines
- Urgency and tone signals
- Risk flags
- Constraints (timing, authority, reversibility)

##### L2B: constraint-first-reasoner

Load `pipeline/constraint-first-reasoner.md`. Map all constraints before action
selection:

- **Hard blocks:** authority limits, missing information, policy restrictions
- **Soft limits:** relationship sensitivity, reversibility concerns
- **Timing windows:** reply urgency, calendar overlap with sender (<48hrs = soft
  constraint against drafting a reply — the topic may be addressed live)
- **Authority boundaries:** the AE's role relative to the recipient (peer, overlay,
  manager, subordinate) — this governs register and directiveness
- **Epistemic limits:** what we don't know well enough to act on

Output a constraint map that L3 uses to eliminate invalid actions.

##### L3: bounded-action-router

Load `pipeline/bounded-action-router.md`. Select exactly ONE action class from
the bounded space after constraint elimination:

```
respond    — reply warranted, context sufficient
review     — needs AE attention, no immediate reply
wait       — ball in someone else's court
escalate   — urgent, high-stakes, or time-sensitive
document   — informational, log only
clarify    — ambiguous, need more info before acting
nudge      — stalling thread, supportive follow-up
schedule   — calendar action needed
defer      — action needed but not now (timing constraint)
none       — no valid action; flag for human review
```

If no valid action survives elimination, select `none` and flag for the AE.

##### L4: message-os

Load `pipeline/message-os.md`. Compose the message per the selected action class:

- Single-ask discipline — one ask or next step per message
- No commitments beyond what the AE has clearly authorized
- Channel-appropriate register (Slack DM to colleague differs from email to VP)
- All claims must trace to `verified`, `probable`, or `inferred` sources

##### L4+: humanizer-compressor

Load `pipeline/humanizer-compressor.md`. Polish the output:

- Remove AI-pattern language (throat-clearing, performed enthusiasm, framework seams)
- Compress to minimum effective word count
- Match the AE's natural voice for the relationship and channel
- No em dashes

Only after L4+ is complete may `slack_send_message` or `gmail_create_draft` be called.

---

## Error Handling

When any pipeline step fails or produces unusable output, the orchestrator routes the thread
to the triage summary ACT tier with a structured failure note. Failures never silently drop
threads.

### GEN-SE Failures (already documented above)
- BLOCK output → ACT tier with block reason
- Action 1 (human escalation) → ACT tier with escalation reason

### Pipeline Failures
- **state-extractor produces unusable state** (parser_confidence = low across all fields,
  or critical schema violations): Route the thread to ACT tier with note: "Pipeline could
  not parse this thread — [reason]. Review manually."
- **constraint-first-reasoner cannot produce a constraint map** (insufficient structured
  state or epistemic coverage): Route to ACT tier with note: "Insufficient context for
  constraint analysis — [missing fields]. Review manually."
- **bounded-action-router selects `none`** (entire action space eliminated by constraints):
  Route to ACT tier with note: "No valid action class — [elimination reasons]. Review
  manually."
- **message-os or humanizer-compressor fails** (composition blocked by claim-pool
  depletion or voice-match failure): Route to ACT tier with the pre-composition state
  and note: "Draft composition failed — [reason]. Thread state preserved for manual
  drafting."

### General Rule
If any pipeline step fails for any reason not listed above, route the thread to ACT tier
with the last successfully produced state object and a structured note identifying which
step failed and why. Never attempt to draft a message from a failed pipeline run. Never
silently skip a thread.

---

## Phase 4: Summarize and Deliver

### 4.1 Build the Summary

See `orchestrators/references/summary-format.md` for the exact template and
formatting rules.

Key rules:
- Header is ONE line with all stats inline
- Three tiers: ACT (requires action), WATCH (monitor), FYI (informational)
- Empty sections are omitted entirely
- Open loops listed as flat checklist (item, owner, deadline)
- PM mode includes "Tomorrow's first 3" ranked by deal risk, not recency
- GEN-SE drafts appear in WATCH with "[Draft ready]"
- GEN-SE BLOCKs appear in ACT with block reason

### 4.2 Pipeline the Summary

The summary itself is a Slack message. It must complete L1 through L4+ before
sending. Specifically:

- L1: confirm all deal amounts, dates, names, and status flags are sourced
  from confirmed data, not inference
- L2A-L3: validate the summary is safe and complete
- L4-L4+: finalize format and compress

### 4.3 Deliver

Send to the AE's Slack user ID (configured as `{{YOUR_SLACK_USER_ID}}`) via
`slack_send_message` with `channel_id` and `message` parameters.

**Fallback:** if Slack fails, create a Gmail draft to `{{YOUR_EMAIL}}`
with subject "[AM/EOD] Inbox Brief — [Date]".

---

## Hard Rules

See `orchestrators/references/hard-rules.md` for the complete list. The critical ones:

1. **No message without full pipeline.** Every Slack message and Gmail draft
   completes L1 through L4+ before touching an API. No exceptions.

2. **No emails sent.** `gmail_create_draft` only. Never `gmail_send`.

3. **No emails marked as read.** Inbox is read-only.

4. **GEN-SE BLOCKs are final.** Never override with a manual draft.

5. **Legal/compliance/financial risk threads route to ACT** regardless of
   urgency score.

6. **Single-ask discipline.** One ask per message, enforced at L4.

7. **Claims must be source-traceable.** L1 tags every claim. L4 strips
   anything ungrounded.

---

## Orchestrator vs Pipeline Skills

This table clarifies what belongs in the orchestrator versus what belongs
in the individual skills. If you're unsure where to put something, use this.

| Responsibility | Belongs In |
|---|---|
| Which MCP sources to query | Orchestrator |
| What time window to scan | Orchestrator |
| How to classify threads (GEN-SE vs pipeline) | Orchestrator |
| Cross-thread correlation logic | Orchestrator |
| Summary format and delivery | Orchestrator |
| Hard rules (drafts only, BLOCKs final, etc.) | Orchestrator |
| How to validate claims | reality-filter |
| How to structure state | state-extractor |
| How to map constraints | constraint-first-reasoner |
| How to select an action class | bounded-action-router |
| How to compose a message | message-os / GEN-SE |
| How to polish output | humanizer-compressor |

The orchestrator coordinates. The skills execute. Never collapse the boundary.

---

## Future Orchestrators

This skill is one orchestrator in a library. Other orchestrators may include:

- **deal-review-orchestrator** — deep-dive on a single deal's full context
- **meeting-prep-orchestrator** — pull attendee context and prepare a briefing
- **ad-hoc-triage-orchestrator** — process a single pasted thread or conversation
- **weekly-digest-orchestrator** — compile a weekly summary across all triage runs

Each orchestrator defines its own context gather, classification, and output
format. All share the same L1-L4+ pipeline skills.
