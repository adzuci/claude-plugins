#!/usr/bin/env python3
"""
check_env.py — Deterministic env scan for token-efficiency-assessment.

Reads Claude Code config files and filesystem to auto-detect 7 token-efficiency
signals that do not require asking the user.

Usage:
    python3 check_env.py
    python3 check_env.py --out /tmp/tea-env.json
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CLAUDE_MD_LINE_THRESHOLD = 200
MCP_COUNT_THRESHOLD = 6  # more than this is flagged as "too many"


def _load_settings():
    """Return merged dict of settings.json values (user → local → project)."""
    paths = [
        Path.home() / ".claude" / "settings.json",
        Path.home() / ".claude" / "settings.local.json",
        Path.cwd() / ".claude" / "settings.json",
        Path.cwd() / ".claude" / "settings.local.json",
    ]
    merged = {}
    for p in paths:
        try:
            merged.update(json.loads(p.read_text()))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return merged


def _sig(score, value, fix=""):
    return {"score": score, "value": value, "fix": fix}


def check_claudeignore():
    candidates = [Path.home() / ".claudeignore", Path.cwd() / ".claudeignore"]
    for p in candidates:
        if p.exists():
            return _sig(1, str(p))
    return _sig(
        0,
        None,
        "Create ~/.claudeignore listing dirs to skip:\n"
        "  node_modules/\n  dist/\n  .git/\n  vendor/\n  tmp/\n  *.log",
    )


def check_claude_md_lean():
    paths = [
        Path.home() / ".claude" / "CLAUDE.md",
        Path.cwd() / "CLAUDE.md",
    ]
    total = 0
    for p in paths:
        try:
            total += len(p.read_text().splitlines())
        except FileNotFoundError:
            pass
    lean = total <= CLAUDE_MD_LINE_THRESHOLD
    fix = (
        ""
        if lean
        else (
            f"CLAUDE.md is {total} lines (threshold: {CLAUDE_MD_LINE_THRESHOLD}). "
            "Remove stale rules, outdated task descriptions, and anything already "
            "enforced by code or CI."
        )
    )
    return _sig(1 if lean else 0, total, fix)


def check_mcp_count():
    settings = _load_settings()
    count = 0

    # Explicit mcpServers key (set via `claude mcp add --global`)
    mcp_servers = settings.get("mcpServers", {})
    count = len(mcp_servers)

    # Try `claude mcp list` for a more accurate live count
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # Lines with "✓ Connected" or "✗" are server entries
        entries = [
            ln
            for ln in result.stdout.splitlines()
            if ": " in ln and ("Connected" in ln or "✗" in ln or "Error" in ln)
        ]
        if entries:
            count = len(entries)
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Fall back to counting enabled marketplace plugins
    if count == 0:
        enabled = settings.get("enabledPlugins", {})
        count = sum(1 for v in enabled.values() if v)

    reasonable = count <= MCP_COUNT_THRESHOLD
    fix = (
        ""
        if reasonable
        else (
            f"{count} MCP servers/plugins are enabled. "
            "Each one adds tokens to every request. "
            "Disable unused ones:\n  claude mcp list\n  claude mcp remove <name>"
        )
    )
    return _sig(1 if reasonable else 0, count, fix)


def check_permission_mode():
    settings = _load_settings()
    mode = settings.get("defaultMode", "default")
    bad = {"auto", "bypassPermissions", "acceptEdits"}
    good = mode not in bad
    fix = (
        ""
        if good
        else (
            f"defaultMode is '{mode}' — auto-accept means Claude goes off-track "
            "without interruption, burning tokens on wrong paths.\n"
            'Set in ~/.claude/settings.json:\n  "defaultMode": "default"'
        )
    )
    return _sig(1 if good else 0, mode, fix)


def check_tool_search_efficient():
    """Score 1 when Tool Search is at the efficient default (all tools deferred on demand).

    The real knob is ENABLE_TOOL_SEARCH in the settings.json env block.
    Unset / 'true' / 'auto' / 'auto:N' with N<=10 all defer tools efficiently.
    'false' loads everything upfront (worst). 'auto:N' with N>10 also loads more upfront.
    """
    settings = _load_settings()
    env_block = settings.get("env", {})
    sentinel = object()
    raw = env_block.get("ENABLE_TOOL_SEARCH", sentinel)
    val = str(raw) if raw is not sentinel else os.environ.get("ENABLE_TOOL_SEARCH")

    if val is None or val == "true":
        return _sig(1, val)

    if val == "false":
        return _sig(
            0,
            val,
            "ENABLE_TOOL_SEARCH=false loads ALL MCP tools upfront on every request.\n"
            "Remove the override to restore the default (full deferral — most efficient):\n"
            "  Remove ENABLE_TOOL_SEARCH from the env block in ~/.claude/settings.json",
        )

    if val == "auto":
        return _sig(1, val)

    if val.startswith("auto:"):
        try:
            pct = int(val.split(":")[1])
            if pct <= 10:
                return _sig(1, val)
            return _sig(
                0,
                val,
                f"ENABLE_TOOL_SEARCH={val} loads tools upfront when they fit in {pct}% of context.\n"
                "The default (unset) defers all tools — the most efficient setting.\n"
                "If you want threshold mode, use auto:3 or lower:\n"
                '  "ENABLE_TOOL_SEARCH": "auto:3"  # in env block of ~/.claude/settings.json',
            )
        except (IndexError, ValueError):
            pass

    return _sig(1, val)


def check_default_model():
    settings = _load_settings()
    model = settings.get("model", "")
    if not model or "opus" in model.lower():
        return _sig(
            0,
            model or None,
            "Default model is Opus (or unset, defaulting to Opus). "
            "Set Sonnet as your default and reach for Opus only when the task needs deep reasoning:\n"
            '  "model": "claude-sonnet-4-6"  # in ~/.claude/settings.json',
        )
    return _sig(1, model)


def check_memory_populated():
    dirs = list(Path.home().glob(".claude/projects/*/memory"))
    dirs.append(Path.home() / ".claude" / "memory")
    has = any(d.is_dir() and any(d.iterdir()) for d in dirs if d.exists())
    fix = (
        ""
        if has
        else (
            "No memory files found. Caching repeated MCP lookups or context in "
            "~/.claude/memory/ prevents redundant tool calls on every session.\n"
            "Use /remember or the Write tool to save stable reference data."
        )
    )
    return _sig(1 if has else 0, has, fix)


def _collect_info(settings):
    env_block = settings.get("env", {})
    return {
        "model_configured": settings.get("model"),
        "ccflare_configured": bool(
            env_block.get("ANTHROPIC_BASE_URL")
            or os.environ.get("ANTHROPIC_BASE_URL")
        ),
        "autocompact_override": env_block.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"),
        "default_mode": settings.get("defaultMode", "default"),
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Claude Code env for token efficiency signals.")
    parser.add_argument("--out", metavar="FILE", help="Write JSON to file (default: stdout)")
    args = parser.parse_args()

    settings = _load_settings()

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "signals": {
            "claudeignore_configured": check_claudeignore(),
            "claude_md_lean": check_claude_md_lean(),
            "mcp_count_reasonable": check_mcp_count(),
            "permission_mode_non_auto": check_permission_mode(),
            "tool_search_efficient": check_tool_search_efficient(),
            "memory_populated": check_memory_populated(),
            "default_model_not_opus": check_default_model(),
        },
        "info": _collect_info(settings),
    }

    output = json.dumps(report, indent=2)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Env report written to {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
