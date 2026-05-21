---
last_reviewed: 2026-05-20
primary_source: GDoc 1jS8UmIPE0rsd7pFK9Fj8YF8x27jbNeLr41jneF4gdL4 + apolloio/SFDCgearset
sync_status: stub — awaiting GDoc content import (Phase 1 task)
---

# Salesforce automation

Covers flows, triggers, validation rules, and process builders in Apollo's Salesforce org.

## Automation landscape

Apollo's org uses Salesforce Flow as the primary automation layer. Apex triggers exist for complex logic.
Process Builders and Workflow Rules are legacy — actively being migrated to Flow.

Key automation owners: GTM Systems team (Ed Dunn primary for Apex and complex flows; Jared Thompson for integration-adjacent automation).

## Field-ownership heuristic

If a field is populated by automation rather than user input, the flow or trigger responsible is typically named
after the field or the RVOSYS ticket. Check:
1. Field description for `RVOSYS-XXXX` → look up that ticket in Jira
2. SFDCgearset repo for flows/triggers referencing the field API name
3. `#sales-ops` if the above doesn't surface the owner

## TODO

> Full automation inventory (flow names, trigger objects, validation rule list, owner per automation) will be
> populated during Phase 1 by importing GDoc `1jS8UmIPE0rsd7pFK9Fj8YF8x27jbNeLr41jneF4gdL4`.
> Until then, use the Salesforce MCP (`retrieve_metadata`) or ask in `#sales-ops`.
