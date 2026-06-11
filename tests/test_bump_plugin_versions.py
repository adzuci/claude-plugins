"""Unit tests for the per-plugin version-bump logic."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "bump_plugin_versions.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("bump_plugin_versions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bpv = pytest.importorskip("importlib") and _load_module()


@pytest.mark.parametrize(
    "text,expected",
    [
        ("feat: add a thing", "minor"),
        ("feat(apollo-people): add 1:1-prep skill", "minor"),
        ("fix: correct a bug", "patch"),
        ("fix(apollo-people): link recognition", "patch"),
        ("refactor(scope): tidy", "patch"),
        ("perf: speed up", "patch"),
        ("feat!: breaking change", "major"),
        ("feat(scope)!: breaking change", "major"),
        ("chore: housekeeping\n\nBREAKING CHANGE: drops X", "major"),
        ("chore: bump deps", "none"),
        ("docs: update readme", "none"),
        ("ci: tweak workflow", "none"),
        ("style: format", "none"),
        ("test: add coverage", "none"),
    ],
)
def test_classify_bump(text, expected):
    assert bpv.classify_bump(text) == expected


def test_classify_bump_picks_highest_across_commits():
    text = "fix: small fix\nfeat: new feature\nchore: noise"
    assert bpv.classify_bump(text) == "minor"


@pytest.mark.parametrize(
    "version,level,expected",
    [
        ("0.1.0", "minor", "0.2.0"),
        ("0.1.0", "patch", "0.1.1"),
        ("0.1.5", "major", "1.0.0"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "none", "1.2.3"),
    ],
)
def test_bump_version(version, level, expected):
    assert bpv.bump_version(version, level) == expected


def test_bump_changed_plugins_updates_claude_and_codex_manifests(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "apollo-test"
    claude_dir = plugin_dir / ".claude-plugin"
    codex_dir = plugin_dir / ".codex-plugin"
    claude_dir.mkdir(parents=True)
    codex_dir.mkdir(parents=True)
    (claude_dir / "plugin.json").write_text('{"name": "apollo-test", "version": "1.2.3"}\n')
    (codex_dir / "plugin.json").write_text('{"name": "apollo-test", "version": "1.2.3"}\n')

    monkeypatch.setattr(bpv, "PLUGINS_DIR", tmp_path)
    monkeypatch.setattr(bpv, "_changed_plugins", lambda rev_range: {"apollo-test"})
    monkeypatch.setattr(bpv, "_commits_for_plugin", lambda rev_range, plugin: "feat: add test skill")

    assert bpv.bump_changed_plugins("v1.0.0..HEAD") == ["apollo-test: 1.2.3 -> 1.3.0 (minor)"]

    assert '"version": "1.3.0"' in (claude_dir / "plugin.json").read_text()
    assert '"version": "1.3.0"' in (codex_dir / "plugin.json").read_text()
