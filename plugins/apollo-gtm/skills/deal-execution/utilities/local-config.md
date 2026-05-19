# Local Config — Persistent User Preferences

Manages a local YAML config file on the AE's machine that persists identity,
triage preferences, and session state across all sessions. This file is read
on every session start and written during preflight or when the AE changes
settings. No skill should ask the AE for information that is already stored
in this file.

---

## Purpose

The Claude skill environment resets between sessions. Any configuration stored
inside the skill files themselves (like `{{PLACEHOLDER}}` markers in orchestrator
config blocks) is not user-specific and does not persist across installs. This
config file solves that by storing all user-specific state on the local filesystem
where it survives session resets.

**What belongs here:**
- Identity (email, domains, Slack ID, timezone)
- Triage preferences (volume bounds, filtering mode, time windows)
- Feature flags (onboarding state, optional connectors detected)
- Timestamps (last triage run, last preflight)

**What does NOT belong here:**
- Task data (that's `tasks.yaml` — managed by task-tracker)
- Deal content, email bodies, or pipeline output
- Anything that changes per-request (use in-session state for that)

---

## Directory Structure

```
~/Documents/apollo-gtm/
├── config.yaml          # User identity + preferences (this spec)
├── tasks/
│   ├── tasks.yaml       # Task tracker operational data
│   └── tasks-archive.yaml
```

**Migration note:** task-tracker v2.2 uses `~/Documents/tasks/tasks.yaml`. With
this change, the task directory moves under `~/Documents/apollo-gtm/tasks/`. On
first run, if `~/Documents/tasks/tasks.yaml` exists and `~/Documents/apollo-gtm/tasks/`
does not, move the existing files to the new location. Leave a symlink at the old
path for backward compatibility.

---

## File Location

Default: `~/Documents/apollo-gtm/config.yaml`

### Cowork Environment

The config file lives on the Mac filesystem, not in the sandbox. Access requires
mounting the directory before any file I/O.

```
# Mount (required before any read/write)
request_cowork_directory with path: ~/Documents

# Effective paths
Config (Mac):   ~/Documents/apollo-gtm/config.yaml
Config (VM):    /sessions/<session-id>/mnt/Documents/apollo-gtm/config.yaml
Tasks (Mac):    ~/Documents/apollo-gtm/tasks/tasks.yaml
Tasks (VM):     /sessions/<session-id>/mnt/Documents/apollo-gtm/tasks/tasks.yaml
```

### Resolution Order on Load

1. Mount `~/Documents` via `request_cowork_directory` if not already mounted.
2. Check if `~/Documents/apollo-gtm/config.yaml` exists.
3. If it exists, read it. All fields are now available — do not re-ask.
4. If it does not exist, run preflight (PREFLIGHT.md) which creates it.
5. If specific fields are missing (e.g., file exists but `triage_config` absent),
   use defaults for missing fields. Do not block the session.

### CLAUDE.md Integration

Add to the AE's `~/.claude/CLAUDE.md`:

```markdown
## Apollo GTM Config
Config file: ~/Documents/apollo-gtm/config.yaml
Task file: ~/Documents/apollo-gtm/tasks/tasks.yaml
```

This ensures any Claude session knows where to find the files without
hardcoding paths in skill files.

---

## Config Schema

```yaml
# Apollo GTM System — User Configuration
# Written by PREFLIGHT.md, read by ROUTER.md on every session start.
# Do not edit manually unless you know what you're doing.
# Last updated: {ISO 8601 timestamp}

schema_version: 1

# ─── Identity ─────────────────────────────────────────────
# Set during preflight auto-detection. Changeable via "change settings."
identity:
  seller_email: "jane.smith@apollo.io"
  seller_domains: ["apollo.io"]
  internal_domains: ["apollo.io"]
  slack_user_id: "U0ABC123DEF"
  timezone: "America/Denver"

# ─── Triage Preferences ──────────────────────────────────
# Set during preflight Triage Preferences step.
# Controls how inbox-triage.md gathers and filters email in Phase 1.
triage_config:
  # Mode: how aggressively to filter incoming threads.
  #   "all"           — scan all unread threads in the time window (default)
  #   "sales_focused" — full pipeline for prospect/customer/deal threads,
  #                     lightweight scan for everything else
  #   "b2b_only"      — skip internal-only threads and automated notifications,
  #                     process only external business email
  mode: "all"

  # Volume bounds: hard caps on what Phase 1 pulls.
  max_threads: 25            # Max threads per triage run (5-50, default 25)
  max_turns_per_thread: 10   # Max turns to pull per thread (3-25, default 10)

  # Time window overrides (in hours). Null = use default.
  # Defaults: AM = 13h (6pm prior day), PM = 10h (7am today)
  lookback_hours_am: null    # Override AM window (4-24)
  lookback_hours_pm: null    # Override PM window (4-24)

  # Priority ordering: when max_threads cap is hit, which threads to keep.
  #   "recency"  — most recent first (default)
  #   "apollo"   — Apollo-enriched contacts first, then recency
  #   "starred"  — starred/important first, then recency
  priority: "recency"

# ─── Connectors ───────────────────────────────────────────
# Detected during preflight. Updated when preflight is re-run.
connectors:
  gmail: true
  gcal: true
  slack: true
  apollo_mcp: false          # true if Apollo MCP verified during preflight
  google_drive: false
  notion: false
  granola: false

# ─── State ────────────────────────────────────────────────
# System-managed timestamps and flags. Do not edit.
state:
  onboarding_complete: false
  preflight_passed: true
  preflight_date: "2026-04-15T16:30:00-06:00"
  last_triage_am: null       # ISO 8601 timestamp of last AM triage
  last_triage_pm: null       # ISO 8601 timestamp of last PM triage
  inbox_volume_estimate: 22  # Threads/day detected during preflight probe
```

### Field Validation

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `schema_version` | int | yes | 1 | Must equal 1 |
| `identity.seller_email` | string | yes | — | Must contain @ |
| `identity.seller_domains` | string[] | yes | — | At least 1 |
| `identity.internal_domains` | string[] | yes | — | At least 1 |
| `identity.slack_user_id` | string | yes | — | Must start with U |
| `identity.timezone` | string | yes | — | Valid IANA timezone |
| `triage_config.mode` | enum | no | "all" | all, sales_focused, b2b_only |
| `triage_config.max_threads` | int | no | 25 | 5-50 |
| `triage_config.max_turns_per_thread` | int | no | 10 | 3-25 |
| `triage_config.lookback_hours_am` | int/null | no | null | 4-24 if set |
| `triage_config.lookback_hours_pm` | int/null | no | null | 4-24 if set |
| `triage_config.priority` | enum | no | "recency" | recency, apollo, starred |
| `connectors.*` | bool | no | false | — |
| `state.onboarding_complete` | bool | no | false | — |

### Read Protocol

1. Mount the directory.
2. Read the file.
3. Validate `schema_version`. If missing or wrong version, warn and re-run preflight.
4. For any missing field, use the default from the table above. Do not prompt.
5. Store the loaded config in session memory for the duration of the session.
6. **Never re-ask for information that exists in the config file.**

### Write Protocol

1. Read the existing file first (preserve fields you're not updating).
2. Merge updates into the existing structure.
3. Update `last_updated` timestamp in the YAML comment header.
4. Write the complete file back (full overwrite, not append).
5. Confirm write succeeded. If the directory doesn't exist, create it.

### When to Write

| Trigger | What Gets Written |
|---|---|
| Preflight completes | Full config (identity, connectors, triage_config, state) |
| AE changes settings | Updated field(s) only (merge write) |
| Onboarding completes | `state.onboarding_complete: true` |
| Triage runs | `state.last_triage_am` or `state.last_triage_pm` timestamp |
| AE changes triage prefs | `triage_config` section |

---

## Relationship to Other Files

| File | Relationship |
|---|---|
| `ROUTER.md` | Reads config on session start (Step 0). Uses identity + onboarding state. |
| `PREFLIGHT.md` | Creates and writes the config file. Runs auto-detection + preferences. |
| `inbox-triage.md` | Reads `triage_config` at Phase 1 start. Reads `identity` for seller context. |
| `ONBOARDING.md` | Settings help topic tells AE how to change values in the config. |
| `task-tracker.md` | Sibling file in same parent directory. Independent read/write. |
| `gense/gense.md` | Reads `identity` for seller context (seller_email, seller_domains). |

---

## Migration from Inline Config

Before v3.3.0, seller identity was stored as `{{PLACEHOLDER}}` markers in
`orchestrators/inbox-triage.md` and `gense/gense.md`. With this change:

1. Orchestrator config blocks remain as documentation/fallback, but are no longer
   the source of truth.
2. On session start, ROUTER.md reads the local config file. If it exists, those
   values override any inline config block values.
3. If the local config file does not exist, the system falls back to the inline
   config blocks (backward compatible).
4. Preflight always writes the local config file, so after the first preflight
   run, the local file becomes authoritative.
