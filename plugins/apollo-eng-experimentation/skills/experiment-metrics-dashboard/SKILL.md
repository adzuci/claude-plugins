---
name: experiment-metrics-dashboard
description: Build an Amplitude dashboard that complements the standard experiment Analysis View, from an experiment name, branch, or PR.
disable-model-invocation: true
---

# Experiment Metrics Dashboard

Take an experiment name, branch, or PR for an experiment, understand what the change actually
does from the code, and build one consistent Amplitude dashboard that lets us see **everything
that is going on** with the feature — the behavioral questions the standard experiment Analysis
View can't answer.

**Example invocations:**

- `/apollo-eng-experimentation:experiment-metrics-dashboard https://github.com/apolloio/leadgenie/pull/123456` — a PR link/number.
- `/apollo-eng-experimentation:experiment-metrics-dashboard piotrp/my-experiment-branch` — a branch name.
- `/apollo-eng-experimentation:experiment-metrics-dashboard MonthlyRecapModalAt1k` — an experiment name (PascalCase key,
  `monthlyRecapModalAt1k` camelCase, or `monthly-recap-modal-at-1k` kebab key all work). Use this
  when the experiment is implemented across **multiple branches/PRs** — the skill unions them all.

This skill is direct-invocation only. Run it as a slash command with the target as the
argument; the skill detects which of the three input kinds it received (see Step 1).

**Where this fits in the standard experiment flow:**

1. Create experiment on **staging** (`168367`) — see `create-amplitude-experiment`.
1. Test it on staging.
1. **Copy the experiment to production** (`241072`).
1. **← This skill:** build the behavioral dashboard on **production** (`241072`).

So when this skill runs, the experiment already lives in prod with its live variants.

## Hard rule — complement, never duplicate

Amplitude's standard experiment **Analysis View** already provides: exposure/assignment
charts, cumulative exposures, confidence intervals, significance (p-value), lift, and
primary/secondary metric vs control. **Do not recreate any of those.** Every chart this
skill creates must answer a question the standard view cannot (funnel decomposition,
retention curves, pathing/adjacent behavior, adoption depth, guardrail diagnostics).
Reference: <https://amplitude.com/docs/feature-experiment/analysis-view>

The full canonical structure lives in `references/dashboard-template.md`. The metric
categories every dashboard must cover live in `references/metric-taxonomy.md`. Read both
before building.

## Step 0 — Preflight

Run both checks before Step 1. Stop on either failure rather than discovering it mid-run.

**Amplitude MCP.** Verify the Amplitude MCP is connected by calling `get_amplitude_context` (tool names carry a client-specific prefix — match on the suffix, and treat any available Amplitude tool as proof of a live connection). Capture the
project context (project IDs, available chart/dashboard tools). If the tool doesn't exist
or returns not-found, stop and tell the user:

> **Amplitude MCP is not connected.**
> Run `/mcp` in Claude Code and connect the Amplitude MCP server, then restart the skill.

**GitHub CLI.** Step 1 resolves the input through `gh pr diff`, `gh pr view`, and `gh pr list`, so an
unauthenticated `gh` fails at the first resolution attempt with an opaque error. Check it up front:

```bash
gh auth status
```

Non-zero exit means `gh` is missing or not logged in. Stop and tell the user:

> **GitHub CLI is not authenticated.**
> Run `gh auth login` (install `gh` first if the command is missing), then restart the skill.

## Step 1 — Resolve input → diff → experiment

**Input** is one of three kinds — a **GitHub PR link/number**, a **branch name**, or an
**experiment name** — and must work whether the PR is **not-yet-merged** or **already merged**.

**Detection ladder (run in this exact order — first match wins, except the collision rule):**

1. **PR** — input is a GitHub PR URL, `#N`, or a bare integer → **PR path** below.
1. **Experiment name** — input matches a registry entry in `assets/types/experiments.ts`
   (case-insensitive against: the `ExperimentNames` PascalCase key, its camelCase value, the
   `activeExperiments[*].key` kebab amplitude key, or a normalized human form with spaces/kebab/camel
   folded). On a **unique** match → **experiment-name path** below.
