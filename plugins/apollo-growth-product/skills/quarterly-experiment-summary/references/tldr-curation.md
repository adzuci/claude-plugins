# TL;DR curation

The TL;DR at the top of the doc is the part most readers will actually finish. It's a list of patterns that have held across multiple tests, not a list of recent results. Treating it as a changelog is the fastest way to make it useless.

Current heading in the doc:

```
## TL;DR — patterns that have held across multiple tests
```

Entry format, numbered:

```
N. **<The claim, one bold sentence.>** <Why it's true and where the evidence comes from, with experiment names or IDs in parens.> **<High|Medium|Low> confidence.**
```

Worked example from the doc:

```
3. **Adding "more" to a feature gate usually loses.** Social proof bars, Free vs. Pro comparisons, plan recommendations, and extra Talk-to-Sales CTAs have all rolled back or gone negative. Simpler gates win. **High confidence** (5+ tests).
```

The bolded lead is doing the real work. A reader skimming only the bold text should come away with the team's operating beliefs.

______________________________________________________________________

## How a slot is earned

A new experiment does not earn a TL;DR slot just for concluding. Two ways in:

1. **A pattern held across two or more independent tests.** Independent means different surfaces, audiences, or mechanisms — a rerun of the same test is one data point, not two.
1. **A single result is high-confidence, high-impact, and changes how the team operates.** The Interactive Trial Indicator earned a slot on its own because $1.83M and a replicable mechanism changes what the team builds next.

Everything else belongs in its quarter entry and nowhere else.

## Prefer strengthening over adding

Most new results are the fourth or fifth data point on a pattern already in the list. That's a *good* outcome and the right move is to fold the evidence into the existing entry, not to add a neighbour that says almost the same thing.

Signs you should be merging rather than adding:

- The new claim's bold sentence could be swapped with an existing one without a reader noticing.
- Your draft entry cites experiments that are already cited elsewhere in the list.
- The list is growing faster than the team's actual understanding is.

When you strengthen an entry, update three things: the evidence parenthetical (add the new IDs), the confidence label if the added evidence changes it, and the count if the entry claims one ("4+ independent tests" → "6+ independent tests").

## Contradictions

When a new result cuts against an existing learning, surface it in the review explicitly. Don't leave both claims standing and don't silently delete the old one. Three legitimate resolutions:

- **Narrow the scope.** The learning holds, but not everywhere. "Persistent status indicators outperform banners" became scoped when GA-374 showed the Pro Indicator's win didn't carry to Basic trials.
- **Split it.** Two mechanisms were bundled into one claim and the new test separated them.
- **Downgrade the confidence.** The pattern may still be real but it no longer deserves High.

Say which one you're doing and why, in the review, in one sentence. This is the single highest-value judgment in the whole run — it's what keeps the doc from accumulating claims nobody has checked in a year.

## Pruning past 20

At 20 entries the list stops being scannable. Don't trim on your own judgment past that point; the call about which beliefs the team keeps front-and-centre belongs to the doc owner. Present options:

> "The TL;DR is at 22 entries. Three ways to get it back under 20:
>
> **A. Merge overlapping claims (recommended).** Entries 2, 9, and 14 are all versions of "isolated visual tweaks don't convert." Folding them into one keeps every data point and drops two slots.
>
> **B. Retire the Low-confidence entries.** Entries 11 and 18 are Low confidence and haven't picked up new evidence in three quarters. They'd still live in their quarter sections.
>
> **C. Split by durability.** Keep 12 High-confidence patterns in the TL;DR, move the Medium/Low ones into a collapsed "Weaker signals we're still watching" toggle below it.
>
> Which way, or a mix?"

Give real entry numbers and real overlaps from the doc you just read. Generic options make the reader do the analysis the skill was supposed to do.

______________________________________________________________________

## Cross-cutting themes for XFN teams

The section at the bottom of the doc routes learnings to the teams that can use them. It's grouped by audience:

```
**For Onboarding/Activation teams:**
**For Pricing & Packaging teams:**
**For Expansion teams:**
**For everyone:**
```

Each bullet is one line, imperative, with supporting experiment IDs in parens:

```
- Don't disrupt success moments to push side-actions (GA-391).
- Defaults at signup compound (GA-80, GA-160).
```

Maintenance each run:

- Add new experiment IDs to bullets they support. A new data point on an existing bullet usually needs no new prose, just the ID.
- Add a bullet only when a new learning is genuinely actionable by a *different* team. If it only tells this team what to do next, it isn't cross-cutting.
- Revise a bullet when a new result undercuts it. Same three resolutions as contradictions above.
- Keep each group to roughly five bullets. If a group is bloating, the weakest bullets are usually the ones citing a single Low-confidence test.

The "For everyone" group holds the meta-lessons about how to run tests, not what to build — power your revenue metrics, don't spend cycles on isolated visual tweaks, protect gates that already convert. New entries there should be about experimental practice.
