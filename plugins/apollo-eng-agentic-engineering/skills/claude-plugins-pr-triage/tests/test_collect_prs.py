from __future__ import annotations

from datetime import date

import pytest

cp = pytest.importorskip("collect_prs")

CODEOWNERS = """
* @o/devops @o/ae
plugins/apollo-gtm/ @o/devops @o/gtm
plugins/apollo-gtm/skills/x/ @o/gtm-x
/skill-review-rubric.md @o/it
"""


def run(conclusion=None, status="COMPLETED"):
    return {"__typename": "CheckRun", "conclusion": conclusion, "status": status}


def test_checks_green_failing_pending():
    assert cp.checks_status([run("SUCCESS"), run("SKIPPED")]) == "green"
    assert cp.checks_status([run("SUCCESS"), run("TIMED_OUT")]) == "failing"
    assert cp.checks_status([run(None, "IN_PROGRESS")]) == "pending"
    assert cp.checks_status([]) == "green"


def test_checks_status_context():
    ok = {"__typename": "StatusContext", "state": "SUCCESS"}
    bad = {"__typename": "StatusContext", "state": "ERROR"}
    coderabbit = {"__typename": "StatusContext", "state": "PENDING"}
    assert cp.checks_status([ok, run("SUCCESS")]) == "green"
    assert cp.checks_status([bad]) == "failing"
    assert cp.checks_status([coderabbit, run("SUCCESS")]) == "green"


def test_owner_longest_prefix_and_fallback():
    rules = cp.parse_codeowners(CODEOWNERS)
    assert cp.owners_for_path(rules, "plugins/apollo-gtm/a.md") == ["@o/devops", "@o/gtm"]
    assert cp.owners_for_path(rules, "plugins/apollo-gtm/skills/x/SKILL.md") == ["@o/gtm-x"]
    assert cp.owners_for_path(rules, "plugins/other/a.md") == ["@o/devops", "@o/ae"]


def test_owner_union_ignores_shared_files():
    rules = cp.parse_codeowners(CODEOWNERS)
    paths = ["README.md", "plugins/apollo-gtm/a.md", "plugins/apollo-gtm/skills/x/b.md",
             ".claude-plugin/marketplace.json"]
    assert cp.pr_owners(rules, paths) == ["@o/devops", "@o/gtm", "@o/gtm-x"]
    # only shared paths: fall back to them
    assert cp.pr_owners(rules, ["README.md"]) == ["@o/devops", "@o/ae"]


def test_last_commit_selection():
    commits = [{"committedDate": "2026-01-01T00:00:00Z"},
               {"committedDate": "2026-03-05T10:00:00Z"}]
    assert cp.last_commit_date(commits) == "2026-03-05T10:00:00Z"
    assert cp.last_commit_date([]) is None


def test_cutoff_42_days():
    assert cp.cutoff_date(date(2026, 10, 7)) == date(2026, 8, 26)


def test_approvals_newer_than_head():
    head = "2026-03-05T10:00:00Z"
    newer = [{"state": "APPROVED", "submittedAt": "2026-03-06T00:00:00Z"}]
    older = [{"state": "APPROVED", "submittedAt": "2026-03-01T00:00:00Z"}]
    changes = [{"state": "CHANGES_REQUESTED", "submittedAt": "2026-03-06T00:00:00Z"}]
    assert cp.approvals_newer_than_head(newer, head) is True
    assert cp.approvals_newer_than_head(older, head) is False
    assert cp.approvals_newer_than_head(changes, head) is False
    assert cp.approvals_newer_than_head(newer, None) is False


def test_stacked_on():
    heads = {"feat-a": 244}
    assert cp.stacked_on("main", heads) is None
    assert cp.stacked_on("feat-a", heads) == {"base": "feat-a", "pr": 244}
    assert cp.stacked_on("gone", heads) == {"base": "gone", "pr": None}


def test_build_record_stale_flag():
    pr = {"number": 1, "title": "t", "author": {"login": "a"}, "isDraft": False,
          "createdAt": "2026-01-01T00:00:00Z", "labels": [], "additions": 3,
          "baseRefName": "main", "mergeable": "MERGEABLE", "reviewDecision": None,
          "reviewRequests": []}
    detail = {"commits": [{"committedDate": "2026-06-01T00:00:00Z"}],
              "statusCheckRollup": [], "latestReviews": []}
    rec = cp.build_record(pr, detail, ["a.md"], [], {}, date(2026, 8, 26))
    assert rec["stale_candidate"] is True and rec["checks"] == "green"
