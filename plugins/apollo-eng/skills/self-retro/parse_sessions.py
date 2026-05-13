#!/usr/bin/env python3
"""
parse_sessions.py — Session discovery, parsing, and context builder for /reflect.

Usage:
    python3 parse_sessions.py [--days N] [--sessions N] [--project-hash HASH]

Outputs a structured transcript to stdout, ready for the Claude analysis prompt.
"""

import os
import glob
import json
import sys
import argparse
from datetime import datetime, timedelta


# ─── Session Discovery ────────────────────────────────────────────────────────

def is_real_session(jsonl_path: str) -> bool:
    """Skip ghost sessions (queue-operation-only files with no real user turns)."""
    with open(jsonl_path, "r", errors="replace") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "user":
                    # Make sure it's a human turn, not a tool result injected as user role
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    # Skip pure tool_result user messages (no text content)
                    if isinstance(content, list):
                        has_text = any(
                            b.get("type") == "text" and b.get("text", "").strip()
                            for b in content
                        )
                        if not has_text:
                            continue
                    elif isinstance(content, str) and content.strip():
                        return True
                    if isinstance(content, list) and has_text:
                        return True
            except (json.JSONDecodeError, UnboundLocalError):
                continue
    return False


def discover_sessions(days: int = 14, max_sessions: int = None, project_hash: str = None) -> list:
    """
    Return a list of session dicts filtered by time window and/or project hash.

    Each dict: { path, project, modified }
    Sorted newest-first. Ghost sessions are excluded.
    """
    base = os.path.expanduser("~/.claude/projects")
    cutoff = datetime.now() - timedelta(days=days)

    if project_hash:
        search_base = os.path.join(base, project_hash)
        if not os.path.isdir(search_base):
            print(f"[reflect] ERROR: project-hash directory not found: {search_base}", file=sys.stderr)
            sys.exit(1)
        pattern = f"{search_base}/*.jsonl"
    else:
        pattern = f"{base}/**/*.jsonl"

    sessions = []
    for jsonl_path in glob.glob(pattern, recursive=True):
        mtime = datetime.fromtimestamp(os.path.getmtime(jsonl_path))
        if mtime < cutoff:
            continue
        if not is_real_session(jsonl_path):
            continue
        project_dir = os.path.basename(os.path.dirname(jsonl_path))
        sessions.append({
            "path": jsonl_path,
            "project": project_dir,
            "modified": mtime,
        })

    sessions.sort(key=lambda s: s["modified"], reverse=True)

    if max_sessions is not None:
        sessions = sessions[:max_sessions]

    return sessions


# ─── Message Extraction ───────────────────────────────────────────────────────

