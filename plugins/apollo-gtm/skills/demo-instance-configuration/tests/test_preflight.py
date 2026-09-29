"""Tests for scripts/revops-preflight.sh, run against a fake curl on PATH.

The fake responses reproduce what each surface actually returned when probed on
2026-09-24: Apollo itself, Claude.ai Chat's egress proxy, and Cowork's egress proxy.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "revops-preflight.sh"

if shutil.which("bash") is None:
    pytest.skip("bash is required to run the preflight script", allow_module_level=True)

# Each scenario: (exit code, http_code, content_type, header lines written to -D).
SCENARIOS = {
    "apollo_401": (0, "401", "application/json; charset=utf-8", ["HTTP/2 401", "server: cloudflare"]),
    "apollo_422": (0, "422", "application/json; charset=utf-8", ["HTTP/2 422", "server: cloudflare"]),
    "chat_proxy": (0, "403", "text/plain", ["HTTP/2 403", "x-deny-reason: host_not_allowed"]),
    "cowork_proxy": (56, "000", "", ["HTTP/1.1 403 Forbidden", "X-Proxy-Error: blocked-by-allowlist"]),
    "no_network": (6, "000", "", []),
    "html_200": (0, "200", "text/html", ["HTTP/2 200"]),
}

FAKE_CURL = r"""#!/usr/bin/env bash
hdr=""; url=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -D) hdr="$2"; shift 2 ;;
    -o|-m|-w) shift 2 ;;
    -*) shift ;;
    *) url="$1"; shift ;;
  esac
done
case "$url" in
  *app.apollo.io*) scenario="$FAKE_APP" ;;
  *) scenario="$FAKE_API" ;;
esac
dir="$FAKE_DIR/$scenario"
[ -n "$hdr" ] && cp "$dir/headers" "$hdr"
printf '%s' "$(cat "$dir/w")"
exit "$(cat "$dir/rc")"
"""


@pytest.fixture
def fake_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    curl = bindir / "curl"
    curl.write_text(FAKE_CURL)
    curl.chmod(0o755)
    for name, (rc, code, ctype, headers) in SCENARIOS.items():
        d = tmp_path / "scenarios" / name
        d.mkdir(parents=True)
        (d / "rc").write_text(str(rc))
        (d / "w").write_text(f"{code} {ctype}")
        (d / "headers").write_text("".join(f"{h}\r\n" for h in headers))
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    env["FAKE_DIR"] = str(tmp_path / "scenarios")
    return env


def run(env: dict[str, str], app: str, api: str, claudecode: str | None = "1") -> subprocess.CompletedProcess:
    env = dict(env, FAKE_APP=app, FAKE_API=api)
    if claudecode is not None:
        env["CLAUDECODE"] = claudecode
    return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True, check=False)


def test_passes_when_both_hosts_answer_as_apollo(fake_env):
    result = run(fake_env, "apollo_401", "apollo_422")
    assert (result.returncode, result.stdout.strip()) == (0, "PREFLIGHT_OK")


@pytest.mark.parametrize("claudecode", [None, "", "0"])
def test_stops_outside_claude_code_before_any_network_call(fake_env, claudecode):
    # A scenario name with no fixture directory would make the fake curl fail loudly,
    # so a clean NOT_CLAUDE_CODE proves curl was never reached.
    result = run(fake_env, "unused", "unused", claudecode=claudecode)
    assert (result.returncode, result.stdout.strip()) == (10, "PREFLIGHT_NOT_CLAUDE_CODE")


@pytest.mark.parametrize(
    ("app", "reason"),
    [
        ("chat_proxy", "app.apollo.io:proxy-blocked"),
        ("cowork_proxy", "app.apollo.io:proxy-blocked"),
        ("no_network", "app.apollo.io:curl-exit-6"),
        ("html_200", "app.apollo.io:non-apollo-response-200"),
    ],
)
def test_a_proxy_or_non_apollo_answer_is_not_a_pass(fake_env, app, reason):
    result = run(fake_env, app, "apollo_422")
    assert result.returncode == 20
    assert result.stdout.strip() == f"PREFLIGHT_APOLLO_UNREACHABLE {reason}"


def test_reports_every_failing_host(fake_env):
    result = run(fake_env, "chat_proxy", "cowork_proxy")
    assert result.returncode == 20
    assert result.stdout.strip() == (
        "PREFLIGHT_APOLLO_UNREACHABLE app.apollo.io:proxy-blocked api.apollo.io:proxy-blocked"
    )
