"""
Import Codex rollout sessions into the memory vault.

Reads ~/.codex/sessions/**/*.jsonl and appends new sessions to
<vault>/sessions/YYYY-MM-DD.md. Rollout files are read-only; imported ids are
tracked in ~/.codex/.vault-ingested unless --dry-run is set.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from session_importer_common import ensure_daily_file, read_state, redact, write_state


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def h(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def text_from_payload(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("text", "message", "content"):
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            content = value.get("content")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                parts.extend(item.get("text", "") for item in content if isinstance(item, dict))
        elif isinstance(value, list):
            parts.extend(item.get("text", "") for item in value if isinstance(item, dict))
    return "\n".join(part for part in parts if part)


def terse_summary(agent_texts: list[str]) -> str:
    candidates: list[str] = []
    verbs = re.compile(r"\b(did|fixed|added|updated|created|ran|verified|decided|blocked|next)\b", re.I)
    for text in agent_texts[-8:]:
        for raw_line in text.splitlines():
            line = raw_line.strip(" -\t")
            if 16 <= len(line) <= 220 and verbs.search(line):
                candidates.append(redact(line))
            if len(candidates) >= 4:
                break
        if len(candidates) >= 4:
            break
    if not candidates:
        return ""
    bullets = "\n".join(f"- {line}" for line in candidates[:4])
    return f"### summary\n\n**Did:**\n{bullets}\n\n"


def parse_rollout(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    usage: dict[str, int] = {}
    msg_count = 0
    agent_texts: list[str] = []
    fallback_ts = None

    for line in path.read_text(errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if fallback_ts is None:
            fallback_ts = obj.get("timestamp")
        obj_type = obj.get("type")
        if obj_type == "session_meta":
            meta = obj.get("payload", {})
            fallback_ts = meta.get("timestamp") or obj.get("timestamp") or fallback_ts
            continue
        payload = obj.get("payload", {})
        if obj_type == "event_msg":
            payload_type = payload.get("type")
            if payload_type == "token_count":
                usage = payload.get("info", {}).get("total_token_usage", {}) or {}
            elif payload_type in {"user_message", "agent_message"}:
                msg_count += 1
                if payload_type == "agent_message":
                    text = text_from_payload(payload)
                    if text:
                        agent_texts.append(text)
        elif obj_type == "response_item" and payload.get("type") == "message":
            role = payload.get("role")
            if role in {"user", "assistant"}:
                msg_count += 1
            if role == "assistant":
                text = text_from_payload(payload)
                if text:
                    agent_texts.append(text)

    git = meta.get("git") if isinstance(meta.get("git"), dict) else {}
    dt = parse_time(meta.get("timestamp") or fallback_ts)
    return {
        "id": meta.get("id") or path.stem,
        "timestamp": dt,
        "cwd": meta.get("cwd") or "unknown",
        "branch": git.get("branch") or "unknown",
        "model": meta.get("model") or meta.get("originator") or "codex",
        "usage": usage,
        "msg_count": msg_count,
        "summary": terse_summary(agent_texts),
        "path": str(path),
    }


def session_entry(session: dict[str, Any]) -> tuple[str, str]:
    dt = session["timestamp"]
    date = dt.strftime("%Y-%m-%d")
    now = dt.strftime("%H:%M")
    cwd = session["cwd"]
    project = Path(cwd).name if cwd != "unknown" else "unknown"
    usage = session["usage"]
    input_tokens = int(usage.get("input_tokens", 0)) + int(usage.get("cached_input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    reasoning = int(usage.get("reasoning_output_tokens", 0))
    model = str(session["model"]).replace("\n", " ")

    entry = (
        f"## {now} — {project} (codex)\n"
        "- **source:** codex\n"
        f"- **cwd:** `{redact(cwd)}`\n"
        f"- **branch:** `{redact(session['branch'])}`\n"
        f"- **session:** `{session['id']}`\n"
        f"- **tokens:** {redact(model)}: {h(output_tokens)} out / {h(input_tokens)} in "
        f"({h(reasoning)} reasoning, {session['msg_count']} msgs)\n\n"
    )
    if session["summary"]:
        entry += session["summary"]
    return date, entry + "\n"


def recent_rollouts(sessions_root: Path) -> list[Path]:
    return sorted(
        sessions_root.glob("**/rollout-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def run(vault: Path, sessions_root: Path, state_file: Path, limit: int, dry_run: bool) -> dict[str, Any]:
    ingested = read_state(state_file)
    appended: list[dict[str, str]] = []
    new_ids = set(ingested)

    for path in recent_rollouts(sessions_root):
        session = parse_rollout(path)
        if session["id"] in new_ids:
            continue
        date, entry = session_entry(session)
        appended.append({"id": session["id"], "date": date, "entry": entry})
        new_ids.add(session["id"])
        if not dry_run:
            daily = ensure_daily_file(vault, date)
            daily.write_text(daily.read_text() + entry)
        if limit and len(appended) >= limit:
            break

    if not dry_run:
        write_state(state_file, new_ids)
    return {"dry_run": dry_run, "count": len(appended), "sessions": appended}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Codex sessions into an Obsidian vault.")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault.")
    parser.add_argument("--sessions-root", default="~/.codex/sessions")
    parser.add_argument("--state-file", default="~/.codex/.vault-ingested")
    parser.add_argument("--limit", type=int, default=0, help="Maximum new sessions to import.")
    parser.add_argument("--dry-run", action="store_true", help="Print entries without writing.")
    args = parser.parse_args()

    result = run(
        vault=Path(args.vault).expanduser(),
        sessions_root=Path(args.sessions_root).expanduser(),
        state_file=Path(args.state_file).expanduser(),
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    if result["count"] == 0:
        sys.exit(0)


if __name__ == "__main__":
    main()
