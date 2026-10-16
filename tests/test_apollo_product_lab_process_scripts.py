from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins" / "apollo-product-lab" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preview = load("preview-status")
doctor = load("ci-doctor")
stack = load("stack-sync")
claims = load("verify-claims")

HEAD = "a" * 40
OLD = "b" * 40


class PreviewGh:
    def __init__(self, run_lists):
        self.run_lists = list(run_lists)
        self.calls = []

    def __call__(self, args, cwd=None):
        self.calls.append(args)
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"headRefOid": HEAD, "headRefName": "feature", "url": "https://github.test/pull/1"})
        if args[:2] == ["run", "list"]:
            value = self.run_lists.pop(0) if len(self.run_lists) > 1 else self.run_lists[0]
            return 0, json.dumps(value)
        return 1, ""


def run_item(sha=HEAD, status="completed", conclusion="success", name="Preview deploy", created="2026-01-02", run_id=2):
    return {"databaseId": run_id, "workflowName": name, "headSha": sha, "status": status,
            "conclusion": conclusion, "createdAt": created, "url": "https://github.test/runs/%s" % run_id}


def test_preview_success_reports_deployed_head():
    result = preview.inspect_preview(1, gh=PreviewGh([[run_item()]]))
    assert result["ok"] and result["deployed_sha"] == HEAD and result["conclusion"] == "success"


def test_preview_missing_current_head_reports_old_deployment():
    result = preview.inspect_preview(1, gh=PreviewGh([[run_item(OLD)]]))
    assert not result["ok"] and result["deployed_sha"] == OLD
    assert "current PR head" in result["problems"][0]["problem"]
    assert result["problems"][0]["next"]


def test_preview_fallback_is_limited_to_the_pr_branch():
    gh = PreviewGh([[run_item(status="completed", conclusion="failure")], [run_item(OLD)]])
    result = preview.inspect_preview(1, gh=gh)
    fallback = [call for call in gh.calls if call[:2] == ["run", "list"] and "--commit" not in call][0]
    assert fallback[fallback.index("--branch") + 1] == "feature"
    assert result["deployed_sha"] == OLD


def test_preview_fallback_uses_the_current_preview_workflow():
    current = run_item(status="completed", conclusion="failure", name="API Preview", run_id=4)
    api_old = run_item(OLD, name="API Preview", created="2026-01-01", run_id=1)
    docs_new = run_item("c" * 40, name="Docs Preview", created="2026-01-03", run_id=3)
    result = preview.inspect_preview(1, gh=PreviewGh([[current], [api_old, docs_new]]))
    assert result["deployed_sha"] == OLD


def test_preview_does_not_use_repository_wide_fallback_without_pr_branch():
    def gh(args, cwd=None):
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"headRefOid": HEAD})
        if "--commit" in args:
            return 0, json.dumps([run_item(status="completed", conclusion="failure")])
        raise AssertionError("repository-wide fallback must not run")

    assert preview.inspect_preview(1, gh=gh)["deployed_sha"] is None


@pytest.mark.parametrize("conclusion", ["failure", "cancelled"])
def test_preview_failed_or_cancelled_needs_action(conclusion):
    result = preview.inspect_preview(1, gh=PreviewGh([[run_item(conclusion=conclusion)]]))
    assert not result["ok"] and result["conclusion"] == conclusion
    assert "Next:" in preview.render(result)


def test_preview_wait_polls_until_completed():
    gh = PreviewGh([[run_item(status="in_progress", conclusion=None)], [run_item()]])
    ticks = iter([0, 0, 1, 1])
    result = preview.inspect_preview(1, wait=10, gh=gh, sleep=lambda _: None, clock=lambda: next(ticks))
    assert result["ok"]
    assert len([call for call in gh.calls if call[:2] == ["run", "list"]]) == 2


def test_preview_wait_polls_until_a_run_appears():
    gh = PreviewGh([[], [run_item()]])
    ticks = iter([0, 0, 1, 1])
    result = preview.inspect_preview(1, wait=10, gh=gh, sleep=lambda _: None, clock=lambda: next(ticks))
    assert result["ok"]


