#!/usr/bin/env python3
"""Add persistent tasks to an Obsidian Kanban backlog Inbox."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path


KANBAN_SECTIONS = (
    "Inbox",
    "This Week",
    "In Progress",
    "Waiting",
    "Done This Week",
    "Someday",
)
URGENT_PREFIX = "URGENT — "


def normalize_items(raw: str) -> list[str]:
    items: list[str] = []
    for line in raw.splitlines():
        item = line.strip()
        if not item:
            continue
        item = re.sub(r"^[-*]\s+", "", item)
        item = re.sub(r"^\d+[.)]\s+", "", item)
        item = re.sub(r"^\[[ xX]\]\s+", "", item)
        if item:
            items.append(item)
    if not items:
        raise SystemExit("No todo items provided.")
    return items


def canonical(item: str) -> str:
    value = item.strip()
    if value.casefold().startswith(URGENT_PREFIX.casefold()):
        value = value[len(URGENT_PREFIX) :]
    return re.sub(r"\s+", " ", value).casefold()


def ensure_kanban_sections(existing: str) -> str:
    text = existing.rstrip()
    headings = set(re.findall(r"^## (.+)$", text, re.M))
    for section in KANBAN_SECTIONS:
        if section not in headings:
            text += f"\n\n## {section}\n"
    return text.rstrip() + "\n"


def open_items(text: str) -> dict[str, str]:
    return {
        canonical(match.group(1)): match.group(1).strip()
        for match in re.finditer(r"^- \[ \] (.+)$", text, re.M)
    }


def update_backlog(existing: str, items: list[str], urgent: bool) -> tuple[str, dict[str, int]]:
    text = ensure_kanban_sections(existing)
    known = open_items(text)
    additions: list[str] = []
    promoted = 0
    skipped = 0

    for raw_item in items:
        key = canonical(raw_item)
        desired = raw_item
        if urgent and not raw_item.casefold().startswith(URGENT_PREFIX.casefold()):
            desired = f"{URGENT_PREFIX}{raw_item}"
        current = known.get(key)
        if current is None:
            additions.append(desired)
            known[key] = desired
            continue
        if urgent and not current.casefold().startswith(URGENT_PREFIX.casefold()):
            text = text.replace(f"- [ ] {current}", f"- [ ] {URGENT_PREFIX}{current}", 1)
            promoted += 1
            known[key] = f"{URGENT_PREFIX}{current}"
        else:
            skipped += 1

    if additions:
        body = "\n".join(f"- [ ] {item}" for item in additions)
        pattern = re.compile(r"(^## Inbox\n)(.*?)(?=^## |\Z)", re.M | re.S)
        match = pattern.search(text)
        if not match:
            raise SystemExit("Unable to locate the backlog Inbox section.")
        current = match.group(2).rstrip()
        replacement = f"{match.group(1)}\n{current + chr(10) if current else ''}{body}\n\n"
        text = pattern.sub(replacement, text, count=1)

    return text.rstrip() + "\n", {
        "added": len(additions),
        "promoted": promoted,
        "skipped": skipped,
    }


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def main() -> None:
    default_vault = os.environ.get("VAULT", os.path.expanduser("~/obsidian-vault"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True, help="Todo text, one item per line or as bullets.")
    parser.add_argument("--vault", default=default_vault, help="Obsidian vault root.")
    parser.add_argument("--urgent", action="store_true", help="Mark each task urgent.")
    parser.add_argument("--dry-run", action="store_true", help="Print the updated backlog without writing.")
    args = parser.parse_args()

    backlog = Path(args.vault).expanduser() / "backlog.md"
    existing = backlog.read_text(encoding="utf-8") if backlog.exists() else "---\ntype: backlog\ndescription: Task backlog\n---\n"
    updated, result = update_backlog(existing, normalize_items(args.items), args.urgent)
    if args.dry_run:
        print(updated, end="")
        return
    atomic_write(backlog, updated)
    print(json.dumps({"path": str(backlog), **result}))


if __name__ == "__main__":
    main()
