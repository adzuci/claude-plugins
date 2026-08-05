---
name: demo-prep-intelligence
description: Read-only demo preparation for Apollo Solutions Consultants. Turns one deal identifier - an account name, Salesforce opportunity, or Slack dealroom - into a seven-section demo prep brief or an expanded demo synthesis package, then hands off to demo-instance-configuration.
allowed-tools: AskUserQuestion, Read, Write
disable-model-invocation: true
metadata:
  author: David Johnson
  author_title: Senior Solutions Consultant, Apollo
  author_handle: johnson-hall
  author_contact_slack: U0ADXHGS8CW
  frameworks: Consulting methodology by David Johnson
  version: '1.4.0'
  layer: intelligence-readonly
  architecture: standalone
  sibling_to: deal-execution
---

# Demo Prep Intelligence

Read-only deal-context synthesis skill. One input, one output, no side effects.

## Invoking this skill

Direct invocation only - this skill does not load automatically. Pass the deal identifier in the same message:

```
/apollo-gtm:demo-prep-intelligence https://apolloio.lightning.force.com/lightning/r/Opportunity/<id>/view
/apollo-gtm:demo-prep-intelligence I want to create a tailored demo instance for this opp: <SFDC URL>
/apollo-gtm:demo-prep-intelligence prep for my AE sync on <account name>
```

Everything after the command is read as the SC's message, so Step Zero's intent detection and `SC-GUIDE.md`'s routing table work exactly as they do in conversation. Invoked with no identifier, ask for one before doing anything else.

## Purpose

Generate demo-ready deal intelligence for an Apollo SC from a single deal identifier. The base output tells the SC who they are talking to, what to show, why to show it, what to avoid, and what to ask in the first five minutes. The guided interaction layer follows the SC's real operating motion — assigned opportunity → coordinate with AE/dealroom → AE sync already on calendar → meeting evidence intake → demo — and helps the SC choose the next useful action without needing to know the underlying output modes. When the user asks for demo automation, setup prompts, talk track, or full synthesis, expand the base brief into a five-part demo synthesis package with paste-ready prompts for Apollo's in-app AI Assistant.

This skill is the read-only sibling of `deal-execution`. deal-execution is the write-capable execution system (drafts, posts, orchestrators, MCP execution). demo-prep-intelligence is the corresponding intelligence-only surface: it observes and synthesizes, but does not act.

## Architectural Position

Layer 1 of a three-layer demo automation architecture. Layer 2 is live as of 2026-07-06:

| Layer | Skill | Role |
|---|---|---|
| 1 | demo-prep-intelligence (this skill) | Read-only synthesis. Stable seven-section output contract. |
| 2 | demo-instance-configuration | Downstream consumer of the Context Center payload and/or Recommended Demo Flow, received via the `demo-prep-scratchpad.md` handoff file and/or same-session context. See "Handoff to demo-instance-configuration" below and `SC-GUIDE.md`'s "Configure the demo instance" menu option. |
| 3 | walkthrough-generation (planned) | Downstream consumer of the full brief. |

The seven-section brief is the stable Layer 1 interface for layers 2 and 3. In expanded synthesis mode, embed the seven-section brief unchanged as Part 2 rather than replacing or reordering it.

## Standalone by Design

**Standalone within its plugin family, with `deal-execution` as one named sibling dependency — revised 2026-07-28.** Every core path — intake, the seven-section brief, the synthesis package, the Context Center payload, Apollo AI prompts, the Outbound Messaging Pipeline, the Layer 2 handoff — runs entirely on what ships in this plugin. It does **not**:

- Depend on deal-execution's router, its references, or its orchestrators for any of its own generation logic
- Require anything outside this plugin to produce any of its artifacts

