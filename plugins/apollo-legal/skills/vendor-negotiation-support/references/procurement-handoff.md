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

## Zip / Procurement Process Lookup

Before describing a Zip or procurement process, use Glean/Drive/Notion search with targeted
queries:

- `Zip procurement`
- `Zip renewal`
- `procurement intake`
- `vendor renewal process`
- `<vendor> Zip`

Only describe process steps that sources return. If no process source is found, say:

```text
I could not verify the current Zip/procurement process from available sources. Procurement should confirm intake steps and required approvals.
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
