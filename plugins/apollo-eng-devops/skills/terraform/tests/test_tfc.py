from __future__ import annotations

import json

import pytest

tfc = pytest.importorskip("tfc")


def test_parse_run_url():
    url = "https://app.terraform.io/app/apolloio/workspaces/gcp-data-platform-iam/runs/run-5dvoEjXaiqbytcrK"
    assert tfc.parse_run_url(url) == ("apolloio", "gcp-data-platform-iam", "run-5dvoEjXaiqbytcrK")


def test_parse_run_url_workspace_only():
    url = "https://app.terraform.io/app/apolloio/workspaces/gcp-data-platform-iam"
    assert tfc.parse_run_url(url) == ("apolloio", "gcp-data-platform-iam", None)


def test_parse_run_url_rejects_other_hosts():
    with pytest.raises(ValueError):
        tfc.parse_run_url("https://evil.example.com/app/apolloio/workspaces/x/runs/run-abc")


def test_load_token_prefers_env(monkeypatch, tmp_path):
    monkeypatch.setenv("TFE_TOKEN", "env-token")
    assert tfc.load_token(home=tmp_path) == "env-token"


def test_load_token_from_credentials_file(monkeypatch, tmp_path):
    monkeypatch.delenv("TFE_TOKEN", raising=False)
    monkeypatch.delenv("TF_TOKEN_app_terraform_io", raising=False)
    d = tmp_path / ".terraform.d"
    d.mkdir()
    (d / "credentials.tfrc.json").write_text(
        json.dumps({"credentials": {"app.terraform.io": {"token": "file-token"}}})
    )
    assert tfc.load_token(home=tmp_path) == "file-token"


def test_load_token_missing_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("TFE_TOKEN", raising=False)
    monkeypatch.delenv("TF_TOKEN_app_terraform_io", raising=False)
    with pytest.raises(RuntimeError, match="terraform login"):
        tfc.load_token(home=tmp_path)


def _plan():
    def rc(addr, typ, actions):
        return {"address": addr, "type": typ, "change": {"actions": actions}}

    return {
        "resource_changes": [
            rc("google_project_iam_member.a", "google_project_iam_member", ["create"]),
            rc("google_bigquery_dataset.b", "google_bigquery_dataset", ["update"]),
            rc("google_storage_bucket.c", "google_storage_bucket", ["delete"]),
            rc("google_sql_instance.d", "google_sql_instance", ["delete", "create"]),
            rc("google_project.e", "google_project", ["no-op"]),
            rc("data.google_x.f", "google_x", ["read"]),
        ]
    }


def test_summarize_plan_counts():
    s = tfc.summarize_plan(_plan())
    assert s["counts"] == {"create": 1, "update": 1, "delete": 1, "replace": 1}


def test_summarize_plan_flags_risk():
    s = tfc.summarize_plan(_plan())
    assert "google_storage_bucket.c" in s["destroy"]
    assert "google_sql_instance.d" in s["replace"]
    assert "google_project_iam_member.a" in s["iam"]


def test_summarize_plan_empty():
    s = tfc.summarize_plan({"resource_changes": []})
    assert s["counts"] == {"create": 0, "update": 0, "delete": 0, "replace": 0}
    assert s["iam"] == []


def test_summarize_plan_caps_lists():
    plan = {
        "resource_changes": [
            {"address": f"r.{i}", "type": "r", "change": {"actions": ["delete"]}} for i in range(100)
        ]
    }
    s = tfc.summarize_plan(plan, cap=10)
    assert len(s["destroy"]) == 10
    assert s["counts"]["delete"] == 100


def test_dirs_from_files_tf_only():
    files = ["iam/main.tf", "iam/vars.tf", "README.md", "data/x/main.tf", "docs/a.md"]
    assert tfc.dirs_from_files(files) == ["data/x", "iam"]


def test_dirs_from_files_root():
    assert tfc.dirs_from_files(["main.tf"]) == ["."]


def test_match_workspaces_by_working_directory():
    ws = [
        {"name": "a", "working-directory": "iam"},
        {"name": "b", "working-directory": "data/x"},
        {"name": "c", "working-directory": "other"},
    ]
    assert [w["name"] for w in tfc.match_workspaces(ws, ["iam", "data/x"])] == ["a", "b"]


