"""
Tests for Codex and Antigravity vault importers.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .conftest import load_script_module

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

codex_importer = load_script_module("codex_session_importer")
antigravity_importer = load_script_module("antigravity_session_importer")
install_antigravity_hook = load_script_module("install_antigravity_hook")


def _write_jsonl(path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def test_importer_scripts_resolve_local_helpers_from_any_cwd(tmp_path) -> None:
    for script in ["codex_session_importer.py", "antigravity_session_importer.py"]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--help"],
            cwd=tmp_path,
            check=True,
            text=True,
            capture_output=True,
        )
        assert "usage:" in result.stdout


def test_redact_handles_named_and_bare_secret_patterns() -> None:
    common = load_script_module("session_importer_common")

    text = common.redact("api_key=abc123 sk-live-secret-token")

    assert "api_key=[REDACTED]" in text
    assert "sk-live-secret-token" not in text


def test_codex_importer_dry_run_does_not_write(tmp_path) -> None:
    rollout = tmp_path / "sessions" / "2026" / "06" / "07" / "rollout-test.jsonl"
    _write_jsonl(
        rollout,
        [
            {
                "type": "session_meta",
                "timestamp": "2026-06-07T10:00:00Z",
                "payload": {
                    "id": "sess-1",
                    "timestamp": "2026-06-07T10:00:00Z",
                    "cwd": "/repo/demo",
                    "originator": "Codex Desktop",
                    "git": {"branch": "feature"},
                },
            },
            {"type": "event_msg", "payload": {"type": "user_message", "text": "please fix"}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "agent_message",
                    "text": "Implemented the importer and verified tests.",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Updated Codex response parsing."}],
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 5,
                            "output_tokens": 7,
                            "reasoning_output_tokens": 2,
                        }
                    },
                },
            },
        ],
    )

    result = codex_importer.run(
        vault=tmp_path / "vault",
        sessions_root=tmp_path / "sessions",
        state_file=tmp_path / "state",
        limit=3,
        dry_run=True,
    )

    assert result["count"] == 1
    assert "- **source:** codex" in result["sessions"][0]["entry"]
    assert "7 out / 15 in" in result["sessions"][0]["entry"]
    assert "3 msgs" in result["sessions"][0]["entry"]
    assert "Updated Codex response parsing." in result["sessions"][0]["entry"]
    assert not (tmp_path / "vault" / "sessions" / "2026-06-07.md").exists()
    assert not (tmp_path / "state").exists()


def test_codex_importer_writes_state_and_skips_second_run(tmp_path) -> None:
    rollout = tmp_path / "sessions" / "rollout-test.jsonl"
    _write_jsonl(
        rollout,
        [
            {
                "type": "session_meta",
                "payload": {"id": "sess-1", "timestamp": "2026-06-07T10:00:00Z"},
            }
        ],
    )

    first = codex_importer.run(tmp_path / "vault", tmp_path / "sessions", tmp_path / "state", 0, False)
    second = codex_importer.run(tmp_path / "vault", tmp_path / "sessions", tmp_path / "state", 0, False)

    assert first["count"] == 1
    assert second["count"] == 0
    assert (tmp_path / "state").read_text().strip() == "sess-1"


def test_codex_importer_dedupes_duplicate_ids_within_one_run(tmp_path) -> None:
    for idx in range(2):
        rollout = tmp_path / "sessions" / f"rollout-{idx}.jsonl"
        _write_jsonl(
            rollout,
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "same-session", "timestamp": "2026-06-07T10:00:00Z"},
                }
            ],
        )

    result = codex_importer.run(tmp_path / "vault", tmp_path / "sessions", tmp_path / "state", 0, False)

    assert result["count"] == 1
    assert (tmp_path / "state").read_text().strip() == "same-session"


def test_antigravity_importer_dry_run_uses_metadata_and_task(tmp_path) -> None:
    convo = tmp_path / "brain" / "conv-1"
    convo.mkdir(parents=True)
    (convo / "task.md.metadata.json").write_text(
        json.dumps(
            {
                "summary": "Task checklist tracking Antigravity migration.",
                "updatedAt": "2026-06-05T22:21:55Z",
            }
        )
    )
    (convo / "task.md").write_text("# Migration Task\n\n- [x] Create hook script\n")

    result = antigravity_importer.run(
        vault=tmp_path / "vault",
        brain_root=tmp_path / "brain",
        state_file=tmp_path / "state",
        limit=1,
        dry_run=True,
    )

    assert result["count"] == 1
    entry = result["sessions"][0]["entry"]
    assert "- **source:** antigravity" in entry
    assert "unavailable locally" in entry
    assert "Task checklist tracking Antigravity migration." in entry
    assert not (tmp_path / "state").exists()


def test_antigravity_importer_ignores_non_string_metadata_summary(tmp_path) -> None:
    convo = tmp_path / "brain" / "conv-1"
    convo.mkdir(parents=True)
    (convo / "task.md.metadata.json").write_text(json.dumps({"summary": {"not": "text"}, "updatedAt": 123}))
    (convo / "implementation_plan.md.metadata.json").write_text(
        json.dumps({"summary": "String summary still works.", "updatedAt": "2026-06-05T22:21:55Z"})
    )
    (convo / "task.md").write_text("# Migration Task\n\n- [x] Create hook script\n")

    result = antigravity_importer.run(
        vault=tmp_path / "vault",
        brain_root=tmp_path / "brain",
        state_file=tmp_path / "state",
        limit=1,
        dry_run=True,
    )

    assert result["count"] == 1
    assert "String summary still works." in result["sessions"][0]["entry"]
    assert "- [x] Create hook script" in result["sessions"][0]["entry"]


def test_install_antigravity_hook_is_idempotent(tmp_path) -> None:
    first = install_antigravity_hook.install("/tmp/vault", tmp_path, now=123)
    second = install_antigravity_hook.install("/tmp/vault", tmp_path, now=124)

    assert first["ok"] is True
    assert first["changed"] is True
    assert second["ok"] is True
    assert second["changed"] is False
    hooks = json.loads((tmp_path / ".gemini" / "config" / "hooks.json").read_text())
    commands = [
        hook["command"]
        for entry in hooks["SessionEnd"]
        for hook in entry.get("hooks", [])
    ]
    assert len(commands) == 1


def test_install_antigravity_hook_shell_quotes_vault(tmp_path) -> None:
    result = install_antigravity_hook.install("/tmp/vault with $(danger)", tmp_path, now=123)

    assert result["ok"] is True
    assert "'/tmp/vault with $(danger)'" in result["command"]


def test_install_antigravity_hook_backs_up_malformed_without_hook_write(tmp_path) -> None:
    hooks_path = tmp_path / ".gemini" / "config" / "hooks.json"
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text("{bad")

    result = install_antigravity_hook.install("/tmp/vault", tmp_path, now=123)

    assert result["ok"] is False
    assert hooks_path.read_text() == "{bad"
    assert (hooks_path.parent / "hooks.json.bak-123").exists()


def test_install_antigravity_hook_rejects_wrong_json_shape(tmp_path) -> None:
    hooks_path = tmp_path / ".gemini" / "config" / "hooks.json"
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text("[]")

    result = install_antigravity_hook.install("/tmp/vault", tmp_path, now=123)

    assert result["ok"] is False
    assert "JSON object" in result["error"]
    assert (hooks_path.parent / "hooks.json.bak-123").exists()


def test_antigravity_importer_missing_brain_root_is_empty(tmp_path) -> None:
    result = antigravity_importer.run(
        vault=tmp_path / "vault",
        brain_root=tmp_path / "missing-brain",
        state_file=tmp_path / "state",
        limit=3,
        dry_run=True,
    )

    assert result == {"dry_run": True, "count": 0, "sessions": []}
