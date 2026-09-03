# Metric Taxonomy

Every experiment dashboard must account for **all** categories below — none may be silently
omitted. This keeps dashboards comparable across experiments. Each category maps to a section
in `dashboard-template.md`.

All code greps referenced here run against the **PR-head tree** (see SKILL.md Step 1 pin rule),
not current `master` — so the emitted-slice set and touched-surface set reflect what *this* PR
ships and stay identical run-to-run.

______________________________________________________________________

## Success metrics (proposed from diff, confirmed by user)

| Category | Behavioral question | Source |
|----------|--------------------|--------|
| Primary action | Are users doing the new behavior the experiment is meant to drive? | The tracking event (inline `zenalytics.track` **or** wrapper-fired — see SKILL.md "Indirect / wrapper tracking") closest to the experiment intent, found in the diff |
| Secondary actions | Are users doing the supporting behaviors on the same flow? | Other meaningful events / slices on the feature flow |

Primary is required; secondary optional. Cross-ref `shared/configs/always_tracked_events.yml`
— a metric on a non-whitelisted event under-counts free users.

**Single-event / new-slice experiment rule (deterministic).** This rule fires when the diff's
new behavioral signal is carried by **one event** — either:

- (a) the diff **adds exactly one new event** (inline or wrapper-fired — common for badge/UI-surface
  experiments), OR
- (b) the diff **adds no new event but adds a distinguishing new property value/slice** to a
  pre-existing event (e.g. `feature_gate_type='monthly_recap'` on the shared
  `Feature Gate Action Clicked` — common for feature-gate / promo experiments). Here the experiment
  event = that pre-existing event **filtered to the new slice value**.

In either case do NOT invent extra events:

- **Primary** = the experiment event filtered to its **deepest-intent property slice**, chosen ONLY
  from slices the diff's code **actually emits**. First grep every call site (in the PR-head tree,
  resolving wrappers to the underlying `zenalytics.track`) and record the literal property values
  passed — that is the **emitted set**. Then pick the deepest-intent emitted slice:
  - If the event has `action`/`component`, use the fixed ordering `action=clicked > hovered > viewed`; `component=popover > badge`, **over the emitted set only**.
  - **If those property names are absent** (the event uses other props, e.g. `type` /
    `feature_gate_subtype`), rank the emitted values **deterministically** by token-overlap with the
    experiment key + stated goal (the conversion/intent action wins — e.g. `upgrade_plan_direct`
    over post-success CTAs like `book_onboarding_call`). Tiebreak: the value whose call site is
    **latest in the funnel** (nearest the conversion), then first-occurrence by `file:line`.
  - Never select a schema value that no call site passes (if the type allows `clicked` but no call
    fires it, do not pick `clicked`). This keeps the primary off dead/empty slices and identical
    run-to-run.
- **Secondaries** = the **other emitted property slices of the same event** (each remaining emitted
  `action`/`type` value, each emitted `component`, plus break-downs by feature-identifying props
  like `feature` / `filterVersion` / `trigger_location`). These are property breakdowns, never
  separate events. Do not list slices with no emitting call site.

**Urgency / time-remaining property breakdown (deterministic, auto-add when present).** If the
experiment event emits a **numeric countdown/urgency property** — detected by name matching
`/_(days|hours|seconds)_(remaining|left)$/`, `/^(days|hours)_(until|to)_/`, or `*_remaining`
(e.g. `trial_days_remaining`, `seats_remaining`, `days_until_renewal`) — add a secondary that
breaks the primary down by that property bucketed into **fixed deterministic buckets** so two runs
produce identical charts:

- days-remaining → `0–3 / 4–7 / 8–14 / 15+`
- hours-remaining → `0–6 / 7–24 / 25–72 / 73+`
- generic count remaining → `0 / 1 / 2–5 / 6+`

This answers "does behavior change as the deadline/urgency window closes" — the highest-intent
conversion window for trial/renewal/seat-limit experiments. Only add when the property is actually
emitted by a call site (per the emitted-set rule above); never invent the bucket dimension.

