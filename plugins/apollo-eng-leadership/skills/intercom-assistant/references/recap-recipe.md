# Recap Recipe

Use this reference for `recap` or `wrapup` after an Intercom chat, call, Granola meeting, pasted transcript, or notes.

## Source Check (run first, in order)

1. If the user pasted a full transcript or notes directly, use that as the primary source for content — do not re-fetch the same conversation from Intercom or Granola just to confirm what is already in the paste. Still check Intercom for account context (plan, ARR, conversation state) if a conversation ID or URL is present and those details are not in the pasted content.
1. Check `mcp__Granola__get_meeting_transcript` or `mcp__Granola__query_granola_meetings` for a call recording transcript. Use it as the primary source if found.
1. Check `mcp__Intercom__get_conversation` for the conversation context if a conversation ID or URL was provided. Intercom stores call transcripts within the conversation parts — look for call recording parts in addition to chat messages and use any call transcript found as source material.
1. If neither Granola nor Intercom returned usable content and no paste was provided, ask the user for notes or a transcript.

## Rules

- Use only sourced content — transcript, notes, or fetched context.
- Be specific but concise.
- Do not invent details, root cause, account facts, outcomes, or follow-ups.
- Do not update Intercom automatically. Draft the closeout reply or internal note and tell the EM what to apply.

## Required Output

```text
Customer:
<customer and company if known>

Issue:
<what the customer needed>

Actions taken:
<what was done during the interaction — checked, tested, shared, escalated, configured>

Outcome:
<what changed, what was resolved, or current state>

Quick Script:
<1-2 natural sentences to close the call/chat, confirm outcome, and set any next step>
```

## Optional Fields

Include only when actionable or meaningful:

```text
Root cause or best current understanding:
Feedback:
<1-2 sentences from the call recording or transcript on what went well or could improve — only if Granola transcript is available>
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
