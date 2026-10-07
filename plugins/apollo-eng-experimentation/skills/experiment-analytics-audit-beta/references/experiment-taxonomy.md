# Experiment event taxonomy

Derived 2026-10-05 from the two prior analytics audits — the
[SSO Analytics Audit](https://app.notion.com/p/apolloio/SSO-Analytics-Audit-3d0ab2b3b49680f6a1dcc52b2e9326b3)
(Saved Search Overhaul) and
[AI Onboarding Analytics Tracking](https://app.notion.com/p/apolloio/AI-Onboarding-Analytics-Tracking-366ab2b3b49681d78bfdd46ffa9e4c64).
Everything here is a **proposal pattern** the audit recommends and DS confirms;
this skill never decides taxonomy.

## Event shape: one consolidated event over many micro-events

Both audits converged on a small number of events read through discriminator
properties, instead of an event per interaction:

- SSO: one `Saved Search Action` event answering four questions —
  **what** (`action_name`), **how** (`interaction_type`), **where** (`surface`),
  **which arm** (`experiment_variant`).
- AI Onboarding: one `AI Onboarding Actioned` event with an `action`
  discriminator and a `Surface` grouping, plus Amplitude taxonomy properties
  `kingdom` / `phylum` (e.g. `Product Growth` / `Activation`).

Recommend the consolidated shape for a new experiment's events unless the team
has a standing per-event convention on that surface.

## Intent vs. outcome

SSO's reading rule generalizes: `menu_open` / `click` / `menu_item_click`
values are **intent**; a `flow_outcome` value with an `outcome` property is
**success**. Failures are not events (they go to Sentry) — a click with no
following `flow_outcome` means cancel/abandon/error. When proposing new events,
keep intent and outcome distinguishable; a funnel needs both ends.

## Experiment-scoped properties

**Current minimum, on the exposure event:** `experiment_key` (the flag key),
`variant`, and `groups` (`account_id` → team). This is what Amplitude's
`$exposure` relay sends today.

**Observed on metric events:**

- SSO stamped `experiment_variant` on every `Saved Search Action` (client-side)
  and `experiment_name` + `experiment_variant` on the backend
  `Saved Search Alert Sent` (server-side, cache-only — a `null` variant means a
  cold assignment cache and shrinks over time, not a bug).
- AI Onboarding did not stamp variant on downstream events; analysis relied on
  exposure-based segmentation.

**Open question for DS (capture it in every audit's open-questions section
until DS answers it globally):** should `variant` be stamped on *all* downstream
events, or only on the exposure event plus the primary-metric action event? The
latter is enough for a client-vs-server assignment consistency check without
creating a second source of truth for who is in which arm. Record whichever DS
decides for this experiment in the affected events' Properties column.

## Segment-cut properties

Whatever segment cuts pre-analysis declared (team segment, plan, …) must arrive
on the events that compute the sliced metrics — check them per event in Stage A step 6,
and prefer an existing user/group property over a new event property when the
cut is user-level.

## Gotchas that masquerade as taxonomy problems

- **`whitelisted` tracking-level users don't send custom product events.** Both
  arms are filtered identically, so comparisons stay fair, but absolute volumes
  undercount. Low volume from a segment usually means "not enrolled," not
  "broken."
- **Legacy events carry no variant.** They're usable for pre-experiment
  baselines only; never propose reading an arm split off an event that predates
  the experiment unless exposure-based segmentation does the splitting.
