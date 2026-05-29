---
name: gtme-run-next
description: Run the next weekly GTME deep-dive workflow end to end and produce a deck-ready enablement package
---

Use the `apollo-gtme-enablement-deck` skill.

If the output is a deck or slides, also use `apollo-branding-enablement` as the design and production standard.

**Before running, verify required connectors are available.** Confirm Notion, Salesforce, and Gong respond to trivial test queries. If any fails, stop and tell the user to run `/gtme-setup` before retrying — the run depends on all three.

Run the full workflow for the next scheduled GTME deep-dive session.

Actions:

1. Read the Notion enablement calendar and identify the next relevant session topic.
1. Find the matching intervention or source materials.
1. Read Salesforce evidence to determine whether the intervention is active and how it is showing up operationally.
1. Read Gong trackers, streams, initiative boards, and scored calls to identify strong examples, rep gaps, and talk-track opportunities.
1. Synthesize the intervention into a practical enablement point of view.
1. Build a facilitator-ready 45-minute session for a 60-minute Zoom slot.
1. Produce a slide-by-slide Apollo-ready deck outline with speaker notes and an interactive activity.
1. If required inputs for final branded deck production are missing, clearly list them at the end.

Return:

- identified topic
- evidence summary
- session strategy
- full deck outline
- open questions or missing inputs
