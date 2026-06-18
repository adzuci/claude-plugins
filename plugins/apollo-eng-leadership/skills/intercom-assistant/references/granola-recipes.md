# Granola Recipes

Use this reference from `setup` when the EM uses Granola. If not using Granola, keep these prompts available and paste notes/transcripts directly into the skill.

## `/Wrap-up`

```text
Help me as a Product Advocate wrap up a support interaction.

Use only the transcript/notes. Be specific but concise. Do not invent details.

Always include:
- Quick Script
- Customer
- Issue
- Outcome

Include optional fields only if actionable or meaningful:
- Root cause or best current understanding
- Actions taken
- Customer-facing follow-up needed
- Internal follow-up needed
- Escalation needed
- Loom needed
- Product signal / friction observed
- Intercom note draft
```

## `/Stall`

```text
# /Stall

Use this when a support-rotation conversation, shadowing session, or customer issue feels stuck, unclear, or blocked.

Produce a concise stall note with these sections:

## Situation
- Customer / account:
- Support channel or source:
- What they are trying to do:
- What is currently stuck:

## Evidence So Far
List only facts observed in the conversation, tools, logs, KB/SOP, or teammate guidance. Do not infer beyond the evidence.

## Stall Reason
Choose one:
- Missing customer context
- Missing internal tool access
- Ambiguous product behavior
- Needs KB/SOP confirmation
- Needs engineering input
- Needs Support / PA escalation
- Waiting on customer
- Other

Then explain the reason in 1-2 sentences.

## Next Best Move
Give the single most useful next action, with owner and target channel/tool.

Format:
- Owner:
- Action:
- Where:
- Why now:

## Draft Customer Reply
Write a short, calm reply that:
- Acknowledges the issue
- Avoids overpromising
- States what we are checking or doing next
- Gives a clear next step or expectation

## Internal Note
Write a compact internal handoff note for Support / PA / Engineering with:
- Customer impact
- Evidence
- Blocker
- Ask
- Suggested priority

## Rotation Learning
Capture 1-2 takeaways I should remember for future support shifts, especially tool paths, escalation rules, access friction, or product gaps.
```

## `/Deescalate`

```text
# /Deescalate

Help me respond to a frustrated or stuck customer during a support interaction.

Use only the transcript/notes. Be specific, calm, and concise. Do not invent details. Do not over-apologize. Do not assign fault unless it is clearly established.

Output:

Customer reply:
Write a warm support response using this pattern:
1. Name the specific situation, not generic frustration
2. Own the next step
3. Say what you will check or do
4. Offer a call early if it would help
5. Give only one clear next step

What not to say:
List any wording I should avoid, such as blaming another team, promising a fix, or projecting emotions the customer did not state.

If they push back:
Write one short follow-up that keeps the conversation moving.

Internal note:
Summarize the customer's concern, what was acknowledged, and the next step.
```
