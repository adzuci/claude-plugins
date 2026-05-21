#!/usr/bin/env bash
# session-start.sh — Athena SessionStart hook
#
# Runs on every Athena session start. Output is printed to Claude's context.
# Failures are non-fatal — errors are warnings, not blockers.
#
# Note: Snowflake user profiling and Notion tool-inventory refresh happen
# via MCP inside Claude (see agents/athena.md "On session start"). This
# script handles only the shell-executable setup tasks.

set -uo pipefail

# 1. Ensure gap-log directory exists so Athena can always write to it.
GAP_LOG_DIR="${HOME}/.claude/data/athena"
mkdir -p "${GAP_LOG_DIR}" 2>/dev/null \
  && echo "[session-start] gap-log dir ready: ${GAP_LOG_DIR}/gap-log.jsonl" \
  || echo "[session-start] WARN: could not create ${GAP_LOG_DIR} — gap logging may fail"

# 2. Echo today's date for use in inline citations.
echo "[session-start] date: $(date -u +%Y-%m-%d)"

# 3. Remind Claude to run the startup profile via MCP before first response.
echo "[session-start] action required: query Snowflake dim_teams_analyst (or fallback chain) to build user profile before responding. See agents/athena.md 'On session start'."
