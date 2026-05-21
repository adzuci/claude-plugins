---
last_reviewed: 2026-05-20
primary_source: Notion Apps DB
---

# Tool inventory

Canonical source: Notion Apps DB. This file is a cached snapshot. If content feels stale or if you need ownership details, integration status, or contract information, check Notion directly.

## Primary GTM stack

| Tool | Category | Primary use at Apollo |
|---|---|---|
| Apollo.io | Sales engagement | Prospecting, sequencing, contact and account database, outbound execution |
| Salesforce | CRM | System of record for leads, contacts, accounts, opportunities, and activities |
| Snowflake | Data warehouse | Analytics, modeled metrics, org structure, pipeline reporting |
| Gong | Conversation intelligence | Call recording, coaching, deal inspection, pipeline hygiene signals |
| Chili Piper | Scheduling / routing | Inbound lead routing to AE/CSM, scheduling, personal meeting rooms |
| Ironclad | Contract lifecycle management | Contract drafting, redlining, approval workflows, executed contract storage |
| Notion | Documentation | SOPs, runbooks, project docs, RevOps intake |
| Jira (RVOSYS) | Work tracking | GTM Systems project and sprint management |
| Jira (RS) | Service desk | End-user intake for access requests, admin work, and system changes |
| Slack | Communication | Team and cross-functional async communication |
| Google Workspace | Productivity | Calendar, Drive, Docs, Sheets, Slides |
| Gearset | CI/CD | Salesforce deployment management, change-set tracking, and pipeline |
| GitHub | Version control / CI | Source code, deployment pipelines, and GTM Systems tooling repos |
| Cloudingo | Deduplication | Record deduplication and data quality management in Salesforce |
| Tray.ai | iPaaS | Integration platform for complex, multi-step GTM workflows |
| Zapier | iPaaS | Lightweight integration automation for simpler point-to-point flows |
| Miro | Collaboration | Team whiteboarding, flow diagrams, and architecture planning |
| Claude | AI | AI assistant for GTM Systems workflows, knowledge management, and RevOps automation |
| Cursor | AI dev | AI-assisted development for Salesforce/Apex and GTM tooling |

## Peripheral and secondary tools

Tools used in specific workflows or by specific teams but not centrally administered by GTM Systems:

| Tool | Category | Notes |
|---|---|---|
| Fivetran | ETL / reverse ETL | Data pipeline management |
| HubSpot | Marketing automation | Used by the marketing org |
| CIO | Integration platform | Specific integrations |
| PartnerStack | Partner relationship management | Partner program |
| Crossbeam | Partner intelligence | Account overlap and co-sell |
| Enterpret | Feedback intelligence | Voice of customer analysis |

## Deprecated tools

Tools that have been decommissioned at Apollo. May appear in old tickets, documentation, or field descriptions.

| Tool | Former category | Notes |
|---|---|---|
| Vitally | Customer success | Decommissioned |
| Troops.ai | Salesforce Slack integration | Decommissioned |
| Arovy / Sonar | Change management | Decommissioned |
| Clay | Data enrichment | Decommissioned |
| Spotdraft | Contract management | Replaced by Ironclad |

## Notes

Full Apps DB with ownership, integration status, renewal dates, and admin contacts is in Notion. This file covers the primary and known peripheral stack. Niche tools and department-specific apps may not be listed.

For access provisioning for any tool above, file a JIRA RS ticket. See `access-map.md` for role-based defaults.
