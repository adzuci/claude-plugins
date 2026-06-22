"""
test_install_hook.py — Test merge_session_end_hook with realistic two-entry
SessionEnd fixtures (a session-end.sh entry + a claudebar matcher entry).

Pure helper tests — no main(), no network, no filesystem.
"""
from __future__ import annotations

import copy

from .conftest import load_script_module

lib = load_script_module("lib")
install_hook = load_script_module("install_hook")

HOOK_CMD = "~/.claude/hooks/session-end.sh"

# A realistic two-entry SessionEnd: our hook + a claudebar matcher entry.
CLAUDEBAR_ENTRY = {
    "matcher": "claudebar",
    "hooks": [{"type": "command", "command": "/usr/local/bin/claudebar"}],
}

SESSION_END_HOOK_ENTRY = {
    "hooks": [{"type": "command", "command": HOOK_CMD}]
}

TWO_ENTRY_SETTINGS = {
    "hooks": {
        "SessionEnd": [SESSION_END_HOOK_ENTRY, CLAUDEBAR_ENTRY],
        "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}],
    },
    "theme": "dark",
}


class TestMergeSessionEndHookWithTwoEntries:
    def test_idempotent_with_two_entries(self) -> None:
        """Merging an already-present hook into a two-entry SessionEnd is a no-op."""
        result = lib.merge_session_end_hook(TWO_ENTRY_SETTINGS, HOOK_CMD)
        assert result["hooks"]["SessionEnd"] == TWO_ENTRY_SETTINGS["hooks"]["SessionEnd"]

    def test_claudebar_entry_preserved(self) -> None:
        """Claudebar matcher entry is never disturbed."""
        result = lib.merge_session_end_hook(TWO_ENTRY_SETTINGS, HOOK_CMD)
        assert CLAUDEBAR_ENTRY in result["hooks"]["SessionEnd"]

    def test_session_end_hook_entry_preserved(self) -> None:
        """The session-end.sh hook entry itself is preserved."""
        result = lib.merge_session_end_hook(TWO_ENTRY_SETTINGS, HOOK_CMD)
        assert SESSION_END_HOOK_ENTRY in result["hooks"]["SessionEnd"]

    def test_stop_hook_untouched(self) -> None:
        """Unrelated Stop hook is never touched."""
        result = lib.merge_session_end_hook(TWO_ENTRY_SETTINGS, HOOK_CMD)
        assert result["hooks"]["Stop"] == TWO_ENTRY_SETTINGS["hooks"]["Stop"]

    def test_other_settings_preserved(self) -> None:
        """Other top-level settings (e.g. 'theme') are carried through."""
        result = lib.merge_session_end_hook(TWO_ENTRY_SETTINGS, HOOK_CMD)
        assert result.get("theme") == "dark"

    def test_does_not_mutate_input(self) -> None:
        """Input dict is not mutated (deep copy semantics)."""
        original = copy.deepcopy(TWO_ENTRY_SETTINGS)
        lib.merge_session_end_hook(TWO_ENTRY_SETTINGS, HOOK_CMD)
        assert TWO_ENTRY_SETTINGS == original

    def test_new_hook_appended_when_absent(self) -> None:
        """When starting from only a claudebar entry, our hook is appended."""
        settings = {
            "hooks": {
                "SessionEnd": [CLAUDEBAR_ENTRY],
            }
        }
        result = lib.merge_session_end_hook(settings, HOOK_CMD)
        se = result["hooks"]["SessionEnd"]
        assert len(se) == 2
        assert CLAUDEBAR_ENTRY in se
        cmds = [h["command"] for e in se for h in e.get("hooks", [])]
        assert HOOK_CMD in cmds

    def test_is_hook_present_true_for_two_entry(self) -> None:
        assert lib.is_hook_present(TWO_ENTRY_SETTINGS, HOOK_CMD) is True

    def test_is_hook_present_false_for_different_cmd(self) -> None:
        assert lib.is_hook_present(TWO_ENTRY_SETTINGS, "/other/hook.sh") is False


def test_install_does_not_write_hook_when_settings_malformed(tmp_path) -> None:
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings = claude_dir / "settings.json"
    settings.write_text("{malformed")

    result = install_hook.install(vault="/tmp/vault", home=tmp_path, now=123)

    assert result["ok"] is False
    assert not (claude_dir / "hooks" / "session-end.sh").exists()
    assert (claude_dir / "settings.json.bak-123").exists()


def test_install_reports_unreadable_settings_without_hook_write(tmp_path) -> None:
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings = claude_dir / "settings.json"
    settings.mkdir()

    result = install_hook.install(vault="/tmp/vault", home=tmp_path, now=123)

    assert result["ok"] is False
    assert "could not be read" in result["error"]
    assert not (claude_dir / "hooks" / "session-end.sh").exists()


def test_installed_hook_exits_gracefully_without_jq(tmp_path) -> None:
    result = install_hook.install(vault="/tmp/vault", home=tmp_path, now=123)

    assert result["ok"] is True
    hook = (tmp_path / ".claude" / "hooks" / "session-end.sh").read_text()
    assert "command -v jq" in hook
    assert "jq missing; session summary hook skipped" in hook
