# Mode A: Khaydien-Style Natural Language Template

Use when the query originates from a client question or call, and the human context (relationship, urgency, account dynamics) matters for how the agent frames the answer.

**Tag format reminder:**

- If pasting into Slack UI: use `@Apollo Agent` (Slack autocomplete will resolve to the mention)
- If sending via MCP API: use `<@U0ABEQ94H7Z>` (the literal mention syntax)
- The skill converts between these automatically based on the action you pick. The template below uses the UI format; the skill swaps it before any API send.

______________________________________________________________________

## Fill-in template

```
@Apollo Agent I'm working with [CUSTOMER_NAME] ([GODMODE_LINK]) and have [N] technical questions [from CLIENT_NAME and ROLE / ahead of our call on DATE / following our call on DATE].

Context: [1-3 sentences. Cover company stage, team size, stack, what they are trying to do, what is currently breaking or unclear. This is where you put the human story so the agent weights its answer correctly.]

1. [Question 1, specific and self-contained. State what you want to know AND what counts as a useful answer (e.g., "Is this natively supported, or does it require a workaround?").]

2. [Question 2, related topic.]

3. [Question 3, related topic.]

[Optional: paste the client's original email below for verbatim context]

Here is [CLIENT_NAME]'s full email for context:
[paste]

Respond with VERIFIED / INFERRED / UNKNOWN confidence labels on each answer. Include KB links where applicable.
```

______________________________________________________________________

## Required fields

- `CUSTOMER_NAME`: the account
- `GODMODE_LINK`: full godmode URL (with `godemail=` param)
- `N`: how many questions (≤5, topically related)
- Opening one-sentence framing: who you are working with, why now
- 1-3 sentence context paragraph
- Numbered questions (1-5)
- Confidence label request

## Optional but recommended

- Client name and role (so the agent knows the seniority of the person whose question it is)
- Call date (so the agent knows the urgency)
- Full client email pasted at the bottom (verbatim or sanitized)
- KB link request

## Anti-patterns

- Do not embed the godmode link inside a sentence; put it in parentheses after the customer name so it is obvious
- Do not exceed 5 questions
- Do not mix unrelated topics (e.g., deliverability + billing + a feature request in the same post)
- Do not ask for out-of-scope items: refunds, ops actions, video/audio transcription, secrets, third-party URL HTTP checks
