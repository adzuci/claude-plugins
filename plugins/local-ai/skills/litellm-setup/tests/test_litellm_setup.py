"""Tests for the local LiteLLM setup helper."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "litellm_setup.sh"

if not SCRIPT.exists():
    pytest.skip("litellm_setup.sh is missing", allow_module_level=True)

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash is required"
)


def run_script(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    environment = os.environ.copy()
    environment["HOME"] = str(tmp_path)
    return subprocess.run(
        [str(SCRIPT), *args], capture_output=True, text=True, env=environment
    )


def test_default_check_does_not_create_files(tmp_path: Path):
    result = run_script(tmp_path)
    assert result.returncode == 0
    assert "configuration missing" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_apply_writes_secret_free_private_config(tmp_path: Path):
    result = run_script(tmp_path, "--apply", "--model", "qwen3:14b")
    assert result.returncode == 0
    config = tmp_path / ".config/local-ai/litellm/config.yaml"
    text = config.read_text()
    assert "model: openai/qwen3:14b" in text
    assert "os.environ/LOCAL_AI_PROXY_KEY" in text
    assert "os.environ/LITELLM_MASTER_KEY" in text
    assert "sk-" not in text
    assert config.stat().st_mode & 0o077 == 0


def test_apply_does_not_overwrite_existing_config(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config = config_dir / "config.yaml"
    config.write_text("keep-me\n")
    result = run_script(tmp_path, "--apply", "--dir", str(config_dir))
    assert result.returncode == 0
    assert config.read_text() == "keep-me\n"


def test_install_requires_apply(tmp_path: Path):
    result = run_script(tmp_path, "--install")
    assert result.returncode == 2
    assert "requires --apply" in result.stderr


def test_installer_uses_isolated_pinned_package():
    text = SCRIPT.read_text()
    assert 'LITELLM_VERSION="1.101.0"' in text
    assert '"litellm[proxy]==${LITELLM_VERSION}"' in text
    assert "pip3 install" not in text
    assert "python3 -m venv" in text


def test_unknown_argument_is_rejected(tmp_path: Path):
    result = run_script(tmp_path, "--bogus")
    assert result.returncode == 2


def test_help_is_actionable(tmp_path: Path):
    result = run_script(tmp_path, "--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout


@pytest.mark.parametrize("flag", ["--dir", "--venv", "--model"])
def test_missing_argument_values_are_rejected(tmp_path: Path, flag: str):
    result = run_script(tmp_path, flag)
    assert result.returncode == 2


def test_script_is_valid_bash_and_executable():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert SCRIPT.stat().st_mode & 0o111