**Bridge metric (deterministic, auto-add when a path exists).** The **intermediate product behavior
that sits causally between the primary engagement action and the nearest business conversion
guardrail** — e.g. badge-viewed → *advanced-filter-applied* → checkout. Derivation: candidates come
**only** from the touched-surface set (§1 below) — the same bounded, deterministically-derived set
the guardrail derivation produces. Do **not** widen to other "adjacent" events, hand-picked flows,
or files outside that set (e.g. `actions/*`, unrelated dirs) — that breaks reproducibility. From
that set, pick the event that (a) is downstream of the primary action in the reconstructed feature
flow and (b) is upstream of a free→paid / checkout business guardrail. If exactly one such event
exists, add it as the bridge secondary; if several, add the one nearest the primary by
`file:line`/flow order; if none, omit (do not fabricate). It
answers "did engagement translate into the product usage that actually precedes conversion" —
distinguishing "feature noticed" from "feature used."

______________________________________________________________________

## Behavioral categories (auto-built, complement the Analysis View)

| Category | Behavioral question | Dashboard section |
|----------|--------------------|-------------------|
| Adoption depth | How *much* / how *often* do users do the action? | §1 |
| Funnel decomposition | Where in the multi-step flow do users drop? | §2 |
| Time-to-conversion | Does treatment *accelerate* the outcome, not just lift its rate? | §2 |
| Retention curve | Do users keep coming back to the behavior over N days? | §3 |
| Pathing / adjacent | What do users do before/after; what downstream features shift? | §4 |

**Time-to-conversion (deterministic, auto-add for monetization experiments).** Trigger is a
**token match — no flow-reachability judgement** (the old "reachable from the primary action"
wording was ambiguous and made runs diverge): add the chart iff the **experiment key OR the stated
hypothesis/goal contains a monetization token** — `trial`, `upgrade`, `convert`/`conversion`,
`paid`, `checkout`, `subscription`/`subscribe`, `plan`, `billing`, `monetiz`, `arr`, `seat`. When
it fires, add a **time-to-convert distribution** chart in §2: elapsed time from the primary action
(or exposure) to the **nearest free→paid business guardrail** (`Start Subscription` →
`Express Checkout Upgrade Completed` → `Checkout Page Viewed`, first that is queryable), segmented
by variant, conversion/measurement window = the experiment's natural horizon (e.g. trial length),
not a fixed calendar window, so recently exposed units aren't under-counted. If no monetization
token matches, omit it. A rate lift with no time shift, or a time shift with no rate lift, are
different results — this chart separates them.

______________________________________________________________________

## Guardrails (auto-derived, always included — 2 categories)

Feature-flag / kill-switch guardrails and error/perf observability are intentionally **out of
scope** for this skill.

### 1. Touched-surface events

Existing tracking events already fired in the files/components the diff modifies. The change must
not suppress or drop them. → Dashboard §5.

**Deterministic derivation (must be identical run-to-run):**

1. Grep every touched file (PR-head tree) for the literal patterns (`zenalytics.track(` /
   `sharedZenalytics` / `zenalytics.throttle(` frontend; `Zenalytics.track` / `sync_track` /
   `event_type:` backend) **and the wrapper patterns** (`track[A-Z]\w*(`, `useTrack\w*(`,
   `\w*Analytics\.track\w*(`), resolving each wrapper to its underlying event name. **Count only
   PRE-EXISTING events — exclude any event the diff adds (literal or wrapper track call on a
   `+`/added line).** The diff's own new success event must not count as a hit.
1. **If zero pre-existing matches** (change only adds markup/props, fires no inline tracking), widen
   by a **fixed, bounded scope only**: the touched files **plus their direct sibling files in the
   same directory (non-recursive)**. Grep siblings for the same literal + wrapper patterns. The
   union is the touched-surface set. Do NOT recurse into subdirectories; do NOT hand-pick "adjacent
   surface" events by intuition — same-directory siblings is the sole allowed widening scope, so the
   set stays bounded and reproducible even when a touched file sits at the top of a large tree.