**The one named exception: delivery of composed messages and canvases.** Because this skill never calls a write tool (see `GOVERNANCE.md`'s Read-only bullet), anything that actually posts to Slack is either the SC acting manually or a delegation to `deal-execution`. The "Send / queue this in dealroom" and Slack Canvas paths therefore do depend on `deal-execution` being present. Two consequences worth being precise about:

- **The dependency is real, not theoretical.** The previous wording here — "requires nothing outside this plugin, everything it needs ships with it" — was flatly contradicted by those menu options, which offer the SC a path that cannot complete without a sibling skill.
- **It resolves at the merge, not before.** The agreed destination is `apolloio/claude-plugins/plugins/apollo-gtm/`, where `deal-execution` already lives, so post-merge this is simply a sibling call. Until then, if `deal-execution` isn't available in the runtime, those delivery options degrade to copyable text — which is the honest fallback, and never a reason to reach for a Slack tool directly.

Confidence tagging uses a deliberately small 3-value SC-ergonomic scale (`verified | inferred | assumed`) — see Epistemic Tagging. If the user explicitly requests strategic angle analysis or deal-execution coordination, that is an opt-in extension. In that mode, use the seven-section brief as the input to the downstream analysis; do not let downstream analysis mutate unsupported source claims.

## SC-Facing Output Rules (Hard)

> **Canonical source:** these rules are governed by `GOVERNANCE.md` (loaded unconditionally every session, never truncated). The copy below is retained for reading continuity; `GOVERNANCE.md` governs on any conflict.

These rules govern what the SC sees by default. They override any earlier convention in this file that might suggest emitting raw machine-readable state to the SC.

1. **Never show internal router YAML, orchestration state, pipeline traces, or reasoning chains as the default visible output.** YAML, router payloads, pipeline-stage logs, and intermediate state may exist internally to drive routing and composition, but they must not be the primary artifact rendered to the SC.
1. **The visible output must be human-facing.** The first thing the SC sees for any flow must be either (a) a short intake summary plus one or more directly usable artifacts (copyable message, AE-sync questions, brief, walkthrough), or (b) a prompt for the missing input the skill needs to proceed.
1. **The router selects the next move; it is not the message.** Treat the router as an internal control that picks AE sync questions vs. analyze evidence vs. build brief. Never present the router's selection as the primary deliverable.
1. **Diagnostics are opt-in.** If the SC explicitly asks "why did you pick this path", "show your reasoning", "show the router", or "show the YAML", the skill may emit a compact "Why this route" summary (3–6 lines, plain English). Only emit raw YAML, raw pipeline trace, or machine-readable router state when the SC explicitly asks for machine-readable, debug, or diagnostic output.
1. **Action-surface first.** For any flow that produces an outbound message (AE sync ask, dealroom coordination, internal escalation, customer-facing follow-up), the primary artifact must be a clean, copyable message the SC can paste, plus a small action menu — not the upstream reasoning that produced it.

**Allowed artifact class — Visible Gate Block.** A rendered, human-facing **Visible Gate Block** (see the primitive definition below) is an ALLOWED SC-facing artifact and is explicitly NOT the forbidden machine-readable state described in rule 1. It is a plain-English checklist — not raw router YAML, pipeline trace, or machine state. Rendering a Visible Gate Block never trips these rules or the Terminal Output Assertion's output-leak strip.

## Visible Gate Block (Primitive — enforcement made visible)

The skill's gates were historically *specified but not surfaced*: the model checked them internally and the SC never saw the result, so miscalibrations passed silently. The **Visible Gate Block** is the primitive that fixes this. It is defined once here and reused wherever a gate must be enforced (currently the Company + Business Understanding Gate; future gates reuse the same shape).

A Visible Gate Block is a small, rendered, human-facing artifact in **plain English** (never machine state) with exactly three parts:

1. **What was checked** — the named gate and the criteria it evaluates, in one short list.
1. **Pass / fail per criterion** — for each criterion: `✅ pass` or `❌ fail`, plus its **source** and **confidence** (`verified | inferred | assumed`). A criterion resting on `[assumed]` or `[inferred]` evidence is flagged as such even when it "passes."
1. **What happens next / what is blocked** — either "gate passed → proceeding to [next artifact]" or "gate failed → blocked; here is the Missing [X] checklist."

Rules for the primitive:

- It is human-facing prose, not YAML/JSON/machine state. It is the allowed artifact class carved out in SC-Facing Output Rules above.
- It renders **before** the artifact it gates, so the SC sees the pass/fail reasoning before the payload.
- On any failing criterion, the gated artifact is **blocked** — the block states what is missing and offers the relevant Missing-context checklist instead. Never emit the gated artifact past a failed gate.
- 3-value tagging discipline (`verified | inferred | assumed`) is used verbatim.

## Terminal Output Assertion (Primitive — last check before any SC-visible render)

The skill's render-time rules were historically *specified but not enforced at render*: the same prohibition ("don't leak YAML") was restated in five scattered places and still fired inconsistently. The **Terminal Output Assertion** is a single named check that runs immediately before ANY SC-visible render, regardless of entry path (brief, synthesis, assigned-opp, canvas, out-of-band "just post it"). It is the one place these render rules are enforced; the scattered restatements collapse into a reference to this primitive.

Run the Terminal Output Assertion on every default render. It has **three** conditions — (c) was added 2026-07-06 and this count said "two" until 2026-07-28; all three are mandatory, and (c) in particular is the one that creates the Layer 2 handoff file:

- **(a) Output-leak strip.** Strip internal machine state from default output: router/orchestration YAML, pipeline-stage labels and traces, internal state tags, and router payload. These may exist internally but must never be the artifact the SC sees by default. This single assertion is the canonical enforcement of the leak prohibition — the previously scattered leak rules now point here instead of restating it. (The Visible Gate Block is plain-English prose, not machine state, so it is unaffected by this strip.)

- **(b) Canvas prerequisite.** If the output is **canvas-shaped**, assert that `references/canvas-generation.md` is loaded AND a prior major artifact exists (brief, synthesis, or Context Center + prompts) to compile from. If either is missing, **block** the canvas render and tell the SC what is required first. This fires on ANY canvas-shaped output — including the out-of-band "just post it as a canvas" path — not only the in-flow canvas menu selection.

- **(c) Scratchpad persistence (Layer 1→2 handoff, added 2026-07-06).** If the output is a **major artifact** — the seven-section brief, the synthesis package, or a Context Center payload — write its exact content, with every `[verified]`/`[inferred]`/`[assumed]` tag intact, to `demo-prep-scratchpad.md` per `GOVERNANCE.md`'s session-scratchpad exception, before or alongside the render. This is the mandatory trigger for the write permission `GOVERNANCE.md` grants — it is not conditional on the SC asking, and it is not something the skill may skip. Skipping it means `demo-instance-configuration` has nothing to check for on its end, defeating the entire handoff.

  **Write the file directly - do not shell out first (added 2026-07-31).** The runtime's ephemeral scratchpad directory already exists; it is provided by the host, not created by this skill. Use the `Write` tool on the target path and nothing else. Do **not** run `mkdir`, test for the directory's existence, or otherwise call `Bash` to prepare for this write - a live run was observed doing exactly that, and it is both unnecessary and out of character for a skill whose stated boundary is read-only plus this one file. If the write genuinely fails because the path does not exist, say so plainly rather than shelling out to fix it.

**Constraint — diagnostics opt-in preserved.** The assertion scopes to DEFAULT renders only. It must NOT strip diagnostics the SC explicitly requested: when the SC asks "show the router", "show the YAML", "show your reasoning", or requests machine-readable / debug output (per SC-Facing Output Rules item 4 and the diagnostics-on-demand behavior), the requested diagnostic passes through unstripped. The assertion enforces the default; it never overrides an explicit opt-in.

## Outbound Messaging Pipeline (Mandatory)

> **Canonical source:** `GOVERNANCE.md` (loaded unconditionally every session, never truncated). The copy below is retained for reading continuity.

Every outbound message generated by this skill — AE sync ask, dealroom post, Slack DM, internal escalation, internal coordination draft, customer-facing follow-up — must be composed through this skill's own six-stage composition discipline before it is shown or queued.

Operational sequence applied internally to every outbound message:

1. **Parse state** — extract entities, attendees, stage, deal motion, calendar/email signals, prior promises.
1. **Filter / ground claims** — drop unsupported certainty, mark inferred vs. verified, never assert what the source data does not support.
1. **Map constraints** — read-only boundary, no-send-without-approval, audience constraint, do-not-promise constraint, dealroom destination rules.
1. **Route action** — choose AE DM vs. dealroom post vs. AE-sync question set vs. handoff to deal-execution.
1. **Compose** — draft the message for its audience: internal coordination, AE-sync asks, and internal escalations use a direct internal voice; customer-facing follow-up and prospect-facing language use a sales-appropriate voice.
1. **Humanize / compress** — polish the draft for voice, compress for length, and remove AI-sounding patterns before it reaches the SC.

Rules:

- This pipeline runs internally. Do not expose the pipeline trace, stage labels, or intermediate drafts unless the SC explicitly asks for diagnostics.
- The pipeline applies to drafts only. This skill remains read-only — composing through the pipeline does not authorize sending.
- The SC sees the final composed, humanized draft. The router payload, pipeline state, and intermediate drafts stay internal.

## Slack / Dealroom Execution Behavior

This skill is read-only and does not send, post, or DM by default. When a Slack/dealroom connector is available in the runtime (via `/deal-execution` MCP execution or another approved integration), this skill **may offer** to queue or post the composed coordination message to the active dealroom or as an AE DM. The offer must follow these rules:

1. **Approval gate is mandatory.** The skill must show the complete composed draft (and explicit destination) and ask for the SC's approval before any queue/post action. Approval is a single, explicit confirmation per message — not a standing pre-authorization.
1. **No automatic posting or DMing.** The skill must never queue, post, send, or schedule a message without an explicit per-message approval from the SC, even if the SC has previously approved similar messages.
1. **Connector unavailable → copyable text only.** If Slack/dealroom connector is unavailable, the skill must provide the message as copyable text with a clear note that posting requires `/deal-execution` (or another approved integration) and is not happening from this skill.
1. **Destination clarity.** Every offer must label the exact destination (`Dealroom: #channel` or `AE DM: AE name`) and the dealroom_status that produced that destination choice.
1. **Posting is delegated.** Even when the SC approves a post, the actual queue/post is executed via `/deal-execution` (the write-capable sibling). This skill itself does not write to Slack.

## Slack Canvas Deal Room (Optional Output Path)

After any major output is generated — the seven-section brief, the five-part synthesis package, the Apollo AI Context Center payload + demo setup prompts, the demo flow / SC walkthrough — the skill **may** offer **Build Slack Canvas deal room** as a Pick Your Path option — **changed from "must" 2026-07-28.** `SC-GUIDE.md`'s menus are bounded to the 2-4 most relevant options out of 6-7 candidates, with "Configure the demo instance (Recommended)" listed first when the gate has passed, so an unconditional "must offer" was unsatisfiable by construction. Offer it when a canvas is genuinely the useful next step for this deal; don't crowd out the recommended path to satisfy a quota. The canvas extends the skill's intelligence into Slack as a single shareable Deal Room artifact for the AE, SC, shadow SC, and any internal participants.

Canvas generation is also offered when the SC explicitly asks for a deal room, canvas, shared reference, or Slack canvas for the deal.

Canvas content compiles entirely from the current session's existing outputs and source data — deal snapshot, team roster, prospect contacts, company description, tech stack, ranked buyer pains, data duel results (if present), demo flow, meeting link, landmines, key questions, next steps, and shadow briefing (if a shadow SC is on the deal). The canvas does not introduce new source claims; it presents existing brief / synthesis content. If a section's source data is missing, render `Unknown` or omit the section — never invent content to fill the canvas.

The canvas must use **Canvas-flavored Markdown**, not Slack message Markdown. Hard rules:

- User profile cards: `![](@SLACK_USER_ID)` on its own line. Standard `<@USER_ID>` mentions do not render in a canvas.
- Channel cards: `![](#CHANNEL_ID)` on its own line. Standard `<#CHANNEL_ID>` does not render.
- Callout blocks: `::: {.callout}` ... `:::` for highlights such as the Zoom link.
- Maximum heading depth: `###`. Anything deeper is treated as plain text and breaks hierarchy.
- Tables use standard pipe syntax with `---` separator rows.
- No code blocks inside list items.
- No mixed nested list types (do not mix bulleted and numbered lists in the same nesting).
- Slack emoji codes (`:warning:`, `:large_yellow_circle:`, `:page_facing_up:`, etc.) are allowed.

Slack actions split into two classes by side-effect risk and the corresponding approval rule applies:

| Slack action | Side effect? | Approval required |
|---|---|---|
| `slack_search_users` | No | No |
| `slack_search_channels` | No | No |
| `slack_read_canvas` | No | No |
| `slack_create_canvas` | Write — **never called by this skill** | N/A — see the delegate-only rule below |
| `slack_update_canvas` | Write — **never called by this skill** | N/A — see the delegate-only rule below |
| `slack_send_message` | Write — **never called by this skill** | N/A — see the delegate-only rule below |
| `slack_send_message_draft` | Write — **never called by this skill** | N/A — see the delegate-only rule below |

**Delegate-only, decided 2026-07-28 by David Johnson (skill author) — this replaces the per-artifact approval model the four rows above used to describe.** This skill never calls a Slack write tool under any circumstance: not with approval, not per-canvas, not per-message. It **composes** canvas and message content as copyable output; posting is the SC's own action or a delegation to `deal-execution`, which carries its own approval gate. Rationale, in David's words: reframing it this way also "help[s] to conserve tokens for the larger deals," since the skill no longer carries write-orchestration mechanics it never had authority to use. **Why this was necessary:** `GOVERNANCE.md` — which governs on any conflict with this file — has always forbidden Slack writes absolutely, so the approval-gated creation path documented here was canonically unauthorized while being presented as a feature (found in a full-file audit, 2026-07-28). See `GOVERNANCE.md`'s Read-only bullet for the precise boundary.

Canvas-flavored Markdown for manual copy (or for delegation to `deal-execution`) is now the *only* output mode, connector or not — revised 2026-07-28, see the delegate-only rule above. The skill never offers to create or distribute a canvas itself, and never attempts an alternate path that bypasses that boundary. This used to be the degraded-mode behavior; it is now the standard behavior, which makes runtime connector availability irrelevant to what this skill produces.

Distribution flow after canvas creation:

1. Search for an active dealroom channel using `Slack:slack_search_channels` (and cross-check Glean Slack search). If found, propose a single dealroom post; if not, fall back to individual DMs to internal participants.
1. Identify deal participants from calendar event attendees (internal email domains only — filter prospect / external attendees out), the SFDC opportunity owner, the SC assignment, and any internal Slack users mentioned in dealroom or DM threads about the deal. Exclude the SC themselves.
1. Resolve Slack user IDs via `Slack:slack_search_users`. Surface any unresolved participants in the approval block.
1. Compose every distribution message through the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize). Role-aware shapes: AE message, shadow SC message, other internal participants, dealroom post.
1. Show the SC the full distribution plan (recipients, destination, every composed draft) and require explicit per-batch approval before any send. Approval is per-batch, not standing — every future canvas distribution requires fresh approval.
1. After approval, delegate the actual post / DMs to `/deal-execution` (or the connector's `slack_send_message` action) one message at a time and confirm each send result.

The skill must never auto-create, auto-distribute, or DM external / prospect attendees. Distribution is internal-only.

Canvas refresh flow:

1. Read the existing canvas with `Slack:slack_read_canvas` (no approval required — read-only).
1. Identify which sections need updating based on new session information; propose a section-scoped update list to the SC.
1. Update specific sections only — call `Slack:slack_update_canvas` with `action="replace"` (or the connector's equivalent) targeting individual `section_id`s. Each section update requires explicit SC approval before the call.
1. Never replace the entire canvas without explicit SC approval. Whole-canvas replacement is allowed only when the SC explicitly says "rebuild from scratch" and the skill re-shows the full new draft and destination first.
1. After updating, ask whether to re-distribute the canvas link. Re-distribution follows the same approval gate as initial distribution.

Canvas composition does not alter the read-only boundary for **any** system, Slack included — revised 2026-07-28. (This sentence previously read "for non-Slack systems," which was an implicit admission that it altered the boundary for Slack; under the delegate-only rule above it no longer does, because this skill never calls a Slack write tool.) The composed canvas writes nothing to SFDC, Notion, Google Drive, Gmail, Calendar, Slack, or anywhere else. The canvas is a snapshot — it does not auto-refresh as deal context evolves.

The detailed canvas workflow, structure template, distribution sequence, approval checklist, and tool dependency table live in `references/canvas-generation.md`.

## When to Use This Skill

- An SC needs to prepare for a demo or technical call
- An opportunity has just been assigned and the SC needs an AE-sync plan before customer prep
- The AE sync, customer demo, or technical call is already on calendar and the SC needs Gmail/Calendar alignment before questions or demo setup
- The SC needs a copy-paste internal message for the AE or active dealroom to coordinate demo prep
- The SC has an AE-sync, discovery, demo, or technical-call transcript/link from Gong, Apollo, Granola, Zoom, or another meeting system and wants it analyzed before building the demo
- Someone asks "what should I show [account]?" or "what do we know about [account]?"
- Prep for a Stage 3 call, technical win review, or pre-demo internal sync
- Anyone asks for deal context before a customer-facing meeting
- The user asks for Apollo AI setup prompts, demo automation prompts, a talk track, SC walkthrough, or a full demo synthesis package
- The SC returns later in the deal and asks to refresh context, adjust for a new audience, respond to a new competitor, prep a post-demo debrief, or generate trial setup prompts

## When NOT to Use This Skill

- The user wants to send, post, or update anything in a system — use deal-execution
- The user wants customer-facing outreach or follow-up drafted — use deal-execution
- The user wants pipeline inspection, deal review, or stage validation — use deal-execution
- No deal identifier is provided

## Operating Boundaries

> **Canonical source:** the read-only boundary is governed by `GOVERNANCE.md` (loaded unconditionally every session, never truncated). The copy below is retained for reading continuity.

- **One input**: a deal identifier — account name, SFDC opportunity name, or Slack dealroom/channel name.
- **Canonical outputs**: either a structured seven-section demo prep brief or the five-part synthesis package, selected by the user's ask. Lifecycle outputs such as Assigned Opp Intake, AE Sync Prep, refresh summaries, debrief prep, and trial planning extend from that contract without replacing the seven-section brief.
- **Read-only**: never write to Salesforce, Slack, Gong, Glean, Notion, email, CRM, the Apollo product, or any real business system while executing this skill. Single narrow exception: a session-scratchpad handoff file for `demo-instance-configuration` - see `GOVERNANCE.md` for the full rule (scratchpad-only location, overwritten each run, never SC-facing, no other exceptions).
- **Calendar/email read-only**: when Gmail with Calendar is connected, the skill may search calendar events and email threads to align meeting context, attendees, agenda, and recent customer/AE communications. It must never draft, send, update, RSVP, reschedule, or modify calendar/email from this skill.
- **Internal coordination drafts allowed**: the skill may generate copy-paste draft text for AE sync requests or active dealroom coordination, but it must label the text as a draft and never send, post, schedule, route, or update anything.
- **No customer-facing outreach, routing, pipeline updates, or execution.**
- **Canonical rebuilds are full rebuilds**: when the skill queries source systems, rebuild the brief from currently available data rather than silently patching an old artifact.
- **Contextual refreshes are allowed inside the current conversation**: when the SC provides new call notes, Slack excerpts, data test results, or attendee changes, merge that user-provided context into the current brief with explicit source labels and a short change summary. This is not persistent storage and does not replace a source-backed full rebuild. Layer-2/Layer-3 consumers must always be passed a brief whose user-provided claims are source-labeled (`Source: User-provided ...`) and confidence-tagged so downstream skills can decide whether to trust them.
- **Never hallucinate.** Unknown is better than confidently wrong.

## Required References

Load these bundled references on demand. `SC-GUIDE.md` is the interaction layer. SKILL.md is the generation contract. References hold operational detail.

| Reference | When to load |
|---|---|
| `GOVERNANCE.md` | **Every session, load unconditionally — never truncate.** Non-negotiable governance backbone (SC-Facing Output Rules, Outbound Messaging Pipeline, read-only Operating Boundaries). This is the first governance-only file in the skill; any router or context-loader must load it in full and must never conditionally skip or truncate it. |
| `SC-GUIDE.md` | Every session. Load first (after `GOVERNANCE.md`). Controls interaction flow, intent detection, and next-step menus. Read only the relevant section after routing; lifecycle templates live in `references/deal-lifecycle-support.md`. |
| `references/output-template.md` | Every run. Defines the exact seven-section brief format and formatting rules. |
| `references/synthesis-template.md` | When the user asks for full synthesis, talk track, Apollo AI prompts, demo automation, or setup walkthrough. |
| `references/apollo-ai-prompt-patterns.md` | When generating the Apollo AI Context Center payload, Apollo AI demo setup prompts, or trial setup prompts for the in-app AI Assistant. |
| `references/data-sources.md` | **Every run, load unconditionally before any Salesforce/Glean/Snowflake query is issued — this is not a conditional reference like the entries below it.** Contains the Glean query pattern, the SFDC Field Dictionary, the Provenance Guard, and the source priority order. Skipping this file is a confirmed, real cause of incomplete or wrongly-asserted SFDC data — e.g. asserting "no economic buyer identified" when the value was actually present but never checked against this file's Field Dictionary, because this file was never loaded in the first place. |
| `references/capabilities-map.md` | When mapping pain to Apollo capabilities, decision criteria, or demo flow. |
| `references/competitive-positioning.md` | When any competitor is named or suspected in the deal data. |
| `references/technical-blockers.md` | When CRM, email, security, migration, integration, or technical feasibility appears in the data. |
| `references/deal-lifecycle-support.md` | When the SC asks for assigned-opportunity intake, AE-sync prep, internal AE/dealroom coordination, transcript or call-link analysis, refresh, audience adjustment, competitive repositioning, post-demo debrief, trial success criteria, or mid-deal evolution support. |
| `references/canvas-generation.md` | When the SC selects **Build Slack Canvas deal room** from a Pick Your Path menu after a major output (brief, synthesis, Context Center + prompts, demo flow), or explicitly asks for a deal room, canvas, shared reference, or Slack canvas. Defines compilation, Canvas-flavored Markdown rules, distribution logic, approval gates, and refresh flow. |

Context-load discipline: load only the references whose trigger condition fires. In particular, do not load `references/synthesis-template.md` or `references/apollo-ai-prompt-patterns.md` for a brief-only request. Load `references/competitive-positioning.md` and `references/technical-blockers.md` only when their trigger keywords or signals appear in source data. Load `references/canvas-generation.md` only when the SC selects the canvas path or explicitly asks for a deal room / shared Slack reference.

## Calendar + Gmail Alignment Gate

When the SC says an AE sync, customer demo, technical call, follow-up demo, or prep meeting is already scheduled, run a read-only Calendar + Gmail alignment check before generating AE-sync questions, a full brief, a demo story, Context Center payload, or Apollo AI prompts.

Use the connected Gmail with Calendar source when available:

- `search_calendar` to find the relevant event, attendees, time, title, description/agenda, conferencing link context, and any clue about meeting objective.
- `search_email` to find recent scheduling, agenda, customer, AE, and stakeholder threads related to the account, opportunity, meeting title, attendees, or customer domain.

Use the standard Calendar/Gmail alignment status taxonomy: `found | partial | not_found | unavailable`. Use `found` when both calendar and email return relevant context, `partial` when only one returns useful context, `not_found` when the connector searched successfully but nothing matched, and `unavailable` when the connector is disconnected, blocked, or errors. If the connector is unavailable, record `calendar_email_alignment.status: unavailable` and continue with a caveat. Do not invent event context from SFDC alone. Calendar/email evidence is not a replacement for SFDC, Slack, Gong, or transcript evidence; it is an alignment layer that confirms who is meeting, why, when, and what has recently been communicated.

The alignment output should surface:

- matched calendar event(s), date/time, attendees, and meeting type;
- recent relevant email thread signals, including agenda, prep asks, commitments, attachments, or open questions;
- mismatches between calendar, SFDC, Slack, and email (wrong attendees, unclear objective, stale stage, missing AE, unexpected customer stakeholders);
- what the SC should ask the AE because of those mismatches.

Do not produce AE-sync questions or Apollo AI setup prompts for an already-scheduled meeting without either running this alignment check or explicitly stating that Gmail/Calendar was unavailable.

**The four statuses are exhaustive, and every one of them requires an attempt — added 2026-07-30, confirmed necessary live.** `found | partial | not_found | unavailable` is the complete set. **`not run`, `skipped`, `not performed`, and any equivalent are not valid statuses** — there is deliberately no state meaning "I didn't try." Two consequences:

- **`unavailable` requires a real attempt that failed.** It means a tool was invoked and errored, or the connector genuinely isn't present. It does not mean the search was never attempted. If you haven't tried, you don't yet know which status applies.
- **The trigger is the meeting existing, not who mentioned it.** This gate fires whenever the meeting is already on calendar (see Workflow step 7), including when *you* discovered it from SFDC rather than the SC stating it.

**Only the SC may grant a caveat — never yourself.** On `not_found` or `unavailable`, call `AskUserQuestion` (per the Menu Presentation Contract) offering: **"Supply the details"** (the SC pastes attendees/agenda/timing directly) or **"Proceed with caveat"** (recorded in the Visible Gate Block as `proceeding with caveat` for this gate). Do not record a caveat on your own initiative, and do not continue past this gate on the assumption the SC would have waived it. A caveat requires a real attempt *and* a real answer.

**Why this rule exists.** A live run (2026-07-30) rendered *"Calendar + Gmail alignment: not run — proceeding with caveat (no calendar/email search performed this session)"* and then generated a full Context Center payload plus four Apollo AI prompts. Three things went wrong at once: a status outside this taxonomy was invented, the caveat was self-granted without asking, and the anti-pattern immediately above was tripped. The meeting in question was a CEO-feedback call on the deal's own close date — precisely the case where knowing the real attendee list and the last email exchange matters most. Note also that the run's own phrasing, "no calendar/email search performed this session," is ambiguous between *couldn't* and *didn't*; had the connector actually been unavailable, `unavailable` was already permitted and would have been correct.

## Company + Business Understanding Gate (Mandatory)

The Apollo AI Context Center is **upstream** of how Apollo AI interprets every prompt. It is not a deal-prompt scratchpad — it calibrates Apollo AI on **the prospect company and their business**: what they sell, who they sell to, how they go to market, and how they win. Generating a Context Center payload from deal mechanics alone (pain points, competitors-against-Apollo, AE notes) produces a generic or fictional company profile and contaminates every downstream prompt.

Before producing any Apollo AI Context Center payload, Apollo AI prompt, or trial setup prompt, the skill must pass this gate.

### SFDC account identity cross-validation (run first)

Before any business-understanding research begins, run a lightweight identity check to confirm the SFDC account actually matches the deal in front of you. A wrong-account resolution poisons the entire chain — Snapshot → business understanding → Context Center → canvas → Run Sheet — and the error compounds silently (the Intiveo / Fatigue Science case). This is cheap insurance against the most expensive failure mode.

Cross-validate the resolved SFDC account against at least two independent signals:

- **Email domain** — do the primary contact / attendee email domains match the account's website domain? A mismatch (e.g. resolved account `fatiguescience.com` but every attendee is `@intiveo.com`) is a hard stop.
- **Gong recap** — does the most recent Gong call recap name the same company, product, and people as the resolved account? Company/product drift is a red flag.
- **Notes / dealroom** — do the SFDC notes or the dealroom channel name reference the same account?

If the signals agree, proceed. If any signal contradicts the resolved account, **stop and surface the conflict to the SC** ("the SFDC account resolves to X but the attendees / Gong / dealroom point to Y — confirm which account before I continue") rather than silently building on the wrong account. This is a read-only check; it never writes to or reassigns the SFDC record.

### What "enough business understanding" means

The skill must have grounded answers — from sources, not invention — for at least:

1. **What the prospect company does** — offering, product/service, business model.
1. **Who the prospect sells to** — their customers, ICP/target accounts, buyer personas, segments, geographies.
1. **How they go to market** — outbound, inbound, PLG, channel/reseller, hybrid; sales motion if visible.
1. **What problems they solve for their customers** — buyer pains *their* buyers have, outcomes *their* buyers want.
1. **Their value proposition / positioning** — how they describe themselves, what is differentiated, any unique characteristics.
1. **Their competitive context** — primary competitors *in their market* (not just competitors against Apollo), category language they use.
1. **Social proof** — verifiable customers, case studies, logos, metrics — only if directly attested by the company or a credible public source.
1. **CTA + demo objective** — split into two distinct concepts that were previously conflated:
   - **8a. Prospect's CTA** — the prospect company's call-to-action to their own buyers: what the prospect asks their customers, leads, or prospects to do next in the prospect's own sales cycle. This is a *company-profile* fact about how the prospect goes to market, and it belongs in the Context Center alongside items 1–7.
   - **8b. SC's demo objective** — what *this* deal's demo is supposed to prove or move the buyer toward. This is deal-specific calibration only and must NOT enter the Context Center company profile.
   - **Validation:** If the CTA mentions Apollo, the demo, the trial, or what the prospect should evaluate, it's wrong — that is the SC's demo objective (8b), not the prospect's CTA (8a). Move it to Deal-specific calibration notes.

Items 1–7 plus 8a are about the prospect's business. Item 8b is the deal-specific calibration. The Context Center payload must be primarily 1–7 and 8a, with 8b as a smaller calibration block, not the inverse.

### Sources for business understanding (use in this order)

1. The prospect's **own website** (homepage, /product, /customers, /pricing, /about, blog, careers) for offering, ICP signals, value prop, social proof, and category language.
1. **SFDC** account record (Description, Industry, Segment, AE/SC notes) and **Glean** for any internal account briefs, prior decks, or research docs.
1. **Slack dealroom** and **Gong** for buyer-language framing of their own business when stakeholders describe it.
1. **Lightweight public web research** — recent press, G2/Capterra category, LinkedIn company snapshot, news, funding — only as needed to fill gaps.
1. SC-provided context when the SC has direct knowledge of the account.

Internal deal evidence outranks public research when they conflict; surface conflicts in Open Questions or Missing Business Context (see below).

### Gate behavior

Run the gate any time the skill is asked to produce, refresh, or accompany an Apollo AI Context Center payload, demo setup prompts, or trial setup prompts (standalone, after a brief, inside synthesis mode, or via Pick Your Path). Steps:

1. Build a `business_understanding` object covering items 1–7 above, each with a source label and confidence tag (`[verified] | [inferred] | [assumed]`). `[assumed]` is not enough on its own for any field that will appear in the Context Center.
1. If any of items 1–6 are `Unknown` or only `[assumed]` after running available sources, **stop and either run additional research or emit a Missing Business Context checklist** (see No-Invention Rule below). Do not fill with plausible generic content.
1. Only after items 1–6 are at least `[inferred]` with a real source, generate the Context Center payload using the Context Center Field Mapping Template (see "Context Center Field Mapping" below).
1. Item 7 (social proof) is optional — include only if `[verified]` from the company's own materials or a credible public source. If unverifiable, omit and note in Missing Business Context.
1. Item 8 (deal-specific calibration) is rendered as a **separate, smaller section** at the end of the payload, not as the body.

### No-Invention Rule (hard)

The skill must never invent or backfill any of the following:

- A fictional company offering, vertical, ICP, persona, customer list, competitor, metric, case study, award, or proof point.
- A "plausible" company description when the website was not fetched or the account is genuinely unknown.
- An unrelated example company in place of the actual prospect (e.g. describing a generic SaaS company when the prospect sells healthcare services).
- Competitor lists copied from Apollo battlecards as the prospect's *own* market competitors.
- Generic SaaS pain language ("manual processes", "lack of visibility") when the prospect's actual buyer pains are unknown.

If the gate fails — required business understanding is not grounded — the skill must do one of:

- **Run research now** (website fetch + targeted web search + Glean account search) and re-evaluate the gate.
- **Emit a Missing Business Context checklist** instead of a Context Center payload, listing the specific fields that are unknown and the questions or sources needed to resolve them. The checklist is itself a useful artifact: the SC can answer it inline, paste content from the website, or hand it to the AE.

Producing a Context Center payload with `[assumed]` or invented business facts is a failure mode, not a fallback.

### Missing Business Context Checklist (artifact)

When the gate fails and research cannot close the gap in-session, render this artifact instead of a payload:

```markdown
## Missing Business Context — cannot generate Apollo AI Context Center payload yet

Apollo AI's Context Center calibrates Apollo AI on the prospect's business. Before pasting any payload, we need grounded answers to the following. The Apollo Context Center UI groups fields under non-editable section headers (Overview, Key benefits & outcomes, Unique characteristics, Other details). Confirm with the AE, paste from the prospect's site, or let me run research.

- Overview (section header — fill the editable subfields below):
  - Company domain: [Unknown — paste or confirm]
  - Company name: [Unknown]
  - Offering — what [Account] does (offering, business model): [Unknown]
  - Customer profile / ICP — who [Account] sells to (incl. primary buyer personas / titles): [Unknown]
- Key benefits & outcomes (section header — fill the editable subfields below):
  - Pain points [Account]'s buyers have (in their words): [Unknown]
  - Value proposition / how [Account] describes themselves: [Unknown]
- Unique characteristics (section header — fill the editable subfields below):
  - Advantage over competitors — how [Account] frames their advantage in their market: [Unknown]
  - Primary competitors in [Account]'s market (not Apollo competitors): [Unknown]
  - Social proof / named customers / case studies (only if verifiable): [Unknown]
- Other details (section header — fill the editable subfield below):
  - CTA — the prospect's call-to-action to their own buyers (NOT the Apollo demo objective, which is deal-specific calibration): [Unknown]

Sources I will use if you say "go": prospect website, Glean, SFDC account record, Slack dealroom, Gong, lightweight web search.
```

The checklist is allowed to leave fields `Unknown`. It must not be filled with invented content to look complete.

### Context Center Validation Checklist (pre-prompt)

Before producing **any** Apollo AI prompt (standalone or inside synthesis), the skill must verify the just-drafted Context Center payload satisfies all of:

- [ ] Payload follows the observed UI hierarchy: Overview → Key benefits & outcomes → Unique characteristics → Other details (with Additional information only used as a paste target when the UI exposes an editable body field under it).
- [ ] Section headers (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information) are rendered as headers above their child fields and contain no body text.
- [ ] Cancel / Save are not present as fields; they are UI controls only.
- [ ] Company domain and Company name (under Overview) are present and verified.
- [ ] Offering (under Overview) / what the company sells is grounded in the prospect's own words or a cited source.
- [ ] Customer profile (under Overview) describes *the prospect's* customers (not Apollo's).
- [ ] Pain points (under Key benefits & outcomes) describe *the prospect's buyers'* pains (not Apollo's pitch).
- [ ] Value proposition (under Key benefits & outcomes) is the prospect's positioning, not generic SaaS language.
- [ ] Advantage over competitors (under Unique characteristics) reflects the prospect's framing in their market.
- [ ] Primary competitors (under Unique characteristics) are competitors in the prospect's market, not Apollo battlecard competitors.
- [ ] Social proof (under Unique characteristics) is omitted unless verifiable.
- [ ] CTA describes the prospect's call-to-action to their own buyers, not the Apollo SC's demo objective. If the CTA mentions Apollo, the demo, or the trial, move that content to Deal-specific calibration notes. CTA is rendered as the editable child field under Other details (not as a top-level field and not as a section header).
- [ ] Every claim has a source label and confidence tag; no `[assumed]` content in the company-profile section.
- [ ] Deal-specific calibration is a clearly separated section, not the body of the payload, and is not forced into any UI field unless a visible editable Additional information / account-specific / demo-context field exists and the SC has confirmed scoping. Otherwise it is delivered as a separate note for the SC to keep outside the global Context Center.

If any checkbox fails, do not emit prompts. Either revise the payload, run more research, or emit the Missing Business Context checklist.

### Mandatory Visible Gate Block before the Context Center payload

The Business Understanding Gate is enforced through a **Visible Gate Block** (see the primitive definition near the top of this file). This is a HARD precondition: **no Apollo AI Context Center field may be composed, and no Context Center payload may be rendered, until the Visible Gate Block has been emitted and every criterion passes.** An internal-only check is not sufficient — the pass/fail reasoning must be surfaced to the SC first. This is the fix for the highest-severity live-demo trap: a silently miscalibrated Context Center produces prospect-facing Apollo AI output that is wrong in front of the buyer, and a dry-run does not reliably catch it.

Emit the Visible Gate Block with these criteria, each carrying source + confidence (`verified | inferred | assumed`):

1. **What the prospect company does** (offering / business model) — from prospect / public / company-grounded sources.
1. **Who the prospect sells to** (ICP / buyers) — prospect-grounded.
1. **How they go to market** — prospect-grounded.
1. **Buyer pains their customers have** — prospect-grounded.
1. **Value proposition / positioning** — prospect-grounded.
1. **Competitive context (in their market)** — prospect-grounded.
1. **Social proof** — verifiable only, else omitted (a clean omission passes).
1. **CTA (8a) + demo objective (8b) correctly separated** — 8a (prospect's CTA to their own buyers) is a company-profile fact; 8b (Apollo demo objective) is deal-specific calibration and calibrates ONLY 8b. If the CTA field contains the Apollo demo objective, this criterion **fails**.

Gate rules:

- Criteria **1–7 and 8a must be grounded in prospect / public / company-grounded sources.** Deal evidence (AE notes, SFDC pain fields, competitors-against-Apollo) may calibrate **only 8b** — it must never be the source for the company profile.
- If any criterion fails or rests on `[assumed]` company facts, the gate **blocks**: emit the Missing Business Context checklist instead of the payload. Do not render a payload past a failed visible gate.
- The Visible Gate Block renders **before** the field-mapped payload on every path that produces a Context Center payload (standalone, inside synthesis, or via Pick Your Path). It is not merely an internal precondition. See `references/apollo-ai-prompt-patterns.md` Step 0 for the payload it gates, and `SC-GUIDE.md` for how the interaction layer surfaces it.

## Input Contract

Single input: a deal identifier string. Examples:

- Account name: `Collage Group`
- SFDC opportunity name: `Keeper Security - Apollo Pro Q2`
- Slack dealroom: `#deal-thredd-johnson` or `dealroom-thredd`

If multiple likely deals match the input, stop and ask the user to choose before proceeding. Do not guess.

## Step Zero — Configuration Fast Path

**Added 2026-07-10. Design sign-off confirmed via Granola ("Standup - Tailored Demo Process," 2026-07-08) — David: "Yep. Yep. I think that's a good idea," also agreeing the narration problem is real ("it's too much to digest").**

**Two ways into the fast path — an explicit signal skips the question entirely; an ambiguous one asks it. Gating this to assigned-opportunity intent alone would miss the actual common phrasing (e.g. "create a tailored demo instance," "configure the demo instance for [account]," "set up a demo instance for [account]") — that phrasing doesn't match any assigned-opportunity intent trigger below, so it would never reach this section at all if the question were the only door in.**

1. **Explicit demo-configuration intent (checked first, independent of assigned-opportunity intent) — go straight to the "Skip to demo configuration" sequence below, no question asked.** Detect this when the SC says any of: "create a tailored demo instance," "configure the demo instance," "set up a demo instance," "build the demo instance for [account]," "configure a tailored demo for [account]," or similarly names demo-instance configuration as the actual goal rather than AE-sync prep. This is already unambiguous — asking "prep for AE sync or skip to config?" here would itself be the wasted turn Step Zero exists to remove.
1. **Assigned-opportunity intent, otherwise ambiguous (see the intent triggers under the Router Default Flow below) — ask one bounded question via `AskUserQuestion`** (per the Menu Presentation Contract), before running any part of that flow:
   - `question`: "Are you going through this to prep for an AE sync, or just to get to headless demo configuration?"
   - `header`: "Fast path?"
   - Options: **"Full AE-sync prep"** (the existing flow below, unchanged — intake summary, copyable message, AE-sync questions, Pick Your Path menu) / **"Skip to demo configuration"** (skip that narration; still do the real work, then hand off).

**On "Skip to demo configuration," the exact sequence to run — this replaces the Pick Your Path menu's role of resolving what gets built, so it must be explicit, not implied:**

1. Skip the Assigned Opportunity Router Default Flow's visible narration entirely — no intake summary, no copyable AE/dealroom message, no rendered AE-sync questions, no Pick Your Path menu.
1. Run the full Workflow below (source searches, claim normalization, capability mapping) through Step 13. This produces the seven-section brief, which carries the Recommended Demo Flow as one of its sections (a byproduct of the brief, not a separate generation step — see "Handoff to demo-instance-configuration" below). **Note on the gate — corrected 2026-07-28:** this step does *not* run the Company + Business Understanding Gate. Earlier wording here said it "passes the gate along the way," but Workflow steps 1-13 contain no such gate; it is scoped to "before producing any Apollo AI Context Center payload, Apollo AI prompt, or trial setup prompt" and therefore fires inside item 3's Context Center branch below. On the no-Context-Center branch the gate legitimately never runs, and nothing should claim it did.
1. **Immediately after the brief exists, ask the Context Center readiness check — the same question already defined in "Handoff to demo-instance-configuration" item 1** ("Before we proceed with generating the tailored demo org, will you want to populate the AI Context Center too? If so, I'll synthesize the prompts for that now."). This is the one real fork the Pick Your Path menu used to resolve (brief alone vs. brief + Context Center), so the fast path still has to ask it — it is a decision point, not narration, and skipping it would silently pick one branch on the SC's behalf.
   - **If yes:** run the Context Center payload flow (Context Center Validation Checklist, its Mandatory Visible Gate Block, then the payload itself).
   - **If no:** proceed with the brief and its Recommended Demo Flow section alone — a legitimate, narrower handoff (sequence staging only), not a fallback or an error.
1. If any gate fails along the way (Company + Business Understanding Gate, Context Center Validation Checklist), render the Visible Gate Block and the relevant Missing-context checklist as usual, and stop there — a failed gate is real, necessary output, not narration, and this fast path never suppresses it.
1. Satisfy the Terminal Output Assertion's scratchpad-persistence condition (c) for whichever artifact(s) actually exist at this point (brief alone, or brief + Context Center payload).
1. Close with a short, terse note that the artifact is built and saved — not the full narration — and rely on the existing "Same-session continuation" handoff already described under "Handoff to demo-instance-configuration" below (the scratchpad file and this conversation's context are already what `demo-instance-configuration` needs; no new invocation mechanism is required here).

**On "Full AE-sync prep," or if this question hasn't been asked yet and intent is ambiguous:** proceed exactly as documented in the Router Default Flow below — unchanged.

**Ask this once per session, not on every turn.** If the SC already answered this earlier in the same conversation, don't ask again — the earlier answer keeps governing unless the SC explicitly says otherwise.

## Assigned Opportunity Router Default Flow

This section is mandatory and overrides any default that would build a brief or synthesis package first. It is the active interaction model for assigned-opportunity intent.

For assigned-opportunity / AE-sync prep intent, the skill internally builds a router payload (YAML) to choose the next move, but the **visible output** the SC sees is a clean action surface — not the YAML. The router selects; the SC reads a copyable message, the AE-sync questions, and a Pick Your Path action menu.

**Intent triggers.** Detect this flow when the SC says any of: "assigned opp", "new opp", "just got assigned", "I picked up [account]", "prep for AE sync", "I'm the SC on [deal]", "got pulled into [deal]", or provides a deal identifier with no other qualifier in a context where AE-sync prep is the obvious next step.

**Hard rule for assigned-opportunity intent.** When this intent is detected:

1. **Do not** start by building the seven-section brief.
1. **Do not** start by building the five-part synthesis package.
1. **Do not** generate Apollo AI prompts, walkthroughs, talk tracks, demo flows, or demo stories yet.
1. **Do not** render the internal router YAML, pipeline trace, or routing reasoning as the visible output.
1. **Do** compose the outbound coordination message through the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize) before it appears on screen.
1. **Do** lead the visible response with a short intake summary, the copyable AE/dealroom message, recommended AE sync questions, and the Pick Your Path action menu — **unless Step Zero (above) has already run and the SC selected "Skip to demo configuration," in which case Step Zero's own sequence governs instead and this rule does not apply.** Step Zero runs *before* this flow and takes precedence over it, the same direction as Workflow Step 0 already establishes for this whole Router Default Flow relative to the base Workflow.

**Internal vs. visible.** The skill resolves the account, runs the dealroom search, and selects the next move via an internal router payload. The router payload is a possible internal answer, not the SC-facing artifact. It must not be rendered to the SC by default.

Internal router payload (kept off-screen by default) must include, at minimum:

- `route: assigned_opp_router`
- `account` and `opportunity` (or `Unknown`)
- `dealroom_search`: `status` (`found | not_found | ambiguous | unavailable`), `candidate_channels`, `destination_reasoning`
- `coordination_draft`: `destination`, the composed `draft_text` (post-pipeline), and the six `required_asks` (blockers, buyer audience, commitments, success criteria, next step, transcript/call link)
- `pick_your_path`: 2–4 bounded options
- `read_only_boundary: no_send_no_post_no_update`

This payload exists to drive routing. It is not what the SC reads.

**Visible flow (in order, this is what the SC sees):**

1. **Step 1 — Short Intake Summary.** A compact 4–8 line summary covering: account / opportunity, AE / SC, stage / ARR / close date when known, and dealroom status (`found | not_found | ambiguous | unavailable`) with the candidate channel(s) if any. No raw fields; no YAML; no router payload. Plain English.

1. **Step 2 — Copyable Message to AE / Dealroom.** A clean, ready-to-paste Slack-native message under a heading titled exactly `## Copyable Message to AE / Dealroom`. The message is composed through the Outbound Messaging Pipeline (see "Outbound Messaging Pipeline" above) — state-parsed, claim-filtered, constraint-mapped, routed, composed, and humanized — before it is shown. The block must:

   - Label the destination explicitly: `Destination: Dealroom #channel` or `Destination: AE DM — AE name`.
   - State the dealroom search status that produced that destination.
   - Render the message body inside a single fenced code block so the SC can copy it cleanly.
   - Cover all six required asks (blockers, buyer audience, commitments, success criteria, next step, transcript/call link) inside the body.

1. **Step 3 — Recommended AE Sync Questions.** A short, scannable list of AE-sync questions the SC should ask, grouped or flagged by lens (blockers, technical feasibility, sales process, demo story). Heading: `## Recommended AE Sync Questions`. This is the default recommended next action and must be present alongside the copyable message — not buried under a menu choice.

1. **Step 4 — Pick Your Path (action menu). This is the terminal step of the default response.** Immediately after the message and questions, present a bounded 2–4 option action menu and then **STOP the response and wait for the SC's selection**. Heading (as a lead-in line): `## Pick Your Path`. **Render this menu through the Menu Presentation Contract (see below): call the `AskUserQuestion` tool so each option appears as a clickable button — do NOT print the options as a Markdown list, and do NOT continue past this point into a brief, Context Center, or any other action on your own.** Default options (label exactly):

   - **Send / queue this in dealroom** — only offered when a Slack/dealroom connector is available; on selection, the skill must re-show the complete composed draft and ask for explicit per-message approval before any queue/post is delegated to `/deal-execution`. Never auto-posts.
   - **Revise message** — adjust tone, length, destination, or specific asks; recompose through the pipeline and re-show.
   - **Analyze meeting transcript / recording** — ask for or analyze a Gong / Apollo / Granola / Zoom transcript or call link before building any demo content.
   - **Build brief** — produce the seven-section source-backed brief (only on explicit SC choice).
   - **Context Center + Apollo AI prompts** — only after meeting evidence is analyzed or the SC explicitly proceeds; always produces the Apollo AI Context Center payload first, then prompts.
   - **Add context** — let the SC paste call notes, Slack excerpts, or other context to merge into the current state and recompose.

   Pick the 2–4 most relevant options for the current dealroom status and evidence state. "Send / queue this in dealroom" appears only when the connector is available; otherwise replace it with "Copy to clipboard" / similar copyable framing.

1. **Step 5+ — Downstream actions (only after the SC selects).** Run the SC's selected path. The seven-section brief and five-part synthesis package are entered via this menu, never as the initial visible output for assigned-opportunity intent. **Producing the full seven-section brief (or any of Steps 5+) in the same response as the intake — before the SC has selected "Build brief" — is a violation of the router default flow and of the Menu Presentation Contract's STOP rule. The default response ends at the Pick Your Path `AskUserQuestion` call.** **Exception: this whole Steps 1-5 sequence, including this rule, does not apply when Step Zero (above) routed to "Skip to demo configuration"** — Step Zero's own sequence produces the brief directly, by design, without a Pick Your Path selection ever happening.

**Diagnostics on demand.** If the SC explicitly asks "why this route", "show your reasoning", "show the router", or "show the YAML", emit:

- A compact 3–6 line **"Why this route"** plain-English summary by default.
- The full router YAML / machine-readable state **only if** the SC explicitly asks for "YAML", "machine-readable", "raw router", or "debug" output.

**Brief and synthesis are downstream of this flow for assigned-opportunity intent.** The seven-section brief and the five-part synthesis package remain the stable core output contract, but they are entered via the Pick Your Path menu, not produced ahead of the visible action surface — **except via Step Zero's "Skip to demo configuration" path (above), which is the one deliberate, by-design way the brief gets produced without going through this menu.**

**Other intents are unchanged.** Direct asks like "what should I show [account]?" or "full synthesis" route to the existing brief/synthesis flows in the Workflow section. The router default above applies specifically to assigned-opportunity intent.

### Menu Presentation Contract (interactive Pick Your Path)

This contract governs how **every** action menu in this skill is presented — the assigned-opportunity Pick Your Path menu above and all Deal Action Menus in `SC-GUIDE.md` (After Assigned Opportunity Intake, After a Seven-Section Brief, After Context Center + Prompts, After Full Synthesis, After Trial Setup). It is a presentation rule, not a routing rule; it does not change which options are offered.

**Runtime.** This skill runs in Claude / Claude Code. The interactive mechanism is Claude's **`AskUserQuestion`** tool, which renders each option as a clickable button. `AskUserQuestion` is declared in this skill's `allowed-tools` frontmatter so it is available at every gate. There is no other button widget to target in this runtime.

**On `allowed-tools` semantics — resolved against Claude Code's own documentation 2026-07-30, superseding the empirical guess recorded here on 2026-07-28.** `allowed-tools` is **not an allowlist and restricts nothing.** The docs define it as *"Tools Claude can use without asking permission during the turn that invokes this skill,"* with the grant clearing on the next message — it is a permission **pre-grant**. Removing tools is a different field, `disallowed-tools`. Three consequences:

- This file listing `AskUserQuestion` only does **not** make Salesforce, Slack, Gong, Glean, Gmail, or Calendar unreachable. They work normally; they just prompt for permission like anything else. That matches the many real runs that have pulled SFDC/Slack/Gong data with this exact frontmatter.
- The sibling `demo-instance-configuration` adding `Bash` did not *grant* shell access — it made shell access **unprompted**. The earlier note here inferred a built-in-vs-MCP distinction from that; there isn't one.
- **Do not "fix" this file by enumerating connector tools**, and never conclude a tool is unavailable because it isn't listed. If something needs to be genuinely blocked, `disallowed-tools` is the field — not the absence of an `allowed-tools` entry.

**Rule (hard STOP pattern).** When the skill reaches a menu / decision gate (Pick Your Path, "what do you want next?", path selection, or any bounded set of next actions), the agent MUST:

1. Render the content that precedes the menu (intake summary, copyable message, AE sync questions).
1. **STOP.**
1. Call the **`AskUserQuestion`** tool with the menu's options.
1. **Do NOT proceed to any next action, and do NOT continue the response, until the SC selects an option.**

The agent MUST NOT print the options as a numbered or bulleted Markdown list (no `A. / B. / C.`, no `1. / 2. / 3.`) for the SC to read and type back, and MUST NOT pick an option on the SC's behalf and keep going. "Stop and ask" here means literally end the turn on the `AskUserQuestion` call. In Claude, an agent will keep going unless explicitly forbidden — so this gate is explicitly forbidding it.

**How to invoke `AskUserQuestion`.** Treat the menu as an instruction to the agent, not as literal output text. Call `AskUserQuestion` with:

- a `question`: the menu's `Question:` line (e.g. "The copyable message and AE sync questions are ready. Pick your path."),
- a short `header` chip (e.g. "Next step"),
- one `option` per menu item, where the option label is the exact action label (e.g. "Send / queue in dealroom", "Revise message", "Build brief", "Add context") and its description is the one-line explanation from the menu definition.

Claude renders these as clickable buttons. The bounded 2–4 option count and the per-option availability rules (e.g. "Send / queue" only when a Slack connector is present) still apply — build the choice set first, then pass it to `AskUserQuestion`.

**Fallback (plain-terminal surfaces only).** Some Claude surfaces (e.g. a raw terminal) may not render `AskUserQuestion` as buttons. The agent should still CALL `AskUserQuestion` — the host degrades it to a text selection prompt on its own. Only if the tool is genuinely unavailable in the running surface may the agent fall back to a bounded, numbered menu and say `Interactive menu unavailable here — reply with the option number.` A Markdown option list emitted **without** an `AskUserQuestion` call, while the tool was available, is a defect, not a style choice.

**Unchanged boundaries.** This contract changes presentation only. It does not authorize the skill to take any action on the SC's behalf: selecting a menu option still runs the normal read-only flow, and any send/post/queue still requires the explicit per-message approval gate defined above.

### Assigned Opportunity Anti-Patterns

These behaviors are forbidden in assigned-opportunity mode and must be treated as failures, not stylistic preferences — **except when Step Zero has run and the SC selected "Skip to demo configuration," in which case Step Zero's own sequence is authoritative and the intake-summary/message/Pick-Your-Path-first bullets below do not apply.** (This carve-out does not touch the Outbound Messaging Pipeline, approval, or gate-related bullets — those still apply in full regardless of which Step Zero path was taken.)

- Producing the seven-section brief or the five-part synthesis package as the first output for assigned-opportunity intent.
- Leaking internal machine state (router YAML, pipeline trace, layer labels, routing reasoning) as the default visible output, or producing only reasoning/routing commentary without a copyable artifact. The visible artifact is the copyable message + AE sync questions + Pick Your Path. **Enforced by the Terminal Output Assertion** and the SC-Facing Output Rules.
- Composing the coordination message outside the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize). Hand-written or model-direct drafts are not allowed.
- Offering to post / DM / queue to Slack without first showing the complete composed draft and asking for explicit per-message SC approval. Auto-posting is never allowed.
- Drafting the coordination message without specifying a destination (dealroom vs AE DM) or without including the dealroom search status that produced that destination.
- Burying or omitting the Pick Your Path menu after the message and questions, or replacing it with prose that the SC must parse to discover the next action. Emitting the menu as a Markdown list (`A./B./C.` or `1./2./3.`) **without calling `AskUserQuestion`**, or continuing past the menu into an action without waiting for the SC's selection, is the same defect — every menu must go through the Menu Presentation Contract's hard STOP + `AskUserQuestion` pattern.
- Producing a "here's what I'll do" preamble before the intake summary and copyable message.
- Generating Apollo AI demo setup prompts, walkthroughs, talk tracks, or demo stories before meeting evidence has been analyzed or the SC explicitly opts to proceed without it.
- Generating Apollo AI demo setup prompts without first producing the Apollo AI Context Center payload, or producing a Context Center payload before passing the Company + Business Understanding Gate.
- Generating AE-sync questions, a demo story, Context Center payload, or Apollo AI prompts for a meeting the SC says is already on calendar without first running Calendar + Gmail alignment or explicitly stating the connector was unavailable.
- Drafting customer-facing outreach instead of an internal coordination draft. Customer-facing follow-up routes to deal-execution.

## Workflow

0. Load `SC-GUIDE.md` first and use it to classify the SC's intent. SC-GUIDE decides what to offer next; this workflow decides how to generate the requested output. **For assigned-opportunity intent, the Assigned Opportunity Router Default Flow above takes precedence over the steps below until the SC selects a downstream action from the Pick Your Path menu.**
1. Resolve the account and opportunity from the input. If ambiguous, ask the user to choose.
1. Execute all available source searches regardless of prior source results. Salesforce, optional Snowflake, Slack, Gong, Calendar/Gmail alignment, and web research are independent inputs; degradation affects the output, not whether later searches run. Steps 3-8 are the execution order; failure of any step does not stop later steps.
1. Search Salesforce first via Glean (`references/data-sources.md` §1). Build the canonical deal record when possible.
1. If a Snowflake MCP/source is available in the live project, inspect schema and use it only as structured read-only validation or enrichment (`references/data-sources.md` §2).
1. Search Slack dealrooms via Glean (`references/data-sources.md` §3). Fill SFDC gaps and capture current deal motion.
1. Search Gong via Glean (`references/data-sources.md` §4). Capture stakeholder-language evidence and call-specific claims.
1. If the meeting is already on calendar or the SC asks for AE-sync/demo prep for a scheduled meeting, run the Calendar + Gmail alignment check (`references/data-sources.md` §5) before generating AE-sync questions, demo story, Context Center payload, or Apollo AI prompts.
1. Run lightweight company research if relevant (`references/data-sources.md` §6).
1. Normalize all findings into claim objects: `{claim, source, confidence, notes}`.
1. Map verified and inferred pains to Apollo capabilities using `references/capabilities-map.md`.
1. If competitors are detected, load `references/competitive-positioning.md`.
1. If technical risk signals are detected, load `references/technical-blockers.md`.
1. Produce the brief using `references/output-template.md`.
1. Use `SC-GUIDE.md` to offer the next relevant action: Apollo AI prompts, full synthesis, walkthrough, refresh, post-demo debrief, trial prompts, or deal-specific Q&A.

### SC Operating Motion

The interaction layer should treat demo prep as a staged SC workflow, not only a final customer-facing artifact:

1. **Assigned opportunity** — establish what the deal is, where it is in stage, what is known, what is missing, and what the SC should verify with the AE before investing in setup.
1. **Coordinate with AE or dealroom** — generate a copy-paste internal draft that requests the AE sync, frames the SC's prep needs, asks for known blockers, and requests any relevant call recording/transcript.
1. **AE sync** — if the sync is already on calendar, first align calendar attendees/timing/agenda and recent Gmail threads, then surface blockers, unknowns, commitments, technical feasibility risks, MEDDPICC gaps, stakeholder gaps, and questions that help the AE uncover issues that could prevent the deal from moving forward.
1. **Meeting evidence intake** — after the sync or customer call, ask for a transcript or accessible link from Gong, Apollo, Granola, Zoom, or another meeting source; if the link is inaccessible, ask the SC to paste the transcript or notes.
1. **Demo** — convert the verified deal context, AE-sync answers, and meeting evidence into a buyer-facing story: why change, why now, why Apollo, what to show, what to avoid, and how the SC should act as the technical expert on the call.

For assigned-opportunity intent, the Assigned Opportunity Router Default Flow controls ordering: short intake summary, then the Copyable Message to AE / Dealroom (composed through the Outbound Messaging Pipeline), then Recommended AE Sync Questions, then the Pick Your Path action menu — **unless Step Zero routed to "Skip to demo configuration," in which case Step Zero's own sequence controls ordering instead.** The internal router YAML and pipeline state stay internal and are not rendered to the SC unless explicitly requested as diagnostics. If a brief or synthesis is later generated before the AE sync has happened (because the SC selected that path or arrived through a non-assigned-opp intent), include AE-sync questions prominently, offer an internal AE/dealroom coordination draft, ask for any meeting transcript or call link, and avoid over-configuring Apollo AI prompts from assumptions.

## Epistemic Tagging

Every factual claim in the brief must carry a confidence tag and source. The skill uses a deliberately small three-value scale tuned for SC ergonomics.

| Tag | Meaning |
|---|---|
| `[verified]` | Directly stated by a person in a transcript, written in SFDC by the AE or SC, or documented in a shared artifact. |
| `[inferred]` | Derived from context — e.g. cost pressure inferred from renewal timing, tool consolidation inferred from Slack discussion. |
| `[assumed]` | Standard assumption based on deal stage, segment, or industry. |

If a section contains only `[assumed]` or `[inferred]` content, append: `Low confidence section — verify with AE before demo.`

Source labels and degradation behavior live in `references/data-sources.md`.

## Demo Flow Logic

Order Recommended Demo Flow items by evidence quality:

1. Verified pain tied to a stated decision criterion.
1. Verified pain without explicit decision criterion.
1. Inferred need from Slack, Gong, or SFDC notes.
1. Standard flow additions generally valuable for the identified use case.

Weight by use case:

- **Outbound**: sequencing, deliverability, AI messaging, dialing, workflows, scheduling.
- **Inbound**: website visitor identification, form enrichment, routing, meeting scheduling.
- **Enrichment**: data/TAM enrichment, waterfall enrichment, scoring, AI research, signals/intent, browser extension.
- **Deal execution**: post-call automation, deal management, call recording and insights.
- **Agency/reseller**: multi-client workspace management and scalable outbound operations.

Recommended Demo Flow is a prioritized show plan with a specific reason and source for each item — not a script.

## Risk Detection Rules

Always flag in the Stakeholder Map or Landmines section when present:

- Single-thread risk: only one known stakeholder.
- No Economic Buyer identified.
- Champion missing, unvalidated, or only implied.
- Fewer than three verified pain points → `Thin pain documentation. Recommend confirming pain points in first 5 minutes of demo.`
- Competition field populated but no deal-specific competitor strengths/weaknesses found.
- Technical blocker or integration risk in any source.
- AE promises, pricing claims, security commitments, or product capability claims that the SC should not contradict.

Hard blockers to surface in Landmines:

- Salesforce Essentials plan: no API access, integration impossible.
- Microsoft GCC High or government tenant: mailbox linking not supported.
- On-premise Exchange: not supported.

## Output Modes

Choose the output mode from the user's ask:

| Mode | Trigger | Output |
|---|---|---|
| Brief mode | Default when the user asks for demo prep, deal context, or what to show | The seven-section Demo Prep Brief from `references/output-template.md` |
| Synthesis mode | User asks for full synthesis, talk track, Apollo AI prompts, setup walkthrough, or demo automation | The five-part Demo Synthesis Package from `references/synthesis-template.md`. Part 3 always begins with the Apollo AI Context Center payload, then the demo setup prompts. |
| Apollo AI Context Center payload | Always upstream of Apollo AI demo or trial setup prompts. Triggered any time Apollo AI prompts are requested, whether standalone or inside synthesis mode. Requires passing the Company + Business Understanding Gate first. | A field-mapped, source-grounded Apollo AI calibration payload from `references/apollo-ai-prompt-patterns.md` for the SC to paste into Apollo Settings → AI Context Center. Primarily about the prospect's company and business; deal-specific calibration is a separate appended section. If the gate fails, render the Missing Business Context checklist instead. |
| Slack Canvas Deal Room | The SC selects **Build Slack Canvas deal room** from a Pick Your Path menu after a major output, or explicitly asks for a deal room, canvas, shared reference, or Slack canvas for the deal. Requires that at least one major intelligence artifact (brief, synthesis, Context Center + prompts, or demo flow) already exists in the session. | A Canvas-flavored Markdown Deal Room compiled from existing session content, plus a distribution plan (dealroom post or role-aware DMs) composed through the Outbound Messaging Pipeline. Canvas creation, updates, and message sends require explicit per-action SC approval. If the Slack connector is unavailable, output Canvas-flavored Markdown for manual paste only. Detailed workflow lives in `references/canvas-generation.md`. |
| Run Sheet (optional 5th artifact) | The SC selects **Generate Run Sheet** from a Pick Your Path menu after a synthesis package exists, or explicitly asks for an in-call run sheet / cue card / live demo sheet. Requires an existing synthesis package (Parts 3 + 4) to compile from. | A time-blocked, in-call run sheet compiled from Parts 3 + 4 — a **compilation, never a new source**; the brief and synthesis package stay byte-stable. Obeys the cue-card density rules; carries a header confidence declaration and tags only `[assumed]`/`[inferred]` exceptions inline; bars `[assumed]` company facts from PASTE blocks; inherits a gate-passed Context Center payload. Pre-call artifact only — live transcript guidance is the conversational layer, not a Run Sheet regeneration. Full spec in `references/synthesis-template.md` (Run Sheet section). |

In synthesis mode:

- Part 1 uses Command of the Message constructs natively: Before/After, Negative Consequences, Why Buy Anything, Why Now, Why Apollo, value drivers, and a lightweight MEDDPICC check. These constructs are embedded in `references/synthesis-template.md` and do not require loading deal-execution.
- If the user explicitly requests GTM pipeline analysis or the deal-execution router, that is a separate opt-in. In that case, use the seven-section brief as input to deal-execution and do not let downstream analysis mutate unsupported source claims.
- Part 2 must contain the seven-section brief, preserving its claims, confidence tags, and sources.
- Part 3 must begin with the Apollo AI Context Center calibration payload (Step 0), produced only after the Company + Business Understanding Gate has been passed. The payload is field-mapped to the Apollo Context Center UI and is primarily a company-and-business calibration of Apollo AI; deal-specific calibration is a separate appended section. Then generate paste-ready natural-language Apollo AI Assistant prompts bounded by the visible/known Apollo platform capabilities and ordered from the Part 1 strategic angle. The Context Center payload is upstream and the prompts must explicitly reference it.
- Part 4 turns the brief and strategic angle into an SC implementation walkthrough and talk-track hooks.
- Part 5 lists post-demo recommended actions only; do not execute or draft them.

If the user asks for Apollo AI prompts without a full synthesis package, first pass the Company + Business Understanding Gate, then generate the Apollo AI Context Center calibration payload (Step 0) using `references/apollo-ai-prompt-patterns.md`, then run the Context Center Validation Checklist, then produce or infer a lightweight strategic angle from the seven-section brief. If a strategic angle is not warranted, order prompts from the Recommended Demo Flow evidence ranking: the first prompt addresses the highest-ranked verified demo flow item, then follow inferred needs, then standard additions. The Context Center payload always precedes the first prompt; if the gate or the validation checklist fails, emit the Missing Business Context checklist and stop instead of producing prompts.

### Apollo AI Context Center Dependency

Apollo AI prompts are downstream of the Apollo AI Context Center. Apollo's in-app AI Assistant interprets every prompt through the Context Center configured in Apollo Settings → AI Context Center. The Context Center calibrates Apollo AI on **the prospect company and their business** — what they sell, who they sell to, their pains, their value prop, their competitors, their proof. Without that calibration, prompt outputs default to generic feature framing or, worse, an invented company profile.

The Context Center payload is therefore an **Apollo AI calibration payload** about the prospect's company first, with deal-specific calibration (this meeting's objective, AE asks, do-not-say constraints) appended as a separate, smaller section. It is **not** a deal-prompt context blob.

Hard rules:

1. Whenever Apollo AI demo or trial setup prompts are generated — standalone, after a brief, inside synthesis mode, or via the Pick Your Path "Context Center + Apollo AI prompts" option — first pass the **Company + Business Understanding Gate** above, then produce the Apollo AI Context Center payload.
1. The Context Center payload is a copy-paste artifact for the SC to add or update in Apollo Settings → AI Context Center. This skill does not write to Apollo.
1. The payload must be **primarily about the prospect company's business**, organized under the observed Apollo UI section headers: **Overview** (Company domain, Company name, Offering, Customer profile), **Key benefits & outcomes** (Pain points, Value proposition), **Unique characteristics** (Advantage over competitors, Primary competitors, Social proof), and **Other details** (CTA). Deal-specific calibration (this demo's objective, AE commitments, do-not-say) is a separate appended section, not pasted into any global UI field unless a visible editable Additional information / account-scoped field exists.
1. Every claim must be source-grounded and confidence-tagged. No invention. If grounding is missing, emit the Missing Business Context checklist instead of a payload (see Company + Business Understanding Gate).
1. The payload must follow the **Context Center Field Mapping** below so blocks are paste-ready into the observed Apollo Context Center UI. The UI groups editable fields under non-editable section headers in this exact hierarchy: **Overview** (Company domain, Company name, Offering, Customer profile), **Key benefits & outcomes** (Pain points, Value proposition), **Unique characteristics** (Advantage over competitors, Primary competitors, Social proof), **Other details** (CTA), and **Additional information** (paste target only if the UI exposes a visible editable body field under it). Section headers are not paste targets. CTA is a paste-ready editable field under Other details, not a top-level field. Cancel / Save are UI controls, never fields. Deal-specific calibration is a separate section appended after the UI fields and is not forced into any UI field unless a visible editable Additional information or account-specific / demo-context field exists.
1. Surface a placement-and-safety warning: the Context Center may apply broadly to AI interactions in the workspace. Confidential deal claims belong in the deal-specific calibration section, not the company-profile fields, and must not be pasted into a global Company/Products profile without explicit SC approval.
1. The Apollo AI prompts section must explicitly depend on the Context Center payload. Prompt 1 is preceded by an explicit "Step 0: Update AI Context Center" instruction.
1. Run the **Context Center Validation Checklist** (in the Company + Business Understanding Gate section) before producing any prompt. If validation fails, do not emit prompts.
1. The skill remains read-only. It only drafts the payload. It does not update Apollo AI, the Context Center, or any Apollo object.

