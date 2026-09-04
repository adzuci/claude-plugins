---
name: product-gap-measurement
description: Plans and reviews measurement for product gap work across ticket analysis, PR review, and post-merge impact tracking.
disable-model-invocation: true
---

# Product Gap Measurement

Use this skill to plan or review measurement for product gap work across the PR lifecycle. The goal is to connect product telemetry, support demand, and qualitative conversation proof without overclaiming causality.

## Usage

```text
/apollo-eng:product-gap-measurement pre-ticket AITR-79
/apollo-eng:product-gap-measurement pre-merge https://github.com/apolloio/leadgenie/pull/95135
/apollo-eng:product-gap-measurement post-merge https://github.com/apolloio/leadgenie/pull/93453
```

If the user omits a mode, infer it from input state:

- Merged PR or shipped fix -> `post-merge`
- Open, unmerged GitHub PR -> `pre-merge`
- Jira, Vertical Agent story, Notion support-rotation idea, or support topic -> `pre-ticket`

## Connectors

This skill uses the Amplitude and Enterpret MCP connectors (Intercom optional). If a
required connector's MCP tools are unavailable or error out, read and share
`references/connector-setup.md` with the user, then continue once connectors respond
(or with pasted data).

Pre-Ticket Mode can optionally use the local Glean CLI (not the Glean MCP connector) for
internal-doc context. See `references/glean-context-lookup.md`.

## Workflow Contract

Always:

- Step 1: Pin the source of truth: PR, Jira, Vertical Agent story, dashboard, or support topic.
- Step 2: Name the product gap in one sentence.
- Step 3: Classify pain timing:
  - `immediate`: support click window likely valid.
  - `delayed`: support click window likely noisy.
  - `hybrid`: delayed problem, immediate UI exposure.
- Step 4: Choose the measurement model:
  - Enterpret sizes support severity: volume, themes, representative conversations, and urgency.
  - Amplitude sizes product exposure and behavior: affected surfaces, journey steps, recovery actions, support intent, and downstream actions.
  - Intercom provides exact conversation links when direct review or user follow-up matters.
- Step 5: Label proof level:
  - `code-backed`: event or behavior exists only in code.
  - `taxonomy-backed`: event exists in Amplitude taxonomy.
  - `live-count-backed`: event has observed production counts.
  - `support-severity-backed`: Enterpret shows topic volume, themes, or representative support records.
  - `product-exposure-backed`: Amplitude shows users reached the affected product surface or journey.
  - `behavior-baseline-backed`: Amplitude shows pre-fix behavior to compare after the fix.
  - `support-reduction-backed`: a post-fix Enterpret or Intercom trend shows reduced support demand.
  - `Intercom-backed`: exact conversation was fetched or linked.
  - `directional-only`: evidence is plausible but not joined end to end.
  - `exact-click-to-ticket`: converted users are joined to support conversations.
- Step 6: State claim boundary: what can be claimed and what cannot be claimed.

## Common Signals

Use these defaults unless the repo, PR, or dashboard proves a better signal:

- Amplitude project: `241072`.
- Support intent: `Contextual Sidebar Event` filtered to `type = click`, `cta = Talk to support`, `resourceType = intercom`.
- Segment by `gp:tier` when available. If `gp:plan`, role, or tenure is missing, say so and use the closest available segment.
- Prefer unique users for exposure denominators.
- If UI gives the user a recovery link, button, or task, require a tracked recovery action. Support clicks alone are not enough.
- For Intercom review links, use Enterpret `origin_record_id` as the conversation id when available:

```text
https://app.intercom.com/a/inbox/dyws6i9m/inbox/view/299248/conversation/{origin_record_id}?view=List
```

## Enterpret Query Execution

When running Enterpret queries, read `references/enterpret-query-guide.md` first.

## Pre-Ticket Mode

Use when product gap is still being scoped from Jira, Vertical Agent, Notion support-rotation idea, support topic, or conversation examples. If input is raw ideation, first answer whether the gap is real and worth sizing before writing ticket acceptance criteria.

