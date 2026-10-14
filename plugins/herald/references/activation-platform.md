# Apollo Activation Platform Reference

Source of truth for in-app notification surfaces and feature gates. Captures the actual components, the Air Traffic Controller (ATC), the mandatory intake processes, naming conventions, and analytics so that `herald:email` proposes in-app copy and feature-gate copy that fits the real platform.

> **As of:** February–April 2026. The Activation Platform and Feature Gate guidelines are maintained in Notion; verify component status before treating as live.
>
> **Sources:**
>
> - [Activation Platform Documentation](https://www.notion.so/apolloio/Activation-Platform-Documentation-11cab2b3b4968029b6c2ddcca41b4b70)
> - [Notification Intake DB](https://www.notion.so/apolloio/135ab2b3b4968059bf20e674b812366a)
> - [Feature gate guidelines](https://www.notion.so/apolloio/Feature-gate-guidelines-2b7ab2b3b49680db9d81f7035807296b)

______________________________________________________________________

## Mandatory intake — read first

> **All notifications must go through the intake process.** No in-app notification ships without a Notification Intake Form submission and approval.

- **Where:** Notification Intake DB
- **Status flow:** Requirements being drafted → Submitted → In Review → Approved / Rejected / Sent back
- **Required fields:** Name, PRD, ERD (engineering requirements doc), PM/Product Owner, Eng Lead, Analytics Lead, Need By Date, Product Dev Stage
- **Implication for Herald:** Every in-app notification artifact `herald:email` produces is an *input* to this intake process, not a finished spec. Generate copy and structure that maps cleanly to the form fields.

Feature gates have a parallel intake — see the Feature Gates section below.

______________________________________________________________________

## Product Adoption Process — pick the right surface for the stage

Apollo's Activation Platform maps components to the user's adoption stage. Choose the surface that matches where the target user is in their journey, not the one that's most attention-grabbing.

| Stage | Goal | Components available |
|-------|------|---------------------|
| **1. Awareness** | Spark curiosity, drive CSAT signal that product is improving | Onboarding Hub, Announcement Banner, Announcement Modal |
| **2. Interest** | Just-in-time nudges when feature becomes relevant | Contextual Tip, Side Tip, Email Marketing |
| **3. Evaluation** | Communicate the value prop and the next best action | Tour, Wizard, Empty State *(not yet implemented)* |
| **4. Trial** | Let the user experience value | Activation Platform offers little here — focus on the FTUX |
| **5. Adoption** | Land the aha moment | Activation Platform offers little here |

**Default for a standard feature launch:** Side Tip + targeted Contextual Tips + Email Marketing. Use the Banner or Modal *only* when justified (see component details).

______________________________________________________________________

## Components

### Onboarding Hub / Welcome pages

- **Stage:** Awareness
- **Use:** Tasks for new users on first login. Feature inclusion happens via "recommended setup tasks" or use cases.
- **For a launch:** Propose new tasks/use cases to the Onboarding team — does not ship from a feature launch directly.

### Announcement Banner

- **Stage:** Awareness
- **Surfaces:** Designated app-wide locations (top of app, Searcher, ID pages)
- **Use:** Brief promotional message with **one** clear CTA. Best when engagement is **time-sensitive** (expiring promo, scheduled webinar).
- **Avoid:** Non-time-sensitive content. Respect where users are in their journey.
- **Component prop:** `bannerName`
- **ATC controlled:** Yes (see ATC section)
- **Engineering:** [`AnnouncementBanner` in Storybook](https://app-master.preview.staging-gcp.apollo.io/docs/?path=/docs/design-system-2-0-patterns-notifications-announcement-banner--docs)

### Announcement Modal

- **Stage:** Awareness
- **Use:** Full-screen interstitial that requires interaction. **Reserved for very significant P0 releases.** Coordinate with other squads to share the modal slot.
- **For standard feature releases:** Use Side Tip instead. Do not propose a Modal unless the launch is genuinely a P0 grouped release.
- **Component prop:** `modalName`
- **ATC controlled:** Yes
- **Engineering:** [`AnnouncementModal` in Storybook](https://app-master.preview.staging-gcp.apollo.io/docs/?path=/docs/design-system-2-0-patterns-notifications-announcement-modal--docs)

### Contextual Tip

- **Stage:** Interest
- **Use:** Popup attached to a specific element. Surfaces a feature **just-in-time** when the user signals it could be valuable. Best for new entrypoints across the app.
- **Component prop:** `contextualTipName`
- **ATC controlled:** Yes
- **Engineering:** [`ContextualTip` in Storybook](https://app-master.preview.staging-gcp.apollo.io/storybook/?path=/docs/design-system-2-0-patterns-notifications-contextual-tip--docs)

### Side Tip

- **Stage:** Interest
- **Surface:** Bottom-right corner of screen
- **Use:** Feature releases, promotions, product feedback. **One** clear CTA. Once dismissed, never shown again to that user.
- **Default for standard feature launches.** This is the recommended component for "we shipped a feature, here's how to find it."
- **Component prop:** `sideTipName`
- **ATC controlled:** Yes
- **Engineering:** [`SideTip` in Storybook](https://localhost:9001/?path=/docs/design-system-2-0-patterns-notifications-side-tip--docs)

### Tour

- **Stage:** Evaluation
- **Use:** Sequence of popups walking the user through a page or flow. Used on first visit to a surface, or after a major redesign.
- **Constraint:** **≤4 steps.** More than 4 makes the user feel overwhelmed and projects an overly complex product.
- **Component prop:** `tourName`
- **ATC controlled:** Yes
- **Engineering:** [`Tour` in Storybook](https://localhost:9001/?path=/docs/design-system-2-0-patterns-notifications-tour--docs)
- **Replay support:** Tours can be made replayable from the Help sidebar via `userInitiated` (bypasses ATC rules).

### Wizard

- **Stage:** Evaluation
- **Use:** Full-page modal multi-step setup flow. Each step is a form; subsequent steps can branch on prior input. Goal: simplify what would otherwise be a complex configuration.
- **Tracking:** `Setup Wizard Page View` and `Setup Wizard Click` events with `name`, `surface`, `progress`, `step`, `substep` properties.
- **Engineering:** [`Wizard` in Storybook](https://localhost:9001/?path=/docs/squad-specific-components-growth-activation-wizard--docs) — uses `useManagedWizard` hook.

### Empty State

- *Not yet implemented.*

### Email Marketing

- **Stage:** Interest
- **Use:** Reaches users outside their immediate workflow with targeted insights/guidance. The complementary channel to in-app nudges.
- **Intake:** Submit via the same Notification Intake Form (lifecycle email is part of Activation Platform's purview). Hand off to Lifecycle team.
- **For Herald:** Email Marketing is `herald:email`'s primary output. The Activation Platform context is the in-app component sections above plus this email channel.

______________________________________________________________________

## Air Traffic Controller (ATC)

The ATC is the system that decides which popup notifications actually display. Critical to understand because **rendering a notification ≠ showing a notification.**

### ATC-controlled components

- Tour
- Contextual Tip
- Side Tip
- Announcement Modal

(Banners and Wizards have their own surface/lifecycle and aren't controlled by ATC in the same way.)

### How the ATC decides

1. **Type prioritization** — Tours rank above Tips because they've been shown to deliver more value.
1. **Round-robin on ties** — Same-priority notifications take turns.
1. **Cooldown** — After any notification shows, others wait. Configurable per provider; off-by-default in dev.
1. **Active-notification block** — If one notification is currently showing, others wait.
1. **Dismissal persistence** — Dismissed notifications are stored in the `Dismissal` Mongo collection and not shown again. Opt-out via `shouldSaveDismissal={false}` (rare).
1. **`userInitiated` bypass** — When the user explicitly invokes a notification (e.g., replays a tour from Help), all ATC rules are bypassed.

### Implication for launch copy

- **You may have only one shot.** A launch competing with other Awareness/Interest notifications may be deferred or lose its slot. Design copy that's worth the slot.
- **No "follow-up" reminders by default.** Once dismissed, the notification doesn't return. Any "second touch" needs to be a different component or an email.
- **Launch order matters.** If a launch ships during a busy notification window, propose either a delayed activation or coordinate with other teams to back off.

______________________________________________________________________

## Notification naming convention

From real entries in the Notification Intake DB, the convention is:

> **`[Surface area or trigger context] - [Component type]`**

Real examples:

- `Top Nav Credit Usage - Tour`
- `Linkedin New Search Page tour`
- `NavSwitcher Product Tour`
- `Scoring Config and Score Preview tours`
- `Task recommendation tab sidetip`
- `New context center contextual sidetip`
- `Outdated Extension Version Sidetip`
- `CRM setup Invite Teammate sidetip nudge`
- `Website Visitors Limit Reached Banner`
- `Out of credits banner`
- `Expiring credits nudge banner`
- `Dialer / Advanced Dialer Dec Launch Banners`
- `12/8 Deliverability Webinar Banner`

**Use this convention** in `herald:email` in-app outputs. Names should be human-readable, place-specific, and end in the component type so the ATC + analytics naming stays consistent.

______________________________________________________________________

## Analytics — automatic, no extra instrumentation

All Activation Platform components fire the `Activation Notification Actioned` Customer.io event with consistent properties. Do **not** propose additional event instrumentation for these components — it ships for free.

| Property | Value per component |
|----------|---------------------|
| `notification_type` | `Announcement Banner Event`, `Announcement Modal Event`, `Contextual Tip Event`, `Side Tip Event`, `Tour Event` |
| `[component]_name` | `bannerName` / `modalName` / `contextualTipName` / `sideTipName` / `tourName` |
| `action` | Component-specific — see below |

**Standard `action` values:**

- Banner / Modal / Side Tip: `viewed`, `clicked`, `dismissed`
- Contextual Tip: `viewed`, `closed`
- Tour: `opened`, `next`, `previous`, `go-to-step`, `dismissed`, `finished`

The Wizard has its own events: `Setup Wizard Page View` and `Setup Wizard Click`.

______________________________________________________________________

## Feature gates

Feature gates are product components that control access to features based on plan or usage limits. They communicate value and provide an upgrade path.

> **Source:** [Feature gate guidelines](https://www.notion.so/apolloio/Feature-gate-guidelines-2b7ab2b3b49680db9d81f7035807296b)
>
> **Discussion channel:** `#growth-feature-gates` (Slack)

### The 7 documented feature gate types

| Name | Interface | Use |
|------|-----------|-----|
| **Modal / Standard** | In-product | Standard upgrade gate — most common. |
| **Modal / Content-driven** | In-product | Content-rich upgrade gate (more education, less hard sell). |
| **Modal / Transactional** | In-product | Transactional gate (e.g., credit purchase, seat add). |
| **Drawer / Standard** | Extension | Drawer-based gate inside the Chrome Extension. |
| **Inline / Standard** | In-product | Inline gate within a page or flow (no overlay). |
| **Inline / Badge** | In-product | Lightweight badge marking a feature as gated. |
| **Paywall / Standard** | In-product | Hard paywall blocking access to a premium surface. |

Each type has its own Figma file and content guidelines in the `Types` database under the Feature gate guidelines page. Reference those before drafting copy.

### Feature gate process

1. **Choose a feature gate type** from the table above. Follow the type-specific guidelines plus legal guidelines.
1. **Submit for review** via the feature gate intake form. Share the design in `#growth-feature-gates` and cc the DRIs (PM, Product Design, Engineering, Content Design, Analytics).
1. **Develop** following engineering guidelines.

### Feature gate trigger event

Feature gates fire the `Feature Gate Shown` Customer.io event with properties:

- `feature_name`
- `gate_type`
- `user_eligible`
- `upgrade_required`
- `experiment_id` (if part of an A/B test)

This event is the canonical hook for upgrade nudge sequences in `herald:email`.

______________________________________________________________________

## What Herald skills should produce vs. defer

| Output | Herald produces | Team owns |
|--------|----------------|-----------|
| In-app notification copy + structure | Yes — per component, ready to drop into intake form | Final UX review, ATC slotting |
| Notification name (using the convention above) | Yes | — |
| Notification component selection (Banner / Side Tip / Tour / etc.) | Yes — based on adoption stage | — |
| Analytics requirements | No (fires automatically) | — |
| Feature gate type selection | Yes — based on the 7 documented types | Content design + Growth team review |
| Feature gate copy | Yes — per type's content guidelines | Content design review |
| Engineering implementation | No | Engineering |
| ATC slotting / launch coordination | No — flag conflicts in the execution plan in brief.md | Growth team |
