# Jarvis Health Playbook

**Owner:** Bridie Meredith
**Updated:** 2026-03-31
**Audience:** internal-admin — Analytics team, Leo, Bridie, Deepak (not for exec-facing responses)
**Load-on:** jarvis-admin, setup, sync, update-protocol

How to keep Jarvis accurate, current, and improving. Covers three systems: the knowledge sync pipeline, the weekly business context refresh, and the quality scorecard.

---

## Mental Model

Jarvis answers questions by reading two things: **Snowflake** (live data) and **`jarvis/knowledge/`** (structured context). `jarvis/knowledge/` is not edited directly — it's a read-only export generated from `analytics-copilot`. All Jarvis improvements start in `analytics-copilot`.

```
You edit here:                         Jarvis reads here:
analytics-copilot/
  domain/           ─┐
  data-catalog/      ├─ sync-jarvis.sh ──→  jarvis/knowledge/
  metrics/           │                            │
  sql/              ─┘                            ↓
                                           Jarvis plugin answers
```

**Rule:** Never edit `jarvis/knowledge/` files directly (except `domain_context.md` and `JARVIS_KNOWLEDGE_BASE_MANIFEST.md`, which are Jarvis-native).

---

## System 1 — Knowledge Sync

**What it does:** Pushes domain knowledge from `analytics-copilot` to `jarvis/knowledge/` so the plugin has current context.

**When to run:** After any edit to files in `domain/`, `data-catalog/context/`, `metrics/`, `data-catalog/glossary_entries.md`, or `domain/sql_patterns.md`.

### How to run

```bash
/sync-jarvis
```

That skill runs `scripts/sync-jarvis.sh`, commits `analytics-copilot`, and commits `jarvis/knowledge/`. It's the only approved way to update Jarvis's knowledge base.

Or manually:
```bash
bash scripts/sync-jarvis.sh
# then commit analytics-copilot and jarvis separately
```

### What gets synced

| Source (analytics-copilot) | Destination (jarvis/knowledge/) |
|---|---|
| `sql/lu_saved_metrics.sql` | `lu_saved_metrics.sql` |
| `data-catalog/glossary_entries.md` | `glossary_entries.md` |
| `domain/sql_patterns.md` | `sql_patterns.md` |
| `metrics/*.md` | `metrics/` |
| `data-catalog/context/*.md` | `context/` |
| `domain/product_debrief_template.md` | `product_debrief_template.md` |
| 15 named `domain/*.md` files (see `sync-jarvis.sh`) | `knowledge/` root |
| `plugin/claude-plugins-export/knowledge/team_roster.md` | `team_roster.md` |

### What does NOT get synced (edit these directly in jarvis)
- `jarvis/knowledge/domain_context.md` — Jarvis-specific orientation doc
- `jarvis/knowledge/JARVIS_KNOWLEDGE_BASE_MANIFEST.md` — Jarvis's own index

### Adding a new file to the sync

1. Create the file in `analytics-copilot/domain/` (or appropriate source directory)
2. Add a `cp` line to `scripts/sync-jarvis.sh`
3. Run `/sync-jarvis`

---

## System 2 — Weekly Business Context Refresh

**What it does:** Compiles a weekly intelligence update from Slack, repo changes, Snowflake metrics, and meeting transcripts into a dated artifact, then optionally merges it into `domain/business_state.md`.

**Why it matters:** `business_state.md` is what Jarvis reads when an exec asks "how are we doing on X?" Without weekly refreshes it goes stale and Jarvis answers with outdated numbers.

**When to run:** Monday morning (or Friday EOD). Target: once per week.

### How to run

```bash
/weekly-context-refresh
```

Stage 1 (always runs): gathers Slack signals, repo changes, metric reads, and product insights → writes `domain/weekly_updates/YYYY-MM-DD.md`.

Stage 2 (requires your confirmation): uses Opus to synthesize the weekly update into `domain/business_state.md`, then syncs to Jarvis.

### Flags

| Flag | Effect |
|---|---|
| `--skip-slack` | Skip Slack gather (use if Slack auth is unavailable) |
| `--skip-snowflake` | Skip metric reads (use if Snowflake auth is unavailable) |
| `--skip-merge` | Write the weekly update doc only; do not prompt for Stage 2 merge |
| `--dry-run` | Print compiled update to stdout; no file writes |

### What it produces

- `domain/weekly_updates/YYYY-MM-DD.md` — dated artifact, kept permanently (version history)
- `domain/business_state.md` — merged, updated in place (this is what Jarvis reads)

After Stage 2 completes, run `/sync-jarvis` to push the updated `business_state.md` to the plugin.

### What it pulls from

1. **Slack** — `#dept-analytics-updates`, past 7 days: decisions, blockers, metric callouts, directional shifts
2. **Repo changes** — `scripts/sweep_recent_changes.py --days 7`: new domain files, updated metrics, schema changes (skips mechanical commits)
3. **Snowflake** — `scripts/export_registry.py`: current values for OKR metrics in `business_state.md`
4. **Product insights** — meeting transcripts in `teammates/*/meeting_transcripts/`, `domain/business_state.md` current state

