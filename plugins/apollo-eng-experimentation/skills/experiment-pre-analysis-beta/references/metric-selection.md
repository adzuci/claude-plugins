# Choosing metrics: primary, secondary, guardrail

Open this at the metric step when the person isn't sure how to pick. The goal is
to land on **one primary**, a few **secondary**, and the **guardrails**.

## The three roles

**Primary — the decision metric (exactly one).**
The single metric the ship/no-ship call hangs on. It must be:

- causally downstream of what's changing,
- sensitive enough to move in the runtime you can afford, and
- something leadership already trusts.
  One primary keeps you honest — two "primaries" secretly doubles your false-alarm
  rate and gives you a menu to cherry-pick from.

Apollo bar (shared with jarvis `experiment-setup`, which warn-and-confirms on
this): the primary must be a **core Apollo-level outcome** — activation,
conversion, retention, core-product adoption — **not a minor funnel step** (a
button click, a modal open, one intermediate event). A treatment can move a
funnel step without moving any outcome the business ships on.

**Secondary — supporting / explanatory.**
These tell you *why* the primary moved and build the story, but you do **not**
gate the decision on them. Because you'll look at several, expect one or two to
"hit" by chance — treat them as directional, or correct for multiple comparisons
and label them exploratory.

**Guardrail — the "don't break anything" metrics.**
Things you're not trying to improve but would refuse to ship a regression on:
latency, error/crash rate, unsubscribes, refund/support-ticket rate, and your
other north-star metrics not under test. Guardrails are tested to *rule out
harm*, not to detect a win — see `experiment-types/no-harm.md`.

## Role is about the question, not the importance

The most common confusion: people assume the metric they care about most should
be the primary. Not so. **A metric's role is defined by the question it answers
and the decision it drives — not by its rank on the list of things you love.**

- Primary answers **"did it help?"** (a superiority test — you must prove a lift).
- Guardrail answers **"did it hurt?"** (a non-inferiority test — you must rule
  out a drop).

Retention can be the single most important metric in the building *and* be a
guardrail. Those aren't in tension. In fact, making your most-protected metric a
superiority *primary* is a trap: a change that's safe-but-neutral would then fail
your test for the wrong reason, and a null result would get misread as "no harm."

## How to pick, mechanically

Trace the causal chain of the change:

```
intervention → immediate behavior → intermediate outcome → business north star
```

- The metric closest to the intervention is the most **sensitive** but least
  meaningful.
- The north star is the most **meaningful** but least sensitive (and slowest).
- Your **primary** usually sits in the middle — sensitive enough to move in a
  reasonable runtime, meaningful enough to decide on.
- Far-downstream metrics you can't move fast become **guardrails** or secondary.

Watch for slow metrics: retention (D7/D30) is meaningful but needs a maturation
window and lots of data, which is why teams often use a faster proxy as the
primary and keep retention as a guardrail/secondary.

## If a team catalog exists

When the experiment belongs to a team with a file under `teams/`, use its
`metrics.md` catalog to propose the standard primary/secondary/guardrail set and
to find where each baseline is pulled from — rather than reinventing it. Confirm
the set still fits this specific experiment before locking it.
