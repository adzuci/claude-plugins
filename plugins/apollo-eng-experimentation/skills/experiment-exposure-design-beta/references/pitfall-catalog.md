# Exposure & eligibility pitfall catalog

Each entry: what it is (plain English) → why it matters → code signals to look for in leadgenie →
a real Apollo example → the usual fix. Use one example per finding at most; they're here to make the
risk concrete, not to lecture.

Know how sure you are of every finding (traced both arms end to end; traced with a named assumption; could not resolve) and name the evidence (file:line, path traced). The grade stays in your head: the hand-over carries the words, not the grade.
"Can't tell" is a valid answer — turn it into a question for the engineer with a concrete way to check.

______________________________________________________________________

## P1. Exposure only reachable by one arm (asymmetric exposure)

**What:** the exposure call sits somewhere control users never (or rarely) reach — inside a modal,
component, or branch that only mounts for treatment.
**Why:** exposures are the denominator. If control can't expose, the "experiment" compares treatment
users to almost nobody; Amplitude flags SRM, or worse, doesn't and you read garbage.
**Signals:** `useExperiment`/`exposeExperiment` inside a component rendered under
`variant === 'treatment'`; exposure in a treatment-only modal/drawer; a wrapper hook with
`automaticExposure: <condition>` where the condition correlates with variant;
`ExperimentExposureTracker` rendered in only one switch branch.
**Example:** Default Fields Exp 2 (Dec 2025) — exposure fired inside a modal that only rendered for
treatment. Not 5% vs 27%: **0% vs 100%**. Home Hub side-nav (May 2026) — exposure only from the
treatment side-nav path until ACT-4294.
**Fix:** one call, one place, reached by both arms; in control, fire where treatment *would have*
diverged ("counterfactual" placement).

## P2. Variant influences routing / redirects / early returns before exposure

