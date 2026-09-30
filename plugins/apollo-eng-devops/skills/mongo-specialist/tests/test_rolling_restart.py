"""Tests for rolling_restart.py. All subprocess, input and sleeps are mocked."""

from __future__ import annotations

import json
import re
import subprocess

import pytest

import rolling_restart as rr


def cp(stdout="", rc=0):
    return subprocess.CompletedProcess([], rc, stdout=stdout, stderr="")


def prom(values, cluster="accounts"):
    """values: {n: float}; shape mimics a Prometheus instant result."""
    res = [
        {"metric": {"instance": f"mongos-{cluster}-{n}.internal:9216"}, "value": [0, str(v)]}
        for n, v in values.items()
    ]
    return json.dumps({"data": {"result": res}})


class Env:
    """Scripted fake for rr.run_cmd."""

    def __init__(self, deploy="[]", up=None, uptime=None, active="active\n"):
        self.calls = []
        self.deploy = deploy
        self.up = up if up is not None else {n: 1 for n in range(6)}
        self.uptime = uptime if uptime is not None else {n: 30 for n in range(6)}
        self.active = active

    def __call__(self, cmd, timeout=180):
        self.calls.append(cmd)
        joined = " ".join(cmd)
        if cmd[0] == "gh":
            return cp(self.deploy)
        if cmd[0] == "gcx":
            expr = joined
            if "uptime" in expr:
                return cp(prom(self.uptime))
            return cp(prom(self.up))
        if cmd[0] == "gcloud":
            return cp("sometext\n" + self.active)
        raise AssertionError(joined)

    def restarts(self):
        return [c for c in self.calls if "systemctl restart" in " ".join(c)]


@pytest.fixture
def env(monkeypatch):
    e = Env()
    monkeypatch.setattr(rr, "run_cmd", e)
    sleeps = []
    monkeypatch.setattr(rr, "_sleep", lambda s: sleeps.append(s))
    e.sleeps = sleeps
    return e


def typed(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_a: next(it))


# validation
@pytest.mark.parametrize("argv", [
    ["--cluster", "nope", "--hosts", "1"],
    ["--cluster", "accounts", "--hosts", "x"],
    ["--cluster", "accounts", "--hosts", "6"],
    ["--cluster", "accounts", "--hosts", "-1"],
    ["--cluster", "accounts", "--hosts", "1,1"],
    ["--cluster", "accounts", "--hosts", "0,1,2,3,4,5"],
    ["--cluster", "accounts", "--hosts", "1", "--role", "change-stream"],
    ["--cluster", "accounts", "--hosts", "1", "--role", "mongod"],
    ["--cluster", "accounts", "--hosts", "1", "--soak-min", "-1"],
    ["--cluster", "accounts;rm", "--hosts", "1"],
])
def test_invalid_args_refused(argv, env, capsys):
    assert rr.main(argv) == 2
    assert env.calls == []


def test_no_parallel_option():
    with pytest.raises(SystemExit):
        rr.main(["--cluster", "accounts", "--hosts", "1", "--parallel", "2"])


def test_subset_of_group_allowed(env):
    assert rr.main(["--cluster", "accounts", "--hosts", "3,4,5"]) == 0


# dry run
def test_dry_run_runs_nothing_and_prints_commands(env, capsys):
    assert rr.main(["--cluster", "accounts", "--hosts", "3,4"]) == 0
    assert env.calls == []
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "gh run list --repo apolloio/leadgenie --workflow production.yml" in out
    assert "gcloud compute ssh mongos-accounts-3 --project indigo-lotus-415 --zone us-central1-c --internal-ip" in out
    assert "sudo systemctl restart mongos-accounts.service" in out
    assert 'up{cluster="accounts",role="mongos"' in out
    assert "mongos-accounts-4" in out
    assert out.count("systemctl restart") == 2