1. **Branch** — input resolves as a git ref (`git rev-parse --verify origin/<input>` or `<input>`),
   or matches a PR via `gh pr list --search "<input>"` → **branch path** below.

**Collision rule:** if the input matches BOTH a registry entry (2) AND a git ref (3), do **not**
guess — stop and ask the user whether they mean the experiment or the branch. If it matches none of
the three, ask the user to clarify or supply a PR link.

### PR path / branch path — resolve to a diff

- PR link/number → `gh pr diff <url-or-number>` (works for open and merged PRs). Use
  `gh pr view <url-or-number> --json title,headRefName,state,url,body` for title/branch/state
  and any Jira/Notion links in the body.
- Branch name that still exists → `git diff origin/master...<branch>`.
- Branch merged & deleted (no ref) → find its PR with
  `gh pr list --search "<branch>" --state all --json number,headRefName,title,url` then
  `gh pr diff <number>`. If a merge commit SHA is known, `git show <merge-sha>` as a
  fallback. If the branch can't be located, tell the user and ask for the PR link.
- If neither is given, fall back to the current branch / staged / unstaged changes per the
  CLAUDE.md review scope rules.

### Experiment-name path — resolve to the union of all referencing PRs

Use this when the detection ladder picked an experiment name. An experiment may be implemented
across **multiple branches/PRs**, so analyze the **union** of every PR that references it.

- **Resolve the experiment directly from the registry** (`assets/types/experiments.ts`): get
  `{ PascalKey, camelValue, key (amplitude kebab), variants }`. The experiment is already known up
  front, so **skip the diff→`ExperimentNames` detection block below** (that block only exists to
  recover the experiment from a single PR; here you have it already).
- **Find all referencing PRs (merged + open), deterministically:**
  ```
  gh pr list --search "ExperimentNames.<PascalKey>" --state all \
    --json number,headRefName,title,url,state,mergedAt
  ```
  If that returns nothing, retry the search with the camelCase value and the kebab key as fallback
  terms. **Sort the results by PR number ascending** for run-to-run repeatability. If no PR
  references the experiment, tell the user and ask for a PR link/branch.
- **Auto-union all** referencing PRs (do not prompt mid-resolution). For EACH PR, apply the
  full-fidelity pin technique below (fetch `pull/<n>/head`, diff against its merge base) and run
  every later grep (Step 2 emitted-slice / touched-surface / wrapper resolution) against **that PR's
  own head tree**. Then **union across PRs**: union of touched files, union of emitted event slices,
  union of touched-surface events (dedupe by ingested event name, keep the earliest `file:line`).
  Each grep stays pinned to a head tree (never `master`), so the per-PR determinism guarantee holds
  while coverage spans the whole experiment.
- **Carry the list of referencing PRs forward** — it must appear in the Step 3 review block and the
  Step 4 description-block `Source:` field (list all PRs/branches, not one).

**Get the diff at full fidelity, and pin all later greps to the PR-head tree.** `gh pr diff`
wraps long lines (so literal args like `action: 'viewed'` may not match a grep) and
`gh pr diff --patch` returns only the first commit on a multi-commit PR. Fetch the PR head ref
and diff against the merge base instead:

```
gh pr view <n> --json headRefOid,baseRefName
git fetch origin pull/<n>/head:pr<n>
git diff origin/<base>...pr<n>          # full-fidelity, all commits, unwrapped
```

**Pin rule (critical for repeatability):** every later grep in this skill — emitted-slice
detection (Step 2 success), touched-surface derivation, wrapper resolution — must run against
**the PR-head tree** (`git show pr<n>:<path>`), NOT current `master`. The skill answers "what
does *this* PR do"; later PRs may have added or removed call sites on `master`, which would
silently change the emitted-slice set and the chosen primary between runs. Always analyze the
PR-head tree. (When the input is a live branch, that branch tip is the head tree. For the
**experiment-name path**, this pin is applied **per referencing PR head tree** and the results are
unioned — the single-tree wording applies to PR/branch input.)

