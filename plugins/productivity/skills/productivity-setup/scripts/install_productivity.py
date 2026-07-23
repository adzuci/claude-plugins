#!/usr/bin/env python3
"""Install managed productivity skills for detected Claude Code and Codex clients."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from typing import Callable


CORE_SKILLS = ("productivity-setup", "todo", "wrapup", "daily-wrapup", "ai-coach", "standup")
CLIENT_DIRS = {"claude": Path(".claude/skills"), "codex": Path(".codex/skills")}
MARKER = ".productivity-managed.json"


def detect_clients(which: Callable[[str], str | None] = shutil.which) -> list[str]:
    return [client for client in CLIENT_DIRS if which(client)]


def codex_skill_text(text: str) -> str:
    """Remove Claude-only direct-invocation metadata from a Codex copy."""
    return re.sub(r"^disable-model-invocation:\s*true\s*\n", "", text, flags=re.MULTILINE)


def managed(target: Path) -> bool:
    return (target / MARKER).is_file()


def copy_skill(source: Path, target: Path, client: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "tests"),
    )
    skill_file = target / "SKILL.md"
    if client == "codex":
        skill_file.write_text(codex_skill_text(skill_file.read_text(encoding="utf-8")), encoding="utf-8")
    (target / MARKER).write_text(
        json.dumps({"schema_version": 1, "source": "adzuci-plugins/productivity", "skill": source.name}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def install(source_root: Path, home: Path, clients: list[str], vault: Path, apply: bool) -> dict[str, object]:
    actions: list[dict[str, str]] = []
    for client in clients:
        if client not in CLIENT_DIRS:
            raise ValueError(f"unsupported client: {client}")
        for name in CORE_SKILLS:
            source = source_root / name
            target = home / CLIENT_DIRS[client] / name
            if not (source / "SKILL.md").is_file():
                actions.append({"client": client, "skill": name, "status": "source-missing", "target": str(target)})
                continue
            if target.resolve() == source.resolve():
                actions.append({"client": client, "skill": name, "status": "already-source", "target": str(target)})
                continue
            if target.exists() and not managed(target):
                actions.append({"client": client, "skill": name, "status": "conflict-preserved", "target": str(target)})
                continue
            status = "update" if target.exists() else "install"
            if apply:
                copy_skill(source, target, client)
            actions.append({"client": client, "skill": name, "status": status, "target": str(target)})
    config_path = home / ".config" / "adzuci-productivity" / "config.json"
    if apply:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps({"schema_version": 1, "vault": str(vault.resolve())}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        config_path.chmod(0o600)
    return {
        "ok": True,
        "dry_run": not apply,
        "clients": clients,
        "skills": list(CORE_SKILLS),
        "config": str(config_path),
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, help="Obsidian vault used by the installed workflows.")
    parser.add_argument("--home", default=str(Path.home()), help="Override the user home directory.")
    parser.add_argument("--source-root", help="Override the plugin skills directory.")
    parser.add_argument("--client", action="append", choices=tuple(CLIENT_DIRS), help="Install only this client; repeatable.")
    parser.add_argument("--apply", action="store_true", help="Apply the planned copies.")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        raise SystemExit(f"vault does not exist: {vault}")
    clients = list(dict.fromkeys(args.client or detect_clients()))
    if not clients:
        print(json.dumps({"ok": False, "error": "no local Claude Code or Codex client detected"}, sort_keys=True))
        return 1
    source_root = Path(args.source_root).expanduser() if args.source_root else Path(__file__).resolve().parents[2]
    result = install(source_root, Path(args.home).expanduser(), clients, vault, args.apply)
    result["vault"] = str(vault.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
