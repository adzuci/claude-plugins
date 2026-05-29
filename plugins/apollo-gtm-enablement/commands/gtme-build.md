---
name: gtme-build
description: Build a facilitator-ready Apollo GTM enablement deck from Notion, Salesforce, and Gong evidence (Sales, CS, or Product)
---

Use the `apollo-gtme-enablement-deck` skill.

If the request involves a presentation, deck, or slides, also follow `apollo-branding-enablement` as the source of truth for Apollo deck design and production rules.

**Before building, verify required connectors are available.** Confirm Notion and Google Drive respond to a trivial test query (e.g. "search Notion for 'GTME'"). If either fails, stop and tell the user to run `/gtme-setup` before retrying — do not attempt to build a deck without the data sources available.

Build a complete GTM enablement output for the requested or upcoming topic.

**Usage:**

- `/gtme-build` — Build deck for next GTME calendar topic
- `/gtme-build "Topic Name"` — Build deck for specific topic
- `/gtme-build "Feature Launch" --team cs` — Build CS-focused deck

**Examples:**

- `/gtme-build "AI Prospect Research Demo Training"`
- `/gtme-build "Customer Onboarding Best Practices" --team cs`
- `/gtme-build "Beta Program Enablement"`

Actions:

1. Identify the session topic from the user request or the specified Notion calendar.
1. Read the matching source documentation (intervention page, feature doc, playbook, process guide).
1. Pull Salesforce evidence to determine activity patterns and operational reality:
   - **Sales topics:** Intervention completion, win rates, deal velocity
   - **CS topics:** Adoption metrics, customer health, renewal rates
   - **Product topics:** Feature usage, beta customer data, product-qualified leads
1. Pull Gong evidence from relevant call types to understand:
   - what good execution sounds like (top performer examples)
   - what common gaps or mistakes appear (coaching opportunities)
   - what real examples should be taught (actual customer conversations)
1. Synthesize the enablement point of view:
   - what the topic is (intervention, feature, process, skill)
   - why it matters (business impact, customer outcomes, revenue impact)
   - whether it is active in the field (Salesforce data)
   - what the audience needs to recognize, say, diagnose, or do differently
1. Create a 45-minute enablement experience for a 60-minute Zoom session.
1. Produce a slide-by-slide deck outline with:
   - slide title
   - core message
   - on-slide bullets
   - suggested visual or layout
   - speaker notes
1. Include:
   - session objective
   - business relevance
   - Salesforce-backed operational reality
   - Gong-backed examples
   - common failure points
   - workflow or diagnostic framework
   - talk track guidance
   - interactive activity
   - discussion/debrief
   - key takeaways
   - next steps
1. If inputs required by the Apollo branding workflow are missing, clearly list them.

Do not invent internal facts. If evidence is incomplete, call out the gap explicitly.
