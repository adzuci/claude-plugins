#!/usr/bin/env python3
"""
power_calc.py  —  Experiment pre-analysis calculator (dependency-free)

Everything the pre-analysis flow needs to turn a business goal into a sample
size, a runtime, and a decision-quality check. No third-party packages: the
normal distribution is implemented locally so this runs anywhere Python 3 does
(including inside the app repo with nothing installed).

Four things it does:

  1. size     Given a goal (an effect to detect, or a drop to rule out),
              return the sample size PER ARM and the total.
  2. runtime  Turn a sample size into weeks, given weekly exposure.
  3. power    Verify a planned sample: "if I run this many per arm, what power
              do I get to detect the effect I care about?" (used by the pre-delivery review)
  4. table    A sensitivity grid — sample size + runtime across a range of
              effects / powers — the thing you paste into a pre-analysis doc.

Two experiment goals are supported everywhere:

  - superiority     "detect a change of size X"  (the usual A/B win-seeking test)
  - non-inferiority "rule out a drop bigger than X"  (guardrails / no-harm)

Two metric shapes:

  - proportion   a rate: conversion, activation, retention (a %/fraction)
  - continuous   a per-user number: sessions, clicks, minutes, revenue

Multi-arm (A/B/n) is handled by telling it how many arms you have; it splits
traffic evenly and tightens the significance threshold for the extra
comparisons against control (Bonferroni — deliberately conservative; see notes).

Run  `python power_calc.py --selftest`  to check it against known values.
Run  `python power_calc.py <command> --help`  for any command's options.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Normal distribution (no scipy required)
# ---------------------------------------------------------------------------

def norm_cdf(z: float) -> float:
    """P(Z <= z) for a standard normal. Uses the error function."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """
    Inverse standard-normal CDF (the 'z for a given probability').
    Acklam's rational approximation; absolute error < ~1.2e-9, which is far
    tighter than anything that matters for sample sizing.
    """
    if not (0.0 < p < 1.0):
        raise ValueError("norm_ppf expects a probability strictly between 0 and 1")

    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]

    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
               ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q / \
           (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1)


# ---------------------------------------------------------------------------
# The z-values that a pre-analysis actually turns on
# ---------------------------------------------------------------------------

def z_significance(confidence: float, two_sided: bool) -> float:
    """
    z for the false-alarm control. `confidence` is 0.95 for 95%.
    Two-sided splits the risk across both tails; one-sided puts it all in one.
    Non-inferiority is inherently one-sided, so pass two_sided=False there.
    """
    alpha = 1.0 - confidence
    return norm_ppf(1 - alpha / 2) if two_sided else norm_ppf(1 - alpha)


def z_power(power: float) -> float:
    """z for the miss control. `power` is 0.8 for 80%."""
    return norm_ppf(power)


def _comparisons(arms: int) -> int:
    """How many variant-vs-control comparisons we're making."""
    return max(1, arms - 1)


def _adjusted_confidence(confidence: float, arms: int, correct: bool) -> float:
    """
    Bonferroni: spread the false-alarm budget across the extra comparisons.
    Conservative (it slightly over-sizes), but simple and defensible. Dunnett's
    correction is a little less punishing for many-vs-one-control designs; if
    traffic is tight, size with Dunnett in a dedicated tool instead.
    """
    if not correct:
        return confidence
    k = _comparisons(arms)
    alpha = (1.0 - confidence) / k
    return 1.0 - alpha


# ---------------------------------------------------------------------------
# Results container
# ---------------------------------------------------------------------------

@dataclass
class SizeResult:
    n_per_arm: int
    arms: int
    total_n: int
    effect_variance_note: str

    def __str__(self) -> str:
        return (f"  per arm : {self.n_per_arm:,}\n"
                f"  arms    : {self.arms}\n"
                f"  total   : {self.total_n:,}")


# ---------------------------------------------------------------------------
# Sizing — proportions
# ---------------------------------------------------------------------------

