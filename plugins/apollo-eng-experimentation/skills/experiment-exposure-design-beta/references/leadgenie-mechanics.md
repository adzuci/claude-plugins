# How experiments are wired in leadgenie

Verified against the codebase on 2026-10-05. Paths are stable; exact line numbers drift — prefer
reading the named file over trusting a stale number, and update this file when the code moves.

## The three-part pattern

`experiment configuration → variant assignment → exposure firing`

Targeting limits **assignment**; if a team is not assigned there is no variant and therefore no
exposure. Exposure is the moment a user actually experiences the variant. All analysis is computed
over exposed units, so **where exposure fires defines the experiment population**.

## 1. Registry (source of truth for keys and variants)

`assets/types/experiments.ts` — two entries per experiment, both required:

```ts
export enum ExperimentNames {
  MyNewExperiment = 'myNewExperiment', // PascalCase member, camelCase value = Redux store key
}
export const activeExperiments = {
  [ExperimentNames.MyNewExperiment]: {
    variants: ['control', 'treatment'] as const,
    key: 'my-new-experiment', // explicit kebab string; must equal the Amplitude flag key exactly
  },
} as const;
```

- There is no camelCase→kebab conversion: `key` is a hand-written literal. A typo means nil
  variant everywhere — silent "control for all".
- `ExperimentVariant<T>` is derived from `variants`, so a variant typo in code fails typecheck —
  but a variant missing *in Amplitude* does not.
- **Ownership YAML** (not a second registry): `config/experiments/<team>.yml` (e.g.
  `growth-activation.yml`) maps `amplitude_key` → `name` + `code_ref` for the owning team.
  `scripts/experiments/validator.ts` (`pnpm run validate:experiments`, CI job
  `validate-experiments`, non-blocking) enforces that experiments.ts and the YAML stay in sync —
  a new experiment needs both.

**Review check:** the flag key under review exists in `activeExperiments` and the ownership YAML;
variants match the Amplitude config.

## 2. Frontend hooks

### `useExperiment(experimentName, defaultVariant)` — `assets/common/hooks/useExperiment.ts`

Auto-exposes on mount: wraps `useExperimentExposure`, calls `exposeExperiment()` in a `useEffect`
when `exposureStatus === 'not exposed'`, returns `variant ?? defaultVariant`. The default hook for
most cases. Its strength is that you can't read a variant without exposing; its weakness is that
hooks run at the top of the component, so **exposure fires whenever the component mounts —
including when conditional logic below hides the experiment UI, or when the surface is in a
loading/empty state.** The standard fix is component composition: extract a small component that
renders only when the experiment UI would be visible, and call the hook inside it.

### `useExperimentExposure(experimentName)` — `assets/common/hooks/useExperimentExposure.ts`

Manual control. Returns `{ variant, exposeExperiment, exposureStatus, key }`;
`exposureStatus: 'not exposed' | 'exposing' | 'exposed' | 'failed'`.

`exposeExperiment()` logs `experiment.expose` (experimentName, flagKey, variant, alreadyExposed,
exposureStatus) **before** any guard — but only in builds with `process.env.SHOULD_ENABLE_LOGGING`,
i.e. local dev (webpack: `(IS_DEVELOPMENT || IS_TEST) && !IS_CI`). It is a local debugging aid, not
available in staging/production DevTools, and seeing it is **not** proof the exposure reached
Amplitude — the guards run after it.

Then one early return skips exposure when **any** of these hold (single `||` chain, in this order):

