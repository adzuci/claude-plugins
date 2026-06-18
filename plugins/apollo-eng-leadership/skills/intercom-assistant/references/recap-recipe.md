# Recap Recipe

Use this reference for `recap` or `wrapup` after an Intercom chat, call, Granola meeting, pasted transcript, or notes.

## Rules

- Use only the transcript, notes, or fetched conversation context.
- Be specific but concise.
- Do not invent details, root cause, account facts, outcomes, or follow-ups.
- Always include the required fields.
- Include optional fields only when they have useful content. Do not include optional fields just to say `No`, `None`, `N/A`, or `Unknown`.
- Do not update Intercom automatically at wrap-up. Draft the customer closeout reply or internal note and tell the EM what to apply.

## Required Output

```text
Quick Script:
<1-2 natural sentences to close the call/chat, mention what changed, confirm outcome, and set any next step. If not asked already, ask if they need anything else.>

Customer:
<customer and company if known>

Issue:
<what the customer needed>

Outcome:
<what changed, what was resolved, or current state>
```

## Optional Fields

Include only when actionable or meaningful:

```text
Root cause or best current understanding:
Actions taken:
Customer-facing follow-up needed:
Internal follow-up needed:
Escalation needed:
Loom needed:
Product signal / friction observed:
Intercom note draft:
```

## Intercom Note Draft

When useful, write a concise internal note for the next Product Advocate:

```text
Intercom note draft:
Customer was <issue>. Checked <evidence/actions>. Result: <outcome>. Next step: <owner/follow-up>.
```

## Conversation Closeout

When the call or chat appears complete, draft the closeout language and say whether the `<name> Closeout` macro is appropriate. Do not send it automatically.

```text
Closeout recommendation:
<send `<name> Closeout`, send a custom closeout, or do not close yet>

Draft:
I'll go ahead and close this out, but feel free to reply here if anything else comes up.
```
