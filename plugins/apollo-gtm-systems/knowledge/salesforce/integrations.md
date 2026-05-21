---
last_reviewed: 2026-05-20
primary_source: GDoc 1jS8UmIPE0rsd7pFK9Fj8YF8x27jbNeLr41jneF4gdL4
sync_status: stub — awaiting GDoc content import (Phase 1 task)
---

# Salesforce integrations

Documents the integrations that write to or read from Apollo's Salesforce org.

## Key integrations

| System | Direction | Sync type | Typical delay | Owner |
|---|---|---|---|---|
| Apollo product | Apollo → SF | Near-real-time (webhook) | 1-5 min | GTM Systems |
| Gong | Gong → SF | Batch | ~15 min (SLA: <1 hr) | GTM Systems |
| Ironclad | Ironclad → SF | Webhook on status change | Minutes | GTM Systems |
| Chili Piper | CP ↔ SF | Read/write for routing | Real-time | GTM Systems |

## Apollo product → Salesforce sync

The Apollo product (sales engagement platform) syncs contact and account activity to Salesforce.
Common sync fields: email open/click events, sequence enrollment status, contact owner.

**Sync delay caveat:** If a contact was added to a sequence moments ago, the SF record may not reflect it yet. Wait 5-10 minutes before treating a missing sync as an issue.

## Gong → Salesforce sync

Gong writes call summaries, scorecards, and next steps back to SF Opportunity records.
The sync runs in batch — expect ~15 minutes (SLA: under 1 hour) between a Gong call completing and the SF fields updating.

## TODO

> Full integration map, field-level sync details, error patterns, and known edge cases will be populated
> during Phase 1 by importing GDoc `1jS8UmIPE0rsd7pFK9Fj8YF8x27jbNeLr41jneF4gdL4`.
> For sync issues, see `knowledge/playbooks/integration-issue.md` and `knowledge/diagnostics/`.