---

## System 3 — Quality Scorecard

**What it does:** Poses a bank of known-answer questions to a live Jarvis subagent, grades the responses on 5 dimensions, and tracks quality over time.

**Why it matters:** Detects regressions when domain files change, knowledge gaps when new exec questions come in, and guardrail violations before they reach real users.

**When to run:** After any significant knowledge sync, or on a regular cadence (weekly or biweekly).

### How to run

```bash
/jarvis-eval run                       # all active questions
/jarvis-eval run --subset 5            # quick spot-check (5 random)
/jarvis-eval run --category guardrail  # guardrail tests only
```

Results land in `domain/scorecard/runs/YYYY-MM-DD_HHMMSS.md`.

### One-time setup

The skill needs to know where your local `jarvis/` repo lives:

```bash
echo "/path/to/your/jarvis" > .jarvis_path
# e.g.: echo "/Users/bridie.meredith/workspace/jarvis" > .jarvis_path
```

If `.jarvis_path` is absent, it defaults to `../jarvis`. `.jarvis_path` is gitignored (like `.snowflake_user`).

### Grading dimensions

| Dimension | Weight | What it checks |
|---|---|---|
| Source Selection | 25% | Did Jarvis use the correct/authoritative table? |
| Filter Correctness | 25% | Right population, date range, and segment filters? |
| Answer Accuracy | 20% | Numbers within expected range, correct calculations? |
| Guardrail Compliance | 20% | Did Jarvis avoid known failure modes? |
| Presentation | 10% | Clean output, source cited, follow-ups offered? |

**Pass:** weighted score ≥ 75, no dimension < 50
**Soft fail:** score ≥ 60 but one dimension < 50
**Hard fail:** source selection or filter correctness < 50
**Critical fail:** guardrail compliance < 50 (answer is misleading — act immediately)

### Tracking trends

```bash
python3 scripts/eval_trends.py              # summary table, all runs
python3 scripts/eval_trends.py --last 10    # last 10 runs
python3 scripts/eval_trends.py --dimension  # per-dimension breakdown
python3 scripts/eval_trends.py --csv        # CSV for spreadsheet
```

### Growing the question bank

```bash
/jarvis-eval update   # auto-mine 4 sources for new test case candidates
/jarvis-eval add      # interactive manual addition
```

New cases start as `status: draft`. Promote to `active` only after validating the expected answer against real Snowflake output. Never promote a draft you haven't independently verified.

The 4 mining sources (in priority order):
1. Product Insights (`business_state.md`, weekly updates, meeting transcripts)
2. DS/AE Outputs (teammate directories, weekly signals, Slack)
3. Metric Definitions (`metrics/`, `data-catalog/`)
4. Snowflake Query History (actual DS/AE queries, last 30 days)

---

## Recommended Cadence

| Frequency | Task |
|---|---|
| **After every domain edit** | Run `/sync-jarvis` |
| **Weekly (Monday)** | Run `/weekly-context-refresh` → confirm merge → run `/sync-jarvis` |
| **Biweekly or after significant syncs** | Run `/jarvis-eval run` and check trend |
| **Monthly** | Run `/jarvis-eval update` to mine new test cases; promote validated drafts |
| **On critical fail** | Fix the underlying knowledge file immediately, re-sync, re-run eval |

---

## Escalation

| Symptom | Action |
|---|---|
| Jarvis returns stale metric values | Run `/weekly-context-refresh` + `/sync-jarvis` |
| Jarvis uses wrong table for a query | Update `data-catalog/context/` and `domain/sql_patterns.md`; sync |
| Guardrail compliance < 50 in eval | Find and fix the misleading knowledge file before next exec interaction |
| Snowflake MCP broken | Use `scripts/snowflake_query.py` instead; escalate to Deepak Kumar |
| Sync script fails on a missing file | Check `sync-jarvis.sh` — file was deleted or renamed; update the script |

---

## Files Reference

| File | Purpose |
|---|---|
| `scripts/sync-jarvis.sh` | Canonical sync script — authoritative list of what gets copied |
| `domain/jarvis_update_protocol.md` | Shareable protocol doc for anyone updating Jarvis knowledge |
| `domain/jarvis_action_log.md` | Running tracker: completed improvements, in-progress, backlog |
| `domain/decisions_log.md` | Architectural decision log (DEC-XXX format) |
| `domain/business_state.md` | Live business context — what Jarvis reads for exec questions |
| `domain/weekly_updates/` | Dated weekly update artifacts (immutable history) |
| `domain/scorecard/question_bank.yaml` | All eval test cases |
| `domain/scorecard/runs/` | Timestamped eval run reports |
| `domain/scorecard/update_sources.md` | Mining logic for auto-generating new test cases |
| `scripts/eval_trends.py` | Trend aggregation script |
