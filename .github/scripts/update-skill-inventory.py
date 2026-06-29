#!/usr/bin/env python3
"""Regenerate README plugin inventory and the full skill inventory."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

README_PLUGIN_START = "<!-- PLUGIN-INVENTORY-START -->"
README_PLUGIN_END = "<!-- PLUGIN-INVENTORY-END -->"
SKILL_START = "<!-- SKILL-INVENTORY-START -->"
SKILL_END = "<!-- SKILL-INVENTORY-END -->"

README_PATH = Path("README.md")
SKILL_INVENTORY_PATH = Path("SKILL_INVENTORY.md")
MARKETPLACE_PATH = Path(".claude-plugin/marketplace.json")


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("__", "\\_\\_").replace("\n", " ").strip()


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def first_sentence(value: str) -> str:
    if ". " not in value:
        return value
    return value.split(". ", 1)[0].rstrip(".") + "."


def parse_frontmatter(filepath: Path) -> dict[str, str]:
    content = filepath.read_text()
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    values: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line or line.startswith((" ", "\t")) or ":" not in line:
            index += 1
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value in {">", ">-", "|", "|-"}:
            block: list[str] = []
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line and not next_line.startswith((" ", "\t")) and ":" in next_line:
                    break
                block.append(next_line.strip())
                index += 1
            values[key] = " ".join(part for part in block if part).strip()
            continue

        values[key] = strip_quotes(raw_value)
        index += 1

    return values


def marketplace_entries() -> list[dict]:
    return json.loads(MARKETPLACE_PATH.read_text())["plugins"]


def plugin_manifest(entry: dict) -> dict:
    return json.loads((Path(entry["source"]) / ".claude-plugin" / "plugin.json").read_text())


def _tracked_skill_mds(plugin_source: str) -> list[str]:
    """Return git-tracked SKILL.md paths under plugin_source/skills/."""
    prefix = str(Path(plugin_source) / "skills") + "/"
    try:
        out = subprocess.check_output(
            ["git", "ls-files", prefix],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to filesystem glob when git is unavailable.
        return [str(p) for p in (Path(plugin_source) / "skills").glob("*/SKILL.md") if p.is_file()]
    return [line for line in out.splitlines() if line.endswith("/SKILL.md")]


def skill_count(plugin_source: str) -> int:
    skills_dir = Path(plugin_source) / "skills"
    if not skills_dir.is_dir():
        return 0
    return len(_tracked_skill_mds(plugin_source))


def build_plugin_table() -> str:
    rows = []
    for entry in marketplace_entries():
        manifest = plugin_manifest(entry)
        rows.append(
            "| {plugin} | {description} | {count} |".format(
                plugin=f"`{manifest['name']}`",
                description=markdown_escape(first_sentence(manifest["description"])),
                count=skill_count(entry["source"]),
            )
        )

    header = "| Plugin | Description | Skills |\n| --- | --- | ---: |"
    return header + "\n" + "\n".join(rows)


def build_skill_table() -> str:
    rows = []
    plugins_dir = Path("plugins")
    for plugin_name in sorted(os.listdir(plugins_dir)):
        plugin_source = str(plugins_dir / plugin_name)
        for skill_md_path in sorted(_tracked_skill_mds(plugin_source)):
            skill_md = Path(skill_md_path)
            if not skill_md.is_file():
                continue
            frontmatter = parse_frontmatter(skill_md)
            name = frontmatter.get("name")
            description = frontmatter.get("description")
            if not name or not description:
                print(f"WARNING: missing name or description in {skill_md}", file=sys.stderr)
                continue
            command = f"`/{plugin_name}:{name}`"
            rows.append(
                "| {plugin} | {command} | {description} |".format(
                    plugin=plugin_name,
                    command=command,
                    description=markdown_escape(description),
                )
            )

    if not rows:
        return "_No skills found._"
    header = "| Plugin | Command | Description |\n| --- | --- | --- |"
    return header + "\n" + "\n".join(rows)


def replace_block(content: str, start: str, end: str, replacement: str, path: Path) -> str:
    if start not in content:
        print(f"ERROR: '{start}' not found in {path}", file=sys.stderr)
        sys.exit(1)

    new_block = f"{start}\n\n{replacement}\n\n{end}"
    return re.sub(
        f"{re.escape(start)}.*?{re.escape(end)}",
        new_block,
        content,
        flags=re.DOTALL,
    )


def update_readme(plugin_table: str) -> None:
    content = README_PATH.read_text()
    plugin_section = "\n".join(
        [
            "## Plugin Inventory",
            "",
            "See [SKILL_INVENTORY.md](SKILL_INVENTORY.md) for the full generated skill command inventory.",
            "",
            README_PLUGIN_START,
            "",
            plugin_table,
            "",
            README_PLUGIN_END,
        ]
    )
    if README_PLUGIN_START in content:
        new_content = replace_block(content, README_PLUGIN_START, README_PLUGIN_END, plugin_table, README_PATH)
    elif SKILL_START in content and SKILL_END in content:
        new_content = re.sub(
            rf"## Skill Inventory\n\n{re.escape(SKILL_START)}.*?{re.escape(SKILL_END)}",
            plugin_section,
            content,
            flags=re.DOTALL,
        )
    else:
        print(
            f"ERROR: '{README_PLUGIN_START}' or '{SKILL_START}' not found in {README_PATH}",
            file=sys.stderr,
        )
        sys.exit(1)
    README_PATH.write_text(new_content)
    print("README.md plugin inventory updated.")


def update_skill_inventory(skill_table: str) -> None:
    content = "\n".join(
        [
            "# Apollo Skill Inventory",
            "",
            "Generated from `plugins/*/skills/*/SKILL.md`. Do not edit this table manually.",
            "",
            SKILL_START,
            "",
            skill_table,
            "",
            SKILL_END,
            "",
        ]
    )
    SKILL_INVENTORY_PATH.write_text(content)
    print("SKILL_INVENTORY.md updated.")


def main() -> None:
    update_readme(build_plugin_table())
    update_skill_inventory(build_skill_table())


if __name__ == "__main__":
    main()
