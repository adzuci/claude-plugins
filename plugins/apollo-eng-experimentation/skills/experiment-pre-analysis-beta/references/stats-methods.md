# Stats methods: the formulas and when each applies

This is the "for the record" layer — the math behind `scripts/power_calc.py`, so
anyone can check the work or size something by hand. You rarely need to read this
to *run* a pre-analysis; the calculator handles it. It matters for review and
for edge cases the calculator doesn't cover.

## The z-values you reuse

| Purpose | Symbol | Value |
|---|---|---|
| Significance, 95% two-sided | z(1−α/2) | 1.960 |
| Significance, 95% one-sided | z(1−α) | 1.645 |
| Power 80% | z(1−β) | 0.842 |
| Power 90% | z(1−β) | 1.282 |

## Sample size — proportion metric (per arm)

For a rate metric (conversion, activation, retention), two-sample, equal split:

```
n = (z_sig + z_pow)²  ×  [ p_c(1−p_c) + p_t(1−p_t) ]  /  (p_t − p_c)²
```

- `p_c` = control (baseline) rate, `p_t` = `p_c` + effect.
- Superiority: `z_sig` is two-sided by default.
- Non-inferiority: use one-sided `z_sig`, set the denominator to `margin²`, and
  assume `p_t = p_c` (you power it as if the true effect is zero). That's the
  "rule out a drop bigger than the margin" test.

## Sample size — continuous metric (per arm)

For a per-user number (sessions, clicks, minutes, revenue):

```
n = 2 × (z_sig + z_pow)² × σ²  /  effect²
```

- `σ` is the **per-user** standard deviation, measured at the unit of
  randomization — not per event. Per-event variance understates the truth and
  badly undersizes the test.
- Skewed metrics (revenue, counts) have large σ; consider a capped/winsorized
  version or variance reduction (below).

## Variance reduction (CUPED)

If you have a pre-period value of the metric per user, regressing it out shrinks
variance by roughly `(1 − ρ²)`, where ρ is the pre/post correlation:

```
σ²_adjusted = σ² × (1 − ρ²)
```

Typical reductions of 30–50% cut the required sample size by the same fraction,
for free. For continuous engagement metrics this is usually the biggest lever
after the MDE. Feed the reduced σ into the continuous formula.

## Reverse: verify a planned sample's power

To confirm a chosen sample size delivers the target power, solve the same
equation for power:

```
z_pow = effect × sqrt( n_per_arm / [p_c(1−p_c) + p_t(1−p_t)] )  −  z_sig
power = Φ(z_pow)          # Φ is the normal CDF; z=0.84→80%, z=1.28→90%
```

Use the effect you're planning around (MDE or margin). This is a pre-analysis
check — interpreting a test that's already running is post-analysis, out of scope.

## Multiple arms (A/B/n)

With `k` arms there are `k−1` comparisons against control. The default handling
is Bonferroni: use `α / (k−1)` for each comparison (i.e. raise the per-comparison
confidence). It's conservative — it slightly over-sizes. Dunnett's correction is
tighter for many-variants-vs-one-control designs; if traffic is tight, size with
a tool that implements Dunnett. Either way, total sample = per-arm × k, and
splitting traffic k ways lengthens runtime. See `experiment-types/multivariant.md`.

## Things the formulas assume (and when they break)

- **Independent units.** If users cluster (shared accounts, teams, sessions
  within a user), the effective sample is smaller than the row count — you need
  cluster-robust methods or randomize at the cluster level.
- **Roughly stable base rates.** Strong seasonality or trends inflate variance;
  size on a representative window and run at least a full week.
- **Fixed horizon.** These sizes assume you look once, at the end. If you peek
  repeatedly, use sequential/always-valid methods (Amplitude does this by
  default — see `data-sources/amplitude.md`) rather than the fixed-n result.