### Context Center Field Mapping

The Apollo AI Context Center UI exposes a mix of non-editable **section headers** and editable child fields, organized into the following observed hierarchy:

- **Overview** *(section header — UI element only, not a paste target)*
  - Company domain *(editable)*
  - Company name *(editable)*
  - Offering *(editable)*
  - Customer profile *(editable)*
- **Key benefits & outcomes** *(section header — UI element only, not a paste target)*
  - Pain points *(editable)*
  - Value proposition *(editable)*
- **Unique characteristics** *(section header — UI element only, not a paste target)*
  - Advantage over competitors *(editable)*
  - Primary competitors *(editable)*
  - Social proof *(editable)*
- **Other details** *(section header — UI element only, not a paste target)*
  - CTA *(editable)*
- **Additional information** *(section — only treat as a paste target if the UI exposes a visible editable body field under it; otherwise it is a section header only)*

Section headers (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information) are UI labels / accordions, not paste targets. Do not paste body text into a section header; paste only into the editable child fields. The payload must be structured so each block below is paste-ready into the corresponding editable field. Populate each field from the Company + Business Understanding object — not from deal mechanics. Each field includes source/confidence inline, but the text body is concise enough to paste into the UI directly.

Paste-ready editable field blocks (rendered under their section headers, in this order):

