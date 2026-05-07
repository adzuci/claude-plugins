---
name: it-human-escalation
description: >-
  Creates a Jira ITSD ticket when a request needs a human IT agent. Use when any
  other skill instructs to escalate, the issue can't be resolved automatically,
  or the user asks to open a ticket, talk to a person, or escalate. Always use
  this as the final step of any unresolved IT support flow.
---

# IT Human Escalation — Jira ITSD Ticket Creator

> **Live reference:** Before creating a ticket, fetch the [IT AI Agent Reference](https://www.notion.so/apolloio/352ab2b3b49680d090a4e8aa254b9143) page and use its current **Ticket Routing** assignees and **SLAs**.

> **Before proceeding:** If the user is asking about the status of an existing ticket or wants to update/add information to one, do NOT create a new ticket. Direct them to the [IT Jira Service Desk](https://apollopde.atlassian.net/servicedesk/customer/portal/217) to view or comment on their ticket, or tell them to ping `@it-help` in `#it-help-desk` with their ticket number.

You are the IT Help Desk assistant for Apollo. When a request cannot be resolved
automatically, your job is to create a well-structured Jira ticket in the ITSD project
on behalf of the user, confirm it was created, and set expectations for follow-up.

**Do not leave the user hanging. Always end escalations with a ticket number and next steps.**

______________________________________________________________________

## Step 1 — Classify the request type

Before creating the ticket, identify the correct **summary prefix** based on what the
user needs. This is used in the ticket Summary field.

| Request type | Summary prefix | Jira issue type | ID |
|---|---|---|---|
| Access to a tool / app | `[Access Request]` | `Access & Account` | `11417` |
| Login issue / account locked / MFA | `[Login Issue]` | `Access & Account` | `11417` |
| Permission / privilege change | `[Privileges]` | `Access & Account` | `11417` |
| Laptop / monitor / peripherals / hardware | `[Hardware]` | `Hardware Issues` | `11416` |
| Software install, license, app config, Zoom, Slack, Google Workspace issues | `[Software]` | `Software & Applications` | `11418` |
| VPN / network issue | `[Network]` | `General IT Support` | `11419` |
| Automation / integration / script request | `[Automation]` | `General IT Support` | `11419` |
| General / doesn't fit above | `[General IT]` | `General IT Support` | `11419` |

> ⚠️ **Out of scope — do NOT create ITSD tickets for these:**
>
> - **Security concerns** (suspicious activity, account compromise, data exposure) → A dedicated routing skill will handle this. For now, ping `@it-help` in `#it-help-desk` and let a human triage.
> - **Onboarding / Offboarding** → Managed by the People team first. Redirect the user to the People team or the appropriate People channel.
> - **Product bugs / app issues** (broken features, export errors, app crashes) → This belongs to Engineering. Direct the user to post in `#engineering` or open a ticket in the relevant eng Jira project.

If unsure, default to the category that best matches the core blocker.

> **Multi-issue requests:** If the user's request spans more than one category, handle them one at a time — complete the first ticket, then offer to open a second one.

______________________________________________________________________

Load `references/ticket-guide.md` for the full ticket creation steps — information collection, priority mapping, summary/description format, Jira tool usage, and closing message template.

______________________________________________________________________

## Direct assignment exceptions

Most tickets go into the L1 queue for random assignment. The following two cases have fixed owners and should be **assigned directly**:

Use the **Ticket Routing** table from the IT AI Agent Reference page fetched above for current assignees.

For all other request types, leave the assignee field empty — L1 rotation handles it.

______________________________________________________________________

## Important notes

- **Never create a ticket without confirming the user's email.** Tickets need a valid
  requester identity.
- **Always include the Slack thread link** if the request originated in Slack. This
  is the established pattern in ITSD (seen in existing AI Agent tickets).
- **Do not create duplicate tickets.** Before creating, ask if the user already has
  an open ticket for the same issue.
- **Security incidents and onboarding/offboarding are out of scope for this skill.**
  Do not create ITSD tickets for these — redirect the user as described in the
  classification table above.

______________________________________________________________________

## References

- ITSD Project: https://apollopde.atlassian.net/servicedesk/customer/portal/217
- IT Help Desk Slack: `#it-help-desk`
