"""test_bq_preflight.py — hermetic tests for bq_preflight.sh.

Modeled on plugins/apollo-eng-devops/skills/k8s-safe-exec/tests/test_k8s_safe_exec.py:
the script is a bash script, not a Python module, so it is exercised as a
subprocess with a fake PATH containing stub gcloud/bq/jq/brew shell scripts.
No live gcloud/bq/jq/brew is ever invoked; the real ones are also hidden from
PATH so the tests never depend on (or affect) the host's actual GCP auth
state.

Runs on Python 3.9 (see repo CLAUDE.md Testing convention).
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "bq_preflight.sh"

if not SCRIPT.exists():
    pytest.skip("bq_preflight.sh has not landed yet", allow_module_level=True)

if shutil.which("bash") is None:
    pytest.skip("bash is not available on this machine", allow_module_level=True)


def _write_stub(bin_dir: Path, name: str, body: str) -> Path:
    path = bin_dir / name
    path.write_text("#!/usr/bin/env bash\n" + body + "\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


# Coreutils bq_preflight.sh shells out to besides gcloud/bq/jq/brew — symlinked
# into bin_dir so PATH can be narrowed to the stub dir alone (see bin_dir
# fixture below). "bash" itself is included since the script is invoked as
# `bash <script>` and subprocess resolves it via this same isolated PATH.
# "touch" is included because the test stubs (not the script) use it to
# record that a stub ran.
_REQUIRED_HOST_TOOLS = ("bash", "cat", "head", "tr", "touch")


def _fake_path_env(bin_dir: Path, home_dir: Path, extra=None) -> dict:
    # PATH is ONLY the stub dir: this hides any real gcloud/bq/jq/brew
    # elsewhere on the host (e.g. a Homebrew or gcloud-SDK bin directory) so
    # tests can never accidentally find or touch live GCP state. HOME is an
    # isolated tmp dir for the same reason (no real gcloud config to read).
    env = {
        "PATH": str(bin_dir),
        "HOME": str(home_dir),
    }
    if extra:
        env.update(extra)
    return env


def run(bin_dir: Path, args, env_overrides=None, stdin: str = None, timeout=10):
    home_dir = bin_dir.parent / "home"
    home_dir.mkdir(exist_ok=True)
    env = _fake_path_env(bin_dir, home_dir, env_overrides)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _install_passing_stubs(bin_dir: Path):
    _write_stub(
        bin_dir,
        "gcloud",
        """
case "$1 $2" in
  "auth list")
    echo "adam.blackwell@apollo.io"
    exit 0
    ;;
esac
exit 0
""",
    )
    _write_stub(
        bin_dir,
        "bq",
        """