**Overview** *(section header — not a paste target)*

1. **Company domain** — the prospect's primary domain (e.g. `acme.com`). Source: prospect website / SFDC.
1. **Company name** — legal/marketing name as the prospect uses it. Source: prospect website / SFDC.
1. **Offering** — what the company sells, in their language. 1–3 sentences.
1. **Customer profile** — who the company sells to: ICP, industries, segments, geographies, buyer personas. 1–3 sentences or a short bullet list.

**Key benefits & outcomes** *(section header — not a paste target)*

5. **Pain points** — the pains *the prospect's buyers* have, in the prospect's framing. 2–4 bullets.
1. **Value proposition** — the prospect's positioning / why customers buy from them. 1–3 sentences.

**Unique characteristics** *(section header — not a paste target)*

7a. **Advantage over competitors** — how the prospect frames their advantage in their market. 2–4 bullets. *Not* Apollo's advantage over Apollo competitors.
7b. **Primary competitors** — competitors in the prospect's market (named alternatives their buyers consider). 2–6 bullets. Only include named, source-backed competitors. Omit if unknown.
7c. **Social proof** — verifiable named customers, case studies, metrics, awards. Only if directly attested by the company or a credible public source. Omit if unverifiable.

**Other details** *(section header — not a paste target)*

8. **CTA** — the prospect company's call-to-action to their own buyers: what the prospect asks their customers, leads, or prospects to do next in the prospect's own sales cycle. 1–2 sentences. This is a company-profile fact, NOT the Apollo demo objective — if it mentions Apollo, the demo, or the trial, it belongs in Deal-specific calibration notes instead. CTA is a paste-ready editable field under Other details — it is **not** a top-level field and **not** a section header.

