# Inline / Standard

> **[PROVISIONAL — guidelines pending]**
> Official design and content guidelines for Inline surfaces are not yet finalized. The guidance below is inferred from general Apollo patterns and style rules. Confirm with the design team before shipping.

## When to Use

Inline upgrade prompt embedded **within the page layout** — not an overlay. Appears as a small element baked into the broader UI, typically next to or replacing a disabled/locked feature element.

**Best for:**

- Small, contextual upgrade nudges within a page
- Features where a specific UI element is hidden or disabled
- Situations where a modal would be too disruptive to the flow
- Persistent prompts that remain visible as the user works

## Component Anatomy (Provisional)

| Component | Required | Max Chars | Notes |
|-----------|----------|-----------|-------|
| Header/Label | Required | 25 | Shorter than modal headers due to inline footprint. State what's locked. |
| Description | Optional | 80 | Brief explanation if space allows. May be omitted in tight layouts. |
| CTA | Required | 15 | Compact CTA — shorter than modal CTAs to fit inline. |

> **Note:** Character limits are estimated based on typical inline component sizes. Actual limits will depend on the specific implementation and layout context.

## Tone (Provisional)

**Subtle, informative, non-disruptive.**

Inline prompts live alongside other content. They should feel like a natural part of the page — not an advertisement. Keep the tone factual and helpful.

## Header Patterns (Provisional)

Inline headers are shorter and more label-like:

- "[Feature] (Pro)"
- "Upgrade to access"
- "[Feature] — upgrade required"

## Description Rules (Provisional)

- One short sentence max (if space allows)
- May be omitted entirely in compact layouts
- Focus on what the feature does, not the upgrade pitch

## CTA Patterns (Provisional)

| CTA | Text | When to Use |
|-----|------|-------------|
| Primary | `Upgrade` | Default compact CTA |
| Primary (alt) | `Learn more` | When space is limited or legal risk is elevated |
| Primary (verbose) | `View plans` | When slightly more space is available |

## Expected Differences from Modal Surfaces

- **Smaller footprint** — inline prompts share space with other UI elements
- **No image component** — typically text-only or icon + text
- **Persistent visibility** — unlike modals, inline prompts don't disappear on close
- **Lower interruption** — the user can continue working while the prompt is visible
- **Potentially different analytics events** — uses `Inline Upgrade Prompt Shown` and `Inline Upgrade Prompt Clicked` (not Feature Gate events)

## Important Notes

- This surface type's guidelines are **provisional** and should be reviewed by the design team before production use
- Inline prompts vary significantly by context — always check the specific Figma design for the implementation
- Character limits will depend on the layout; the limits above are conservative estimates
- When guidelines are finalized, this file will be updated to match official specifications
