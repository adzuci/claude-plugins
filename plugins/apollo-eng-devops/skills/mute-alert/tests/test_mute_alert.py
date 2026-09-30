from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

mod = pytest.importorskip("mute_alert")

PATH_S = "/api/alertmanager/grafana/api/v2/silences"
ALERT = "alertname=MongoDB Host has restarted"


class FakeGcx:
    """Stateful stand-in for the gcx CLI (subprocess.run replacement)."""

    def __init__(self):
        self.calls = []
        self.silences = {}
        self.check_rc = 0
        self.api_rc, self.api_err = 0, ""
        self.break_delete = False
        self.timeout = False

    def api_calls(self):
        return [c for c in self.calls if c[0][:2] == ["gcx", "api"]]

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        ok = lambda out="": mock.Mock(returncode=0, stdout=out, stderr="")  # noqa: E731
        if argv[:2] == ["gcx", "version"]:
            return ok('{"version":"v1.0.0"}')
        if argv[:3] == ["gcx", "config", "check"]:
            return mock.Mock(returncode=self.check_rc, stdout="server: SECRET-CONFIG-BODY", stderr="")
        if argv[:3] == ["gcx", "config", "current-context"]:
            return ok("apollo-prod\n")
        if self.timeout:
            raise mod.subprocess.TimeoutExpired(argv, 30)
        if self.api_rc:
            return mock.Mock(returncode=self.api_rc, stdout="", stderr=self.api_err)
        method = argv[argv.index("-X") + 1] if "-X" in argv else "GET"
        if method == "POST":
            sid = "sil-%d" % (len(self.silences) + 1)
            self.silences[sid] = dict(json.loads(kw["input"]), id=sid, status={"state": "active"})
            return ok(json.dumps({"silenceID": sid}))
        if method == "DELETE":
            sid = argv[2].rsplit("/", 1)[1]
            if sid in self.silences and not self.break_delete:
                self.silences[sid]["status"]["state"] = "expired"
            return ok()
        return ok(json.dumps(list(self.silences.values())))


@pytest.fixture(autouse=True)
def gcx(monkeypatch):
    monkeypatch.setenv("MUTE_ALERT_CREATED_BY", "adam@example.com")
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/opt/homebrew/bin/gcx")
    fake = FakeGcx()
    monkeypatch.setattr(mod.subprocess, "run", fake)
    return fake


def create_args(*extra):
    return ["create", "--matcher", ALERT, "--matcher", "cluster=accounts",
            "--comment", "planned router restarts", *extra]


# ---- duration ----
@pytest.mark.parametrize("s,mins", [("30m", 30), ("1h", 60), ("90m", 90), ("4h", 240)])
def test_duration_ok(s, mins):
    assert mod.parse_duration(s) == timedelta(minutes=mins)


@pytest.mark.parametrize("s", ["", "abc", "0m", "-5m", "1d", "1.5h", "90"])
def test_duration_invalid(s):
    with pytest.raises(mod.InputError):
        mod.parse_duration(s)


def test_duration_over_max_and_allow_long():
    with pytest.raises(mod.InputError):
        mod.parse_duration("241m")
    with pytest.raises(mod.InputError):
        mod.parse_duration("5h")
    assert mod.parse_duration("12h", allow_long=True) == timedelta(hours=12)
    with pytest.raises(mod.InputError):
        mod.parse_duration("13h", allow_long=True)


# ---- matchers ----
def test_matcher_parsing():
    assert mod.parse_matcher("cluster=accounts") == {
        "name": "cluster", "value": "accounts", "isRegex": False, "isEqual": True}
    assert mod.parse_matcher(ALERT)["value"] == "MongoDB Host has restarted"
    assert mod.parse_matcher("instance=10.0.0.1:9100")["value"] == "10.0.0.1:9100"


@pytest.mark.parametrize("bad", ["novalue", "=x", "a=", "a=~b", "a!=b", "a!~b", "1bad=x",
                                 "cluster=acc*", "cluster=.*", "cluster=a|b", "cluster=^a$"])
def test_matcher_rejects_regex_wildcard_and_malformed(bad):
    with pytest.raises(mod.InputError):
        mod.parse_matcher(bad)


def test_alertname_required_and_exact():
    with pytest.raises(mod.InputError, match="alertname"):
        mod.validate_matchers([mod.parse_matcher("cluster=accounts")], allow_broad=False)


def test_scoping_label_required_unless_allow_broad():
    only_alert = [mod.parse_matcher(ALERT)]
    with pytest.raises(mod.InputError, match="cluster"):
        mod.validate_matchers(only_alert, allow_broad=False)
    mod.validate_matchers(only_alert, allow_broad=True)
    mod.validate_matchers(only_alert + [mod.parse_matcher("instance=h1")], allow_broad=False)


def test_comment_required():
    assert mod.main(["create", "--matcher", ALERT, "--matcher", "cluster=a", "--yes"]) == 2


def test_comment_required_blank():
    assert mod.main(["create", "--matcher", ALERT, "--matcher", "cluster=a",
                     "--comment", "  ", "--yes"]) == 2


# ---- payload ----
def test_payload_shape():
    now = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
    p = mod.build_payload([mod.parse_matcher(ALERT)], now, timedelta(minutes=90),
                          "adam@example.com", "planned", "INFRA-2234")
    assert p["startsAt"] == "2026-09-29T12:00:00Z"
    assert p["endsAt"] == "2026-09-29T13:30:00Z"
    assert p["startsAt"] <= p["endsAt"]
    assert p["createdBy"] == "adam@example.com"
    assert "planned" in p["comment"] and "INFRA-2234" in p["comment"]
    m = p["matchers"][0]
    assert m["isRegex"] is False and m["isEqual"] is True


