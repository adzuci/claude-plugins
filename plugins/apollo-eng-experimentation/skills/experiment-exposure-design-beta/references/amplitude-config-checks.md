# Amplitude-side checks (and how they collide with code)

Code and Amplitude config are two halves of one setup. Check them against each other.

## How to get the config

1. **Via the Amplitude MCP (preferred):** `use_amp_flags` (action `get`) accepts flag keys
   directly — experiments are flags, so this returns the shell config in one call. For
   experiment-level detail, resolve the numeric ID with `search_amp_entities`
   (`entityTypes: ["EXPERIMENT"]`) then `use_amp_experiments` (action `get`). Extract: bucketing unit / bucket-by,
   evaluation mode, targeting segments (conditions + operators), allocation weights, rollout %,
   variants list, state (testing/running), tester assignments, exclusion cohorts, analysis start date.
1. **Via the user:** ask them to paste the config or answer: bucketing unit, targeting conditions,
   allocation, rollout %, variants, whether it's in testing state. Keep it to one message.

## Checks

| Check | Expect at Apollo | Why it matters / what goes wrong |
|---|---|---|
| Bucketing unit / bucket-by | `account_id` / Group Name: Account ID (team-level) | Code assumes the whole team shares a variant. User-level bucketing (GA-505) breaks that and the team-level cache. Locked once anyone is bucketed, including testers — set it first. |
| Evaluation mode | remote | Local eval has different property/cohort semantics. |
| Variants | Exactly match `activeExperiments[...].variants` in code | A variant present in Amplitude but not in code is unhandled; the reverse means it can never be assigned. |
| Flag key | Exactly matches the registry `key` and is traceable to the tracker (e.g. `...-ga80`) | Typos → nil variant everywhere → silent "control for all". |
| Targeting conditions | Each property is (a) sent in the server evaluation call, or (b) accepted to lag ~60 min; meaning traced (`lib/zenalytics.rb`) or confirmed with DS | Targeting on a property not sent at evaluation time means brand-new/changed teams are evaluated before the property exists → wrong population, VSB leakage. "Don't guess what a property represents." |
| Targeting vs in-code gate | One owner per condition; no duplicate or contradictory filters | Double-filtering hides which layer excluded a team; contradictions create populations nobody intended. |
| Post-hoc filtering | Not used to define the population | Exposing everyone and filtering to SMB+ in analysis does not preserve the split within the slice; the 50/50 must hold for the *targeted* population. |
| Allocation | 50/50 (unless deliberately otherwise), unchanged after start | Changing weights mid-run re-randomizes; restart with a new key instead. |
| Rollout % | Dial this to ramp; never change audience/distribution mid-run | Rollout controls how many eligible teams can be bucketed. |
| Exclusion cohorts | `Experiment Exclusion Cohorts` (RevOps) on the `off` group; ARR-exclusion filter kept | High-ARR / in-deal accounts must not be experimented on. |
| Testers | Inside the target audience; remember one user ID assigns the whole team | Testers outside the audience never get assigned/exposed and people conclude "it's broken". |
| Start date vs actual rollout | Analysis range starts when exposures actually start | AI Onboarding v2: start Aug 3, rollout Aug 20 → 17 days of nulls in every window. |
| Empty targeting rule | None | An empty segment matches everyone. |

## Known structural signals (not bugs)

- **Exposures without assignments** (~3× ratio): one assignment per team per day (Redis cache) vs one
  exposure per user. Dismiss the diagnostic per experiment; lift math is exposure-denominated anyway.
- **Post-rollback trickle**: exposures continue until the 1-day assignment cache expires.
- **Exposures missing an account** for brand-new signups: see pitfall P15 — the groups-payload fix
  is merged but gated behind the `experiment_exposure_event_groups` feature flag; check its
  production rollout.

## Amplitude semantics worth knowing (external docs)

- Assignment fires on `fetch()`/remote evaluation; exposure fires when code reads/reports the variant.
  Analysis relies on the exposure event setting the `[Experiment] <flag>` user property.
- Targeting is evaluated at fetch time only; cached variants can expose teams that are no longer
  eligible — which is why targeting changes need a cache reset and effectively a new experiment.
- Never send an exposure for a fallback/default variant (over-counts control → SRM).
- Cohort-based targeting syncs ~hourly; `First Seen` is absent in a user's first session.

Refs: `sources.md` → Amplitude event-tracking, remote-evaluation, SRM, exposures-without-assignments.