**Detect the experiment (PR/branch path only — skip for the experiment-name path, which already
resolved the experiment from the registry):** find `ExperimentNames.*` keys used or added in the
diff, then
cross-reference `assets/types/experiments.ts` `activeExperiments` to get `{ key, variants }`.
The `key` is an explicit kebab-case string literal set directly on each entry. If there are 0 or
more than 1 candidates, ask the user which
experiment this dashboard is for.

**Recover the live Amplitude flag** + experiment config id. This skill runs at the **last**
step of the standard flow (1. create experiment on staging → 2. test → 3. **copy experiment
to production** → 4. *this skill: build dashboard on production*), so the experiment must
already exist in **prod `241072`**. Search prod first. The live `search` tool wants `queries`
(an **array**), not a singular `query`; a bare `{ "query": "<key>" }` silently ignores
`entityTypes`/`appIds` and returns a stale generic list (50 CHART rows, all `score:0`,
`appId:0`). Use:

```json
{ "queries": ["<key>"], "entityTypes": ["EXPERIMENT"], "appIds": [241072] }
```

Pick the result whose key matches. Capture `flagId` and the config `id`/`experimentId` —
needed for variant segmentation and the prod Analysis View URL. **If `search` still returns
`appId:0` / `score:0` junk** (a known transient failure mode), retry the array form once; if it
persists, fall back to `get_experiments` with a known id, or ask the user for the config id /
Analysis View URL. **Do not fabricate** `flagId`/`experimentId`/start-date/`bucketingKey`, and
do not silently accept the today−30 start fallback when the real start date was merely
unreadable — say so and stop for the id rather than building a wrong-window dashboard.

**Derive the dashboard start date.** From the experiment config, read the experiment's
**start date** (the date the experiment was started/rolled out). If the config has no start
date set, default to **today**. The dashboard's time-window start date is then **that date
minus 30 days** — i.e. `(experiment start date | today) − 30 days`. This gives a 30-day
pre-period baseline before the experiment began. Use this computed date for the
"Start date" field of the description block and as the time-window start for every chart.

**Concluded / rolled-back experiment branch (deterministic window + label).** Read the config
`enabled` flag and `decision`/`endDate` fields:

- If `enabled:false` **or** a `decision` is set (e.g. `rollback`, `ship`) **or** an end date
  exists → the experiment is **concluded**. The dashboard is **retrospective**:
  - Time window for every chart is **fixed**: `[start − 30d, experiment end date]` — do NOT use
    `now` (the experiment is no longer collecting; an open-ended window adds dead time and makes
    runs differ by when they execute). End date = config end date, else the `decision` date.
  - Append `(retrospective)` to the dashboard title alongside the date/PR discriminator.
  - State the conclusion (`decision` + reason) in the description block.
- If `enabled:true` and no decision/end date → **live**: window is `[start − 30d, now]`.

**New-event / new-slice pre-period caveat (prevents misreads).** The `start − 30d` baseline is
only meaningful for events that existed before rollout — i.e. the **guardrails** (touched-surface

- business). For a **new-event or new-slice experiment** (single-event/new-slice rule fired in
  Step 2), the success event/property value did not exist before the start date, so the 30-day
  pre-period is **flat zero for the success charts (§1–§3) by construction** — that is expected,
  NOT a drop/regression. State this in the description block; treat §1–§3 as baselining from the
  rollout date; the pre-period only carries signal for §5 guardrails. Do not let a reviewer read
  the empty pre-period as a negative result.

**Guard — experiment not yet in prod:** if the experiment is found only in staging `168367`
(or not at all in `241072`), stop and tell the user:

> The experiment `<key>` isn't in the production project (`241072`) yet — only staging.
> Per the standard flow, copy the experiment to production first (step 3), then re-run this
> skill. The dashboard must be built in prod so charts can segment by the live variants.

Do not build a staging dashboard or a prod dashboard without variant segmentation.

## Step 2 — Analyze the diff for the behavioral flow + candidate metrics