echo "f0"
echo "1"
exit 0
""",
    )
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")


@pytest.fixture
def bin_dir(tmp_path: Path) -> Path:
    d = tmp_path / "bin"
    d.mkdir()
    for tool in _REQUIRED_HOST_TOOLS:
        real = shutil.which(tool)
        if real is None:
            pytest.skip("{0} is not available on this machine".format(tool))
        os.symlink(real, d / tool)
    return d


# ---------------------------------------------------------------------------
# --check: usage
# ---------------------------------------------------------------------------


def test_unrecognized_argument_exits_2(bin_dir):
    _install_passing_stubs(bin_dir)
    result = run(bin_dir, ["--bogus"])
    assert result.returncode == 2
    assert "unrecognized" in result.stderr.lower()


def test_extra_arguments_exit_2(bin_dir):
    _install_passing_stubs(bin_dir)
    result = run(bin_dir, ["--check", "extra"])
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# --check: passing path
# ---------------------------------------------------------------------------


def test_check_passes_with_all_stubs_present(bin_dir):
    _install_passing_stubs(bin_dir)
    result = run(bin_dir, ["--check"])
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout
    assert "verdict: PASS" in result.stdout


def test_check_is_default_when_no_argument_given(bin_dir):
    _install_passing_stubs(bin_dir)
    result = run(bin_dir, [])
    assert result.returncode == 0
    assert "verdict: PASS" in result.stdout


# ---------------------------------------------------------------------------
# --check: hard failures
# ---------------------------------------------------------------------------


def test_check_fails_when_bq_missing(bin_dir):
    # gcloud and jq present, bq deliberately absent from the stub PATH.
    _write_stub(bin_dir, "gcloud", 'echo "adam.blackwell@apollo.io"\nexit 0')
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")
    result = run(bin_dir, ["--check"])
    assert result.returncode == 1
    assert "bq is not installed" in result.stderr
    assert "verdict: FAIL" in result.stdout


def test_check_fails_when_gcloud_missing(bin_dir):
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")
    result = run(bin_dir, ["--check"])
    assert result.returncode == 1
    assert "gcloud is not installed" in result.stderr


def test_check_fails_when_no_active_account(bin_dir):
    _install_passing_stubs(bin_dir)
    _write_stub(bin_dir, "gcloud", 'case "$1 $2" in "auth list") exit 0 ;; esac\nexit 0')
    result = run(bin_dir, ["--check"])
    assert result.returncode == 1
    assert "No active gcloud account" in result.stderr


def test_check_fails_when_account_not_apollo(bin_dir):
    _install_passing_stubs(bin_dir)
    _write_stub(
        bin_dir,
        "gcloud",
        'case "$1 $2" in "auth list") echo "someone@gmail.com"; exit 0 ;; esac\nexit 0',
    )
    result = run(bin_dir, ["--check"])
    assert result.returncode == 1
    assert "not an @apollo.io account" in result.stderr


def test_check_fails_when_smoke_query_fails(bin_dir):
    _install_passing_stubs(bin_dir)
    _write_stub(bin_dir, "bq", 'echo "permission denied" >&2\nexit 1')
    result = run(bin_dir, ["--check"])
    assert result.returncode == 1
    assert "smoke test failed" in result.stderr


# ---------------------------------------------------------------------------
# --install: never installs without an explicit "yes", and never offers to
# install anything when nothing is missing.
# ---------------------------------------------------------------------------


def _stub_bq_missing(bin_dir: Path):
    # gcloud and jq present, bq deliberately absent — this is the
    # MISSING_TOOL=1 path that should reach the install prompt under
    # --install, distinct from the "gcloud missing" early-exit path.
    _write_stub(bin_dir, "gcloud", 'echo "adam.blackwell@apollo.io"\nexit 0')
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")


def test_install_prints_nothing_to_install_when_all_present(bin_dir, tmp_path):
    _install_passing_stubs(bin_dir)
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"])

    assert not marker.exists(), "brew must never run when nothing is missing"
    assert result.returncode == 0
    assert "nothing to install" in result.stdout.lower()


def test_install_without_tty_or_confirmation_does_not_call_brew(bin_dir, tmp_path):
    _stub_bq_missing(bin_dir)
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    # No stdin (non-interactive, no TTY) and BQ_PREFLIGHT_YES unset: the
    # script must refuse to install rather than assume consent.
    result = run(bin_dir, ["--install"], stdin="")

    assert not marker.exists(), "brew must never run without explicit confirmation"
    assert result.returncode == 1
    assert "declined" in result.stdout.lower() or "refusing" in result.stdout.lower()


def test_install_with_explicit_no_does_not_call_brew(bin_dir, tmp_path):
    _stub_bq_missing(bin_dir)
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"], stdin="n\n")

    assert not marker.exists()
    assert result.returncode == 1


def test_install_with_explicit_yes_calls_brew(bin_dir, tmp_path):
    _stub_bq_missing(bin_dir)
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"], stdin="y\n")

    assert marker.exists(), "brew should run once the prompt is explicitly confirmed"
    assert result.returncode == 1


def test_install_env_escape_hatch_calls_brew_without_stdin(bin_dir, tmp_path):
    # BQ_PREFLIGHT_YES=1 is documented as test-only; confirms the escape
    # hatch works without needing to simulate a TTY.
    _stub_bq_missing(bin_dir)
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"], env_overrides={"BQ_PREFLIGHT_YES": "1"})

    assert marker.exists()
    assert result.returncode == 1


def test_install_offers_brew_when_gcloud_is_missing(bin_dir, tmp_path):
    # The case --install exists for: no gcloud on PATH. The script must still
    # report FAIL (exit 1) but must reach the install prompt, otherwise the
    # documented install path can never fire.
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"], env_overrides={"BQ_PREFLIGHT_YES": "1"})

    assert result.returncode == 1, result.stdout
    assert marker.exists(), "--install must reach the brew step when gcloud is missing"


def test_install_does_not_offer_brew_when_gcloud_missing_but_not_confirmed(
    bin_dir, tmp_path
):
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"], stdin="n\n")

    assert result.returncode == 1
    assert not marker.exists()


def test_check_alone_never_offers_brew_when_gcloud_is_missing(bin_dir, tmp_path):
    # --check is read-only: a missing tool must never trigger an install,
    # even with the test escape hatch set.
    _write_stub(bin_dir, "jq", "echo 'jq-1.7'\nexit 0")
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--check"], env_overrides={"BQ_PREFLIGHT_YES": "1"})

    assert result.returncode == 1
    assert not marker.exists()


def test_install_does_not_offer_brew_when_only_the_smoke_query_fails(bin_dir, tmp_path):
    # An auth/permission failure is not fixed by brew; --install must surface
    # the --check failure and never reach the install prompt.
    _install_passing_stubs(bin_dir)
    _write_stub(bin_dir, "bq", 'echo "permission denied" >&2\nexit 1')
    marker = tmp_path / "brew_was_called"
    _write_stub(bin_dir, "brew", 'touch "{0}"\nexit 0'.format(marker))

    result = run(bin_dir, ["--install"], env_overrides={"BQ_PREFLIGHT_YES": "1"})

    assert result.returncode == 1
    assert not marker.exists()