def test_preview_custom_workflow_regex_and_bad_regex():
    result = preview.inspect_preview(1, workflow="storybook", gh=PreviewGh([[run_item(name="Storybook Publish")]]))
    assert result["ok"]
    with pytest.raises(ValueError):
        preview.inspect_preview(1, workflow="[", gh=PreviewGh([[]]))


class DoctorGh:
    def __init__(self, checks, logs=None, attempts=None, files=None):
        self.checks = checks
        self.logs = logs or {}
        self.attempts = attempts or {}
        self.files = [{"path": "app/a.rb"}] if files is None else [{"path": path} for path in files]
        self.calls = []

    def __call__(self, args, cwd=None):
        self.calls.append(args)
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"headRefOid": HEAD, "baseRefName": "master", "files": self.files})
        if args[:2] == ["pr", "checks"]:
            return 0, json.dumps(self.checks)
        if args[:2] == ["run", "view"]:
            if "--json" in args:
                return 0, json.dumps({"attempt": self.attempts.get(args[2], 1)})
            return 0, self.logs.get(args[2], "")
        return 1, ""


def doctor_git(behind=0):
    def runner(args, cwd=None):
        if args[:2] == ["rev-list", "--count"]:
            return 0, str(behind)
        return 1, ""
    return runner


def failed(name="test", run=11):
    return {"name": name, "bucket": "fail", "state": "FAILURE", "link": "https://github.test/actions/runs/%s/job/2" % run}


def test_ci_doctor_classifies_seed_patterns_and_pending():
    checks = [failed("frontend", 1), failed("verify-job-runs-on-sensitive-files-approval", 2),
              failed("policy-bot", 3), {"name": "backend", "bucket": "pending", "state": "PENDING", "link": ""}]
    gh = DoctorGh(checks, {"1": "0 examples", "2": "waiting", "3": "denied"}, {"1": 2})
    result = doctor.diagnose(7, gh=gh, git=doctor_git())
    assert [row["classification"] for row in result["checks"]] == [
        "knapsack_empty_queue", "sensitive_file_approval", "policy-bot", "pending"
    ]
    assert all(row["next"] for row in result["checks"])


def test_ci_doctor_empty_queue_on_first_attempt_is_not_called_rerun_bug():
    result = doctor.diagnose(7, gh=DoctorGh([failed()], {"11": "0 examples"}), git=doctor_git())
    assert result["checks"][0]["classification"] == "real_failure"


def test_ci_doctor_stale_branch_when_untouched_spec_fails():
    log = "spec/models/other_spec.rb:12: failure"
    result = doctor.diagnose(7, gh=DoctorGh([failed()], {"11": log}), git=doctor_git(3))
    row = result["checks"][0]
    assert row["classification"] == "stale_branch" and row["next"] == "merge the base and rerun"


def test_ci_doctor_changed_spec_is_real_failure_with_first_error():
    gh = DoctorGh([failed()], {"11": "spec/models/changed_spec.rb:12\nERROR first useful line\nERROR later"},
                  files=["spec/models/changed_spec.rb"])
    result = doctor.diagnose(7, gh=gh, git=doctor_git(2))
    row = result["checks"][0]
    assert row["classification"] == "real_failure"
    assert row["detail"] == "ERROR first useful line" and "ERROR first useful line" in row["next"]


def test_ci_doctor_scopes_failed_logs_to_each_job_before_classifying():
    checks = [failed("unit", 11), {**failed("lint", 11), "link": "https://github.test/actions/runs/11/job/3"}]
    calls = []

    def gh(args, cwd=None):
        calls.append(args)
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"headRefOid": HEAD, "baseRefName": "master", "files": []})
        if args[:2] == ["pr", "checks"]:
            return 1, json.dumps(checks)
        if "--json" in args:
            return 0, json.dumps({"attempt": 2})
        return 0, "unit: 0 examples\nlint: ERROR syntax error"

    result = doctor.diagnose(1, gh=gh, git=doctor_git())
    assert [row["classification"] for row in result["checks"]] == ["knapsack_empty_queue", "real_failure"]
    assert [row["log_tail"] for row in result["checks"]] == ["0 examples", "ERROR syntax error"]
    assert [call[call.index("--job") + 1] for call in calls if "--job" in call] == ["2", "3"]