1. Sort by `file:line`, dedupe by ingested event name, resolve each against `241072` with
   `get_events`. **Drop only events that are NOT `isQueryable` — queryable is the sole gate; KEEP
   `isQueryable:true` events even if `isActive:false`** (annotate "(inactive)"). Do NOT
   relevance-trim survivors.

### 2. Standard business guardrails (fixed list — real prod events)

Always tracked regardless of the diff. → Dashboard §5. Every event below is **confirmed active in
Amplitude prod project `241072`** (verified via the Amplitude MCP on 2026-06-23 and cross-referenced
against `shared/configs/always_tracked_events.yml` / `packs/iam/lib/zenalytics.rb` where noted).
Column **Ingested name** is the exact Amplitude `event_type` to use in chart definitions — do not
guess; the display name differs.

| Guardrail | Behavioral question | Ingested name (Amplitude `event_type`) | Display name | Key event properties to segment/break down |
|-----------|--------------------|----------------------------------------|--------------|--------------------------------------------|
| Signup (funnel top) | Did the change reduce signups? | `Sign Up Success` | Sign Up Success | `method`, `oauth_provider`, `company_size`, `signup_page`, `user_role_type`, `is_admin_only`, `invited_with_incentive` |
| Activation (user) | Did the change hurt new-user activation? | `Activate Account` | Apollo User Email Verified | — (fires after signup / email verified) |
| Activation (team / habit) | Did the change hurt team activation? | `Habit Record Actioned Team Activated` | Habit Record Actioned Team Activated | codebase: `HABIT_ACTIVATION_RECORD_EVENTS`, `packs/iam/lib/zenalytics.rb:221` |
| Free→paid conversion | Did the change reduce paid conversions? | `Start Subscription` | Subscription Started | `new_arr`, `arr`, `arr_change`, `previous_arr`, `new_seat_edition`, `new_seat_limit`, `contract_term_num_months`, `is_self_serve`, `has_add_on`, `team_id` |
| Paid→paid conversion (expansion/up-down-grade) | Did the change shift in-plan changes (seats/edition/ARR)? | `Change Subscription` | Subscription Changed | `delta_arr`, `arr`, `arr_change`, `previous_arr`, `previous_seat_edition`, `seats_to_add`, `previous_seat_limit`, `new_lead_credit_limit`/`previous_lead_credit_limit`, `is_self_serve`, `new_contract_term_num_months` |
| Self-serve checkout completion | Did self-serve upgrades drop? | `Express Checkout Upgrade Completed` | Express Checkout Upgrade Completed | — |
| Revenue funnel (checkout step) | Did fewer users reach/clear checkout? | `Checkout Page Viewed` | Checkout Page Viewed | `new_arr`, `new_seat_edition`, `new_seat_limit`, `contract_term_num_months`, `sales_tax_amount`, `source_url` (required) |
| Churn (cancellation) | Did the change increase cancellations? | `Cancel Subscription` | Subscription Cancelled | `previous_arr`, `arr`, `arr_change`, `source` |
| Churn (reason) | What's driving cancellations? | `Churn Reason Selected` | Churn Reason Selected | — |

**Retention** is not a single event — measure it as a retention *curve* of the experiment's
**primary success action** (Dashboard §3), not as a business-guardrail event.

**Adjacent revenue events available** if the experiment touches them (same project, confirmed
active): `Trial Started`, `Nav Upgrade CTA Clicked`, `Add-on Purchased`, `Cancel Add-on`,
`Subscription Reactivated`, `Credit Threshold`. Add only when the diff touches that surface.

Each business guardrail chart is segmented by variant and annotated with the expected "must not
regress vs control" threshold. Before charting, re-confirm the event with `get_events`/`get_properties`
against `241072` (taxonomy can change).
