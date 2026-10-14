# Modal / Transactional

## When to Use

Overlay component for **time-sensitive scenarios** featuring concise messaging and an order summary. Triggered within the user flow.

**Best for:**

- User doesn't have enough credits to complete an action
- User has reached a usage limit mid-action
- Feature isn't included in their plan and continuing requires a purchase
- An order summary or credit count is shown alongside the copy

**Do NOT use when:**

- No transaction is involved (use `modal-standard` or `modal-content-driven`)
- The feature is entirely blocked at page level (use `paywall-standard`)

## Component Anatomy

| Component | Required | Max Chars | Notes |
|-----------|----------|-----------|-------|
| A. Image | Required | N/A | Illustration that complements the message. |
| B. Header | Required | 35 | Clearly communicate insufficient credits, usage limit reached, or feature not available. |
| C. Description | Required | 102 | Communicate the action attempted and encourage purchase/upgrade. |
| D. Primary CTA | Required | 20 | Prompt users to buy more credits. |
| Secondary CTA | Optional | 20 | Prompt users to explore upgrade options or pricing. |
| Tertiary CTA | Optional | 20 | Reserved for "Talk to Sales" action. Core teams only. |

## Tone

**Clear, practical, transparent.**

The user tried to do something and got blocked. Be straightforward about what happened, what they need, and how to get it. No fluff — this is a transactional moment.

## Header Patterns

- **Credit-based:** "Not enough credits"
- **Feature-based:** "[Feature name] isn't included in your [plan name] plan"
- **Usage-based:** "You've used all your [feature] credits"

Rules:

- 35 character max
- Sentence case
- No period
- State the issue directly

## Description Rules

- 1-2 sentences max (102 characters)
- Lead with what the user tried to do, then what they need
- **If upgrading:** "Upgrade to [do something new] to [get a meaningful result]."
- **If buying credits:** "You tried to [action], but don't have any credits left. Buy more credits to continue."

**Examples:**

- "Upgrade to **send unlimited emails** and reach more prospects."
- "You tried to enrich 50 contacts but don't have enough credits. Buy more to continue."

## CTA Patterns

| CTA | Text | When to Use |
|-----|------|-------------|
| Primary | `Buy credits` | Credit purchase flow |
| Primary (alt) | `Purchase credits` | Credit purchase flow (variant) |
| Primary (upgrade) | `Upgrade to [plan name]` | Plan upgrade flow |
| Primary (upgrade alt) | `Upgrade now` | Plan upgrade flow (variant) |
| Secondary | `View pricing plans` | When primary is credit-specific, secondary shows plan options |
| Tertiary | `Talk to Sales` | Core teams only. |

## Do's and Don'ts

**Do:**

- Include a brief order summary when buying credits or an add-on
- Pair with a simple illustration
- State the issue first, then the action
- Use short, direct sentences

**Don't:**

- Use long copy or multi-bullet explanations
- Obscure the transaction — be transparent about what the user is buying
- Use more than 2 sentences in the description
- Skip the order summary when a purchase is involved

## Placement

Center of screen, overlaying main content.
