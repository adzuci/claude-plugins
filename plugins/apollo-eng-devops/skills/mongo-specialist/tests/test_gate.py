"""Tests for the deploy-aware gate in rolling_restart.py. No network; gh/gcx are faked."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone

import pytest

import rolling_restart as rr

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def iso(minutes_ago):
    return (NOW - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def cp(stdout="", rc=0):
    return subprocess.CompletedProcess([], rc, stdout=stdout, stderr="")


def history_runs(lead=60, deploy=11):
    """Three successful runs: deploy stage starts `lead` min after creation, lasts `deploy`."""
    runs, jobs = [], {}
    for i, age in enumerate((300, 600, 900), start=1):
        runs.append({"databaseId": i, "status": "completed", "conclusion": "success",
                     "createdAt": iso(age), "displayTitle": "x"})
        jobs[i] = [{"name": "deploy / sidekiq-workers", "status": "completed",
                    "startedAt": iso(age - lead), "completedAt": iso(age - lead - deploy)}]
    return runs, jobs


def pending(run_id, age, jobs=()):
    return {"databaseId": run_id, "status": "pending" if not jobs else "in_progress",
            "conclusion": None, "createdAt": iso(age), "displayTitle": "p"}, list(jobs)


class Fake:
    def __init__(self, extra=(), lead=60, conns=None, gh_rc=0, gcx_rc=0):
        runs, self.jobs = history_runs(lead)
        self.runs = []
        for run, jobs in extra:
            self.runs.append(run)
            self.jobs[run["databaseId"]] = jobs
        self.runs += runs
        self.conns = conns or {0: 14517, 1: 14517, 2: 14517, 3: 9560, 4: 9560, 5: 9560}
        self.gh_rc, self.gcx_rc = gh_rc, gcx_rc

    def __call__(self, cmd, timeout=180):
        if cmd[0] == "gh":
            if self.gh_rc:
                return cp("", self.gh_rc)
            if cmd[2] == "view":
                return cp(json.dumps({"jobs": self.jobs[int(cmd[3])]}))
            return cp(json.dumps(self.runs))
        assert cmd[0] == "gcx"
        if self.gcx_rc:
            return cp("", self.gcx_rc)
        res = [{"metric": {"instance": f"mongos-accounts-{n}.internal:9216"}, "value": [0, str(v)]}
               for n, v in self.conns.items()]
        return cp(json.dumps({"data": {"result": res}}))


@pytest.fixture
def use(monkeypatch):
    def _use(fake):
        monkeypatch.setattr(rr, "run_cmd", fake)
        monkeypatch.setattr(rr, "_now", lambda: NOW)
        return fake
    return _use


def gate(n=3, soak=10, margin=10, max_conns=None):
    return rr.gate("accounts", n, soak, margin, max_conns)


def active_job(started_ago, name="sidekiq-workers"):
    return {"name": f"deploy / {name}", "status": "in_progress", "startedAt": iso(started_ago)}


def test_active_deploy_job_waits_with_eta(use):
    use(Fake([pending(10, 70, [active_job(4)])]))
    d, reasons, retry = gate()
    assert d == "WAIT"
    assert retry == NOW + timedelta(minutes=7)  # started 4 min ago, typical 11
    assert any("ETA 12:07" in r and "deploy / sidekiq-workers" in r for r in reasons)


def test_pending_run_with_no_jobs_and_55_min_left_goes(use):
    use(Fake([pending(10, 5)]))  # lead 60, elapsed 5 -> 55 left; need 3+10+15+10=38
    d, reasons, _ = gate()
    assert d == "GO"
    assert any("55 min" in r and "38 min" in r for r in reasons)


def test_pending_run_with_12_min_left_waits(use):
    use(Fake([pending(10, 48)]))
    d, reasons, retry = gate()
    assert d == "WAIT"
    assert retry >= NOW + timedelta(minutes=12)
    assert any("12 min" in r for r in reasons)


def test_completed_runs_only_goes(use):
    use(Fake())
    assert gate()[0] == "GO"


def test_connections_over_ceiling_waits(use):
    conns = {0: 14517, 1: 14517, 2: 14517, 3: 11300, 4: 11618, 5: 11641}
    use(Fake(conns=conns))
    d, reasons, retry = gate()
    text = "\n".join(reasons)
    assert d == "WAIT" and retry is not None
    assert "17,291" in text and "16,000" in text and "worker group" in text


def test_web_job_active_does_not_block_worker_router(use):
    use(Fake([pending(10, 70, [active_job(4, "rails-api")])]))
    d, reasons, _ = gate(n=3)
    assert d == "GO"
    assert any("ignored" in r and "deploy / rails-api" in r and "web" in r for r in reasons)


def test_worker_job_active_blocks_worker_router(use):
    use(Fake([pending(10, 70, [active_job(4)])]))
    assert gate(n=3)[0] == "WAIT"


@pytest.mark.parametrize("job", ["rails-api", "events-api", "tracking-api", "mcp-api"])
def test_web_job_active_blocks_web_router(use, job):
    use(Fake([pending(10, 70, [active_job(4, job)])], conns={n: 5000 for n in range(6)}))
    assert gate(n=1)[0] == "WAIT"


def test_unknown_job_blocks_either_group(use):
    use(Fake([pending(10, 70, [active_job(4, "mystery")])], conns={n: 5000 for n in range(6)}))
    assert gate(n=3)[0] == "WAIT" and gate(n=1)[0] == "WAIT"


def test_web_router_under_ceiling_goes(use):
    use(Fake(conns={0: 14500, 1: 14500, 2: 14500, 3: 9800, 4: 9800, 5: 9800}))
    d, reasons, _ = gate(n=1)  # peers 14.5k + 7.25k = 21.75k < 22k
    assert d == "GO" and any("web group" in r and "22,000" in r for r in reasons)


def test_connections_after_rollout_go(use):
    use(Fake(conns={0: 14517, 1: 14517, 2: 14517, 3: 9560, 4: 9560, 5: 9560}))
    assert gate()[0] == "GO"


def test_max_conns_flag_overrides_ceiling(use):
    use(Fake(conns={0: 1, 1: 1, 2: 1, 3: 9000, 4: 9000, 5: 9000}))
    d, reasons, _ = gate(max_conns=10000)
    assert d == "WAIT" and any("--max-conns" in r for r in reasons)


def test_web_group_mates_are_0_to_2(use):
    use(Fake(conns={0: 100, 1: 100, 2: 100, 3: 99999, 4: 99999, 5: 99999}))
    assert gate(n=0)[0] == "GO"  # sidekiq-side load is irrelevant to a web router


def test_gh_failure_stops(use):
    use(Fake(gh_rc=1))
    assert gate()[0] == "STOP"


def test_gh_garbage_stops(use, monkeypatch):
    use(Fake())
    monkeypatch.setattr(rr, "run_cmd", lambda cmd, timeout=180: cp("garbage"))
    assert gate()[0] == "STOP"


def test_gcx_failure_stops(use):
    use(Fake(gcx_rc=1))
    assert gate()[0] == "STOP"


def test_missing_router_series_stops(use):
    use(Fake(conns={0: 1, 1: 1, 2: 1, 3: 1, 4: 1}))
    assert gate()[0] == "STOP"


def test_format_prints_one_gate_line_and_retry():
    out = rr.format_gate("WAIT", ["a", "b"], NOW)
    assert out.splitlines()[0] == "GATE: WAIT"
    assert "- a" in out and "earliest retry 12:00 UTC" in out


def test_no_bypass_flag():
    with pytest.raises(SystemExit):
        rr.main(["--cluster", "accounts", "--hosts", "3", "--ignore-deploy-gate"])
