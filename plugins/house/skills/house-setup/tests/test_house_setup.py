"""Tests for the house-manager installer (HOME is redirected to a temp dir)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "house_setup.py"
spec = importlib.util.spec_from_file_location("house_setup", SCRIPT)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    vault = tmp_path / "vault"
    (vault / "agents").mkdir(parents=True)
    return tmp_path, vault


def test_check_is_read_only(env):
    tmp, vault = env
    report = setup.check(str(vault), which=lambda name: None)
    assert report["vault_exists"] and report["vault_has_agents_dir"]
    assert not report["config_exists"]
    assert not (tmp / "home" / ".config").exists()


def test_install_dry_run_writes_nothing(env):
    tmp, vault = env
    result = setup.install(str(vault), ["claude"], apply=False)
    assert result["dry_run"] is True and result["actions"]
    assert not (tmp / "home" / ".claude").exists()
    assert not (vault / "house").exists()


def test_install_apply_creates_everything(env):
    tmp, vault = env
    result = setup.install(str(vault), ["claude", "codex"], apply=True)
    home = tmp / "home"
    assert (home / ".claude/skills/hm/SKILL.md").is_file()
    assert (home / ".claude/skills/hm" / setup.MARKER).is_file()
    assert "disable-model-invocation" in (home / ".claude/skills/hm/SKILL.md").read_text()
    assert "disable-model-invocation" not in (home / ".codex/skills/hm/SKILL.md").read_text()
    for helper in setup.HELPERS:
        assert (home / ".config/adzuci-house/bin" / helper).is_file()
    config = json.loads((home / ".config/adzuci-house/config.json").read_text())
    assert config["vault"] == str(vault) and config["schedule"] == "0 18 * * 0"
    assert oct((home / ".config/adzuci-house/config.json").stat().st_mode & 0o777) == "0o600"
    assert (vault / "agents/house-manager.md").is_file()
    assert (vault / "house/README.md").is_file()
    assert (vault / "house/digests/.gitkeep").read_text().strip() == "keep"
    assert result["vault_files_created"]


def test_install_is_idempotent_and_keeps_existing_files(env):
    tmp, vault = env
    setup.install(str(vault), ["claude"], apply=True)
    note = vault / "agents/house-manager.md"
    note.write_text("my edits")
    again = setup.install(str(vault), ["claude"], apply=True)
    assert note.read_text() == "my edits"
    assert again["vault_files_created"] == []


def test_install_preserves_nest_config(env):
    tmp, vault = env
    cfg = tmp / "home/.config/adzuci-house/config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"nest": {"project_id": "p", "client_id": "c"}}))
    setup.install(str(vault), ["claude"], apply=True)
    assert json.loads(cfg.read_text())["nest"]["project_id"] == "p"


def test_refuses_to_overwrite_unmanaged_skill(env):
    tmp, vault = env
    target = tmp / "home/.claude/skills/hm"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("mine")
    with pytest.raises(SystemExit):
        setup.install(str(vault), ["claude"], apply=True)
    assert (target / "SKILL.md").read_text() == "mine"


def test_notify_numbers_validated_and_recorded(env):
    tmp, vault = env
    with pytest.raises(SystemExit):
        setup.install(str(vault), ["claude"], apply=True, notify_to="9785551234")
    setup.install(str(vault), ["claude"], apply=True, notify_to="+19785551234",
                  twilio_from="+15555550100", twilio_profile="house")
    notify = json.loads((tmp / "home/.config/adzuci-house/config.json").read_text())["notify"]
    assert notify["to"] == "+19785551234" and notify["quiet_hours"] == "22-7"


def test_uninstall_removes_only_managed(env):
    tmp, vault = env
    setup.install(str(vault), ["claude"], apply=True)
    dry = setup.uninstall(["claude"], apply=False)
    assert dry["would_remove"] and (tmp / "home/.claude/skills/hm").exists()
    setup.uninstall(["claude"], apply=True)
    assert not (tmp / "home/.claude/skills/hm").exists()
    assert (vault / "house/README.md").exists()  # vault content is never removed


def test_missing_vault_is_an_error(env):
    tmp, _ = env
    with pytest.raises(SystemExit):
        setup.install(str(tmp / "nope"), ["claude"], apply=False)


def test_bundled_hm_skill_forbids_email_mutation():
    text = (setup.SKILLS_ROOT / "hm" / "SKILL.md").read_text()
    assert "Never send, reply, forward, label, trash, or delete" in text
