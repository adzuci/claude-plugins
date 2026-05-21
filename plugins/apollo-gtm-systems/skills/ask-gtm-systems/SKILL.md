---
name: ask-gtm-systems
description: Handles any GTM stack question at Apollo: Salesforce records and fields, system ownership, tool integrations, access requests, routing behavior, RVOSYS tickets. Common patterns include "who owns X", "how does X connect to Y", "what team manages Z", "why did X not sync". Checks knowledge files, Glean, and MCPs before routing to intake.
---

# Ask GTM Systems

Default inbound skill for any GTM Systems question. Work through the four retrieval tiers in order. Stop at the first tier that produces an answer.

## Step 1 — Classify the question

Determine the question domain before retrieving. Always follow the retrieval steps in order: knowledge files (Step 2) → Glean (Step 3) → MCP (Step 4). The table below shows which action applies per domain.

| Domain | Action |
|---|---|
| Salesforce field or record | Check `knowledge/salesforce/`; fall back to Salesforce MCP |
| Integration or data flow | Check `knowledge/salesforce/integrations.md`; fall back to relevant system MCP |
| Tool ownership or system overview | Check `knowledge/systems/`; cache only |
| Process question ("how do I...") | Load the relevant playbook from `knowledge/playbooks/` |
| "Why didn't X happen" | Run the diagnostic checklist from `knowledge/diagnostics/` |
| Salesforce field origin | Trace the field via SFDCgearset, SF MCP metadata, and automation docs |
| Aggregate metric requiring Snowflake | Apply the Jarvis classifier; hand off if 2+ signals fire without a record-level anchor |

## Step 2 — Check knowledge files

Load the relevant file from the `knowledge/` subdirectory. If the file covers the question with enough specificity to answer confidently, answer from it.

Cite as: `[source: knowledge/systems/salesforce.md]`

If the file exists but the specific answer is missing, note what the file covers and continue to Step 3.

## Step 3 — Search Glean

Run a Glean search using the key terms from the question. Glean searches Confluence, Notion, Slack, Google Drive, and JIRA simultaneously.

- Accept a Glean result as supporting evidence, not an authoritative answer.
- If the result is a Notion or Confluence page, read its full content before citing.
- Cite as: `[source: Glean, "<title>" (source type), retrieved <date>]`

If Glean returns nothing relevant, continue to Step 4.

## Step 4 — Query the source MCP

Pick the MCP based on the domain from Step 1. Read-only queries only.

Before querying, check MCP availability. If unavailable, skip to degraded-mode fallback from `athena.md`.

Cite live results as: `[source: <System> MCP, queried <date>]`

If the MCP query returns no answer, continue to Step 5.

## Step 5 — Route to intake

All four tiers returned nothing. Do not improvise an answer.

1. Tell the user: "I don't have a documented answer for this. Here's where to route it:"
2. Load `knowledge/intake-routing.md` and follow the routing table to pick the right channel or intake.
3. Include the user's verbatim question in the routing message.
4. Log a gap entry per the gap-flagging procedure in `agents/athena.md`.

## Output format

- Lead with the answer. One sentence summary, then detail.
- Always include a source citation.
- If the answer required multiple sources, list each one.
- If routing to intake, say clearly where and why.
