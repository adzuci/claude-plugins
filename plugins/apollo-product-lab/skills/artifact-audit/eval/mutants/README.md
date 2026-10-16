# Mutant corpus — proving the gate is not dead

> Answers the blocker that has been open since the framework started: there is no labelled corpus, so the audit cannot be gated.

## Why this exists

> Green is two different messages wearing the same colour. "I checked, and the work was clean" and "I am incapable of finding anything" produce identical output.

A gate that never fires looks exactly like a gate with nothing to catch. **The only way to tell them apart is to hand it something it should reject and confirm it does.**

Our org rule for shipping an agent skill is ≥90% activation precision and ≤15% false-positive rate over 50 historical PRs. That is a *model-capability* measure and needs history we do not have for documents. The claim we actually need is narrower and a **control** claim:

> The audit rejects a document carrying a defect it is specified to catch, and does not reject a clean one.

That corpus we **author**, not mine.

## Structure

```
mutants/
  originals/            accepted documents, unmodified
  <class>/              one mutant per original, per defect class
  expected.json         which class each mutant carries, and where
```

Each mutant is a copy of an original with **exactly one defect injected**, and the injection site recorded. One defect per mutant, or a miss cannot be attributed.

## The five defect classes

Provisional — these should be re-derived from the fifteen real findings once they are adjudicated (Q-X2). Guessing the classes risks testing sensitivity to defects that do not occur.

| Class | Injection | Must be caught by |
|---|---|---|
| `missing-required-section` | Delete a required section, or empty it while leaving the heading | Phase 2, deterministic |
| `unmeasurable-metric` | Replace a numeric success metric with a directional claim | Phase 2, deterministic |
| `self-contradiction` | Change one instance of a repeated quantity so the document disagrees with itself | Phase 2.5, deterministic |
| `unestimated-requirement` | Add a gating requirement to a constraint register with no matching estimate line | Phase 5, deterministic |
| `mutually-exclusive-claim` | Change one document so it contradicts a settled decision in a sibling | Phase 4, model judgement |

Four of five are catchable deterministically, which is the point: **most of the gate's value should be provable without a live model**, and therefore re-runnable in CI for free.

## Pass conditions

```
fire_on_mutant      = 1.00   # every mutant is caught. A miss is a dead gate.
fire_on_original    ≤ 0.15   # false positives on clean docs, against the org bar
attribution_correct ≥ 0.90   # caught it AND named the right class
```

`fire_on_mutant` is deliberately 1.00, not 0.90. These are defects we chose and injected ourselves — failing to catch one is not a capability shortfall, it is proof the check does not work.

`attribution_correct` matters separately because a finding routed to the wrong class routes to the wrong stage, and mis-routing poisons the selection signal.

## What this does and does not buy

**Buys:** proof the gate is alive, a real false-positive rate against a stated bar, a deterministic CI check with no live model, and a regression test — the same mutants re-run next month must still be caught.

**Does not buy:** any precision estimate on **unseen real defects.** Injection measures sensitivity to defects already enumerated. It substitutes for the load-bearing half of the org rule and not the other half.

**Say that when proposing it.** Overclaiming here would be the same failure the corpus exists to prevent.

## Pair it with shadow mode

Run the audit advisory-only on real initiatives while the injected corpus guards the control claim. Human gate verdicts on real findings become the labelled corpus over time — real defects, real distribution, no authoring bias.

The injected corpus keeps the gate honest from day one; shadow mode builds the corpus that eventually answers the precision question. Neither substitutes for the other.

## Status

**Not built.** This is the specification. Building it is roughly an afternoon: pick ten accepted documents, inject five defects each, record sites in `expected.json`, wire a CI job.

It is the single highest-value unbuilt item in the framework, because until it exists **no claim about audit quality is falsifiable.**
