# TLDR Mode

Use this for Slack-ready summaries, executive blurbs, and "what are we agreeing to?"
questions. The output should help a manager quickly decide whether to proceed, negotiate, or
pull in Procurement/Legal.

## Required Read

Answer these in order:

1. Current annualized spend or commitment.
1. Proposed annualized spend or commitment.
1. Total contract value and term.
1. Dollar delta and percent delta versus current.
1. Cash due now versus annualized commitment.
1. What Apollo gets for the increase.
1. What remains unverified.

## Wording Pattern

When the user asks for Slack language, default to:

```text
As I understand the proposal, we currently pay <vendor> <current annualized amount> and <current constraint>.

The <term> proposal would commit us to <proposed annual amount> per year, or <TCV> total contract value.

So the annual commit increases by <dollar delta>/yr vs. today, or <percent delta>% more annually. <Cash-flow wrinkle if any>.

IMO, the value add pitch for <project/vendor> is: <customer/business value in one sentence>.
```

## Value Pitch Rules

- Make the value pitch specific to the internal project, not a generic vendor benefit.
- Use customer impact when real, otherwise use operational impact.
- Avoid DORA metrics unless the source material actually ties the work to deployment
  frequency, lead time for changes, MTTR, or change failure rate.
- For Assistant/Hermes-style infrastructure, prefer reliability and workflow continuity:
  "Assistant keeps working through long-running tasks without stuck threads, duplicate runs,
  or lost progress."

## Math Rules

- Annual delta: `proposed annual commitment - current annual commitment`.
- Percent delta: `annual delta / current annual commitment * 100`.
- If credits reduce year-one cash due, state that separately from the annualized commit.
- Do not compare list-price usage to current spend unless the user asks; list-price usage is
  vendor framing, not Apollo's actual payment.
