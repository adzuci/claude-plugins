# Paywall / Standard

## When to Use

Full-page component for **time-sensitive scenarios** — typically shown at the start of a flow when a user navigates to a feature that requires a plan upgrade.

**Best for:**

- User taps into a feature they don't have access to
- User isn't blocked by a limit — they simply don't have the feature yet
- A quick explanation helps them see why the feature is useful
- The moment benefits from a larger visual (product image or GIF)

**Do NOT use when:**

- The user hit a usage limit mid-action (use `modal-standard` or `modal-transactional`)
- The user needs detailed benefit bullets (use `modal-content-driven`)
- The gate appears as a small inline element (use `inline-standard`)

## Component Anatomy

| Component | Required | Max Chars | Notes |
|-----------|----------|-----------|-------|
| A. Image | Required | N/A | Product image, GIF, or custom illustration. Visuals that closely reflect the interface perform best. |
| B. Header | Required | 60 | Clearly highlight the value of gaining access. |
| C. Description | Required | 102 | Encourage users to upgrade by emphasizing value. |
| D. Primary CTA | Required | 30 | Prompt users to explore upgrade options. |
| Secondary CTA | Optional | 30 | Reserved for "Talk to Sales" action. Core teams only. |
| Proof line | Optional | 80 | Reinforce value with a stat or trust statement. Statistical claims must be confirmed by PMM. |

## Tone

**Encouraging, positive.**

The user just discovered something new. Focus on what they **can** do — not what they're missing. Make the feature feel valuable and the upgrade feel worth exploring.

## Header Patterns

- Lead with **what the user can accomplish**
- Make the benefit obvious
- Conversational tone

**Examples:**

- "Call contacts directly from Apollo to book more meetings"
- "Protect your account with multi-factor authentication"
- "Build precise prospect lists with advanced filters"

Rules:

- 60 character max
- Sentence case
- No period
- Lead with outcomes, not features

## Description Rules

- 1-2 short sentences (102 characters max)
- Focus on the **outcome** — what the user gets
- Don't repeat the header
- Keep it benefit-focused, not technical

**Pattern:** "[What the feature enables] to [meaningful result]."

**Examples:**

- "Use the Dialer to **call prospects directly** from Apollo and log every interaction."
- "Build precise prospect lists with **advanced filters** that save hours of research."

## Proof Line Rules

- **Optional** — include when a confirmed stat or relevant trust statement is available
- Can be an outcome-focused stat OR a trust/security/credibility statement
- Short and scannable (80 characters max)
- **Statistical claims must be confirmed by PMM** before including
- Non-statistical trust statements (security, compliance, reliability) don't require PMM sign-off

**Stat examples:**

- "Dialer users book 30% more meetings than those relying solely on email."
- "Teams using advanced filters find prospects 2x faster."

**Trust statement examples:**

- "Multi-factor authentication significantly reduces account takeover risk."
- "End-to-end encryption keeps your prospect data secure in transit."

**If no confirmed stat or relevant trust statement is available**, omit this component entirely. Do not fabricate or estimate.

## CTA Patterns

| CTA | Text | When to Use |
|-----|------|-------------|
| Primary | `Upgrade to [verb] [feature]` | Default for paywalls (e.g., "Upgrade to enable MFA", "Upgrade to use the dialer") |
| Primary (alt) | `View pricing plans` | When the gate isn't tied to a single feature |
| Primary (alt) | `Upgrade now` | When the upgrade path is clear |
| Secondary | `Talk to Sales` | Core teams only. |

## Do's and Don'ts

**Do:**

- Use a product image, GIF, or custom illustration that shows the feature interface
- Lead with outcomes, not features
- Keep the tone positive — the user is discovering, not being blocked
- Include proof lines only when backed by a PMM-confirmed stat or a relevant trust statement

**Don't:**

- Use long copy or multi-bullet benefit lists
- Include unconfirmed statistics or promises
- Use technical explanations of how the feature works
- Make the user feel like they're missing out (FOMO language)

## Placement

Fills the main content area of the page the user navigated to. The paywall replaces the feature content itself (e.g., settings tab, calls page). No blurred background; the paywall IS the page content.
