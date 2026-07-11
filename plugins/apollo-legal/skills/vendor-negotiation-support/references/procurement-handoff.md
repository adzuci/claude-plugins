# Procurement Handoff

Use this when packaging manager work for Procurement, Commercial Legal, Security, Finance, or
the business owner.

## Role Boundaries

- Manager/Codex: gather sources, summarize business value, calculate deltas, propose asks,
  identify missing information.
- Procurement: owns sourcing process, vendor negotiation mechanics, Zip workflow, and
  purchase-process guidance.
- Commercial Legal: owns legal review, redlines, signability, DPA, liability, indemnity, and
  contract language.
- Security/Privacy: owns data/security review, DPA inputs, subprocessors, production data,
  AI training/data-use concerns.
- Finance: owns budget, payment timing, capitalization/accounting treatment, and approval
  thresholds.

## When To Call Out To Contract Review

Use `/apollo-legal:vendor-contract-review` for:

- "Can we sign this?"
- "Redline this."
- "Is this clause okay?"
- "Does this DPA/liability/indemnity/termination language work?"
- "Scan Ironclad for vendor contracts."

In the manager-facing handoff, write:

```text
Legal review needed: run `/apollo-legal:vendor-contract-review` on <document/link> for <specific issues>.
```

## Submitting in Zip for Formal Approval

Zip is Apollo's procurement intake and approval system. This skill preps the deal; Zip is
where it becomes an official request and routes for sign-off. Prep the packet here, then the
business owner submits it in Zip. Do not create or submit the Zip request automatically
unless the user explicitly asks and a Zip connector is available.

**Have this ready before opening the Zip request:**

- Final proposal or order form, and the vendor contact.
- Business justification and the usage/value story.
- Current vs. proposed annual spend, TCV, and cash due on signing.
- Renewal or signature date, and any cancellation-notice deadline.
- Negotiation summary: recommended ask, acceptable fallback, do-not-concede line.
- Security/privacy flags (personal data, subprocessors, AI data use) and any legal items.

**Approval routing by annual value** (verify against the live Procurement FAQ or
`/apollo-procurement:procurement-faq` — figures change):

| Annual value | Zip approval path |
| --- | --- |
| < $10K | Auto-approves to the next step |
| $10K–$50K | Procurement review |
| $50K+ | Procurement + Finance review |
| $100K+ | Executive approval required |

- A formal contract review in **IronClad is triggered for anything over $25K or any
  multi-year agreement** — plan for it on multi-year deals regardless of annual size.
- Zip approvals fan out into **parallel lanes** (Procurement, Finance, Legal, IT, InfoSec,
  and onboarding as applicable). The request advances to signature only once every required
  lane clears, so a single slow lane sets the timeline. Build that lead time into any
  signature date you agree with the vendor.
- For redlines, signability, or DPA/liability/termination language, route the contract to
  `/apollo-legal:vendor-contract-review`. Legal review happens inside the Zip/IronClad flow,
  not as a manager sign-off here.

**Confirm current steps and get help:** search Glean/Drive/Notion (`Zip procurement`,
`Zip renewal`, `procurement intake`, `<vendor> Zip`) or ask in **#zip-help-desk**. If you
cannot verify the current process, say so rather than guessing:

```text
I could not verify the current Zip intake steps from available sources. Confirm the request type and required approvals in Zip or #zip-help-desk before submitting.
```

## Handoff Note

```text
Context: <vendor, product, business owner, renewal/signature date>
Business value: <why Apollo needs it, usage, customer/internal impact>
Commercial read: <current spend, proposed spend, delta, TCV, cash due now>
Recommended ask: <primary negotiation ask>
Acceptable fallback: <fallback>
Do not concede without approval: <walk-away point>
Legal/security review needed: <specific issues or "none identified from manager review">
Missing info: <unknowns>
Sources: <links>
```
