---
last_reviewed: 2026-05-20
primary_source: apolloio/SFDCgearset (nightly sync) + GDoc 1jS8UmIPE0rsd7pFK9Fj8YF8x27jbNeLr41jneF4gdL4
sync_status: stub — awaiting GDoc content import (Phase 1 task)
---

# Salesforce data model

Org: Apollo.io production (alias: Prod). Source of truth for record-level current state.

## Core objects

| Object | API name | Purpose |
|---|---|---|
| Lead | Lead | Unqualified prospect before conversion |
| Contact | Contact | Qualified individual, tied to an Account |
| Account | Account | Company record |
| Opportunity | Opportunity | Active deal |
| Task | Task | Logged rep activity |
| Event | Event | Calendar-based activity |
| Campaign | Campaign | Marketing attribution source |
| Case | Case | Support and service requests |

## Common fields used in hygiene and mapping work

- `Lead.Status`, `Lead.LeadSource`, `Lead.OwnerId`, `Lead.ConvertedContactId`
- `Contact.AccountId`, `Contact.Title`, `Contact.Email`, `Contact.OwnerId`
- `Opportunity.StageName`, `Opportunity.CloseDate`, `Opportunity.Amount`, `Opportunity.OwnerId`
- `Account.OwnerId`, `Account.Type`, `Account.Industry`, `Account.BillingCountry`

## Field naming conventions

All custom fields created by GTM Systems follow the format:
`Field_Name__c` with a description using: `RVOSYS-XXXX | <human-readable description>`

The `RVOSYS-XXXX` ticket reference in the field description is the canonical traceability mechanism. If a field has no RVOSYS ticket in its description, it predates the convention or was created outside GTM Systems.

## TODO

> This file is a stub. The full data model, custom object inventory, and relationship map will be populated
> during Phase 1 by importing and reorganizing GDoc `1jS8UmIPE0rsd7pFK9Fj8YF8x27jbNeLr41jneF4gdL4`
> (Apollo SFDC brain dump). Until then, use the Salesforce MCP or `#sales-ops` for detailed field questions.
