---
name: experiment-pre-analysis-beta
description: >-
  BETA. Plans an experiment before launch: primary, secondary and guardrail
  metrics, fresh baselines, the effect to detect or the drop to rule out,
  confidence and power, sample size and runtime. Hands over a chat summary, a
  plan file, and an offered update to the Experiments DB entry. Not for
  interpreting a running or finished experiment.
disable-model-invocation: true
metadata:
  lifecycle-stage: Discovery
---

# Experiment Pre-Analysis

Lifecycle stage: **Discovery**. Follow
`${CLAUDE_PLUGIN_ROOT}/references/experiment-lifecycle-conventions.md` for how to
open, check tools, collect inputs, teach, hand over, review, and close. This file
holds only what is specific to pre-analysis.

Plans an experiment so its results will mean something. The output is a
**decision contract**: what result makes us ship, kill, or iterate, proven to
have enough data to tell those apart.

## Invocation

```text
/apollo-eng-experimentation:experiment-pre-analysis-beta
/apollo-eng-experimentation:experiment-pre-analysis-beta <experiment name or one-line description>
```

The argument is optional; intake asks for anything not passed.

## Open

- **Produces:** a pre-launch plan: metrics, baselines, targets, sample size,
  runtime, and the decision rule.
- **Does not:** interpret a running or finished experiment (that is
  post-analysis, out of scope); decide where exposure fires
  (`experiment-exposure-design-beta`); inventory the experiment's
  events (`experiment-analytics-audit-beta`). It picks one existing event as
  the exposure proxy so the runtime clock has a number, nothing more.

## Preflight

- **Baselines need a data source.** Snowflake through the Jarvis MCP
  (`references/data-sources/snowflake.md`) or the Amplitude MCP
  (`references/data-sources/amplitude.md`). With neither, baselines can only come
  from numbers the user pastes, and the plan says so next to each one.
- **Calculator:** `python scripts/power_calc.py --selftest` passes.
- **Notion MCP:** only if the user wants the DB entry update written for them.
- **Leadgenie checkout**, recommended: step 3 reads the code around the
  planned exposure surface to find which existing event fires there. Without
  it, candidates come from the Amplitude taxonomy or the user, and the plan
  says so.

## Inputs

Ask for what is missing in one message; read prior artifacts before asking what
they already answer.

1. **The change and the hypothesis**: "[change] moves [metric] because [reason]".
1. **The decision**: what we do for each outcome. Write this first; it drives
   everything.
1. **The Experiments DB entry** (URL), if one exists. Read Problem, Hypothesis,
   Prediction, and Experiment Design from it.
1. **Exposure assumptions**: who is eligible, the moment or surface that counts
   someone as exposed (that is the entry event the weekly volume proxy counts),
   population, arms and split. Take them from the exposure-design hand-over when
   one exists (the skills ran out of the usual order), otherwise from the ERD,
   PRD, DB entry, or the user's own words, and record the source. The real
   exposure event does not exist yet at this stage; step 3 picks an existing
   event close enough to serve as its proxy. This skill does not decide where
   exposure fires; it gets as close as the data already there allows, and says
   so.
1. **Expected weekly volume** into the surface, if known; otherwise pulled in
   step 3.

Restate in at most six lines and get a yes.

## Standards

- `references/defaults.md` is the one statistical standard: 95% confidence; 80%
  power, or 90% when the goal is to rule out harm; two-sided for a primary,
  one-sided for a pure guardrail; Bonferroni when there are more than two arms.
  Teams never override it. These match the jarvis `experiment-setup` skill
  (α 0.05, Bonferroni for more arms, relative lift) so the two pipelines agree.
- **Baselines are always pulled fresh**, on the eligible population, at the unit
  of randomization, over a recent full-week-plus window. No number is a gap to
  flag, never a guess.
- **Explain by consequence**, from `references/concepts.md`, when asked or when a
  choice has a cost the user may not see (a smaller effect to detect quadruples
  the data; loosening confidence buys speed with false alarms).

## Flow

1. **Classify.** Standard win-seeking A/B, or open the matching file and follow
   it: `references/experiment-types/no-harm.md`, `multivariant.md`,
   `learning.md`.
1. **Metrics.** One **primary** (the decision metric, a core Apollo outcome, not
   a funnel step; the bar is in `references/metric-selection.md`), a few
   **secondary** (explanatory, never gated), and the **guardrails** (must not
   break). Apollo's four always-on team-level guardrails (Apollo active,
   free-to-paid, record actioned, email sent) are the default set; anything else
   is a custom guardrail and labeled as such. Role is the question a metric
   answers, not its importance: the metric you most want to protect is usually a
   guardrail.
1. **Exposure proxy and volume.** Pick the existing event closest to the
   exposure moment: the one that fires when an eligible user reaches the
   surface where the first visible difference will be, and no earlier. Find
   candidates in the leadgenie code around that surface
   (`rg -n "zenalytics\.track\(" <surface folder>` lists what fires there) and
   in the Amplitude taxonomy (`references/data-sources/amplitude.md`). Show
   them, say what each one misses (fires before eligibility is known, fires on
   a route treatment skips, day-sampled, extension-only), and let the user
   pick. Pull weekly distinct eligible users on it with the same eligibility
   filter the baselines use. The plan names it as a proxy and says what the
   real exposure point must match.
