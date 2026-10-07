from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "checkpoint.py"
SPEC = importlib.util.spec_from_file_location("slack_response_checkpoint", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_missing_checkpoint_is_empty(tmp_path: Path) -> None:
    assert MODULE.load_state(tmp_path / "checkpoint.json") == MODULE.empty_state()


def test_complete_is_atomic_private_and_deduplicated(tmp_path: Path) -> None:
    path = tmp_path / "state" / "checkpoint.json"
    MODULE.complete(path, "2026-09-30T17:00:00Z", ["thread-1", "thread-1", "thread-2"])

    state = MODULE.load_state(path)
    assert state["last_success"] == "2026-09-30T17:00:00Z"
    assert state["surfaced_item_ids"] == ["thread-1", "thread-2"]
    assert path.stat().st_mode & 0o777 == 0o600


def test_complete_preserves_existing_ids(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    MODULE.complete(path, "2026-09-30T17:00:00Z", ["thread-1"])
    MODULE.complete(path, "2026-09-30T18:00:00Z", ["thread-2"])

    assert MODULE.load_state(path)["surfaced_item_ids"] == ["thread-1", "thread-2"]


def test_timestamp_must_be_utc() -> None:
    with pytest.raises(Exception, match="UTC"):
        MODULE.parse_utc("2026-09-30T13:00:00-04:00")
