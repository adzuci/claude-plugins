# Function Layer — MCP Execution Reference

This file maps pipeline outputs to MCP tool actions. Read this file when the task requires execution — sending a message, creating a draft, posting to Slack, or generating an artifact. Do not read this file for analysis-only tasks.

---

## Available Functions

The skill can execute actions through MCP-connected services. Each function requires the corresponding MCP server to be connected. If a required connection is missing, tell the user which connection is needed and stop — do not attempt the action.

---

### Gmail

**MCP Server:** Gmail / Google Workspace
**What it enables:** Read inbox, search threads, create drafts, send emails

| Action | When to Use | How |
|---|---|---|
| **Search inbox for sales threads** | AM/PM triage, deal review prep, GEN-SE trigger | Search for threads matching criteria (sender domain, date range, labels). Feed matching threads to the pipeline for analysis. |
| **Create reply draft** | After GEN-SE produces a safe reply | Create a draft reply threaded to the original message. Never auto-send — always draft. The rep reviews and sends. |
| **Create new email draft** | Follow-up emails, champion recaps, meeting confirmations | Create a new draft with composed content. Include recipients, subject, body. |

**Safety rule:** Never send emails automatically. Always create drafts. The rep reviews and hits send.

---

### Slack

**MCP Server:** Slack
**What it enables:** Read channels, post messages, DM users, search message history

| Action | When to Use | How |
|---|---|---|
| **Post to deal channel** | Deal status update, follow-up needed, blocker surfaced | Post a structured update in the deal's Slack channel. Tag relevant people if action is needed. |
| **DM a teammate** | SC needs to be looped in, manager needs context, AE needs info from someone | Send a direct message to the specific person with context on what's needed and why. |
| **Post notes to self** | After triage, after a call, after pipeline review | Post a structured summary to the rep's own DM (notes to self). Include open loops, next actions, risk flags. |
| **Search deal channel history** | Checking what's been discussed, finding last update, verifying commitments | Search the deal channel for recent messages to build context before taking action. |

**Channel naming convention:** Deal channels are typically named with the account name. Ask the rep for the channel name if not obvious.

---

### Google Calendar

**MCP Server:** Google Calendar
**What it enables:** Search events, check availability, context for upcoming meetings

| Action | When to Use | How |
|---|---|---|
| **Pull upcoming meetings** | AM triage ("what's on today"), call prep, deal review context | Search calendar for upcoming events. Surface meeting names, attendees, and times. |
| **Prep for a specific meeting** | "Help me prep for my call with [account]" | Find the calendar event, extract attendees and context, then pull relevant deal data from the pipeline. |

---

### Google Docs / Drive

**MCP Server:** Google Docs / Google Drive
**What it enables:** Create documents, export artifacts

| Action | When to Use | How |
|---|---|---|
| **Generate champion one-pager** | Rep needs a shareable artifact for their champion to circulate internally | Build a one-page document with: problem statement (Before Scenario), business impact (Negative Consequences), proposed outcomes (PBOs), required capabilities, success metrics, and proof points. Written in the buyer's language, not Apollo's. |
| **Generate deal summary** | Internal deal review, manager briefing, handoff documentation | Build a structured deal summary with: stage, MEDDPICC scorecard, open risks, next steps, and timeline. |
| **Export to Drive** | Rep wants to share an artifact | Export the generated document to Google Drive for sharing. |

---

### Notion

**MCP Server:** Notion
**What it enables:** Search workspace, read pages, read databases, update pages, create pages

**MCP Tools:**

| Tool | Purpose | Parameters |
|---|---|---|
| `notion_search` | Semantic search across the workspace | `query` (search terms), `page_size` (default 10, max 25) |
| `notion_fetch` | Read a specific page or database by URL/ID | `id` (page URL, UUID, or database URL) |
| `notion_update_page` | Update properties or content on a page | `page_id`, `properties` (JSON map of property names to values) |
| `notion_create_pages` | Create new pages in a database or under a parent page | `parent` (page_id or data_source_id), `properties`, `content` |

**When to query Notion:**

