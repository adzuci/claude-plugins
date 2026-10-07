"""Hermetic tests for the PAIR setup shell helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
LIB = SCRIPTS / "lib_pair.sh"

if not LIB.exists():
    pytest.skip("pair-setup scripts are missing", allow_module_level=True)

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash is required"
)


def sh(snippet: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", f". {LIB}\n{snippet}"],
        capture_output=True,
        text=True,
    )


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPTS / name), *args], capture_output=True, text=True
    )


def test_parse_mount_point_finds_first_mounted_entity():
    payload = '{"system-entities":[{"a":1},{"mount-point":"/Volumes/PAIR"}]}'
    result = sh(f"parse_mount_point '{payload}'")
    assert result.returncode == 0
    assert result.stdout.strip() == "/Volumes/PAIR"


def test_parse_mount_point_preserves_spaces():
    payload = '{"system-entities":[{"mount-point":"/Volumes/Personal AI Router"}]}'
    result = sh(f"parse_mount_point '{payload}'")
    assert result.returncode == 0
    assert result.stdout.strip() == "/Volumes/Personal AI Router"


@pytest.mark.parametrize(
    "payload",
    ['{"system-entities":[]}', '{"system-entities":[{"a":1}]}', "not json", ""],
)
def test_parse_mount_point_fails_closed(payload: str):
    assert sh(f"parse_mount_point '{payload}'").returncode != 0


@pytest.mark.parametrize(
    "current,candidate,force,valid,expected",
    [
        ("0.1.1", "0.1.1", "0", "1", "no"),
        ("0.1.1", "0.1.1", "0", "0", "yes"),
        ("0.1.1", "0.1.1", "1", "1", "yes"),
        ("0.1.0", "0.1.1", "0", "1", "yes"),
        ("", "0.1.1", "0", "0", "yes"),
    ],
)
def test_should_reinstall(current, candidate, force, valid, expected):
    result = sh(
        f'should_reinstall "{current}" "{candidate}" "{force}" "{valid}"'
    )
    assert result.stdout.strip() == expected


@pytest.mark.parametrize("role", ["host", "client"])
def test_validate_role_accepts_known_roles(role: str):
    result = sh(f'validate_role "{role}"')
    assert result.returncode == 0
    assert result.stdout.strip() == role


@pytest.mark.parametrize("role", ["", "HOST", "server", "host client"])
def test_validate_role_rejects_unknown_roles(role: str):
    assert sh(f'validate_role "{role}"').returncode != 0


@pytest.mark.parametrize(
    "command,expected",
    [
        ("ollama-proxy", "ok"),
        ("ollama", "bypassed"),
        ("", "absent"),
        ("nginx", "foreign"),
    ],
)
def test_classify_listener(command: str, expected: str):
    assert sh(f'classify_listener "{command}"').stdout.strip() == expected


def test_installer_pins_reviewed_release_and_digest():
    library = (SCRIPTS / "lib_pair.sh").read_text()
    installer = (SCRIPTS / "pair_install.sh").read_text()
    assert 'PAIR_VERSION="0.1.1"' in library
    assert "releases/latest" not in library
    assert (
        "ee719fd699308c87e289f799cd780b799636343865638e8af65a57b953cb3f44"
        in library
    )
    assert "read-only default" in installer
    assert "--apply" in installer


@pytest.mark.parametrize("script", ["pair_install.sh", "pair_doctor.sh"])
def test_scripts_reject_unknown_arguments(script: str):
    result = run_script(script, "--bogus")
    assert result.returncode == 2


@pytest.mark.parametrize(
    "script,flag", [("pair_install.sh", "--dmg"), ("pair_doctor.sh", "--role")]
)
def test_scripts_reject_missing_argument_values(script: str, flag: str):
    result = run_script(script, flag)
    assert result.returncode == 2


@pytest.mark.parametrize("script", ["pair_install.sh", "pair_doctor.sh"])
def test_help_is_actionable(script: str):
    result = run_script(script, "--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_scripts_are_valid_bash():
    for script in sorted(SCRIPTS.glob("*.sh")):
        result = subprocess.run(
            ["bash", "-n", str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, f"{script.name}: {result.stderr}"


def test_executable_scripts_have_execute_bit():
    for script in (SCRIPTS / "pair_install.sh", SCRIPTS / "pair_doctor.sh"):
        assert script.stat().st_mode & 0o111
