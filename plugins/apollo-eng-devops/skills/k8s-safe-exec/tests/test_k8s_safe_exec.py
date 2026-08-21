"""
test_k8s_safe_exec.py — hermetic tests for the k8s-safe-exec skill's bash
scripts (preflight.sh, posthealth.sh, lib_context.sh).

These are bash scripts, not Python modules, so we test them by invoking them
as subprocesses and asserting on exit codes / stdout / stderr — never by
importing them. Every test here must run WITHOUT a live cluster: namespace
and env-arg validation is pure and happens before any kubectl call, and the
K8S_SAFE_EXEC_SKIP_CLUSTER=1 escape hatch (documented in both scripts'
header comments) short-circuits before any live-cluster kubectl call so the
namespace-pattern logic can be exercised hermetically too.

Runs on Python 3.9 (see AGENTS.md "Testing" convention).
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
PREFLIGHT = SCRIPTS_DIR / "preflight.sh"
POSTHEALTH = SCRIPTS_DIR / "posthealth.sh"
LIB_CONTEXT = SCRIPTS_DIR / "lib_context.sh"
ALL_SCRIPTS = (PREFLIGHT, POSTHEALTH, LIB_CONTEXT)
EXECUTABLE_SCRIPTS = (PREFLIGHT, POSTHEALTH)

if not all(p.exists() for p in ALL_SCRIPTS):
    pytest.skip("k8s-safe-exec scripts have not landed yet", allow_module_level=True)

if shutil.which("bash") is None:
    pytest.skip("bash is not available on this machine", allow_module_level=True)

# A clean environment for every subprocess call: never inherit a stray
# K8S_SAFE_EXEC_SKIP_CLUSTER from the host shell into "should hard-fail on
# args" tests, and never let host kubeconfig/context state leak into a test
# that expects a specific pure-validation outcome.
BASE_ENV = {k: v for k, v in os.environ.items() if k != "K8S_SAFE_EXEC_SKIP_CLUSTER"}


def run(script: Path, args, env_overrides=None, timeout=10):
    env = dict(BASE_ENV)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(script), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Arg validation: missing / invalid env arg -> exit 2
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script", EXECUTABLE_SCRIPTS, ids=lambda p: p.name)
def test_missing_env_arg_exits_2(script):
    result = run(script, [])
    assert result.returncode == 2
    assert "stage" in result.stderr and "prod" in result.stderr


@pytest.mark.parametrize("script", EXECUTABLE_SCRIPTS, ids=lambda p: p.name)
@pytest.mark.parametrize("bad_env", ["production", "PROD", "dev", "staging", ""])
def test_invalid_env_arg_exits_2(script, bad_env):
    result = run(script, [bad_env])
    assert result.returncode == 2, (
        f"{script.name} {bad_env!r} -> exit {result.returncode}, "
        f"stderr={result.stderr!r}"
    )
    assert "stage" in result.stderr
    assert "prod" in result.stderr


@pytest.mark.parametrize("script", EXECUTABLE_SCRIPTS, ids=lambda p: p.name)
def test_usage_mentions_stage_and_prod(script):
    result = run(script, ["-h"])
    assert result.returncode == 0
    assert "stage" in result.stdout
    assert "prod" in result.stdout


# ---------------------------------------------------------------------------
# posthealth.sh: its own required args (-n, --pod) beyond the env arg
# ---------------------------------------------------------------------------


def test_posthealth_missing_namespace_exits_2():
    result = run(POSTHEALTH, ["prod", "--pod", "some-pod"])
    assert result.returncode == 2
    assert "-n" in result.stderr or "namespace" in result.stderr.lower()


def test_posthealth_missing_pod_exits_2():
    result = run(POSTHEALTH, ["prod", "-n", "leadgenie"])
    assert result.returncode == 2
    assert "--pod" in result.stderr or "pod" in result.stderr.lower()


def test_posthealth_bad_baseline_restarts_exits_2():
    result = run(
        POSTHEALTH,
        ["prod", "-n", "leadgenie", "--pod", "foo", "--baseline-restarts", "nope"],
    )
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# Namespace validation logic (preflight.sh), hermetic via SKIP_CLUSTER
# ---------------------------------------------------------------------------


def test_preview_namespace_rejected_in_prod():
    result = run(
        PREFLIGHT,
        ["prod", "-n", "preview-foo"],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "preview-foo" in combined
    assert "stage" in combined  # tells the operator preview-* is stage-only


def test_preview_namespace_accepted_in_stage():
    result = run(
        PREFLIGHT,
        ["stage", "-n", "preview-foo"],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    # Accepted by pattern: never the hard-reject exit code, even though
    # SKIP_CLUSTER mode can't confirm live existence (that's a WARN, exit 3).
    assert result.returncode != 1
    assert "preview-foo" in result.stdout


@pytest.mark.parametrize("env", ["prod", "stage"])
def test_leadgenie_namespace_accepted_in_both_envs(env):
    result = run(
        PREFLIGHT,
        [env, "-n", "leadgenie"],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode != 1
    assert "leadgenie" in result.stdout


@pytest.mark.parametrize("env", ["prod", "stage"])
def test_garbage_namespace_rejected(env):
    result = run(
        PREFLIGHT,
        [env, "-n", "totally-bogus-namespace-xyz"],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "totally-bogus-namespace-xyz" in combined


def test_fabric_studio_namespace_rejected_in_prod():
    result = run(
        PREFLIGHT,
        ["prod", "-n", "fabric-studio-widget"],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode == 1


def test_fabric_studio_namespace_accepted_in_stage():
    result = run(
        PREFLIGHT,
        ["stage", "-n", "fabric-studio-widget"],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode != 1


@pytest.mark.parametrize("prod_only_ns", ["leadgenie-beta", "marketing", "pricus", "resolve"])
def test_prod_only_namespace_accepted_in_prod(prod_only_ns):
    result = run(
        PREFLIGHT,
        ["prod", "-n", prod_only_ns],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode != 1


@pytest.mark.parametrize("prod_only_ns", ["leadgenie-beta", "marketing"])
def test_prod_only_namespace_rejected_in_stage(prod_only_ns):
    result = run(
        PREFLIGHT,
        ["stage", "-n", prod_only_ns],
        env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"},
    )
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Syntax / executability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script", ALL_SCRIPTS, ids=lambda p: p.name)
def test_bash_syntax_check(script):
    result = subprocess.run(
        ["bash", "-n", str(script)], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("script", EXECUTABLE_SCRIPTS, ids=lambda p: p.name)
def test_script_is_executable(script):
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR, f"{script.name} is not executable (chmod +x)"


# ---------------------------------------------------------------------------
# Regression guard: no mutating kubectl verbs anywhere in the source.
#
# Full comment lines and quoted string literals (echo/printf/hardfail
# messages that legitimately tell the *operator* what command to run, e.g.
# "kubectl config use-context <ctx>") are stripped before matching, so this
# guards against an actual invocation being added later without flagging
# the scripts' own read-only documentation.
# ---------------------------------------------------------------------------

_FORBIDDEN_PATTERNS = [
    re.compile(r"\bexec\b"),
    re.compile(r"\bdelete\s"),
    re.compile(r"\bpatch\b"),
    re.compile(r"\bapply\b"),
    re.compile(r"\buse-context\b"),
    re.compile(r"\bscale\b"),
]


def _strip_comments_and_string_literals(text: str) -> str:
    kept_lines = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        line = re.sub(r'"[^"]*"', '""', line)
        line = re.sub(r"'[^']*'", "''", line)
        kept_lines.append(line)
    return "\n".join(kept_lines)


@pytest.mark.parametrize("script", ALL_SCRIPTS, ids=lambda p: p.name)
def test_no_mutating_kubectl_verbs_in_executable_code(script):
    code = _strip_comments_and_string_literals(script.read_text())
    for pattern in _FORBIDDEN_PATTERNS:
        match = pattern.search(code)
        assert match is None, (
            f"{script.name} appears to invoke a mutating verb matching "
            f"{pattern.pattern!r} outside of comments/messages: "
            f"{code.splitlines()[code[:match.start()].count(chr(10))] if match else ''}"
        )


@pytest.mark.parametrize("script", EXECUTABLE_SCRIPTS, ids=lambda p: p.name)
def test_every_live_kubectl_call_passes_explicit_context(script):
    """Every kubectl invocation that queries live cluster state must pass
    --context explicitly rather than relying on the ambient current-context
    (kubectl config / current-context reads are exempt: they're local and
    are how we *detect* mismatches in the first place)."""
    text = script.read_text()
    kubectl_word = re.compile(r"\bkubectl\b")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not kubectl_word.search(stripped):
            continue
        if "kubectl config" in stripped or "current-context" in stripped:
            continue
        if "command -v kubectl" in stripped or "kubectl version" in stripped:
            continue
        # Skip lines where "kubectl" only appears inside a quoted message.
        no_dquotes = re.sub(r'"[^"]*"', '""', stripped)
        no_quotes = re.sub(r"'[^']*'", "''", no_dquotes)
        if not kubectl_word.search(no_quotes):
            continue
        assert "--context" in no_quotes, f"{script.name}: {stripped!r} missing --context"