**Additional information** *(section — only paste here if the UI exposes a visible editable body field under it. If no such editable field is visible, treat Additional information as a section header only and place any deal-specific notes outside / after the Context Center entirely.)*

Then, outside / after the UI fields, a clearly separated section that is **not** pasted into any global Context Center field:

9. **Deal-specific calibration notes** — the demo's strategic angle for this deal, top 2–3 deal-specific buyer pains pulled from the brief, AE commitments to preserve, do-not-say / do-not-promise constraints, and prompt interpretation instructions for Apollo AI. This block is the only place where deal-specific claims belong. Place it in a clearly labeled separate note for the SC to keep outside the global Context Center. (Earlier wording here also offered "an account-scoped card" or "session-level demo context" — corrected 2026-07-28: neither exists inside an Apollo instance, every Context Center write resolves to the team's one Global CC. Isolation comes from the instance itself, which for this workflow is a per-prospect demo sub-account.) Do not force deal-specific calibration notes into UI fields. If the Apollo UI exposes a visible editable Additional information body field (or another visible editable account-specific / demo-context field) and the SC confirms scoping, that field may receive the deal-specific block; otherwise it is provided to the SC as a separate note kept outside the global Context Center.

Each editable-field block must carry a one-line `Source: ... | Confidence: [verified|inferred]` annotation underneath the paste-ready text. `[assumed]` is not allowed in fields 1–6 or 7a–7b; if the only available evidence is `[assumed]`, omit the field and surface it in Missing Business Context. The Unique characteristics section is required as a section *with at least one source-backed subfield (7a–7c)* where grounding exists; section headers themselves are never paste targets.

