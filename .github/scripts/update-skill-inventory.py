#!/usr/bin/env python3
"""Regenerates the skill inventory table in README.md."""

import os
import re
import sys

START_MARKER = "<!-- SKILL-INVENTORY-START -->"
END_MARKER = "<!-- SKILL-INVENTORY-END -->"


def parse_frontmatter(filepath):
    with open(filepath) as f:
        content = f.read()
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None, None
    fm = match.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    desc = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    return (
        name.group(1).strip() if name else None,
        desc.group(1).strip() if desc else None,
    )


def build_table():
    rows = []
    plugins_dir = "plugins"
    for plugin_name in sorted(os.listdir(plugins_dir)):
        skills_dir = os.path.join(plugins_dir, plugin_name, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for skill_dir in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, skill_dir, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            name, description = parse_frontmatter(skill_md)
            if not name or not description:
                print(f"WARNING: missing name or description in {skill_md}", file=sys.stderr)
                continue
            command = f"`/{plugin_name}:{name}`"
            rows.append(f"| {plugin_name} | {command} | {description} |")

    if not rows:
        return "_No skills found._"
    header = "| Plugin | Command | Description |\n| --- | --- | --- |"
    return header + "\n" + "\n".join(rows)


def update_readme(table):
    readme_path = "README.md"
    with open(readme_path) as f:
        content = f.read()

    if START_MARKER not in content:
        print(f"ERROR: '{START_MARKER}' not found in {readme_path}", file=sys.stderr)
        sys.exit(1)

    new_block = f"{START_MARKER}\n{table}\n{END_MARKER}"
    new_content = re.sub(
        f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        new_block,
        content,
        flags=re.DOTALL,
    )

    with open(readme_path, "w") as f:
        f.write(new_content)
    print("README.md updated.")


if __name__ == "__main__":
    update_readme(build_table())
