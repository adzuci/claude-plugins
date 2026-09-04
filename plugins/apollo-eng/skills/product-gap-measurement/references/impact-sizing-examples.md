# Impact Sizing Examples

Use these examples as measurement patterns. Refresh live counts before making a decision; do not reuse old numbers as current evidence.

## Trial Credits Bait-And-Switch Plan Page

Use this as the canonical Notion/support-rotation ideation example because it has both real support pain and measurable product exposure.

Enterpret sizing:

- Query strict Intercom records about trial credits, billing surprise, plan-page expectations, reduced credits after plan change, refund requests, and blocked work.
- Compare against a broader trial-plus-credits query only to find adjacent themes; broad queries can be noisy and include sales calls.
- Report support volume, actual record window, top themes, severity language, and representative record links.

Amplitude exposure and journey:

- Exposure denominator: `Trial Started`.
- Credit journey events: `Credits Bar Button Clicked`, `Current Credit Usage Page Viewed`, and `Credit Usage History Page Actioned`.
- Support intent: `Contextual Sidebar Event` where `type = click`, `cta = Talk to support`, and `resourceType = intercom`.
- Business/action outcome: `Start Subscription`, upgrade, or plan-selection events when available.
- Segment by `gp:tier`, `gp:plan`, `gp:seat_edition`, role, or closest available property.

Claim boundary:

- Enterpret can support `support-severity-backed` claims.
- Amplitude can support `product-exposure-backed` and `behavior-baseline-backed` claims.
- Do not claim support reduction until a post-fix Enterpret or Intercom trend shows reduced support demand.

Good PR or ticket acceptance criteria:

- Defines the confusing plan-page or credits surface.
- Identifies the exposed cohort and the credit-check path.
- Tracks the recovery action the UI expects users to take.
- Plans a post-fix readout for exposed users, repeat credit checks, support-intent clicks, and upgrade/subscription behavior.

## Agent-Mediated Or Weak-Telemetry Gaps

Do not force an Amplitude funnel when the product gap happens mostly inside an agent, background process, or support conversation without clean product events.

Use Enterpret as the primary sizing layer, then use Amplitude only for the closest exposure proxy. If the proxy is weak, label the result as an instrumentation gap and recommend the smallest event needed for future measurement.

## Immediate Pain

Scraper/TOS block:

- Product PR: `https://github.com/apolloio/leadgenie/pull/93453`
- Tracking PR: `https://github.com/apolloio/leadgenie/pull/93790`
- Dashboard: `https://app.amplitude.com/analytics/apollo-io/dashboard/jcz6ul3p`

Use these links as illustrative patterns only. Re-check PR state, dashboard
availability, event counts, and date windows before citing evidence.

This is a good support-click case because pain is immediate. A short exposure to `Talk to support` window can be directionally meaningful when joined with product context.

## Hybrid Pain

Blocked sequence task badge:

- PR: `https://github.com/apolloio/leadgenie/pull/95135`
- Good exposure event: `Contact Blocked On Task Step Shown`
- Missing recovery action example: `Contact Blocked On Task Step Tasks Link Clicked`

This is hybrid because the user sees an immediate UI exposure, but support pain may depend on whether they understand and complete recovery.

## Delayed Pain

LinkedIn sequence confusion:

- Avoid short `exposure -> Talk to Support` claims.
- Prefer exposed cohort plus 7-day or 14-day topic-specific support trend.
- Treat support-click funnels as directional unless conversations are joined or the support topic is narrow.
