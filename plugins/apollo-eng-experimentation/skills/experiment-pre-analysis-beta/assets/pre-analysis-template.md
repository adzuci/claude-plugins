# Pre-Analysis — {{experiment_name}}

<!--
Fill every {{placeholder}}; delete rows that don't apply. Sections 1–3 and 7 are
for any reader. Plain words throughout: no grades, codes, or internal labels.
Provenance and exact queries go in "How this was checked" at the end so the plan
is reproducible. Plain markdown, so it imports cleanly into Notion or a ticket.
-->

## 1. What we're testing

**The change:** {{one or two plain sentences}}

**Hypothesis:** We think {{change}} will move {{metric}} because {{reason}}.

**Experiment type:** {{standard A/B | no-harm | multivariant | learning}}

## 2. The decision

Agreed before launch:

- **Ship if:** {{condition}}
- **Kill or iterate if:** {{condition}}
- **Inconclusive means:** {{block / keep running; for a no-harm test never "ship"}}

## 3. Audience and exposure

- **Who's eligible:** {{eligibility}}
- **Exposure moment:** {{plain words: when an eligible user counts as exposed}}
- **Proxy event for volume:** {{existing event used until the real exposure
  event exists, and what it misses}}
- **Population:** {{new teams only | all teams | other}}
- **Expected exposure:** {{N}} per week across all arms, on the proxy event
- **Arms and split:** {{e.g. 2 arms, 50/50}}

## 4. Metrics

| Role | Metric | Baseline (pulled {{date}}) | How solid is the baseline | Guardrail tolerance |
|---|---|---|---|---|
| Primary | {{metric}} | {{rate or mean ± sd}} | {{exact pull on the eligible population / proxy: assumption / still missing}} | — |
| Secondary | {{metric}} | {{baseline}} | {{…}} | — (explanatory, not gated) |
| Guardrail | {{metric}} | {{baseline}} | {{…}} | max {{drop}} |

A missing baseline must be resolved before launch; it was not used for sizing.

## 5. Targets and risk settings

| Metric | Effect to detect or max drop | Confidence | Power | Direction | In plain terms |
|---|---|---|---|---|---|
| {{primary}} | detect {{+X% relative}} | 95% | 80% | either way | {{"we'll reliably spot a change of at least X in either direction"}} |
| {{guardrail}} | rule out a drop over {{X}} | 95% | 90% | drop only | {{"we'll confidently catch it if this drops by more than X"}} |

## 6. Sample size and runtime

{{Paste the sensitivity table from power_calc.py here.}}

- **Metric that sets the clock:** {{which needs the most data, and why}}
- **Required sample:** {{n}} per arm ({{total}} total)
- **Estimated runtime:** {{weeks}} accrual {{+ maturation}} = **~{{total}} weeks**

## 7. Decision rule

- **Ship:** {{primary condition}} and every guardrail clears its bar.
- **Ship and celebrate:** additionally, {{primary shows a real lift}}.
- **Block or iterate:** any guardrail fails, or the primary shows a real drop.
- **Inconclusive → {{block / keep running}}:** "we couldn't rule out harm" is not
  "no harm."

## 8. Sanity checks planned

- **Split check:** compare the observed split to the intended one on day one.
- **Peeking:** {{"Amplitude sequential, safe to monitor" | "fixed horizon, read at
  the planned end"}}
- **Novelty:** {{how the effect over time will be inspected}}
- **Multiple comparisons:** {{"single primary, protected" | "Bonferroni across
  arms"}}

## 9. Independent verification (jarvis)

- **Sizing doc:** {{Notion "Exposure Sizing & MDE" URL, or "not run"}}
- **Reconciliation:** {{numbers agree | disagreed on {{what}}; the warehouse
  wins and this plan was updated {{date}}}}

<details>
<summary>How this was checked</summary>

- **Prior artifacts used:** {{exposure-design hand-over / ERD / PRD / DB entry, or
  "none"}}
- **Replaces:** {{prior plan and date, or "first version"}}
- **Parameters:** confidence {{}} · power {{}} · direction {{}} · arms {{}} ·
  correction {{}} · MDE or margin per metric {{}}
- **Assumptions:** {{clustering, seasonality, variance reduction, …}}
- **Baseline queries** (source and query per metric):

```text
{{query for metric 1}}
```

```text
{{query for metric 2}}
```

- **Calculator commands:**

```text
{{the power_calc.py commands run}}
```

</details>
