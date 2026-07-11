# Negotiation Playbook

The procurement lens Apollo applies to vendor deals, written so any team owner can run a
competent negotiation without routing every step through Procurement. Use it for pricing,
term, usage, and renewal strategy.

## Core Principle

A vendor negotiation is about total value across the full contract lifecycle, not the
headline price on the first quote. Price is one lever among many. A fair rate **plus** terms
that protect Apollo at renewal, at scale, and if the vendor underdelivers beats a great price
with a bad auto-renewal or no liability cap.

## The Procurement Lens

Six shifts to internalize before engaging a vendor:

- **Every quote is a first offer.** Vendors price to their ask, not their floor. Treat the
  opening number as the ceiling, not the anchor.
- **Leverage is built, not found.** Assemble it before you negotiate: the incumbent contract,
  comparable pricing, usage data, a credible alternative.
- **The contract is the deliverable.** Price gets the attention, but terms are what you live
  with for the whole term.
- **Benchmark before you counter.** A number without a comparison is just an opinion. Anchor
  every counter to something concrete.
- **Multi-year and commitment are currency.** Spend them deliberately for price protection,
  not by default (see `multiyear-strategy.md`).
- **Document the baseline and the outcome.** If you did not record the "before," you cannot
  claim the savings.

## Negotiation Lifecycle

Map every deal to Apollo's tooling so the process is repeatable and auditable:

| Stage | What happens | Apollo system |
| --- | --- | --- |
| Intake / request | Scope, budget, and business owner captured | Zip |
| Discovery & benchmark | Pull incumbent contract, comparable agreements, usage/spend | IronClad, NetSuite, Notion |
| Strategy & term sheet | Define target price, walk-away, and must-have terms | Notion / term sheet |
| Counter & redline | Exchange proposals and legal redlines | IronClad |
| Approval | Route to approvers by cost center and threshold | Zip |
| Signature | The correct entity's authorized signatory executes | IronClad |
| Record | Log baseline vs. final, key terms, and renewal date | Notion |

Open renewals early — the most common way to lose a negotiation is to start it a week before
an auto-renewal, with no time to benchmark or walk. See `procurement-handoff.md` for Zip
submission and approval routing.

## Before You Counter

Gather the deal facts:

- Current spend, proposed spend, TCV, payment timing, and unused credits.
- Renewal date, signature deadline, and cancellation notice deadline.
- Current usage versus proposed commit; forecast confidence and whether demand is proven.
- Whether the vendor is critical, substitutable, or experimental; switching and migration
  cost.
- Apollo data signals when vendor scale would calibrate tone or concession size (use
  `apollo-data-negotiation.md`).

Assemble the leverage:

- Incumbent contract pulled and read: price, term, auto-renewal, notice window, caps.
- At least one benchmark in hand: a peer price, public list, or comparable internal
  agreement.
- Target price, walk-away price, and must-have terms written down.
- The business owner's real requirements separated from nice-to-haves.
- Renewal and notice deadlines on the calendar; approval path and the correct entity's
  signatory identified in Zip.

## Building Leverage

The plays that move price and terms:

| Play | When it applies | How to use it |
| --- | --- | --- |
| Reference / first-logo | You are an early or marquee customer | Trade your logo, a case study, or a reference call for pricing and protective terms — get the concession in writing before agreeing to any publicity |
| Competitive benchmark | A comparable agreement or peer price exists | Anchor the counter to it and make the vendor explain the delta |
| Credible alternative (BATNA) | A real substitute exists | Name it, price it, be willing to walk — the threat only works if it is real |
| Timing | Early renewal or a hard deadline | Open renewals early; track notice windows so auto-renewal never negotiates for you |
| Commitment & volume | You can commit spend or term | Trade multi-year or committed spend for a lower rate and a renewal cap (see `multiyear-strategy.md`) |
| Vendor underperformance | SLA misses, outages, disputed or unpaid invoices | Document the failures and use material breach as leverage — route these through Procurement/Legal, do not freelance |

## Standard Options

Present 2-4 options:

| Option | When to use | Ask | Fallback |
| --- | --- | --- | --- |
| Hold price | Vendor wants expansion but current value is unclear | Keep annual commit flat while adding needed scope | Use remaining credits or short bridge term |
| Commit with guardrails | Vendor is critical and growth is plausible | Multi-year at locked rate with annual opt-out, rollover, and capped overages | Two-year term or year-one opt-out |
| Lower commit | Usage forecast is uncertain | Commit to measured baseline plus modest headroom | Quarterly true-up or usage rollover |
| Deadline extension | Discount pressure is artificial or review is incomplete | Extend signature deadline through Procurement/Legal review | Business approval now, signature after paper matches terms |
| Side-by-side options | Internal owner has not chosen risk appetite | Ask vendor for 1-year, 2-year, and 3-year options | Use 2-year as compromise |
| Multi-year term | Need is proven, switching cost is real, and the discount is worth the lock | Trade the longer term for a deeper discount and a price hold; keep an opt-out or rollover | 1-year at same unit rate; or 2-year with termination for convenience after Year 1 |

## Pricing Structures

Know the common structures and when to push for each:

| Structure | What it is | Push for it when | Watch-outs |
| --- | --- | --- | --- |
| Per-unit | Price per discrete unit consumed | Volume is predictable and you want cost to track usage | Define the unit precisely; lock the top-up rate now |
| PEPM | Per employee per month | Headcount-linked tools (HR, EOR, per-seat) | Define who counts as billable; cap growth |
| Prepaid + top-up | Buy a block up front, refill as needed | You want a volume discount and can forecast a floor | Negotiate the top-up rate now, not later; watch expiry and breakage |
| Committed vs. usage | Fixed commitment vs. pay-as-you-go | Committed for discount and predictability; usage for volatile demand | Model both; committed only wins if you will actually use it |
| Tiered | Price steps by tier or edition | You can right-size the tier | Do not buy up a tier for one feature; negotiate the step, not just the tier |

