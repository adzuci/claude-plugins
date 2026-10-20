from __future__ import annotations

import json

import pytest

dc = pytest.importorskip("drift_check")


class FakeAPI:
    """Scripted stand-in for the TFC HTTP calls."""

    def __init__(self, plan_json, plan_statuses=("running", "finished"), applied=True):
        self.plan_json = plan_json
        self.statuses = list(plan_statuses)
        self.applied = applied
        self.calls = []

    def __call__(self, method, path, body=None):
        self.calls.append((method, path, body))
        if path.startswith("/organizations/") and "/workspaces/" in path:
            return {"data": {"id": "ws-1"}}
        if path.startswith("/workspaces/ws-1/runs"):
            data = [{"id": "run-old", "relationships": {"configuration-version": {"data": {"id": "cv-1"}}}}]
            return {"data": data if self.applied else []}
        if method == "POST" and path == "/runs":
            return {"data": {"id": "run-new", "relationships": {"plan": {"data": {"id": "plan-1"}}}}}
        if path == "/plans/plan-1":
            st = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
            return {"data": {"attributes": {"status": st}}}
        if path == "/plans/plan-1/json-output":
            return self.plan_json
        if path.endswith("/actions/cancel"):
            return {}
        raise AssertionError(f"unexpected call {method} {path}")


def test_creates_plan_only_run_on_last_applied_config(load):
    api = FakeAPI(load("plan_drift"))
    r = dc.check_workspace(api, "apolloio", "gcp-prod", timeout=5, poll=0)
    post = [c for c in api.calls if c[0] == "POST" and c[1] == "/runs"][0][2]
    attrs = post["data"]["attributes"]
    assert attrs["plan-only"] is True
    assert post["data"]["relationships"]["configuration-version"]["data"]["id"] == "cv-1"
    assert "is-destroy" not in attrs and "auto-apply" not in attrs
    assert r["status"] == "drift" and r["counts"]["drift"] == 2


def test_never_calls_apply_or_confirm(load):
    api = FakeAPI(load("plan_drift"))
    dc.check_workspace(api, "apolloio", "gcp-prod", timeout=5, poll=0)
    assert not any("apply" in p or "confirm" in p for _, p, _ in api.calls)


def test_clean_plan(load):
    r = dc.check_workspace(FakeAPI(load("plan_clean")), "apolloio", "gcp-iam", timeout=5, poll=0)
    assert r["status"] == "clean"


def test_pending_without_drift_is_its_own_status(load):
    plan = load("plan_drift")
    plan["resource_drift"] = []
    r = dc.check_workspace(FakeAPI(plan), "apolloio", "gcp-prod", timeout=5, poll=0)
    assert r["status"] == "pending"


def test_errored_plan_is_error(load):
    api = FakeAPI(load("plan_clean"), plan_statuses=("errored",))
    r = dc.check_workspace(api, "apolloio", "gcp-ops", timeout=5, poll=0)
    assert r["status"] == "error"


@pytest.mark.parametrize("status", ["canceled", "discarded", "force_canceled", "unreachable"])
def test_terminal_failed_plan_is_error(load, status):
    r = dc.check_workspace(FakeAPI(load("plan_clean"), plan_statuses=(status,)), "apolloio", "gcp-ops", timeout=5, poll=0)
    assert r["status"] == "error" and status in r["error"]


def test_timeout_cancels_run(load):
    api = FakeAPI(load("plan_clean"), plan_statuses=("running",))
    r = dc.check_workspace(api, "apolloio", "gcp-ops", timeout=0, poll=0)
    assert r["status"] == "error" and "timeout" in r["error"]
    assert any(p == "/runs/run-new/actions/cancel" for _, p, _ in api.calls)


def test_no_applied_run_is_error(load):
    r = dc.check_workspace(FakeAPI(load("plan_clean"), applied=False), "apolloio", "x", timeout=5, poll=0)
    assert r["status"] == "error" and "no applied run" in r["error"]


def test_token_resolution_prefers_env(tmp_path):
    creds = tmp_path / "c.json"
    creds.write_text(json.dumps({"credentials": {"app.terraform.io": {"token": "file-tok"}}}))
    assert dc.resolve_token({"TFE_TOKEN": "env-tok"}, creds) == "env-tok"
    assert dc.resolve_token({"TF_API_TOKEN": "api-tok"}, creds) == "api-tok"
    assert dc.resolve_token({}, creds) == "file-tok"
    assert dc.resolve_token({}, tmp_path / "missing.json") is None


def test_workspace_list_override_and_default(tmp_path):
    ref = tmp_path / "w.json"
    ref.write_text(json.dumps({"organization": "apolloio", "workspaces": [{"name": "a"}, {"name": "b"}]}))
    assert dc.load_workspaces(ref, None) == ("apolloio", ["a", "b"])
    assert dc.load_workspaces(ref, "c, d") == ("apolloio", ["c", "d"])


def test_workspace_name_rejects_paths(tmp_path):
    ref = tmp_path / "w.json"
    ref.write_text(json.dumps({"organization": "apolloio", "workspaces": []}))
    with pytest.raises(ValueError):
        dc.load_workspaces(ref, "../evil")


def test_forbidden_is_explained(load):
    import urllib.error

    def api(method, path, body=None):
        raise urllib.error.HTTPError(path, 403, "Forbidden", {}, None)

    r = dc.check_workspace(api, "apolloio", "gcp-prod", timeout=5, poll=0)
    assert r["status"] == "error" and "403" in r["error"] and "permission" in r["error"]


def test_main_json_output(monkeypatch, capsys, tmp_path):
    ref = tmp_path / "w.json"
    ref.write_text(json.dumps({"organization": "apolloio", "workspaces": [{"name": "gcp-ops"}]}))
    monkeypatch.setattr(dc, "REF", ref)
    monkeypatch.setattr(dc, "resolve_token", lambda env: "token")
    monkeypatch.setattr(dc, "make_api", lambda token: FakeAPI({"resource_changes": [], "resource_drift": []}))
    assert dc.main(["--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["overall"] == "clean" and report["results"][0]["workspace"] == "gcp-ops"
