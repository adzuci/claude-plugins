---
last_reviewed: 2026-05-20
---

# Knowledge file index

This directory is the knowledge layer for the Apollo GTM Systems Athena plugin. Files here are embedded at session start (cached) and act as the first retrieval hop: fast, free, and usually sufficient for common questions.

Heavy content lives in subdirectories. Lean top-level files act as indexes into those subdirectories. When a top-level file points you to a subdirectory, load that file only if the top-level summary is insufficient.

**v0.1.0 coverage note:** Five of the six `salesforce/` files are stubs pending GDoc import in Phase 1. They provide fallback routing to `#sales-ops` but will not resolve detailed SFDC questions. For live Salesforce data, use the Salesforce MCP directly. Coverage will expand after the Phase 1 knowledge import.

## Tiering

| Tier | What it covers | Load behavior |
|------|---------------|--------------|
| Top-level files | Routing, team, tool index, access policy | Embedded at session start |
| `systems/` | Per-system deep dives (Salesforce, Gong, Chili Piper, etc.) | Load on demand when user asks about a specific system |
| `salesforce/` | Data model, object reference, integration detail | Load on demand; content is organized GDoc and team knowledge, not a live sync |
| `playbooks/` | Step-by-step operational playbooks | Load on demand by topic |
| `diagnostics/` | Troubleshooting guides for known recurring issues | Load on demand by symptom |
| `team-internal/` | GTM Systems team-only process docs; not surfaced to end users | Load only when team members ask about internal processes |

## File inventory

**Top-level** (loaded at session start)

| File | Content |
|------|---------|
| _index.md | This index |
| access-map.md | Role/team to tool access mapping |
| data-access.md | Refused query categories; source-system precedence |
| intake-routing.md | Channel and portal routing when Athena can't answer |
| team-roster.md | GTM Systems team members and leadership chain |
| tool-inventory.md | Primary GTM stack overview |

**systems/** (load on demand)

| File | Content |
|------|---------|
| systems/chili-piper.md | Chili Piper routing, meeting rooms, recording dependency |
| systems/gong.md | Gong usage, recording requirements, data path |
| systems/ironclad.md | Ironclad contract flow and Salesforce integration |
| systems/salesforce.md | Salesforce org overview, integrations, ownership |

**salesforce/** (load on demand; most are stubs pending Phase 1 GDoc import)

| File | Content |
|------|---------|
| salesforce/automation.md | Flows, triggers, validation rules (stub) |
| salesforce/data-model.md | Core objects, fields, naming conventions (stub) |
| salesforce/integrations.md | Systems that sync to/from SF, delays, owners (partial) |
| salesforce/opportunity-exit-criteria.md | Stage exit criteria for new business and upsell (stub) |
| salesforce/quirks.md | Known tribal-knowledge gotchas (stub) |

**playbooks/** (load on demand by topic)

| File | Content |
|------|---------|
| playbooks/data-correction-request.md | How to request a data correction |
| playbooks/integration-issue.md | Diagnosing and escalating integration problems |
| playbooks/mcp-reconnect-help.md | MCP auth reconnect steps |
| playbooks/new-field-request.md | How to request a new Salesforce field |
| playbooks/new-user-access.md | Tool access provisioning process |

**diagnostics/** (load on demand by symptom)

| File | Content |
|------|---------|
| diagnostics/no-gong-recording.md | Call not recorded in Gong |
| diagnostics/no-zoom-or-apollo-processing.md | Zoom or Apollo recording not processing |
| diagnostics/sf-errors.md | Salesforce validation, flow, or trigger errors |
| diagnostics/unexpected-routing.md | Meeting or lead routed to wrong rep |

**team-internal/** (not surfaced to end users)

| File | Content |
|------|---------|
| team-internal/knowledge-management-process.md | Monthly knowledge update process |

## Notes on sync and freshness

- `last_reviewed` frontmatter is bumped on every edit to any file.
- Files with a `primary_source` frontmatter field have a canonical upstream. When those sources are accessible via MCP at session start, Athena should prefer the live source over cached content.
- `salesforce/` content is derived from organized GDoc content and team knowledge. It is not a live sync from the Salesforce org or the SFDCgearset repo. For repo access, see `systems/salesforce.md`.
- `team-roster.md` may lag Snowflake by up to 24 hours. Always treat Snowflake `dim_teams_analyst` as canonical for org structure.
- `team-internal/` files are for GTM Systems team process documentation. The `playbook` skill does not load from this directory; these files are not surfaced to end users asking process questions.
- All `salesforce/` files are updated via the monthly knowledge management process. Cadence, ownership, and PR requirements are in `knowledge/team-internal/knowledge-management-process.md`.
- MCP server configuration (which source systems Athena connects to and why) is documented in `.mcp.json` at the plugin root. Update that file and open a PR to add or modify an MCP connection.
