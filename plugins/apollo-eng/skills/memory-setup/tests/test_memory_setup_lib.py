"""
Thorough unit tests for every helper in lib.py.
All tests are pure — no network, no filesystem.
"""
from __future__ import annotations

import copy

import pytest

from .conftest import load_script_module

lib = load_script_module("lib")

# ---------------------------------------------------------------------------
# merge_session_end_hook / is_hook_present
# ---------------------------------------------------------------------------

HOOK_CMD = "/home/user/.claude/hooks/session-end.sh"

CLAUDEBAR_ENTRY = {
    "matcher": "claudebar",
    "hooks": [{"type": "command", "command": "/usr/local/bin/claudebar"}],
}


def _settings_with_claudebar() -> dict:
    """A realistic settings dict with a claudebar SessionEnd entry."""
    return {
        "hooks": {
            "SessionEnd": [CLAUDEBAR_ENTRY],
            "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}],
        }
    }


class TestIsHookPresent:
    def test_absent(self) -> None:
        assert lib.is_hook_present({}, HOOK_CMD) is False

    def test_present(self) -> None:
        settings = lib.merge_session_end_hook({}, HOOK_CMD)
        assert lib.is_hook_present(settings, HOOK_CMD) is True

    def test_different_command(self) -> None:
        settings = lib.merge_session_end_hook({}, "/other/cmd.sh")
        assert lib.is_hook_present(settings, HOOK_CMD) is False

    def test_empty_hooks(self) -> None:
        assert lib.is_hook_present({"hooks": {}}, HOOK_CMD) is False


class TestMergeSessionEndHook:
    def test_absent_appended(self) -> None:
        result = lib.merge_session_end_hook({}, HOOK_CMD)
        se = result["hooks"]["SessionEnd"]
        assert len(se) == 1
        assert se[0]["hooks"][0]["command"] == HOOK_CMD

    def test_idempotent(self) -> None:
        first = lib.merge_session_end_hook({}, HOOK_CMD)
        second = lib.merge_session_end_hook(first, HOOK_CMD)
        assert first["hooks"]["SessionEnd"] == second["hooks"]["SessionEnd"]
        assert len(second["hooks"]["SessionEnd"]) == 1

    def test_preserves_claudebar_entry(self) -> None:
        settings = _settings_with_claudebar()
        result = lib.merge_session_end_hook(settings, HOOK_CMD)
        se = result["hooks"]["SessionEnd"]
        # Claudebar entry still present
        assert CLAUDEBAR_ENTRY in se
        # Our new entry also present
        cmds = [h["command"] for e in se for h in e.get("hooks", [])]
        assert HOOK_CMD in cmds

    def test_preserves_stop_hook(self) -> None:
        settings = _settings_with_claudebar()
        result = lib.merge_session_end_hook(settings, HOOK_CMD)
        # Unrelated Stop hook untouched
        assert result["hooks"]["Stop"] == settings["hooks"]["Stop"]

    def test_does_not_mutate_input(self) -> None:
        original = _settings_with_claudebar()
        original_copy = copy.deepcopy(original)
        lib.merge_session_end_hook(original, HOOK_CMD)
        assert original == original_copy

    def test_creates_hooks_key(self) -> None:
        result = lib.merge_session_end_hook({}, HOOK_CMD)
        assert "hooks" in result
        assert "SessionEnd" in result["hooks"]

    def test_entry_structure(self) -> None:
        result = lib.merge_session_end_hook({}, HOOK_CMD)
        entry = result["hooks"]["SessionEnd"][0]
        assert "hooks" in entry
        assert entry["hooks"][0]["type"] == "command"
        assert entry["hooks"][0]["command"] == HOOK_CMD


# ---------------------------------------------------------------------------
# merge_community_plugins
# ---------------------------------------------------------------------------

class TestMergeCommunityPlugins:
    def test_union(self) -> None:
        result = lib.merge_community_plugins(["a", "b"], ["c"])
        assert result == ["a", "b", "c"]

    def test_dedup_existing(self) -> None:
        result = lib.merge_community_plugins(["a", "a", "b"], [])
        assert result == ["a", "b"]

    def test_dedup_overlap(self) -> None:
        result = lib.merge_community_plugins(["a", "b"], ["b", "c"])
        assert result == ["a", "b", "c"]

    def test_empty_existing(self) -> None:
        result = lib.merge_community_plugins([], ["x", "y"])
        assert result == ["x", "y"]

    def test_empty_new(self) -> None:
        result = lib.merge_community_plugins(["x", "y"], [])
        assert result == ["x", "y"]

    def test_both_empty(self) -> None:
        assert lib.merge_community_plugins([], []) == []

    def test_order_preserved(self) -> None:
        result = lib.merge_community_plugins(["z", "a"], ["m", "a"])
        assert result == ["z", "a", "m"]


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