def size_proportion(baseline: float,
                    effect: float,
                    confidence: float = 0.95,
                    power: float = 0.80,
                    two_sided: bool = True,
                    non_inferiority: bool = False,
                    arms: int = 2,
                    correct_multiple: bool = True) -> SizeResult:
    """
    Sample size per arm for a rate metric.

    baseline        current rate, e.g. 0.65
    effect          superiority: the absolute change to detect, e.g. 0.02 (2 pts)
                    non-inferiority: the max drop to rule out (a positive number)
    non_inferiority forces a one-sided test around a tolerated margin
    arms            total arms including control (2 = plain A/B)
    """
    if non_inferiority:
        two_sided = False  # ruling out a one-directional drop
        p_c = baseline
        p_t = baseline          # assume no true harm when powering an NI test
        denom = effect ** 2
        var = p_c * (1 - p_c) + p_t * (1 - p_t)
        note = "non-inferiority: powered assuming the true effect is zero"
    else:
        p_c = baseline
        p_t = baseline + effect
        if not (0 < p_t < 1):
            raise ValueError("baseline + effect must stay between 0 and 1")
        denom = (p_t - p_c) ** 2
        var = p_c * (1 - p_c) + p_t * (1 - p_t)
        note = "superiority: two rates compared"

    conf = _adjusted_confidence(confidence, arms, correct_multiple)
    za = z_significance(conf, two_sided)
    zb = z_power(power)
    n = ((za + zb) ** 2) * var / denom
    n_per_arm = math.ceil(n)
    return SizeResult(n_per_arm, arms, n_per_arm * arms, note)


# ---------------------------------------------------------------------------
# Sizing — continuous
# ---------------------------------------------------------------------------

def size_continuous(sd: float,
                    effect: float,
                    confidence: float = 0.95,
                    power: float = 0.80,
                    two_sided: bool = True,
                    non_inferiority: bool = False,
                    arms: int = 2,
                    correct_multiple: bool = True) -> SizeResult:
    """
    Sample size per arm for a per-user number.

    sd       standard deviation of the metric PER USER (from the baseline query)
    effect   superiority: the change to detect, in the metric's units
             non-inferiority: the max drop to rule out (positive)

    Tip: if you have a pre-period value per user, variance reduction (CUPED)
    shrinks `sd` by sqrt(1 - rho^2). Feed the reduced sd here and the test
    gets correspondingly shorter for free.
    """
    if non_inferiority:
        two_sided = False
    conf = _adjusted_confidence(confidence, arms, correct_multiple)
    za = z_significance(conf, two_sided)
    zb = z_power(power)
    n = ((za + zb) ** 2) * (2 * sd ** 2) / (effect ** 2)
    n_per_arm = math.ceil(n)
    note = ("non-inferiority (continuous)" if non_inferiority
            else "superiority (continuous)")
    return SizeResult(n_per_arm, arms, n_per_arm * arms, note)


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

def runtime_weeks(n_per_arm: int,
                  weekly_exposure_total: float,
                  arms: int = 2,
                  min_weeks: float = 1.0) -> float:
    """
    Weeks to accrue the sample. weekly_exposure_total is units/week across ALL
    arms; it gets split evenly. Rounds up to a minimum full-week run so we never
    read a test that only saw part of a week. Does NOT add a metric-maturation
    window (e.g. D7 retention needs +7 days) — add that separately.
    """
    per_arm_weekly = weekly_exposure_total / arms
    weeks = n_per_arm / per_arm_weekly
    return max(weeks, min_weeks)


# ---------------------------------------------------------------------------
# Reverse: verify a planned sample's power
# ---------------------------------------------------------------------------

def power_from_n_proportion(n_per_arm: int,
                            baseline: float,
                            effect: float,
                            confidence: float = 0.95,
                            two_sided: bool = True,
                            non_inferiority: bool = False,
                            arms: int = 2,
                            correct_multiple: bool = True) -> float:
    """
    Verify a PLANNED sample: "if I run n_per_arm per arm, what's my power to
    detect an effect of the size I care about?" Used by the pre-delivery review to confirm
    a chosen sample size actually delivers the target power.

    Pass the effect you're planning around (your MDE or harm margin). This is a
    pre-analysis check — not a tool for interpreting an experiment already running.
    """
    if non_inferiority:
        two_sided = False
        p_c = p_t = baseline
    else:
        p_c = baseline
        p_t = baseline + effect
    var = p_c * (1 - p_c) + p_t * (1 - p_t)
    conf = _adjusted_confidence(confidence, arms, correct_multiple)
    za = z_significance(conf, two_sided)
    zb = abs(effect) * math.sqrt(n_per_arm / var) - za
    return norm_cdf(zb)


# ---------------------------------------------------------------------------
# Sensitivity table
# ---------------------------------------------------------------------------

