# How product analytics events fire in leadgenie

Verified against the codebase, the Amplitude MCP, and
Snowflake. Paths are stable; line numbers drift — prefer reading
the named file, and update this file when the code moves.

## The one pipe (frontend)

Every web product event ends at **`zenalytics.track(event, properties?, options?)`**
— `assets/common/lib/zenalytics.ts`, imported as `common/lib/zenalytics`
(~1,900 importing files). It fans out to Amplitude **and** Customer.io. The
Amplitude leg goes through the `@amplitude/analytics-browser` SDK
(`assets/common/lib/amplitude.ts`) straight to the first-party proxy
`https://www.apollo.io/amp-outbound2/` — **not** through Rails. There is no
Rails relay endpoint for frontend product events (the `/experiments/expose`
relay is exposure-only).

Wrappers all end at `zenalytics.track`; find the call behind the event, then
record the wrapper as the `code_location`:

- `useAnalyticsTrack` / `AnalyticsContextProvider` —
  `packages/analytics/src/zenalytics/components/AnalyticsContext.tsx`. Merges
  hierarchical default properties (defaults → context → call site).
- `ProspectingAnalytics.*` and `trackSearchPerformedEvent` —
  `packages/app-commons/src/utils/amplitude/prospecting.ts` and `.../utils.ts`.
  Builds the `Record Actioned: <X>` family and the search events.
- Redux middleware `assets/common/lib/middleware/analyticsMiddleware.ts` emits
  Record Actioned events from completion actions (see
  `documentation/prospecting/record-actioned.md`).
- `assets/common/lib/flowTracker.ts` — `Flow Started/Succeeded/Failed`.
- Page views: `trackPageViewedEvent` fires `View Page` **only for routes in the
  `TRACKED_ROUTES` map** in `packages/app-commons/src/utils/amplitude/utils.ts`;
  many pages also call `zenalytics.track('View Page', …)` directly.
- Packages that can't import `common/lib` use the **pub/sub shim**
  `zenalytics` from `@apolloio/shared` (`packages/shared/src/lib/zenalytics.ts`)
  — an event bus that `common/lib/zenalytics.ts` subscribes to and forwards.
  Gotcha: the shim silently drops events if `common/lib/zenalytics` was never
  imported in that bundle.
- Day-sampling helper `assets/common/lib/amplitudeDaySampling.ts`
  (`shouldSampleAmplitudeByWeekday`, Mon/Tue) — an event using it undercounts
  by design; check before trusting its volume for a metric.

## Backend (Ruby)

`Zenalytics` (`packs/iam/lib/zenalytics.rb`, `@pack_public`) sends directly to
Amplitude's HTTP API (`https://api2.amplitude.com/2/httpapi`):

- `Zenalytics.track({ user_id:, event:, properties: }, amplitude: true, ...)` —
  async; `sync_track` is the synchronous path. Blank `user_id` → silent no-op.
- Test env is a no-op unless `ENABLE_AMPLITUDE_IN_TEST=true` — a passing spec
  proves nothing about delivery.
- `AmplitudeUtils.track_record_actioned_event` in
  `packs/experiments/lib/amplitude_utils.rb` wraps the Record Actioned family
  (its `EVENT_NAMES` comment points at a stale `assets/app/...` path; the real
  file is `packages/app-commons/src/utils/amplitude/prospecting.ts`).
- ~394 `Zenalytics.(sync_)track` call lines across `packs/` and `app/`.

## Extension and mobile

Extension content scripts can't reach Amplitude (CORB): they
`chrome.runtime.sendMessage` (`SEGMENT_ANALYTICS_TRACK` — legacy name, there is
no Segment) to the background worker, which calls the same `zenalytics.track`
(`assets/chrome-extension/background/extensionAnalyticsService.ts`). Extension
events have **no `source_url`** and dedupe `Extension Used` /
`LinkedIn Extension Viewed` for 24h. Mobile (`assets/mobile/`) imports
`common/lib/zenalytics` directly.

## What arrives automatically (matters for the property check)

- **Per event, web:** only `source_url` (normalized route), added in
  `_amplitudeTrack` — and it **overwrites** any caller-passed `source_url`.
  Everything else on an event is explicit at the call site.
- **User/group properties** are set by `identify`, not per event: client traits
  from `RegisteredApp` / `bootstrapWithData` (viewport, device, nav version,
  group `account_id` = team id), and the rich server-side set — plan, team,
  ARR, seats, feature flags, UTMs — from `Zenalytics.formatted_user_info`
  (`packs/iam/lib/zenalytics.rb`) pushed by the billing identify workers.
  **Segment cuts (plan, team segment) usually live here, as user/group scope —
  check the property's scope in Amplitude before asking for a new event
  property.**

