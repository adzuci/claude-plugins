"""
Import Antigravity brain artifacts into the memory vault.

Reads ~/.gemini/antigravity/brain/<conversation-id>/ markdown and metadata.
Conversation files remain read-only; imported ids are tracked in
~/.gemini/antigravity/.vault-ingested unless --dry-run is set.
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
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def markdown_lines(path: Path) -> list[str]:
    try:
        return path.read_text(errors="replace").splitlines()
    except FileNotFoundError:
        return []


def artifact_summary(task_lines: list[str], metadata_summaries: list[str]) -> str:
    bullets: list[str] = []
    for summary in metadata_summaries:
        if isinstance(summary, str) and summary:
            bullets.append(redact(summary.strip()))
    for line in task_lines:
        clean = line.strip()
        if clean.startswith("- [x]") or clean.startswith("- [ ]"):
            bullets.append(redact(clean))
        if len(bullets) >= 5:
            break
    if not bullets:
        return ""
    return "### summary\n\n**Did:**\n" + "\n".join(f"- {b}" for b in bullets[:5]) + "\n\n"


def parse_conversation(path: Path) -> dict[str, Any]:
    metadata = [read_json(p) for p in path.glob("*.metadata.json")]
    updated_values = [m.get("updatedAt") for m in metadata if isinstance(m.get("updatedAt"), str) and m.get("updatedAt")]
    updated_at = sorted(updated_values)[-1] if updated_values else None
    task_lines = markdown_lines(path / "task.md")
    implementation_lines = markdown_lines(path / "implementation_plan.md")
    summaries = [m.get("summary", "") for m in metadata]
    title = "unknown"
    for line in task_lines + implementation_lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    cwd = "unknown"
    for m in metadata:
        value = m.get("cwd") or m.get("workspacePath")
        if value:
            cwd = str(value)
            break
    return {
        "id": path.name,
        "timestamp": parse_time(updated_at),
        "title": title,
        "cwd": cwd,
        "artifact_count": len(list(path.iterdir())),
        "summary": artifact_summary(task_lines, summaries),
    }


def conversation_entry(session: dict[str, Any]) -> tuple[str, str]:
    dt = session["timestamp"]
    date = dt.strftime("%Y-%m-%d")
    now = dt.strftime("%H:%M")
    project = Path(session["cwd"]).name if session["cwd"] != "unknown" else session["title"]
    project = re.sub(r"\s+", " ", project)[:80] or "unknown"
    entry = (
        f"## {now} — {redact(project)} (antigravity)\n"
        "- **source:** antigravity\n"
        f"- **cwd:** `{redact(session['cwd'])}`\n"
        f"- **session:** `{session['id']}`\n"
        f"- **tokens:** antigravity: unavailable locally ({session['artifact_count']} artifacts)\n\n"
    )
    if session["summary"]:
        entry += session["summary"]
    return date, entry + "\n"


def recent_conversations(brain_root: Path) -> list[Path]:
    if not brain_root.is_dir():
        return []
    paths = [p for p in brain_root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)


def run(vault: Path, brain_root: Path, state_file: Path, limit: int, dry_run: bool) -> dict[str, Any]:
    ingested = read_state(state_file)
    new_ids = set(ingested)
    appended: list[dict[str, str]] = []
    for path in recent_conversations(brain_root):
        session = parse_conversation(path)
        if session["id"] in ingested:
            continue
        date, entry = conversation_entry(session)
        appended.append({"id": session["id"], "date": date, "entry": entry})
        if not dry_run:
            daily = ensure_daily_file(vault, date)
            daily.write_text(daily.read_text() + entry)
            new_ids.add(session["id"])
        if limit and len(appended) >= limit:
            break
    if not dry_run:
        write_state(state_file, new_ids)
    return {"dry_run": dry_run, "count": len(appended), "sessions": appended}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Antigravity sessions into an Obsidian vault.")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault.")
    parser.add_argument("--brain-root", default="~/.gemini/antigravity/brain")
    parser.add_argument("--state-file", default="~/.gemini/antigravity/.vault-ingested")
    parser.add_argument("--limit", type=int, default=0, help="Maximum new conversations to import.")
    parser.add_argument("--dry-run", action="store_true", help="Print entries without writing.")
    args = parser.parse_args()
    result = run(
        vault=Path(args.vault).expanduser(),
        brain_root=Path(args.brain_root).expanduser(),
        state_file=Path(args.state_file).expanduser(),
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
