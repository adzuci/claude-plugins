# Global defaults (org-wide standard)

These are the single source of truth for the statistical dials. They are set
**once, for everyone** — individual teams do not override them, so that a result
from one team means the same thing as a result from another. Team files carry
metrics, OKRs, and learnings only.

If someone needs a test to finish sooner, the safe lever is to **widen the
effect they're detecting** (or the harm margin), never to loosen these. See
`concepts.md` for why.

| Dial | Standard | When it changes |
|---|---|---|
| Confidence | **95%** | Lower to 99% only for an irreversible/expensive launch. |
| Power | **80%** for normal (win-seeking) tests | **90%** when the goal is to *rule out harm* (no-harm / guardrails), because missing real damage is the costly mistake there. |
| Sided | **Two-sided** for a primary decision metric | **One-sided** only for pure guardrails / non-inferiority. See `one-vs-two-sided.md`. |
| Minimum runtime | **1 full week, 2 preferred** | Never read a test that has seen only part of a week — weekday/weekend behavior differs. Add metric-maturation time (e.g. +7 days for D7 retention) on top. |
| Traffic split | **Even (50/50, or 1/k for k arms)** | Uneven splits cost total sample; only use a small holdback with a specific reason. |
| Multiple comparisons | **Correct when >2 arms** (Bonferroni against control by default) | See `experiment-types/multivariant.md`. |

## Maintenance

- **Owner:** the apollo-eng-experimentation plugin maintainers (growth experimentation lead to adopt post-beta)
- **Review cadence:** revisit only when the team deliberately changes its
  standard, not per experiment.
- If you change a value here, every experiment inherits it automatically — that's
  the point of keeping it in one place.