| Action | When to Use | How |
|---|---|---|
| **Look up deal context** | Deal review, call prep, triage enrichment, stage validation | Search by account name or deal name. Pull deal notes, stage history, stakeholder maps, internal commentary. Feed into L2A state-extractor or GEN-SE account_context. |
| **Look up competitive intel** | Competitor mentioned in thread, competitive differentiation needed | Search by competitor name (e.g., "Gong battlecard", "ZoomInfo takeout"). Pull battlecards, positioning, and proof points. Feed into GEN-SE enablement_assets for grounded competitive claims. |
| **Look up enablement content** | Thread references a product area, prospect asks about capabilities | Search by product area (e.g., "enrichment playbook", "inbound talk track"). Pull playbooks, one-pagers, ROI frameworks. |
| **Update deal page** | After a call, after stage advancement, after MEDDPICC fields change | Update the deal's Notion page with new information extracted by the pipeline. |
| **Create deal summary** | After a deal review or stage validation | Create a new page with structured deal summary (stage, MEDDPICC scorecard, risks, next steps). |

**Grounding rule:** Content retrieved from Notion is treated as `self_report` on the source quality scale. It is internal documentation, not authoritative record. Claims sourced from Notion pages should be attributed ("per internal notes" or "per deal room") and tagged `asserted` unless independently verified.

**Failure behavior:** Notion is optional. If not connected, if search returns no results, or if the connection is slow, proceed without it. Never block pipeline processing on Notion availability.

---

## Pipeline-to-Function Mapping

When the pipeline produces an output, this table tells you what to execute:

| Pipeline Output | Function to Execute |
|---|---|
| GEN-SE produces a safe reply draft | → **Gmail: Create reply draft** (threaded to original) |
| GEN-SE escalates to human | → **Slack: DM the person who needs to act** with escalation context |
| Triage surfaces open loops | → **Slack: Post notes to self** with structured open loops |
| Deal review identifies risk | → **Slack: Post to deal channel** flagging the risk |
| Stage validation finds missing MEDDPICC fields | → **Slack: Post notes to self** or **DM the AE** with specific gaps |
| Champion artifact requested | → **Generate champion one-pager** → **Google Drive: Export** |
| Call prep requested | → **Google Calendar: Pull meeting** → read relevant references → compose prep notes |
| Someone needs to be looped in | → **Slack: DM that person** with context and the specific ask |
| Deal review or stage validation requested | → **Notion: Search for deal page** → augment with reference files → compose analysis |
| Competitor mentioned in thread | → **Notion: Search for battlecard** → feed into GEN-SE enablement_assets or pipeline context |

---

## Artifact Templates

### Champion One-Pager

When asked to create a champion-facing artifact, use this structure:

```
[COMPANY LOGO AREA]

# [Problem Statement — in buyer's language]

## Current Situation
[Before Scenario — their world today, their words]

## Business Impact
[Negative Consequences — quantified where possible]

## Proposed Outcomes
[PBOs — specific, measurable improvements they care about]

## What You Need to Be Able to Do
[Required Capabilities — in buyer language, not Apollo features]

## How We Measure Success
[Metrics — the KPIs they defined]

## How Apollo Delivers This
[How We Do It — brief, connected to capabilities above]

## Proof
[Relevant proof points — customer quotes, stats, case studies from product one-sheets]
```

**Key rule:** This document is for the champion to circulate internally. It must be in the buyer's language, not Apollo's. No internal jargon. No MEDDPICC labels. No pipeline tags.

### Deal Summary (Internal)

When asked for an internal deal summary:

```
# [Account Name] — Deal Summary
Stage: [X] | ARR: [$X] | Close Date: [date]

## MEDDPICC Scorecard
M: [status] | E: [status] | D: [status] | D: [status]
P: [status] | I: [status] | C: [status] | C: [status]

## Key Risks
- [risk 1]
- [risk 2]

## Next Steps
- [next step + owner + date]

## Open Loops
- [unresolved items]
```

---

*This file defines execution capabilities. The skill reads it only when a task requires action, not analysis.*