All greps in this step run against the **PR-head tree** (see Step 1 pin rule).

**Reconstruct the feature flow** (this drives the funnel + pathing charts): from the diff,
identify the ordered set of analytics events the change fires across the touched components.

- Frontend: grep the touched files for `zenalytics.track('<Event>'`, `sharedZenalytics`,
  `zenalytics.throttle(` under `assets/`, `packages/`.
- Backend: grep for `Zenalytics.track`, `sync_track`, `event_type:` under `packs/`, `app/`.
- **Indirect / wrapper tracking (mandatory — do not stop at literal `zenalytics.track`).** Many
  surfaces fire events through helper wrappers, not inline `zenalytics.track`. A diff can fire
  events while containing **zero** literal `zenalytics.track` calls. Also grep the touched files
  for wrapper patterns: `track[A-Z]\w*(`, `useTrack\w*(`, `\w*Analytics\.track\w*(` (e.g.
  `trackFeatureGateActionClicked(`, `useTrackFeatureGateShown(`, `createUpgradeTracker(`,
  `trackExtensionRecordSaved(`, `ProspectingAnalytics.trackCopyEmailEvent(`). For each wrapper
  hit, open the wrapper's definition and resolve it down to the underlying
  `zenalytics.track('<Event>')` literal(s) to recover the real **ingested** event name(s) and
  the property values passed. Treat wrapper-fired events identically to inline ones for both
  success-candidate and touched-surface derivation. Skipping wrappers is the single biggest
  source of "wrong/empty" dashboards (e.g. feature-gate experiments fire entirely via
  `featureGateTracker.ts`).