class TestRenderTemplate:
    def test_substitution(self) -> None:
        assert lib.render_template("Hello {{NAME}}!", {"NAME": "world"}) == "Hello world!"

    def test_multiple_tokens(self) -> None:
        text = "{{A}} and {{B}}"
        assert lib.render_template(text, {"A": "foo", "B": "bar"}) == "foo and bar"

    def test_no_tokens(self) -> None:
        assert lib.render_template("plain text", {}) == "plain text"

    def test_raises_on_leftover_token(self) -> None:
        with pytest.raises(ValueError, match="Unfilled"):
            lib.render_template("Hello {{MISSING}}!", {"NAME": "x"})

    def test_multiple_occurrences(self) -> None:
        assert lib.render_template("{{X}} {{X}}", {"X": "hi"}) == "hi hi"

    def test_extra_mapping_ok(self) -> None:
        # Extra keys that don't appear in text are fine
        assert lib.render_template("{{A}}", {"A": "1", "B": "2"}) == "1"


# ---------------------------------------------------------------------------
# upsert_claude_md
# ---------------------------------------------------------------------------

BEGIN = "<!-- BEGIN test -->"
END = "<!-- END test -->"
BLOCK = f"{BEGIN}\n## Managed\ncontent\n{END}"


class TestUpsertClaudeMd:
    def test_insert_when_markers_absent(self) -> None:
        existing = "# My CLAUDE.md\n\nSome text."
        result = lib.upsert_claude_md(existing, BLOCK, BEGIN, END)
        assert result.endswith(BLOCK)
        assert "Some text." in result

    def test_replace_when_markers_present(self) -> None:
        existing = f"# Header\n\n{BEGIN}\nold content\n{END}\n\nTrailing."
        new_block = f"{BEGIN}\nnew content\n{END}"
        result = lib.upsert_claude_md(existing, new_block, BEGIN, END)
        assert "old content" not in result
        assert "new content" in result
        assert "# Header" in result
        assert "Trailing." in result

    def test_idempotent(self) -> None:
        existing = f"# Header\n\n{BLOCK}\n"
        result = lib.upsert_claude_md(existing, BLOCK, BEGIN, END)
        result2 = lib.upsert_claude_md(result, BLOCK, BEGIN, END)
        assert result == result2

    def test_preserves_surrounding_text(self) -> None:
        existing = f"Before\n{BEGIN}\nold\n{END}\nAfter"
        result = lib.upsert_claude_md(existing, BLOCK, BEGIN, END)
        assert result.startswith("Before")
        assert "After" in result

    def test_empty_existing(self) -> None:
        result = lib.upsert_claude_md("", BLOCK, BEGIN, END)
        assert BLOCK in result

    def test_append_after_single_newline_uses_one_blank_line(self) -> None:
        result = lib.upsert_claude_md("# Header\n", BLOCK, BEGIN, END)
        assert result == "# Header\n\n" + BLOCK

    def test_append_after_double_newline_does_not_add_extra_newline(self) -> None:
        result = lib.upsert_claude_md("# Header\n\n", BLOCK, BEGIN, END)
        assert result == "# Header\n\n" + BLOCK


# ---------------------------------------------------------------------------
# resolve_release_asset
# ---------------------------------------------------------------------------

FAKE_RELEASE = {
    "tag_name": "v1.0.0",
    "assets": [
        {"name": "manifest.json", "browser_download_url": "https://example.com/manifest.json"},
        {"name": "main.js", "browser_download_url": "https://example.com/main.js"},
        {"name": "styles.css", "browser_download_url": "https://example.com/styles.css"},
        {"name": "plugin-v1.0.0.zip", "browser_download_url": "https://example.com/plugin.zip"},
    ],
}

FAKE_RELEASE_NO_STYLES = {
    "tag_name": "v1.0.0",
    "assets": [
        {"name": "manifest.json", "browser_download_url": "https://example.com/manifest.json"},
        {"name": "main.js", "browser_download_url": "https://example.com/main.js"},
    ],
}

FAKE_RELEASE_MISSING_MAIN = {
    "tag_name": "v1.0.0",
    "assets": [
        {"name": "manifest.json", "browser_download_url": "https://example.com/manifest.json"},
    ],
}


