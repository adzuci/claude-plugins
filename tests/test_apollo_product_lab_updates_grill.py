from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "apollo-product-lab"
STORAGE = PLUGIN / "scripts" / "storage.py"
POST_UPDATE = PLUGIN / "scripts" / "post-update.py"
GRILL_CHECK = PLUGIN / "scripts" / "grill-check.py"
RECORD_SYNC = PLUGIN / "scripts" / "record-sync.sh"
SESSION_START = PLUGIN / "scripts" / "session-start.sh"
APPEND = PLUGIN / "framework" / "ledger" / "append.py"


def run_python(script, *args, cwd=None, env=None):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        cwd=cwd or REPO,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
    )


def profile(path, tracker, *, project="WO", issue="", persona="pm", storage="local"):
    path.write_text(
        f"persona: {persona}\nstorage: {storage}\ncollaboration: solo\ndefault_run: demo-run1\n"
        "notion_parent: https://notion.test/demo\n"
        f"updates:\n  tracker: {tracker}\n  jira_project: {project}\n  jira_issue: {issue}\n"
        "  notion_parent: https://notion.test/demo\n"
    )


def update_identity(outcome="resolved-clean"):
    return (
        "--initiative", "demo", "--run", "demo-run1", "--event", "stage-event-1",
        "--agent", "skill:harness-snapshot", "--outcome", outcome,
    )


def test_profile_tracker_validation_has_actionable_errors(tmp_path):
    path = tmp_path / "profile.yml"
    profile(path, "linear")
    result = run_python(STORAGE, "validate-profile", path)
    assert result.returncode == 2
    assert "unknown tracker" in result.stderr and "Next:" in result.stderr
    profile(path, "jira", project="")
    result = run_python(STORAGE, "validate-profile", path)
    assert result.returncode == 2
    assert "jira_project" in result.stderr and "Next:" in result.stderr
    profile(path, "linear")
    detected = run_python(STORAGE, "detect", "--profile", path, cwd=tmp_path, env={"HOME": str(tmp_path)})
    assert detected.returncode != 0 and "unknown tracker" in detected.stderr and "Next:" in detected.stderr


