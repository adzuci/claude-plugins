# Drawer (Extension)

> **[PROVISIONAL — guidelines pending]**
> Official design and content guidelines for Drawer surfaces are not yet finalized. The guidance below is inferred from modal-standard patterns and general Apollo style rules. Confirm with the design team before shipping.

## When to Use

Side-panel (drawer) component used in **browser extension** contexts. Appears when a user interacts with a gated feature within the Apollo Chrome extension or similar extension surfaces.

**Best for:**

- Feature gates within the Apollo browser extension
- Contexts where a full modal would be too intrusive
- Extension-specific upgrade prompts

## Component Anatomy (Provisional)

| Component | Required | Max Chars | Notes |
|-----------|----------|-----------|-------|
| Header | Required | 35 | Same limit as modal-standard. Clearly state the limit or lock. |
| Description | Required | 102 | Same limit as modal-standard. Emphasize upgrade value. |
| Primary CTA | Required | 20 | Prompt to explore upgrade options. |
| Secondary CTA | Optional | 20 | Reserved for "Talk to Sales" if applicable. |

> **Note:** Character limits are inherited from modal-standard as provisional defaults. Actual limits may differ once official guidelines ship.

## Tone (Provisional)

**Clear, helpful, non-intrusive.**

Drawers have a smaller footprint than modals. The user is likely in the middle of browsing or prospecting. Keep copy concise and avoid anything that feels like an interruption.

## Header Patterns (Provisional)

Inherit from modal-standard:

- "You've hit your [feature] limit"
- "[Feature] isn't included in your plan"

## Description Rules (Provisional)

Inherit from modal-standard:

- 1-2 lines max
- Start with "Upgrade now to..." or similar
- Focus on the outcome

## CTA Patterns (Provisional)

| CTA | Text | When to Use |
|-----|------|-------------|
| Primary | `View pricing plans` | Default |
| Primary (alt) | `Upgrade now` | When upgrade path is clear |
| Secondary | `Talk to Sales` | Core teams only. |

## Important Notes

- This surface type's guidelines are **provisional** and should be reviewed by the design team before production use
- The drawer's smaller viewport may require shorter copy in practice — test in the actual component
- Extension contexts may have different PII visibility considerations than in-app contexts
- When guidelines are finalized, this file will be updated to match official specifications
