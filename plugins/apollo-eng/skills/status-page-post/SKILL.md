---
name: status-page-post
description: Draft customer-facing incident copy for Apollo's status page (status.apollo.io). Run via /apollo-eng:status-page-post.
disable-model-invocation: true
---

# Status Page Post

Draft customer-facing incident posts for status.apollo.io (a Better Stack status page) and hand paste-ready copy to the incident owner. House style, component labels, titles, and real past posts live in [references/house-style.md](references/house-style.md) — read it before drafting.

## Workflow

1. **Check the status page.** Check for open incidents so the new post doesn't duplicate or contradict an existing one. If a [Better Stack MCP/tool](https://betterstack.com/docs/getting-started/integrations/mcp/) is connected, use it to list current status-page reports/incidents. Otherwise fetch <https://status.apollo.io> (curl or WebFetch); if unreachable or unparseable, ask the user what's currently posted.
1. **Gather context.** Pull recent discussion from the incident Slack channels via fetch_channel/fetch_thread: #incident-response-sev0-sev1 (C0362RC2GR2) and #eng-infrastructure-alerts (CCHSWB3DK). The agent may not be a member of the sev0-sev1 channel — if the channels are unreadable, ask the user for:
   - the user-visible symptom
   - the affected components/features
   - the current stage (investigating/identified/monitoring/resolved)
   - whether data loss or automatic retry is confirmed
1. **Draft.** Fill the stage template below, applying the house style and component labels from the reference. Run the pre-publish checklist.
1. **Hand off.** Present the draft to the incident owner for review, then link them to <https://betterstack.com/users/sign-in#magic> to sign in and post it. Never post to the status page directly — even if a Better Stack MCP with write access is connected, do not create or update status-page reports; always hand the approved text to the incident owner.

## Stage Templates

Fill the placeholders; delete anything that doesn't apply.

- **Investigating**: "We are currently investigating reports of [user-visible symptom] affecting [product surface]. Some users may notice [concrete symptom]. [Surface X] is not affected."
- **Identified**: "We have identified the cause of [symptom] and are working on a fix. [A small subset of users / Some users] may continue to see [symptom]."
- **Monitoring**: "[Product surface] has stabilized and [symptom] should be improving. We are continuing to monitor."
- **Resolved**: "The issue has been resolved and \[all products should be operating normally / [feature] are now processing normally\]. [Jobs queued during the affected window will be completed automatically.]"

## Workflow Contract

- **Deterministic (this skill provides)**: stage templates, house-style rules, component labels, pre-publish checklist.
- **Agent judgment**: symptom wording, impact-scope phrasing, what to call out as unaffected.
- **Human (incident owner)**: verifies impact scope and any no-data-loss claim, approves the draft, publishes via Better Stack.

## Safety

Always present the draft to the incident owner for review — never publish or post to the status page directly. Impact scope and any no-data-loss claim must be verified by the incident owner before publishing.

## Pre-Publish Checklist

- [ ] No internal details leaked (systems, tools, customers, ticket IDs, service names)
- [ ] Impact scope verified with the incident owner
- [ ] No-data-loss / automatic-retry claim confirmed with the incident owner
- [ ] Affected component(s) tagged
- [ ] Title is symptom-first, 2-7 words

## Further Reading

- [references/house-style.md](references/house-style.md) — Apollo's house style, components, and real past posts
- [Atlassian Statuspage incident communication guide](https://www.atlassian.com/incident-management/tutorials/incident-communication)