def test_match_workspaces_none():
    assert tfc.match_workspaces([{"name": "a", "working-directory": "z"}], ["iam"]) == []


def test_lock_summary_unlocked():
    ws = {"attributes": {"locked": False}}
    assert tfc.lock_summary(ws, None) == "unlocked"


def test_lock_summary_locked_by_run():
    ws = {"attributes": {"locked": True}, "relationships": {"locked-by": {"data": {"id": "run-1", "type": "runs"}}}}
    assert "run-1" in tfc.lock_summary(ws, None)


def test_require_yes_blocks_mutation():
    with pytest.raises(SystemExit):
        tfc.require_yes(False, "apply run-1")


def test_require_yes_allows():
    tfc.require_yes(True, "apply run-1")


def test_workspace_from_provider_tf():
    text = '''
terraform {
  cloud {
    organization = "apolloio"
    workspaces {
      name = "gcp-data-platform-iam"
    }
  }
}
'''
    assert tfc.workspace_from_provider_tf(text) == ("apolloio", "gcp-data-platform-iam")


def test_workspace_from_provider_tf_missing():
    assert tfc.workspace_from_provider_tf("terraform {}") is None


def test_workspace_name_for_path():
    assert tfc.workspace_name_for_path("terraform/gcp/data-platform/iam/dp-staging.tf") == "gcp-data-platform-iam"
    assert tfc.workspace_name_for_path("terraform/gcp/prod/ops_agent/x.tf") == "gcp-prod-ops-agent"


def test_workspace_name_for_path_outside_terraform():
    assert tfc.workspace_name_for_path("README.md") is None


def test_plan_required_excludes():
    assert tfc.plan_required("terraform/gcp/modules/foo/main.tf") is False
    assert tfc.plan_required("terraform/gcp/staging/mongo-a/main.tf") is False
    assert tfc.plan_required("terraform/gcp/prod/validation/x.tf") is False
    assert tfc.plan_required("terraform/gcp/team/tfc-permissions/x.tf") is False
    assert tfc.plan_required("terraform/gcp/prod/cf-functions/x.tf") is False
    assert tfc.plan_required("terraform/gcp/data-platform/iam/main.tf") is True
    assert tfc.plan_required("docs/x.md") is False


def test_workspaces_for_files():
    files = [
        "terraform/gcp/data-platform/iam/a.tf",
        "terraform/gcp/data-platform/iam/b.tf",
        "terraform/gcp/modules/m/main.tf",
        "README.md",
    ]
    ws, skipped = tfc.workspaces_for_files(files)
    assert ws == ["gcp-data-platform-iam"]
    assert skipped == ["terraform/gcp/modules/m/main.tf"]


COMMENT = """#### Terraform Cloud Plan Output on gcp-data-platform-iam
```
Plan: 2 to add, 1 to change, 0 to destroy.
```
[Terraform Plan](https://app.terraform.io/app/apolloio/workspaces/gcp-data-platform-iam/runs/run-abc123)
"""


def test_parse_plan_comment():
    r = tfc.parse_plan_comment(COMMENT)
    assert r == {
        "workspace": "gcp-data-platform-iam",
        "add": 2,
        "change": 1,
        "destroy": 0,
        "run": "run-abc123",
    }


def test_parse_plan_comment_other_comment():
    assert tfc.parse_plan_comment("LGTM") is None


def _run(id_, created, plan_only=True):
    return {"id": id_, "attributes": {"created-at": created, "plan-only": plan_only, "status": "planned_and_finished"}}


def test_pick_plan_run_newest_after_since():
    runs = [
        _run("run-new", "2026-10-15T12:00:00Z"),
        _run("run-apply", "2026-10-15T11:00:00Z", plan_only=False),
        _run("run-old", "2026-10-14T00:00:00Z"),
    ]
    assert tfc.pick_plan_run(runs, "2026-10-15T10:00:00Z")["id"] == "run-new"


def test_pick_plan_run_none_after_since():
    assert tfc.pick_plan_run([_run("run-old", "2026-10-14T00:00:00Z")], "2026-10-15T10:00:00Z") is None


def test_pick_plan_run_ignores_non_plan_only():
    assert tfc.pick_plan_run([_run("r", "2026-10-16T00:00:00Z", plan_only=False)], "2026-10-15T00:00:00Z") is None