def sensitivity_table(baseline: float,
                      effects: list[float],
                      weekly_exposure_total: float,
                      powers: tuple[float, ...] = (0.80, 0.90),
                      confidence: float = 0.95,
                      two_sided: bool = True,
                      non_inferiority: bool = False,
                      arms: int = 2,
                      correct_multiple: bool = True,
                      maturation_days: float = 0.0) -> str:
    """Markdown table of sample size + runtime across effects and powers."""
    if non_inferiority:
        two_sided = False  # NI is one-sided; keep the footer label honest
    label = "Max drop to rule out" if non_inferiority else "Effect to detect"
    header = f"| {label} | " + " | ".join(
        f"n/arm @{int(p*100)}% | runtime @{int(p*100)}%" for p in powers) + " |"
    sep = "|" + "---|" * (1 + 2 * len(powers))
    lines = [header, sep]
    mat_weeks = maturation_days / 7.0
    for e in effects:
        cells = [f"{e:+.3g} (base {baseline:.3g})" if not non_inferiority
                 else f"{e:.3g}"]
        for p in powers:
            r = size_proportion(baseline, e, confidence, p, two_sided,
                                non_inferiority, arms, correct_multiple)
            wk = runtime_weeks(r.n_per_arm, weekly_exposure_total, arms) + mat_weeks
            cells.append(f"{r.n_per_arm:,}")
            cells.append(f"{wk:.1f} wk")
        lines.append("| " + " | ".join(cells) + " |")
    footer = (f"\n_Baseline {baseline:.3g}, {int(confidence*100)}% confidence, "
              f"{'two' if two_sided else 'one'}-sided, {arms} arms"
              f"{', Bonferroni-corrected' if correct_multiple and arms > 2 else ''}"
              f"{f', +{maturation_days:g}d maturation' if maturation_days else ''}."
              " Runtime rounds up to a 1-week minimum._")
    return "\n".join(lines) + "\n" + footer


# ---------------------------------------------------------------------------
# Self-test — checks against the numbers worked by hand in the playbook
# ---------------------------------------------------------------------------

