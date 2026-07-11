# Billing Triage

Use this reference in `live` when a customer raises billing, charges, credits, refunds, cancellation, or invoices. Billing is the largest share of escalated volume. It is read-only: suggest a route and what to verify; do not decide outcomes or mutate anything.

Post-Fin context: Fin already handled the simple self-serve billing answers, so a human on a billing thread usually needs account state inspected or a decision made. Lead with what to verify and where to route, not with an article to paste.

## Triage Versus Policy

Triage means classify the issue, identify the correct route or macro, and state what to verify. Policy means the actual decision: whether a refund or credit is granted, the dollar amount, the eligibility window, and who has the authority. **This file never states an outcome.** Any number, eligibility window, or "yes you qualify" lives in `apollo-policies.md` and is decided by Billing. A decision node here outputs a route plus a macro, not an answer.

## Decision Tree

Check the fraud fork first, before treating anything as a refund:

1. **Unauthorized, unrecognized charge, or chargeback** -> route to External Fraud (see `routing-and-macros.md`). Never triage a disputed charge as a routine refund.
1. **Failed or declined payment, dunning, past-due account** -> verify the card on file in Settings; if the customer is blocked, route to Billing.
1. **Credit question or refund request** -> fetch the live Notion credits policy (see Credits and Refunds section below) before quoting any threshold or suggesting an amount. Identify the credit type (email, export, mobile, unified), confirm the account's credit model in GodMode, check if all three eligibility conditions are met, then state the route and suggested starting percentage. Do not state a final yes/no -- that is the rep's call after verifying live policy.
1. **Cancellation** -> if the account has an AM or CSM, route to that owner before processing; cancellation is a revenue event. Note that cancel does not equal an immediate refund.
1. **Seat or plan change mid-cycle, proration, invoice, tax, or VAT detail** -> resolve via self-serve where possible, otherwise route to the AE.

Cross-link the Billing and Billing Renewals rows in `routing-and-macros.md` for the exact macros, workflows, and internal-note templates. Confirm exact names in IKB before acting.

## Credits and Refunds

**Before suggesting any credit or refund amount, always fetch the live policy first:**

```python
mcp__claude_ai_Notion__notion-fetch(id="https://app.notion.com/p/apolloio/Temporary-Credits-Exception-Guidelines-for-Product-Advocates-and-Tech-23fab2b3b49680ae9a64d9595feac2bf")
```

Use the fetched content as the authoritative thresholds. If the Notion fetch fails, state that you cannot verify current credit policy and advise the rep to check the page directly before quoting any amount.

### Baseline (illustrative only; always superseded by the live Notion fetch above)

> **Do not quote these numbers if the Notion fetch failed.** Tell the rep to check the page directly. The table below reflects a past snapshot and may be stale.

**Three conditions that must all be met for a PA to offer credits without escalation:**

1. Requested amount is 2,000 credits or fewer
1. Customer is reporting a legitimate platform or product issue (prospecting, sequences, integrations, enrichment, mailbox linking) -- not user error or misconfiguration
1. Customer explicitly requested compensation -- never offer proactively unless there is a bad press risk or legal thread

**Rep self-approval limits (per credit type):**

| Credit type | Rep max | PA/Tech Lead max |
| --- | --- | --- |
| Email | 2,000 | 5,000 |
| Export | 2,000 | 5,000 |
| Mobile | 200 | 1,000 |
| Unified | 2,000 | 10,000 |

Requests above PA/Tech Lead limits must go to Billing Leadership (Jocel or Santi).

**Gradual escalation -- do not offer the max upfront:**

- Start at 25% of the prorated amount (excluding add-ons)
- Increase to 40% if the customer pushes back
- Maximum without lead approval: 55%

**Expiration:** Credits cannot be set beyond the current billing cycle end date. If fewer than 10 days remain in the cycle, offer the customer the choice of current cycle or next cycle. Next-cycle requests must be escalated to Billing Advocates.

**Edge cases:** AI Research Fields (Qualify Contacts / Qualify Accounts) have a separate handling path -- the Notion page Edge Cases section is the source of truth.

**Positioning:** Frame credits as a goodwill gesture tied to the specific product issue, not as a retention incentive or apology. Example: "Since this was a confirmed platform issue, I've applied credits to offset the impact."

IKB reference: https://apolloikb.zendesk.com/hc/en-us/articles/37632611319181-Review-grant-credits-for-customer-inconvenience

## Guardrail

Read-only. Suggest the route, the macro to apply, and what to verify. Do not apply macros, run workflows, or state refund/credit decisions. For credits and refunds, always fetch the Notion policy page before quoting a threshold.
