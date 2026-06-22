"""
Tests for read-only client/environment detection.
"""
from __future__ import annotations

import pytest

from .conftest import load_script_module

check_env = load_script_module("check_env")


def test_build_report_includes_multi_client_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_env, "detect_macos", lambda: True)
    monkeypatch.setattr(check_env, "detect_brew", lambda: False)
    monkeypatch.setattr(check_env, "detect_obsidian", lambda is_mac: False)
    monkeypatch.setattr(check_env, "detect_which", lambda name: name in {"git", "codex", "jq"})
    monkeypatch.setattr(check_env, "detect_path", lambda path, kind="any": path.endswith("sessions") and kind == "dir")

    report = check_env.build_report()

    assert report["git"] is True
    assert report["claude"] is False
    assert report["codex"] is True
    assert report["codex_sessions"] is True
    assert report["codex_session_index"] is False
    assert report["antigravity_brain"] is False
