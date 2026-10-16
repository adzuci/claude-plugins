import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPLAY = ROOT / "plugins" / "apollo-product-lab" / "framework" / "eval" / "replay" / "ads-m1-human-reviews"
sys.path.insert(0, str(REPLAY))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPLAY / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rr = load("astra_run_replay", "run_replay.py")
bt = load("astra_build_tiers", "build_tiers.py")


def replay_case(cid="c1", **kw):
    data = {"id": cid, "pr": 1, "path": "a.rb", "line": 10, "category": "correctness/logic bug",
            "excerpt": "missing account validation before save", "expected_rules": ["B24"], "rule_gap": False, "url": "u",
            "match": {"same_file": True, "line_tolerance": 8,
                      "any_of": {"rules": ["B24"], "category": "correctness/logic bug"}}}
    data.update(kw)
    return data


def finding(**kw):
    data = {"file": "a.rb", "line": 10, "rule": "B24", "category": "correctness", "summary": "missing validation"}
    data.update(kw)
    return data


def score(cases, findings, outcomes, max_fp_rate=0.15):
    with tempfile.TemporaryDirectory() as tmp:
        cases_path = os.path.join(tmp, "cases.jsonl")
        with open(cases_path, "w") as handle:
            handle.write("".join(json.dumps(case) + "\n" for case in cases))
        outcomes_path = os.path.join(tmp, "outcomes.json")
        with open(outcomes_path, "w") as handle:
            json.dump([{"id": key, "outcome": value} for key, value in outcomes.items()], handle)
        findings_path = os.path.join(tmp, "findings.json")
        with open(findings_path, "w") as handle:
            json.dump(findings, handle)
        with open(os.path.join(tmp, "groups.json"), "w") as handle:
            json.dump([{"case_ids": [case["id"] for case in cases], "outputs": {"reviewer": findings_path}}], handle)
        args = type("Args", (), {"runs": tmp, "cases": cases_path, "outcomes": outcomes_path,
                                  "max_fp_rate": max_fp_rate})
        rr.cmd_score(args)
        with open(os.path.join(tmp, "report.json")) as handle:
            return json.load(handle)


def test_category_tiers_only_block_for_major_or_policy_categories():
    outcomes = [
        {"id": "d", "expected_rules": [], "category": "comments policy", "outcome": "fixed", "severity": "minor"},
        {"id": "x", "expected_rules": [], "category": "dead code/duplication/over-engineering", "outcome": "fixed", "severity": "nit"},
        {"id": "m", "expected_rules": [], "category": "security/permission", "outcome": "fixed", "severity": "major"},
        {"id": "p", "expected_rules": [], "category": "data model/index/query perf", "outcome": "declined"},
    ]
    tiers = bt.tiers(outcomes)
    assert tiers["category:docs"] == "warn"
    assert tiers["category:design"] == "warn"
    assert tiers["category:security"] == "block"
    assert tiers["category:perf"] == "block"


def test_from_outcomes_rebuild_is_offline():
    with tempfile.TemporaryDirectory() as tmp:
        outcomes_path = os.path.join(tmp, "outcomes.json")
        overrides_path = os.path.join(tmp, "overrides.json")
        tiers_path = os.path.join(tmp, "tiers.json")
        with open(outcomes_path, "w") as handle:
            json.dump([{"id": "x", "expected_rules": ["B1"], "category": "comments policy",
                        "outcome": "declined"}], handle)
        with open(overrides_path, "w") as handle:
            json.dump({}, handle)
        bt.rebuild_tiers_from_outcomes(outcomes_path, overrides_path, tiers_path)
        assert json.load(open(tiers_path)) == {"B1": "warn", "category:docs": "warn"}


def test_relabel_stored_uses_reply_and_moved_without_github():
    with tempfile.TemporaryDirectory() as tmp:
        outcomes_path = os.path.join(tmp, "outcomes.json")
        overrides_path = os.path.join(tmp, "overrides.json")
        tiers_path = os.path.join(tmp, "tiers.json")
        stored = [
            {"id": "n", "expected_rules": [], "category": "comments policy", "outcome": "fixed",
             "our_reply": "Not fixed in this PR", "moved": False},
            {"id": "d", "expected_rules": [], "category": "comments policy", "outcome": "fixed",
             "our_reply": "Will be fixed in a follow-up ticket", "moved": False},
            {"id": "f", "expected_rules": ["B1"], "category": "comments policy", "outcome": "declined",
             "our_reply": "Done, moved it", "moved": False},
            {"id": "u", "expected_rules": [], "category": "comments policy", "outcome": "fixed",
             "our_reply": "Thanks, looking into it", "moved": True},
        ]
        with open(outcomes_path, "w") as handle:
            json.dump(stored, handle)
        with open(overrides_path, "w") as handle:
            json.dump({}, handle)
        bt.relabel_stored(outcomes_path, overrides_path, tiers_path)
        got = {item["id"]: item["outcome"] for item in json.load(open(outcomes_path))}
        assert got == {"n": "declined", "d": "deferred", "f": "fixed", "u": "unknown"}
        assert json.load(open(tiers_path))["B1"] == "block"


