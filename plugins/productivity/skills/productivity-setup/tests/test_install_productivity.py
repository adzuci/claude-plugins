from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "install_productivity.py"
SPEC = importlib.util.spec_from_file_location("install_productivity", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_sources(root: Path) -> None:
    for name in MODULE.CORE_SKILLS:
        skill = root / name
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\ndisable-model-invocation: true\n---\n",
            encoding="utf-8",
        )


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    source = tmp_path / "source"
    make_sources(source)
    result = MODULE.install(source, tmp_path / "home", ["claude", "codex"], tmp_path / "vault", False)
    assert result["dry_run"] is True
    assert not (tmp_path / "home").exists()
    assert len(result["actions"]) == len(MODULE.CORE_SKILLS) * 2


def test_apply_installs_both_clients_and_sanitizes_codex(tmp_path: Path) -> None:
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_sources(source)
    vault = tmp_path / "vault"
    vault.mkdir()
    MODULE.install(source, home, ["claude", "codex"], vault, True)
    claude = (home / ".claude/skills/todo/SKILL.md").read_text(encoding="utf-8")
    codex = (home / ".codex/skills/todo/SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation" in claude
    assert "disable-model-invocation" not in codex
    marker = json.loads((home / ".codex/skills/todo" / MODULE.MARKER).read_text(encoding="utf-8"))
    assert marker["skill"] == "todo"
    config = json.loads((home / ".config/adzuci-productivity/config.json").read_text(encoding="utf-8"))
    assert config["vault"] == str(vault)


def test_unmanaged_conflict_is_preserved(tmp_path: Path) -> None:
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_sources(source)
    target = home / ".claude/skills/todo"
    target.mkdir(parents=True)
    target.joinpath("SKILL.md").write_text("personal copy\n", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()
    result = MODULE.install(source, home, ["claude"], vault, True)
    todo = next(action for action in result["actions"] if action["skill"] == "todo")
    assert todo["status"] == "conflict-preserved"
    assert target.joinpath("SKILL.md").read_text(encoding="utf-8") == "personal copy\n"
