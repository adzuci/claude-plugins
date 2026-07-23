from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_standup.py"
SPEC = importlib.util.spec_from_file_location("check_standup", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_accepts_concise_update() -> None:
    result = MODULE.metrics("Last week\n- Closed INFRA-1.\n\nIn flight\n- Driving INFRA-2.")
    assert result["valid"] is True
    assert result["bullets"] == 2


def test_rejects_eight_bullets() -> None:
    result = MODULE.metrics("\n".join(f"- Item {number}" for number in range(8)))
    assert result["valid"] is False
    assert result["bullets"] == 8


def test_rejects_ninety_words() -> None:
    result = MODULE.metrics(" ".join(["word"] * 90))
    assert result["valid"] is False
    assert result["words"] == 90