def test_ci_doctor_fetches_and_keeps_only_last_80_log_lines():
    log = "\n".join("line %s" % n for n in range(100))
    result = doctor.diagnose(7, gh=DoctorGh([failed()], {"11": log}), git=doctor_git())
    kept = result["checks"][0]["log_tail"].splitlines()
    assert len(kept) == 80 and kept[0] == "line 20"


def test_ci_doctor_clean_checks_are_ok():
    gh = DoctorGh([{"name": "unit", "bucket": "pass", "state": "SUCCESS", "link": ""}])
    assert doctor.diagnose(7, gh=gh, git=doctor_git())["ok"]


def test_ci_doctor_accepts_gh_failure_and_pending_exit_codes_when_json_is_present():
    for exit_code in (1, 8):
        def gh(args, cwd=None, code=exit_code):
            if args[:2] == ["pr", "view"]:
                return 0, json.dumps({"headRefOid": HEAD, "baseRefName": "master", "files": []})
            if args[:2] == ["pr", "checks"]:
                return code, json.dumps([{"name": "unit", "bucket": "pending", "state": "PENDING", "link": ""}])
            return 1, ""
        assert doctor.diagnose(7, gh=gh, git=doctor_git())["checks"][0]["classification"] == "pending"


def test_ci_pattern_file_requires_seed_keys_and_valid_regex(tmp_path):
    missing = tmp_path / "missing.yml"
    missing.write_text("{}")
    with pytest.raises(RuntimeError, match="must define"):
        doctor.load_patterns(missing)
    bad = tmp_path / "bad.yml"
    source = json.loads((ROOT / "plugins" / "apollo-product-lab" / "framework" / "references" / "ci-patterns.yml").read_text())
    source["policy-bot"]["patterns"] = ["["]
    bad.write_text(json.dumps(source))
    with pytest.raises(RuntimeError, match="invalid CI regex"):
        doctor.load_patterns(bad)


class StackGh:
    def __init__(self):
        self.bases = {"feature-2": (22, "feature-1"), "feature-1": (21, "master")}

    def __call__(self, args, cwd=None):
        branch = args[args.index("--head") + 1]
        if branch not in self.bases:
            return 0, "[]"
        number, base = self.bases[branch]
        return 0, json.dumps([{"number": number, "headRefName": branch, "baseRefName": base, "url": "u"}])


class StackGit:
    def __init__(self, conflict=None, merge_failure=None, dirty=False, bad_ancestry=None):
        self.calls = []
        self.conflict = conflict
        self.merge_failure = merge_failure
        self.dirty = dirty
        self.bad_ancestry = bad_ancestry

    def __call__(self, args, cwd=None):
        self.calls.append(args)
        if args[:2] == ["rev-list", "--count"]:
            return 0, "2"
        if args[:2] == ["merge-tree", "--write-tree"]:
            return (1, "CONFLICT") if args[2] == self.conflict else (0, "tree")
        if args == ["status", "--porcelain"]:
            return 0, " M x" if self.dirty else ""
        if args[:1] == ["switch"]:
            return 0, ""
        if args[:3] == ["-c", "merge.autostash=false", "merge"]:
            return (1, "CONFLICT") if args[-1] == self.merge_failure else (0, "merged")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return (1, "") if args[2] == self.bad_ancestry else (0, "")
        return 1, ""


