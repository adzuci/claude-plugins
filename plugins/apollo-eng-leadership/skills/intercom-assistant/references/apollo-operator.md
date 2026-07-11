# Apollo Operator via Slack MCP

Use Apollo Operator when an Intercom investigation still needs product behavior, account-specific diagnosis, logs, or a supported customer-facing explanation that Intercom, GodMode, Glean, and IKB cannot establish.

## Route

| Caller | Channel | Channel ID |
| --- | --- | --- |
| Verified rotation EM in `em-rotation-roster.md` | [`#ama-technical-support`](https://apolloio.slack.com/archives/C01JF1PP74N) | `C01JF1PP74N` |
| Product Advocate or Customer Advocate | [`#ama-pa-apollo-operator`](https://apolloio.slack.com/archives/C0ALMDYQ5PT) | `C0ALMDYQ5PT` |

For a caller with an unknown role, ask one concise role question before offering a Slack route. Apollo Operator research does not replace a customer-facing Intercom technical handoff when one is needed.

## Workflow

1. Confirm the exact unanswered question and collect the verified Intercom, account, Glean, and IKB evidence first.
2. For an EM-channel question, resolve the caller through the authenticated host profile or a Slack MCP user-profile lookup and apply `em-rotation-roster.md` **Use In Escalations**. If that evidence is unavailable, give the reviewed manual-channel draft and direct link instead of sending through Slack MCP.
3. Use the Slack MCP read-channel tool on the selected channel to confirm the connector can access it. If it is unavailable, give the reviewed message and the direct channel link instead.
4. Draft a concise message that mentions Apollo Operator as `<@U0ABEQ94H7Z>`.
5. Show the draft and state the target channel. Do not send it until the caller explicitly confirms.
6. Keep one Apollo Operator thread per Intercom conversation. Before a new post, search the target channel for the verified conversation ID. If a matching thread exists, use it; otherwise create one new channel message and record its timestamp in the private notes as `Apollo Operator thread`.
7. After explicit confirmation, use the available Slack MCP send-message tool with the channel ID above. For the same conversation, post follow-up questions only as replies in that one thread. Do not create a second root message.
8. Read the resulting thread before turning the response into customer-facing guidance. Verify it against IKB or account evidence, then rewrite it in the caller's own words. Never paste Apollo Operator output verbatim to a customer.

## During Live Calls

When a Product Advocate or Customer Advocate is on a live call and Apollo Operator is needed, use `#ama-pa-apollo-operator` to propose a short, reviewed draft. Include only the customer goal, observed symptom, verified team or conversation ID, and exact question. After explicit confirmation, post it through Slack MCP and monitor the same thread for the answer. Bring the verified answer back into the live guidance as concise internal notes and customer-safe wording.

## Draft Template

```text
<@U0ABEQ94H7Z> Investigate this team: <team ID or "not verified yet">. <Customer goal and symptom without identifying details>. Checked: <Intercom, GodMode, Glean, IKB, and other evidence>. Need help with: <specific question>. Evidence: <conversation or team ID, timestamp, sanitized error text, or unknown>. Urgency: <business impact or "normal">.
```

Team and conversation IDs are expected investigation identifiers and may remain in the reviewed draft. Redact customer-facing identifiers by default.

## Guardrails

- Do not ask Apollo Operator for information already answered by Intercom, GodMode, Glean, or IKB.
- Redact customer names, email addresses, phone numbers, full Intercom URLs, and full account URLs by default. Include an identifier or link only when it is necessary for the investigation and the caller explicitly keeps it in the reviewed draft.
- Do not send messages without explicit caller confirmation, even when the Slack MCP tool is available.
- Never create more than one Apollo Operator root thread for the same Intercom conversation. Use replies in that thread for follow-ups.
- If Slack MCP is unavailable or cannot read the target channel, provide the reviewed, paste-ready message and its direct channel link instead.
