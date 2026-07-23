"""
Tests for install_sync.py — scheduled git sync (obsidian-git settings +
launchd agent / cron suggestion).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .conftest import load_script_module

install_sync = load_script_module("install_sync")


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "test-vault"
    vault.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(vault), check=True, capture_output=True)
    return vault


def test_merge_obsidian_git_settings_preserves_existing_keys() -> None:
    existing = {"theme": "custom", "autoSaveInterval": 99}
    merged = install_sync.merge_obsidian_git_settings(
        existing, install_sync.OBSIDIAN_GIT_SYNC_SETTINGS
    )
    assert merged["theme"] == "custom"                # preserved
    assert merged["autoSaveInterval"] == 10           # enforced
    assert merged["pullBeforePush"] is True
    assert existing["autoSaveInterval"] == 99         # input not mutated


def test_render_launchd_plist() -> None:
    xml = install_sync.render_launchd_plist(
        "com.test.vault-sync", "/home/t/.claude/hooks/vault-sync.sh", 900,
        "/home/t/.claude/logs/vault-sync.log",
    )
    assert "<string>com.test.vault-sync</string>" in xml
    assert "<integer>900</integer>" in xml
    assert "<string>/home/t/.claude/hooks/vault-sync.sh</string>" in xml


def test_install_darwin_writes_script_plist_and_data_json(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    home = tmp_path / "home"
    data_json = vault / ".obsidian" / "plugins" / "obsidian-git" / "data.json"
    data_json.parent.mkdir(parents=True)
    data_json.write_text(json.dumps({"theme": "keep-me"}))

    result = install_sync.run(
        vault=vault, home=home, interval=600, uninstall=False,
        load=False, now=1234, platform_name="Darwin",
    )

    assert result["ok"] is True
    script = home / ".claude" / "hooks" / "vault-sync.sh"
    assert script.exists()
    assert script.stat().st_mode & 0o111  # executable
    rendered = script.read_text()
    assert str(vault) in rendered
    assert "{{" not in rendered  # no unfilled template tokens

    plist = Path(result["launchd_plist"])
    assert plist.exists()
    assert "<integer>600</integer>" in plist.read_text()

    # data.json merged with backup
    merged = json.loads(data_json.read_text())
    assert merged["theme"] == "keep-me"
    assert merged["autoSaveInterval"] == 10
    assert (data_json.parent / "data.json.bak-1234").exists()

    # The overwritten keys are declared in the output
    assert result["enforced_settings"] == sorted(install_sync.OBSIDIAN_GIT_SYNC_SETTINGS)


def test_install_non_darwin_suggests_cron(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    home = tmp_path / "home"
    result = install_sync.run(
        vault=vault, home=home, interval=900, uninstall=False,
        load=False, now=1, platform_name="Linux",
    )
    assert result["ok"] is True
    assert "launchd_plist" not in result
    assert result["cron_line"].startswith("*/15 * * * *")
    assert (home / ".claude" / "hooks" / "vault-sync.sh").exists()


def test_install_errors_on_non_git_vault(tmp_path: Path) -> None:
    vault = tmp_path / "plain"
    vault.mkdir()
    result = install_sync.run(
        vault=vault, home=tmp_path / "home", interval=900,
        uninstall=False, load=False, now=1, platform_name="Darwin",
    )
    assert result["ok"] is False
    assert "Not a git repository" in result["error"]


def test_uninstall_removes_agent_and_script(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    home = tmp_path / "home"
    installed = install_sync.run(
        vault=vault, home=home, interval=900, uninstall=False,
        load=False, now=1, platform_name="Darwin",
    )
    assert Path(installed["sync_script"]).exists()

    result = install_sync.run(
        vault=vault, home=home, interval=900, uninstall=True,
        load=False, now=2, platform_name="Darwin",
    )
    assert result["ok"] is True
    assert not Path(installed["sync_script"]).exists()
    assert not Path(installed["launchd_plist"]).exists()
    assert len(result["removed"]) == 2
