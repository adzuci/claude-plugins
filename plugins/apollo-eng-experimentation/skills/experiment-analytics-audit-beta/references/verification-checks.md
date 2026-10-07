# Verification checks

How to classify, check arms, confirm landing, link events, and build fixes.
Repo wiring and lookup mechanics live in `leadgenie-analytics-mechanics.md` in this folder;
this file is the judgment layer on top. Amplitude project names verified
2026-10-05.

## Classification (build vs. audit)

Exactly one per expected event, each with file:line evidence:

| Classification | Meaning | Bar |
|---|---|---|
| `built-as-specced` | Code fires the event with the audited name, trigger, and properties | Every one of the three matches; a partial match is `drifted` |
| `drifted` | The event exists but differs from the audit — name, trigger/gating, or properties | Say exactly which field drifted and quote both sides |
| `missing` | The audit specced it; nothing in code fires it | The absence was established with the full grep set, not one pattern |
| `extra` | Code fires it on the experiment surfaces; the audit never listed it | Report it — it may be a legit addition or scope creep; the invoker decides |

An audited `Preexisting` event that can't be found in code is a special drift:
the audit may have recorded a renamed constant or a moved call site — re-run the
constant-aware greps before declaring it `missing`.

**Landing** is a second, independent axis per event:

- `landing-verified` — taxonomy hit **and** recent volume with properties
  arriving, in the project that matches the experiment's stage.
- `staging-only` — confirmed in `168367` but the experiment hasn't launched;
  best obtainable evidence pre-launch, and say so.
- `not-yet-verifiable` — no build deployed anywhere that could emit it. A named
  state, never a pass.

## Arm-symmetry patterns (code level)

The audit's intent (usually "both arms") is the baseline. Flag, with the
condition quoted:

- An analytics call inside a variant branch:
  `variant === 'treatment' && zenalytics.track(…)`, or a `track` call in code
  only reachable after a variant check (routing, early returns, selector-gated
  renders).
- An event fired from a treatment-only component with no control counterpart
  firing the same event at the equivalent moment (and the reverse: control-only
  events the treatment path lost — e.g. the old surface's event no longer fires
  after the treatment replaces the surface).
- A shared event whose *gating surface* the treatment moved or removed — the
  Stage A audit's 🚨 rows; verify each one's fix actually landed.
- Properties that differ by arm when the audit expects them identical (a
  `variant` property is fine; a different `surface` value per arm changes what
  the event means).

Trace each arm's path to the call separately; "the component is shared" is not
evidence the condition above it is.

## Landing checks (Amplitude)

- **Project:** pre-launch → `168367` ("Marketing + App V2 (Staging+Preview)");
  live → `241072` ("Marketing + App V2 (PROD)"). Never `267347` ("Test
  Integration") — that is the E2E coverage project.
- **Exists + properties:** `search_amp_data_taxonomy` on the exact code name
  (kind `events`, then `property_values`/`properties` scoped by `eventType`).
  Match on `name`, not `display_name`.
- **Volume:** `query_amplitude_data` segmentation over a recent window; staging
  volume is internal traffic, so expect low absolute counts — presence and
  properties matter there, not magnitude.
- **Per-arm split (live experiments only):** segment the event by the user
  property `gp:[Experiment] <flag key>`. Zero volume on one arm of a
  both-arms event is a launch-blocking finding.
- **Why code-confirmed events can still show nothing:** Rails `Zenalytics` is a
  no-op in test env; FE hooks refuse under `IS_TEST`/`IS_E2E_TEST`; day-sampled
  events (`shouldSampleAmplitudeByWeekday`) only fire Mon/Tue; events missing
  from `always_tracked_events.yml` undercount when the tracking-level gate
  binds. Check these before declaring an emit bug.

## Amplitude catalog links

Every event that exists in Amplitude gets its data-catalog URL in the report:

```
https://app.amplitude.com/data/apollo-io/<project name, URL-encoded>/events/main/latest/<event name, URL-encoded>?tab=DETAILS
```

Project names (verified 2026-10-05): `Marketing + App V2 (PROD)` and
`Marketing + App V2 (Staging+Preview)` — encode spaces/`+`/parens (e.g.
`Marketing%20%2B%20App%20V2%20(PROD)`). Format matches the links in the SSO
audit. Open or spot-check at least one generated link per run; a 404 usually
means the event name was the display name, not the code name.

## Building a missing event (Stage B step 5)

1. The spec is the audit row: name, trigger moment, gating, properties. No row →
   the invoker defines it first, or it's logged as deferred.
1. Place the call per the mechanics file: `zenalytics.track` from
   `common/lib/zenalytics` (or the feature's existing tracker wrapper / the
   `@apolloio/shared` bus in extracted packages — match the surrounding code's
   pattern, including its `.messages`/tracker file layout).
1. Mind the arm: if the audit says both arms, the call goes at a moment both
   arms reach — never inside the variant branch for symmetry-sensitive events.
1. Show the full diff and get an explicit yes before touching the tree.
1. After applying, run the targeted checks: the unit tests beside the touched
   files (`pnpm test <path>` — never `pnpm test -- <path>`) and typecheck via
   `pnpm exec vitest --typecheck --run <path>` (plain `tsc --noEmit` is known to
   crash on Node 24 in this repo). New behavior warrants a test per the repo's
   standards; follow `.cursor/rules/frontend-unit-tests.mdc` when writing one.
1. The report records the event as `missing → built this run (<commit/diff>)`,
   landing `not-yet-verifiable` until it ships somewhere.
