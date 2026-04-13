# Jarvis Update Protocol

**Owner:** Bridie Meredith
**Updated:** 2026-03-31
**Audience:** internal-admin — Analytics team, Leo, Bridie, Deepak (not for exec-facing responses)
**Load-on:** jarvis-admin, sync, knowledge-update

How to update Jarvis's knowledge base. This document is the canonical reference for anyone (Analytics team, Leo, Deepak) who needs to add or change what Jarvis knows.

> **POLICY: Direct edits to `jarvis/knowledge/` are prohibited for all synced files.** Edits made there will be overwritten on the next sync. Always edit analytics-copilot first, then run `/sync-jarvis`. The only files editable directly in jarvis are `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` and `domain_context.md` (jarvis-native, not synced).

---

## Architecture in one sentence

`analytics-copilot/domain/` is the source of truth. `jarvis/knowledge/` is a read-only sync export. **Edit analytics-copilot first, then sync.**

---

## How Jarvis Gets Updated

```
analytics-copilot/domain/    →  sync-jarvis.sh  →  jarvis/knowledge/
     (edit here)                  (run this)           (auto-updated)
```

### Step-by-step

1. **Edit the canonical source** in `analytics-copilot`:
   - Domain knowledge → `domain/`
   - Table documentation → `data-catalog/context/`
   - Metric definitions → `metrics/`
   - SQL patterns / glossary → `domain/sql_patterns.md`, `data-catalog/glossary_entries.md`

2. **Run `/sync-jarvis`** (recommended) — handles the sync script + commits in both repos automatically.

   Or manually:
   ```bash
   bash scripts/sync-jarvis.sh

   # In analytics-copilot:
   git add -p && git commit -m "..." && git push

   # In jarvis:
   git add knowledge/ && git commit -m "context(sync): knowledge updated from analytics-copilot YYYY-MM-DD" && git push
   ```

---

## What the Sync Covers

| Source (analytics-copilot) | Destination (jarvis/knowledge/) |
|---|---|
| `sql/lu_saved_metrics.sql` | `lu_saved_metrics.sql` |
| `data-catalog/glossary_entries.md` | `glossary_entries.md` |
| `domain/sql_patterns.md` | `sql_patterns.md` |
| `metrics/*.md` | `metrics/*.md` |
| `data-catalog/context/*.md` | `context/*.md` |
| `domain/product_debrief_template.md` | `product_debrief_template.md` |
| `domain/activation_methodology.md` + 9 other domain files | (same name in knowledge/) |
| `teammates/bridie_meredith/jarvis_context_building/knowledge/*.md` | (same name in knowledge/) |
| `plugin/claude-plugins-export/knowledge/team_roster.md` | `team_roster.md` |

See `scripts/sync-jarvis.sh` for the authoritative list.

---

## What the Sync Does NOT Cover

These files live natively in `jarvis/` and are **not overwritten** by the sync:

- `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` — Jarvis's own knowledge index
- `domain_context.md` — Jarvis-specific domain orientation

Edit these directly in the `jarvis` repo.

---

## Adding a New Knowledge File to the Sync

1. Create the file in the appropriate `analytics-copilot` source directory (usually `domain/`)
2. Add a `cp` line to `scripts/sync-jarvis.sh` (follow the existing pattern)
3. Run the sync and commit both repos

---

## Who Does What

| Task | Owner |
|---|---|
| Domain knowledge edits | Bridie, Leo, or any Analytics team member |
| Running the sync | Whoever made the edit (usually Bridie) |
| Jarvis agent routing (`agents/jarvis.md`) | Bridie |
| Jarvis-native files (`domain_context.md`, manifest) | Bridie |
| Snowflake MCP connection / infra | Deepak Kumar |

---

## Why This Architecture

`analytics-copilot` has richer context, version history, and team contribution workflows. `jarvis/knowledge/` needs to stay lean (token budget for the plugin). The sync pipeline is the abstraction — not two independent sources of truth. See `domain/decisions_log.md` DEC-004 for the full decision record.
