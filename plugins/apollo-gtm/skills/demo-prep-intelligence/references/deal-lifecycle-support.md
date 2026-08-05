# Deal Lifecycle Support

Use this reference when the SC asks for support before or after the initial brief: assigned-opportunity intake, internal AE/dealroom coordination, AE-sync prep, meeting transcript or call-link analysis, refresh, audience adjustment, competitive repositioning, post-demo debrief, trial success criteria, trial check-in prep, or second-demo planning.

This reference does not change the seven-section brief contract. It helps update, reinterpret, or extend from the brief while preserving source labels and confidence.

______________________________________________________________________

## Core Rule

Every lifecycle output must say which source it is using:

- `Source: Existing brief`
- `Source: User-provided call notes`
- `Source: User-provided call link`
- `Source: User-provided call transcript`
- `Source: User-provided Slack excerpt`
- `Source: User-provided data test result`
- `Source: Calendar event`
- `Source: Gmail thread`
- `Source: Fresh source-backed rebuild`

Do not present user-provided context as if it came from SFDC, Slack, Gong, Snowflake, or web search.

User-provided summaries are useful but not automatically `[verified]`. Default user-provided notes, recollections, and summaries to `[inferred]` unless the SC provides a raw transcript, raw Slack excerpt, raw email excerpt, direct quote, or explicit field/source value. Direct quotes or raw excerpts can be `[verified]` with the source label `Source: User-provided [raw transcript / Slack excerpt / email excerpt]`.

______________________________________________________________________

## Refresh Decision Tree