class StatefulStackGit:
    def __init__(self):
        self.state = {"master": {"a", "new"}, "feature-1": {"a", "p"}, "feature-2": {"a", "p", "c"}}
        self.current = None
        self.calls = []

    def __call__(self, args, cwd=None):
        self.calls.append(args)
        if args[:2] == ["rev-list", "--count"]:
            branch, base = args[-1].split("..")
            return 0, str(len(self.state[base] - self.state[branch]))
        if args[:2] == ["merge-tree", "--write-tree"]:
            return 0, "tree"
        if args == ["status", "--porcelain"]:
            return 0, ""
        if args[:1] == ["switch"]:
            self.current = args[1]
            return 0, ""
        if args[:3] == ["-c", "merge.autostash=false", "merge"]:
            self.state[self.current] |= self.state[args[-1]]
            return 0, "merged"
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return (0 if self.state[args[2]] <= self.state[args[3]] else 1), ""
        return 1, ""


def test_stack_sync_reports_bottom_up_commands_and_conflicts():
    result = stack.inspect_stack("feature-2", gh=StackGh(), git=StackGit(conflict="feature-2"))
    assert [item["branch"] for item in result["stack"]] == ["feature-1", "feature-2"]
    assert result["commands"][0] == "git switch feature-1"
    assert not result["ok"] and result["problems"][0]["next"]


def test_stack_sync_behind_branch_needs_action_even_without_conflict():
    result = stack.inspect_stack("feature-2", gh=StackGh(), git=StackGit())
    assert not result["ok"]
    assert any("behind" in item["problem"] for item in result["problems"])


def test_stack_sync_apply_merges_bottom_up_and_only_prints_gated_pushes():
    git = StackGit()
    result = stack.inspect_stack("feature-2", apply=True, gh=StackGh(), git=git)
    merges = [call for call in git.calls if call[:3] == ["-c", "merge.autostash=false", "merge"]]
    assert [call[-1] for call in merges] == ["master", "feature-1"]
    assert result["push_commands"] == ["git push origin feature-1", "git push origin feature-2"]
    assert not any(call[:1] == ["push"] for call in git.calls)


def test_stack_sync_recomputes_child_after_parent_merge():
    git = StatefulStackGit()
    result = stack.inspect_stack("feature-2", apply=True, gh=StackGh(), git=git)
    merges = [call[-1] for call in git.calls if call[:3] == ["-c", "merge.autostash=false", "merge"]]
    assert merges == ["master", "feature-1"]
    assert [item["behind"] for item in result["stack"]] == [0, 0]
    assert result["push_commands"] == ["git push origin feature-1", "git push origin feature-2"]


def test_stack_sync_dry_run_propagates_parent_update_to_current_child():
    result = stack.inspect_stack("feature-2", gh=StackGh(), git=StatefulStackGit())
    assert result["commands"] == [
        "git switch feature-1", "git -c merge.autostash=false merge --no-edit master",
        "git switch feature-2", "git -c merge.autostash=false merge --no-edit feature-1",
    ]


def test_stack_sync_apply_stops_at_first_merge_conflict():
    git = StackGit(merge_failure="master")
    result = stack.inspect_stack("feature-2", apply=True, gh=StackGh(), git=git)
    assert not result["ok"] and len([call for call in git.calls if call[:1] == ["switch"]]) == 1
    assert not result["push_commands"]


def test_stack_sync_refuses_dirty_tree_and_gates_each_push():
    with pytest.raises(RuntimeError, match="dirty"):
        stack.inspect_stack("feature-2", apply=True, gh=StackGh(), git=StackGit(dirty=True))
    result = stack.inspect_stack("feature-2", apply=True, gh=StackGh(), git=StackGit(bad_ancestry="master"))
    assert not result["ok"] and result["push_commands"] == ["git push origin feature-2"]


def test_verify_claims_accepts_each_evidence_kind_and_negations(tmp_path):
    output = tmp_path / "test-output.log"
    output.write_text("ok")
    report = tmp_path / "report.md"
    report.write_text(
        "Fixed parser — abcdef1\n"
        "Deploy verified: https://preview.test/x\n"
        "Tests passed\n  `test-output.log`\n"
        "Build is green\n  cmd: pytest -q; exit status: 0\n"
        "Preview not verified\nTests not run\n"
    )

    def git(args, cwd=None):
        return (0, "") if args[:2] == ["cat-file", "-e"] and args[2].startswith("abcdef1") else (1, "")

    result = claims.verify_report(report, git=git, cwd=tmp_path)
    assert result["ok"] and result["claims_checked"] == 4


