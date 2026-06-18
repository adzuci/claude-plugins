# Routing And Intercom Macros

Use this reference in `live`, `monitor`, and `macro-suggest` when the issue class and route are clear.

Source: Customer Care Rotation Wave 2 Notes knowledge-check / escalation section, fetched June 18, 2026. Re-verify exact macro/workflow names in IKB before acting.

## Rules

- Propose macros/workflows only when the route is clear from the provided context or fetched Intercom/account evidence.
- Do not apply macros, notes, workflows, tags, snoozes, closes, or routes.
- When a macro/workflow name is screenshot-only, uncertain, or missing from text, say to confirm the exact name in IKB before acting.
- Apply the correct macro or internal note first for context, then run the workflow to route the conversation.
- Invoice/charge wrong goes to Billing. Product behaving unexpectedly goes to Tech Support instead.

## Text-Backed Routes

| Queue / team | When to use | Macro or internal note | Workflow | Gotchas |
| --- | --- | --- | --- | --- |
| Billing | Invoice or charge is wrong | Internal note `Template: Billing Escalation`; reply macro `Escalate to Billing` | `Escalate to Billing` | Fill all Billing Escalation internal note fields before routing. |
| Billing Renewals | Renewal, refund, or downgrade issues | `Escalate to Billing Renewals` | `Escalate to Billing Renewals` | Renewed less than 10 days ago, or more than 10 days plus refund request, goes to Billing PA. ARR at or above `$25k` means find AM in SFDC/Vitally and do not send to Billing. Custom plan under `$25k` with no CSM/AM gets downgrade macro; escalate only if customer insists. |
| Customer Advocates | Customer needs CA and no technical help is needed | `Escalate to CA - To Confirm` | Live chat: `Escalate to CA - Transfer Chat`; email: `Escalate to CA - Transfer Ticket` | Confirm no technical help is needed before transferring. |
| Blockages | Account or prospecting blocks | `Escalate to Blockages - Inform Customer of Transfer` | `Escalate to Blockages` | Triggers include ToS violation Code X / 1-hour prospecting block, IP/domain block from many signups, fraud activity log, signup errors `61872` / `61873`, or voice number deactivation. |
| External Fraud | Account takeover, unauthorized charges, chargebacks, identity checks | Suspected takeover: `Unauthorized Activity - Suspected Account Takeover`; unrecognized charges: `Unexpected or Unauthorized Transaction(s) - Apollo User`; chargeback suspension: `Dispute: Dispute Withdrawal Request`; identity check: `Dispute: Account Verification` | After customer responds, live chat: `Escalate to External Fraud (Chats)`; email/web: `Escalate to External Fraud (Tickets)` | Two-step flow: send the customer-facing macro first, then workflow after the customer responds. |

## Confirm-In-IKB Routes

| Queue / team | When to use | Guidance |
| --- | --- | --- |
| Account Advocates | Account-advocate cases | Macro/workflow names are image-only in the source section; confirm exact names in IKB. |
| Tech Support / Tech Team | Product behaving unexpectedly | Macro/workflow names are image-only in the source section. Use the handoff script only after confirming it is not billing. Incorrect escalations are tracked with `TC Pilot - Incorrect escalation`. |
| GodMode queue | GodMode-specific routing | Source notes indicate screenshot-only details; confirm exact macro/workflow names in IKB. |

## Other Named Workflows

| Item | Use |
| --- | --- |
| `Live Support Snooze for 24 Hours` | When waiting on engineering. Always use this workflow instead of Intercom's manual snooze. |
| `Call Offer Framing` | To offer the customer a call. This is not a team escalation. |
| `#ama-support-peer-assist` | Escalation of last resort after Glean, IKB, Apollo Agent, and Slack search. |

## Output Shape

```text
Recommended macro/workflow:
<macro/workflow or "not clear yet">

Why this route:
<source-backed reason>

Required confirmation:
<fields, account facts, IKB confirmation, or none>

Customer-facing draft:
<reply if useful>

Internal note draft:
<note if useful>

Do not do automatically:
<send, tag, close, snooze, route, mutate account>
```
