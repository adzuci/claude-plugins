# Apollo Data Negotiation

Use Apollo data to calibrate tone, leverage, and ask size when negotiating with a vendor.

## Data To Gather

- Vendor domain and matched organization ID.
- Revenue, headcount, funding, industry, company size, and growth signals.
- Confidence level from the source record: exact, estimated, stale, or unknown.

Use `references/apollo-cli.md` for lookup commands. Do not run credit-consuming enrichment
without user approval.

## How To Use It

- Treat revenue, headcount, funding, and company size as directional context, not audited
  facts.
- Compare Apollo's requested concession against vendor scale. Example: a `$25K` concession is
  different for a small startup than for a large, well-funded vendor.
- Show the vendor's upside, not just Apollo's discount ask:
  - `vendor proposal net ARR = proposed annual commit - current annual commit`
  - `counter net ARR = counter annual commit - current annual commit`
  - `concession ask = proposed annual commit - counter annual commit`
  - `TCV retained = counter annual commit * term years`
- Use vendor scale to choose tone: hardline for replaceable or high-scale vendors, conditional
  fast close when timing is valuable, relationship-preserving counter when the vendor is
  strategic or support quality matters.
- Combine Apollo data with deal facts: current spend, proposed commit, TCV, unused credits,
  usage trend, renewal deadline, and switching cost.

## Claim Rules

- Do not overclaim unverified data. Say "Apollo data suggests" or "directionally" when fields
  are estimated.
- Cite source and confidence: `Apollo company search, <date>, confidence: directional`.
- If Apollo data conflicts with contract materials or vendor-provided evidence, state the
  conflict and prefer primary contract/proposal sources for commercial math.
- Never imply Apollo has audited the vendor's finances.

## Output Pattern

Use one short line when the user needs a leader-ready reasonableness check:

```text
<Vendor>'s <commercial model> proposal takes Apollo from <current ARR> ARR to <proposed ARR> ARR (<proposal net ARR> net ARR) and locks a <term>, <proposal TCV> renewal; our <counter ARR> ARR counter still gives them <counter net ARR> net ARR and the same <term/model> lock-in, while asking a <vendor scale signal> vendor for only <concession>/yr less than their proposal.
```

For usage-based billing, only challenge the part that is actually too high:

```text
We are aligned on UBB and the term; the piece to sharpen is annual commit.
```
