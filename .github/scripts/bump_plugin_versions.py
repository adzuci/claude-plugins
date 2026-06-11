#!/usr/bin/env python3
"""Bump per-plugin manifest versions from Conventional Commits.

Invoked by the release workflow on push to ``main``. For each plugin directory
changed within a git revision range, it inspects the commits that touched that
plugin and bumps the ``version`` field in both Claude and Codex manifests using the same
Conventional Commits → semver rules as the repo-wide ``bump-version.yml``:

    MAJOR  feat!: / BREAKING CHANGE
    MINOR  feat:
    PATCH  fix: / refactor: / perf: / build: / revert:

Non-releasing types (chore, docs, ci, style, test) produce no bump.

Usage:
    python3 .github/scripts/bump_plugin_versions.py <rev-range>

Prints one ``<plugin>: <old> -> <new> (<level>)`` line per bumped plugin so the
workflow can detect changes and build a commit message. Writes nothing when no
plugin needs a bump.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PLUGINS_DIR = REPO / "plugins"

# Mirror the mapping in .github/workflows/bump-version.yml.
_BREAKING = re.compile(r"^[a-z]+(\([^)]+\))?!:|^BREAKING CHANGE", re.MULTILINE)
_MINOR = re.compile(r"^feat(\([^)]+\))?:", re.MULTILINE)
_PATCH = re.compile(r"^(fix|refactor|perf|build|revert)(\([^)]+\))?:", re.MULTILINE)


def classify_bump(commit_text: str) -> str:
    """Return the highest semver bump level implied by commit message text."""
    if _BREAKING.search(commit_text):
        return "major"
    if _MINOR.search(commit_text):
        return "minor"
    if _PATCH.search(commit_text):
        return "patch"
    return "none"


def bump_version(version: str, level: str) -> str:
    """Apply a semver bump level to a ``major.minor.patch`` string."""
    major, minor, patch = (int(part) for part in version.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return version


def _run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True)


def _changed_plugins(rev_range: str) -> set[str]:
    files = _run("git", "diff", "--name-only", rev_range).splitlines()
    plugins = set()
    for path in files:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "plugins":
            plugins.add(parts[1])
    return plugins


def _commits_for_plugin(rev_range: str, plugin: str) -> str:
    return _run(
        "git", "log", "--format=%s%n%b", rev_range, "--", f"plugins/{plugin}/"
    )


def bump_changed_plugins(rev_range: str) -> list[str]:
    """Bump every plugin changed in ``rev_range``; return summary lines."""
    summary = []
    for plugin in sorted(_changed_plugins(rev_range)):
        claude_manifest = PLUGINS_DIR / plugin / ".claude-plugin" / "plugin.json"
        codex_manifest = PLUGINS_DIR / plugin / ".codex-plugin" / "plugin.json"
        if not claude_manifest.exists():
            continue
        level = classify_bump(_commits_for_plugin(rev_range, plugin))
        if level == "none":
            continue
        data = json.loads(claude_manifest.read_text())
        old = data.get("version", "0.0.0")
        new = bump_version(old, level)
        if new == old:
            continue
        data["version"] = new
        # ensure_ascii=False keeps em-dashes etc. intact; trailing newline matches repo style.
        claude_manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        if codex_manifest.exists():
            codex_data = json.loads(codex_manifest.read_text())
            codex_data["version"] = new
            codex_manifest.write_text(json.dumps(codex_data, indent=2, ensure_ascii=False) + "\n")
        summary.append(f"{plugin}: {old} -> {new} ({level})")
    return summary


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    for line in bump_changed_plugins(argv[1]):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