class TestResolveReleaseAsset:
    def test_returns_correct_urls(self) -> None:
        result = lib.resolve_release_asset(
            FAKE_RELEASE, ["manifest.json", "main.js", "styles.css"]
        )
        assert result["manifest.json"] == "https://example.com/manifest.json"
        assert result["main.js"] == "https://example.com/main.js"
        assert result["styles.css"] == "https://example.com/styles.css"

    def test_unrelated_zip_not_included(self) -> None:
        result = lib.resolve_release_asset(
            FAKE_RELEASE, ["manifest.json", "main.js", "styles.css"]
        )
        assert "plugin-v1.0.0.zip" not in result

    def test_styles_optional_omitted_when_absent(self) -> None:
        result = lib.resolve_release_asset(
            FAKE_RELEASE_NO_STYLES, ["manifest.json", "main.js", "styles.css"]
        )
        assert "styles.css" not in result
        assert "manifest.json" in result
        assert "main.js" in result

    def test_raises_key_error_when_main_js_missing(self) -> None:
        with pytest.raises(KeyError):
            lib.resolve_release_asset(
                FAKE_RELEASE_MISSING_MAIN, ["manifest.json", "main.js", "styles.css"]
            )

    def test_raises_key_error_when_manifest_missing(self) -> None:
        release = {
            "assets": [
                {"name": "main.js", "browser_download_url": "https://example.com/main.js"},
            ]
        }
        with pytest.raises(KeyError):
            lib.resolve_release_asset(release, ["manifest.json", "main.js"])

    def test_empty_assets(self) -> None:
        with pytest.raises(KeyError):
            lib.resolve_release_asset({"assets": []}, ["manifest.json", "main.js"])


# ---------------------------------------------------------------------------
# validate_plugin_dir
# ---------------------------------------------------------------------------

class TestValidatePluginDir:
    def test_all_present(self) -> None:
        assert lib.validate_plugin_dir({"manifest.json": b"{}", "main.js": b"x"}) == []

    def test_missing_main_js(self) -> None:
        assert lib.validate_plugin_dir({"manifest.json": b"{}"}) == ["main.js"]

    def test_missing_manifest(self) -> None:
        assert lib.validate_plugin_dir({"main.js": b"x"}) == ["manifest.json"]

    def test_both_missing(self) -> None:
        result = lib.validate_plugin_dir({})
        assert "manifest.json" in result
        assert "main.js" in result

    def test_extra_files_ok(self) -> None:
        assert lib.validate_plugin_dir(
            {"manifest.json": b"{}", "main.js": b"x", "styles.css": b""}
        ) == []

    def test_result_sorted(self) -> None:
        result = lib.validate_plugin_dir({})
        assert result == sorted(result)


# ---------------------------------------------------------------------------
# strip_claude_mem_hooks
# ---------------------------------------------------------------------------

class TestStripClaudeMemHooks:
    def _settings_with_claude_mem(self) -> dict:
        return {
            "hooks": {
                "SessionEnd": [
                    {
                        "hooks": [
                            {"type": "command", "command": "~/.claude/hooks/claude-mem.sh"},
                            {"type": "command", "command": "~/.claude/hooks/session-end.sh"},
                        ]
                    },
                    CLAUDEBAR_ENTRY,
                ],
                "Stop": [
                    {"hooks": [{"type": "command", "command": "echo done"}]}
                ],
            }
        }

    def test_removes_claude_mem_command(self) -> None:
        settings = self._settings_with_claude_mem()
        new_s, removed = lib.strip_claude_mem_hooks(settings)
        cmds = [
            h["command"]
            for entries in new_s.get("hooks", {}).values()
            for e in entries
            for h in e.get("hooks", [])
        ]
        assert "~/.claude/hooks/claude-mem.sh" not in cmds

    def test_removed_list_contains_cmd(self) -> None:
        settings = self._settings_with_claude_mem()
        _, removed = lib.strip_claude_mem_hooks(settings)
        assert "~/.claude/hooks/claude-mem.sh" in removed

    def test_non_claude_mem_cmd_preserved(self) -> None:
        settings = self._settings_with_claude_mem()
        new_s, _ = lib.strip_claude_mem_hooks(settings)
        cmds = [
            h["command"]
            for entries in new_s.get("hooks", {}).values()
            for e in entries
            for h in e.get("hooks", [])
        ]
        assert "~/.claude/hooks/session-end.sh" in cmds

    def test_stop_hook_preserved(self) -> None:
        settings = self._settings_with_claude_mem()
        new_s, _ = lib.strip_claude_mem_hooks(settings)
        assert new_s["hooks"]["Stop"] == settings["hooks"]["Stop"]

    def test_does_not_mutate_input(self) -> None:
        settings = self._settings_with_claude_mem()
        original = copy.deepcopy(settings)
        lib.strip_claude_mem_hooks(settings)
        assert settings == original

    def test_no_claude_mem_noop(self) -> None:
        settings = {"hooks": {"SessionEnd": [CLAUDEBAR_ENTRY]}}
        new_s, removed = lib.strip_claude_mem_hooks(settings)
        assert removed == []
        assert new_s["hooks"]["SessionEnd"] == [CLAUDEBAR_ENTRY]

    def test_empty_settings(self) -> None:
        new_s, removed = lib.strip_claude_mem_hooks({})
        assert removed == []

    def test_multiple_events(self) -> None:
        settings = {
            "hooks": {
                "PreToolUse": [
                    {"hooks": [{"type": "command", "command": "/usr/bin/claude-mem-pre.sh"}]}
                ],
                "PostToolUse": [
                    {"hooks": [{"type": "command", "command": "echo safe"}]}
                ],
            }
        }
        new_s, removed = lib.strip_claude_mem_hooks(settings)
        assert "/usr/bin/claude-mem-pre.sh" in removed
        pre_cmds = [
            h["command"]
            for e in new_s["hooks"].get("PreToolUse", [])
            for h in e.get("hooks", [])
        ]
        assert "/usr/bin/claude-mem-pre.sh" not in pre_cmds
        # PostToolUse untouched
        post_cmds = [
            h["command"]
            for e in new_s["hooks"].get("PostToolUse", [])
            for h in e.get("hooks", [])
        ]
        assert "echo safe" in post_cmds