**What:** code reads the variant (often straight from the store) and changes where the user goes or
whether a branch continues — before any exposure fires. The arms then reach the exposure surface at
different rates.
**Why:** the most common cause of post-launch SRM at Apollo. Assignments balanced, exposures not.
**Signals:** selectors/routing reading `state.experiments` with no hook; `variant === 'treatment' ? '/a' : '/b'` in navigation; `if (variant !== 'treatment') return null` above the exposure call; redirects or
`navigate()` conditioned on variant; treatment needing extra data whose failure returns early.
**Example:** Home Hub Reconciliation Rerun (May–Jun 2026) — `selectInitialPage.ts` routed treatment to
`/home` (auto-exposes) and control to `/onboarding-hub/queue` (no exposure). 32.7% vs 27.1%
assignment→exposure, concentrated in very small businesses who bounced. Exposing on the queue page
would have been wrong (unrelated surface). The bad branch is gone (shipped and removed in PR #97463).
Correct pattern, live in code: expose at the shared boundary before either path renders — the
Onboarding Entry A/A's `useOnboardingEntryExposure` hook, called at every onboarding entry surface
(see mechanics §6).
**Fix:** move exposure to the last point both arms share before divergence; or route both arms through
the same surface; never expose on an unrelated surface to "balance" it.

## P3. Exposure fires too early (mount / page load) — dilution

**What:** exposure on component mount or route load, when the user may see an empty state, a loading
state, or an off-screen region — i.e. before the treatment difference is actually visible.
**Why:** counts people who never experienced the difference. Shrinks the measured effect toward zero
and needs more traffic to detect anything. Also produces "exposed but nothing changed" cohorts DS has to
slice out afterwards.
**Signals:** `useExperiment` at the top of a page/view component; exposure before data fetch resolves;
exposure on a list view where the differing element (a column, an action bar) may be empty, off-screen,
or only appear on hover.
**Example:** People Default Columns (Jul–Aug 2026) — exposure on page mount; exposed population
included users who saw an empty state and never saw a treatment column. Hoverbar did it right: exposed
when the action column rendered *or would have rendered*, or on hover — whichever came first.
**Fix:** expose at the first user-visible divergence tied to the hypothesis. Compose a small component
that mounts only when that moment happens and put the hook there. Exception: if the hypothesis is about
backend behavior/performance on load, exposing on load can be right — ask "is the divergence tied to
the hypothesis?"

## P4. Exposure fires too late / only after an action

**What:** exposure gated behind a click, hover or completed step that the treatment itself makes more
or less likely.
**Why:** the trigger condition becomes treatment-dependent → SRM and biased population.
**Signals:** `exposeExperiment()` inside an `onClick`/`onHover` handler that exists only because of the
treatment; exposure after a step the treatment removes or adds.
**Example:** AI Onboarding Challenger v1 fix (May 2026) — treatment at the join-team page had no
exposure until progressing; control exposed immediately on its first page.
**Fix:** fire when the divergence is *visible*, not when it is *acted on*. If two moments are
candidates, fire at whichever comes first, in both arms.

## P5. Nil / default variant mishandled

**What:** an ineligible or unassigned team (nil variant) either gets the treatment experience, or
gets exposed.
**Why:** ineligible teams pollute the population; exposing a fallback variant over-counts control
(Amplitude lists this as an SRM cause).
**Signals:** `variant !== 'control'` used to mean treatment (nil passes!); `defaultVariant` set to
treatment; manual exposure paths without the `isEmpty(variant)` guard; backend code that doesn't treat
nil as control.
**Fix:** `variant === 'treatment'` (positive check) for treatment; nil → control experience, no exposure.

## P6. Eligibility checked in more than one place / different layers

**What:** eligibility partly in Amplitude targeting, partly in FE, partly in BE — with different
definitions, or evaluated at different times.
**Why:** the effective population differs from what Amplitude thinks it targeted; DS can't size it;
arms can differ if one check depends on treatment state.
**Signals:** an in-code gate (`isCore && isPaying && seats >= 1`) *and* Amplitude targeting on overlapping
properties; FE gate on a Redux selector while BE gates on a model field; gating selector keyed on the
wrong concept (admin status vs billing access).
**Example:** Default Fields Exp 2 — gating selector keyed off admin status instead of billing access →
wrong population. AI Onboarding V2 — SMB+ definition depended on data that back-populates after
onboarding.
**Fix:** one check, one place, same for all arms, using data that exists at assignment time. Decide
explicitly what lives in Amplitude vs code and why; if a property Amplitude targets isn't sent in the
evaluation call, it lags — send it or don't target on it.

## P7. Amplitude targeting vs in-code targeting drift

**What:** Amplitude's audience rules and the code's assumptions disagree (bucketing unit, property
semantics, variants list, rollout).
**Signals:** user-level bucketing while code assumes the whole team shares a variant; targeting on a
property whose meaning nobody traced (`lib/zenalytics.rb`); variants in code ≠ Amplitude; targeting
rules that duplicate an in-code gate (double-filtering); an empty targeting rule (matches everyone).
**Example:** GA-505 — bucketing ran at user level instead of account level. Combined Kaizen discussion —
proposal to expose everyone and filter to SMB+ in Amplitude afterwards would not preserve the 50/50 within
the filtered slice (post-hoc filtering ≠ targeting).
**Fix:** see `amplitude-config-checks.md`. Target before bucketing; never rely on post-hoc filtering to
define the population.

## P8. Other conditionals above the exposure point block treatment after exposure

**What:** exposure fires, then some unrelated conditional (someone else's feature flag, a concurrent
experiment, a permission check) prevents the treatment from rendering.
**Why:** users counted as treated saw control. Silent dilution; can't be fixed in analysis.
**Signals:** treatment UI threaded through shared components with many conditionals; other experiment
hooks on the same surface; feature flags evaluated between exposure and render.
**Example:** Kaizen Part 1 — components added to the orchestrator post-launch caused runtime errors;
`ai_assistant_debug` flipped by another team broke staging; `assistantFileAttachments` broke composer
layering.
**Fix:** isolate treatment in net-new components behind an error boundary; fire exposure as close as
possible to the render decision; list concurrent experiments on the surface in the hand-over.

## P9. Loading-state parity

**What:** one arm renders something (a CTA, a column) during loading that the other hides until load
completes.
**Why:** inflates one arm's impression denominator; mechanically moves CTR-style metrics.
**Example:** GA-484 Finder Empty State — CTA rendered during loading in treatment only; CTR halved;
test invalid.
**Fix:** verify both arms' loading and empty states side by side before launch (ask for control vs
treatment in Figma).

