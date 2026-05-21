---
last_reviewed: 2026-05-20
last_synced: 2026-05-20
primary_source: Snowflake dim_teams_analyst
---

# Team roster

This file is a cached fallback. At session start, Athena should prefer Snowflake `dim_teams_analyst` for org structure queries. This file may lag Snowflake by up to 24 hours.

## GTM Systems leadership chain

| Name | Title | Reports to |
|---|---|---|
| Andrew Lai | Director of GTM Systems | Henry Mizel |
| Henry Mizel | VP of Revenue Operations | Adam Carr |
| Adam Carr | CRO | Matt Curl |
| Matt Curl | CEO | — |

## GTM Systems team members

| Name | Title | Focus area |
|---|---|---|
| Harini Vijayaraghavan Chitra | Staff BSA | Systems analysis, requirements gathering, process design |
| Ed Dunn | Sr. Salesforce Developer II | Apex development, LWC, system integrations, deployments |
| Nghi Lam | Sr. BSA II | Data quality, reporting, analytics requirements |
| Pedro Eiras | Sr. BSA II | GTM systems analysis, RevOps analytics |
| Jared Thompson | Sr. BSA II | Tooling, AI-assisted RevOps workflows |

## Team coverage map

A coverage map showing team member focus areas, system ownership, and on-call rotation is maintained in Notion: https://www.notion.so/apolloio/0f323253e1124572beb9805f5f0b5881?v=257ab2b3b496803cbcab000c4d902b1c

## Emeritus

Former team members who may be referenced in tickets, documentation, or system history:

| Name | Former role | Notes |
|---|---|---|
| Celeste Kiphut | Sr. BSA II | Left Apollo May 2026 |
| Leyna Hoffer | GTM Systems | Former team member |
| Linnea Olson | GTM Systems | Former team member |

## Revenue Operations org context

GTM Systems sits within Henry Mizel's Revenue Operations org, which reports to Adam Carr (CRO). RevOps at Apollo has two types of functions: vertical functions (Sales Operations, Customer Operations, Support Operations, Deal Desk) that serve specific business motions, and horizontal functions (GTM Systems, GTM Strategy and Operations) that span the full go-to-market org. GTM Systems specifically owns the CRM architecture, data integrations, and GTM toolstack administration. For broader RevOps org questions, Snowflake `dim_teams_analyst` is the authoritative source.

## Freshness note

This file is a point-in-time snapshot. For the current org chart, headcount, or recent team changes, query Snowflake `dim_teams_analyst` directly or check Workday.
