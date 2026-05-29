---
name: gtme-init
description: Initialize a new enablement run for any GTM team (Sales, CS, Product)
---

Use the `apollo-gtme-enablement-deck` skill.

**Before initializing, verify required connectors are available.** Confirm Notion responds to a trivial test query (e.g. "search Notion for 'GTME'"). If it fails, stop and tell the user to run `/gtme-setup` before retrying — do not attempt to initialize a run without the enablement calendar reachable.

Initialize a new Apollo GTM enablement run.

**Usage:**

- `/gtme-init` — Auto-detect next GTME calendar topic
- `/gtme-init "Topic Name"` — Specify custom topic
- `/gtme-init --calendar "CS Training"` — Use different calendar

**Examples:**

- `/gtme-init "AI Prospect Research Feature Launch"`
- `/gtme-init --calendar "Product Launch Calendar"`
- `/gtme-init "Customer Onboarding Best Practices"`

Actions:

1. Read the specified Notion calendar (default: GTME enablement calendar) and identify the upcoming topic, OR use the user-provided topic.
1. Find the matching source documentation (intervention page, feature doc, playbook, process guide).
1. Pull the initial context needed:
   - topic name
   - source documentation
   - business purpose
   - target audience (AEs, CSMs, Sales + CS, etc.)
   - expected behavior or outcome
1. Check Salesforce for relevant activity patterns (interventions for Sales topics, adoption metrics for CS topics, feature usage for Product topics).
1. Check Gong for relevant conversation examples (sales calls, CS calls, demos, etc.).
1. Return an initialization brief with:
   - session topic
   - source documentation identified
   - whether the topic appears active in the field (Salesforce evidence)
   - available Gong conversation examples
   - missing inputs needed before final deck creation
   - recommended session audience and format

If no topic is specified, use the next scheduled item from the default GTME enablement calendar.
Do not create the full deck yet unless explicitly asked.