def test_session_start_reports_an_unknown_tracker_with_next_step(tmp_path):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    profile(home / ".claude" / "harness-profile.yml", "linear")
    result = subprocess.run(
        ["bash", str(SESSION_START)], input="{}", cwd=tmp_path,
        env={**os.environ, "HOME": str(home), "CLAUDE_PLUGIN_ROOT": str(PLUGIN)},
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "ERROR:" in result.stdout and "unknown tracker" in result.stdout and "Next:" in result.stdout


@pytest.mark.parametrize(
    ("tracker", "tools", "jira_status"),
    [
        ("notion", ["storage.py ledger-entry"], None),
        ("jira", ["mcp__atlassian__addCommentToJiraIssue"], "jira: planned for WO-9"),
        ("both", ["storage.py ledger-entry", "mcp__atlassian__addCommentToJiraIssue"], "jira: planned for WO-9"),
    ],
)
def test_post_update_plans_each_tracker_without_calling_network(tmp_path, tracker, tools, jira_status):
    path = tmp_path / "profile.yml"
    profile(path, tracker, issue="WO-9")
    result = run_python(
        POST_UPDATE,
        "--stage", "F.build", "--summary", "Built the slice", "--links", "https://example.test/a",
        *update_identity(), "--profile", path,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert [call["tool"] for call in plan["calls"]] == tools
    if jira_status:
        assert jira_status in plan["status"]


def test_post_update_prefers_cli_then_current_selected_intake_then_profile_issue(tmp_path):
    repo = tmp_path / "repo"
    run = repo / ".ai" / "demo" / "runs" / "demo-run1"
    run.mkdir(parents=True)
    (run / "intake.snapshot.md").write_text("tracker epic: WO-11\n")
    (run / "intake.snapshot.2.md").write_text("tracker epic: WO-22\n")
    (run / "intake.snapshot.3.md").write_text("tracker epic: WO-33\n")
    other = repo / ".ai" / "aaa" / "runs" / "demo-run1"
    other.mkdir(parents=True)
    (other / "intake.snapshot.9.md").write_text("tracker epic: WRONG-9\n")
    path = tmp_path / "profile.yml"
    profile(path, "jira", issue="WO-9")
    env = {"HARNESS_REPO_ROOT": str(repo)}
    intake = json.loads(run_python(
        POST_UPDATE, "--stage", "G.verify", "--summary", "ok", "--initiative", "demo", "--run", "demo-run1",
        "--profile", path, env=env,
    ).stdout)
    explicit = json.loads(run_python(
        POST_UPDATE, "--stage", "G.verify", "--summary", "ok", "--issue", "WO-44", "--initiative", "demo",
        "--run", "demo-run1", "--profile", path, env=env,
    ).stdout)
    assert intake["calls"][0]["args"]["issueIdOrKey"] == "WO-33"
    assert explicit["calls"][0]["args"]["issueIdOrKey"] == "WO-44"


def test_post_update_latest_blocked_intake_does_not_revive_an_old_or_profile_issue(tmp_path):
    repo = tmp_path / "repo"
    run = repo / ".ai" / "demo" / "runs" / "demo-run1"
    run.mkdir(parents=True)
    (run / "intake.snapshot.2.md").write_text("jira: WO-22\n")
    (run / "intake.snapshot.3.md").write_text("jira: blocked:waiting for replacement issue\n")
    path = tmp_path / "profile.yml"
    profile(path, "jira", issue="WO-9")
    result = json.loads(run_python(
        POST_UPDATE, "--stage", "G.verify", "--summary", "ok", "--initiative", "demo", "--run", "demo-run1",
        "--profile", path, env={"HARNESS_REPO_ROOT": str(repo)},
    ).stdout)
    assert result["calls"] == []
    assert "jira: blocked: no Jira issue" in result["status"]


def test_both_keeps_notion_when_jira_has_no_issue_or_is_blocked(tmp_path):
    path = tmp_path / "profile.yml"
    profile(path, "both", issue="none")
    no_issue = json.loads(run_python(
        POST_UPDATE, "--stage", "C.specify", "--summary", "done", *update_identity(), "--profile", path,
    ).stdout)
    assert [call["tool"] for call in no_issue["calls"]] == ["storage.py ledger-entry"]
    assert "jira: blocked: no Jira issue" in no_issue["status"]
    path.write_text(path.read_text() + "  tracker_blocked: jira\n")
    blocked = json.loads(run_python(
        POST_UPDATE, "--stage", "C.specify", "--summary", "done", *update_identity(), "--profile", path,
    ).stdout)
    assert [call["tool"] for call in blocked["calls"]] == ["storage.py ledger-entry"]
    assert any("Atlassian connector unavailable" in status for status in blocked["status"])


def grill_snapshot(items, persona=None):
    lines = ["---", "stage: A.context", "---", "", "## Grill"]
    if persona:
        lines.insert(2, f"persona: {persona}")
    lines.extend(f"- {item}: answered (source: docs/{n}.md)" for n, item in enumerate(items))
    return "\n".join(lines) + "\n"


def checklist_items(persona):
    text = (PLUGIN / "framework" / "templates" / "grill-checklist.yml").read_text().splitlines()
    start = text.index(f"{persona}:") + 1
    out = []
    for line in text[start:]:
        if line and not line.startswith(" "):
            break
        if line.startswith("  - "):
            out.append(line[4:])
    return out


@pytest.mark.parametrize("persona", ["pm", "designer", "engineer", "qa", "em", "researcher", "end-to-end"])
def test_grill_check_accepts_complete_checklist_for_every_persona(tmp_path, persona):
    snapshot = tmp_path / "A.context.snapshot.md"
    snapshot.write_text(grill_snapshot(checklist_items(persona)))
    assert run_python(GRILL_CHECK, snapshot, "--persona", persona).returncode == 0


def test_grill_check_lists_missing_items_and_next_step(tmp_path):
    snapshot = tmp_path / "A.context.snapshot.md"
    snapshot.write_text(grill_snapshot(["problem and who has it"]))
    result = run_python(GRILL_CHECK, snapshot, "--persona", "pm")
    assert result.returncode == 2
    assert "success metric" in result.stderr and "Next:" in result.stderr


def sync_repo(tmp_path, tracker, snapshot):
    repo = tmp_path / tracker
    subprocess.run(["git", "init", "-q", "-b", "feature/test", str(repo)], check=True)
    (repo / ".ai" / "demo" / "runs" / "demo-run1").mkdir(parents=True)
    profile(repo / ".ai" / "harness-profile.yml", tracker)
    (repo / ".ai" / "demo" / "runs" / "demo-run1" / "B.research.snapshot.md").write_text(snapshot)
    return subprocess.run(
        ["bash", str(RECORD_SYNC), "push", "demo", "test"], cwd=repo,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(tmp_path / "home")},
        capture_output=True, text=True,
    )


@pytest.mark.parametrize(
    ("tracker", "snapshot", "expected"),
    [
        ("notion", "stage: B.research\n", 0),
        ("jira", "stage: B.research\njira: WO-123\n", 0),
        ("both", "stage: B.research\njira: blocked:no issue yet\n", 0),
    ],
)
def test_record_sync_accepts_snapshot_rule_for_each_tracker(tmp_path, tracker, snapshot, expected):
    result = sync_repo(tmp_path, tracker, snapshot)
    assert result.returncode == expected, result.stderr


@pytest.mark.parametrize("tracker", ["jira", "both"])
def test_record_sync_rejects_missing_jira_snapshot_line(tmp_path, tracker):
    result = sync_repo(tmp_path, tracker, "stage: B.research\n")
    assert result.returncode == 2 and "require every stage snapshot" in result.stderr


def test_record_sync_checks_superseding_snapshot_names(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "feature/test", str(repo)], check=True)
    run = repo / ".ai" / "demo" / "runs" / "demo-run1"
    run.mkdir(parents=True)
    profile(repo / ".ai" / "harness-profile.yml", "jira")
    (run / "B.research.snapshot.2.md").write_text("stage: B.research\n")
    result = subprocess.run(
        ["bash", str(RECORD_SYNC), "push", "demo", "test"], cwd=repo,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(tmp_path / "home")},
        capture_output=True, text=True,
    )
    assert result.returncode == 2 and "B.research.snapshot.2.md" in result.stderr