The Apollo UI does **not** expose Cancel / Save as Context Center fields; those are page controls and must never appear as field blocks in the payload.

**UI hierarchy note**: Do not paste text into any non-editable section header (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information). Paste only into the editable child fields under each header. Body text dropped into a section header has no effect and corrupts the layout. CTA is the editable child field under Other details, not a top-level paste target.

The detailed template lives in `references/apollo-ai-prompt-patterns.md` "Step 0: Apollo AI Context Center Payload — Field-Mapped Template".

Trial setup prompts are a separate prompt type from demo setup prompts. Use `references/apollo-ai-prompt-patterns.md` trial rules and `references/deal-lifecycle-support.md` when the SC asks to set up a trial, evaluation environment, POC, pilot, data test follow-through, or buyer-facing validation workflow. Trial prompts must default to preview/review modes and must warn about activation, enrollment, sending, enrichment, data mutation, and credit consumption.

If the trial scope or success criteria are unclear, generate trial planning prompts first rather than full setup prompts. Trial planning prompts help the SC define success criteria and dependencies; trial setup prompts configure or propose Apollo objects after scope is clear.

## Handoff to deal-execution

This skill remains read-only. When the SC asks for a customer-facing email, Slack recap, SFDC update, non-AE-sync internal message, or execution action, hand off explicitly. The only exception is an internal AE/dealroom coordination draft used to prepare for AE sync, which this skill may generate as copy-paste text without sending or posting.

