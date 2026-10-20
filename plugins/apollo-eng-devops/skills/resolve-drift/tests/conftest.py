"""Make the sibling scripts/ directory importable as top-level modules in tests."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if SCRIPTS.is_dir() and str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def load():
    """Return a loader that deep-copies a fixture so tests can mutate it."""

    def _load(name):
        return copy.deepcopy(json.loads((FIXTURES / f"{name}.json").read_text()))

    return _load