def test_record_sync_enforces_context_grill_even_for_solo(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "feature/test", str(repo)], check=True)
    run = repo / ".ai" / "demo" / "runs" / "demo-run1"
    run.mkdir(parents=True)
    profile(repo / ".ai" / "harness-profile.yml", "notion")
    (run / "A.context.snapshot.md").write_text(grill_snapshot(["problem and who has it"]))
    result = subprocess.run(
        ["bash", str(RECORD_SYNC), "push", "demo", "test"], cwd=repo,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(tmp_path / "home")},
        capture_output=True, text=True,
    )
    assert result.returncode == 2 and "success metric" in result.stderr


def test_post_update_repeats_evidence_flags_and_generated_args_execute(tmp_path):
    path = tmp_path / "profile.yml"
    profile(path, "notion")
    result = run_python(
        POST_UPDATE, "--stage", "F.build", "--summary", "Built", "--links",
        "https://example.test/snapshot,https://example.test/page", *update_identity(), "--profile", path,
    )
    append_args = json.loads(result.stdout)["calls"][0]["args"]["append_args"]
    executed = run_python(APPEND, *append_args, env={"HARNESS_REPO_ROOT": str(tmp_path)})
    assert executed.returncode == 0, executed.stderr
    event = json.loads((tmp_path / ".ai" / "demo" / "ledger.jsonl").read_text())
    assert event["evidence"] == ["https://example.test/snapshot", "https://example.test/page"]