| User request | Refresh type | Output |
|---|---|---|
| "I was assigned this opp" / "prep me for AE sync" | Assigned-opportunity / AE-sync prep | Visible response, copyable-message-first: short intake summary, then `## Copyable Message to AE / Dealroom` (composed through this skill's own six-stage Outbound Messaging Pipeline — corrected 2026-07-28; `SKILL.md` is explicit that these constructs do not require loading `deal-execution`), then `## Recommended AE Sync Questions`, then `## Pick Your Path` menu. The internal router payload is built off-screen to drive routing and is never rendered to the SC unless they explicitly ask for diagnostics. The action menu offers send/queue (with explicit per-message approval), revise, analyze transcript, build brief, Context Center + Apollo AI prompts, or add context. |
| "I have an AE sync/demo on calendar" / "meeting is scheduled" | Calendar + Gmail alignment | Read-only calendar/email alignment summary, then AE-sync or demo-prep questions. |
| "Message the AE" / "post in the dealroom" / "ask AE for context" | Internal coordination draft | Copy-paste AE DM or dealroom post draft. Never send or post. |
| "Here's the transcript" / "Gong link" / "Apollo call" / "Granola notes" / "Zoom recording" | Meeting evidence analysis | Evidence summary, updated blockers/questions, and demo-story implications. |
| "Refresh this deal" with no new context | Full source-backed rebuild | New brief or synthesis, plus "What changed" if prior output exists. |
| Pasted notes, Slack, email, or transcript excerpt | Contextual update | Updated affected sections plus "What changed." |
| "The VP is joining" | Audience adjustment | Updated Stakeholder Map, demo flow, talk-track hooks, and open questions. |
| "They're looking at [competitor]" | Competitive repositioning | Updated Competitive Landscape, demo emphasis, and landmines. |
| "Data test came back" | Evidence update | Add result to Pain Points, Competitive Landscape, Landmines, or Open Questions. |
| "Second demo on [capability]" | Focused follow-up demo plan | Updated demo flow, refreshed Apollo AI Context Center payload, and Apollo AI prompts for that capability. Context Center payload comes first; never regenerate prompts without it. |
| "Set up their trial" | Trial setup | Trial-scoped Apollo AI Context Center payload (Step 0) plus trial prompts and safety/readiness checklist. |

______________________________________________________________________

## Internal AE / Dealroom Coordination Draft

Use this when the SC needs to contact the AE or active dealroom before the AE sync. This is the only message-drafting path in this skill, and it is limited to internal coordination. Generate draft text only. Do not send, post, schedule, tag, update, or execute.

### Output Format Rules

The visible artifact for the SC is **always a copyable message-first layout** — never raw router YAML, pipeline trace, or routing reasoning by default.

- **Assigned-opportunity flow (default for assigned-opp intent).** The visible response is, in order: a short intake summary, the `## Copyable Message to AE / Dealroom` block (composed through the Outbound Messaging Pipeline and rendered inside a fenced code block), the `## Recommended AE Sync Questions` block, and the `## Pick Your Path` action menu. The internal router payload (route, account, opportunity, dealroom_search, coordination_draft, pick_your_path, read_only_boundary) is built off-screen to drive routing and is **not** rendered to the SC by default.
- **Standalone draft requests (later in the deal, or non-assigned-opp intents like "message the AE about [account]").** The standalone markdown template below remains available. Compose the draft through the Outbound Messaging Pipeline before showing it. Do not surface raw router YAML.

Raw router YAML is shown only when the SC explicitly asks for "YAML", "machine-readable", "raw router", or "debug" output. If the SC asks "why this route", emit a compact 3–6 line "Why this route" plain-English summary instead.

### Mandatory Composition Pipeline

Every coordination draft (assigned-opp or standalone) must be composed through the Outbound Messaging Pipeline before display:

1. parse state → 2. filter / ground claims → 3. map constraints → 4. route action → 5. compose for the audience (internal coordination voice) → 6. humanize / compress.

The SC sees only the final composed, humanized draft. Pipeline traces, stage labels, and intermediate drafts stay internal.

### Slack / Dealroom Posting (Approval Required)

If a Slack/dealroom connector is available in the runtime, the skill **may offer** to queue/post the composed draft via the Pick Your Path menu (`Send / queue this in dealroom`). On selection, the skill must re-show the complete composed draft and the explicit destination, then ask for per-message SC approval before delegating the queue/post to `/deal-execution`. The skill itself never writes to Slack. Auto-posting, DMing, or queuing without per-message approval is forbidden. If the connector is unavailable, the skill provides copyable text only and notes that posting requires `/deal-execution`.

### Dealroom Search Status

Before drafting, run the Slack/Glean dealroom search from `data-sources.md` §3 and record:

- `dealroom_status`: `found | not_found | ambiguous | unavailable`
- `candidate_channels`: list of channel names that look like the dealroom, if any.

If access to Slack/Glean is unavailable, record `unavailable` and continue with a caveat in the draft. Do not skip the search silently when access is available.

### Destination Selection Rules

| dealroom_status | Destination | Required ask in draft |
|---|---|---|
| `found` | Dealroom post in `#[channel]` | Confirm this is the correct active dealroom. |
| `not_found` | AE DM | "Do you have an active dealroom for this account, or should we spin one up?" |
| `ambiguous` | AE DM | List the candidate channels and ask the AE which one (if any) is the active dealroom. |
| `unavailable` | AE DM with caveat | Note that the SC could not search Slack/Glean and ask the AE to confirm or share the active dealroom. |

### Internal Router Payload Schema (off-screen)

For the assigned-opportunity flow, the skill internally builds a router payload to choose the next move. This payload **stays internal** by default — the SC sees the copyable message + AE sync questions + Pick Your Path menu, not this YAML. Render the payload only when the SC explicitly asks for "YAML", "machine-readable", "raw router", or "debug" output. For "why this route" / "show your reasoning" asks, emit a compact 3–6 line plain-English summary instead.

Internal payload fields (defined in `SC-GUIDE.md` "Assigned Opportunity Visible Output (copyable-message-first)"):

- `route: assigned_opp_router`
- `account`, `opportunity`, `ae`, `sc`, `stage`, `arr`, `close_date`
- `dealroom_search.status`, `dealroom_search.candidate_channels`, `dealroom_search.destination_reasoning`
- `coordination_draft.destination`, `coordination_draft.draft_text` (post-pipeline), `coordination_draft.required_asks` (all six: `blockers`, `buyer_audience`, `commitments`, `success_criteria`, `next_step`, `transcript_or_call_link`)
- `pick_your_path` (2–4 options)
- `read_only_boundary: no_send_no_post_no_update`

The payload's role is routing, not display. The visible output is the copyable message-first layout described above.

### Output Template (standalone markdown — not for assigned-opp router flow)

The markdown template below is preserved for **standalone, non-router** draft requests (e.g. the SC asks "draft a message to the AE about [account]" later in the deal, or in a non-assigned-opp intent). Do not use this markdown template as the first artifact for assigned-opportunity intent — follow the visible copyable-message-first flow described above instead. **To be explicit, since the earlier wording here said "use the YAML payload above instead" and read as an instruction to render it:** the router YAML is never a visible artifact. It stays internal (see "The payload's role is routing, not display" above, and `SKILL.md`'s SC-Facing Output Rule 1 plus the Terminal Output Assertion's output-leak strip).

```markdown
## Internal Coordination Draft: [Account Name]

### Destination

- **Send to** — [Dealroom: #channel | AE DM: AE name].
- **Dealroom status** — [found / not_found / ambiguous / unavailable].
- **Candidate channels** — [list or none].

### Draft for AE DM or Dealroom

[Draft message]

### Why This Message

- **Sync goal** — [what the message is trying to clarify].
- **SC lens** — [technical feasibility / blockers / buyer story / demo success criteria].
- **Evidence request** — [call transcript or link requested, if missing].
- **Destination rationale** — [why dealroom vs AE DM, based on dealroom status].

### Questions Embedded

- [Blockers question]
- [Buyer audience question]
- [AE commitments question]
- [Success criteria question]
- [Next step question]
- [Meeting transcript / call link request]
```

Drafting rules:

- Keep the message concise and Slack-native.
- Ask for the AE sync, **known blockers, buyer audience, AE commitments, success criteria, next step, and any relevant Gong / Apollo / Granola / Zoom / other meeting transcript or call link**. All six must appear in the draft.
- If `dealroom_status: found`, draft for the dealroom unless the SC specifically says DM the AE.
- If `dealroom_status: not_found | ambiguous | unavailable`, draft as an AE DM and include the ask to confirm or create an active dealroom (per the table above).
- If the message references facts from the brief, keep them grounded and avoid unsupported certainty.
- End with a clear single ask (the sync + the transcript request), not a sprawl of unrelated asks.

Default draft shape:

```text
Hey [AE] — I’m getting spun up on [Account] and want to make sure I’m shaping the demo around the real deal motion.

Can we sync on:
1. what triggered the evaluation / why now,
2. who’s in the room and who can block,
3. any known CRM, email, security, data, migration, or roadmap risks,
4. anything already promised around functionality, timeline, pricing, or security,
5. what the customer needs to believe or validate by the end of the demo?

If there’s a Gong/Apollo/Granola/Zoom recording or transcript from discovery or the last customer call, can you drop it here too? I’ll use that to build the demo story and avoid turning this into a generic feature tour.
```

______________________________________________________________________

## AE Sync Prep

Use this when an SC is assigned an opportunity, has an internal AE sync before the demo, or needs to pressure-test whether the deal is ready for a customer-facing technical call.

The goal is not to create a customer script yet. The goal is to help the SC use the AE sync to uncover blockers, missing context, risky promises, technical constraints, and the story the demo needs to tell.

For assigned-opportunity / AE-sync prep intent, the recommended AE sync questions are surfaced **alongside the Copyable Message to AE / Dealroom** in the visible response (under the heading `## Recommended AE Sync Questions`), not as a deferred follow-up. This expanded AE Sync Prep package (blocker scan, pre-demo story hypothesis, SC posture, full question table) is generated when the SC selects deeper AE-sync prep from the Pick Your Path menu, when a Calendar/Gmail alignment surfaces additional risk, or when meeting evidence has been analyzed. It does not replace the visible copyable-message-first surface or the Pick Your Path menu.

If the SC says the AE sync or customer meeting is already on calendar, run Calendar + Gmail alignment before this output. The questions should reflect the actual invite, attendees, agenda, and recent email threads rather than only SFDC/Slack assumptions.

### Calendar + Gmail Alignment Add-On

Use this add-on before the AE Sync Prep template when a scheduled event exists or is implied:

```markdown
## Calendar + Gmail Alignment: [Account Name]

### Calendar Match
- **Status** — [found / partial / not_found / unavailable].
- **Event** — [title, date/time, organizer, attendees]. Source: Calendar event.
- **Meeting type** — [AE sync / customer demo / technical call / unclear].

### Recent Email Signals
- **Status** — [found / partial / not_found / unavailable].
- **Threads** — [1-3 bullets with subject/date/signal]. Source: Gmail thread.

### Alignment Risks
- **Attendee mismatch** — [none or describe].
- **Objective mismatch** — [none or describe].
- **Commitment risk** — [pricing/security/product/timeline promise found in email, or none detected].
- **Missing context** — [what the AE must confirm].
```

Then generate AE Sync Prep questions that directly address the alignment risks.

### Output Template

```markdown
## AE Sync Prep: [Account Name]

### Sync Objective

Use the AE sync to confirm what must be true for the deal to move forward, what could block it, and what story the demo needs to prove for the customer.

### What To Confirm With AE

| Area | Question | Why It Matters |
|---|---|---|
| Deal motion | What triggered this evaluation, and what changes if the customer does nothing? | Anchors Why Buy Anything and prevents feature-tour demos. |
| Stage / next step | What is the next customer-facing milestone after the demo? | Prevents demos without an advancement path. |
| Audience | Who is attending, who owns the technical decision, and who can block the deal? | Shapes depth, language, and landmine handling. |
| Pain | Which pain is real enough that the customer would spend money to fix it? | Determines what the demo must lead with. |
| Blockers | Any CRM, email, security, data, migration, procurement, or roadmap risk already known? | Lets the SC pressure-test feasibility before the call. |
| AE commitments | Has anything been promised around pricing, security, product behavior, implementation timeline, or roadmap? | Prevents the SC from contradicting or accidentally validating unsupported commitments. |
| Meeting evidence | Is there a Gong, Apollo, Granola, Zoom, or other recording/transcript from discovery or the last customer call? | Grounds the demo in buyer language instead of AE interpretation alone. |
| Success criteria | What does the buyer need to believe, see, or validate by the end of the demo? | Turns the demo into a story with a defined outcome. |

### Blocker Scan

- **Technical blockers** — [CRM/email/security/integration/data/migration risks]. Confidence: [verified/inferred/assumed]. Source: [source].
- **Commercial/process blockers** — [budget, EB, decision process, procurement, timing]. Confidence: [verified/inferred/assumed]. Source: [source].
- **Knowledge gaps** — [missing facts that should be asked before demo setup].

### Pre-Demo Story Hypothesis

- **Before** — [customer's current state/pain].
- **Negative consequences** — [what gets worse if unchanged].
- **After** — [state Apollo should help them believe is possible].
- **Why Apollo** — [primary differentiator to prove].
- **Demo proof point** — [capability or workflow to show first].

### SC Posture on the AE Sync

- Be the technical expert: validate feasibility, name risks early, and separate product truth from sales optimism.
- Be deal-progressive: ask questions that reveal whether the customer can actually move forward.
- Be story-led: push the AE to define the buyer-facing narrative before building demo assets.
```

Rules:

- If the source data is sparse, make the AE questions the main output rather than inventing a demo story.
- If the AE has already provided answers, label them `Source: User-provided AE sync notes` and preserve confidence tags.
- If the AE-sync output identifies blocker risk, do not generate detailed Apollo AI setup prompts until the blocker is acknowledged in the AE-sync output, Landmines, or Open Questions.

______________________________________________________________________

## Meeting Evidence Intake and Analysis

Use this after the SC provides a transcript, raw notes, or a link to a call recording/source such as Gong, Apollo, Granola, Zoom, or another meeting system.

### Intake Rule

If the SC has not provided a transcript, raw notes, or accessible call link, ask for one before building the final demo story:

```text
Before I lock the demo story, can you share the Gong, Apollo, Granola, Zoom, or other call transcript/link from discovery or the latest customer meeting? If the link is not accessible here, paste the transcript, AI summary, or raw notes. I’ll use that to extract buyer language, blockers, success criteria, and the strongest demo angle.
```

If only a link is provided and the runtime cannot access it, do not pretend to analyze the call. Ask the SC to paste the transcript, AI summary, or raw notes.

### Output Template

```markdown
## Meeting Evidence Analysis: [Account Name]

### Evidence Source

- **Source type** — [Gong / Apollo / Granola / Zoom / pasted transcript / pasted notes / user-provided summary].
- **Access status** — [analyzed transcript / analyzed notes / link provided but not accessible / summary only].
- **Confidence rule** — [verified for direct transcript excerpts; inferred for summaries or recollections].

### Buyer Language

- **Quote / phrase** — [exact language if available]. Confidence: [verified/inferred]. Source: [source].

### Deal-Moving Signals

- **Pain** — [what the buyer says hurts]. Source: [source].
- **Decision criteria** — [what they need to see or validate]. Source: [source].
- **Blocker** — [technical, security, migration, data, procurement, or adoption risk]. Source: [source].
- **Stakeholder signal** — [who cares / who can block / who owns the decision]. Source: [source].

### Demo Implications

- **Lead with** — [capability or workflow to show first].
- **Story angle** — [Before → Negative Consequences → After → Why Apollo].
- **Avoid** — [feature, claim, or path that could create risk].
- **Ask first** — [question to confirm before demoing].

### What Changed

- **Brief update** — [section that changes]. Confidence: [verified/inferred/assumed]. Source: [source].
```

Analysis rules:

- Prefer exact buyer language over AE paraphrase.
- Treat AI call summaries and SC recollections as `[inferred]` unless direct quotes or transcript excerpts are provided.
- Pull out product commitments, security claims, implementation timelines, or roadmap references as landmines.
- Do not build detailed Apollo AI demo setup prompts until meeting evidence has been analyzed or the SC explicitly chooses to proceed without it.

______________________________________________________________________

## What Changed Summary

Use this after any refresh or contextual update.

```markdown
## What Changed

- **[Section]** — [New or changed claim]. Confidence: [verified/inferred/assumed]. Source: [source label].
- **[Section]** — [Resolved or newly created gap]. Source: [source label].
- **No change** — [Section] remains unchanged because no new evidence was found or provided.

### Conflicts or Unknowns

- [Conflict or unknown framed as an open question.]
```

Rules:

- Do not list cosmetic changes.
- Do not claim a field changed unless the source supports it.
- If old and new context conflict, preserve both and route to Open Questions or Landmines.
- A newer claim may supersede an older claim only when it is timestamped, addresses the same field/topic, comes from the same or stronger source type, and clearly replaces the older state.
- User-provided summaries do not supersede SFDC, Gong, Slack, or Snowflake records unless they include a direct quote/raw excerpt or the SC explicitly states they are correcting the source of record. If not, preserve both and flag the discrepancy.

______________________________________________________________________

## Audience Adjustment

Use when demo attendees change, an executive joins, a technical evaluator joins, or the SC asks to adjust the demo for a different audience.

### Output Template

```markdown
## Audience Adjustment: [Account Name]

### New or Changed Attendees

- **[Name or role]** — [title / likely role in deal]. Confidence: [verified/inferred/assumed]. Source: [source].

### What This Changes

- **Demo emphasis** — [what to emphasize now and why].
- **Talk track** — [how to frame the value for this audience].
- **Landmines** — [what to avoid or handle carefully].
- **Open question** — [question to ask early in the meeting].

### Revised Demo Flow

1. **[Capability]** — Show this because [audience-specific reason]. Source: [source].
2. **[Capability]** — Show this because [audience-specific reason]. Source: [source].
```

Audience guidance:

| Audience | Emphasize | Avoid |
|---|---|---|
| CRO / revenue executive | Business impact, urgency, consolidation, risk reduction, productivity. | Deep configuration unless tied directly to business impact. |
| RevOps / systems owner | Workflow logic, governance, CRM fit, migration, admin control. | Hand-wavy strategic claims without implementation detail. |
| Frontline manager | Rep productivity, reporting, coaching, adoption, sequence performance. | Over-indexing on admin setup. |
| Rep / end user | Day-to-day workflow, speed, ease of use, data quality in flow. | Executive business-case framing only. |
| Security / IT | Data handling, integrations, permissions, auditability, known blockers. | Unverified claims about security posture. |

______________________________________________________________________

## Competitive Repositioning

Use when a competitor appears after the initial brief or the buyer reframes the evaluation.

### Output Template

```markdown
## Competitive Repositioning: [Competitor]

### What Changed

[Describe what new competitor signal appeared. Confidence: [verified/inferred/assumed]. Source: [source].]

### Deal-Specific Comparison

| Buyer criterion | Apollo angle | Competitor risk | Demo adjustment |
|---|---|---|---|
| [criterion] | [Apollo strength tied to evidence] | [risk or unknown] | [what to show or avoid] |

### Talk-Track Hooks

- "Instead of comparing feature-by-feature, let's anchor on [buyer outcome]."
- "[Deal-specific positioning sentence grounded in the brief.]"

### Claims to Avoid

- Do not make generic battlecard claims as verified facts.
- Do not attack a competitor where the buyer has a personal or executive connection.
- Do not claim technical superiority unless supported by deal evidence or approved reference material.

### Open Questions

- [Question to clarify the buyer's comparison criteria.]
```

If the competitor is not covered in `competitive-positioning.md`, state:

`Competitive positioning for [competitor] is not in the reference map — verify with PMM before making claims.`

______________________________________________________________________

## Data Test or Data Duel Update

Use when the SC provides data test results, fill-rate results, enrichment outcomes, or prospect feedback on data quality.

Route the result:

| Result type | Where it goes |
|---|---|
| Strong Apollo performance against incumbent | Pain Points and Competitive Landscape. |
| Weak or mixed Apollo performance | Landmines and Open Questions. |
| Coverage by region/persona | Recommended Demo Flow and Trial Success Criteria. |
| Prospect disputes result | Open Questions and Landmines. |
| Result changes buying criteria | Decision Criteria in brief context and demo flow. |

Output pattern:

```markdown
## Data Test Update

### Result

[Summarize the result with confidence/source.]

### Impact on Demo Strategy

- **Show** — [what to emphasize].
- **Handle carefully** — [what could create risk].
- **Ask** — [question to clarify buyer interpretation].

### Sections Updated

- [Brief section] — [change].
```

Do not overstate data test results. A sample test is evidence, not universal proof.

______________________________________________________________________

## Post-Demo Debrief

Use this after a demo, technical call, trial setup session, or follow-up demo.

### Internal Debrief Questions

```markdown
## Post-Demo Debrief: [Account Name]

### What Landed

- Which demo moment generated the most engagement?
- Which pain point did the prospect explicitly confirm?
- Which stakeholder reacted most positively, and what did they say?
- Did the highest-priority demo flow item from the brief still feel like the right lead?

### What Did Not Land

- Where did attention drop?
- Which capability created confusion?
- Which claim, workflow, or UI moment required extra explanation?
- Did any assumed pain fail to validate?

### New Information

- Did a new stakeholder, competitor, timeline, decision criterion, or metric surface?
- Did the prospect correct anything from SFDC, Slack, or prior discovery?
- Did the buying process or paper process change?

### Technical Concerns

- Were any CRM, email, security, data, migration, or workflow blockers raised?
- Did the prospect ask for a capability that Apollo lacks or handles differently?
- Are any technical claims now dependent on Product, Engineering, Security, or PMM validation?

### Next Steps

- What did we commit to?
- Who owns each action?
- What is the next meeting or deadline?
- What must be updated in the brief before the next customer-facing interaction?
```

### Debrief Output

After the SC answers any debrief questions or provides notes, produce:

```markdown
## Debrief Summary

- **Confirmed** — [confirmed pain, criterion, stakeholder, or next step]. Source: [user-provided notes].
- **Changed** — [what changed from the prior brief]. Source: [user-provided notes].
- **Risk** — [new landmine or blocker].
- **Next action recommendation** — [recommendation only; no execution].
- **Update needed** — [brief section or prompt set that should be refreshed].
```

If the SC asks for a customer follow-up email, Slack recap, SFDC update, or internal message, use the SKILL.md handoff protocol for deal-execution.

______________________________________________________________________

## Trial Success Criteria

Use when the SC asks for trial planning, trial setup, trial validation, POC prep, or mid-trial check-in.

If trial scope is unclear, produce trial planning output first. Trial planning defines success criteria, evaluation owner, data dependencies, integration dependencies, and safety constraints. Trial setup configures or proposes Apollo objects only after the evaluation target is clear.

### Success Criteria Template

```markdown
## Trial Success Criteria: [Account Name]

### Evaluation Goal

[What the buyer is trying to prove. Confidence: [verified/inferred/assumed]. Source: [source].]

### Success Criteria

| Criterion | Why it matters | How to validate in Apollo | Risk / open question |
|---|---|---|---|
| [criterion] | [pain or decision criterion] | [Apollo workflow / report / setup] | [risk or unknown] |

### Trial Setup Dependencies

- **Data** — [lists, accounts, contacts, fields, enrichment requirements].
- **Integrations** — [CRM, email, calendar, security, permissions].
- **People** — [trial owner, RevOps/admin, manager, end users].
- **Timeline** — [trial start, check-in, decision date].

### Mid-Trial Check-In Questions

- What have you validated so far?
- Which workflow or dataset is not matching expectations?
- What would need to be true for this trial to be considered successful?
- Who else needs to see results before a decision?
```

Rules:

- Success criteria should be measurable when possible.
- If no success criteria are known, generate trial planning prompts and trial success criteria before any broad setup prompt set.
- Trial setup should connect back to the buyer's stated decision criteria, not generic Apollo feature coverage.

______________________________________________________________________

## Second Demo or Follow-Up Demo

Use when the buyer asks for another demo focused on a specific use case, stakeholder, competitor, or technical proof point.

Output:

```markdown
## Follow-Up Demo Plan: [Account Name]

### New Focus

[What changed and why this demo exists.]

### Revised Show Plan

1. **[Capability]** — [why this is first now]. Source: [source].
2. **[Capability]** — [why this is next]. Source: [source].

### Talk-Track Reset

"Last time we focused on [previous focus]. Today I want to go deeper on [new focus] because [buyer reason]."

### Must-Confirm Questions

- [Question tied to the new focus.]

### Apollo AI Context Center Payload + Prompt Adjustments

- **Context Center payload (Step 0)** — Regenerate the Apollo AI Context Center payload to reflect the new focus, audience, or competitor before regenerating prompts. The SC pastes the updated payload into Apollo Settings → AI Context Center using the placement-and-safety guidance in `references/apollo-ai-prompt-patterns.md` Step 0.
- [Prompt to regenerate or modify, ordered by the updated strategic angle. Each prompt's "Why this works" must reference the updated Context Center payload.]
```

Do not repeat the original demo flow unless the buyer's new ask is actually the same as the original ask.
