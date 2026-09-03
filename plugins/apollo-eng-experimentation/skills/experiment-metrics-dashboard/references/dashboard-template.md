# Canonical Experiment Dashboard Template

This is the unification artifact. Every experiment dashboard this skill builds uses the
**same description block, the same five sections in the same order, and the same per-chart
spec**, so all experiment dashboards read identically. Do not add, reorder, or rename
sections per experiment — only the events/metrics inside them change.

All charts are built in **Amplitude production project `241072`** and **grouped/segmented by
the experiment variant** (`control`, `treatment`, …) using the resolved experiment key.

______________________________________________________________________

## Do NOT duplicate the standard Analysis View

These already exist on every Amplitude experiment and must NOT be recreated here:

- Exposure / assignment charts, cumulative exposures
- Confidence intervals, significance / p-value
- Lift / relative performance
- Primary & secondary metric vs control stat tables
- Winsorization stats

This dashboard exists to answer what those cannot. Reference:
<https://amplitude.com/docs/feature-experiment/analysis-view>

______________________________________________________________________

## Description block (top of dashboard, fixed fields and order)

Title disambiguation: always a NEW dashboard — never overwrite an existing one. If a
dashboard for this experiment/PR/feature already exists, append a discriminator
(`(YYYY-MM-DD)` or `(PR #NNNNN)`); add `(retrospective)` for concluded experiments.

```
# <Experiment human name> — Behavioral Dashboard [(YYYY-MM-DD or PR #) (retrospective)]

Complements the standard Amplitude Analysis View by covering: adoption depth, funnel
decomposition, retention curves, pathing/adjacent behavior, and guardrail diagnostics.

- Amplitude key: <key>
- Experiment / Analysis View: <experiment URL>
- Owning team: <team>
- Variants: <control, treatment, …>
- Hypothesis: <one line>
- Feature flow (event sequence): <Event A → Event B → Event C>
- Start date: <YYYY-MM-DD>  # (experiment start date | today) − 30 days; see SKILL.md Step 1
- Conclusion: <decision + reason, for concluded/rolled-back experiments; else "live">
- Pre-period note: <for new-event/new-slice experiments: §1–§3 pre-period is flat-zero by
  construction; pre-period signal applies only to §5 guardrails>
- Links: <Jira> · <Notion> · <Design>
- Source: <branch or PR link; for experiment-name input, list ALL unioned PRs/branches>
```

______________________________________________________________________

## Sections (fixed order)

### 1. Feature adoption / engagement depth

**Gap filled:** standard view gives "% converted"; it does not show how *much* or how *often*.
**Charts (segment by variant):**

- Event frequency per unit (avg / distribution) for the primary action event.
- Volume of the primary action over time (daily/weekly).
- Active units performing the action (uniques) over time.

### 2. Funnel decomposition

**Gap filled:** standard view has no step-by-step funnel / abandonment view.
**Charts (segment by variant):**

- Funnel built from the reconstructed feature flow (ordered events from Step 2).
- Step-to-step conversion + drop-off at each step.
- **Time-to-conversion distribution** (auto-add when the experiment key OR stated goal contains a
  monetization token — `trial`/`upgrade`/`convert`/`conversion`/`paid`/`checkout`/`subscription`/
  `subscribe`/`plan`/`billing`/`monetiz`/`arr`/`seat`; token match only, no flow-reachability guess
  — see metric-taxonomy "Time-to-conversion"): elapsed time from the primary action (or exposure) to
  the nearest free→paid conversion event. Conversion window = the experiment's natural horizon (e.g.
  trial length), not a fixed calendar window. Tests acceleration, not just rate lift.

### 3. Retention curves

**Gap filled:** standard view gives a single retention number, not a curve.
**Charts (segment by variant):**

- N-day retention *curve* of the primary action event (e.g. days 0–14/30).
- Optionally unbounded retention for the core feature behavior.

### 4. Pathing / adjacent behavior

**Gap filled:** standard view shows no user pathing or downstream/secondary feature usage.
**Charts (segment by variant):**

- Pathfinder/journey: what users do immediately before and after the experiment action.
- Usage of adjacent/downstream features the change could shift (from the success secondary
  events + touched-surface events).
- **Bridge metric** (auto-add when one exists — see metric-taxonomy "Bridge metric"): the
  intermediate product behavior between the primary engagement action and the nearest conversion
  guardrail (e.g. *advanced-filter-applied* between badge-viewed and checkout). Distinguishes
  "feature noticed" from "feature used → led toward conversion."
- **Urgency / time-remaining breakdown** (auto-add when the primary event emits a countdown
  property — see metric-taxonomy "Urgency / time-remaining property breakdown"): the primary action
  bucketed by the emitted `*_remaining` / `*_until_*` property (fixed deterministic buckets). Shows
  whether behavior intensifies as the deadline window closes.

### 5. Guardrail diagnostics

**Gap filled:** behavioral read on whether the change suppressed an existing path (beyond
the stat guardrails on the Analysis View).
**Charts (segment by variant):**

- Trend of each **touched-surface event** (auto-derived) — watch for drops vs control.
- The fixed **business guardrails**: activation, free→paid conversion, churn/retention,
  revenue funnel.
- Annotate each guardrail chart with the expected "must not regress vs control" threshold.

______________________________________________________________________

## Per-chart spec (apply to every chart)

| Field | Value |
|-------|-------|
| Project | Production `241072` |
| Segment / group-by | Group by experiment property `gp:[Experiment] <key>` **and** add a population segment restricting to real variants (`op:"is", values:["control","treatment"]`, i.e. exclude the unenrolled `(none)` group). Group-by alone leaves a giant `(none)` series that dwarfs the variants — the segment filter is mandatory. |
| Counting unit (bucketing) | **Match the experiment's `bucketingKey`.** If `bucketingKey: group_name` (team/account-level — the common case), the experiment property is a **group property** and every chart must count by **team (group)**, not user: set the counting/aggregation unit to the group, segment by the group experiment property, and read "uniques"/retention as unique **teams**. Per-user counts on a team-bucketed experiment mis-weight large teams. Only count per user when `bucketingKey` is user/device. |
| Chart type | Section-appropriate: event segmentation (§1, §5), funnel (§2), retention curve (§3), pathfinder/journey (§4) |
| Time window | Live experiment: dashboard start date → now. Concluded/rolled-back: `[start, experiment end date]` (see SKILL.md Step 1 concluded branch). Start = `(experiment start date or today) − 30 days`; retention uses a fixed N-day window. **New-event/new-slice experiments:** the `−30d` pre-period is flat-zero for success charts (§1–§3) by construction (the event/slice didn't exist pre-rollout) — expected, not a drop; pre-period signal applies only to §5 guardrails. |
| Population | Exposed teams (team-bucketed) / exposed users (user-bucketed), matching the counting unit above |
| Annotation | For guardrails, note the regression threshold vs control |

Before creating any chart, `search_amp_entities` for an existing chart with the same
name/definition to avoid duplicates.
