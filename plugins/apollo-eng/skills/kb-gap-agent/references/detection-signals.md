# Detection Signals

What code changes signal a KB update is needed, and what the coverage limitations are.

______________________________________________________________________

## Signal Matrix

| Signal | Files to Watch | KB Action | Confidence |
|---|---|---|---|
| New `FeatureFlagWrapper` in routes | `assets/app/routes.tsx` | New article likely needed | HIGH |
| New `*FeatureFlagWrapper` component wrapping a route | `assets/app/routes.tsx` | New article likely needed | HIGH |
| Changed `*ContextualHelp.tsx` | `assets/app/components/contextual-sidebar/` | Direct KB→surface map change | HIGH |
| New/changed `KB.*` entry | `assets/app/constants/KnowledgeBaseArticles.ts` | Article URL changed or added | HIGH |
| New settings container | `assets/app/containers/settings*/` | Settings how-to article needed | MEDIUM |
| New route added | `assets/app/routes.tsx` | New page = potential new KB article | MEDIUM |
| Changed feature-gate dialog | `assets/app/components/feature-gates/` | Pricing/plan KB update needed | MEDIUM |
| Toast message changes in settings | `assets/app/containers/settings*/` | Minor KB text update possible | LOW |
| New component in existing surface | `assets/app/containers/[surface]/` | Existing KB article may need update | MEDIUM |
| New prop/flag exposed in UI | Any UI container | Feature addition may need KB mention | LOW |

______________________________________________________________________

## File Path Filtering

When processing a git diff, keep only these paths for KB analysis:

**HIGH priority (almost always KB-relevant):**

```
assets/app/components/contextual-sidebar/
assets/app/constants/KnowledgeBaseArticles.ts
assets/app/routes.tsx
assets/app/components/feature-gates/
```

**MEDIUM priority (check for new features/UI changes):**

```
assets/app/containers/settings/
assets/app/containers/sequences/
assets/app/containers/enrichment/
assets/app/containers/search/
assets/app/containers/deals/
assets/app/containers/analytics/
assets/app/containers/conversations/
assets/app/components/[surface]/
```

**DISCARD always:**

```
*.test.tsx, *.test.ts, *.spec.tsx, *.spec.ts
*.module.scss
*.messages.ts (i18n message definitions)
*/types.ts, */types/
*/utils/ (unless it's kbLinkUtils.ts)
*/hooks/ (unless it's hook that gates a KB feature)
**/__tests__/
**/node_modules/
assets/chrome-extension/ (extension has separate KB needs)
packs/ (backend changes — use doc-driven mode instead)
```

______________________________________________________________________

## Detection Priority by Mode

### Branch Diff / Time-Scoped

Focus on what changed in the diff. Check:

1. ContextualHelp files changed? → Direct KB mapping change
1. New KB.\* constant added/changed? → Article added or URL updated
1. New route with FeatureFlagWrapper? → New feature needing KB article
1. Container changes in settings/? → Settings workflow may need update
1. Feature gate dialog changed? → Pricing tier KB copy may need update

### Surface-Scoped

Focus on all files owned by the team. Check:

1. All ContextualHelp files for this surface
1. All KB articles mapped by those ContextualHelp files
1. Invisible articles — KB articles that exist on site but aren't linked from this surface's code
1. Stale refs — KB constants used in this surface's code that point to deleted articles

### Quick Audit

No diff needed. Static checks only:

1. Stale refs in `KnowledgeBaseArticles.ts` vs live Zendesk API
1. Broken placeholder entries (`ARTICLE_ID` pattern)
1. Invisible articles — report as **aggregate count only** (e.g., "112 articles not linked from code"), not individual action items
1. Hardcoded KB URLs outside `KnowledgeBaseArticles.ts`
1. TODO comments mentioning KB articles
1. ESLint enforcement gaps

______________________________________________________________________

## Known Detection Blind Spots