1. Preserve the current seven-section brief or relevant lifecycle output as source context.
1. Tell the SC: `For drafting or execution, use deal-execution with this brief as input.`
1. Provide a copy-paste handoff prompt:
   Replace the bracketed menu with the single action the SC actually wants before using the prompt.

```text
Use deal-execution. Based on the demo-prep-intelligence brief below, [draft the follow-up / draft the Slack recap / prepare the SFDC update / route the next action]. Preserve the source/confidence boundaries and do not add unsupported claims.

[paste brief or relevant section]
```

4. Do not load or execute deal-execution unless the user explicitly opts in within the current conversation.

## Handoff to demo-instance-configuration

This skill remains read-only. Once a Context Center payload and/or Recommended Demo Flow is produced, `demo-instance-configuration` is the downstream layer that turns it into an approved, executable demo-instance plan. This is the logic that runs when the SC selects **Configure the demo instance** from any of `SC-GUIDE.md`'s Deal Action Menus (after the brief, after the Context Center payload, or after full synthesis).

1. **Context Center readiness check (before anything else, whenever only the brief/Recommended Demo Flow exists).** `demo-instance-configuration` can populate the AI Context Center only if a Context Center payload has actually been generated - the brief and Recommended Demo Flow alone don't carry it, because generating one is its own separate flow (`SC-GUIDE.md`'s "Context Center payload + Apollo AI prompts" option), not a byproduct of the brief. If the SC selects **Configure the demo instance** straight from the brief-only menu and no Context Center payload exists yet in this session or the scratchpad, ask before proceeding - do not silently hand off the Recommended Demo Flow alone and let `demo-instance-configuration` discover the gap on its own turn later. Ask something close to: *"Before we proceed with generating the tailored demo org, will you want to populate the AI Context Center too? If so, I'll synthesize the prompts for that now."* If yes, run the Context Center payload flow first, then continue to the steps below with both artifacts. If no, proceed with the Recommended Demo Flow alone - that's a legitimate, narrower handoff (sequence staging only), not an error, as long as it was the SC's actual choice and not a default nobody checked. Skip this check entirely when a Context Center payload already exists (i.e. the SC is coming from the Context Center or full-synthesis menus) - it's only relevant for the brief-only path.

1. **Same-session continuation.** If the SC is continuing straight into `demo-instance-configuration` now, no extra step is needed - the `demo-prep-scratchpad.md` handoff file and this conversation's context are both already available to it per its Input Contract. **Say something close to:** *"Both artifacts are saved and ready for demo-instance-configuration. Tell me to go ahead and I'll hand off, or run `/apollo-gtm:demo-instance-configuration` yourself."* Keep it short - one line, not a re-explanation of what was just built.

   **On an explicit go-ahead, actually invoke it — added 2026-07-30, confirmed necessary live.** When the SC says to proceed ("go ahead," "yes," "do it," or similar), **call the `Skill` tool with `apollo-gtm:demo-instance-configuration`.** Do not tell the SC to run it themselves as a first response, and do not claim skills can't invoke each other — per Claude Code's own skills documentation, *"By default, both you and Claude can invoke any skill,"* a `Skill` tool exists for exactly this, and `demo-instance-configuration` sets no `disable-model-invocation` flag. **Why this rule exists:** a live run (2026-07-30) ended with the SC saying "go ahead" and the skill replying that it *"can't chain directly… skills don't invoke each other as function calls"* — factually wrong, and it dead-ended a handoff the SC had explicitly authorized.

   **Only on an explicit go-ahead — never chain automatically.** Do not invoke the sibling skill on your own initiative just because both artifacts exist. Layer 1 deciding to start Layer 2 is a scope decision that belongs to the SC, and the handoff sentence above is the ask, not a formality.

   **If the `Skill` tool genuinely isn't available** (denied in this session's permissions, or the call errors), *then* give the SC the slash command as the fallback and say plainly that you couldn't invoke it yourself. That is a real tool-availability statement about your own turn — which is different from, and must never be phrased as, a claim about whether the sibling skill is installed (see the rule immediately below).

   **Never frame this as a check on whether `demo-instance-configuration` is "available" or "invokable" in this session - added 2026-07-28, confirmed necessary live.** A real test run said the downstream skill "isn't available as an invokable skill in this session, so I can't hand off to it automatically," when the skill was in fact installed and slash-invokable the entire time (confirmed by the SC's own autocomplete). This is a different situation from the genuinely conditional Slack/dealroom connector checks elsewhere in this file (a live MCP connector that really can be present or absent) - do not borrow that pattern here. Once this plugin is installed, `demo-instance-configuration` is always present. **Corrected 2026-07-30 — the rest of this rule used to read "this skill has no mechanism to invoke it directly (skills don't call other skills as functions) and was never meant to try." That was factually wrong, and it caused a real failure:** on 2026-07-30 an SC said "go ahead" and the skill refused, echoing that exact reasoning back almost verbatim. Claude Code's own skills documentation says *"By default, both you and Claude can invoke any skill,"* and a `Skill` tool exists precisely for it. **The correct behavior is in the go-ahead rule above: invoke the sibling skill on an explicit go-ahead.** What this rule still forbids, unchanged and still the point: describing the sibling skill's *presence* as conditional or unverified. If genuinely unsure how the SC wants to proceed, ask directly - do not guess at or assert anything about the other skill's availability.

