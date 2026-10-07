# Activation — learnings

Two jobs: (1) tell you **where** past experiment knowledge lives so you can go
find it, and (2) hold a growing **digest** of takeaways — especially past effect
sizes, which are the best reality check for setting a realistic MDE.

Starting shape is **pointer-first**: the search playbook is the bulk today, and
the digest fills in over time as experiments conclude (each finished experiment
should add one card). This is easy to change if the team decides it wants a
heavier curated digest instead.

> Scaffold — fill the [brackets] with the team's real locations and results.

## Where to find past learnings

When someone needs prior results (to set an MDE, or to check "has this been
tried?"), look across these — formats vary, so search rather than expecting a
single source:

- **Amplitude** — [project/space name]; past experiments under [where]; naming
  convention \[e.g. `ACT-<date>-<slug>`\]. Look at the results/analysis tab for
  effect sizes actually observed.
- **Notion** — [workspace / database name and link]; filter/tag \[e.g. team =
  Activation, type = experiment\]. Post-analysis write-ups live [where].
- **Slack** — search channels \[#growth-activation, #experiments, #exp-results —
  TODO real names\]; useful terms: [metric name], "readout", "results", the
  experiment slug.
- **Post-analysis docs** — [where they're stored; format currently unknown].
  When you find one, extract: what changed, primary effect + rough CI, guardrail
  hits, and the takeaway — then add a card below.

## Digest — learning cards

Append one card per concluded experiment, newest first. Keep the fixed shape so
the digest stays scannable and so past effect sizes are easy to pull for MDE
realism.

```
### [Experiment name] — [YYYY-MM-DD] · [link]
- Change: [one line — what was different]
- Primary: [metric] → [effect seen, with rough CI or size]
- Guardrails: [any hits? or "all clear"]
- Takeaway: [what we concluded / would do differently]
- Tags: [surface], [lever]
```

<!-- Seed with any flagship results the team already knows by heart, e.g.:

### Onboarding checklist redesign — [date] · [link]
- Change: replaced 5-step wizard with a 3-step checklist
- Primary: activation rate → +1.8pp (95% CI ~ +0.9 to +2.7)
- Guardrails: D7 retention flat (within margin); error rate flat
- Takeaway: step reduction helps; ~2pp is a realistic ceiling for flow tweaks
- Tags: onboarding, friction
-->

## How this compounds

The pre-analysis doc this skill produces, plus the team's post-analysis docs,
are the natural feedstock for these cards. Standardizing those outputs means the
digest grows on its own instead of by heroic backfill — so the more the team uses
the skill, the better its MDE realism gets.

## Maintenance

- **Owner:** [TODO: whoever runs experiment readouts]
- **Cadence:** append a card whenever an experiment concludes.
- Revisit the pointer-first vs. curated-digest balance once there are enough
  cards to see what the team actually reaches for.