| Blind Spot | Why It's Missed | Mitigation |
|---|---|---|
| **Backend-only changes** | Skill relies on frontend file changes; packs/ are ignored | Use doc-driven mode with the PRD/epic instead |
| **Subtle behavior changes** | Button label same, workflow different | Article comparison catches if KB describes old behavior in detail |
| **Config/env changes** | Feature toggled via env var, not feature flag | Not detectable — known limitation; doc-driven with PRD helps |
| **Third-party integration changes** | External API version upgrades invisible in our code | Surface-scoped on "integrations" catches some; doc-driven for known integration updates |
| **New features with no ContextualHelp** | Feature ships without a Help file | Skill flags explicitly: "No ContextualHelp file found for [container]" |
| **Copy/text-only changes** | Error message or tooltip text changes | Files appear in diff but aren't always mapped to specific KB articles |
| **Mobile app changes** | `assets/mobile/` is not part of the KB signal path | Known gap — mobile KB articles may drift |
| **Chrome extension changes** | `assets/chrome-extension/` has its own KB patterns | Run surface-scoped on "extension" if extension changes are in scope |
| **Deleted features** | Removed container = removed KB relevance | Stale refs check partially covers this; full audit catches deleted-but-still-linked articles |

**Overall detection coverage:** ~70–80% of KB-impacting changes via code-driven modes.
Remaining 20–30% caught by doc-driven mode or human judgment.
Current baseline without this skill: **0% automated detection.**

______________________________________________________________________

## Confidence Level Definitions

**HIGH confidence** — Strong evidence that KB update is needed:

- Article text directly contradicts what changed in code
- New UI element/workflow that article completely omits
- Article ID in constants points to deleted article (verified via API)
- Broken placeholder URL (verified via pattern match)

**MEDIUM confidence** — Probable KB gap, but needs human validation:

- Code change adds a new option/field not mentioned in article
- Article was last updated 6+ months before this code change
- New route exists with no ContextualHelp file linked
- Article title suggests it covers the feature but content seems partial

**LOW confidence** — Possible gap, worth flagging but lower priority:

- Minor UI text change that may or may not affect article screenshots
- New component in existing surface (article may still be accurate)
- Article exists and seems complete, but was last updated long ago
- Feature mentioned in article but description seems vague

______________________________________________________________________

## Detecting Specific Gap Types

### STALE (article describes old behavior)

- Trigger: code change in a container that a ContextualHelp file maps to an article
- Check: does the article's text describe old UI flow/steps that the code no longer does?
- Signal: `Updated: [old date]` + code change in same surface area

### NEW_FEATURE (feature shipped, no KB article)

- Trigger: new route with `FeatureFlagWrapper` + no matching ContextualHelp article link
- Also: new container with no ContextualHelp file at all

### UI_CHANGED (screenshots/steps outdated)

- Trigger: changed container + article has step-by-step instructions that reference old UI
- Look for: numbered steps, "click the X button", "navigate to Y" in article content

### STALE_REFERENCE (deleted article ID in constants)

- Trigger: article ID in `KnowledgeBaseArticles.ts` not in live Zendesk index
- Always HIGH confidence — definitive data mismatch

### INVISIBLE_ARTICLE (on site, not linked from product)

**IMPORTANT:** `KnowledgeBaseArticles.ts` and ContextualHelp files are NOT the source of truth for all KB articles. Many articles legitimately exist only on the KB site — getting started guides, best practices, troubleshooting, release notes — and don't need product UI linking. An article being absent from code is **normal, not a gap**.

**Do NOT:** Scan all 272 Zendesk articles and flag every one missing from code as INVISIBLE_ARTICLE. That generates 112 false positives.

**Only flag INVISIBLE_ARTICLE when there's additional evidence** the article belongs in the product:

1. **Surface-scoped mode:** Flag only when the article's title/content clearly matches the surface being audited AND describes an in-product feature (not a guide or best practice). E.g., auditing "integrations" → an article titled "Configure Salesforce Push Settings" that isn't linked is worth flagging; an article titled "Getting Started with Apollo" is not.
1. **Branch diff / time-scoped:** Flag only if a code change adds a feature that an existing KB article already documents, but the article isn't linked from the ContextualHelp for that surface.
1. **Quick audit:** Report the count of articles not in code as an **informational stat** (e.g., "112 articles on KB site not linked from product code"), NOT as 112 individual action items. Do not investigate each one.

**Confidence:** Always LOW unless the article title is a direct match for the surface and describes an in-product workflow.

### NOT_IMPLEMENTED / UNDOCUMENTED_ADDITION (doc-driven only)

- NOT_IMPLEMENTED: PRD describes feature X, but `grep` of codebase finds no evidence of it
- UNDOCUMENTED_ADDITION: code has feature Y not described in PRD — may need KB article even if PRD doesn't mention it
