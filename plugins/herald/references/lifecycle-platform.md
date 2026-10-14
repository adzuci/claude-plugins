# Apollo Lifecycle Platform Reference

Source of truth for Apollo's lifecycle marketing platform: Customer.io. Captures the canonical attribute and event vocabulary, sync mechanisms, segmentation hooks, and operational rules so that `herald:email` proposes triggers and segments using names that actually exist in the platform.

> **As of:** February–April 2026. Verify specific attribute/event currency against the Customer.io Attributes and Events Definitions Notion DB before treating as live.
>
> **Source DB:** [Customer.io Attributes and Events Definitions](https://www.notion.so/apolloio/Customer-io-Attributes-and-Events-Definitions-247ab2b3b49680ca8786cbeeb7aa90ca) — when in doubt, query that DB; this doc is a curated subset.

______________________________________________________________________

## Platform

**Customer.io (CIO)** is Apollo's lifecycle marketing platform. All lifecycle email sequences and campaigns ship from CIO.

- **User identifier:** Apollo MongoDB user ID (`id` attribute), unique per CIO profile.
- **Sync source:** Apollo backend via `ZpWorkflows::ZenalyticsIdentifyUserLazyWorker` and `Zenalytics.formatted_user_info`.
- **Attribute batch limit:** 295 attributes per sync (CIO's hard limit is 300 — Apollo stays under).
- **Scope:** Events are tied to the user who performed the action. They are **not** propagated to teammates or to users affected via admin actions. Plan triggers and segments accordingly.

### Sync mechanisms

| Mechanism | Worker / job | Cadence | Use |
|-----------|--------------|---------|-----|
| Lazy worker | `ZpWorkflows::ZenalyticsIdentifyUserLazyWorker` | Triggered by user/team updates | Default attribute updates |
| Real-time worker | `ZpWorkflows::ZenalyticsIdentifyUserWorker` | Immediate | Time-sensitive updates |
| Snowflake batch (rETL, owned by Analytics) | — | Twice daily | Pushes calculated metrics into CIO |
| Saved Search sync | `CustomerIoSavedSearchSyncWorker` | Only for users created in last 30 days | Saved search preferences |
| Onboarding sync | `OnboardingService` | On task completion | Onboarding state |

**Implication:** Calculated metrics (e.g., rolling 7/28-day prospecting counts) lag by up to ~12 hours. Don't design triggers that assume real-time updates from Snowflake-derived attributes — use frontend events instead.

______________________________________________________________________

## Canonical attribute vocabulary

Use these exact names when proposing triggers, segments, or personalization tokens. This is a curated subset focused on attributes a launch lifecycle is likely to use; the full DB has 60+ attributes.

### Identity

| Attribute | Notes |
|-----------|-------|
| `id` | Apollo user ID, unique CIO identifier |
| `email` | User email |
| `name`, `last_name` | Full / last name |
| `country`, `state`, `city`, `region` | Geo / locale |
| `domain` | Team's primary email domain |
| `is_free_domain` | True if email is from a free provider (gmail, yahoo, etc.) |

### Plan, billing, segment

| Attribute | Values | Use |
|-----------|--------|-----|
| `team_status` | `free_access`, `paying`, `trial`, `churned`, `trial_over` | Primary plan-tier segmentation |
| `ZP_TEAM_STATUS` | Same as `team_status` (legacy ZP\_ prefix) | Reporting/analytics views |
| `ZP_TEAM_EDITION` | Subscription tier | Plan-level cuts (Free/Basic/Professional/Org) |
| `arr` / `ZP_TEAM_ACTIVE_ARR` | Number | ARR for the team |
| `inbound_arr` | Number | ARR specifically from the inbound product |
| `inbound_status` | `active`, `churned`, `never_purchased` | Inbound product adoption |
| `account_segment` | After GTM overrides | Authoritative segment for routing |
| `account_segment_default` | Original segment based on employee count | Pre-override segment |
| `Tier` | `1`, `2`, `3`, `4` | Market segment by company size/revenue |
| `seats_limit` | Number | Max seats on current plan |
| `ZP_TEAM_ENABLED_USER_COUNT` | Number | Occupied seats (legacy) |
| `sales_led` | Boolean | True if team was acquired via sales-led motion |
| `startup_program` | Program name | Enrolled in a startup program |

### Persona / role

| Attribute | Notes |
|-----------|-------|
| `user_role` | `Admin` / `Non-Admin` (permission set) |
| `ZP_USER_HAS_BILLING_PERMISSIONS` | Boolean |
| `is_persona_sales_leader` | Title-matched: VP Sales, Sales Director, Head of Sales, Sales Manager |
| `is_persona_sales_leadership` | Self-selected sales leadership |
| `is_persona_sales_director_manager` | Title-matched director/manager |
| `primary_use_case` | `outbound`, `inbound`, `enrichment`, `deal_execution` |
| `sales_department_size` | Self-reported |
| `company_size` | Self-reported |

### Behavior / engagement

| Attribute | Notes |
|-----------|-------|
| `last_logged_in` / `ZP_USER_LAST_LOGGED_IN` | Timestamp of most recent login |
| `mailbox_linked` / `ZP_USER_NUM_MAILBOX_LINKED` | Email connected? Count of linked mailboxes |
| `performed_search` | Boolean — has the user ever searched? |
| `gamification_score` | Points from platform engagement |
| `enrolled_onboarding`, `enrolled_gamification`, `classic_onboarding_tag` | Onboarding flow state |
| `dialer_minutes_available` | Remaining dialer minutes this billing cycle |
| `OA_User_Activated` | Boolean — currently defined as ≥4 `Record Actioned` events within the activation window. Key activation signal. |

### Prospecting / volume metrics (Snowflake-synced, ~12hr lag)

These follow a naming convention: `ZP_USER_…` for user-level, `ZP_TEAM_…` for team-level. Suffix `_XTL7D`/`_XTL28D` = trailing rolling window; `_XDL7D` = daily average; `_XTF28D` = trailing fixed window from user creation; `_NUM_TIMES_ALL_TIME` = lifetime.

| Attribute | Notes |
|-----------|-------|
| `ZP_USER_PROSPECT_APP_XTL7D` / `_XTL28D` | App-prospected count, last 7 / 28 days |
| `ZP_USER_PROSPECT_LI_XTL7D` / `_XTL28D` | LinkedIn-prospected count, last 7 / 28 days |
| `ZP_USER_PROSPECT_APP_XDL7D` / `_LI_XDL7D` | Daily average, last 7 days |
| `ZP_USER_PROSPECT_APP_NUM_TIMES_ALL_TIME` / `_LI_…` | Lifetime |
| `ZP_USER_EMAIL_SENT_XTF28D` | Emails sent in first 28 days after creation (fixed) |
| `ZP_USER_CONTACT_VERIFIED_APP_NUM_TIMES_ALL_TIME` | Lifetime contact verifications |
| `ZP_TEAM_PROSPECT_APP_XTL28D` | Team-level rolling 28-day prospecting count |
| `ZP_TEAM_EMAIL_SENT_XTL7D` / `_NUM_TIMES_ALL_TIME` / `_NUM_EMAILS_SENT_LAST30DAYS` | Team email volume |

### Integrations

| Attribute | Notes |
|-----------|-------|
| `ZP_TEAM_SFDC_INTEGRATION` | Salesforce connected |
| `ZP_TEAM_HUBSPOT_INTEGRATION` | HubSpot connected |
| `ZP_TEAM_OUTREACH_INTEGRATION` | Outreach connected |
| `ZP_TEAM_SALESLOFT_INTEGRATION` | SalesLoft connected |

### Suppression / experimentation

| Attribute | Notes |
|-----------|-------|
| `unsubscribed` | Hard suppression — never include in any sequence |
| `lifecycle_eligible` | **10% global holdout for new free users.** Used to measure lifecycle email impact on free→paid conversion. New launch sequences targeting free users **must** respect this attribute. |
| `Split Test - [A/B] JTBD Onboarding 2` | Example A/B variant assignment — pattern: `Split Test - [test name]` |

______________________________________________________________________

## Saved segments library

Customer.io contains a library of **saved segments** for common audiences (e.g., free users by activation state, paying users by tier, persona slices, integration cohorts). These are maintained by the Lifecycle team and reused across campaigns.

**Implication for launch sequences:**

- **Look for an existing saved segment first.** Before constructing a new segment from raw attributes, check whether there's a saved segment that already covers the launch audience (or a close superset that can be filtered down).
- **Filter down rather than rebuild.** If a saved segment is close but not exact, propose the saved segment as the base and add a small set of additional filters — don't recreate the whole segment from raw attributes.
- **Coordinate with the Lifecycle team** to identify the right starting saved segment. The full list of saved segments is maintained in Customer.io, not in this doc.
- **Fall back to raw attributes** only when no saved segment fits — and flag the new segment definition for Lifecycle team review.

______________________________________________________________________

## Canonical event vocabulary

Use exact event names when proposing triggers. Event names with spaces, brackets, or specific casing must be matched literally — CIO is case-sensitive.

### Activation / lifecycle milestones

| Event | Use as trigger for |
|-------|-------------------|
| `Activate Account` | Activation moment — completion of key onboarding milestones |
| `JTBD Onboarding - Task Completed` | Onboarding task progress |
| `User Logged In` | Login-based triggers (every login attempt — filter on success) |
| `Onboarding Survey Actioned` | Onboarding survey interaction |
| `Mailbox Linked` | Email account connected |

### Core feature usage (good for activation/nurture triggers)

| Event | Use |
|-------|-----|
| `Create Sequence` | Sequences feature first use |
| `Create Sequence Step` | Sequence depth |
| `Saved Search Saved` | Search persistence |
| `[App] Finder View Created` / `[App] Finder View Updated` | Finder view lifecycle |
| `List Created` | List creation |
| `Record Actioned: Add to List` | Records added to lists |
| `Record Actioned: Save Accounts` | Account saves |
| `Persona Created` | Persona/ICP setup |
| `Rule Created` | Workflow rules |
| `Email Sent` | Outbound send (any channel/source) |
| `Meeting Set` | Meeting booked |
| `Play Builder Opened` | Plays feature |
| `Send User Invitation Email` | Team invite sent |

### Premium / power-up / AI

| Event | Use |
|-------|-----|
| `Power-up CTA Clicked` | Premium feature CTA engagement |
| `Power-up Enrichment Completed` | Enrichment success |
| `AI Assist CTA Clicked` | AI feature engagement |
| `AI Content Displayed` | AI content shown to user |
| `Advanced Filters Used` | Premium filter usage (funding, revenue, technology, lookalikes, etc.) |

### Imports / data

| Event | Use |
|-------|-----|
| `[App] Import CSV` / `CSV Import Called` | CSV imports (started, in-progress) |
| `Download Record` | Record downloads |
| `Data Request Complete` | Generic data request completion |

### Extension

| Event | Use |
|-------|-----|
| `Chrome Extension Installed` | Install / upgrade |
| `Chrome Extension Uninstalled` | Uninstall (with `reason` if provided) |
| `Extension Used` | Any interaction |

### Monetization / gating

| Event | Use |
|-------|-----|
| `Feature Gate Shown` | User encountered a feature gate. Properties: `feature_name`, `gate_type`, `user_eligible`, `upgrade_required`, `experiment_id`. **Use as a trigger for upgrade nudge sequences.** |
| `plsmintrocall_landed` | PLSM (product-led sales motion) landing on in-app pricing page |
| `plsmintrocall_engaged` | PLSM engaged with Intercom — used to suppress re-engagement |

### Standard event properties (most events include these)

- `source` — UI location or trigger source
- `timestamp` — when the event occurred
- `user_id` — performer (NOT propagated to team)
- `success` — Boolean (on completion events)
- `error_type` — on failure
- `duration` — for timed processes
- `location`, `source_url`, `referrer` — UI / page context

______________________________________________________________________

## Holdout policy (lifecycle_eligible)

**10% of new free users are assigned to a global holdout** via the `lifecycle_eligible` attribute. This holdout exists to measure the impact of lifecycle emails on free→paid monetization.

**Implication for any new sequence targeting free users:**

- Filter the entry segment by `lifecycle_eligible = true`.
- Treat the holdout as sacred — do not bypass even for "important" announcement sends.
- Coordinate with the Lifecycle team if a launch genuinely requires reaching the holdout (e.g., legal/compliance announcements).

______________________________________________________________________

## Suppression rules

Always-applied suppression for any new sequence:

1. `unsubscribed = true` — never send.
1. `lifecycle_eligible = false` — exclude from free-user sequences (per holdout policy above).
1. **No conflicting active sequence** — coordinate with the Lifecycle team to confirm target users aren't already enrolled in an overlapping always-on program.
1. **De-enrollment on conversion** — if a user converts (free → paid) mid-sequence, exit nurture and enter the appropriate paid-customer flow.

______________________________________________________________________

## Frequency cap

**Global default: 1 send per user per day.** Customer.io enforces this cap across all lifecycle programs.

- Individual campaigns may be configured to **bypass the cap** with explicit Lifecycle team approval. Bypasses are documented per-campaign — there is no general "ignore the cap" lever.
- New launch sequences should assume the 1/day cap applies. If the launch genuinely needs to send more than once on a given day to a user (e.g., a paired announcement + activation push), flag the bypass request to the Lifecycle team rather than designing around the cap silently.
- Coordination is still required to avoid same-day collision with other active campaigns the user might be enrolled in.

______________________________________________________________________

## Email Modular Design System (MDS)

Apollo is rolling out a **Modular Design System (MDS)** for Customer.io emails (led by Aaron). MDS provides a standardized library of email **modules** that compose into branded emails consistently across the platform. New launch emails should be authored as a sequence of named MDS modules rather than free-form prose, so the handoff to whoever assembles the email in CIO is mechanical.

### Module library (observed in production emails, April 2026)

| Module | Purpose | Content shape | Notes |
|---|---|---|---|
| **Logo Header** | Top of every email | Centered Apollo wordmark | May include a "Log in" link top-right for nurture/upgrade emails |
| **Hero Card** | Primary message + primary CTA | Tinted background card (often light purple) with headline + 1–3 sentence body + single CTA button (dark/black) + optional illustration on the right | Carries the launch's main message and primary CTA |
| **Hero Image** | Visual-led primary | Full-width image (typically a product screenshot), no card overlay | Alternative to Hero Card for product-update emails where the image IS the hook |
| **Benefits Snapshot Card** | Quick value proof | White bordered card with section heading + check-bulleted feature list (3–5 bullets, each one short phrase) | Used in conversion/upgrade emails |
| **Reasons List Card** | Multi-point persuasion | Heading (e.g., "5 reasons to upgrade:") + icon-bulleted list with bold lead-ins followed by a short value sentence | Used for upgrade nudges with multiple value points |
| **Feature Card** | One feature spotlight | Headline + 1–2 paragraph body (often with inline bullet list) + 1–2 CTA buttons (e.g., "Try it now" + "Learn more") + adjacent product screenshot (image-left or image-right) | Stack multiple per email for product round-ups |
| **Standalone CTA Card** | Secondary closer | White bordered card with short headline (+ optional body) + button (often yellow for visual contrast with Hero CTA) | Used as a closer below the main message |
| **Side Note Card** | Supplementary nudge | Small text + secondary CTA | Used to point at help center, release notes, archive, etc. |
| **Footer** | Required closer | Optional fine-print disclaimer (e.g., "\*Annual plan required") + social icons + Manage preferences / Unsubscribe links + copyright + Apollo address + Apollo wordmark | Always present |

### Common email recipes

| Email type | Module sequence |
|---|---|
| Conversion / upgrade nudge | Logo Header → Hero Card → Benefits Snapshot Card → Standalone CTA Card → Footer |
| Multi-feature roundup / product update | Logo Header → Hero Image → Feature Card × N → Side Note Card → Footer |
| Reasons-based upgrade | Logo Header → Hero Card → Reasons List Card → Standalone CTA Card → Footer |
| Single-message launch announcement | Logo Header → Hero Card → Footer |
| Activation / education | Logo Header → Hero Card → Feature Card → Footer |

### Implications for `herald:email`

- Author each email's body as a sequence of **named MDS modules** drawn from the library above.
- Pick a recipe based on the email's job, then fill the modules with copy.
- Use the actual module names (`Hero Card`, `Benefits Snapshot Card`, etc.) — not generic terms like "block" or "section" — so the handoff to CIO assembly is unambiguous.
- The MDS module library is in active development. If a launch needs a layout that doesn't fit any module above, **flag it to Aaron / the Lifecycle team** rather than designing around it. New modules will be added as the system matures.

______________________________________________________________________

## What this reference does NOT cover

The Customer.io DB has additional attributes and events not curated here. When proposing a trigger or segment that isn't in this doc, query the source DB:

- [Customer.io Attributes and Events Definitions](https://www.notion.so/apolloio/Customer-io-Attributes-and-Events-Definitions-247ab2b3b49680ca8786cbeeb7aa90ca)

If the attribute or event you want doesn't exist, **flag it** and propose the closest existing one — do not invent names. Inventing trigger names that don't exist breaks the lifecycle handoff to the team that builds the sequence in CIO.

______________________________________________________________________

## Known unknowns / open questions

These should be confirmed with the Lifecycle team before relying on them in a launch design:

- **Send-time policy:** Fixed time windows? Per-user send-time optimization?
- **Active always-on programs:** The Lifecycle team maintains the canonical list of currently-running always-on campaigns (onboarding, activation, expansion, churn-save). New launch sequences should coordinate with this list to avoid collision — the list lives outside this repo.
- **Approval flow:** Who reviews and approves new sequences before activation?
- **Saved segment list:** Customer.io's saved segment library — point at the relevant segment for a given launch audience (see Saved segments library section above).
