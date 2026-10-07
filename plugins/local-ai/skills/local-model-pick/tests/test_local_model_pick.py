"""Tests for local-model-pick's pure shell helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "local_model_pick.sh"

if not SCRIPT.exists():
    pytest.skip("local_model_pick.sh is missing", allow_module_level=True)

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash is required"
)


def sh(snippet: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", f". {SCRIPT}\n{snippet}"],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "memory_gb,expected",
    [
        (128, "qwen3-coder:30b"),
        (64, "qwen3-coder:30b"),
        (63, "gpt-oss:20b"),
        (48, "gpt-oss:20b"),
        (47, "qwen3:14b"),
        (32, "qwen3:14b"),
        (31, "qwen3:8b"),
        (16, "qwen3:8b"),
    ],
)
def test_model_for_ram(memory_gb: int, expected: str):
    assert sh(f"model_for_ram {memory_gb}").stdout.strip() == expected


def test_every_recommended_model_has_size_and_headroom():
    for memory_gb in (16, 32, 48, 64):
        model = sh(f"model_for_ram {memory_gb}").stdout.strip()
        size = float(sh(f"model_size_gb {model}").stdout.strip())
        headroom = float(sh(f"model_headroom_gb {model}").stdout.strip())
        assert size > 0
        assert headroom > size


def test_unknown_argument_is_rejected_before_platform_check():
    result = subprocess.run(
        [str(SCRIPT), "--bogus"], capture_output=True, text=True
    )
    assert result.returncode == 2


def test_help_is_actionable():
    result = subprocess.run(
        [str(SCRIPT), "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_script_is_valid_bash_and_executable():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert SCRIPT.stat().st_mode & 0o111