1. **Session-break offer.** If the SC indicates they'll run `demo-instance-configuration` later, in a separate or fresh session - anything implying a break, e.g. "I'll come back to this," "let's pick it up tomorrow," "I need to finish this some other time" - proactively ask whether they want to see and save the scratchpad's exact content now. Say plainly that the scratchpad file itself may not persist once this session ends, so this is the one reliable way to carry the output into a later session.

1. **If the SC says yes**, render the scratchpad's exact content as copyable text - the same content written to `demo-prep-scratchpad.md`, full Context Center payload and/or Recommended Demo Flow, every `[verified]`/`[inferred]`/`[assumed]` tag intact - labeled clearly as a saved copy for later use with `demo-instance-configuration`, not as a new artifact type and not as a replacement for the primary brief output.

1. This is the one deliberate, conditional exception to the scratchpad's "not SC-facing by default" rule in `GOVERNANCE.md` - it only triggers when the SC has indicated a session break, not on request at any other time.

## Output Contract

The brief must follow `references/output-template.md` exactly. Seven numbered sections, in this order:

1. Account Snapshot
1. Stakeholder Map
1. Pain Points (Ranked)
1. Competitive Landscape
1. Recommended Demo Flow
1. Landmines
1. Open Questions

Output rules:

- Include the generated date, stage, ARR, and close date when known.
- Account Snapshot: 3–5 sentences.
- Pain points ranked by specificity and verification.
- Competitive readout uses deal-specific strengths/weaknesses; generic battlecard content can supplement but must not replace deal evidence.
- Open Questions are actual questions the SC can ask customers or the AE — not internal labels.
- Use `Unknown` for missing data.
- Inline source and confidence labels for every factual claim. No source appendix.
- Output as a Markdown artifact by default for the full brief or synthesis package. If the user needs inline delivery, provide a concise summary and offer to generate the artifact.
- After major outputs, offer the next relevant action using `SC-GUIDE.md`. Do not bury Apollo AI prompts behind hidden mode names the SC must already know.

The full synthesis package must follow `references/synthesis-template.md` exactly. It has five parts and embeds the seven-section brief as Part 2.

## Anti-Patterns

> **Consolidation note (v1.3.0):** render-time output-leak rules and canvas-prerequisite rules are now enforced by the **Terminal Output Assertion** primitive (defined near the top of this file), and gate-enforcement is handled by the **Visible Gate Block** primitive. The individual bullets that merely restated those checks have been removed and replaced with single references to the primitives, so the net rule count goes down without losing any enforcement. See the changelog for before/after counts.

Avoid:

- Inventing stakeholders, pains, competitors, metrics, or tech stack to fill gaps.
- Using public research to override internal deal evidence.
- Treating fluent SFDC text as verified when it is actually assumed or copy-pasted boilerplate.
- Producing a demo flow that is a script rather than a prioritized show plan with sources.
- Adding sections beyond the seven-section contract.
- Removing source labels for readability.
- Writing to any system, sending/posting any message, drafting customer-facing outreach, or proposing outbound actions. Internal AE/dealroom coordination drafts are allowed only as read-only copy-paste text. The single exception across this entire skill is the session-scratchpad handoff file defined in `GOVERNANCE.md` - do not treat that narrow exception as license to write anywhere else.
- Loading deal-execution references unless the user explicitly opts in.
- Stopping after a failed SFDC search instead of continuing to Slack, Gong, and web.
- Treating Apollo AI prompts as guaranteed executable schemas without verifying the live Apollo connector/tool schema.
- Expanding the brief into synthesis mode by dropping epistemic tags or sources.
- Generating Apollo AI prompts that optimize for generic feature coverage instead of the highest-leverage strategic angle from Part 1.
- Hiding Apollo AI prompt generation behind an unmentioned "synthesis mode" instead of proactively offering it after a brief.
- Regenerating Apollo AI prompts after a change to audience, scope, competitor, success criteria, or meeting context without also regenerating the Step 0 Context Center payload. The payload conditions Apollo AI's interpretation and must be refreshed alongside any prompt regeneration triggered by changed context; updated prompts paired with a stale Context Center will be interpreted against the prior framing.
- Pasting account-specific confidential claims into the global Company information or Products & services profile without warning the SC, when Apollo only exposes global Context Center surfaces and no account-specific or session-level context area.
- Implying that the skill writes to or updates the Apollo AI Context Center. The skill only drafts a copy-paste payload for the SC to apply.
- Producing a Context Center payload built primarily from deal mechanics (deal pain, AE notes, Apollo battlecard competitors) rather than from the prospect's actual company and business. The payload calibrates Apollo AI on the prospect's company; deal calibration is a smaller appended section, not the body.
- Inventing or backfilling company facts when the prospect's offering, ICP, value prop, competitors, or social proof are unknown. Fictional or "plausible-looking" company profiles are forbidden; emit the Missing Business Context checklist instead.
- Substituting an unrelated example company (e.g. describing a generic SaaS or a different vertical) when the actual prospect's business is unknown. The payload must describe the actual prospect or fail the gate.
- Treating Apollo's battlecard competitors as the prospect's *own* market competitors. The Primary competitors field describes competitors the prospect's buyers consider, not Apollo's competitors.
- Filling Pain points, Value proposition, or Customer profile fields with generic SaaS language when the prospect's actual buyer pains, positioning, or ICP have not been verified.
- Generating Apollo AI prompts before passing the Company + Business Understanding Gate and the Context Center Validation Checklist. Prompts emitted against an ungrounded or fictional Context Center will be interpreted against an invented company.
- Producing a Context Center payload that is not field-mapped to the observed Apollo UI hierarchy. The observed sections are Overview (Company domain, Company name, Offering, Customer profile), Key benefits & outcomes (Pain points, Value proposition), Unique characteristics (Advantage over competitors, Primary competitors, Social proof), Other details (CTA), and Additional information (paste target only if the UI exposes a visible editable body field under it). Free-form blobs are not paste-ready and break the calibration step.
- Treating any section header (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information) as a paste target. Section headers are UI labels / accordions; pasting body text into them has no effect. Paste only into the editable child fields under each header.
- Treating CTA as a top-level field or a section header. CTA is the editable child field under **Other details** and must be rendered there, not at the top level.
- Listing Cancel or Save as Context Center fields. Those are page controls, not fields; they must never appear in the payload.
- Forcing deal-specific calibration notes into UI fields when no visible editable Additional information, account-specific, or demo-context field exists. Without such a field, deal-specific notes are provided to the SC as a separate note kept outside the global Context Center, not pasted into a global Company / Products field.
- Treating data-test results, deal mechanics, or AE pain notes as substitutes for understanding the prospect's company. Deal pain belongs in deal-specific calibration; the company-profile fields require company-grounded sources.
- Presenting lifecycle action menus as long prose bullet lists when an interactive prompt/question UI is available.
- Implying the skill persists deal state across sessions. Across sessions, rebuild from current sources or ask the SC to provide the prior brief.
- Treating contextual refreshes as source-backed facts without labeling the new user-provided context.
- Offering trial setup prompts before the deal has enough verified pain, decision criteria, or evaluation scope to make them safe and useful.
- Generating trial prompts that could activate workflows, enroll contacts, send emails, enrich data, or consume credits without explicit preview/review/no-activation language.
- Building the seven-section brief or five-part synthesis package first when assigned-opportunity intent is detected, instead of running the Assigned Opportunity Router Default Flow.
- Producing the Internal AE / Dealroom Coordination Draft without first searching Slack/Glean for an active dealroom when that source is available.
- Leaking internal machine state (router YAML, pipeline traces, layer labels, internal state tags, routing reasoning) or MCP JSON schemas as the default visible output when the SC asked for Apollo AI prompts. **Enforced by the Terminal Output Assertion.** Diagnostics remain opt-in.
- Producing only reasoning, analysis, or routing commentary without a sendable/copyable artifact for the SC to act on.
- Generating any outbound message (AE sync ask, dealroom post, Slack DM, internal escalation, customer follow-up) outside the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize).
- Posting, DMing, queueing, or scheduling a Slack/dealroom message without first showing the complete composed draft and getting explicit per-message SC approval. Auto-posting is forbidden.
- Treating prior approval of one message as a standing pre-authorization for future messages.
- Drafting the coordination message without specifying a destination (`Dealroom: #channel` or `AE DM: AE name`) and without including the dealroom search status that produced that destination choice.
- Hiding or burying the Pick Your Path action menu after the message and questions, or treating action options as passive prose instead of a bounded interactive choice.
- Treating Canvas-flavored Markdown as Slack message Markdown (or vice versa). The two are different formats — profile cards, channel cards, callouts, and table rendering all differ — and mixing them silently breaks the canvas layout.
- Using `<@USER_ID>` mention syntax inside the canvas for team members. Profile cards on a Slack Canvas must be `![](@SLACK_USER_ID)` rendered on their own line.
- Using `<#CHANNEL_ID>` channel syntax inside the canvas. Channel cards must be `![](#CHANNEL_ID)` on their own line.
- Calling `slack_create_canvas` without first showing the full Canvas-flavored Markdown draft and the proposed canvas title to the SC and getting explicit approval. Canvas creation produces a Slack artifact and is a write action.
- Calling `slack_send_message` (or `slack_send_message_draft`) to distribute the canvas link without first showing every composed draft and the recipient list and getting explicit per-batch SC approval.
- Skipping the dealroom search before falling back to DMs. The skill must search Slack/Glean for an active dealroom channel before defaulting to individual DMs.
- Distributing the canvas link to external / prospect attendees. Filter prospect email domains out of the calendar attendee list before resolving Slack user IDs and never DM customer / prospect Slack accounts.
- Replacing the entire canvas during a refresh without explicit SC approval. Refreshes update specific sections; whole-canvas replacement requires a fresh, explicit approval after the full new draft is shown.
- Composing canvas distribution messages outside the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize). Hand-written or model-direct distribution drafts are not allowed.
- Treating prior approval of one canvas action as a standing pre-authorization for future canvas actions. Every Slack write action (create_canvas, update_canvas, send_message, send_message_draft) requires a fresh per-action approval.
- Rendering a canvas without its prerequisites (`references/canvas-generation.md` loaded AND a prior major artifact to compile from), on any path including out-of-band "just post it as a canvas." **Enforced by the Terminal Output Assertion.**
- Pulling new source data solely to fill canvas sections. The canvas presents existing brief / synthesis content; if data is missing, refresh the brief or render `Unknown` for that section.
- Inventing canvas content — fictional contacts, fabricated buyer pains, made-up tech stack — to make the canvas look complete. Use `Unknown` or omit the section instead.

## Validation Test Cases

After installation, validate quality against current active deals. Initial historical test cases:

- **Collage Group** — historical validation deal, David as SC. Current stage may differ from the original Stage 3 expectation; validate against the live SFDC stage and note stage mismatch if present.
- **Keeper Security** — Stage 3, Radu as SC. Expect dense MEDDPICC and multiple Gong calls.
- **Thredd** — active eval, Nicholas as SC. Expect Slack dealroom and data test activity.
- **One sparse Stage 3 opportunity** — expect graceful degradation, long Open Questions, explicit sparse-data callout.

For rollout and ongoing validation, refresh the named deals and select one current deal from each category:

- A Stage 3 opportunity with rich SFDC, Slack, and Gong data.
- A Stage 3 opportunity with sparse SFDC and active Slack.
- A Stage 3 opportunity with minimal data across all sources.