def _selftest() -> None:
    print("Running self-test against known playbook values...\n")

    # Primary: activation 65%, +2pp, two-sided 95%, 80% power  -> ~8,800/arm
    r = size_proportion(0.65, 0.02, 0.95, 0.80, two_sided=True)
    print(f"Activation +2pp, 95%/80% two-sided : {r.n_per_arm:,}/arm  (expect ~8,800)")
    assert 8600 <= r.n_per_arm <= 9000, r.n_per_arm

    # Guardrail: retention 12%, 1pp margin, one-sided 95%, 90% power -> ~18,100/arm
    r = size_proportion(0.12, 0.01, 0.95, 0.90, non_inferiority=True)
    print(f"Retention NI 1pp, 95%/90% one-sided: {r.n_per_arm:,}/arm  (expect ~18,100)")
    assert 17800 <= r.n_per_arm <= 18400, r.n_per_arm

    # Reverse: 18,100/arm should read back to ~90% power
    p = power_from_n_proportion(18100, 0.12, 0.01, 0.95,
                                two_sided=False, non_inferiority=True)
    print(f"Reverse power at 18,100/arm        : {p*100:.1f}%   (expect ~90%)")
    assert 0.88 <= p <= 0.92, p

    # 13,100/arm should read back to ~80%
    p = power_from_n_proportion(13100, 0.12, 0.01, 0.95,
                                two_sided=False, non_inferiority=True)
    print(f"Reverse power at 13,100/arm        : {p*100:.1f}%   (expect ~80%)")
    assert 0.78 <= p <= 0.82, p

    # Runtime: 18,100/arm at 11,300/week total, 2 arms -> ~3.2 weeks
    wk = runtime_weeks(18100, 11300, arms=2)
    print(f"Runtime 18,100/arm @ 11,300/wk     : {wk:.1f} wk  (expect ~3.2)")
    assert 3.0 <= wk <= 3.4, wk

    print("\nAll self-tests passed.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_common(sp, ni_default=False):
    sp.add_argument("--baseline", type=float, help="current rate (0-1) for proportion metrics")
    sp.add_argument("--sd", type=float, help="per-user std dev for continuous metrics")
    sp.add_argument("--effect", type=float, required=True,
                    help="superiority: change to detect; non-inferiority: max drop to rule out")
    sp.add_argument("--confidence", type=float, default=0.95)
    sp.add_argument("--power", type=float, default=0.80)
    sp.add_argument("--arms", type=int, default=2)
    sp.add_argument("--one-sided", action="store_true")
    sp.add_argument("--non-inferiority", action="store_true", default=ni_default)
    sp.add_argument("--no-correction", action="store_true",
                    help="skip Bonferroni adjustment for multi-arm")


def main() -> None:
    ap = argparse.ArgumentParser(description="Experiment pre-analysis calculator")
    ap.add_argument("--selftest", action="store_true", help="verify against known values")
    sub = ap.add_subparsers(dest="cmd")

    sp = sub.add_parser("size", help="sample size for a goal")
    _add_common(sp)

    rp = sub.add_parser("runtime", help="weeks to accrue a sample size")
    rp.add_argument("--n-per-arm", type=int, required=True)
    rp.add_argument("--weekly-exposure", type=float, required=True, help="units/week across ALL arms")
    rp.add_argument("--arms", type=int, default=2)
    rp.add_argument("--maturation-days", type=float, default=0.0)

    pp = sub.add_parser("power", help="verify a planned sample reaches the target power")
    pp.add_argument("--n-per-arm", type=int, required=True)
    pp.add_argument("--baseline", type=float, required=True)
    pp.add_argument("--effect", type=float, required=True, help="the effect you're planning around (MDE or harm margin)")
    pp.add_argument("--confidence", type=float, default=0.95)
    pp.add_argument("--arms", type=int, default=2)
    pp.add_argument("--one-sided", action="store_true")
    pp.add_argument("--non-inferiority", action="store_true")
    pp.add_argument("--no-correction", action="store_true")

    tp = sub.add_parser("table", help="sensitivity grid")
    tp.add_argument("--baseline", type=float, required=True)
    tp.add_argument("--effects", type=float, nargs="+", required=True)
    tp.add_argument("--weekly-exposure", type=float, required=True)
    tp.add_argument("--confidence", type=float, default=0.95)
    tp.add_argument("--arms", type=int, default=2)
    tp.add_argument("--one-sided", action="store_true")
    tp.add_argument("--non-inferiority", action="store_true")
    tp.add_argument("--maturation-days", type=float, default=0.0)
    tp.add_argument("--no-correction", action="store_true")

    args = ap.parse_args()

    if args.selftest:
        _selftest()
        return

    if args.cmd == "size":
        two_sided = not args.one_sided
        correct = not args.no_correction
        if args.baseline is not None:
            r = size_proportion(args.baseline, args.effect, args.confidence,
                                args.power, two_sided, args.non_inferiority,
                                args.arms, correct)
        elif args.sd is not None:
            r = size_continuous(args.sd, args.effect, args.confidence, args.power,
                                two_sided, args.non_inferiority, args.arms, correct)
        else:
            ap.error("size needs --baseline (proportion) or --sd (continuous)")
        print(f"Sample size ({r.effect_variance_note}):")
        print(r)

    elif args.cmd == "runtime":
        wk = runtime_weeks(args.n_per_arm, args.weekly_exposure, args.arms)
        wk += args.maturation_days / 7.0
        print(f"Estimated runtime: {wk:.1f} weeks "
              f"({args.n_per_arm:,}/arm, {args.weekly_exposure:,.0f}/wk across {args.arms} arms"
              f"{f', +{args.maturation_days:g}d maturation' if args.maturation_days else ''}).")

    elif args.cmd == "power":
        two_sided = not args.one_sided
        correct = not args.no_correction
        p = power_from_n_proportion(args.n_per_arm, args.baseline, args.effect,
                                    args.confidence, two_sided,
                                    args.non_inferiority, args.arms, correct)
        print(f"Power at planned sample: {p*100:.1f}%  "
              f"(at {args.n_per_arm:,}/arm to detect {args.effect:+.3g} on a {args.baseline:.3g} base).")
        if p < 0.8:
            print("  Below 80% — this planned sample is underpowered for that effect; raise n or widen the effect/margin.")

    elif args.cmd == "table":
        print(sensitivity_table(args.baseline, args.effects, args.weekly_exposure,
                                confidence=args.confidence,
                                two_sided=not args.one_sided,
                                non_inferiority=args.non_inferiority,
                                arms=args.arms,
                                correct_multiple=not args.no_correction,
                                maturation_days=args.maturation_days))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
