# Modal / Content-Driven

## When to Use

Overlay component for **time-sensitive scenarios** with additional space to highlight benefits and supporting copy. Triggered within the user flow.

**Best for:**

- User is in the middle of a workflow and a simple limit message would feel abrupt
- User has made progress or is near a milestone
- The value of upgrading needs more explanation than a single sentence
- User needs help understanding what to do next

**Do NOT use when:**

- A brief limit message is sufficient (use `modal-standard`)
- A credit/purchase transaction is involved (use `modal-transactional`)
- The feature is entirely blocked at page level (use `paywall-standard`)

## Component Anatomy

| Component | Required | Max Chars | Notes |
|-----------|----------|-----------|-------|
| A. Image | Required | N/A | Illustration that complements the message. |
| B. Header | Required | 35 | Clearly communicate limit reached or feature not available. |
| C. Description | Required | 51 | Encourage users to upgrade by emphasizing value. |
| D. Bullets | Required | 47 each | Reinforce header and description with key benefits. Can include checkmarks or icons. 2-3 bullets max. |
| E. Primary CTA | Required | 20 | Prompt users to explore upgrade options. |
| Secondary CTA | Optional | 20 | Reserved exclusively for "Talk to Sales" action. Core teams only. |

## Tone

**Motivating, positive, benefit-led.**

The user is mid-workflow. Acknowledge where they are, show them what's possible, and make the upgrade feel like a natural next step — not a roadblock.

## Header Patterns

Headers should reflect where the user is in the workflow:

- "Get more from your [workflow area]"
- "Take your [feature] further"
- "You've hit your [feature] limit"
- 1-2 short sentences or phrases

Rules:

- 35 character max
- Sentence case
- No period
- Reflect the user's current workflow context

## Description Rules

- **One sentence only** (51 characters max)
- Clear, helpful framing
- Sets up the bullets that follow
- Don't repeat the header

**Pattern:** "[Clear statement about what upgrading enables]."

**Examples:**

- "Here's what you can do with a Professional plan."
- "Unlock powerful tools to grow faster."

## Bullet Rules

- **Benefit-led** — lead with outcomes, not features
- **One idea per bullet**
- 2-3 bullets max
- Short — one line each (47 characters max per bullet)
- **No punctuation** at the end of bullets
- Can use checkmarks or icons as list markers

**Examples:**

- "Select unlimited contacts from any list"
- "Export up to 10,000 records at once"
- "Access advanced search filters"

## CTA Patterns

| CTA | Text | When to Use |
|-----|------|-------------|
| Primary | `Upgrade to [plan name]` | When the target plan is known |
| Primary (alt) | `Upgrade now` | When the target plan varies |
| Primary (add-on) | `Get add-on` | When the unlock is an add-on, not a plan |
| Secondary | `Talk to Sales` | Core teams only. |

## Do's and Don'ts

**Do:**

- Pair with a simple illustration to reinforce the message
- Make bullets scannable — users skim these
- Focus on what the user can **do next**
- Lead with outcomes in every bullet

**Don't:**

- Use short, concise copy only (that's `modal-standard` — this format needs the expanded content)
- Repeat the same benefit in header, description, and bullets
- Use more than 3 bullets
- End bullets with periods or other punctuation

## Placement

Center of screen, overlaying main content.
