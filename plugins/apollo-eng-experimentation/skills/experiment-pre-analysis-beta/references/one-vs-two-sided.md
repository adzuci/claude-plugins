# One-sided vs two-sided: what they are and how to decide

Open this at the risk-posture step whenever there's any doubt. Most of the time
the answer is two-sided; the value of this doc is knowing the one case where
one-sided is legitimate and why it's abused everywhere else.

## What the choice actually is

A statistical test reserves a "false-alarm budget" (your significance level,
e.g. 5%). The question is where you spend it:

- **Two-sided** splits the budget across *both* directions (2.5% in each tail).
  You can detect — and would act on — a move up *or* down.
- **One-sided** puts the whole budget in *one* direction (5% in one tail). You
  can only detect a move the way you're looking; you're deliberately blind to
  the other side.

Mechanically that's the difference between `z = 1.96` (two-sided 95%) and
`z = 1.645` (one-sided 95%). One-sided needs ~20% less data — which is exactly
why it's tempting to misuse.

## The deciding question

**"Which directions would I actually act on?"**

- If you'd respond to movement *either way* — a win means ship, a significant
  loss means you've learned the change hurts — you care about both tails.
  **Use two-sided.** This is the honest default for any primary decision metric.
- If you *truly* only care about one direction and would take the identical
  action across the entire other half, one-sided is defensible.

## Where one-sided is legitimate: guardrails / non-inferiority

The real home for one-sided testing is a **guardrail**, where you genuinely only
care about the downside: "I only need to rule out a *drop* in retention; I'm not
trying to improve it." That's a one-sided non-inferiority test, and it's correct.
See `experiment-types/no-harm.md`.

## Where it's abuse: shrinking a primary to save time

Using one-sided on a *primary* just because it needs less data is p-hacking by
design. It makes the test blind to harm on the very metric you're deciding on,
and a null result becomes uninterpretable. Reviewers and leadership are right to
distrust it. If a primary test is too slow, widen the detectable effect instead
(see `concepts.md`), don't go one-sided.

## Quick rule

- **Primary decision metric → two-sided.** Always, unless there's a truly
  one-directional decision with a written rationale.
- **Pure guardrail (only the drop matters) → one-sided non-inferiority.**
- Never switch a primary to one-sided just to hit a deadline.

In the calculator, two-sided is the default; pass `--one-sided` for guardrails,
and `--non-inferiority` (which forces one-sided) for a no-harm margin test.
