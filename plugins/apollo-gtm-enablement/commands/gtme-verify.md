---
name: gtme-verify
description: Verify that a GTME enablement deck is evidence-based, complete, and ready for delivery
---

Use the `apollo-gtme-enablement-deck` skill.

If the output is a deck or presentation, also validate against `apollo-branding-enablement`.

Re-read the available source context and verify that the enablement output is ready for delivery.

Check for:

1. correct topic identification
1. correct intervention/source mapping
1. Salesforce evidence included and accurately reflected
1. Gong evidence included and accurately reflected
1. a clear teaching thesis
1. a 45-minute session structure inside a 60-minute session
1. at least one interactive activity
1. facilitator-ready guidance
1. practical rep behavior change, not generic training language
1. readiness for Apollo-branded deck production if slides are requested

Return:

- Pass/Fail overall
- What is strong
- What is missing
- What must be fixed before delivery
- Final readiness recommendation
