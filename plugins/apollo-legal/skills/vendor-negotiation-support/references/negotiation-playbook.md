# Negotiation Playbook

Use this for pricing, term, usage, and renewal strategy. The goal is a practical negotiation
plan that saves money, preserves flexibility, and gives Procurement clean asks.

## Commercial Levers

Check these before drafting asks:

- Current spend, proposed spend, TCV, payment timing, and unused credits.
- Renewal date, signature deadline, and cancellation notice deadline.
- Current usage versus proposed commit.
- Forecast confidence and whether demand is proven or speculative.
- Whether the vendor is critical, substitutable, or experimental.
- Switching cost, implementation cost, and internal migration timeline.
- Benchmark or competitive alternative if available.
- Apollo data signals from `apollo companies search` or `apollo companies get` when vendor
  scale would calibrate tone or concession size. Use `apollo-data-negotiation.md`.

## Standard Options

Present 2-4 options:

| Option | When to use | Ask | Fallback |
| --- | --- | --- | --- |
| Hold price | Vendor wants expansion but current value is unclear | Keep annual commit flat while adding needed scope | Use remaining credits or short bridge term |
| Commit with guardrails | Vendor is critical and growth is plausible | Multi-year at locked rate with annual opt-out, rollover, and capped overages | Two-year term or year-one opt-out |
| Lower commit | Usage forecast is uncertain | Commit to measured baseline plus modest headroom | Quarterly true-up or usage rollover |
| Deadline extension | Discount pressure is artificial or review is incomplete | Extend signature deadline through Procurement/Legal review | Business approval now, signature after paper matches terms |
| Side-by-side options | Internal owner has not chosen risk appetite | Ask vendor for 1-year, 2-year, and 3-year options | Use 2-year as compromise |

## Red Flags

- Proposed commit is built from vendor-modeled usage rather than measured usage.
- Overage discount appears in email but not in the order form.
- Vendor says a concession is "not go-forward policy" without writing it into the term.
- Signature deadline is framed as non-negotiable before Procurement/Legal review.
- Auto-renewal, price uplift, or notice window is not visible.
- Product/security/legal dependency is being used to rush commercial approval.

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

## Procurement-Friendly Handoff

End negotiation analysis with:

- "Recommended ask"
- "Acceptable fallback"
- "Do not concede without owner approval"
- "Legal/security items for `/apollo-legal:vendor-contract-review`"
