# Multivariant experiments (A/B/n and full multivariate)

Use this when there's **more than one variant**, or **more than one thing
changing at once**. Two different shapes hide under "multivariant," and they
have very different costs:

- **A/B/n** — several versions of *one* thing (control + variant B + variant C…).
  You're picking the best of a few options.
- **Full multivariate (MVT)** — several *factors* combined (headline × image ×
  button), testing every combination to find interactions. Far more demanding.

## The traffic tax

More arms means each arm gets a smaller slice of the same weekly traffic, so
runtime stretches. The sample size *per arm* is roughly what a plain A/B needs
for the comparison you care about, but you now fund several arms **and** tighten
the threshold for the extra comparisons (below). Rule of thumb: expect a k-arm
test to take meaningfully longer than a 2-arm test at the same traffic.

Full MVT is worse: to estimate interactions reliably you need enough users in
*every combination*, which multiplies quickly (3 factors × 2 levels = 8 cells).
MVT is realistic only on high-traffic surfaces.

## The multiple-comparisons problem

Every extra variant you test against control is another chance to see a fake
"winner." Testing many things at the default 5% false-alarm rate inflates the
real family-wise error well past 5%.

Handle it deliberately:

- **Designate one control** and compare each variant against it (not every
  variant against every other).
- **Correct the threshold.** The calculator applies **Bonferroni** by default
  when `--arms > 2`: it splits the false-alarm budget across the `k−1`
  comparisons. It's conservative (slightly over-sizes) but simple and
  defensible. **Dunnett's** correction is tighter for many-vs-one-control
  designs — reach for it (in a dedicated tool) if traffic is tight and
  Bonferroni makes the test infeasible.
- **Still one primary metric.** Multivariant means multiple *arms*, not multiple
  primary *metrics*. Keep a single decision metric.

## Sizing it

```
# 3 arms (control + 2 variants), detect +2pp on a 65% primary, Bonferroni auto-applied
python scripts/power_calc.py size --baseline 0.65 --effect 0.02 --arms 3

# see the runtime with 3 arms at your weekly exposure
python scripts/power_calc.py runtime --n-per-arm <n> --weekly-exposure <total/wk> --arms 3
```

`--no-correction` disables the Bonferroni adjustment if you're deliberately
handling comparisons another way — use it knowingly.

## Practical guidance

- Prefer **A/B/n against a shared control** over full MVT unless traffic is
  genuinely large and you specifically need interaction effects. Most "we want
  to test a few designs" questions are A/B/n, not MVT.
- If arms are cheap ideas and traffic is tight, consider testing fewer, stronger
  variants — every extra arm you add slows the whole test for everyone.
- Watch that the arms are truly comparable (same eligibility, same exposure
  point); a broken arm poisons the shared-control comparison.
