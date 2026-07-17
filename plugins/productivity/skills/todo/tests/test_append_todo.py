from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "append_todo.py"
SPEC = importlib.util.spec_from_file_location("append_todo", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_adds_items_to_inbox_and_creates_columns() -> None:
    updated, result = MODULE.update_backlog("---\ntype: backlog\n---\n", ["Book travel", "Review contract"], False)
    assert result == {"added": 2, "promoted": 0, "skipped": 0}
    assert "## Inbox\n\n- [ ] Book travel\n- [ ] Review contract" in updated
    for section in MODULE.KANBAN_SECTIONS:
        assert f"## {section}" in updated


def test_repeated_item_is_idempotent() -> None:
    existing = "## Inbox\n\n- [ ] Book travel\n"
    updated, result = MODULE.update_backlog(existing, ["Book travel"], False)
    assert result == {"added": 0, "promoted": 0, "skipped": 1}
    assert updated.count("Book travel") == 1


def test_urgent_promotes_existing_item_without_duplication() -> None:
    existing = "## Inbox\n\n- [ ] Review contract\n"
    updated, result = MODULE.update_backlog(existing, ["Review contract"], True)
    assert result == {"added": 0, "promoted": 1, "skipped": 0}
    assert updated.count("Review contract") == 1
    assert "- [ ] URGENT — Review contract" in updated
