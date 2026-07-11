# Live Conversation Assessment Playbook

Use this reference through `live` when the user shares an Intercom conversation link (or ID) and wants a fast read: a short summary, diagnostic next steps, and a ready-to-send draft reply. This workflow is read-only: draft the reply, do not send it, note it, tag, close, or route.

## Step 1: Resolve The Conversation

Intercom conversation URLs look like:

```text
https://app.intercom.com/a/inbox/<workspace_id>/inbox/.../conversation/<CONVERSATION_ID>
```

Extract the numeric `<CONVERSATION_ID>` (the trailing segment). If the link is a short link or only an ID is given and it is ambiguous, ask the user to confirm the conversation ID.

## Step 2: Fetch The Conversation

Use the Intercom MCP `get_conversation` tool with the conversation ID before making any customer-specific claim (per Live Context Rules). Extract:

- Customer name and company/contact info
- All message parts (customer messages and agent replies), most recent first for current state
- Conversation state (open/closed/snoozed) and any tags/attributes

If Intercom returns no data, tell the user the conversation could not be fetched and ask them to check the link or confirm Intercom is connected. Continue from a pasted thread if they provide one.

## Step 3: Ground Product Claims

If the customer's issue is a product, process, how-to, troubleshooting, or Support-policy question, call the Glean Support Rep Assistant (`python3 scripts/ask_glean_support_rep_assistant.py --mode live --question "<question>"`) before asserting product behavior in the next steps or draft. Do not invent account state, limits, permissions, or product behavior: say what still needs checking.

If the Glean CLI is unavailable or the call errors out, do not block: per the skill's Live Context Rules, label the gap, fall back to Glean MCP/search as a regular Glean source (not Support Rep Assistant output), and keep any unverified product claim out of the draft reply — phrase those next steps as questions to confirm rather than assertions.

If the customer's issue involves eligibility, age, legal, compliance, ToS, privacy, or account policy, check `apollo-policies.md` before asserting any policy fact. Link to https://www.apollo.io/terms or https://www.apollo.io/privacy-policy in the draft reply as appropriate.

## Step 4: Build The Output

- **Summary**: 2-3 factual sentences — who the customer is (name/company if known), the problem, and the outcome they want. No filler.
- **Next steps**: 2-3 specific, actionable items in diagnostic order (verify basics → isolate cause → escalate/fix). Write them as things the customer should do or provide, ready to paste or lightly adapt.
- **Draft reply**: ready to send — warm greeting with the first name, one-sentence acknowledgement, the diagnostic asks woven in naturally (not a robotic list), and a close that offers a call if the issue looks complex. Match the conversation's tone and follow the skill's acknowledgement rules: do not apologize for the product or put emotions in the customer's mouth unless they stated them.

## Output Shape

```text
## 🎫 Conversation Summary
<2-3 sentence summary>

## 🔧 Suggested Next Steps
1. **<Action title>** — <what to ask/have the customer do>
2. **<Action title>** — <what to ask/have the customer do>
3. **<Action title>** — <what to ask/have the customer do>

## ✉️ Draft Reply
<ready-to-send reply the agent can copy into Intercom — do not send it automatically>
```

## Edge Cases

- **Already resolved**: note it in the summary; still provide next steps and a follow-up draft in case it reopens.
- **Long thread**: anchor on the most recent customer message for current state, use earlier messages for context.
- **Ambiguous issue**: summarize what is known, make one next step a clarifying question, and have the draft ask it naturally.
- **Agent already replied**: write the draft as a follow-up that acknowledges what was already said, not a first response. Reference the prior reply by content ("as mentioned in the last update…" or "following up on the note about X") rather than by agent name alone — the person sending this draft may not be the same agent who originally replied, so the language should work regardless of who picks it up.
