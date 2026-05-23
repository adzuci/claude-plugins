---
name: khaydien-context-structuring
description: Builds production-ready context payloads for Apollo Agent queries (the @Apollo Agent in #gtme-support-apollo-agent-forum) AND optionally posts them directly to Slack via MCP. Produces a payload the teammate can (a) copy-paste, (b) save as a Slack draft for review, or (c) send immediately to channel C0A3HGMHMN2 with the Apollo Agent (user U0ABEQ94H7Z) properly tagged. Codifies the Apollo Agent's own stated ideal prompt format plus the two proven patterns from the channel: Khaydien's natural-language client-question style and Jason's CONTEXT QUERY Pipeline 5 structured template. Triggers on "build apollo agent query", "apollo agent prompt", "post to apollo agent", "ask apollo agent", "structure apollo agent context", "khaydien this", "khaydien method", "ask apollo agent about [account]", "query apollo agent for [client]", "context payload for apollo agent", or any request to format or send a question to @Apollo Agent. SCOPE: Apollo Agent only. Does not fire for Glean Agent, Customer Journey Agent, or other agents.
---

# Khaydien Context Structuring

**Named for Khaydien Anderson, whose Mūcho pre-call payload (May 21, 2026) is the canonical reference for how to feed the Apollo Agent enough context to answer in one shot.**

This skill produces a copy-paste-ready Slack payload for `@Apollo Agent` and can also post the payload directly to Slack via MCP. The teammate chooses the action: copy-paste, save as Slack draft, or send immediately. All MCP write actions require explicit teammate confirmation before firing.

**Verified IDs (do not change):**

| Item | Value |
|---|---|
| Channel | `#gtme-support-apollo-agent-forum` |
| Channel ID | `C0A3HGMHMN2` |
| Apollo Agent user ID | `U0ABEQ94H7Z` |
| API tag syntax (for MCP send) | `<@U0ABEQ94H7Z>` |
| UI paste tag (for copy-paste) | `@Apollo Agent` |

The API tag and UI tag are different on purpose. `<@U0ABEQ94H7Z>` is the Slack mention spec — it resolves to a real ping when sent via API, but renders as literal text if you paste it into the Slack composer. `@Apollo Agent` is what you type in the Slack UI to trigger autocomplete. The skill emits the right one for the action chosen.

______________________________________________________________________

## When to use this skill

Fire on any of these:

- "build apollo agent query", "apollo agent prompt", "structure apollo agent context"
- "khaydien this", "khaydien method", "khaydien-ify"
- "ask apollo agent about [account]", "query apollo agent for [client]"
- "context payload for apollo agent", "prep apollo agent message"
- Any explicit ask to format a question for posting to `@Apollo Agent`

**Do not fire for:**

- Glean Agent queries (use the GTME Resolution Agent directly)
- Customer Journey Agent queries
- General Apollo prompt engineering (use `apollo-ai-prompt-engineering` instead, which is for PowerUps, Email Writer, scoring engines)
- Internal client deliverables (use `convergent-copywriting` or relevant deliverable skill)

______________________________________________________________________

## What the Apollo Agent actually wants (its own words)

From the agent's self-description (Slack thread `1775950352.796659`, April 11, 2026), the agent told us directly what it needs to give a clean answer:

1. **Task**: what you are trying to decide or write
1. **Audience**: customer vs internal, and their level (admin, end-user, engineer)
1. **Customer identifiers**: team ID, domain, user email, godmode link, as **separate fields** (not one overloaded string)
1. **Question list**: 1 to 5 precise questions, topically related (do not mix unrelated topics in one post)
1. **Output requirements**: "respond in JSON with this schema" OR "use sections A/B/C", explicit
1. **Constraints**: tone, length, whether to include links, whether to cite sources

The agent supports confidence labels: **VERIFIED** (KB or backend data), **INFERRED** (logical conclusion with stated assumptions), **UNKNOWN** (cannot determine, with follow-ups for what is missing).

The agent has live access to: Apollo internal codebases and runtime, Apollo KB, Jira (read + create), Slack workspace search, Google Sheets, PagerDuty, Notion. The agent **cannot** browse godmode pages like a human (it queries internal DB from the identifier in the URL), cannot HTTP-check arbitrary URLs in real time, cannot take direct action (refunds, ops), and is optimized for interactive single-request use, not high-QPS automation.

______________________________________________________________________

## The Two Modes

### Mode A: Khaydien-style Natural Language

Use when the query originates from a **client question or call** and the human context (relationship, urgency, account dynamics) matters for how the answer is framed.

Strengths: reads naturally, easy for the agent to weight what is critical vs. nice-to-have, easy for a teammate to author from a forwarded client email.

Reference example (Mūcho, May 21 2026):

> "I'm working with Mūcho (godmode link) and have three technical questions from their Growth Manager ahead of our call on the 27th. Context: French employee benefits platform, 4 BDRs + 7 AEs, Pipedrive connected. Heavy sequences + Dialer users (64k GenPipe, 13k Dialer). Louis manages sequence setup on behalf of his BDRs, which is creating the ownership issue below. They want to move toward a more automated, signal-driven workflow. 1. [question] 2. [question] 3. [question]. Here is Louis's full email for context: [paste]"

### Mode B: CONTEXT QUERY Pipeline 5 Structured Template

Use when you want **machine-parseable output**, are running a **diagnostic** (account health, config check, issue triage), or are firing as part of an **automated pipeline**.

Strengths: explicit fields, predictable agent response, parseable JSON output when requested, consistent across reruns.

Reference examples: Domo SFDC trigger verification, VideoAmp deliverability diagnostic, multi-account portfolio Jira cross-reference.

### Decision rule

| Situation | Mode |
|---|---|
| Client emailed a question, you are prepping for a call | A |
| Account is at-risk, you need a config sweep | B |
| You want JSON back to feed downstream automation | B |
| You have a single specific KB-style "does Apollo do X" question | A or B (either works) |
| Cross-account portfolio diagnostic | B |
| Pre-meeting briefing for one named contact | A |

When in doubt, default to **Mode B**. The structure forces precision and makes the response easier to act on.

______________________________________________________________________

## Required Context Blocks (both modes)

The skill enforces these. If any are missing, the skill asks the teammate before producing output.

| Block | Required | Notes |
|---|---|---|
| `Task` | Yes | One of: `research_for_reply`, `diagnose_issue`, `verify_feature`, `check_account_config` |
| `Audience` | Yes | One of: `customer_admin`, `customer_end_user`, `internal_gtme` |
| `team_id` | Conditional | Required if asking about a specific customer. Format: 24-char ObjectID (e.g., `68dd80c2f62bd1000d40e67c`) |
| `domain` | Conditional | Required if no team_id. The customer's email domain |
| `user_email` | Optional | Specific user being investigated |
| `godmode_url` | Optional but recommended | Full godmode URL. Helps the agent identify the right team faster |
| `Questions` | Yes | 1 to 5. Topically related. No mixing unrelated subjects in one post |
| `Output format` | Yes | Plain text sections, or JSON in code block per v1.0 schema |
| `Constraints` | Optional | Tone, max length, include links, cite sources |
| `Confidence labels` | Yes (recommended) | Request VERIFIED / INFERRED / UNKNOWN on each answer |

### Pre-flight checklist (skill enforces before output)

- [ ] Customer identifiers split into **separate fields**, not one overloaded URL string
- [ ] Questions are ≤5 and topically related (if not, split into multiple posts)
- [ ] Output format specified (sections vs JSON)
- [ ] Audience specified
- [ ] Confidence labels requested
- [ ] Question is not asking for things outside agent scope (refunds, ops actions, video/audio, secrets, external web scraping)

______________________________________________________________________

## Mode A Template (Khaydien-style Natural Language)

```
@Apollo Agent I'm working with [CUSTOMER] ([godmode link]) and have [N] technical questions [from CLIENT_ROLE / ahead of our call on DATE].

Context: [1-3 sentences on company stage, team size, stack, current state, what is changing or at stake. This is where you put the human story the agent needs to weight the answer.]

1. [Question 1, specific and self-contained. State what you want to know AND what success looks like (e.g., "Is this natively supported, or does it require a workaround?").]
2. [Question 2, related topic.]
3. [Question 3, related topic.]

[Optional: Here is [CLIENT_NAME]'s full email for context:]
[Paste verbatim or sanitized email.]

Respond with VERIFIED / INFERRED / UNKNOWN confidence labels on each answer. Include KB links where applicable.
```

______________________________________________________________________

## Mode B Template (CONTEXT QUERY Pipeline 5)

```
@Apollo Agent CONTEXT QUERY (Pipeline 5: Communications Orchestrator)
Task: [research_for_reply | diagnose_issue | verify_feature | check_account_config]
Audience: [customer_admin | customer_end_user | internal_gtme]
Customer: [CUSTOMER_NAME]
Team ID: [24-char ObjectID]
Domain: [customer.com]
Godmode: [full godmode URL]
Notion BoB: [optional sub-page link]

[1-3 sentences of situational context: stage of relationship, urgency, what is at stake. Skip if pure feature verification.]

Questions:
1. [Specific question 1]
2. [Specific question 2]
3. [Specific question 3]

For each question, provide:
- Answer
- Confidence label: VERIFIED (KB or backend data) | INFERRED (logical conclusion with assumptions stated) | UNKNOWN (cannot determine, with what is missing)
- Evidence (KB link, backend data point, Jira ticket, Slack thread)
- Customer impact (if applicable)
- Recommended next step or reply snippet

Output format: [Plain text sections | JSON in code block per schema v1.0]
```

______________________________________________________________________

## JSON Response Schema (v1.0)

When you want machine-parseable output, append this to the Mode B prompt: `Output format: JSON in code block per schema v1.0.` The Apollo Agent will respond with this validated structure (see `templates/response-schema-v1.json` for the full schema). Top-level keys the agent commits to:

- `schema_version` (always "1.0")
- `request_id`
- `task`, `audience`, `customer` (split into `team_id`, `domain`, `user_email`, `godmode_url`)
- `questions[]` with `question_id` and `question`
- `results[]` with `question_id`, `answer`, `confidence_label`, `confidence_reason`, `evidence[]`, `kb_links[]`, `customer_impact`, `recommended_reply_snippet`, `follow_ups[]`, `assumptions[]`, `limitations[]`
- `meta` with `sources_used`, `generated_at`, `redactions`
- `errors[]`

Keys always exist (empty arrays / nulls when no data) so the parser does not need conditionals.

______________________________________________________________________

## Confidence Label Rules (the agent's own definitions)

- **VERIFIED**: Explicit KB passage, or exact value pulled from backend data for that team/user. Cite the source.
- **INFERRED**: Reasonable conclusion from partial evidence. The agent lists assumptions in the `assumptions[]` field.
- **UNKNOWN**: Cannot access the needed data, or the question is ambiguous. The agent populates `follow_ups[]` with what is missing.

Always request these. They are the agent's first line of defense against fabrication and your first line of defense against shipping wrong answers to a customer.

______________________________________________________________________

## Anti-Patterns (do not do these)

| Anti-pattern | Why it hurts |
|---|---|
| Mixing 5+ unrelated questions in one post | Agent cannot prioritize; quality of every answer drops |
| Single overloaded "Customer: [godmode url with everything jammed in]" | Agent told us explicitly to split identifiers into separate fields |
| Asking for refunds, contract changes, manual ops | Agent will not execute these; flag for human |
| Asking the agent to watch a video or transcribe audio | Out of capabilities |
| Asking the agent to HTTP-check a third-party URL | Agent cannot browse the live web |
| Asking for secrets, credentials, API keys | Hard no |
| Skipping the output format spec | You get freeform prose; harder to act on |
| No confidence labels requested | You cannot tell verified facts from guesses |
| Posting without team_id or domain when asking account-specific question | Agent has no way to look up the right team |

______________________________________________________________________

## Worked Examples

### Example 1: Khaydien's Mūcho (Mode A, the canonical reference)

```
@Apollo Agent I'm working with Mūcho (https://app.apollo.io/?godemail=louis.lamonerie%40getmucho.fr#/home) and have three technical questions from their Growth Manager ahead of our call on the 27th.

Context: French employee benefits platform, 4 BDRs + 7 AEs, Pipedrive connected. Heavy sequences + Dialer users (64k GenPipe, 13k Dialer). Louis manages sequence setup on behalf of his BDRs, which is creating the ownership issue below. They want to move toward a more automated, signal-driven workflow.

1. Does Apollo have a native lead scoring or prioritisation view based on prospect behavior inside sequences, specifically email opens (especially repeat opens on the same email), link clicks, and job changes? Is there a built-in way for BDRs to see a ranked list of high-intent contacts to call next, or does this require a third-party integration?

2. Can auto-enrollment into sequences be triggered natively based on HR signals (job changes, headcount growth, active job postings) matching saved search criteria? Their key constraint is excluding contacts who already carry specific Apollo labels (current customer, already demo'd, synced from Pipedrive). Is label-based exclusion supported in the trigger/rule logic, and if so what is the setup path?

3. When Louis enrolls contacts into a sequence on behalf of a BDR, he becomes the account owner in Apollo, so Slack notifications tag him instead of the BDR who owns the outreach. Is there a way to assign account or contact ownership to the sequence sender (rather than the enroller) at the time of enrollment, or is there a bulk override at the sequence level? If not, is the standard workaround to pull the sender field rather than the owner field via Zapier/webhook?

Here is Louis's full email for context:
[paste email]

Respond with VERIFIED / INFERRED / UNKNOWN confidence labels on each answer.
```

**Why it worked**: Rich opening context paragraph (company, stack, team shape, what is changing), three numbered questions each ending with "is this native or workaround", full email pasted as supporting context, explicit confidence label request. The agent returned a clean answer with labels and a recommended positioning paragraph Khaydien could use on the call.

### Example 2: VideoAmp At-Risk Diagnostic (Mode B)

```
@Apollo Agent CONTEXT QUERY (Pipeline 5: Communications Orchestrator)
Task: diagnose_issue
Audience: internal_gtme
Customer: VideoAmp
Team ID: 68cdb2bf158a70001d7ccf73
Domain: videoamp.com (also govideoamp.com)
Godmode: https://app.apollo.io/?godemail=megan.taylor%40videoamp.com#/
Notion BoB: https://www.notion.so/apolloio/VideoAmp-2dbab2b3b49681a3ba46ea0c30bd136b

P0 at-risk account. SVP Joe Kotz gave a two-week ultimatum on April 10. Primary issue is deliverability: emails show delivered in Apollo but land in spam or disappear. Team adoption cratering.

Questions:
1. Deliverability health across all connected mailboxes (videoamp.com AND govideoamp.com), bounce rates, mailbox errors, warmup status
2. SFDC sync errors, workflow failures, sequence health issues
3. Open Jira tickets or PagerDuty incidents for VideoAmp or team ID 68cdb2bf158a70001d7ccf73
4. Tracking subdomain configuration status
5. Credit usage vs allocation

For each: description, source (ticket ID), root cause, resolution steps, confidence (VERIFIED/INFERRED/UNKNOWN).

Output format: Plain text sections, prioritized by severity.
```

**Why it worked**: All five customer identifiers split out, urgency stated in one sentence, five topically related questions (all infrastructure/health), explicit confidence labels and output format. Account had a live churn clock and the agent returned actionable items prioritized.

### Example 3: Domo Feature Verification (Mode B)

```
@Apollo Agent CONTEXT QUERY (Pipeline 5: Communications Orchestrator)
Task: verify_feature
Audience: customer_admin
Customer: Domo
Team ID: 68dd80c2f62bd1000d40e67c
Godmode: https://app.apollo.io/?godemail=greg.auxier%40domo.com#/sequences/69d836abb3be15000d465996

Greg Auxier (Dir, Global Sales Ops) updated Domo's outbound workflows per our recommendations. He is asking me to validate his setup.

Questions:
1. Workflows at this filter (https://app.apollo.io/#/workflows?sortByField=updated_at&sortAscending=false&archived=false&qName=orchestration) - are they correctly configured with verified email gates and enrichment steps before sequence enrollment?
2. Sequence (https://app.apollo.io/#/sequences/69d836abb3be15000d465996) - is the AI content using the correct Content Center product context? Is step 1 set to manual approval?
3. Domo's current credit usage vs allocation - Greg is concerned about over-using credits with the enrichment steps.

Respond with: what looks correct, what needs fixing, specific credit usage numbers, VERIFIED/INFERRED/UNKNOWN labels on each.

Output format: Plain text sections.
```

**Why it worked**: One specific customer admin context, three topically related questions (all "is this configured correctly"), exact URLs to the artifacts under inspection, explicit ask for numbers not generalities, confidence labels.

______________________________________________________________________

## Quick-Fill Snippet (copy-paste this and fill in)

```
@Apollo Agent CONTEXT QUERY (Pipeline 5: Communications Orchestrator)
Task: [research_for_reply | diagnose_issue | verify_feature | check_account_config]
Audience: [customer_admin | customer_end_user | internal_gtme]
Customer: [name]
Team ID: [24-char ObjectID]
Domain: [customer.com]
Godmode: [URL]

[One to three sentences of situational context.]

Questions:
1. [Specific question]
2. [Specific question, related topic]
3. [Specific question, related topic]

For each: answer, confidence (VERIFIED/INFERRED/UNKNOWN with reasoning), evidence, customer impact, recommended next step.

Output format: [Plain text sections | JSON code block per schema v1.0]
```

______________________________________________________________________

## How this skill executes

When triggered, the skill runs three phases. The MCP posting phase only fires with explicit teammate confirmation.

### Phase 1: Gather and validate

1. **Ask for the minimum required inputs** if not provided: customer name, identifiers (team_id or domain), questions, audience, mode (A or B).
1. **Select mode** using the decision rule above. Confirm with the teammate if ambiguous.
1. **Validate** the questions: topically related, ≤5, not asking for out-of-scope items (refunds, ops, video, secrets, third-party URL checks).

### Phase 2: Build the payload

4. **Generate the payload** in the chosen mode.
1. **Display the payload as a fenced code block for review** (using `@Apollo Agent` plain text in the preview so the teammate sees what they would copy-paste).
1. **Ask the teammate which action they want**: copy-paste only, draft, or send immediately.

### Phase 3: Action (only with explicit confirmation)

| Action | Tool | Tag format | Confirmation required |
|---|---|---|---|
| Copy-paste | None (skill returns payload only) | `@Apollo Agent` (plain text, teammate retypes in Slack UI) | None, this is the default |
| Draft to Slack | `Slack:slack_send_message_draft` | `<@U0ABEQ94H7Z>` (real mention) | Single "draft it" confirmation |
| Send immediately | `Slack:slack_send_message` | `<@U0ABEQ94H7Z>` (real mention) | Explicit "send now" confirmation, NOT implied by "yes" or "ok" |

**Confirmation gate (mandatory before any MCP write):**

The skill MUST display the exact message that would be posted, the exact channel (`C0A3HGMHMN2` / `#gtme-support-apollo-agent-forum`), and the exact tool that will fire, then wait for one of:

- "draft it" or "save as draft" → fires `slack_send_message_draft`
- "send now" or "post it now" → fires `slack_send_message`
- "copy only" or "don't post" → returns the payload only

Ambiguous replies ("yes", "ok", "go") get a clarifying question, NOT an automatic send.

______________________________________________________________________

## Slack Posting Workflow (technical reference)

### Draft (recommended default for first-time use)

Saves to the channel's draft area so the teammate can review and edit in the Slack UI before sending. Lower-risk than immediate send.

```
Tool: Slack:slack_send_message_draft
Parameters:
  channel_id: "C0A3HGMHMN2"
  message: "<@U0ABEQ94H7Z> [the payload, with @Apollo Agent replaced by the real mention syntax]"
```

Note: `slack_send_message_draft` allows only ONE draft per channel. If a draft already exists, the tool returns `draft_already_exists` and the teammate needs to clear or send the existing draft first.

### Send immediately

Posts the payload to the channel as a new top-level message (not a thread reply). Use only when the teammate has reviewed the payload and explicitly confirmed.

```
Tool: Slack:slack_send_message
Parameters:
  channel_id: "C0A3HGMHMN2"
  message: "<@U0ABEQ94H7Z> [the payload, with @Apollo Agent replaced by the real mention syntax]"
```

### Reply in an existing thread

If the teammate wants to follow up on an existing Apollo Agent thread (for example, asking a clarifying question after an initial response), pass `thread_ts`:

```
Tool: Slack:slack_send_message
Parameters:
  channel_id: "C0A3HGMHMN2"
  thread_ts: "[parent message ts, e.g., 1779364961.068259]"
  message: "<@U0ABEQ94H7Z> [follow-up payload]"
```

### Tag format conversion (critical)

Before any MCP send or draft, the skill ALWAYS converts the human-readable `@Apollo Agent` in the payload to the API mention syntax `<@U0ABEQ94H7Z>`. This is the only programmatic edit the skill makes to the payload between preview and send. Everything else (question wording, context paragraph, customer identifiers) ships verbatim from what the teammate approved.

If the teammate wants to preview the post-conversion message before sending, the skill shows the exact final message body including the `<@U0ABEQ94H7Z>` syntax.

### What the skill will NOT do

- Will not send without an explicit confirmation matching one of the three action phrases above
- Will not post to channels other than `C0A3HGMHMN2`
- Will not tag any user other than `U0ABEQ94H7Z` (the Apollo Agent)
- Will not post messages containing client PII, credentials, or other sensitive fields without flagging them first
- Will not schedule messages (use the regular send if you want it to go now; if you need a delayed send, ask explicitly and the skill will use `slack_schedule_message`)

______________________________________________________________________

## Templates folder

- `templates/mode-a-natural-language.md` — Khaydien-style natural language template, fillable
- `templates/mode-b-context-query.md` — CONTEXT QUERY Pipeline 5 structured template, fillable
- `templates/response-schema-v1.json` — Apollo Agent's validated JSON response schema, for parsing structured replies
- `templates/posting-workflow.md` — exact Slack MCP tool calls, verified IDs, guardrails, and failure modes

______________________________________________________________________

## Source attribution

- Khaydien Anderson's Mūcho payload, Slack ts `1779364961.068259`, May 21 2026 (canonical natural-language reference)
- Apollo Agent's self-described ideal prompt format and JSON schema, Slack ts `1775950352.796659`, April 11 2026
- CONTEXT QUERY Pipeline 5 format, originated in `#gtme-support-apollo-agent-forum` (Domo, VideoAmp, portfolio diagnostics, April 11-12 2026)

______________________________________________________________________

*Version: 1.0 | Skill format: Anthropic SKILL.md*
*Scope: Apollo Agent queries only (`@Apollo Agent` in `#gtme-support-apollo-agent-forum`)*
*Maintained by: Apollo GTME Team*
