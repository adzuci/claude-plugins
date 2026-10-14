# Modal / Standard

## When to Use

Overlay component for **time-sensitive scenarios** — when a user reaches a usage limit or tries to access a feature not included in their plan. Triggered within the user flow.

**Best for:**

- User has hit a credit, count, or usage cap
- Feature isn't included in user's current plan
- Moment is simple — not part of a larger workflow
- A quick explanation is sufficient (no bullet lists needed)

**Do NOT use when:**

- The user needs detailed benefit explanations (use `modal-content-driven`)
- A purchase/credit transaction is involved (use `modal-transactional`)
- The feature is entirely blocked at page level (use `paywall-standard`)

## Component Anatomy

| Component | Required | Max Chars | Notes |
|-----------|----------|-----------|-------|
| A. Image | Required | N/A | Illustration, product image, or GIF. Visuals that closely reflect the interface perform best. |
| B. Header | Required | 35 | Clearly communicate that a usage limit has been reached or that the feature is not available on the current plan. |
| C. Description | Required | 102 | Encourage users to upgrade by emphasizing the value they'll unlock. |
| D. Primary CTA | Required | 20 | Prompt users to explore upgrade options or pricing. |
| Secondary CTA | Optional | 20 | Reserved exclusively for "Talk to Sales" action. Displayed only for core teams. Coordinate with Conversion and Sales teams first. |

## Tone

**Clear, confident, helpful.**

The user hit a limit or found a locked feature. Be direct about what happened and helpful about what they can do. Don't dramatize or over-sell — just explain clearly and point the way forward.

## Header Patterns

Use slot-based patterns. Pick the one that fits the context:

- **Usage-based limit:** "You've hit your [feature] limit"
- **Plan-based lock:** "[Feature] isn't included in your plan"
- **Variant (usage):** "You've reached your [feature] limit"
- **Variant (plan):** "[Feature] requires [Plan name]"

Rules:

- 35 character max
- Sentence case
- No period
- State the situation, not the ask

## Description Rules

- 1-2 lines max (102 characters)
- Start with "Upgrade now to..." or "Upgrade to [plan] to..."
- Explain the benefit — what the user gets by upgrading
- Focus on the **outcome**, not the feature name
- **Bold the specific upgrade benefit** when possible
- End with a period if it's a complete sentence

**Pattern:** "Upgrade now to **[specific benefit]** and [secondary outcome]."

**Examples:**

- "Upgrade now to **select unlimited contacts** and build targeted lists faster."
- "Upgrade to Professional to **unlock advanced filters** for more precise searches."

## CTA Patterns

| CTA | Text | When to Use |
|-----|------|-------------|
| Primary | `View pricing plans` | Default for most standard modals |
| Primary (alt) | `Upgrade now` | When the upgrade path is a single plan |
| Secondary | `Talk to Sales` | Core teams only. Coordinate with Conversion and Sales first. |

## Do's and Don'ts

**Do:**

- Pair with an illustration, product image, or GIF to support the copy
- Keep it brief — this is the "quick hit" modal
- Match the image to the feature being gated

**Don't:**

- Use long copy or multi-bullet explanations of benefits (use `modal-content-driven` instead)
- Include more than 2 sentences in the description
- Use the secondary CTA without team coordination

## Placement

Center of screen, overlaying main content. Standard feature gate component applies blurred background by default.