## Countering a Price Increase

When a vendor opens with a large increase, work it in order:

1. **Make them itemize.** Break the increase into drivers: inflation, tier change, usage
   growth, list-price reset. A large headline number rarely survives itemization.
1. **Benchmark each driver** against your prior rate, comparable tools, and public pricing.
1. **Separate usage growth from rate change.** Pay for what you actually consumed more of;
   reject the rate reset on the rest.
1. **Offer something for the cap.** Trade multi-year or a commitment for a capped increase now
   and a renewal cap going forward.
1. **Anchor low and hold the walk-away.** Counter well under the ask and be specific about
   what happens if you do not align.

## Protective Terms

Price is negotiable in an afternoon; a bad term binds Apollo for the whole contract. This
skill does not redline — spot these, flag them, and route the contract to
`/apollo-legal:vendor-contract-review` for the actual redline.

| Term | Why it matters | Standard Apollo position |
| --- | --- | --- |
| Liability cap | Limits Apollo's financial exposure | Cap at fees paid, often trailing 12 months; carve-outs negotiated deliberately |
| Indemnification | Determines who covers third-party (IP, data) claims | Vendor indemnifies for IP and data claims |
| Termination for convenience | Lets Apollo exit without cause | Notice-based exit where possible |
| Auto-renewal & notice window | Prevents silent lock-in | Know the window, set a reminder, prefer opt-in renewal (see `multiyear-strategy.md`) |
| Price protection | Caps renewal increases | Cap the renewal uplift (fixed % or CPI) for the term and first renewal |
| MFN / most-favored terms | Protects against worse-than-peers pricing | Request where you have leverage |
| SLAs & service credits | Makes performance enforceable | Credits for downtime; remedies for chronic misses |
| Data protection / DPA | Compliance and security | DPA attached; data handling defined |
| Assignment | Controls change of control | Consent or notice on assignment |

Aim to win both the price and the terms, not one at the expense of the other. Assume
sophisticated counterparties and hold your lines. The fastest way to spot a term that has
quietly gotten worse is to compare the new agreement clause by clause against a comparable
existing contract.

## Multi-Entity & International Deals

Apollo contracts across multiple legal entities and billing currencies. Get these right or
the deal stalls at signature:

- **Signatory authority.** The correct entity's authorized signer must execute — confirm the
  signer in Zip before you are at handshake.
- **Tax.** Quote and book amounts inclusive of local tax.
- **Currency.** Confirm the billing currency and who bears FX risk.
- **Co-terming.** Align related agreements to a single renewal date so you negotiate them as
  one.
- **EOR and contractor structures.** Entity of record and PEPM definitions drive cost on
  headcount-based deals.

## Red Flags

- Proposed commit is built from vendor-modeled usage rather than measured usage.
- Overage discount appears in email but not in the order form.
- Vendor says a concession is "not go-forward policy" without writing it into the term.
- Signature deadline is framed as non-negotiable before Procurement/Legal review.
- Auto-renewal, price uplift, or notice window is not visible, or the notice window has
  already passed.
- Product/security/legal dependency is being used to rush commercial approval.
- Vendor proposes ramp-up with Year 2–3 minimums exceeding Year 1 actual usage, or
  use-or-lose credits with no rollover right.
- Uncapped liability, or a vendor refusing to indemnify for IP or data claims.
- Pricing that undercuts a term in a comparable Apollo agreement (MFN risk).
- A signature request routed to the wrong entity or an unauthorized signer.
- Any material-breach, disputed-invoice, or unpaid-invoice situation — route it, do not
  freelance.

For the standard Apollo positions on the terms flagged here (liability cap, indemnification,
auto-renewal, price protection), see the Protective Terms table above rather than restating
them.

For discount tactics, term-length judgment, ramp-up counters, use-or-lose handling, and
renew-vs-reopen triggers, read `references/multiyear-strategy.md`.

## Vendor-Facing Draft

```text
Thanks, this is directionally workable. To get this approved internally, we need the paper to reflect the commercial guardrails clearly:

1. <ask tied to annual commit / term>
2. <ask tied to usage, overages, or credits>
3. <ask tied to renewal, opt-out, or review deadline>

If any of these are hard blockers, send the closest fallback language and we can react quickly.
```

For full vendor email responses, use `email-strategies.md` and include an ask math /
reasonableness check below the draft.

## Term Sheet Skeleton

Capture a deal before it goes to redline:

- **Parties & entities** — correct legal entity plus authorized signatory.
- **Scope** — SKUs, tier, seats.
- **Pricing** — structure, unit, rate, top-up rate.
- **Term & start date.**
- **Renewal terms** — auto vs. opt-in, notice window, renewal price cap.
- **Commitment / minimums.**
- **Liability cap & indemnification.**
- **SLAs & service credits.**
- **Data / DPA.**
- **Termination rights.**
- **Payment terms.**

## Document the Outcome

The Notion procurement database is Apollo's institutional memory for vendor deals. Keep it fed
so the next negotiation has a benchmark:

- Log every negotiation: baseline, final, savings, key terms, renewal date, and owner.
- Record the savings math (baseline vs. final) at close. Unrecorded savings do not exist.

## Procurement-Friendly Handoff

End negotiation analysis with:

- "Recommended ask"
- "Acceptable fallback"
- "Do not concede without owner approval"
- "Legal/security items for `/apollo-legal:vendor-contract-review`"
