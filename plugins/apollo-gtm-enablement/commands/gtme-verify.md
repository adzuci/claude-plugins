---
name: gtme-verify
description: Verify that a GTME enablement deck is evidence-based, complete, and ready for delivery
---

Use the `apollo-gtme-enablement-deck` skill.

If the output is a deck or presentation, also validate against `apollo-branding-enablement`.

Re-read the available source context and verify that the enablement output is ready for delivery.

**If a `.pptx` was built, run the functional check first.** From the
`apollo-branding-enablement/scripts` folder:

```bash
python3 apollo_brand.py verify /tmp/gtme-decks/<topic-slug>.pptx
```

This catches the glitch class that breaks decks — text off-slide, text-on-text
collisions, and non-rendering fonts. It must return `OK` before delivery. If it
reports issues, fix the offending positions/fonts in the build script and rebuild.

Then check the content for:

1. correct topic identification
1. correct intervention/source mapping
1. Salesforce evidence included and accurately reflected
1. Gong evidence included and accurately reflected
1. a clear teaching thesis
1. a 45-minute session structure inside a 60-minute session
1. at least one interactive activity
1. facilitator-ready guidance
1. practical rep behavior change, not generic training language
1. deck matches the `apollo-branding-enablement` design DNA (card-based, dense, Scott's palette/fonts)

Return:

- Pass/Fail overall
- What is strong
- What is missing
- What must be fixed before delivery
- Final readiness recommendation
