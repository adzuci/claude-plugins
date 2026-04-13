# Jarvis Knowledge Base

This directory is Jarvis's live knowledge — domain context, metric definitions, table documentation, and business state that Jarvis loads to answer executive questions.

**All files here (except `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` and `domain_context.md`) are managed by one-way sync from `analytics-copilot`.** Do not edit them directly. Changes will be overwritten on the next sync.

---

## How Knowledge Gets Into Jarvis

```
analytics-copilot/           jarvis/knowledge/
  domain/          ──┐
  data-catalog/    ──┤  scripts/sync-jarvis.sh  ──►  (this directory)
  metrics/         ──┤  (run: /sync-jarvis)
  sql/             ──┘
```

The sync is one-way and intentional. `analytics-copilot` has version history, team contribution workflows, and richer context. `jarvis/knowledge/` stays lean (token budget for the plugin). The sync script is the abstraction — not two independent sources of truth.

### To update something Jarvis knows

1. Find the source file in `analytics-copilot` (usually `domain/`)
2. Edit it there
3. Run `/sync-jarvis` (or `bash scripts/sync-jarvis.sh` + commit both repos)

### To add a new knowledge file

1. Create the file in `analytics-copilot/domain/` (or appropriate subdirectory)
2. Add it to `analytics-copilot/domain/SYNC_MANIFEST.md`
3. Add a `cp` line to `analytics-copilot/scripts/sync-jarvis.sh`
4. Run `/sync-jarvis`

---

## What's In Here

### Strategy & Business Context (Tier 1 — Jarvis reads these first)

| File | What it is |
|---|---|
| `business_state.md` | Current momentum snapshot — NRR, activation, product bets, known risks. **Updated weekly via `/weekly-context-refresh`.** |
| `annual_targets.md` | FY27 OKR targets by metric. Jarvis uses this to answer "are we on track?" |
| `theory_of_change.md` | Causal chain: activation → habit → retention → expansion. Why the strategy makes sense. |
| `product_portfolio_taxonomy.md` | H1/H2/H3 classification + graduation criteria. What's a bet vs. a core product. |
| `pending_definitions.md` | Known data gaps, fallback responses, and ETAs. Jarvis uses this to explain what it can't answer yet. |
| `product_disambiguation.md` | "Product" means four different things. This tells Jarvis which lens to use. |

### Metric Methodologies (Tier 2 — loaded when the question is metric-specific)

| File | Metric |
|---|---|
| `activation_methodology.md` | F14D Habit RA Rate |
| `churn_taxonomy_draft.md` | Churn reasons by category |
| `ai_sheets_user_definition.md` | GTM Engineer cohort definition |
| `inbound_team_identification.md` | Inbound add-on revenue attribution |
| `metrics/*.md` | AE-owned metric definitions (FTP rate, M3 NRR, etc.) |

### Domain Knowledge (Tier 3 — SQL, patterns, operations)

| File | What it is |
|---|---|
| `sql_patterns.md` | Canonical SQL patterns for common analytical questions |
| `segment_join_canonical.md` | How to join segment data — authoritative path |
| `lu_team_segment_patterns.md` | Reusable SQL for segment-sliced queries |
| `glossary_entries.md` | Metric and term definitions |
| `lu_saved_metrics.sql` | Registry SQL for saved metrics |
| `decisions_log.md` | Architecture and methodology decisions |
| `jarvis_update_protocol.md` | How to update this knowledge base |
| `jarvis_action_log.md` | Improvements shipped + backlog |

### Table Context (one file per approved Snowflake table)

| Path | What it is |
|---|---|
| `context/*.md` | ~80 table context files — schema, trust tier, join patterns, caveats |

Jarvis uses these for query grounding. Every approved table has a file. The validator enforces this.

### Other

| File | What it is |
|---|---|
| `product_debrief_template.md` | Standard template for product debrief analyses |
| `team_roster.md` | Apollo team roster (from plugin export) |
| `annual_targets.md` | FY27 OKR targets |

---

## Files NOT Managed by Sync (edit directly in this repo)

| File | Why |
|---|---|
| `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` | Jarvis's capability inventory — jarvis-native |
| `domain_context.md` | Auto-generated from `analytics-copilot/domain/index.md`; regenerated separately via `scripts/build_domain_context.py` |

---

## Sync Reference

| Resource | Location |
|---|---|
| Sync script | `analytics-copilot/scripts/sync-jarvis.sh` |
| Sync manifest (authoritative file list) | `analytics-copilot/domain/SYNC_MANIFEST.md` |
| Skill (recommended way to sync) | `/sync-jarvis` in analytics-copilot |
| Weekly context refresh | `/weekly-context-refresh` in analytics-copilot — updates `business_state.md` then syncs |
| Update protocol | `analytics-copilot/domain/jarvis_update_protocol.md` (also synced here as `jarvis_update_protocol.md`) |
