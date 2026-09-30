"""Make the sibling scripts/ directory importable as top-level modules in tests."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import copy
import json

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def load():
    """Return a loader that deep-copies a fixture so tests can mutate it."""

    def _load(name):
        return copy.deepcopy(json.loads((FIXTURES / f"{name}.json").read_text()))

    return _load
