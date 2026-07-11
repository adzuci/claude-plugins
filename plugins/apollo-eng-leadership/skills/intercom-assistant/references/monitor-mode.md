# Live Call And Chat Playbook

Use this reference through `live` during an active support chat or call.

Live call/chat assist is robust support, not autonomous browser watching. It should refresh from Intercom and optional Granola context when tools are available, and it should work from pasted notes when they are not.

## Inputs

```text
/apollo-eng-leadership:intercom-assistant live <conversation-url-or-id> [--granola <meeting-or-link>]
```

Accept any of:

- Intercom conversation URL or ID
- customer email, company, or domain
- Granola meeting link, meeting ID, notes, or transcript
- pasted chat/call notes

## Workflow

1. Run `scripts/check_dependencies.py` if tool availability is unclear.
1. Read Intercom context when available: full conversation, customer/company, recent related conversations, and account clues.
1. Read Granola notes/transcript when provided and available. If Granola is missing, use pasted notes.
1. If the customer asks a product/process/how-to/troubleshooting question, call `scripts/ask_glean_support_rep_assistant.py`.
1. If the route is clear, read `routing-and-macros.md` and propose the macro/workflow without applying it.
1. Keep known facts, inferences, and unknowns separate.
1. Propose next steps only; do not send, route, tag, snooze, close, or mutate Intercom.

## Output Shape

```text
Current ask:
<one sentence>

Verified facts:
<Intercom/GodMode/Granola facts, with source labels>

Unknowns:
<facts not yet verified>

Risk:
<customer risk, escalation risk, or "low">

Support Rep Assistant finding:
<Glean-backed answer, or "not needed / unavailable">

Recommended macro/workflow:
<clear Intercom macro/workflow, or "not clear yet">

Next best action:
<one concrete action>

Quick Script:
<1-2 natural sentences to say or send next>

Tools to check next:
<GodMode, IKB, Apollo Operator, Slack, peer assist, or none>

Escalation trigger:
<when to escalate and where>

Follow-ups:
<customer/internal/product follow-ups, only if useful>
```