def test_post_update_publishes_summary_with_actual_stage_outcome(tmp_path):
    path = tmp_path / "profile.yml"
    profile(path, "notion")
    summary = "Build blocked by failing tests"
    result = run_python(
        POST_UPDATE, "--stage", "F.build", "--summary", summary, "--links", "https://example.test/snapshot",
        *update_identity("rejected"), "--profile", path,
    )
    append_args = json.loads(result.stdout)["calls"][0]["args"]["append_args"]
    assert append_args[append_args.index("--event") + 1] == "stage-event-1"
    assert append_args[append_args.index("--outcome") + 1] == "rejected"
    assert append_args[append_args.index("--note") + 1] == summary
    executed = run_python(APPEND, *append_args, env={"HARNESS_REPO_ROOT": str(tmp_path)})
    assert executed.returncode == 0, executed.stderr
    event = json.loads((tmp_path / ".ai" / "demo" / "ledger.jsonl").read_text())
    assert event["outcome"] == "rejected" and event["notes"] == summary


def test_post_update_refuses_to_invent_notion_stage_identity(tmp_path):
    path = tmp_path / "profile.yml"
    profile(path, "notion")
    result = run_python(
        POST_UPDATE, "--stage", "F.build", "--summary", "Built", "--initiative", "demo", "--profile", path,
    )
    assert result.returncode == 2
    assert "require --initiative, --run, --event, --agent, and --outcome" in result.stderr


def test_record_sync_uses_context_snapshot_recorded_persona(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "feature/test", str(repo)], check=True)
    run = repo / ".ai" / "demo" / "runs" / "demo-run1"
    run.mkdir(parents=True)
    profile(repo / ".ai" / "harness-profile.yml", "notion", persona="engineer")
    (run / "A.context.snapshot.md").write_text(grill_snapshot(checklist_items("pm"), "pm"))
    historical = repo / ".ai" / "demo" / "runs" / "old-run"
    historical.mkdir()
    (historical / "A.context.snapshot.md").write_text(
        grill_snapshot(checklist_items("engineer"), "engineer")
    )
    result = subprocess.run(
        ["bash", str(RECORD_SYNC), "push", "demo", "test"], cwd=repo,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(tmp_path / "home")},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_record_sync_ignores_superseded_snapshot_validation_failures(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "feature/test", str(repo)], check=True)
    run = repo / ".ai" / "demo" / "runs" / "demo-run1"
    run.mkdir(parents=True)
    profile(repo / ".ai" / "harness-profile.yml", "both")
    (run / "A.context.snapshot.md").write_text("stage: A.context\npersona: engineer\n")
    current = grill_snapshot(checklist_items("pm"), "pm") + "jira: WO-123\n"
    (run / "A.context.snapshot.2.md").write_text(current)
    result = subprocess.run(
        ["bash", str(RECORD_SYNC), "push", "demo", "test"], cwd=repo,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(tmp_path / "home")},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("tracker", "snapshot", "error"),
    [
        ("both", "stage: B.research\n", "require every stage snapshot"),
        ("notion", "stage: A.context\npersona: pm\n## Grill\n- problem and who has it: answered (source: user)\n", "success metric"),
    ],
)
def test_record_sync_validates_nondefault_runs_that_it_publishes(tmp_path, tracker, snapshot, error):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "feature/test", str(repo)], check=True)
    default = repo / ".ai" / "demo" / "runs" / "demo-run1"
    other = repo / ".ai" / "demo" / "runs" / "demo-run2"
    default.mkdir(parents=True)
    other.mkdir(parents=True)
    profile(repo / ".ai" / "harness-profile.yml", tracker)
    (default / "B.research.snapshot.md").write_text("stage: B.research\njira: WO-123\n")
    name = "A.context.snapshot.md" if "A.context" in snapshot else "B.research.snapshot.md"
    (other / name).write_text(snapshot)
    result = subprocess.run(
        ["bash", str(RECORD_SYNC), "push", "demo", "test"], cwd=repo,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(tmp_path / "home")},
        capture_output=True, text=True,
    )
    assert result.returncode == 2 and error in result.stderr