## Tracking-level gate

`shared/configs/always_tracked_events.yml` is the allow-list sent even at
tracking level `whitelisted`; both `zenalytics.ts` and Rails read it. As of
2026-10-05 Rails hard-codes every user's level to `ALL`
(`packs/iam/app/models/concerns/user_amplitude_reporting_functionality.rb`), so
the gate binds only before `identify` runs (frontend defaults to
`whitelisted` until bootstrap). The SSO audit (Sep 2026) still described
whitelisted users as not sending — **re-verify the level logic per audit**
rather than assuming either state; an event missing from the allow-list is a
volume-undercount suspect either way.

## Event names

- **No central registry.** Mostly string literals at call sites (~1.4K), plus
  file-scoped constants — so a literal grep can return zero hits for a live
  event. `'Perform Search'` fires only via `SEARCH_PERFORMED_EVENT_NAME` /
  `trackSearchPerformedEvent`.
- **Code name ≠ Amplitude display name.** Taxonomy entries carry both: code
  sends `Perform Search`; Amplitude displays "Search Performed" (verified via
  taxonomy pull 2026-10-05). Always match on the raw `name`, and quote both in
  the spec when they differ.
- Naming guidance (not enforced): `documentation/frontend/amplitude-event-instrumentation.md`.
- `shared/configs/habit_activation_record_events.yml` — the 9
  `Record Actioned:*` events feeding habit activation (FE + Rails both read it).

## Grep starters (validated 2026-10-05; run from the repo root)

- Literal FE call sites: `rg -n "zenalytics\.track\(\s*'<Event Name>'" assets packages`
- Multi-line calls (single-line rg misses them):
  `rg -n -U "zenalytics\.track\(\s*\n\s*'<Event Name>'" assets packages`
- Constant-fired events — find the literal's one definition, then its users:
  `rg -n "'<Event Name>'" packages assets packs app` then grep the constant name.
- Backend: `rg -n "event(_type)?:\s*['\"]<Event Name>['\"]" packs app`
- Any shape, tests stripped:
  `rg -n -F "<Event Name>" assets packages packs app --glob '!*.test.*' --glob '!*_spec.rb'`
- Skip `db-migration-files/` and `worktrees/`. `Record Actioned: X` names are
  built from the `ProspectingAnalyticsEventType` union in `prospecting.ts` —
  grep the `X` part.
- `scripts/event-tracking/get-event-owner.ts` already maps event name → owning
  team via the same grep patterns; `.claude/skills/automate-amplitude-event/`
  maps an event to its UI flow. Use them as cross-checks, not sources of truth.

## Amplitude lookup mechanics (Stage A step 4, Stage B step 4)

Projects: **241072 prod**, **168367 staging** (267347 is the E2E coverage test
project — never use it for volumes).

- **Existence + properties:** `search_amp_data_taxonomy` (kind `events` for the
  concept, then kind `property_values` / `properties` scoped by `eventType` for
  what actually arrives). Hits return `name` vs `display_name`, owner,
  `first_seen`/`last_seen`, and flag zero-volume events.
- **30-day volume on the target audience:** `query_amplitude_data` with a typed
  segmentation chart — the event, `date_range: {relative: "Last 30 Days"}`,
  `measured_as` totals and uniques, and the audience as `segments`/`where`
  filters. Record project id, filters, and pull date next to the number.
- **Exposure volumes:** segment `$exposure` by the user property
  `gp:[Experiment] <flag key>` — the MCP validator rejects a `flag_key` event
  filter on `$exposure`.
- Flag mismatches both ways: in code but near-zero volume (dead path, gate, or
  allow-list miss), and volume but no code hit (backend sender, extension, or a
  renamed constant).

## Snowflake lookup mechanics (when Amplitude volume is insufficient)

Via the Jarvis MCP, read-only. `ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS`
(columns verified 2026-10-05): filter `EVENT_TYPE` (text name) or
`EVENT_TYPE_ID`, window on `EVENT_DATE`, properties in the `EVENT_PROPERTIES` /
`USER_PROPERTIES` / `GROUPS` VARIANTs, team via `APOLLO_TEAM_ID`. Resolve any
business predicate ("active team", "SMB+") through `lookup-business-term` —
never hand-write one — and check `lookup-saved-metric` for a governed
definition before computing your own.
