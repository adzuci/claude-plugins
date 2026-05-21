---
name: why
description: Diagnoses "why did / didn't X happen" questions for GTM tools — Gong call not recording, Zoom recording not processing, unexpected Chili Piper routing, Salesforce errors — by classifying the failure type and walking through the matching diagnostic checklist from knowledge/diagnostics/.
---

# Why

Triggered by diagnostic questions: "why didn't X happen", "why did X do Y", "why isn't X working", or any question about unexpected tool behavior in the GTM stack.

## Step 1 — Classify the failure type

Read the user's description and classify to one of these categories:

| Category | Keywords | Diagnostic file |
|---|---|---|
| Gong call not recording | "call not recorded", "Gong didn't capture", "missing from Gong", "bot not joining" | `knowledge/diagnostics/no-gong-recording.md` |
| Zoom or Apollo recording not processing | "Zoom recording missing", "recording not in Apollo", "video didn't process" | `knowledge/diagnostics/no-zoom-or-apollo-processing.md` |
| Chili Piper routing | "routed to wrong rep", "meeting not assigned", "Chili Piper routing", "wrong queue" | `knowledge/diagnostics/unexpected-routing.md` |
| Salesforce error | "SFDC error", "validation rule fired", "required field missing", "duplicate rule", "flow error", "trigger error" | `knowledge/diagnostics/sf-errors.md` |
| Data not syncing | "field not updating", "record not syncing", "integration not writing" | `knowledge/playbooks/integration-issue.md` |

If the failure type doesn't match any row, classify it as `unknown` and proceed to Step 4.

## Step 2 — Load the diagnostic file

Read the matched `knowledge/diagnostics/<file>.md`. Each file contains:
- A structured checklist of root causes in order of frequency
- The data point or setting to check for each cause
- The fix or escalation path if that cause is confirmed

Work through the checklist with the user. Ask for the data point if you can't retrieve it via MCP.

Cite as: `[source: knowledge/diagnostics/<file>.md]`

## Step 3 — Verify via MCP where possible

For each checklist item that requires a live lookup:

- **Gong:** Check recording status, bot invite settings, user mapping via Gong MCP
- **Chili Piper:** Check routing rule configuration, territory assignments via Chili Piper MCP (if available) or ask user to share the routing log
- **Salesforce:** Check field values, validation rules, flow run history, and error logs via SF MCP
- **Zoom:** Check recording settings and sync status via available connectors; if unavailable, walk user through self-service check

Cite any live lookups as: `[source: <System> MCP, queried <date>]`

## Step 4 — Unknown failure type

The failure doesn't match any known category. Two options:

1. Ask one clarifying question to narrow the category: "Which tool is this happening in?"
2. If the tool is in the GTM stack but no diagnostic file covers it, route to `#sales-ops` for triage and log a gap entry per `agents/athena.md` with topic: `missing diagnostic: <tool>: <failure description>`.

## Step 5 — Escalation

If the checklist is exhausted and the root cause isn't found:

1. Tell the user what was checked and what was ruled out.
2. Route to intake: most unresolved GTM tool issues go to `#sales-ops` for triage or JIRA RS project for an admin ticket.
3. Include the checklist results in the handoff so the next person doesn't re-run it.

## Output format

Present the diagnostic as a numbered checklist. For each item:
- State what to check
- State what a passing vs failing result looks like
- State the fix if the check fails

Don't present all checklist items at once if there are more than five. Work through the most likely causes first, confirm or rule them out, then continue.
