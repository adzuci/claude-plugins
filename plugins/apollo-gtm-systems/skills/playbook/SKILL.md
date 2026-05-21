---
name: playbook
description: Loads the right step-by-step playbook from knowledge/playbooks/ when a user asks how to complete a known GTM Systems process — new user access, data correction, field requests, integration issues, or MCP reconnects.
---

# Playbook

Triggered when the user's question is a process question: "how do I...", "what's the process for...", "who do I contact to...". Load the matching playbook file and walk through it with the user.

## Known playbooks

| Topic | File | Trigger phrases |
|---|---|---|
| New user access | `knowledge/playbooks/new-user-access.md` | "how do I get access to", "onboard a new user", "new user setup", "provisioning" |
| Data correction request | `knowledge/playbooks/data-correction-request.md` | "how do I fix", "this field is wrong", "data is incorrect", "correct a record" |
| New field request | `knowledge/playbooks/new-field-request.md` | "how do I request a new field", "add a field to Salesforce", "new custom field" |
| Integration issue | `knowledge/playbooks/integration-issue.md` | "integration isn't working", "data not syncing", "missing data from", "connector issue" |
| MCP reconnect | `knowledge/playbooks/mcp-reconnect-help.md` | "MCP isn't connecting", "reconnect MCP", "MCP authentication", "plugin not working" |

## Step 1 — Match the topic

Read the user's question. Match to one row in the table above. If multiple rows could match, ask one clarifying question: "Are you trying to [option A] or [option B]?"

## Step 2 — Load the playbook file

Read the matched `knowledge/playbooks/<topic>.md` file. Present the steps in order. Do not summarize or skip steps — users following a playbook need the full procedure.

Cite as: `[source: knowledge/playbooks/<topic>.md]`

## Step 3 — If no playbook matches

The user's process question doesn't match any known playbook. Treat it as an `ask-gtm-systems` question:

1. Work through Steps 2-4 of `ask-gtm-systems` (Glean, then MCP, then intake routing).
2. Log a gap entry per the gap-flagging procedure in `agents/athena.md` with topic: `missing playbook: <inferred topic>`.

This ensures the GTM Systems team learns which playbooks are missing.

## Output format

- Present playbook steps as a numbered list.
- Include any role-specific variations noted in the playbook file (some steps differ by profile or team).
- After the last step, ask: "Does that cover it, or do you want me to walk through any step in more detail?"
