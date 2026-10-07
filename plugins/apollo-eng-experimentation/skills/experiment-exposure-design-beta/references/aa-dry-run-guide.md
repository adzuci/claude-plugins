# A/A dry run — decision guide and setup

Source: Growth Engineering's "A/A (Dry Run) Testing — proving your exposure logic before it decides
anything" and the Jira lifecycle template story "Assess and execute pre-launch exposure dry
run". Reuse the wording; it's already been socialized with the eng team.

## What it is

An A/A test runs the **exact same exposure logic** you'd use for the real experiment — bucketing,
targeting, logging — but every group gets the **identical product experience**. Nothing changes for the
user; only the plumbing is under test. A "failure" therefore means a bug in bucketing, targeting or
logging, never an underpowered effect.

| | A/B | A/A (dry run) |
|---|---|---|
| Goal | Measure a treatment effect | Validate exposure & instrumentation |
| User experience | Differs by variant | Identical |
| Expected outcome | A real difference | No difference |
| A "failure" means | Underpowered / no effect | Bug in bucketing, targeting or logging |

What it catches: exposure events that fire late, twice, or not at all; broken/non-random bucketing;
SRM; wrong audience (cross-check exposed teams against the intended cohort in Snowflake).

## Run one when

- Targeting combines multiple AND/OR conditions in code.
- Eligibility is evaluated in more than one place (BE and FE, or several services).
- Exposure fires at a *new* meaningful moment — not simply on page load.
- Exposure depends on routing, redirects, onboarding steps, or any surface users reach at different
  rates by variant.
- A shared targeting/evaluation utility is being added or changed.
- Layered or mutually exclusive flags/holdouts are involved.

Rule of thumb: **spend the extra day when a bug would be expensive or hard to detect later.**

## Skip it when

- A simple, well-trodden exposure path on a surface both arms load identically, on the already-validated
  platform.
- Same eligibility criteria *and* same exposure point as an experiment that already ran clean (same
  cohort, same plumbing — there's nothing new to prove).
- Low-stakes, easily re-runnable experiment.
- A tight timeline where the cost of delay clearly outweighs the marginal risk — with eyes open about
  the residual risk: "we might get people we weren't expecting; if it's small you can dice it out in
  post-analysis, as long as it doesn't shift the 50/50."

The default question is "why do you *not* need one?" — but the decision is the team's. Record it and the
reasoning in the hand-over / ERD either way.

## Why it's cheap

You are not writing a second eligibility hook or a second exposure point. You create a second experiment
instance in Amplitude, use *that* key in the same hook at the same point, and the UI returns the control
experience for every variant. Flipping to the A/B is a key change. It runs **in parallel with building
the treatment UI**, so it costs almost no calendar time.

## Setup sequence (AA → AB)

1. **Create the A/A in Amplitude** — `/apollo-eng-experimentation:create-amplitude-experiment`
   (same plugin) does most of this; it has no dedicated A/A mode, so name the experiment as the A/A
   (e.g. `<key>-aa`) and give every variant the control experience.
   Set the primary metric you plan to use for the A/B — it barely matters here — and spend the effort on
   a tight **guardrail set**, monitored for the full run.
1. **Set eligibility and exposure point(s)** exactly as the A/B will use them. No variant-dependent
   eligibility checks. Ship as a dedicated PR with no UX change.
1. **Roll out the A/A** in production. Staging cannot validate exposure — the users are us. Before
   launch, get an **expected bucketed/exposed volume from DS** based on the targeting.
1. **Run minimum 48–72 hours - preferred 7 day** (long enough to evaluate if it matches expected volume — a too-short window can pass by luck).
1. **Validate** (with DS):
   - Exposures per arm consistent with allocation (no SRM) — not just "roughly 50/50".
   - Exposed volume matches the pre-ananlysis estimate; if not, the targeting or the exposure point isn't doing what
     you think.
   - Exposed teams are the intended cohort (Snowflake pull; spot-check outliers in prod).
   - Guardrails flat across arms — if one moves, it's exposure/evaluation overhead; fix before the A/B.
   - Ignore Amplitude's "exposures without assignments" warning — structural at Apollo (team cache).
1. **Layer in the A/B**: same hook, same point, same gate, new key, treatment renders. Anything else that
   differs means the A/A didn't prove the A/B (Stage B check on the A/B PR).

## Two cautions

- A balanced A/A is not proof that a *later* comparison is SRM-free if the A/B adds routing or
  eligibility the A/A didn't have (the Onboarding Entry A/A doc says this explicitly).
- After rollback/completion, exposures trickle in until the 1-day assignment cache expires. Not a leak.