def test_dry_run_mute_reminder(env, capsys):
    rr.main(["--cluster", "accounts", "--hosts", "3", "--mute-id", "abc123"])
    assert "mute-alert expire abc123" in capsys.readouterr().out


# execute
def test_execute_happy_path_single_restart_per_host(env, monkeypatch):
    typed(monkeypatch, "mongos-accounts-3", "mongos-accounts-4")
    assert rr.main(["--cluster", "accounts", "--hosts", "3,4", "--execute"]) == 0
    assert len(env.restarts()) == 2
    assert any(s == 60 for s in env.sleeps)
    assert sum(1 for s in env.sleeps if s == 60) == 20  # 10 min soak x 2 hosts


def test_refuses_when_deploy_in_progress(env, monkeypatch):
    env.deploy = json.dumps([{"status": "in_progress", "conclusion": None}])
    typed(monkeypatch, "mongos-accounts-3")
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1
    assert env.restarts() == []


def test_refuses_when_deploy_queued(env, monkeypatch):
    env.deploy = json.dumps([{"status": "queued", "conclusion": None}])
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1
    assert env.restarts() == []


def test_refuses_on_unparseable_deploy_output(env, monkeypatch):
    env.deploy = "garbage"
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1
    assert env.restarts() == []


def test_refuses_when_peer_down(env, monkeypatch):
    env.up[0] = 0
    typed(monkeypatch, "mongos-accounts-3")
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1
    assert env.restarts() == []


def test_refuses_when_peer_series_missing(env, monkeypatch):
    del env.up[1]
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1
    assert env.restarts() == []


def test_skip_up_check_warns_and_proceeds(env, monkeypatch, capsys):
    env.up[0] = 0
    typed(monkeypatch, "mongos-accounts-3")
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute", "--skip-up-check"]) == 0
    assert "WARNING" in capsys.readouterr().out
    assert len(env.restarts()) == 1


def test_wrong_typed_hostname_aborts(env, monkeypatch):
    typed(monkeypatch, "mongos-accounts-4")
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1
    assert env.restarts() == []


def test_metrics_tooling_missing_refuses(monkeypatch):
    def boom(cmd, timeout=180):
        if cmd[0] == "gcx":
            raise FileNotFoundError("gcx")
        return cp("[]")

    monkeypatch.setattr(rr, "run_cmd", boom)
    monkeypatch.setattr(rr, "_sleep", lambda s: None)
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1


def test_stops_when_not_active(env, monkeypatch, capsys):
    env.active = "failed\n"
    typed(monkeypatch, "mongos-accounts-3", "mongos-accounts-4")
    assert rr.main(["--cluster", "accounts", "--hosts", "3,4", "--execute"]) == 1
    assert len(env.restarts()) == 1
    assert "mongos-accounts-4" not in " ".join(" ".join(c) for c in env.calls)
    assert "journalctl -u mongos-accounts.service" in capsys.readouterr().out


def test_stops_when_up_never_recovers(env, monkeypatch, capsys):
    env.up[3] = 0
    typed(monkeypatch, "mongos-accounts-3", "mongos-accounts-4")
    # skip peer check so preflight passes; verification must then fail
    assert rr.main(["--cluster", "accounts", "--hosts", "3,4", "--execute", "--skip-up-check"]) == 1
    assert len(env.restarts()) == 1
    assert sum(env.sleeps) <= 300 + 60
    assert "journalctl" in capsys.readouterr().out


def test_stops_when_uptime_not_reset(env, monkeypatch):
    env.uptime[3] = 100000
    typed(monkeypatch, "mongos-accounts-3")
    assert rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"]) == 1


def test_no_secret_looking_output(env, monkeypatch, capsys):
    typed(monkeypatch, "mongos-accounts-3")
    rr.main(["--cluster", "accounts", "--hosts", "3"])
    rr.main(["--cluster", "accounts", "--hosts", "3", "--execute"])
    out = capsys.readouterr().out
    assert not re.search(r"(?i)passw|secret|token|MONGO_PASS|vault|-p \"", out)
