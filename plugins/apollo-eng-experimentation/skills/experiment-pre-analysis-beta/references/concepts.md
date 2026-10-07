# Concepts, in plain language

Open this when someone hesitates or asks "what does that mean?". Explain the one
thing they're stuck on, then get back to the flow. Don't read it all out.

## The two mistakes every experiment can make

Everything here comes back to two opposite errors:

- **A false alarm** — calling something a real change when it was just noise.
- **A miss** — failing to see a real change that was actually there.

Two separate dials guard against these two mistakes, and you can't max both for
free — the price of turning either up is more data (a longer test).

## Confidence (a.k.a. significance)

**Confidence protects against false alarms.** 95% confidence means: "if nothing
were really happening, we'd only be fooled into seeing a fake result 5% of the
time."

"Confidence" and "significance level" are the *same dial* from two ends: 95%
confidence = a 5% significance level. Same thing.

## Power

**Power protects against misses.** 80% power means: "if a real effect of the
size we care about exists, we'll actually detect it 80% of the time" (and miss
it the other 20%).

Smoke-alarm analogy that makes it stick:

- **Confidence = not going off when there's no fire** (few false alarms).
- **Power = actually going off when there IS a fire** (few missed fires).

Which one you turn up depends on which mistake is more expensive *here*:

- Normal "find a win" test → a false alarm (shipping a dud) is worst → guard
  confidence, accept 80% power.
- No-harm test → a *miss* (real damage slips through) is worst → raise power to
  90%.

## MDE — the effect worth detecting

The MDE (minimum detectable effect) sounds technical but it's a **business**
number: the smallest change that would actually be worth shipping this for.
Ask it that way. Set it from what pays back the build/maintenance/risk, or from
how big past changes on this surface really were.

The one rule that matters: **a smaller MDE costs sample size quadratically** —
halving the effect you want to detect *quadruples* the data (and time) needed.
So the MDE is the main lever on how long a test runs.

## Why we widen the effect instead of loosening confidence/power

When a test is too slow, it's tempting to drop confidence (say to 80%) to finish
faster. Resist it, especially on a primary: 80% confidence means a 20% false-
alarm rate — one in five times, noise looks like a win. You'd be buying speed by
making your ship decision less trustworthy.

Widening the detectable effect ("we'll only try to catch a bigger change") buys
the same time with no cost to false alarms or missed harm. Reach for that first.
Order of levers: **widen the effect → variance reduction (CUPED) → only then
touch the dials**, and only in the direction that matches which mistake is cheap
for that metric.

## One-sided vs two-sided

A quick gut check — full guidance in `one-vs-two-sided.md`:

- **Two-sided** = you'd act on movement in *either* direction (a win ships, a
  loss teaches). The honest default for a decision metric.
- **One-sided** = you truly only care about one direction. Its legitimate home
  is guardrails ("I only need to rule out a drop"), not win-detection.

## Non-inferiority (the "no-harm" idea)

Normal tests try to *prove a difference*. A non-inferiority test tries to
**rule out a drop bigger than a margin you set in advance**. You can't prove
"exactly zero difference" (that needs infinite data), so instead you agree on a
small tolerable margin and prove the true effect isn't worse than that. This is
the right tool whenever the goal is "don't hurt this metric." See
`experiment-types/no-harm.md`.