def test_deferred_is_recall_and_never_creates_a_warn_tier():
    assert bt.classify({"comment_kind": "line"}, ["Will handle in a follow-up ticket later"], False) == "deferred"
    assert bt.classify({"comment_kind": "line"}, ["Will be fixed in a follow-up ticket"], False) == "deferred"
    assert bt.tiers([{"id": "d", "expected_rules": ["B1"], "category": "comments policy",
                      "outcome": "deferred", "severity": "minor"}]) == {}
    report = score([replay_case()], [finding()], {"c1": "deferred"})
    assert report["overall"]["total"] == 1
    assert report["should_not_flag"]["total"] == 0
    assert report["unknown_outcome"]["total"] == 0


def test_fix_at_start_beats_later_negative_words_and_overrides_are_reasoned():
    assert bt.classify({"comment_kind": "line"}, ["Fixed in abc; keeping the API name for later compatibility"], False) == "fixed"
    assert bt.classify({"comment_kind": "line"}, ["Not fixed in this PR"], False) == "declined"
    assert bt.classify({"comment_kind": "line"}, ["Done, moved it"], False) == "fixed"
    overrides = json.load(open(REPLAY / "outcomes-overrides.json"))
    for cid in ("ads-m1-4194688615", "ads-m1-4215132862"):
        assert overrides[cid]["outcome"] == "fixed"
        assert overrides[cid]["reason"]


def test_head_fetch_failure_returns_none_and_equal_timestamps_sort_by_ancestry():
    def failed(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])
    assert bt.head_for_pr(7, failed) is None
    commits = [
        {"sha": "b", "parents": [{"sha": "p"}], "commit": {"committer": {"date": "2026-01-02T00:00:00Z"}}},
        {"sha": "a", "parents": [{"sha": "b"}], "commit": {"committer": {"date": "2026-01-02T00:00:00Z"}}},
    ]
    assert bt.first_commit_after(commits, "2026-01-01T00:00:00Z") == ("b", "p")


def test_false_positive_gate_and_unrelated_category_claim_probe():
    case = replay_case(expected_rules=[], rule_gap=True)
    unrelated = finding(rule="", category="correctness", summary="pagination cursor loops forever")
    assert not rr.case_matches(case, unrelated)
    related = finding(rule="", category="correctness", summary="account validation is missing")
    assert rr.case_matches(case, related)
    report = score([case], [related], {"c1": "declined"})
    assert report["should_not_flag"]["rate"] == 1.0
    assert report["pass"] is False


def test_replay_routing_matches_skill_probe_paths():
    assert rr.route(["packs/ads/spec/models/a_spec.rb"], "") == ["backend-reviewer"]
    assert rr.route(["config/ads.yml"], "") == ["backend-reviewer"]
    assert rr.route(["packages/ads/config.yaml"], "") == ["backend-reviewer"]
    assert rr.route(["config/routes.rb"], "+  resources :accounts") == ["backend-reviewer", "security-reviewer"]
    assert rr.route(["config/routes.admin.rb"], "+  post '/admin'") == ["backend-reviewer", "security-reviewer"]
    skill = (ROOT / "plugins" / "apollo-product-lab" / "skills" / "code-review" / "SKILL.md").read_text()
    rows = {}
    for line in skill.splitlines():
        if line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows[cells[0].strip("`")] = cells[1]
    backend = rows["backend-reviewer"]
    assert "Ruby spec-only change" in backend
    assert "config/**/*.{rb,yml}" in backend


def test_replay_docs_are_honest_about_manual_status():
    replay_readme = (REPLAY / "README.md").read_text().lower()
    synth_readme = (ROOT / "plugins" / "apollo-product-lab" / "skills" / "code-review" / "eval" /
                    "synthesizer" / "README.md").read_text().lower()
    assert "run manually" in replay_readme and "does not gate merges" in replay_readme
    assert "manual" in synth_readme and "do not gate merges" in synth_readme


def test_review_gate_documents_astra_threat_model_boundary():
    gate = (ROOT / "plugins" / "apollo-product-lab" / "framework" / "50-review-gate.md").read_text().lower()
    assert "## threat model" in gate
    assert "honest mistakes" in gate and "old head" in gate and "wrong directory or pr" in gate
    assert "deliberate evasion" in gate and "forging review records" in gate
    assert "evasion-only bypasses as minor" in gate
