# IT Ticket Creation — Step-by-Step Guide

## Step 2 — Collect missing information

Before creating the ticket, make sure you have:

- ✅ **User's full name and `@apollo.io` email** — if the email provided does not end in `@apollo.io`, do not proceed. Ask the user to provide their Apollo email address.
- ✅ **What they're trying to do** (the action, not just the tool)
- ✅ **What's failing** (error message, behavior observed)
- ✅ **How urgent it is** (blocking work now? nice-to-have?)
- ✅ **Slack thread link** (if the request came from Slack — include it in the ticket)
- ✅ **Business justification** (required for access/privilege requests)

If any of these are missing and can be inferred from context, use the context.
If not, ask for the missing piece before creating the ticket — **one question at a time**.

______________________________________________________________________

## Step 3 — Determine priority

| Situation | Priority |
|---|---|
| User completely blocked from doing their job right now | **P1** |
| User significantly impacted but has a workaround | **P2** (default) |
| Non-urgent request, can wait | **P3** |
| Security incident / data at risk | **P0** — flag immediately |

When in doubt, use **P2**.

______________________________________________________________________

## Step 4 — Build the ticket

### Summary format

```
[Category] Short description of the issue — User Name
```

Examples:

- `[Access Request] GitHub org access — Employee Name`
- `[Login Issue] Okta MFA not triggering on mobile — Employee Name`
- `[Privileges] Permanent Godmode request — Employee Name`
- `[Hardware] Laptop not charging — Employee Name`
- `[Software] Zoom host going to waiting room — Employee Name`
- `[Network] VPN PIN reset needed — Employee Name`

### Description format (use this exact structure)

```
**User:** [Full Name] ([email@apollo.io])
**Request:** [What they need — be specific]
**Issue / Error:** [Exact error message or behavior, if applicable]
**Steps already tried:** [What was attempted before escalating]
**Business justification:** [Why they need this — required for access/privilege tickets]
**Urgency:** [Blocking work / Non-urgent / etc.]

---
This ticket was automatically created by the IT AI Agent.
Slack Thread: [link to original Slack thread, if available]
```

### Project and issue type

- **Project:** `ITSD`
- **Cloud ID:** `5ee66b17-496e-4339-8a97-c9992ff2013f`
- **Issue type:** `Access & Account` (ID: `11417`) for login, access, and permission issues
  - For other categories (hardware, software, etc.), use the most appropriate available type
- **Priority:** As determined in Step 3

______________________________________________________________________

## Step 5 — Create the ticket using the Jira tool

Use the `createJiraIssue` tool with:

```
cloudId: "5ee66b17-496e-4339-8a97-c9992ff2013f"
projectKey: "ITSD"
issueTypeName: "Access & Account"   ← or appropriate type
summary: "[Category] Description — User Name"
description: <structured description from Step 4>
contentFormat: "markdown"
```

______________________________________________________________________

## Step 6 — Confirm and close the loop

After the ticket is created, tell the user:

1. The **ticket number and link** (e.g., `ITSD-20802`)
1. That **an IT L1 agent will pick it up** — tickets are assigned randomly to available L1 support agents and escalated internally if needed
1. **Expected SLA:** Fetch the [IT AI Agent Reference](https://www.notion.so/apolloio/352ab2b3b49680d090a4e8aa254b9143) page and use the current values from its **SLAs** section.
1. **Where to follow up:** [IT Jira Service Desk](https://apollopde.atlassian.net/servicedesk/customer/portal/217) or `#it-help-desk` in Slack

Example closing message:

> ✅ I've created ticket **ITSD-XXXXX** for your request. An IT agent will pick it up shortly — expected response within [SLA]. You can track progress here: [link]. If it's urgent, ping `@it-help` in `#it-help-desk` and reference your ticket number.
