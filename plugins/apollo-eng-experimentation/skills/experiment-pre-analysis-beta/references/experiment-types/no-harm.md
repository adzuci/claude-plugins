# No-harm experiments (non-inferiority)

Use this when the goal is **"don't break anything"** rather than "prove a win" —
typically a broad change (a wholesale UI redesign, a big refactor, a
"modernization") that's too diffuse to measure a clean win on, where the real
mandate is to avoid quietly damaging the product. A lift would be lovely; not
hurting is the requirement.

## Why this is a different problem

In a normal test the expensive mistake is a **false positive** (shipping a dud).
In a no-harm test the expensive mistake is a **false negative — failing to catch
real damage** — because the org is usually predisposed to ship the change, and a
"no significant difference" will be read as a green light. Every design choice
below defends against *missing harm*.

## The inversions to apply

- **Power goes up, not confidence down.** Set power to **90%** (the default for
  this type) so a real drop of margin size is caught 90% of the time, not 80%.
  Confidence stays at the standard.
- **Guardrails are the point, and they usually set the runtime.** The metric
  you're protecting is held to a tight tolerance and often has a low base rate,
  so it needs *more* data than any hoped-for-win primary. Size every gated
  metric and take the largest — expect the guardrail to bind.
- **One-sided on guardrails.** You only care about the downside, so each
  guardrail is a one-sided non-inferiority test. A primary you also hope lifts
  stays two-sided (see `one-vs-two-sided.md`).
- **"Inconclusive" = block.** "We couldn't rule out harm" is not "no harm." If a
  guardrail wasn't adequately powered, the default is don't-ship / keep-running,
  not ship.

## Metric roles for a no-harm test

- **Primary:** the most sensitive near-term metric the change plausibly moves
  (e.g. activation), tested two-sided so a drop also trips it. This carries the
  "did it help?" question if there's any hope of a lift.
- **Guardrails (where the test really lives):** the metrics you must not damage
  — retention, core engagement, plus operational ones (errors, latency, support
  tickets). Each gets a non-inferiority margin.
- **Secondary:** the specific interactions the change was supposed to improve —
  exploratory, for the mechanism story.

## Setting the margin (the crux)

The margin is "the biggest drop we can live with." Deriving it defensibly is the
most important and most-skipped step — don't let anyone pick it by feel. Anchor
it to one of:

- **Business impact:** translate a drop into users/dollars. "A 1pp drop in D7
  retention ≈ N fewer actives/month ≈ $X." The margin is the largest drop still
  below the threshold you'd act on.
- **A fraction of a known effect:** margin ≈ half the smallest historically
  meaningful move on that metric.
- **The trade you'd accept:** the loss you'd tolerate given the win the change
  must deliver elsewhere.

A margin of literally **zero is infeasible** (proving exactly no difference needs
infinite data) — that's the whole reason non-inferiority exists. Get the margin
agreed and written down, with its rationale, **before** launch, so a borderline
result isn't renegotiated after.

## Sizing it

```
# guardrail: rule out a >1pp drop on a 12% metric, one-sided 95%, 90% power
python scripts/power_calc.py size --baseline 0.12 --effect 0.01 --power 0.90 --non-inferiority

# primary: detect a +2pp lift on a 65% metric, two-sided 95%, 80% power
python scripts/power_calc.py size --baseline 0.65 --effect 0.02
```

Take the larger of the two as the sample target; that metric sets the clock. Add
any maturation window (e.g. +7 days for D7 retention) on top of accrual.

## Decision rule to pre-commit

- **Ship** if the primary is flat-or-up (its interval excludes a meaningful
  drop) **and** every guardrail clears its non-inferiority bar.
- **Ship & celebrate** if the primary additionally shows a real lift.
- **Block / iterate** if any guardrail fails its bar, **or** the primary shows a
  real drop — regardless of how good the change looks.
- **Inconclusive** (guardrails underpowered) → block by default and keep running.

## Common trap

Don't make the protected metric a superiority **primary** ("did retention go
*up*?"). Failing to find a lift is not the same as "no harm," and a safe-but-
neutral change would fail for the wrong reason. Protect it as a non-inferiority
guardrail instead. (See `metric-selection.md` on role vs. importance.)