Required checks:

- Step 1: Optionally check Glean for prior internal context (PRDs, tickets, threads) before sizing fresh. Read `references/glean-context-lookup.md`. Best-effort only — never block sizing if Glean is unavailable or unauthenticated.
- Step 2: Start with Enterpret to size support severity:
  - Query the narrow support topic first, then compare with a broader query only to detect nearby themes.
  - Return volume, trend window, top themes, severity language, and representative records.
  - Call out when the query is noisy, sales-call-heavy, or not specific enough for sizing.
- Step 3: Use Amplitude to understand product exposure:
  - Find the exposed cohort, affected surface, journey steps, recovery actions, support intent, and downstream business actions.
  - Prefer unique users for denominators and segment by `gp:tier`, `gp:plan`, role, or closest available property.
  - If the product gap is agent-mediated or lacks clean events, say Amplitude is an instrumentation gap instead of forcing a weak funnel.
- Step 4: Do not frame Amplitude as primary proof of support-ticket reduction for pre-ticket work. Use it to show exposed users, UI behavior, and where the product should be changed.

Answer with:

```md
## Product Gap
## Prior Internal Context (Glean)
## Pain Timing
## Enterpret Severity
## Amplitude Exposure / Journey
## Measurement Strategy
## Instrumentation Needed
## Recommended Ticket Acceptance Criteria
## Claim Boundary
## Next Step
```

Omit `## Prior Internal Context (Glean)` when Glean is unavailable, unauthenticated, or
returns nothing relevant.

Focus on:

- Is this a real product gap or a support/process issue?
- Is the support topic narrow enough, or too broad to measure?
- What exposure denominator should exist?
- What recovery action should be tracked?
- What should the ticket require before the fix ships?

## Pre-Merge PR Review Mode

Use when a GitHub PR exists before merge.

Required checks:

- Read the PR body and diff.
- Find added tracking calls or dashboard links.
- Check whether an exposure event exists.
- Check whether the recovery action is tracked.
- Check whether `Talk to Support` is a valid early signal for this pain timing.
- Check whether the PR includes a post-deploy dashboard/readout plan.
- Warn when the support topic is too broad for a clean readout.

Answer with:

```md
## Verdict
## Existing Measurement
## Missing Measurement
## Recommended Events
## Dashboard Plan
## PR Body Snippet
## Claim Boundary
```

For PR review, include copy the author can paste into the PR. If the PR already tracks exposure but not recovery action, recommend the smallest event addition rather than broad instrumentation.

## Post-Merge Mode

Use when a fix has shipped or merged and the user wants a dashboard, readout, or proof of impact.

Required checks:

- Confirm expected events are queryable in Amplitude before counting.
- Query exposure and recovery-action counts when live.
- Segment by `gp:tier` when available.
- Use support-click funnel only when pain timing makes the window meaningful.
- Use Enterpret for topic trend and candidate conversations.
- Generate Intercom review links for a small, relevant conversation set.
- Treat sparse, zero, or unjoined results as inconclusive, not proof of no issue.

Answer with:

```md
## Verdict
## Live Amplitude Counts
## Support Signal
## Intercom Review Links
## Dashboard / Readout
## Next Check
```

Do not create dashboards automatically unless the user explicitly asks. When creating dashboards, use saved charts, not temporary edit ids.

## Canonical Examples

Read `references/impact-sizing-examples.md` for reusable examples, including the trial-credits Notion idea, immediate support-click cases, hybrid exposure cases, and delayed support-trend cases.

## Output Rules

- Keep output practical and PR-ready.
- Lead with verdict and evidence gaps.
- Prefer narrow, existing events over new broad tracking.
- Separate Amplitude behavior signal from Enterpret/Intercom support proof.
- Never claim exact click-to-ticket proof unless converted users are joined to Intercom conversations.
- Glean (when used) surfaces internal discussion, not measurement evidence — never substitute it for Amplitude/Enterpret proof.
