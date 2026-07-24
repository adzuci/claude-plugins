"""Tests for the generated memory-vault scaffold."""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import load_script_module

scaffold_vault = load_script_module("scaffold_vault")


def test_scaffold_includes_root_readme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        scaffold_vault,
        "_run",
        lambda command, cwd=None: (True, "", ""),
    )

    result = scaffold_vault.scaffold(
        name="platform",
        parent=str(tmp_path),
        remote="https://github.com/apolloio/platform-vault.git",
    )

    vault = tmp_path / "platform-vault"
    readme = (vault / "README.md").read_text()
    assert result["ok"] is True
    assert result["remote"] == "https://github.com/apolloio/platform-vault.git"
    assert "Open folder as vault" in readme
    assert "15 minutes" in readme
    assert "apolloio" in readme
    assert (vault / "index.md").exists()


def test_scaffold_refuses_nonempty_existing_directory(tmp_path: Path) -> None:
    vault = tmp_path / "existing-vault"
    vault.mkdir()
    (vault / "keep.md").write_text("preserve me")

    result = scaffold_vault.scaffold(name="existing", parent=str(tmp_path))

    assert result["ok"] is False
    assert (vault / "keep.md").read_text() == "preserve me"
