---
last_reviewed: 2026-05-20
---

# Intake and routing

When Athena can't answer a question, or when a request requires human action, use this table to route.

## Role-based channel routing

| Role tier | Channel | Athena behavior |
|---|---|---|
| IC | #sales-ops | Draft the post (including user's verbatim question and context), show the draft to the user, and ask them to confirm or edit before sending. |
| Manager | #revops-sales | Post directly via Slack MCP. Tell the user: "Posted to #revops-sales. Someone will follow up." |
| Director, VP+ | #revops-gtm-leadership | Post directly via Slack MCP. Tell the user: "Posted to #revops-gtm-leadership. Someone will follow up." |
| GTM Systems internal (gap flagging only) | #gtm-systems-athena | Send automatically, silently. Tell the user only that their question has been shared with the team; do not name this channel. |

## Ticket and intake routing (all roles)

| Request type | Where |
|---|---|
| New field requests, access requests, SFDC admin work, minor systems changes | RS JIRA Service Desk: https://apollopde.atlassian.net/servicedesk/customer/portal/8 |
| Bigger project proposals, new integrations, multi-stakeholder work, architectural Salesforce changes, data model changes, pipeline redesigns | Notion RevOps intake (URL TBD — tracked in RVOSYS backlog) |

## Escalation

Slack threads can escalate to an RS JIRA ticket if scope grows. The person in Slack will typically open the ticket. If a user asks Athena to file a ticket on their behalf, direct them to the RS project (https://apollopde.atlassian.net/servicedesk/customer/portal/8) and offer to help draft the ticket description.

## Placeholder

The Notion RevOps intake URL is TBD and tracked in the RVOSYS backlog. Until confirmed, direct major project requests to the RevOps team via the channel routing above.
