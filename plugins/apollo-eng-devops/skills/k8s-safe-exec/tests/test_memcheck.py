"""
test_memcheck.py — hermetic tests for the k8s-safe-exec skill's memcheck.sh.

memcheck.sh is a bash script, not a Python module, so it is tested by
invoking it as a subprocess and asserting on exit codes / stdout / stderr —
mirroring test_k8s_safe_exec.py's conventions for the sibling scripts. Every
test here must run WITHOUT a live cluster: all argument, target-selection,
and size/estimate parsing happens before any kubectl call, and the
K8S_SAFE_EXEC_SKIP_CLUSTER=1 escape hatch (documented in the script's header
comment) short-circuits right after that parsing, before any live-cluster
kubectl call, so the parsing logic can be exercised hermetically.

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
MEMCHECK = SCRIPTS_DIR / "memcheck.sh"

if not MEMCHECK.exists():
    pytest.skip("memcheck.sh has not landed yet", allow_module_level=True)

if shutil.which("bash") is None:
    pytest.skip("bash is not available on this machine", allow_module_level=True)

# A clean environment for every subprocess call: never inherit a stray
# K8S_SAFE_EXEC_SKIP_CLUSTER from the host shell into "should hard-fail on
# args" tests, and never let host kubeconfig/context state leak into a test
# that expects a specific pure-validation outcome.
BASE_ENV = {k: v for k, v in os.environ.items() if k != "K8S_SAFE_EXEC_SKIP_CLUSTER"}

# A representative valid invocation, minus whatever's being varied by a test.
BASE_ARGS = ["prod", "-n", "leadgenie", "--pod", "some-pod"]


def run(args, env_overrides=None, timeout=10):
    env = dict(BASE_ENV)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(MEMCHECK), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_skip_cluster(args, timeout=10):
    return run(args, env_overrides={"K8S_SAFE_EXEC_SKIP_CLUSTER": "1"}, timeout=timeout)


# ---------------------------------------------------------------------------
# Env arg: missing / invalid -> exit 2
# ---------------------------------------------------------------------------


def test_missing_env_arg_exits_2():
    result = run([])
    assert result.returncode == 2
    assert "stage" in result.stderr and "prod" in result.stderr


@pytest.mark.parametrize("bad_env", ["production", "PROD", "dev", "staging", ""])
def test_invalid_env_arg_exits_2(bad_env):
    result = run([bad_env, "-n", "leadgenie", "--pod", "some-pod"])
    assert result.returncode == 2, (
        f"{bad_env!r} -> exit {result.returncode}, stderr={result.stderr!r}"
    )
    assert "stage" in result.stderr
    assert "prod" in result.stderr


def test_usage_mentions_stage_and_prod():
    result = run(["-h"])
    assert result.returncode == 0
    assert "stage" in result.stdout
    assert "prod" in result.stdout


# ---------------------------------------------------------------------------
# Namespace required
# ---------------------------------------------------------------------------


def test_missing_namespace_exits_2():
    result = run(["prod", "--pod", "some-pod"])
    assert result.returncode == 2
    assert "-n" in result.stderr or "namespace" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Exactly one of --deploy / --pod / --selector
# ---------------------------------------------------------------------------


def test_no_target_flag_exits_2():
    result = run(["prod", "-n", "leadgenie"])
    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "--deploy" in combined and "--pod" in combined and "--selector" in combined


@pytest.mark.parametrize(
    "extra_flags",
    [
        ["--pod", "foo", "--deploy", "bar"],
        ["--pod", "foo", "--selector", "app=bar"],
        ["--deploy", "bar", "--selector", "app=bar"],
        ["--pod", "foo", "--deploy", "bar", "--selector", "app=bar"],
    ],
)
def test_multiple_target_flags_exits_2(extra_flags):
    result = run(["prod", "-n", "leadgenie", *extra_flags])
    assert result.returncode == 2


@pytest.mark.parametrize(
    "target_flags",
    [["--pod", "some-pod"], ["--deploy", "some-deploy"], ["--selector", "app=foo"]],
)
def test_exactly_one_target_flag_passes_arg_validation(target_flags):
    # Hermetic: SKIP_CLUSTER short-circuits right after arg validation, so a
    # valid single target flag should reach the PASS line and exit 0, not 2.
    result = run_skip_cluster(["prod", "-n", "leadgenie", *target_flags])
    assert result.returncode == 0, result.stderr
    assert "PASS: arguments valid" in result.stdout


# ---------------------------------------------------------------------------
# --estimate: unparseable values, and every named class accepted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_estimate", ["banana", "12Xi", "Gi5", "-5Mi", "5Zi"])
def test_unparseable_estimate_exits_2(bad_estimate):
    result = run(["prod", "-n", "leadgenie", "--pod", "some-pod", "--estimate", bad_estimate])
    assert result.returncode == 2
    assert bad_estimate in result.stderr


@pytest.mark.parametrize(
    "estimate_class", ["trivial", "light", "rails-boot", "rails-query", "heavy"]
)
def test_named_estimate_class_accepted(estimate_class):
    result = run_skip_cluster(
        ["prod", "-n", "leadgenie", "--pod", "some-pod", "--estimate", estimate_class]
    )
    assert result.returncode == 0, result.stderr
    assert f"estimate={estimate_class}" in result.stdout


# ---------------------------------------------------------------------------
# Size parsing correctness (via K8S_SAFE_EXEC_SKIP_CLUSTER=1's echoed,
# normalized MiB value in the "PASS: arguments valid (...)" summary line)
# ---------------------------------------------------------------------------


def _normalized_estimate_mib(estimate_value: str) -> str:
    result = run_skip_cluster(
        ["prod", "-n", "leadgenie", "--pod", "some-pod", "--estimate", estimate_value]
    )
    assert result.returncode == 0, result.stderr
    match = re.search(r"estimate=\S+ \((\d+Mi)\)", result.stdout)
    assert match, f"could not find normalized estimate in: {result.stdout!r}"
    return match.group(1)


def test_1gi_equals_1024mi():
    assert _normalized_estimate_mib("1Gi") == "1024Mi"
    assert _normalized_estimate_mib("1024Mi") == "1024Mi"
    assert _normalized_estimate_mib("1Gi") == _normalized_estimate_mib("1024Mi")


def test_2048mi_equals_2gi():
    assert _normalized_estimate_mib("2048Mi") == "2048Mi"
    assert _normalized_estimate_mib("2Gi") == "2048Mi"
    assert _normalized_estimate_mib("2048Mi") == _normalized_estimate_mib("2Gi")


def test_bare_bytes_handled():
    # 2 MiB expressed as bare bytes.
    assert _normalized_estimate_mib("2097152") == "2Mi"


def test_decimal_size_handled():
    assert _normalized_estimate_mib("1.5Gi") == "1536Mi"


# ---------------------------------------------------------------------------
# --safety-factor / --top validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_factor", ["banana", "-1", ""])
def test_bad_safety_factor_exits_2(bad_factor):
    args = ["prod", "-n", "leadgenie", "--pod", "some-pod", "--safety-factor", bad_factor]
    result = run(args)
    assert result.returncode == 2


@pytest.mark.parametrize("bad_top", ["0", "-1", "banana", ""])
def test_bad_top_exits_2(bad_top):
    args = ["prod", "-n", "leadgenie", "--pod", "some-pod", "--top", bad_top]
    result = run(args)
    assert result.returncode == 2


def test_valid_safety_factor_and_top_pass_arg_validation():
    result = run_skip_cluster(
        ["prod", "-n", "leadgenie", "--pod", "some-pod", "--safety-factor", "2", "--top", "3"]
    )
    assert result.returncode == 0, result.stderr
    assert "safety_factor=2 (x100=200)" in result.stdout
    assert "top=3" in result.stdout


# ---------------------------------------------------------------------------
# Syntax / executability
# ---------------------------------------------------------------------------


def test_bash_syntax_check():
    result = subprocess.run(
        ["bash", "-n", str(MEMCHECK)], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr


def test_script_is_executable():
    mode = MEMCHECK.stat().st_mode
    assert mode & stat.S_IXUSR, "memcheck.sh is not executable (chmod +x)"


# ---------------------------------------------------------------------------
# Regression guard: no mutating kubectl verbs anywhere in the source.
#
# Full comment lines and quoted string literals (echo/printf/error messages
# that legitimately tell the operator what to do, or describe the ephemeral
# pod workflow this script recommends people fall back to) are stripped
# before matching, so this guards against an actual invocation being added
# later without flagging the script's own read-only documentation.
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


def test_no_mutating_kubectl_verbs_in_executable_code():
    code = _strip_comments_and_string_literals(MEMCHECK.read_text())
    for pattern in _FORBIDDEN_PATTERNS:
        match = pattern.search(code)
        assert match is None, (
            f"memcheck.sh appears to invoke a mutating verb matching "
            f"{pattern.pattern!r} outside of comments/messages: "
            f"{code.splitlines()[code[:match.start()].count(chr(10))] if match else ''}"
        )


def test_every_live_kubectl_call_passes_explicit_context():
    """Every kubectl invocation that queries live cluster state must pass
    --context explicitly rather than relying on the ambient current-context.
    memcheck.sh builds a KCTL=(kubectl --context ... -n ... --request-timeout
    ...) array for most calls, plus two direct `kubectl --context ...` calls
    for node reads; both forms satisfy this guard."""
    text = MEMCHECK.read_text()
    kubectl_word = re.compile(r"\bkubectl\b")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not kubectl_word.search(stripped):
            continue
        if "command -v kubectl" in stripped:
            continue
        # Skip lines where "kubectl" only appears inside a quoted message.
        no_dquotes = re.sub(r'"[^"]*"', '""', stripped)
        no_quotes = re.sub(r"'[^']*'", "''", no_dquotes)
        if not kubectl_word.search(no_quotes):
            continue
        # The KCTL=(...) array definition itself carries --context; any line
        # that *invokes* kubectl either uses "${KCTL[@]}" (which expands to
        # include --context) or is a direct `kubectl --context ...` call.
        if '"${KCTL[@]}"' in stripped or "--context" in no_quotes:
            continue
        pytest.fail(f"memcheck.sh: {stripped!r} missing --context (direct or via KCTL array)")


def test_json_mode_keeps_stdout_pure():
    """--json stdout must be parseable JSON, so progress output has to go to stderr.

    Regression guard: `pass()` and `section()` once wrote to stdout unconditionally,
    which broke `jq` parsing for the skill.
    """
    src = MEMCHECK.read_text()
    for fn in ("pass()", "section()"):
        start = src.index(fn)
        body = src[start:start + 400]
        assert "JSON_MODE" in body, f"{fn} must respect JSON_MODE so --json stdout stays pure"
        assert ">&2" in body, f"{fn} must be able to redirect to stderr in --json mode"
    # A bare `echo` immediately before a section header would also pollute --json stdout.
    assert not re.search(r"^[ \t]*echo\n(?=[ \t]*section \")", src, re.M), \
        "bare echo before section() pollutes --json stdout"
