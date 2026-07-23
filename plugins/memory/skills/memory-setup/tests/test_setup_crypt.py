"""
Tests for setup_crypt.py — git-crypt enablement, migration, and unlock.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from .conftest import load_script_module

setup_crypt = load_script_module("setup_crypt")

HAS_GIT_CRYPT = shutil.which("git-crypt") is not None


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True)


def _make_repo(tmp_path: Path, name: str = "test-vault") -> Path:
    vault = tmp_path / name
    vault.mkdir()
    _git(vault, "init", "-q")
    _git(vault, "config", "user.email", "test@example.com")
    _git(vault, "config", "user.name", "Test")
    return vault


def _commit_file(vault: Path, rel: str, content: str, msg: str = "add file") -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    _git(vault, "add", "-A")
    _git(vault, "commit", "-q", "-m", msg)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def test_build_gitattributes_block() -> None:
    block = setup_crypt.build_gitattributes_block(["memory", "sessions/"])
    assert "memory/** filter=git-crypt diff=git-crypt" in block
    assert "sessions/** filter=git-crypt diff=git-crypt" in block
    assert ".gitattributes !filter !diff" in block
    assert block.startswith("# BEGIN memory-setup git-crypt")


def test_merge_gitattributes_preserves_existing_and_is_idempotent() -> None:
    existing = "*.png binary\n"
    once = setup_crypt.merge_gitattributes(existing, ["memory"])
    assert "*.png binary" in once
    assert "memory/** filter=git-crypt" in once
    twice = setup_crypt.merge_gitattributes(once, ["memory"])
    assert twice == once


def test_merge_gitattributes_replaces_block_on_path_change() -> None:
    once = setup_crypt.merge_gitattributes("", ["memory"])
    updated = setup_crypt.merge_gitattributes(once, ["memory", "coaching"])
    assert "coaching/** filter=git-crypt" in updated
    assert updated.count("# BEGIN memory-setup git-crypt") == 1


def test_is_locked_file() -> None:
    assert setup_crypt.is_locked_file(b"\x00GITCRYPT\x00rest")
    assert not setup_crypt.is_locked_file(b"# plain markdown")


# ---------------------------------------------------------------------------
# Mode detection (no git-crypt binary needed)
# ---------------------------------------------------------------------------

def test_detect_mode_fresh(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    _commit_file(vault, "index.md", "# index", "chore: initial vault scaffold")
    assert setup_crypt.detect_mode(vault, ["memory"]) == "fresh"


def test_detect_mode_migrate_with_tracked_sensitive_files(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    _commit_file(vault, "memory/facts.md", "secret fact")
    assert setup_crypt.detect_mode(vault, ["memory"]) == "migrate"


def test_detect_mode_unlock_when_filter_but_no_local_key(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    _commit_file(vault, ".gitattributes", "memory/** filter=git-crypt diff=git-crypt\n")
    assert setup_crypt.detect_mode(vault, ["memory"]) == "unlock"


# ---------------------------------------------------------------------------
# run() guards
# ---------------------------------------------------------------------------

def test_run_errors_without_git_crypt_binary(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    result = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=tmp_path / "k.key",
        apply=False, which=lambda name: None,
    )
    assert result["ok"] is False
    assert "git-crypt binary not found" in result["error"]


def test_run_refuses_key_inside_vault(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    result = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=vault / "k.key",
        apply=False, which=lambda name: "/usr/bin/git-crypt",
    )
    assert result["ok"] is False
    assert "must not be inside the vault" in result["error"]


def test_run_errors_on_non_git_dir(tmp_path: Path) -> None:
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    result = setup_crypt.run(
        vault=plain, paths=["memory"], key_out=tmp_path / "k.key",
        apply=False, which=lambda name: "/usr/bin/git-crypt",
    )
    assert result["ok"] is False
    assert "Not a git repository" in result["error"]


def test_dry_run_makes_no_changes(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    _commit_file(vault, "memory/facts.md", "secret")
    key = tmp_path / "k.key"
    result = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=key,
        apply=False, which=lambda name: "/usr/bin/git-crypt",
    )
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["mode"] == "migrate"
    assert result["history_warning"] is True
    assert not (vault / ".gitattributes").exists()
    assert not key.exists()


def test_key_location_warning_when_key_dir_is_a_git_repo(tmp_path: Path) -> None:
    outer = tmp_path / "outer-repo"
    outer.mkdir()
    _git(outer, "init", "-q")
    vault = _make_repo(outer, "nested-vault")
    _commit_file(vault, "index.md", "# index")

    result = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=outer / "k.key",
        apply=False, which=lambda name: "/usr/bin/git-crypt",
    )
    assert result["ok"] is True
    assert "inside a git repo" in result["key_location_warning"]

    # No warning when the key dir is not inside any git work tree.
    clean = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=tmp_path / "elsewhere" / "k.key",
        apply=False, which=lambda name: "/usr/bin/git-crypt",
    )
    assert "key_location_warning" not in clean


def test_unlock_mode_requires_keyfile(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    _commit_file(vault, ".gitattributes", "memory/** filter=git-crypt diff=git-crypt\n")
    result = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=tmp_path / "k.key",
        apply=True, which=lambda name: "/usr/bin/git-crypt",
    )
    assert result["ok"] is False
    assert "--unlock" in result["error"]


# ---------------------------------------------------------------------------
# Integration (requires the real git-crypt binary)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_GIT_CRYPT, reason="git-crypt binary not installed")
def test_full_migrate_then_lock_then_unlock_roundtrip(tmp_path: Path) -> None:
    vault = _make_repo(tmp_path)
    _commit_file(vault, "index.md", "# index")
    _commit_file(vault, "memory/facts.md", "very secret fact")
    key = tmp_path / "vault.gitcrypt.key"

    result = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=key, apply=True,
    )
    assert result["ok"] is True
    assert result["mode"] == "migrate"
    assert result["commit"] is True
    assert key.exists()

    # The committed blob must be ciphertext...
    blob = subprocess.run(
        ["git", "show", "HEAD:memory/facts.md"],
        cwd=str(vault), capture_output=True, check=True,
    ).stdout
    assert blob.startswith(b"\x00GITCRYPT")
    # ...while the working tree stays plaintext.
    assert (vault / "memory" / "facts.md").read_text() == "very secret fact"

    # Re-running is a no-op.
    again = setup_crypt.run(vault=vault, paths=["memory"], key_out=key, apply=True)
    assert again["mode"] == "noop"

    # Lock (simulates a fresh clone on another machine), then unlock.
    subprocess.run(["git-crypt", "lock"], cwd=str(vault), check=True, capture_output=True)
    assert setup_crypt.detect_mode(vault, ["memory"]) == "unlock"
    unlocked = setup_crypt.run(
        vault=vault, paths=["memory"], key_out=key, apply=True, unlock_key=key,
    )
    assert unlocked["ok"] is True
    assert (vault / "memory" / "facts.md").read_text() == "very secret fact"
