# Learning experiments

Use this when the experiment is run **to learn, not to ship a specific
decision** — to size an opportunity, understand behavior, or test whether an idea
is worth building at all (painted-door / fake-door tests, exploratory reads,
"how much would this even move?"). The output is *insight*, not a ship/kill
verdict.

## The mindset shift

A normal test asks "is this change good enough to ship?" and is powered to clear
a fixed bar. A learning experiment asks "what's actually going on / how big is
this?" — so success is a **reliable enough estimate or a clear enough directional
read**, not statistical significance against a ship threshold.

That changes what you optimize:

- You size for **precision** (how tight an estimate you need) rather than power
  to detect one specific MDE.
- **Looser thresholds are acceptable**, because the cost of being wrong is low —
  a learning result feeds the *next* decision, it isn't the decision. You'll
  validate anything promising with a proper powered test later.

## Sizing for precision (not just power)

The practical question is usually "how tight will my estimate be?" The half-width
of a confidence interval for a rate is roughly:

```
half_width ≈ z_sig × sqrt( p(1−p) / n_per_arm )
```

So to get an estimate to within ±w of the truth:

```
n_per_arm ≈ z_sig² × p(1−p) / w²
```

Decide the precision you need ("I need to know the lift to within ±1pp to make
the build call") and size to that. If you'd rather think in effect-detection
terms, you can still use `power_calc.py size` with a coarse MDE and modest power
(e.g. 80%) — just be explicit that you're sizing for a rough read, not a ship
decision.

## The trap to flag loudly

A learning result must **not** be quietly promoted into a ship decision it
wasn't powered for. The failure mode: run a small, cheap learning test, see a
promising number, and ship on it — even though it was never powered to support
that call. If a learning experiment produces something worth acting on, the
honest next step is a properly powered confirmation test, not a launch.

Say this plainly in the pre-analysis doc's decision section: "this is a learning
experiment; a positive read triggers a powered follow-up, not a ship."

## Fine to be lighter on

- A single hard ship/kill decision rule (there isn't one — there's "learned X,
  next step Y").
- Tight guardrails, *if* exposure is small and reversible. But if the learning
  test still touches real users at scale, keep the basic guardrails — a fake-door
  that frustrates users still does harm.

## Still worth doing properly

- Pick the metric that actually answers the learning question, and pull a real
  baseline (don't guess the thing you're trying to learn).
- Run at least a full week so the read isn't a weekday artifact.
- Write down what result would change your mind in which direction — even a
  learning test benefits from committing to its interpretation in advance.
