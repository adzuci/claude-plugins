---
name: email
description: |
  Lifecycle email architecture, email copy, in-app notification copy, and changelog.
  Produces segment definitions, trigger logic, sequence strategy, then writes actual
  email copy using MDS modules, in-app notifications, and a changelog entry — all in
  one pass. Requires foundation artifacts from /herald:foundation.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# herald:email

Lifecycle architecture + email copy + in-app notifications + changelog in one pass.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Tier Scoping

Read the `Tier` field from `campaigns/[slug]/brief.md` metadata.

- **T1/T2:** Full — lifecycle architecture, all email sequences, in-app notifications, changelog
- **T3:** 1 announcement email + in-app notification (if feature has UI) + changelog only. Skip architecture doc, nurture/activation sequences.
- **T4:** Changelog only + in-app notification if the launch changes UI. Skip everything else. For T4, foundation is not required — run directly after brief.

Read `${CLAUDE_PLUGIN_ROOT}/references/lifecycle-platform.md` for Customer.io vocabulary, canonical attributes and events, saved segments library, sync mechanisms, global holdout policy, **and the Email Modular Design System (MDS) module library**. Email body copy must be authored as named MDS modules, not free-form prose.
Read `${CLAUDE_PLUGIN_ROOT}/references/activation-platform.md` for in-app notification components, the Air Traffic Controller, the mandatory intake process, naming conventions, and feature gate types.

## Phase 1: Load and Orient

Read `campaigns/[slug]/brief.md` and the Artifacts table — verify foundation is done. Read `foundation/strategy.md` and `foundation/audience.md`. If foundation artifacts don't exist, tell the user to run `/herald:foundation` first and stop.

Assess lifecycle needs:

- Which sequences (announcement, nurture, activation)
- How many segments
- **Saved segment fit:** Check the saved segments library in `lifecycle-platform.md` — always start by filtering down from a saved segment rather than rebuilding from raw attributes
- Trigger complexity (scheduled sends vs. behavioral triggers using real CIO events)
- Whether in-app notifications are relevant (feature has UI surface?)
- Coordination with existing always-on programs (the Lifecycle team maintains the canonical list)
- Whether targeting free users (if yes, `lifecycle_eligible` 10% global holdout applies)

Outline your approach:

- Proposed segments, sequences, emails per sequence
- How triggers connect segments to sequences
- Which in-app components are relevant
- MDS module recipe for each email (based on its job — see recipes below)

**STOP.** Wait for go-ahead.

## Phase 2: Lifecycle Architecture

### Step 1: Segment map

**Check saved segments first.** Propose filtering down from existing saved segments when possible. Only fall back to raw-attribute construction when no saved segment fits — and flag for Lifecycle team review.

Present each segment with:

- One-line description and key criteria
- Base saved segment it filters from (or "built from raw attributes" with rationale)
- **Real Customer.io attribute names** from `lifecycle-platform.md`:
  - Plan: `team_status` (`free_access` / `paying` / `trial` / `churned`), `ZP_TEAM_EDITION`
  - Segment: `account_segment`, `Tier`
  - Persona: `is_persona_sales_leader`, `is_persona_sales_director_manager`, `primary_use_case`
  - Behavior: `last_logged_in`, `mailbox_linked`, `performed_search`, `OA_User_Activated`, `ZP_USER_PROSPECT_APP_XTL28D`
  - Integrations: `ZP_TEAM_SFDC_INTEGRATION`, `ZP_TEAM_HUBSPOT_INTEGRATION`, etc.
- Always-applied suppression: `unsubscribed = true` excluded; if free-user-targeted, `lifecycle_eligible = true`
- Estimated size and which sequences each segment enters

> **Do not invent attribute or segment names.** If you need a hook not in `lifecycle-platform.md`, propose the closest existing one and flag the gap.

### Step 2: Sequence architecture

For each sequence:

- Number of emails, timing between them
- Entry trigger using **real CIO event names** (`Activate Account`, `User Logged In`, `Mailbox Linked`, `Create Sequence`, `Feature Gate Shown`, etc.)
- Exit criteria (unsubscribe, conversion, activation, manual exclusion)
- Goal per email (awareness → how-to → proof → push)

### Step 3: Trigger flow

Present simplified flows:

```
[CIO event] → [Attribute condition] → [Enroll in sequence] → [Suppression rules]
```

### Step 4: Key decisions

Use AskUserQuestion for:

1. **Sequence scope:** "I'm proposing [N] sequences: [list]. Right scope?"
1. **Saved segment reuse:** "Is there a saved CIO segment that matches? If yes, point me at it so I can filter down."
1. **Trigger fit:** "Proposing triggers on [CIO events]. Right hooks, or are there other instrumented events?"
1. **Existing campaigns:** "Any currently-running programs for this audience that need coordination?"
1. **Holdout:** (free users only) "This will respect the 10% global holdout. Confirm reduced reach is OK."

**STOP.** Wait for approval.

## Phase 3: Email & In-App Copy

### Step 1: Email copy direction

For each email, present:

- Subject line A and B (drafts, noting what's being tested)
- Preview text direction
- **MDS module recipe** — which named modules the email uses, in order. Recipes by email job:
  - **Conversion / upgrade nudge:** Logo Header → Hero Card → Benefits Snapshot Card → Standalone CTA Card → Footer
  - **Multi-feature roundup:** Logo Header → Hero Image → Feature Card × N → Side Note Card → Footer
  - **Reasons-based upgrade:** Logo Header → Hero Card → Reasons List Card → Standalone CTA Card → Footer
  - **Single-message announcement:** Logo Header → Hero Card → Footer
  - **Activation / education:** Logo Header → Hero Card → Feature Card → Footer
  - Other → flag to Lifecycle team if no recipe fits
- CTA button text and destination

### Step 2: In-app copy direction

Map to Activation Platform components using the adoption-stage table in `activation-platform.md`. Default to **Side Tip** for standard feature releases — Modal reserved for P0 grouped launches.

For each in-app surface:

- **Component** (Side Tip / Contextual Tip / Tour / Announcement Banner / Announcement Modal / Wizard / Onboarding Hub task)
- **Adoption stage** (Awareness / Interest / Evaluation)
- **Notification name** following convention: `[Surface or context] - [Component type]`
- **Trigger context** and headline/body/CTA scoped to component constraints
- **ATC awareness** — flag if shipping into a busy notification window

For upgrade nudges / paywalls, use **Feature Gate** types from `activation-platform.md` (Modal/Standard, Modal/Content-driven, Modal/Transactional, Drawer/Standard, Inline/Standard, Inline/Badge, Paywall/Standard).

For **Changelog entry**: title, category, body direction.

### Step 3: Key decisions

Use AskUserQuestion for:

1. **Sender and tone:** "Should emails come from 'Apollo' or a person (e.g., PM name)?"
1. **CTA destinations:** "Where should CTAs link? Feature, help article, or landing page?"
1. **In-app component:** "Proposing [component(s)]. Confirm? Modals reserved for P0."
1. **Feature gate type:** (if plan-gated) "Proposing [type] from the 7 documented types. Correct?"

**STOP.** Wait for approval.

## Phase 4: Draft

### Step 1: Write lifecycle architecture

Write to `campaigns/[slug]/lifecycle/architecture.md`:

**Segment Definitions:** Each segment with name, description, base saved segment, criteria using real CIO attribute names, estimated size, sequences it feeds, exclusions.

**Trigger Logic:** Each trigger with real CIO event name, conditions (real attribute names), action, suppression. Frequency cap: 1 send/user/day (CIO default). If bypass needed, document and flag for Lifecycle team.

**Email Sequences:** Each sequence with emails, timing, segment, goal per email, subject line direction, CTA direction, A/B test plan.

**Open Coordination Questions** (always include): active always-on campaigns to coordinate with, send-time policy, attributes/events that need adding, frequency-cap bypass requests.

### Step 2: Write email copy

Write to `campaigns/[slug]/lifecycle/emails/`:

1. `announcement-sequence.md` — full copy per email using named MDS modules:

   ```
   ### Logo Header
   [Apollo wordmark renders automatically]

   ### Hero Card
   **Headline:** [8–12 words]
   **Body:** [1–3 sentences]
   **CTA button:** [2–4 words] → [destination]
   **Illustration:** [1-line description or "none"]

   ### Benefits Snapshot Card
   **Section heading:** [2–4 words]
   **Bullets** (3–5): [check-bulleted phrases]

   ### Standalone CTA Card
   **Headline:** [4–8 words]
   **CTA button:** [2–4 words] → [destination]

   ### Footer
   **Disclaimer** (optional): [fine print or "none"]
   ```

   Each Feature Card: image position (left/right), image description, headline (6–10 words), body (1–2 paragraphs), CTAs.
   Each Reasons List Card: heading, icon-bulleted reasons with bold lead-in + value sentence.
   Modules not used in an email are simply omitted (no placeholders).

1. `nurture-sequence.md` — same MDS module structure

1. `activation-sequence.md` — same MDS module structure

Subject lines earn opens through specificity. Body is scannable with one clear CTA. Every email has one job.

### Step 3: Write in-app copy

Write to `campaigns/[slug]/lifecycle/in-app-notifications.md`:

Each notification with: name (convention: `[Surface] - [Component type]`), component type, adoption stage, trigger/surface context, ATC awareness note, component-specific copy, prop value, analytics note ("Fires `Activation Notification Actioned` automatically"), required intake fields (Name, PRD, ERD, PM/Owner, Eng Lead, Analytics Lead, Need By Date — leave blank for team).

Feature gates (if applicable): gate type, interface (in-product/extension), feature name, headline/body/CTA, channel handoff note (`#growth-feature-gates` + DRI CC).

Changelog entry: title, category (New Feature / Improvement / Fix), body, CTA, destination.

### Step 4: Coherence review

Re-read the foundation artifacts (`strategy.md`, `audience.md`, and the brief). Scan every claim, stat, and audience reference in the draft against what the foundation actually says. Fix anything that contradicts, overstates, or misattributes.

### Step 5: Update artifact status

Update the Artifacts table in `campaigns/[slug]/brief.md`:

- Set "Lifecycle Architecture", "Announcement Emails", "Nurture Emails", "Activation Emails", and "In-App Notifications" to `done` with today's date

### Step 6: Summary

Tell the user: artifacts written with file paths, total emails with subject line variants, in-app components by type, feature gates if applicable with `#growth-feature-gates` handoff reminder. Remind that in-app notifications need Notification Intake Form submission and feature gates need their own intake. Flag any emails needing real metrics/quotes/screenshots.
