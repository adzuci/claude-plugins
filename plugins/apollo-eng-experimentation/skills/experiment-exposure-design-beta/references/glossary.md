# Plain-English glossary

Use these inline, one sentence, the first time a term matters. Offer the longer version; don't deliver it
unprompted. Apollo-specific meanings first.

- **Assignment** — Amplitude deciding which arm a *team* is in. At Apollo this happens server-side on
  `auth/check`, once per team per day (cached). Produces the `[Experiment] Assignment` event.
- **Exposure** — the moment a user actually experienced their arm. Fired per user via
  `/experiments/expose`, deduped for a week. **All analysis is over exposed users, so where this fires
  defines who the experiment is about.**
- **Exposure point / exposure moment** — the exact moment the experience first differs for control vs
  treatment, as the user perceives it. Not where the code branches.
- **Counterfactual placement ("would have")** — in control, fire exposure at the moment treatment
  *would have* changed something, so both arms are counted on the same condition.
- **Targeting / audience / eligibility** — the rules for who can enter. Ineligible teams get a **nil
  variant**: control experience, no exposure. Must be decided once, the same way for every arm, with
  data that exists at assignment time.
- **Bucketing unit / bucketing key** — the identifier hashed to pick an arm. Apollo: `account_id`
  (team). Locked once anyone is bucketed.
- **Allocation / split** — control vs treatment share (default 50/50). Don't change mid-run.
- **Rollout %** — how many eligible teams can be bucketed at all. Use this to ramp.
- **Variant** — the named arm (`control`, `treatment`, `variant_a`…). Must match between code and
  Amplitude exactly.
- **Nil / default / fallback variant** — what the code sees when there's no assignment. Treat as
  control; never expose it.
- **Exposure asymmetry** — control and treatment reaching the exposure call at different rates. The
  most common cause of SRM at Apollo.
- **Exposure dropout** — assigned users who leave before reaching the exposure surface (often very
  small businesses who bounce). Becomes a problem only when it differs by arm.
- **SRM (Sample Ratio Mismatch)** — the observed split differs from the configured split by more than
  chance (chi-square). Means the data can't be trusted until the cause is found — nearly always plumbing.
- **Dilution** — counting users who never saw the difference (exposure too early). Shrinks the measured
  effect; needs more traffic to detect anything.
- **Dry run / A/A test / validation test** — same exposure and eligibility plumbing, identical
  experience for all arms, run in production 48–72h to prove the plumbing before the real experiment.
- **Intent-to-treat (ITT)** — analyzing everyone as assigned, whether or not they reached the change.
  Honest for a ship decision; a fallback when exposure is asymmetric.
- **Guardrail metric** — something you must not harm (errors, latency, core conversion). Checked in every
  experiment; in a dry run they should be flat.
- **Power / MDE** — how likely you are to detect an effect of a given size (power) and the smallest effect
  you could detect (MDE, default 10% here). Both depend on the *eligible exposed* volume, not page traffic.
- **Exposures without assignments** — an Amplitude diagnostic that's structural at Apollo (one
  assignment per team, many exposures per team). Dismiss per experiment.
- **God mode** — internal impersonation. Never exposes.
- **VSB / SMB+** — company size < 21 vs ≥ 21 (common targeting boundary).
- **Core user / core team** — activation's common eligibility gate. Backend `Team#is_core?` =
  `company_size > 0` (enriched teams); sent to Amplitude as the `core_user` property; FE reads it
  via `selectCheckCoreStatus`.
- **ERD** — the engineering design doc where exposure point, eligibility and the A/A decision get
  recorded and signed off (design, DS, PM).