1. **Baselines.** Pull each one and keep its source, query, and date. Know how
   solid it is: exact metric on the eligible population over a full window; a
   proxy or shortened window with the assumption named; or missing. A missing
   baseline is never fed into sizing. The plan phrases this in words next to the
   number, not as a grade.
1. **Targets.** The effect to detect (smallest lift worth shipping) or, for a
   guardrail, the margin (biggest tolerable drop). Record the primary's effect as
   a **relative %**; jarvis consumes it that way. Confidence, power, and
   sidedness from `references/defaults.md`; open
   `references/one-vs-two-sided.md` if unsure.
1. **Calculate.** Size **every** gated metric with the calculator and take the
   **largest**; that metric sets the runtime, and it is often the guardrail. Add
   any maturation window (for example +7 days for D7 retention) on top of
   accrual.
1. **Decision rule.** Pin ship, kill, and iterate, and that **inconclusive means
   block or keep running**: a null only reassures if the metric was powered. Name
   the sanity checks: sample-ratio mismatch, peeking approach, novelty window,
   multiple comparisons.
1. **Hand over** in three shapes (below), then offer the jarvis verification.
1. **Verify with jarvis (recommended).** Point the user at `/experiment-setup` in
   the shared DS repo `jarvis`. This plan pre-answers its intake, and it
   recomputes baselines and MDE from Snowflake with an independent pipeline.
   Record its Notion sizing URL in the plan. **If the numbers disagree
   materially, the warehouse wins**: update the plan. Without jarvis access,
   note "not verified" and move on.

## Calculator

```text
python scripts/power_calc.py size    --baseline <rate> --effect <change> [--power 0.9] [--one-sided] [--non-inferiority] [--arms N]
python scripts/power_calc.py size    --sd <stddev> --effect <change>          # continuous metric
python scripts/power_calc.py runtime --n-per-arm <n> --weekly-exposure <total/wk> [--arms N] [--maturation-days 7]
python scripts/power_calc.py table   --baseline <rate> --effects 0.01 0.02 0.03 --weekly-exposure <total/wk>
python scripts/power_calc.py power   --n-per-arm <n> --baseline <rate> --effect <mde>
```

`references/stats-methods.md` documents the formulas for anyone checking the work.

## Hand over

**Chat summary**, the same shape every run:

```text
**Pre-analysis: <experiment>**
Ready to launch when: <one line, or the gaps that block it>

| Role | Metric | Baseline (pulled <date>) | Target | Sets the clock? |
|---|---|---|---|---|

Clock: ~<N>/week on <proxy event>, a proxy for exposure until the exposure review.
Runtime: ~<N> weeks (<accrual> + <maturation>), set by <metric>.
Decision: ship if <…> · kill or iterate if <…> · inconclusive means <block / keep running>.
Still open: <gaps, each with an owner>
```

**Plan file**: fill `assets/pre-analysis-template.md` and hand it over as a
standalone markdown file named `<experiment>-pre-analysis.md`.

**Experiments DB entry update** (offered once, written only on a verbatim yes).
Fill only the fields the entry already has; never edit the template page:

- **Prediction**: "If we [change], then we expect [metric] for [audience] to
  [rise/fall] from [before] to [after] ([relative %])."
- **Experiment Design**: target audience, audience size, estimated duration
  (colored per the template: green up to 3 weeks, yellow 3 to 5, red 5 or
  more), baseline rate, significance, MDE, total sample size, duration.
- **Metrics tables**: primary and secondary rows with baseline and report link.

Guardrails, power, sidedness, and the decision rule have no field on the entry.
They stay in the plan file; link the file from the entry only if the user asks.

## Review

The conventions' silent review, plus:

- Re-run the numbers with `power_calc.py`; the plan must match, and the metric
  that sets the clock must be named.
- No missing baseline fed the sizing.
- Sidedness matches role; dials meet `references/defaults.md`; nothing loosened
  for a deadline.
- The decision rule is complete, including what inconclusive means.
- Every guardrail is powered at its sample target.
- The exposure assumptions name their source. The proxy event is named as a
  proxy, the user agreed to it, what it misses is written down, and the
  weekly volume was pulled on it with the baselines' eligibility filter.

## Team standards

If the experiment belongs to a team with a folder under `teams/`, read its
`overview.md`, `metrics.md`, and `learnings.md` to ground the plan: metric set,
where to pull baselines, past effect sizes for realistic targets. Only Activation
has a folder today. For any other team, say there are no team standards on file
yet and use the general method; never invent a team's metrics or OKRs.

## Never

- Invent a baseline, OKR, or past result.
- Loosen confidence or power for a deadline; widen the detectable effect.
- Gate a decision on secondary metrics.
- Interpret a running or finished experiment.
- Present the proxy event as the exposure event, or pick it without the
  user's agreement.
- Write to the DB entry without a verbatim yes, or edit the template page.