# ---- CLI: validation and dry-run make no gcx call ----
@pytest.mark.parametrize("extra", [["--duration", "5h"], ["--duration", "zzz"]])
def test_bad_input_no_call(extra, gcx):
    assert mod.main(create_args("--yes", *extra)) == 2
    assert gcx.calls == []


def test_missing_scope_no_call(gcx):
    assert mod.main(["create", "--matcher", ALERT, "--comment", "c", "--yes"]) == 2
    assert gcx.calls == []


def test_dry_run_makes_no_call(gcx, capsys):
    assert mod.main(create_args("--dry-run")) == 0
    assert gcx.calls == []
    out = json.loads(capsys.readouterr().out)
    assert out["dry_run"] is True and out["matchers"][0]["name"] == "alertname"


def test_create_requires_yes_when_not_interactive(gcx):
    assert mod.main(create_args()) == 2
    assert gcx.api_calls() == []


def test_transport_option_removed():
    with pytest.raises(SystemExit) as e:
        mod.main(["list", "--transport", "http"])
    assert e.value.code == 2


# ---- gcx calls ----
def test_create_argv_stdin_and_output(gcx, capsys):
    assert mod.main(create_args("--yes", "--duration", "90m", "--ticket", "INFRA-2234")) == 0
    argv, kw = gcx.api_calls()[0]
    assert argv == ["gcx", "api", PATH_S, "-X", "POST", "-d", "@-", "-o", "json"]
    body = json.loads(kw["input"])
    assert body["matchers"][0]["name"] == "alertname" and body["createdBy"] == "adam@example.com"
    assert "INFRA-2234" in body["comment"] and kw["timeout"] == 30
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "sil-1" and out["endsAt"] and out["expire_command"].endswith("expire sil-1")


def test_preflight_runs_first_and_never_views_config(gcx):
    mod.main(["list"])
    assert gcx.calls[0][0] == ["gcx", "config", "check"]
    assert all("view" not in argv for argv, _ in gcx.calls)


def test_expire_and_list_argv(gcx):
    assert mod.main(["expire", "g-1"]) == 0
    assert mod.main(["list"]) == 0
    calls = [a for a, _ in gcx.api_calls()]
    assert calls[0] == ["gcx", "api", PATH_S.replace("silences", "silence/g-1"), "-X", "DELETE", "-o", "json"]
    assert calls[1] == ["gcx", "api", PATH_S, "-o", "json"]


def test_list_active_filters(gcx, capsys):
    gcx.silences = {"a": {"id": "a", "status": {"state": "active"}},
                    "b": {"id": "b", "status": {"state": "expired"}}}
    assert mod.main(["list", "--active"]) == 0
    assert [s["id"] for s in json.loads(capsys.readouterr().out)] == ["a"]
    mod.main(["list"])
    assert len(json.loads(capsys.readouterr().out)) == 2


def test_gcx_failure_exit_3(gcx, capsys):
    gcx.api_rc, gcx.api_err = 1, "HTTP 403 forbidden"
    assert mod.main(["list"]) == 3
    assert "403" in capsys.readouterr().err


def test_gcx_timeout_exit_3(gcx, capsys):
    gcx.timeout = True
    assert mod.main(["list"]) == 3
    assert "timed out" in capsys.readouterr().err.lower()


# ---- self-test ----
def test_self_test_pass(gcx, capsys):
    assert mod.main(["self-test"]) == 0
    assert "PASS" in capsys.readouterr().out
    assert [a[4] if "-X" in a else "GET" for a, _ in gcx.api_calls()] == ["POST", "GET", "DELETE", "GET"]
    s = next(iter(gcx.silences.values()))
    assert s["matchers"][0]["value"] == "__mute_alert_selftest__"
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    assert datetime.strptime(s["endsAt"], fmt) - datetime.strptime(s["startsAt"], fmt) == timedelta(minutes=2)


def test_self_test_fail_if_not_expired(gcx, capsys):
    gcx.break_delete = True
    assert mod.main(["self-test"]) == 3
    assert "FAIL" in capsys.readouterr().out


# ---- doctor / readiness ----
def test_doctor_ok_never_leaks(capsys):
    assert mod.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "gcx OK" in out and "apollo-prod" in out and "SECRET-CONFIG-BODY" not in out


def test_doctor_gcx_missing_exit_2(monkeypatch, capsys):
    monkeypatch.setattr(mod.shutil, "which", lambda n: None)
    assert mod.main(["doctor"]) == 2
    out = capsys.readouterr().out
    assert "NOT READY" in out and "gcx-setup.md" in out


def test_doctor_config_check_fails_exit_2(gcx, capsys):
    gcx.check_rc = 1
    assert mod.main(["doctor"]) == 2
    assert "NOT READY" in capsys.readouterr().out


@pytest.mark.parametrize("args", [["list"], ["expire", "x"], ["self-test"], create_args("--yes")])
def test_not_ready_exits_2_before_any_api_call(args, gcx, capsys):
    gcx.check_rc = 1
    assert mod.main(args) == 2
    assert gcx.api_calls() == []
    assert "gcx-setup.md" in capsys.readouterr().err
