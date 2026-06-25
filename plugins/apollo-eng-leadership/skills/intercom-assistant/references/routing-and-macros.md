# Routing And Intercom Macros

Use this reference in `live`, `monitor`, and `macro-suggest` when the issue class and route are clear.

Source: Customer Care Rotation Wave 2 Notes knowledge-check / escalation section, fetched June 18, 2026. Re-verify exact macro/workflow names in IKB before acting.

## Rules

- Propose macros/workflows only when the route is clear from the provided context or fetched Intercom/account evidence.
- Do not apply macros, notes, workflows, tags, snoozes, closes, or routes.
- When a macro/workflow name is screenshot-only, uncertain, or missing from text, say to confirm the exact name in IKB before acting.
- Sequencing with a confirm-gate: (1) classify the issue and confirm the route is correct, (2) suggest the private internal note, (3) suggest the customer-facing macro, (4) suggest the workflow. The macro is customer-visible, so confirm the route before it fires or the customer is told the wrong destination. Order: note (private), then macro (customer-visible), then workflow (routing).
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

## Escalation Routes

Additional routes from the IKB Intercom Escalation Process, on top of the text-backed routes above. Some teams expose a macro and a workflow with the same name; confirm in Intercom/IKB which object is which, and do not assume they are identical. Macros insert reply text or internal notes; workflows route and assign. The IKB article is the source of truth for exact names.

| Queue / team | When to use | Reply macro | Workflow | Internal note |
| --- | --- | --- | --- | --- |
| PA (chat or ticket) | Needs a Product Advocate; no other team fits | Confirm in IKB | Confirm in IKB | Short context note |
| Internal Billing | Internal billing investigation, not a customer refund decision | Confirm in IKB | Confirm in IKB | `Template: Internal Billing Escalation` |
| Manager | Abuse, legal threat, public-callout threat, or repeated failed escalation | Confirm in IKB | Confirm in IKB | `Escalate to Manager` |
| Technical Support (ticket or chat) | Product behaving unexpectedly, not billing | Confirm in IKB | Confirm in IKB | `Template: Technical Escalation` |
| Fraud Review | Identity or dispute review follow-up | Confirm in IKB | Confirm in IKB | Short context note |
| Incorrect escalation (transfer back) | A conversation was routed to the wrong team | Confirm in IKB | Confirm in IKB | `Billing: Incorrect Escalation note` or `TC Pilot - Incorrect escalation` |

Internal-note templates referenced above and in the text-backed routes: `Template: Billing Escalation`, `Template: Internal Billing Escalation`, `Escalate to Manager`, `Template: Technical Escalation`, `Billing: Incorrect Escalation note`.

Tech handoff sample (suggest, do not send):

```text
I'm going to connect you with our Tech Team, who can take a closer look at this for you. Thanks for your patience while I get this handed off.
```

For an incorrect escalation, do not re-apologize or re-route blindly. Confirm the correct destination first, leave the incorrect-escalation note, then transfer back.

## Other Named Workflows

| Item | Use |
| --- | --- |
| `Live Support Snooze for 24 Hours` | When waiting on engineering. Always use this workflow instead of Intercom's manual snooze. |
| `Call Offer Framing` | To offer the customer a call. This is not a team escalation. |
| `#ama-technical-support` | Technical/product escalation when Support needs account-specific investigation, logs, Apollo Agent help, feature behavior confirmation, or engineering context that cannot be verified from Intercom, GodMode, Glean, or IKB alone. Draft the post; do not send automatically. |
| `#ama-support-peer-assist` | Support-process or peer-calibration escalation of last resort after Glean, IKB, Apollo Agent, and Slack search. Draft the post; do not send automatically. |

## Adam's Personal Macros

Use these in `macro-suggest` when the route is a personal close or intro, not a team escalation.

| Macro | When to suggest |
| --- | --- |
| `Adam Intro + Call` | Default first reply — customer has a clear question |
| `Adam Intro + Review Stall + Call` | First reply when account review is needed before answering |
| `Adam Intro + Not Working + Call` | First reply when the customer reports something broken or not working |
| `Adam You're Welcome` | Customer has confirmed satisfied and the conversation is ready to close |
| `Adam Close Out` | Closing a no-reply or auto-resolve conversation |

Survey nudge: `Adam You're Welcome` includes a soft personal nudge before close. The bot fires CSAT automatically after that. Do not suggest adding a second explicit survey ask in the same message — one personal nudge is warm; two back-to-back feels pushy.

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
<send, tag, close, snooze, run workflow, route, mutate account>
```
