---
last_reviewed: 2026-05-20
---

# Salesforce

## Role at Apollo

Salesforce is Apollo's CRM of record. It holds the authoritative record-level state for leads, contacts, accounts, opportunities, and sales activities. Downstream systems (Snowflake, reporting tools) pull from Salesforce for pipeline and activity data.

## Org details

| Field | Value |
|---|---|
| Org | Apollo.io production |
| Alias | Prod |
| Ownership | GTM Systems team |

## Access

Standard users receive a read-only or role-appropriate profile based on their job function. Profile changes, permission set additions, and new user provisioning all require a JIRA RS ticket. Salesforce admin work is owned by the GTM Systems team (Ed Dunn for development; GTM Systems team for configuration and administration).

## Key objects

| Object | What it represents |
|---|---|
| Lead | Unqualified inbound or outbound prospect before conversion |
| Contact | Individual person associated with an Account |
| Account | Company or organization record |
| Opportunity | Active deal being worked by an AE |
| Task / Activity | Logged touchpoints: calls, emails, meetings |
| Campaign | Marketing program tracking for influence attribution |

## Integration overview

| Integration | Direction | Notes |
|---|---|---|
| Apollo.io product | Apollo product to Salesforce | Sequence activity, contact and account data sync into Salesforce; configurable sync rules |
| Gong | Gong to Salesforce | Call activity and engagement data written back to Activity object; ~15 min typical delay (SLA: <1 hour) |
| Ironclad | Ironclad to Salesforce | Contract status and key dates surfaced on Opportunity or Account; field mapping managed by GTM Systems |

## Source of truth boundaries

Salesforce is canonical for record-level current state: deal stage, owner, contact fields, account attributes. Snowflake is canonical for modeled metrics, aggregates, and pipeline reporting. When these two sources disagree on a metric, Snowflake takes precedence. When they disagree on an individual record field, Salesforce takes precedence.

## Data model reference

Detailed object schema, field definitions, and relationship maps are in `knowledge/salesforce/data-model.md`. That file is derived from organized GDoc content and team knowledge; it is not a live sync from the org.

## GitHub / MCP access

The SFDCgearset repo contains metadata and can be queried via GitHub MCP for users with repo access. Users without GitHub access should use `knowledge/salesforce/data-model.md` as the reference instead.
