from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "gce_events.sh"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="gce_events.sh not present")


LOG_AND_AUTH = (
    'echo "$@" >> "$STUB_LOG"\n'
    'if [ "$1" = "auth" ]; then echo user@example.com; fi\n'
    "exit 0"
)


def make_stub(tmp_path, body=LOG_AND_AUTH):
    stub = tmp_path / "gcloud"
    stub.write_text(f"#!/bin/sh\n{body}\n")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return tmp_path


def run(tmp_path, *args, path_prefix=None):
    env = dict(os.environ)
    env["PATH"] = f"{path_prefix or tmp_path}:/usr/bin:/bin"
    env["STUB_LOG"] = str(tmp_path / "calls.log")
    return subprocess.run(
        ["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env
    )


def calls(tmp_path):
    p = tmp_path / "calls.log"
    return p.read_text().splitlines() if p.exists() else []


def test_only_list_and_read_verbs_called(tmp_path):
    make_stub(tmp_path)
    p = run(tmp_path, "--cluster", "main", "--window", "1h")
    assert p.returncode == 0, p.stderr
    log = calls(tmp_path)
    assert any(c.startswith("compute operations list") for c in log)
    assert any(c.startswith("logging read") for c in log)
    for c in log:
        assert c.split()[0] in ("compute", "logging", "auth", "config")
        assert " delete" not in c and " ssh" not in c and "serial-port" not in c
    ops = next(c for c in log if c.startswith("compute operations"))
    assert "--project indigo-lotus-415" in ops
    assert "insertTime>-PT1H" in ops
    assert "mongos?-main-" in ops


def test_window_converted_to_iso_duration(tmp_path):
    make_stub(tmp_path)
    run(tmp_path, "--cluster", "main", "--window", "24h")
    assert any("insertTime>-PT24H" in c for c in calls(tmp_path))


def test_bad_cluster_and_window_rejected(tmp_path):
    make_stub(tmp_path)
    assert run(tmp_path, "--cluster", 'x"; rm -rf /', "--window", "1h").returncode == 2
    assert run(tmp_path, "--cluster", "main", "--window", "9d").returncode == 2
    assert calls(tmp_path) == []


PROBE = "--probe-gc"  # runs gc() directly with the given gcloud args


@pytest.mark.parametrize(
    "args",
    [
        ("compute", "ssh", "vm"),
        ("compute", "instances", "delete", "vm"),
        ("compute", "instances", "reset", "vm"),
        ("compute", "instances", "stop", "vm"),
        ("compute", "instances", "start", "vm"),
        ("compute", "instances", "get-serial-port-output", "vm"),
        ("compute", "operations", "describe", "op"),
        ("compute", "instances", "list", "--command", "rm -rf /"),  # list verb smuggled in
        ("compute", "operations", "list", "--command=reboot"),
        ("compute", "ssh", "list"),
        ("logging", "read", "x", "--command", "y"),
        ("logging", "write", "log", "msg"),
        ("auth", "login"),
        ("auth", "list", "--command", "x"),
        ("list", "compute", "instances"),  # verb not in command position
    ],
)
def test_gc_rejects_anything_outside_prefix_allowlist(tmp_path, args):
    make_stub(tmp_path)
    p = run(tmp_path, PROBE, *args)
    assert p.returncode == 3, (p.returncode, p.stderr)
    assert "refused" in p.stderr
    assert calls(tmp_path) == []


@pytest.mark.parametrize(
    "args",
    [
        ("compute", "operations", "list", "--project", "p"),
        ("logging", "read", "resource.type=gce_instance", "--project", "p"),
        ("auth", "list", "--filter=status:ACTIVE"),
    ],
)
def test_gc_allows_allowlisted_prefixes(tmp_path, args):
    make_stub(tmp_path)
    p = run(tmp_path, PROBE, *args)
    assert p.returncode == 0, p.stderr
    assert calls(tmp_path) == [" ".join(args)]


def test_missing_gcloud_skips_without_failing(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    p = run(tmp_path, "--cluster", "main", "--window", "1h", path_prefix=empty)
    assert p.returncode == 0
    assert "skip" in (p.stdout + p.stderr).lower()


def test_unauthenticated_gcloud_skips_without_failing(tmp_path):
    # `gcloud auth list` prints no active account
    make_stub(tmp_path, 'echo "$@" >> "$STUB_LOG"\nexit 0')
    p = run(tmp_path, "--cluster", "main", "--window", "1h")
    assert p.returncode == 0
    assert "skip" in (p.stdout + p.stderr).lower()
    assert not any(c.startswith(("compute", "logging")) for c in calls(tmp_path))


def test_operations_sorted_newest_first_and_limited(tmp_path):
    make_stub(tmp_path)
    run(tmp_path, "--cluster", "main", "--window", "1h")
    ops = next(c for c in calls(tmp_path) if c.startswith("compute operations"))
    assert "--sort-by=~insertTime" in ops
    assert "--limit 50" in ops


def test_timestamps_are_normalised_to_utc(tmp_path):
    make_stub(tmp_path)
    run(tmp_path, "--cluster", "main", "--window", "1h")
    for c in calls(tmp_path):
        if c.startswith(("compute operations", "logging read")):
            assert "tz=UTC" in c, c