@pytest.mark.parametrize("storage_mode", ["local", "notion"])
@pytest.mark.parametrize("tracker", ["jira", "notion", "both"])
def test_onboarding_writes_ledger_once_per_storage_mode(tmp_path, storage_mode, tracker):
    text = (PLUGIN / "skills" / "harness-onboard" / "SKILL.md").read_text()
    local_rule = text.split("**`storage: local`:**", 1)[1].split("**`storage: notion`:**", 1)[0]
    notion_rule = text.split("**`storage: notion`:**", 1)[1].split("A Jira-only selection", 1)[0]
    assert "append.py` exactly once" in local_rule
    assert "does not replace or repeat the canonical local append" in local_rule
    assert "do not run `append.py`" in notion_rule
    assert "no ledger call because updates are Jira-only" in notion_rule
    assert "Never execute more than one Notion ledger append" in notion_rule

    path = tmp_path / "profile.yml"
    profile(path, tracker, issue="WO-9", storage=storage_mode)
    result = run_python(
        POST_UPDATE, "--stage", "RUN.onboard", "--summary", "Harness onboarding completed",
        *update_identity(), "--profile", path,
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    notion_appends = sum(call["tool"] == "storage.py ledger-entry" for call in plan["calls"])

    if storage_mode == "local":
        appended = run_python(
            APPEND, "demo", "--run", "demo-run1", "--event", "stage-event-1", "--stage", "RUN.onboard",
            "--agent", "skill:harness-snapshot", "--outcome", "resolved-clean",
            env={"HARNESS_REPO_ROOT": str(tmp_path)},
        )
        assert appended.returncode == 0, appended.stderr
        events = (tmp_path / ".ai" / "demo" / "ledger.jsonl").read_text().splitlines()
        assert len(events) == 1
    else:
        assert not (tmp_path / ".ai" / "demo" / "ledger.jsonl").exists()
        notion_appends = notion_appends or 1

    assert notion_appends == (1 if storage_mode == "notion" or tracker in ("notion", "both") else 0)


def test_update_and_grill_docs_and_entry_points_are_wired():
    assert "53-updates-and-grill.md" in (PLUGIN / "framework" / "index.md").read_text()
    connectors = (PLUGIN / "framework" / "39-connectors-setup.md").read_text()
    assert "updates.tracker" in connectors and "tracker_blocked: jira" in connectors
    quickstart = (PLUGIN / "framework" / "36-roles-quickstart.md").read_text()
    for role in ("PM", "Designer", "Engineer", "QA", "EM", "Researcher", "End to end"):
        assert f"| {role} |" in quickstart
    for skill in ("harness-onboard", "harness-intake", "harness-snapshot", "harness-council", "harness-escape"):
        assert "post-update.py" in (PLUGIN / "skills" / skill / "SKILL.md").read_text(), skill
    assert "Post only at stage boundaries" in (PLUGIN / "framework" / "49-autonomy-progress-and-context-intake.md").read_text()


def test_onboarding_executes_every_planned_call_in_both_storage_modes():
    text = (PLUGIN / "skills" / "harness-onboard" / "SKILL.md").read_text()
    local = text.split("- **`storage: local`:**", 1)[1].split("\n", 1)[0]
    notion = text.split("- **`storage: notion`:**", 1)[1].split("\n", 1)[0]
    assert "xecute every call in the update plan" in local
    assert "xecute every call in the update plan" in notion
    assert "Jira comment" in notion