- Note new event **properties / property values** added by the diff (a change may add only a new
  **value** — e.g. `feature_gate_type='monthly_recap'` — to a pre-existing event; that new slice
  is the experiment's signal, see the single-event/new-slice rule below). Cross-ref
  `shared/configs/always_tracked_events.yml` to flag whitelisted (tracked for free users) vs
  paid-only events — a success metric on a non-whitelisted event under-counts free users.

**Success candidates (propose to user):** the primary action event closest to the experiment's
intended behavior change, plus meaningful secondary actions on the same flow. **If the new
behavioral signal is carried by one event** — either the diff adds exactly one new event, OR it
adds no new event but adds a distinguishing new property value/slice to a pre-existing event
(e.g. `feature_gate_type='monthly_recap'`) — apply the deterministic single-event / new-slice
rule in `references/metric-taxonomy.md` (primary = deepest-intent **emitted** slice; secondaries
= the event's other emitted slices) — do not invent separate events.

**Three deterministic auto-add patterns (see `references/metric-taxonomy.md`)** — include each
only when its trigger is actually present in the diff/flow, never fabricated:

- **Urgency / time-remaining breakdown** — if the primary event emits a countdown property
  (`*_days_remaining`, `*_until_*`, `*_remaining`), add a secondary breaking it down by fixed
  deterministic buckets (→ §4).
- **Time-to-conversion** — if the **experiment key or stated goal contains a monetization token**
  (`trial`/`upgrade`/`convert`/`conversion`/`paid`/`checkout`/`subscription`/`subscribe`/`plan`/`billing`/`monetiz`/`arr`/`seat`), add
  a time-to-convert distribution chart (primary action → nearest free→paid guardrail) with the
  experiment's natural conversion window (→ §2). Token match only — no flow-reachability guess.
- **Bridge metric** — the intermediate product behavior between the primary action and the nearest
  conversion guardrail, drawn **only** from the bounded touched-surface set (the same set §5
  derives — do not widen to `actions/*` or other "adjacent" events); if several qualify, pick the
  one nearest the primary by `file:line`/flow order; if none, omit (→ §4).

**Guardrails (auto-derive, 2 categories — see `references/metric-taxonomy.md`):**

1. **Touched-surface events** — existing tracking events already fired in the files/components
   the diff modifies. The change must not suppress or drop these.
   **Deterministic derivation (no improvisation):**
   1. Grep every touched file (PR-head tree) for the literal patterns (`zenalytics.track('<Event>'`
      / `sharedZenalytics` / `zenalytics.throttle(` frontend; `Zenalytics.track` / `sync_track` /
      `event_type:` backend) **and the wrapper patterns** (`track[A-Z]\w*(`, `useTrack\w*(`,
      `\w*Analytics\.track\w*(`), resolving each wrapper to its underlying
      `zenalytics.track('<Event>')` event name. **Count only PRE-EXISTING events: exclude any
      event the diff adds (literal or wrapper track call on a `+`/added line).** The change's own
      new success event must never count as a step-1 hit — otherwise it falsely blocks widening.
   1. **If step 1 yields zero pre-existing events** (common when the change only adds render
      markup / props and fires no inline tracking), widen by a **fixed, bounded scope**: the
      touched files **plus their direct sibling files in the same directory (non-recursive)**.
      Grep those siblings for the same literal + wrapper patterns. The union is the touched-surface
      set. Do NOT recurse into subdirectories and do NOT hand-pick "adjacent" events from
      intuition — same-directory siblings (non-recursive) is the only allowed widening scope, so
      two runs produce the same bounded set even when a touched file lives at the top of a large
      directory tree.
   1. Sort the events by `file:line` ascending and dedupe by ingested event name. Resolve each
      against prod `241072` with `get_events`. **Drop only events that are NOT `isQueryable` —
      `queryable` is the sole gate.** KEEP events that are `isQueryable:true` even if
      `isActive:false` (Amplitude charts inactive-but-queryable events historically; this matters
      for retrospective windows that predate a deactivation) — just annotate them "(inactive)".
      Do NOT relevance-trim the survivors.
      This guarantees run-to-run repeatability whether or not the modified files track inline.
1. **Standard business guardrails** — the fixed always-on list: activation, free→paid conversion,
   churn/retention, revenue funnel.

## Step 3 — Confirm the FULL analysis (BLOCKING gate — lock before building)

**Hard rule: do NOT call any `create_*` / `edit_*` / `replace_*` / `create_metric` MCP tool
until the user has explicitly approved the analysis below.** All of Steps 1–2 are AI-derived and
*will* contain wrong picks on some PRs (wrong primary slice, an over-broad or empty touched-surface
set, a dead/empty property slice, a misread bucketing unit). Building a dashboard straight from the
un-reviewed analysis produces garbage charts. The user must see the complete analysis and sign off
first.

Present the entire resolved analysis as ONE review block, then stop and wait:

1. **Experiment**: key, flagId/experimentId, variants, bucketingKey + resulting counting unit
   (team vs user), live/concluded + the computed time window (with the math). **If the
   experiment-name path was used, also list the referencing PRs/branches that were unioned**
   (number + title + state) so the user can confirm the right set was found.
1. **Success metrics**: the proposed **primary** (event + exact property slice + why) and
   **secondary** slices — each with its source `file:line` and whether it actually emits data
   (flag dead/empty slices explicitly). Include any triggered auto-add patterns (urgency/
   time-remaining breakdown, time-to-conversion, bridge metric) and state which trigger fired.
1. **Touched-surface guardrails**: the derived set, noting which were kept/dropped and any
   `(inactive)` ones, with `file:line`.
1. **Business guardrails**: the fixed 9 (for awareness — not up for selection).
1. **Proposed charts**: the full §1–§5 list (section → chart type → event → title) that WOULD be
   created.

Then ask the user to **confirm or edit**: they may change the primary, add/drop secondaries, drop
touched-surface events, or correct the window/unit. Primary is required; secondary optional. The
business guardrails (9) are always included — show them but don't ask. Apply any edits, **re-print
the final locked selection**, and only then proceed to Step 4. If the user hasn't responded, do not
build.

(If invoked in a non-interactive/headless context where no user can answer, do NOT create the
dashboard — emit the spec via the Step 4 Fallback and say it needs review before building.)

## Step 4 — Build the unified complementary dashboard via Amplitude MCP

**Precondition: the user approved the Step 3 review gate.** If they did not, stop — do not call
any create/edit MCP tool.

Render strictly from `references/dashboard-template.md`. Build in **production project `241072`** —
real-user behavior lives in prod.

**Always create a NEW dashboard — never modify an existing one.** Before creating, `search` prod
for an existing dashboard for this experiment/PR/feature (by key/name). If one exists, do **not**
edit it: create a fresh dashboard and disambiguate the title (e.g. append the date or PR number,
`… — Behavioral Dashboard (2026-06-23)`). Tell the user the prior dashboard(s) were left untouched
and link them. `edit_dashboard`/`replace_dashboard_properties` are only for laying out the new
dashboard you just created, never an existing one.

- **Description block** (fixed format from the template): experiment name, Amplitude key,
  hypothesis, owning team, variants, the feature flow (event sequence), start date, links, and the
  one-line "complements the standard Analysis View by covering …". The `Source:` field is the branch
  or PR link — for experiment-name input, list **all** the unioned PRs/branches, not one. For
  new-event/new-slice experiments, state the flat-zero pre-period caveat.
- **Segmenting by variant — always exclude the unenrolled `(none)` group.** Group every chart by
  the experiment property `gp:[Experiment] <key>`, AND add a population `segment` restricting it to
  the real variant values, e.g. `op:"is", values:["control","treatment"]` (equivalently exclude
  `"(none)"`). The group-by alone leaves a giant `(none)` series that dwarfs the variants — the
  segment filter is mandatory. Apply to all chart types (segmentation, funnel, retention).
- **Counting unit must match the experiment's `bucketingKey`.** If `bucketingKey: group_name`
  (team/account-bucketed — the common case), count every chart by **team (group)**, not user; set
  the aggregation/counting unit to the group and read uniques/retention as unique teams. Per-user
  counts on a team-bucketed experiment mis-weight large teams. Only count per user when
  `bucketingKey` is user/device.
- **Sections in fixed order, every chart segmented by variant** (using the resolved key/variants):
  1. Feature adoption / engagement depth
  1. Funnel decomposition (from the Step-2 event sequence)
  1. Retention curves
  1. Pathing / adjacent behavior
  1. Guardrail diagnostics (touched-surface events + business guardrails)
- Create the charts and the dashboard via the Amplitude MCP: build/verify chart definitions with
  `verify_chart_definition` + `get_chart_definition_params`, persist with `create_dashboard` (and
  `edit_dashboard` / `replace_dashboard_properties` to lay out sections), `create_metric` for
  guardrail metrics, and `query_chart` to sanity-check data. Search existing charts with `search`
  before creating duplicates.
- **Never guess event names.** Resolve every event against prod `241072` with `get_events` (use the
  exact **ingested** `event_type`, not the display name) and confirm properties with
  `get_properties` before putting an event in a chart definition. The guardrail events are
  pre-resolved in `references/metric-taxonomy.md`.
- **Fallback:** if a needed chart/dashboard creation capability is missing from the MCP, emit the
  complete dashboard spec (every chart's type/events/segmentation/window) plus manual build steps so
  the user can create it in the Amplitude UI.

## Step 5 — Output summary

Print:

- Dashboard URL (prod project `241072`) and the linked experiment Analysis View URL.
- A metric table: **section → metric → behavioral question it answers → source `file:line`** in the
  diff.
- Any manual steps (e.g. fallback chart creation, or properties that need defining in Amplitude).

## Reuse (don't reinvent)

- `assets/types/experiments.ts` — `ExperimentNames`, `activeExperiments` (each entry's `key` is an explicit kebab-case literal).
- `shared/configs/always_tracked_events.yml` — whitelisted-event cross-check.
- `assets/common/lib/zenalytics.ts` / `packs/iam/lib/zenalytics.rb` — event call patterns.
- `../create-amplitude-experiment/SKILL.md` — MCP patterns (`get_amplitude_context`, `search_amp_entities`),
  URL shape. (That skill uses staging `168367`; this dashboard uses prod `241072`.)
