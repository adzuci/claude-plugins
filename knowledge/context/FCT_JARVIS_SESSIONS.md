# FCT_JARVIS_SESSIONS

> Jarvis's own session log — every interaction across analytics-copilot and jarvis repos.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_JARVIS_SESSIONS` |
| **Grain** | One row per logged event (session start, interaction, end) per session per user |
| **Row count** | Small — ~tens to low hundreds per active user per week |
| **Refresh cadence** | Event-triggered via Stop hook → buffered in `session_registry.jsonl` → flushed via `/jarvis` skill (Claude-mediated MCP write) |
| **Coverage period** | ongoing |
| **Trust level** | Use with caution — Claude-mediated flush means silent undercount when flush is skipped |
| **Owner** | Bridie Meredith |
| **DAG** | None — event-driven, not DAG-produced |

## Description

Canonical fact table for Jarvis usage analytics. Every Stop-hook fire and explicit `end` call from `scripts/log_session.py` buffers one JSONL row locally, then flushes to this table when the `/jarvis` skill runs (which calls `log_session.py sql` → MCP `write_query` → `log_session.py mark_flushed`).

Used to prove Jarvis impact (sessions × est_min_saved), monitor adoption per teammate, split usage between copilot and jarvis repos, and identify stale zones (no activity ≥ 14 days).

## Upstream Sources

| Source | Relationship |
|---|---|
| `analytics-copilot/teammates/<name>/session_registry.jsonl` | Per-teammate local buffer, flushed by Claude |
| `jarvis/session_registry.jsonl` | Repo-root buffer for jarvis-side sessions |
| Stop hook in `.claude/settings.json` | Triggers `log_session.py` on every Claude turn end |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `timestamp` | TIMESTAMP_TZ | UTC timestamp of the event | ISO-8601 with timezone |
| `user_email` | STRING | Resolved from `git config user.email` | Fallback: `$USER` env var, else `unknown` |
| `session_id` | STRING | UUID per Claude session | From `/tmp/jarvis_session_id.txt` or hook payload |
| `stop_reason` | STRING | Stop hook reason (`end_turn`, `tool_use`, etc.) | `unknown` for start / explicit end events |
| `platform` | STRING | `analytics-copilot` or `jarvis` | Derived from repo root (presence of `teammates/` dir) |
| `event` | STRING | `start`, `interaction`, or `end` | `interaction` is the default Stop-hook event |
| `activity` | VARIANT | Enriched payload: action, question, all_actions, tables_used, interaction_count, est_min_saved | Parsed JSON — query with `activity:action::STRING` etc. |

## How It's Used

### Common query patterns

```sql
-- Weekly sessions per user × platform
SELECT DATE_TRUNC('week', timestamp) AS week, user_email, platform, COUNT(DISTINCT session_id) AS sessions
FROM ANALYTICS_DB.PLAYGROUND.FCT_JARVIS_SESSIONS
WHERE event = 'interaction' AND timestamp >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2, 3
ORDER BY 1 DESC, sessions DESC;

-- Top actions inferred from transcripts
SELECT activity:action::STRING AS action, COUNT(*) AS n
FROM ANALYTICS_DB.PLAYGROUND.FCT_JARVIS_SESSIONS
WHERE event = 'interaction' AND timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY n DESC;

-- Tables referenced in Jarvis sessions (signal-mining for catalog gaps)
SELECT value::STRING AS table_name, COUNT(DISTINCT session_id) AS sessions
FROM ANALYTICS_DB.PLAYGROUND.FCT_JARVIS_SESSIONS,
     LATERAL FLATTEN(input => activity:tables_used)
WHERE event = 'interaction'
GROUP BY 1 ORDER BY sessions DESC LIMIT 50;
```

### Key consumers

- `scripts/usage_sweep.py --snowflake` — team-wide usage reporting (blends this table with `teammates/*/usage_log.md`)
- `scripts/jarvis_usage_report.py` — complementary report via `QUERY_HISTORY` (query-tag path, not this table)
- Pepper's weekly sweeps — adoption gap detection

## Known Issues & Gotchas

- **Flush is Claude-mediated, not autonomous.** If `/jarvis` skill never fires, buffer entries stay `sf_logged=false` and never reach this table. Silent undercount. Check `session_registry.jsonl` for entries with `sf_logged: false` older than 24h.
- **`activity.action` is regex-heuristic**, extracted from the last user message by `log_session.py`. Not authoritative — treat as a coarse bucket.
- **`activity.tables_used` is noisy** — extracted by regex matching ALL-CAPS tokens from the turn transcript. Contains false positives like `A`, `THE`, `CURRENT`, `RECENT`. Filter to known catalog tables before trusting.
- **`est_min_saved` is only set on explicit `log_session.py end` calls.** Most Stop-hook interactions have no min_saved value. Use `teammates/*/usage_log.md` for min-saved totals, not this table alone.
- **Platform split is repo-root-based, not runtime-based.** If log_session.py runs from a different cwd, platform may be mislabeled.
- **Buffer truncates to last 50 records on flush** (`cmd_mark_flushed` writes only `records[-50:]`). If flush is delayed and buffer exceeds 50 unflushed entries, older entries are lost on next flush.

-

## Slack Context

-

## Business Terms

| Term | Definition |
|---|---|
| Flush | The act of moving unflushed JSONL rows from `session_registry.jsonl` to this table via MCP |
| Session | One Claude conversation, identified by `session_id` UUID |
| Platform | Which repo the session ran in: `analytics-copilot` (hub) or `jarvis` (plugin surface) |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Created context file (previously uncatalogued despite being the core Jarvis usage table) | Bridie |
