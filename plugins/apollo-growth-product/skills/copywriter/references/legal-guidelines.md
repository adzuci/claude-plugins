# Legal Guidelines for Feature Gates

> **ATTORNEY CLIENT PRIVILEGED** — This document summarizes legal risk guidance for Apollo feature gates. Treat this content as internal-only.

## Why This Matters

Apollo has received multiple lawsuits related to "right of publicity" when feature gates with transactional language encouraging users to purchase or upgrade appear near personal identifying information (PII). Existing and new feature gates without appropriate mitigations put Apollo at risk for future lawsuits and potential violations of existing settlement agreements.

## 3-Factor Risk Test

A feature gate is **higher risk** when these 3 factors stack together:

| # | Factor | Question |
|---|--------|----------|
| 1 | **PII visible** | Is a person's full name, email, phone number, or anything identifying a specific person visible on screen? |
| 2 | **Transactional language** | Does the copy use language encouraging a purchase or upgrade? (e.g., "buy more credits," "view pricing plan," "talk to sales," "upgrade") |
| 3 | **Free users** | Is this shown to free users? (Higher risk because the gate is explicitly for conversion and shown to a broader audience.) |

> **If you answered "yes" to 2 or more factors, treat the feature gate as higher risk.** Apply mitigations below and request legal review when in doubt.

## Risk Scoring

| Yes Count | Risk Level | Action |
|-----------|------------|--------|
| 0-1 | **Low** | Standard copy OK. No additional mitigations required. |
| 2 | **Medium** | Apply at least one mitigation. Consider legal review. |
| 3 | **High** | Apply all applicable mitigations. **Request legal review.** |

## Higher-Risk vs Lower-Risk Language

| Higher Risk (transactional) | Lower Risk (informational) |
|-----------------------------|---------------------------|
| Button: "Buy more credits" / "Get more credits" | Button: "Continue" |
| Button: "View pricing plan" | Button: "Next" |
| Button: "Talk to Sales" | Button: "Learn more" |
| "You've hit your limit. Upgrade now to continue." | Explain the limitation and what's unlocked (informational), then move pricing/upgrade language to a separate screen. |

## 3 Mitigation Strategies

### 1. Use the Standard Feature Gate Component (Blurred Background)

All feature gates shown to free users using the standard feature gate component apply a **blurred background** by default. This blur only appears while the feature gate is visible and is designed to obscure any PII that might otherwise be visible behind it.

**When to use:** Always, for any feature gate shown to free users where PII may be visible.

### 2. Add Separation Between Steps

Instead of immediately prompting a user to upgrade in the context of a PII-related action:

1. Lead with an **informative** step (e.g., "You've reached your limit" + "Continue" button)
1. Follow up with a **transactional** step (e.g., "View pricing," "Upgrade now")

This creates a clear separation between the PII context and the purchase prompt.

**When to use:** When PII is visible AND transactional language is needed. The two-step approach moves the purchase language away from the PII context.

### 3. Avoid Transactional Copy When PII Is Visible

Even with the default blur, a feature gate still carries risk when free users + transactional language are involved. Swap transactional language for informational language:

- Instead of "Upgrade now" → "Learn more"
- Instead of "Buy credits" → "Continue"
- Instead of "View pricing plan" → "Next"

**When to use:** When PII is visible and you want to minimize risk without a two-step flow.

## When to Involve Legal

- If a feature gate scores **High risk** (all 3 factors = Yes), request legal review on the content.
- If you are **unsure** about the risk level, request legal review.
- Reach out via Slack:
  - `#legal-product-collab`
  - `#xfn-legal-marketing`

## Quick Reference: Risk Decision Tree

```
Is PII visible?
├── No → Low risk. Standard copy OK.
└── Yes →
    Is transactional language used?
    ├── No → Low risk. Informational copy is safe.
    └── Yes →
        Shown to free users?
        ├── No → Medium risk. Apply at least one mitigation.
        └── Yes → HIGH RISK. Apply all mitigations. Request legal review.
```
