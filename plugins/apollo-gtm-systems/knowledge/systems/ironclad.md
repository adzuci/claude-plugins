---
last_reviewed: 2026-05-19
---

# Ironclad

Contract lifecycle management (CLM) system for Apollo.

## What it is used for

- Authoring, reviewing, and executing contracts (NDAs, MSAs, order forms, SOWs)
- Linking contracts to Salesforce Opportunities (contract → opportunity linkage is the canonical join)
- Tracking contract status: draft, in-review, pending signature, executed, expired
- Storing the signed contract record as the system of record post-execution

## Source of truth

Ironclad is the canonical source for contract data. When Ironclad and Salesforce disagree on contract status,
Ironclad wins. [source: knowledge/data-access.md]

## Access

- Account Executives and CSMs: access to their own deals via Ironclad SSO
- Legal and Finance: full workflow access
- GTM Systems: admin access for integration configuration
- Requesting access: RS JIRA service desk

## Integration with Salesforce

Ironclad syncs contract status back to the linked Salesforce Opportunity.
Sync is webhook-based (triggers on status change), not batch — expect near-real-time updates.

Common linked SF fields: contract stage, executed date, contract value, contract type.

## Data access note

Ironclad contract drafts that have not yet been shared with the requesting user's account team
are not surfaced by Athena. This applies even if the user has Ironclad access — Athena applies
the minimum-necessary principle to pre-close contract data. See `knowledge/data-access.md`.

## Ownership

Legal team owns the Ironclad workflow templates and approval chains.
GTM Systems team owns the Salesforce integration configuration.