def extract_messages(jsonl_path: str) -> list:
    """
    Parse a session JSONL file and return a list of message dicts.

    Handles both content formats:
      - content as a plain string
      - content as an array of blocks
    Only returns messages with non-empty text.
    """
    messages = []
    with open(jsonl_path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Only process real conversation turns
            if entry.get("type") not in ("user", "assistant"):
                continue

            msg = entry.get("message", {})
            role = msg.get("role")
            content = msg.get("content", "")

            # Handle both content formats (both coexist in the wild)
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = " ".join(
                    block.get("text", "")
                    for block in content
                    if block.get("type") == "text"
                )
            else:
                text = ""

            text = text.strip()
            if not role or not text:
                continue

            messages.append({
                "role": role,
                "text": text,
                "timestamp": entry.get("timestamp"),
                "cwd": entry.get("cwd"),
                "gitBranch": entry.get("gitBranch"),
            })

    return messages


# ─── Role Detection ───────────────────────────────────────────────────────────

def detect_role_hint(sessions: list) -> str:
    """
    Infer the engineer's primary domain from cwd paths across sessions.
    Returns one of: frontend | backend | quality | data | mixed
    """
    frontend_signals = ("assets/", "chrome-extension/", "packages/design-system", "frontend/")
    backend_signals = ("packs/", "app/controllers", "app/models", "lib/", "db-migration")
    quality_signals = ("spec/", "test/", "playwright/", "e2e/")
    data_signals = ("etl/", "pipeline/", "dbt/", "airflow/", "analytics/")

    counts = {"frontend": 0, "backend": 0, "quality": 0, "data": 0}
    for session in sessions:
        messages = extract_messages(session["path"])
        for msg in messages:
            cwd = msg.get("cwd") or ""
            matched = False
            for sig in frontend_signals:
                if sig in cwd:
                    counts["frontend"] += 1
                    matched = True
                    break
            if not matched:
                for sig in backend_signals:
                    if sig in cwd:
                        counts["backend"] += 1
                        matched = True
                        break
            if not matched:
                for sig in quality_signals:
                    if sig in cwd:
                        counts["quality"] += 1
                        matched = True
                        break
            if not matched:
                for sig in data_signals:
                    if sig in cwd:
                        counts["data"] += 1
                        break

    dominant = max(counts, key=counts.get)
    if counts[dominant] == 0:
        return "mixed"
    total = sum(counts.values())
    if total > 0 and counts[dominant] / total < 0.5:
        return "mixed"
    return dominant


# ─── Context Builder ──────────────────────────────────────────────────────────

def build_context(sessions: list, role_hint: str = "mixed") -> str:
    """
    Flatten all sessions into a structured transcript string for the analysis prompt.

    Prepends a CONTEXT block with session metadata and role_hint so the analysis
    prompt can adapt its operational dimension accordingly.

    - User messages kept in full (primary signal — engineer's thinking)
    - Assistant messages truncated to 1500 chars to manage context window
    """
    if sessions:
        dates = [s["modified"] for s in sessions]
        start_date = min(dates).strftime("%Y-%m-%d")
        end_date = max(dates).strftime("%Y-%m-%d")
    else:
        start_date = end_date = "unknown"

    context_header = (
        f"=== CONTEXT ===\n"
        f"sessions_analyzed: {len(sessions)}\n"
        f"date_range: {start_date} to {end_date}\n"
        f"role_hint: {role_hint}\n"
        f"=== END CONTEXT ==="
    )

    context_parts = [context_header]

    for session in sessions:
        messages = extract_messages(session["path"])
        if not messages:
            continue

        project_label = session["project"].replace("-", "/").lstrip("/")
        date_label = session["modified"].strftime("%Y-%m-%d")
        context_parts.append(f"\n--- Session: {project_label} ({date_label}) ---")

        for msg in messages:
            if msg["role"] == "user":
                prefix = "Engineer"
                text = msg["text"]          # full engineer message — primary signal
            else:
                prefix = "Claude"
                # Truncate long responses; keep leading context visible
                text = (msg["text"][:1500] + "... [truncated]") if len(msg["text"]) > 1500 else msg["text"]

            context_parts.append(f"{prefix}: {text}")

    return "\n".join(context_parts)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="/reflect session parser — outputs structured transcript to stdout"
    )
    parser.add_argument("--days", type=int, default=14,
                        help="Look back N days (default: 14)")
    parser.add_argument("--sessions", type=int, default=None,
                        help="Limit to the N most recent real sessions")
    parser.add_argument("--project-hash", type=str, default=None,
                        help="Restrict to a single project directory (e.g. -Users-you-repos-myapp)")
    args = parser.parse_args()

    sessions = discover_sessions(
        days=args.days,
        max_sessions=args.sessions,
        project_hash=args.project_hash,
    )

    if not sessions:
        scope = f"project '{args.project_hash}'" if args.project_hash else "any project"
        print(
            f"NO_SESSIONS_FOUND: No real sessions found in the last {args.days} days for {scope}.\n"
            f"Try --days 30 or omit --project-hash to search all projects.",
            file=sys.stderr,
        )
        sys.exit(2)

    role_hint = detect_role_hint(sessions)

    # Print session summary to stderr so it doesn't contaminate the transcript
    print(f"[reflect] Found {len(sessions)} session(s) across "
          f"{len(set(s['project'] for s in sessions))} project(s)", file=sys.stderr)
    print(f"[reflect] Role hint: {role_hint}", file=sys.stderr)
    for s in sessions:
        print(f"  - {s['project']}  ({s['modified'].strftime('%Y-%m-%d %H:%M')})", file=sys.stderr)

    transcript = build_context(sessions, role_hint=role_hint)
    print(transcript)


if __name__ == "__main__":
    main()