## P10. Eligibility pool never sized / stacked conditions

**What:** several AND-ed eligibility conditions whose combined rate nobody multiplied.
**Why:** experiments that can't reach power in any reasonable window; mid-flight loosening → multiple
populations → rerun.
**Example:** Project Alchemy — 7 stacked conditions, one converting at 0.51%; 2 exposures on day one;
eligibility relaxed three times; rerun under a new key. GA-530 reached 7.5% of target in 36 days.
**Fix:** get an expected exposed volume from DS before build; redo it on any scope change. The skill
flags this; it does not compute it.

## P11. Re-exposure asymmetry (dedup differs by arm)

**What:** one arm can re-fire exposure and the other can't (e.g. control re-mounts a component
treatment replaced).
**Why:** Amplitude dedups only within the selected date range, so slicing sub-windows shows SRM drift.
**Example:** Default Scoring 2.0 first run — control could re-fire, treatment couldn't; SRM appeared when
analyzing post-Dec-29 windows.
**Fix:** rely on the platform's 1-week per-user dedup and symmetric placement; analyze full windows only.

## P12. Two experiments in one / bundled treatments

**What:** two cohorts or two changes under one key.
**Why:** can't attribute; one bad cohort sinks both.
**Example:** AI Onboarding V2 — two cohorts baked into one experiment; "should have been a separate
experiment". Action Bar pt1 + pt2 — run independently first, combine later under a new key.
**Fix:** separate keys; same code, different key is cheap.

## P13. Dry run that isn't the same plumbing

**What:** the A/A uses a different hook, placement, or eligibility than the A/B will.
**Why:** it proves nothing about the real experiment.
**Signals:** A/A and A/B call sites differ in anything other than the key and the treatment render.
**Fix:** same hook, same point, same gate; the A/A returns the control UI for all variants; the flip is
a key change.

## P14. Misreading debug signals

**What:** treating the `experiment.expose` console log as proof of an Amplitude event; treating
"exposures without assignments" as a bug; treating trickling exposures after rollback as a leak.
**Why:** wasted investigations and false alarms; the first one can hide a real missing-exposure bug.
**Fix:** the console log fires before the guards — check the network call and the dedup state;
the assignments warning is structural (team cache) — dismiss per experiment; post-rollback trickle
fades as the 1-day cache expires.

## P15. New-signup exposure and the groups payload gap

**What:** experiments exposing users within seconds of signup may have `$exposure` events Amplitude
can't link to an account (when the groups payload isn't attached).
**Why:** Amplitude analyzed ~11% of exposed teams non-randomly in AI Onboarding v2 → false SRM.
**Fix:** PR #102299 (ACT-5149) is merged but gated: `build_exposure_event` attaches
`groups: { account_id }` only when the `experiment_exposure_event_groups` feature flag is on
(`config/feature_flags/growth-activation-fe.yml`). Check the flag's production rollout; if it isn't
fully on, any experiment exposing new signups should plan a Snowflake cross-check of exposure counts.

______________________________________________________________________

## Quick check to run through for any review

1. Trace control's path to the exposure call. Trace treatment's. Same rate? (P1, P2, P4)
1. Does anything read the variant before that call? (P2)
1. What does the user see at the moment exposure fires? Empty/loading/off-screen? (P3, P9)
1. Nil variant → control UI, no exposure? Positive check for treatment? (P5)
1. Where is eligibility decided, how many places, with data available when? Matches Amplitude? (P6, P7)
1. What else sits between exposure and render? Concurrent experiments? (P8)
1. Did anyone size the eligible pool? (P10)
1. A/A identical to A/B except key + render? (P13)