def test_verify_claims_scopes_negation_and_ignores_plans_and_negative_status(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("Tests passed; preview not verified.\nTests have not passed.\nNext: verify that login works.\n")
    result = claims.verify_report(report, git=lambda args, cwd=None: (1, ""), cwd=tmp_path)
    assert result["claims_checked"] == 1
    assert [item["claim"] for item in result["unsupported"]] == ["Tests passed"]


@pytest.mark.parametrize("separator", [". ", "! ", "? ", "; ", "\n"])
def test_verify_claims_splits_sentences_before_applying_negation(tmp_path, separator):
    report = tmp_path / "report.md"
    report.write_text("Tests pass%sPreview not verified.\n" % separator)
    result = claims.verify_report(report, git=lambda args, cwd=None: (1, ""), cwd=tmp_path)
    assert result["claims_checked"] == 1
    assert [item["claim"] for item in result["unsupported"]] == ["Tests pass"]


def test_verify_claims_recognizes_pass_and_requires_successful_command(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("Tests pass\n  cmd: pytest -q; exit status: 1\nTests passed\n  cmd: pytest -q; exit status: 0\n")
    result = claims.verify_report(report, git=lambda args, cwd=None: (1, ""), cwd=tmp_path)
    assert result["claims_checked"] == 2
    assert [item["line"] for item in result["unsupported"]] == [1]


def test_verify_claims_lists_unsupported_claims_and_does_not_borrow_unindented_evidence(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("Feature works\nEvidence elsewhere https://example.test\nMerged cleanly\n")
    result = claims.verify_report(report, git=lambda args, cwd=None: (1, ""), cwd=tmp_path)
    assert [item["line"] for item in result["unsupported"]] == [1, 3]
    assert all(item["next"] for item in result["unsupported"])
    assert "Next:" in claims.render(result)


def test_verify_claims_rejects_nonresolving_sha_and_missing_path(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("Done abcdef1 `missing/output.log`\n")
    result = claims.verify_report(report, git=lambda args, cwd=None: (1, ""), cwd=tmp_path)
    assert not result["ok"]


def test_verify_claims_missing_report_is_error(tmp_path):
    with pytest.raises(RuntimeError, match="cannot read report"):
        claims.verify_report(tmp_path / "missing.md")


def test_process_scripts_are_documented_and_not_hooked():
    plugin = ROOT / "plugins" / "apollo-product-lab"
    docs = "\n".join((plugin / "framework" / name).read_text() for name in (
        "20-build-stage.md", "21-verify-stage.md", "52-process-scripts.md", "index.md"
    ))
    for name in ("preview-status.py", "ci-doctor.py", "stack-sync.py", "verify-claims.py"):
        assert name in docs
        assert name not in (plugin / "hooks" / "hooks.json").read_text()
    for skill in ("harness-intake", "harness-snapshot", "harness-council"):
        assert "verify-claims.py" in (plugin / "skills" / skill / "SKILL.md").read_text()


def test_cli_json_and_exit_code_contracts(tmp_path, capsys):
    assert preview.main(["--pr", "1", "--json"], gh=PreviewGh([[run_item()]])) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True

    ci_gh = DoctorGh([{"name": "unit", "bucket": "pending", "state": "PENDING", "link": ""}])
    assert doctor.main(["--pr", "1", "--json"], gh=ci_gh, git=doctor_git()) == 1
    assert json.loads(capsys.readouterr().out)["checks"][0]["next"]

    assert stack.main(["--tip", "feature-2", "--json"], gh=StackGh(), git=StackGit()) == 1
    assert json.loads(capsys.readouterr().out)["problems"][0]["next"]

    report = tmp_path / "report.md"
    report.write_text("Feature works\n")
    assert claims.main([str(report), "--json"], git=lambda args, cwd=None: (1, "")) == 1
    assert json.loads(capsys.readouterr().out)["unsupported"][0]["next"]

    assert claims.main([str(tmp_path / "missing.md"), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["next"]
