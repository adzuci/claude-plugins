---
last_reviewed: 2026-05-20
---

# Playbook: GTM Systems knowledge management

This process keeps Athena's knowledge base current. Athena is only as good as what it knows; stale files produce stale answers.

## Cadence and ownership

Monthly. Andrew and Jared alternate as the session owner.

## Process

1. The owner opens a new Claude session and starts with: "Brain dump mode — help me capture what I know about [topic]"
2. Dump context conversationally: quirks discovered this month, decisions made, things that surprised you, edge cases that came up in tickets
3. Claude organizes the dump into the appropriate knowledge file(s) using the `commit-to-memory` skill (part of the Hephaestus plugin — not available in Athena)
4. Open a PR against `apolloio/claude-plugins` with the updated knowledge files. PR title format: `docs(knowledge): monthly update — [month year]` (e.g., `docs(knowledge): monthly update — May 2026`)
5. The non-owner reviews and merges. Two-person rule applies to all knowledge updates.
6. Bump the `last_reviewed` frontmatter field on every file touched.

## PR approvers

All knowledge PRs require a team member approver in addition to any default DevOps reviewers:
- Andrew approves Jared's PRs
- Jared approves Andrew's PRs

No exceptions. Direct commits to main are blocked.

## Two-person rule

No direct commits to main. All knowledge updates go through a PR reviewed by the other team member. This prevents single-point-of-failure knowledge and catches errors before they reach users.

## Topics that benefit most

| File | What to dump |
|---|---|
| `knowledge/salesforce/quirks.md` | Gotchas and surprises from recent SFDC admin work |
| `knowledge/diagnostics/` | New patterns in how calls, routing, or tools break |
| `knowledge/systems/` | Sync delays, new edge cases, middleware changes discovered |
| `knowledge/tool-inventory.md` | New tools added to the stack, tools decommissioned |
| `knowledge/playbooks/` | Process changes, new intake patterns, updates to how tickets should be filed |

## When to do an off-cycle update

Do not wait for the monthly cadence if:
- A major configuration change was made to Chili Piper routing, Gong org settings, or a Salesforce automation
- A new integration was deployed or an existing one changed middleware
- A recurring ticket pattern emerged that Athena should know how to handle

Off-cycle updates follow the same PR process; skip the formal session format and go directly to editing the relevant file.
