# Recap Recipe

Use this reference for `recap` or `wrapup` after an Intercom chat, call, Granola meeting, pasted transcript, or notes.

## Source Check (run first, in order)

1. If the user pasted a full transcript or notes directly, use that as the primary source for content — do not re-fetch the same conversation from Intercom or Granola just to confirm what is already in the paste. Still check Intercom for account context (plan, ARR, conversation state) if a conversation ID or URL is present and those details are not in the pasted content.

1. Check `mcp__Granola__get_meeting_transcript` or `mcp__Granola__query_granola_meetings` for a call recording transcript. Use it as the primary source if found.

1. Check `mcp__Intercom__get_conversation` for the conversation context if a conversation ID or URL was provided. Scan `conversation_parts` for a part with `part_type: "call_summary"` — this is an AI-generated bullet summary of the call, not the verbatim transcript. Use it as source material if found, and note it is an AI summary. The full verbatim transcript is not returned by the API; if a `call_summary` part is present, surface a direct download link to the user so they can retrieve the full transcript themselves:

   ```
   Full transcript: https://app.intercom.com/a/inbox/dyws6i9m/inbox/conversation/{CONVERSATION_ID}?view=List#:~:text=Download-,Transcript,-Delete%20Recording%20and
   ```

   Replace `{CONVERSATION_ID}` with the numeric ID from the conversation.

1. If neither Granola nor Intercom returned usable content and no paste was provided, ask the user for notes or a transcript.

## Open Conversation Check

Before generating a recap, check whether the interaction is actually over:

- If the conversation is **open and waiting** (no resolution, no `call_summary`, no closeout message) — do not generate a recap. Instead, identify the current state and suggest the right mode:
  - No first reply sent yet → suggest `intro`
  - Active chat in progress → suggest `live` or `monitor`
  - Customer waiting on a reply → suggest `live` with a draft reply
- If the conversation is **closed or has a `call_summary` part** → proceed with the recap.

State your reasoning in one line before the recap output (e.g., "Conversation is closed with a call summary — generating recap.").

## Rules

- Use only sourced content — transcript, notes, or fetched context.
- Be specific but concise.
- Do not invent details, root cause, account facts, outcomes, or follow-ups.
- Do not update Intercom automatically. Draft the closeout reply or internal note and tell the EM what to apply.
- The recap and Intercom note draft are for the PA's internal record. Only generate customer-facing summary copy if the user signals the customer explicitly asked for one — the default closeout script is not a summary.

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