# ---------------------------------------------------------------------------
# classify_memory_tooling
# ---------------------------------------------------------------------------

class TestClassifyMemoryTooling:
    def test_detects_claude_mem_via_hook(self) -> None:
        settings = {
            "hooks": {
                "SessionEnd": [
                    {"hooks": [{"type": "command", "command": "~/.claude/hooks/claude-mem.sh"}]}
                ]
            }
        }
        result = lib.classify_memory_tooling(settings, [], [])
        assert result["claude_mem"] is True

    def test_detects_claude_mem_via_plugin_dir(self) -> None:
        result = lib.classify_memory_tooling({}, ["claude-mem"], [])
        assert result["claude_mem"] is True

    def test_detects_thedotmack_via_plugin_dir(self) -> None:
        result = lib.classify_memory_tooling({}, ["thedotmack-plugin"], [])
        assert result["claude_mem"] is True

    def test_detects_claude_mem_via_mcp(self) -> None:
        result = lib.classify_memory_tooling({}, [], ["claude-mem-mcp"])
        assert result["claude_mem"] is True

    def test_no_claude_mem(self) -> None:
        result = lib.classify_memory_tooling({}, ["obsidian-git"], ["fs-server"])
        assert result["claude_mem"] is False

    def test_flags_unknown_memory_names(self) -> None:
        result = lib.classify_memory_tooling({}, ["my-recall-plugin"], [])
        assert "my-recall-plugin" in result["unknown"]

    def test_knowledge_flagged_as_unknown(self) -> None:
        result = lib.classify_memory_tooling({}, [], ["knowledge-base-mcp"])
        assert "knowledge-base-mcp" in result["unknown"]

    def test_known_safe_not_flagged(self) -> None:
        # session-end.sh is known safe even though it's a hook runner
        result = lib.classify_memory_tooling({}, ["session-end.sh"], [])
        assert "session-end.sh" not in result["unknown"]
        assert result["claude_mem"] is False

    def test_claudebar_not_flagged(self) -> None:
        result = lib.classify_memory_tooling({}, ["claudebar"], [])
        assert result["claude_mem"] is False
        assert result["unknown"] == []

    def test_non_memory_names_ignored(self) -> None:
        result = lib.classify_memory_tooling(
            {}, ["obsidian-git", "dataview", "templater"], []
        )
        assert result["claude_mem"] is False
        assert result["unknown"] == []

    def test_claude_mem_not_in_unknown(self) -> None:
        # claude-mem should set claude_mem=True, NOT appear in unknown
        result = lib.classify_memory_tooling({}, ["claude-mem"], [])
        assert result["claude_mem"] is True
        assert "claude-mem" not in result["unknown"]

    def test_empty_all(self) -> None:
        result = lib.classify_memory_tooling({}, [], [])
        assert result == {"claude_mem": False, "unknown": []}
