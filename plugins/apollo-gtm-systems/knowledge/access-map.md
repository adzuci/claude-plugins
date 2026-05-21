---
last_reviewed: 2026-05-19
primary_source: Notion (until birthright SoT exists)
---

# Access map

Canonical source: Notion access map. This file is a cached reference. For the authoritative current state of access provisioning, check the Notion access map page.

Long-term note: Lumos / Okta birthright access is the planned canonical source for role-based access at Apollo. Until that system is fully implemented, Notion is the working source of truth.

## All Apollo employees (default access)

| Tool | Default access level |
|---|---|
| Salesforce | Viewer-level unless a role-based profile applies |
| Slack | Full access |
| Notion | Full access |
| Google Workspace | Full access |
| Gong | Viewer access for employees in RevOps and Sales orgs; no access by default outside those orgs |
| Jira RS | Access to submit requests; read-only on RVOSYS by default |

## GTM Systems team (elevated access)

| Tool | Access level |
|---|---|
| Salesforce | Admin and developer access |
| Jira RVOSYS | Full project access |
| Chili Piper | Admin access to routing rules and org settings |
| Gong | Admin access to org settings, library, and scorecards |
| Ironclad | View access plus workflow participation |

## Requesting access

File a JIRA RS ticket for any tool listed above. Include:
- The tool you need access to
- The access level requested and business justification
- Your manager's name for approval

GTM Systems will provision or coordinate provisioning for all GTM stack tools. For tools not listed above, file the RS ticket and the team will route to the correct owner.
