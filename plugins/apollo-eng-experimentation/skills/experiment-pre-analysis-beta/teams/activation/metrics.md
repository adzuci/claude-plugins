# Activation — metric catalog

The canonical metrics for Activation experiments and, crucially, **where to pull
each baseline from**. Baselines are never stored here — only definitions, usual
roles, and the source of truth — so numbers are always pulled fresh at
pre-analysis time (see `references/data-sources/`).

Use this to propose the standard primary / secondary / guardrail set for an
Activation experiment, then confirm it fits the specific test before locking.

> Scaffold — fill the [brackets]. Don't invent metric names, event names, or
> baselines. If a row is still a placeholder, flag it and pull what you can.

## Catalog

| Metric | Plain definition | Usual role | Source of truth (where to pull) | Gotchas |
|---|---|---|---|---|
| [Activation rate] | [% of new users who reach the activation moment within N days] | Primary | \[Amplitude funnel `<exposure>`→`<activation event>`, or Snowflake `<table>`\] | [conversion window = N days; define eligible cohort] |
| [Time to activation] | [median hours from signup to activation] | Secondary | \[Snowflake `<table>`\] | [skewed — use median; needs per-user pull for SD] |
| [Feature/step adoption] | [% who complete key onboarding step] | Secondary | \[Amplitude event `<step event>`\] | [exploratory — don't gate on it] |
| [D7 retention] | [% active again 7 days after activation] | Guardrail | \[Snowflake `<table>` / Amplitude retention\] | [needs +7d maturation; low base rate → sizes the test] |
| [Core engagement] | [sessions or core actions per user, first week] | Guardrail | [Amplitude per-user chart; SD from Snowflake FCT_AMPLITUDE_EVENTS] | [continuous — pull per-user mean AND SD] |
| [Error / crash rate] | [% of sessions with an error] | Guardrail (operational) | \[Snowflake `<table>`\] | [watch for logging gaps] |

## Standard sets (starting point, confirm per experiment)

- **Primary:** [Activation rate] — the decision metric for most Activation tests.
- **Secondary:** [time to activation], [step adoption] — the mechanism story.
- **Guardrails:** [D7 retention], [core engagement], [error rate] — must not
  regress. For a broad/no-harm change, expect a guardrail (often D7 retention)
  to set the runtime.

## How to use with the calculator

For each gated metric, pull its baseline via the linked source, then size it:

```
python scripts/power_calc.py size --baseline <pulled rate> --effect <change>       # rate metrics
python scripts/power_calc.py size --sd <pulled sd> --effect <change>               # continuous metrics
```

Take the largest sample size across all gated metrics — that one sets the clock.

## Maintenance

- **Owner:** [TODO: Activation analytics partner]
- Update when a metric definition, event name, or source table changes.
- Never add a baseline number to this file — the "always pull fresh" rule is
  deliberate (see `references/defaults.md`).