1. `isGodMode()` — internal impersonation never exposes.
1. `process.env.IS_TEST` / `process.env.IS_E2E_TEST` — unit and e2e builds never expose.
1. `isEmpty(variant)` — nil variant means ineligible/unassigned → **no exposure**.
1. `exposureStatus` is `'exposed'`, `'exposing'`, or `'failed'` — dedup plus no auto-retry.
   `'failed'` is sticky for the session, except a failure after unmount resets to `'not exposed'`
   (fire-and-forget: the request isn't aborted on unmount).

Then `POST /experiments/expose` with `{ exposures: [{ flag_key, variant }] }`. It does not talk to
Amplitude directly.

### Variant source

Variants are bootstrapped by the backend on `auth/check` (`bootstrappedData.experiments`) into
Redux (`state.experiments`, `assets/common/reducers/experimentReducer.ts`) — including
`exposed`, from the backend's `ExperimentExposure` records within the last week, hydrated as
`exposureStatus: 'exposed'`. So a user already exposed this week doesn't re-fire in a fresh
session. Reading the variant from the store **does not expose** — this is how routing selectors
end up branching on variant with no exposure.

### Wrapper hooks (team-specific)

`assets/common/components/activation/platform/hooks.ts` has a private
`useGatedExperiment(name, { automaticExposure = true })` (~line 238): exposes in an effect only
while `automaticExposure` is true, returns `(variant ?? 'control') === 'treatment'`. Wrappers that
gate exposure on a condition are exactly where asymmetry hides — the condition may be true more
often for one arm, and must gate both arms of a key identically. Current conditional ones:

- `useSaveSearchOverhaulExperiment` (+ its Aa) — `automaticExposure: !isHyperRestrictedFullCheck`
- `useIsCombinedKaizen1Treatment` — same condition
- `useCleanupDefaultCompanyFiltersExperiment` (+ Aa) — `automaticExposure: enabled`
- `useDefaultColumnsExperiment({ enabled })` — same file, inlines the effect with an `enabled` gate
- `useHoverBarRebalanceExperiment` — manual: returns an expose callback that no-ops off `/people`

`packages/growth/src/onboarding/hooks/useOnboardingEntryExposure.ts` is the onboarding-entry
pattern (see §6). New wrappers appear regularly — grep, don't assume this list is complete.

### Class components / selector-driven surfaces

`ExperimentExposureTracker` (`assets/common/components/ExperimentExposureTracker.tsx`) renders
nothing and fires idempotent exposure via `useExperiment`; props `experimentName` +
`defaultVariant`. Must be rendered alongside *every* variant switch, not just treatment.

## 3. Backend — `packs/experiments/lib/experimentation/experiments.rb`

Class `Experimentation::Experiments`.

**Assignment is per TEAM, cached.** `fetch_variants_for_user(user)` reads Redis key
`experiments_#{user.team_id}` (TTL 1 day). A global marker `experiments_updated_at`
(written by `clear_assignment_cache` with no team arg — admin-UI reset, Apollo-admin-only
controller action) makes every team cache stale at once. On miss/stale it calls Amplitude remote
evaluation (`make_amplitude_fetch_call`) bucketed by `groups: { 'account_id' => [team.id] }`;
Amplitude records the `[Experiment] Assignment` event on that fetch; on cache hit there is no
Amplitude call and no assignment event. Consequences:

- One assignment event per team per cache expiry; every user on the team can expose → the
  "exposures without assignments" Amplitude warning is **structural, not a bug** (~3× ratio).
  Dismiss it per experiment; do not chase it.
- Targeting changes need a cache reset to take effect (and bucketing is locked once anyone is
  bucketed, so targeting changes mid-run effectively mean a new experiment/key).
- After rollback, exposures trickle in until caches expire.
- Batch/cron code must use `get_cached_experiment_variant(flag_key, user)` — cache-only, returns
  nil on a miss (team skipped until next organic evaluation), stale value on stale cache — instead
  of the remote-fetching `get_experiment_variant` (which floods Amplitude with assignments).

User properties sent in the evaluation call (`make_amplitude_fetch_call`, ~line 252): `account_id`,
`team_created_at`, `created_at`, `core_user`, `team_is_free_domain`, `team_status`, plus any flags
listed in `AMPLITUDE_TARGETING_FLAGS` (sent as `Feature Flag - <name>` properties; the list is
empty unless a team adds theirs). A property Amplitude targets on that is **not** in this list
relies on async property sync (~60 min lag) → teams can be evaluated before the property exists.
`company_size` is still not sent.

**Exposure is per USER, relayed.** `POST /experiments/expose`
(`packs/experiments/app/controllers/api/v1/experiments_controller.rb#expose`) → `expose_variants`
→ `make_amplitude_exposure_request` → synchronous HTTP (in-request) to Amplitude's event API with
`event_type: '$exposure'`, `event_properties: { flag_key, variant }`. Deduped **before** the
Amplitude call: skipped when an `ExperimentExposure` record (`user_id`, `flag_key`, `variant`,
`last_exposed_at`) exists within **1 week**. In dev/test the Amplitude request is stubbed to
success — no real event.

**Groups payload on `$exposure` (PR #102299 / ACT-5149): merged, flag-gated.**
`build_exposure_event` attaches `groups: { 'account_id' => [team_id] }` only when the
`experiment_exposure_event_groups` feature flag is on (declared in
`config/feature_flags/growth-activation-fe.yml`). When off, Amplitude infers the account at
ingest, and brand-new signups exposed within seconds of signup can be dropped from account-level
analysis (AI Onboarding v2 false SRM). **Check the flag's production rollout** before dismissing
this for an experiment that exposes new signups; if it isn't fully on, plan a Snowflake
cross-check of exposure counts.

Other public API: `get_experiment_variant(flag_key, user, expose_variant: false)` — note the
kwarg: the backend can expose server-side too, same dedup — `list_experiments`,
`clear_assignment_cache(team_id = nil)`, `view_cache_values(team_id)`. Backend code must handle
nil variants as control.

## 4. Amplitude-side facts that constrain the code

- All Apollo experiments: remote evaluation, bucketed by group `account_id` (Group Name:
  Account ID) — **team-level**. A single user cannot be on a different variant from their team.
- Nil variant = ineligible per targeting → control experience, no exposure.
- Bucketing is locked the moment any unit is bucketed (including testers in test mode). Configure
  bucketing before adding testers.
- Testers: adding one user ID assigns the whole team; the tester must be inside the target audience.
- Rollout % dials how many eligible teams can be bucketed; allocation (50/50) should not change
  mid-run.

## 5. Local/test

- Dev/test backend swaps in `MockExperiment` (`mock_fetch_call`) for assignment and stubs the
  Amplitude exposure request; `MockExperiment.create_and_assign_to_user(flag_key:, ...)` assigns
  any variant regardless of targeting.
- FE hooks themselves refuse to expose under `IS_TEST` / `IS_E2E_TEST`.
- FE tests: `ReduxTestProvider` + `makeExperiment({ name, variant, exposed })`; `exposed: true`
  should produce no `/experiments/expose` call. Unit-test exposure guards; don't test that
  Amplitude received it.
- Staging cannot validate exposure symmetry — traffic is internal and homogeneous. Only
  production can.

## 6. Canonical anti-pattern and the worked fix

**Anti-pattern (historical, now removed):** `assets/common/selectors/selectInitialPage.ts` once
routed on variant — `variant === 'treatment' ? '/home' : '/onboarding-hub/queue'` (introduced in
PR #86646, ACT-3873) — *before* any exposure. Treatment landed on a page that auto-exposed;
control landed on a page that did not. Assignments were balanced; exposures were not (SRM, Home
Hub Reconciliation Rerun investigation). Exposing on `/onboarding-hub/queue` would have been wrong
too (unrelated surface). The experiment shipped and the branch was removed in PR #97463
(ACT-4822); the selector no longer reads any variant. To show a user the known-bad code, check out
the tree just before PR #97463's merge commit (`c1d539c2331f~1`).

**Worked fix (live code):** the Onboarding Entry A/A (`OnboardingEntryExposureTest`, Sep 2026)
exposes via `useOnboardingEntryExposure`
(`packages/growth/src/onboarding/hooks/useOnboardingEntryExposure.ts`) — one shared hook called at
*every* onboarding entry surface (`OnboardingPlatformWelcomeV3`, `AiOnboarding`,
`OnboardingJoinTeamPage`) before the flows diverge, gating both arms identically and guarding on
user/team presence so eligibility cannot skew the split. That is the "expose at the shared
boundary before either path renders" pattern to point engineers at.

## Grep starters for a review

(Validated 2026-10-05 — each produces hits for live experiments. Include `packages/` — product
code is being extracted out of `assets/app` into `packages/<module>`.)

- Registry + ownership: `rg "'<flag-key>'" assets/types/experiments.ts config/experiments/`
- All readers of the variant: `rg "ExperimentNames\.<Name>\b|'<flag-key>'" assets/ packages/ app/ packs/`
- Exposure calls:
  `rg "useExperiment\(|useExperimentExposure\(|exposeExperiment\(|ExperimentExposureTracker" <paths>`
- Store reads without exposure: `rg "state\.experiments|selectExperiment" assets/ packages/`
- Backend variant reads:
  `rg "get_experiment_variant|get_cached_experiment_variant|fetch_variants_for_user" app/ packs/ lib/`
