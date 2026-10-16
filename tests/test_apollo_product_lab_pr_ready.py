import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "plugins" / "apollo-product-lab" / "scripts" / "pr-ready.py"
spec = importlib.util.spec_from_file_location("pr_ready", SCRIPT)
pr_ready = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr_ready)

HEAD = "a" * 40
OLD = "b" * 40
FIX = "c" * 40


def finding(fid="F1", severity="major", category="design", disposition=None, **kw):
    f = {"id": fid, "severity": severity, "category": category, "file": "packs/ads/x.rb", "line": 42,
         "summary": "something is wrong", "disposition": disposition,
         "lens_severities": {"backend-reviewer": severity}}
    f.update(kw)
    return f


def record(head=HEAD, findings=None, verdict="REQUEST_CHANGES", **kw):
    r = {"schema": 2, "repo": "apolloio/leadgenie", "pr": 7, "head_sha": head,
         "reviewed_at": "2026-10-16T10:00:00Z", "verdict": verdict,
         "reviewers": ["backend-reviewer"], "findings": findings if findings is not None else []}
    r.update(kw)
    return r


class Env(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.ancestors = {FIX}
        self.addCleanup(self.tmp.cleanup)

    def write(self, rec, key="7", sha=None):
        d = os.path.join(self.root, ".harness", "reviews", key)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, (sha or rec["head_sha"]) + ".json"), "w") as f:
            json.dump(rec, f)

    def git(self, args, cwd=None):
        if args[:2] == ["cat-file", "-e"]:
            return 0, ""
        if args[:1] == ["show"]:
            return 0, "\n".join("line %s" % n for n in range(1, 101))
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return (0 if args[2] in self.ancestors else 1), ""
        if args[:2] == ["rev-list", "--count"]:
            return 0, "3"
        if args[:3] == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return 0, "akansh/feature"
        if args[:2] == ["rev-parse", "HEAD"]:
            return 0, HEAD
        if args[:2] == ["rev-parse", "--show-toplevel"]:
            return 0, self.root
        return 1, ""

    def gh(self, args, cwd=None):
        if args[:2] == ["repo", "view"]:
            return 0, json.dumps({"nameWithOwner": "apolloio/leadgenie"})
        return 0, json.dumps({"number": 7, "headRefOid": HEAD, "headRefName": "akansh/feature",
                              "baseRefName": "master", "url": "https://github.com/apolloio/leadgenie/pull/7",
                              "files": [{"path": "a.rb"}]})

    def gate(self, mode, **kw):
        options = dict(pr=7, mode=mode, repo_root=self.root, cwd=self.root, gh=self.gh, git=self.git, env={})
        options.update(kw)
        return pr_ready.gate(**options)


class FailReasons(Env):
    def both_modes(self, expect_text):
        for mode in ("block", "warn"):
            code, text, _ = self.gate(mode)
            self.assertEqual(code, 2, mode)
            self.assertIn(expect_text, text)
            self.assertIn("pr-ready BLOCKED", text)
            self.assertIn("1. ", text)

    def test_warn_tier_rule_only_warns_in_warn_mode(self):
        self.write(record(findings=[finding("F4", severity="minor", category="design", rule="P10")]))
        code, text, _ = pr_ready.gate(pr=7, mode="warn", repo_root=self.root, cwd=self.root, gh=self.gh, git=self.git, env={})
        self.assertEqual(code, 0)
        self.assertTrue(text.startswith("TRIAGE REQUIRED"))
        self.assertIn("before asking a human to review", text)
        self.assertIn("F4", text)
        self.assertEqual(self.gate("block")[0], 2)

    def test_block_tier_rule_blocks_even_as_a_nit(self):
        self.write(record(findings=[finding("F5", severity="nit", category="docs", rule="B24")]))
        self.assertEqual(self.gate("warn")[0], 2)

    def test_repo_tiers_override_the_plugin_default(self):
        os.makedirs(os.path.join(self.root, ".harness"), exist_ok=True)
        with open(os.path.join(self.root, ".harness", "rule-tiers.json"), "w") as f:
            json.dump({"B24": "warn"}, f)
        self.write(record(findings=[finding("F6", severity="minor", category="docs", rule="B24")]))
        self.assertEqual(self.gate("warn")[0], 0)

    def test_plugin_default_tiers_are_learned_from_history(self):
        tiers = pr_ready.load_tiers(None)
        self.assertEqual(tiers.get("B24"), "block")
        self.assertEqual(tiers.get("P10"), "warn")

    def test_no_record(self):
        self.both_modes("run the code-review skill on head " + HEAD)

    def test_astra_31_file_probe_blocks_only_in_block_mode(self):
        self.write(record())

        def many_files_gh(args, cwd=None):
            rc, out = self.gh(args, cwd)
            if args[:2] == ["pr", "view"]:
                data = json.loads(out)
                data["files"] = [{"path": "app/file_%02d.rb" % n} for n in range(31)]
                return rc, json.dumps(data)
            return rc, out

        block = self.gate("block", gh=many_files_gh)
        self.assertEqual(block[0], 2)
        self.assertIn("PR size is 31 review files", block[1])
        warn = self.gate("warn", gh=many_files_gh)
        self.assertEqual(warn[0], 0)
        self.assertIn("PR size is 31 review files", warn[1])

    def test_generated_files_use_the_build_stage_exclusions(self):
        self.write(record())
        files = ["app/file_%02d.rb" % n for n in range(30)] + [
            "Gemfile.lock", "db/schema.rb", "spec/fixtures/recording.json",
            "ui/__snapshots__/card.snap", "tmp/recorded_fixtures/request.yml",
        ]

        def generated_gh(args, cwd=None):
            rc, out = self.gh(args, cwd)
            if args[:2] == ["pr", "view"]:
                data = json.loads(out)
                data["files"] = [{"path": path} for path in files]
                return rc, json.dumps(data)
            return rc, out

        self.assertEqual(self.gate("block", gh=generated_gh)[0], 0)

    def test_size_waiver_requires_reason_and_approver(self):
        files = ["app/file_%02d.rb" % n for n in range(31)]

        def many_files_gh(args, cwd=None):
            rc, out = self.gh(args, cwd)
            if args[:2] == ["pr", "view"]:
                data = json.loads(out)
                data["files"] = [{"path": path} for path in files]
                return rc, json.dumps(data)
            return rc, out

        self.write(record(size_waiver={"reason": "mechanical rename cannot be split", "approver": "Ada"}))
        self.assertEqual(self.gate("block", gh=many_files_gh)[0], 0)
        self.write(record(size_waiver={"reason": "too short", "approver": "Ada"}))
        code, text, _ = self.gate("block", gh=many_files_gh)
        self.assertEqual(code, 2)
        self.assertIn("size_waiver is invalid", text)
        code, text, _ = self.gate("warn", gh=many_files_gh)
        self.assertEqual(code, 0)
        self.assertIn("size_waiver is invalid", text)

    def test_stale_record_reports_behind(self):
        self.write(record(head=OLD))
        self.both_modes("newest review is for " + OLD[:10])
        self.assertIn("3 commit(s) behind", self.gate("warn")[1])

    def test_incomplete_and_escalate(self):
        for v in ("INCOMPLETE", "ESCALATE_HUMAN"):
            self.write(record(verdict=v))
            self.both_modes("verdict is " + v)

    def test_untriaged_must_triage(self):
        self.write(record(findings=[finding("F3", severity="minor", category="correctness")]))
        self.both_modes("F3")
        self.both_modes("packs/ads/x.rb:42")
        self.both_modes("something is wrong")
        self.both_modes("triage F3")

    def test_untriaged_blocker_any_category(self):
        self.write(record(findings=[finding("F1", severity="blocker", category="design")]))
        self.assertEqual(self.gate("block")[0], 2)

    def test_minor_nit_outside_categories_may_stay_null(self):
        os.makedirs(os.path.join(self.root, ".harness"), exist_ok=True)
        with open(os.path.join(self.root, ".harness", "rule-tiers.json"), "w") as f:
            json.dump({}, f)
        self.write(record(findings=[finding("F1", severity="nit", category="design"), finding("F2", severity="minor", category="docs")]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_fixed_commit_not_ancestor(self):
        self.write(record(findings=[finding(disposition={"action": "fixed", "commit": OLD})]))
        self.both_modes("not an ancestor")

    def test_fixed_ancestor_ok(self):
        self.write(record(findings=[finding(disposition={"action": "fixed", "commit": FIX})]))
        code, text, _ = self.gate("block")
        self.assertEqual(code, 0)
        self.assertTrue(text.startswith("pr-ready OK"))

    def test_wont_fix_without_reason(self):
        for disp in ({"action": "wont_fix", "rebuttal": False},
                     {"action": "wont_fix", "reason": "too short", "rebuttal": False}):
            self.write(record(findings=[finding(disposition=disp)]))
            self.both_modes("wont_fix without a reason")

    def test_wont_fix_and_deferred_ok(self):
        self.write(record(findings=[
            finding("F1", disposition={"action": "wont_fix", "reason": "intentional, matches existing behaviour",
                                       "rebuttal": False}),
            finding("F2", disposition={"action": "deferred", "ticket": "WO-1", "reason": "follow-up",
                                       "rebuttal": False})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_severity_downgrade_without_evidence_blocks(self):
        self.write(record(findings=[finding(
            "F2", severity="minor", lens_severities={"backend-reviewer": "blocker"},
            disposition={"action": "wont_fix", "reason": "intentional existing behavior", "rebuttal": False})]))
        self.both_modes("F2 is recorded minor but backend-reviewer rated it blocker, with no downgrade_evidence")

    def test_severity_downgrade_with_evidence_passes(self):
        self.write(record(findings=[finding(
            "F2", severity="minor", lens_severities={"backend-reviewer": "blocker"},
            downgrade_evidence={"file": "packs/ads/x.rb", "line": 42,
                                "why": "the guard makes this bounded"},
            disposition={"action": "wont_fix", "reason": "intentional existing behavior", "rebuttal": False})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_equal_lens_severity_passes(self):
        self.write(record(findings=[finding(
            "F2", severity="major", lens_severities={"backend-reviewer": "major"},
            disposition={"action": "wont_fix", "reason": "intentional existing behavior", "rebuttal": False})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_impossibility_claim_with_rebuttal_false_is_only_a_hint(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix", "reason": "can't batch the guarded update",
                               "rebuttal": False})]))
        for mode in ("warn", "block"):
            code, text, _ = self.gate(mode)
            self.assertEqual(code, 0)
            self.assertIn("reads like a technical rebuttal", text)

    def test_impossibility_claim_with_evidence_passes(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix", "reason": "can't batch the guarded update",
                               "rebuttal": True,
                               "evidence": "packs/ads/x.rb:42 shows callbacks are preserved"})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_curly_quote_technical_rebuttal_is_detected_as_a_hint(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix", "reason": "We can’t safely bulk this query",
                               "rebuttal": False})]))
        self.assertIn("reads like a technical rebuttal", self.gate("warn")[1])

    def test_reversed_technical_rebuttal_is_detected_as_a_hint(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix",
                               "reason": "Batching is impossible with these callbacks", "rebuttal": False})]))
        code, text, _ = self.gate("warn")
        self.assertEqual(code, 0)
        self.assertIn("reads like a technical rebuttal", text)

    def test_scheduling_cannot_is_not_a_technical_rebuttal(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix",
                               "reason": "Cannot schedule this until the migration finishes", "rebuttal": False})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_rebuttal_true_requires_typed_evidence(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix", "reason": "The index already handles this",
                               "rebuttal": True})]))
        self.both_modes("rebuttal:true without valid evidence")

    def test_current_schema_requires_valid_lens_severities_in_both_modes(self):
        for value in (None, [], {}, {"": "major"}, {"backend-reviewer": "urgent"}):
            item = finding()
            item["lens_severities"] = value
            self.write(record(findings=[item]))
            self.both_modes("invalid lens_severities")

    def test_invalid_lens_severities_never_raise_or_exit_zero(self):
        item = finding()
        item["lens_severities"] = {"backend-reviewer": ["major"]}
        self.write(record(findings=[item]))
        for mode in ("warn", "block"):
            code, text, _ = self.gate(mode)
            self.assertEqual(code, 2)
            self.assertIn("invalid lens_severities", text)

    def test_old_schema_is_accepted_with_rerun_warning(self):
        item = finding(severity="nit", category="docs", disposition={"action": "fixed", "commit": FIX})
        item.pop("lens_severities")
        self.write(record(schema=1, findings=[item]))
        code, text, _ = self.gate("warn")
        self.assertEqual(code, 0)
        self.assertIn("Re-run the review", text)
        self.assertEqual(self.gate("block")[0], 2)

    def test_downgrade_evidence_must_be_typed(self):
        bad = ["packs/ads/x.rb:42 because bounded", {},
               {"file": "", "line": 42, "why": "long enough explanation"},
               {"file": "none", "line": 42, "why": "long enough explanation"},
               {"file": "x.rb", "line": 0, "why": "long enough explanation"},
               {"file": "x.rb", "line": True, "why": "long enough explanation"},
               {"file": "x.rb", "line": 1, "why": "too short"}]
        for value in bad:
            self.write(record(findings=[finding(downgrade_evidence=value)]))
            self.both_modes("invalid downgrade_evidence")

    def test_disposition_evidence_requires_supported_non_placeholder_string(self):
        bad = ["TODO", "n/a", "true", "a long but unlocated explanation", "x.rb:1"]
        for value in bad:
            self.write(record(findings=[finding(disposition={
                "action": "wont_fix", "reason": "intentional existing behavior", "rebuttal": False,
                "evidence": value})]))
            self.both_modes("invalid disposition.evidence")

    def test_rebuttal_field_must_be_boolean(self):
        self.write(record(findings=[finding(disposition={
            "action": "wont_fix", "reason": "intentional existing behavior", "rebuttal": "true"})]))
        self.both_modes("invalid disposition.rebuttal")

    def test_disposition_evidence_accepts_path_url_explain_and_index(self):
        values = ["packs/ads/x.rb:42 shows the relevant implementation",
                  "https://example.com/design-note documents the decision",
                  "explain: IXSCAN examines only the bounded page",
                  "index: team_id_1_status_1 covers the complete filter"]
        for value in values:
            self.write(record(findings=[finding(disposition={
                "action": "wont_fix", "reason": "intentional existing behavior", "rebuttal": False,
                "evidence": value})]))
            self.assertEqual(self.gate("block")[0], 0)

    def test_wont_fix_and_deferred_require_explicit_rebuttal_boolean(self):
        for disposition in ({"action": "wont_fix", "reason": "accepted maintenance cost"},
                            {"action": "deferred", "ticket": "WO-1", "reason": "scheduled follow-up"}):
            self.write(record(findings=[finding(disposition=disposition)]))
            self.both_modes("must set disposition.rebuttal to true or false")

    def test_ordinary_wont_fix_reason_needs_no_evidence(self):
        self.write(record(findings=[finding(
            "F3", disposition={"action": "wont_fix", "reason": "intentional existing behavior",
                               "rebuttal": False})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_numbered_list_multiple(self):
        self.write(record(findings=[finding("F1", severity="blocker"), finding("F2", severity="major")]))
        text = self.gate("block")[1]
        self.assertIn("1. ", text)
        self.assertIn("2. ", text)

    def test_delta_record_for_new_head(self):
        self.write(record(head=OLD, findings=[finding("F1", severity="blocker")]))
        delta = record(head=HEAD, delta_of=OLD, findings=[finding("F1", severity="blocker", disposition={"action": "fixed", "commit": FIX})])
        self.write(delta)
        code, text, _ = self.gate("block")
        self.assertEqual(code, 0, text)

    def test_delta_record_carrying_untriaged_still_fails(self):
        self.write(record(head=HEAD, delta_of=OLD, findings=[finding("F1", severity="blocker")]))
        self.assertEqual(self.gate("block")[0], 2)

    def test_delta_record_blocks_dropped_or_changed_prior_provenance(self):
        prior = record(head=OLD, findings=[finding(
            "F1", severity="blocker", lens_severities={"backend-reviewer": "blocker"},
            disposition={"action": "wont_fix", "reason": "accepted maintenance cost", "rebuttal": False})])
        self.write(prior)
        cases = [
            ([], "dropped prior finding F1"),
            ([finding("F1", severity="minor", lens_severities={"backend-reviewer": "minor"},
                      disposition={"action": "wont_fix", "reason": "accepted maintenance cost",
                                   "rebuttal": False})], "changed F1's severity or lens_severities"),
        ]
        for findings, message in cases:
            self.write(record(delta_of=OLD, findings=findings))
            self.both_modes(message)

    def test_delta_record_allows_provenance_change_with_checked_downgrade_evidence(self):
        self.write(record(head=OLD, findings=[finding(
            "F1", severity="blocker", lens_severities={"backend-reviewer": "blocker"})]))
        self.write(record(delta_of=OLD, findings=[finding(
            "F1", severity="minor", lens_severities={"backend-reviewer": "minor"},
            downgrade_evidence={"file": "packs/ads/x.rb", "line": 42,
                                "why": "the bounded guard refutes the prior rating"},
            disposition={"action": "fixed", "commit": FIX})]))
        self.assertEqual(self.gate("block")[0], 0)

    def test_delta_record_loads_the_exact_delta_of_sibling(self):
        self.write(record(delta_of=OLD))
        code, text, _ = self.gate("warn")
        self.assertEqual(code, 2)
        self.assertIn("prior review it builds on is missing, invalid or incomplete", text)

    def test_delta_requires_a_valid_completed_prior_review(self):
        current = record(delta_of=OLD)
        cases = (
            None,
            record(head=FIX),
            record(head=OLD, schema=True),
            record(head=OLD, verdict="INCOMPLETE"),
            record(head=OLD, verdict="ESCALATE_HUMAN"),
        )
        for prior in cases:
            with self.subTest(prior=prior):
                self.write(current)
                if prior is not None:
                    self.write(prior, sha=OLD)
                self.both_modes(
                    "Next: re-run a full review; the prior review it builds on is missing, invalid or incomplete.")

    def test_snapshot_evidence_must_exist_and_line_must_be_in_range(self):
        def snapshot_git(args, cwd=None):
            if args[:2] == ["cat-file", "-e"]:
                return (1, "") if args[2].endswith(":missing.rb") else (0, "")
            if args[:1] == ["show"]:
                return 0, "one\ntwo\nthree"
            return self.git(args, cwd)

        invalid = [
            finding(downgrade_evidence={"file": "missing.rb", "line": 1,
                                        "why": "the snapshot refutes the higher rating"}),
            finding(disposition={"action": "wont_fix", "reason": "the finding is already handled",
                                 "rebuttal": True, "evidence": "packs/ads/x.rb:99 shows the guard"}),
        ]
        for item in invalid:
            self.write(record(findings=[item]))
            for mode in ("warn", "block"):
                code, text, _ = self.gate(mode, git=snapshot_git)
                self.assertEqual(code, 2)
                self.assertIn("invalid", text)

    def test_snapshot_line_count_keeps_leading_blank_lines(self):
        result = mock.Mock(returncode=0, stdout="\n\nthird\nfourth")
        with mock.patch.object(pr_ready.subprocess, "run", return_value=result):
            self.assertIsNone(pr_ready.snapshot_reference_problem(
                "packs/ads/x.rb", 4, HEAD, self.root, pr_ready.default_git))
            problem = pr_ready.snapshot_reference_problem(
                "packs/ads/x.rb", 5, HEAD, self.root, pr_ready.default_git)
        self.assertIn("outside the file's 4 lines", problem)

    def test_repeated_placeholder_evidence_is_rejected(self):
        item = finding(
            downgrade_evidence={"file": "packs/ads/x.rb", "line": 1, "why": "TODO TODO TODO TODO"},
            disposition={"action": "wont_fix", "reason": "the finding is already handled", "rebuttal": True,
                         "evidence": "explain: TODO TODO TODO"})
        self.write(record(findings=[item]))
        self.both_modes("invalid downgrade_evidence")
        self.both_modes("invalid disposition.evidence")

    def test_unresolvable_pr_fails_closed_in_block_mode(self):
        code, text, _ = pr_ready.gate(pr=7, mode="block", repo_root=self.root, cwd=self.root, gh=lambda a, c=None: (1, ""), git=self.git, env={})
        self.assertEqual(code, 2)
        self.assertIn("could not run", text)

    def test_creating_uses_branch_record(self):
        def git(args, cwd=None):
            if args[:2] == ["diff", "--name-only"]:
                return 0, "a.rb"
            return self.git(args, cwd)

        code, text, _ = pr_ready.gate(mode="block", repo_root=self.root, cwd=self.root, creating=True, git=git, env={})
        self.assertEqual(code, 2)
        self.assertIn("branch-akansh__feature", text)
        self.assertIn("--draft", text)
        self.write(record(), key="branch-akansh__feature")
        self.assertEqual(pr_ready.gate(mode="block", repo_root=self.root, cwd=self.root, creating=True, git=git, env={})[0], 0)

    def test_creating_fails_closed_when_explicit_base_diff_is_unavailable(self):
        self.write(record(), key="branch-akansh__feature")

        def git(args, cwd=None):
            if args[:2] == ["diff", "--name-only"]:
                if args[2].startswith("origin/HEAD..."):
                    return 0, "a.rb"
                return 1, ""
            return self.git(args, cwd)

        code, text, _ = pr_ready.gate(mode="block", repo_root=self.root, cwd=self.root, creating=True,
                                      create_base="main", gh=self.gh, git=git, env={})
        self.assertEqual(code, 2)
        self.assertIn("Next: fetch the base branch", text)

    def test_create_scan_carries_the_explicit_base_to_the_gate(self):
        hit = pr_ready.scan("gh pr create --base main --head topic")[0]
        self.assertEqual(hit["base"], "main")


class ModeResolution(Env):
    def test_default_warn(self):
        self.assertEqual(pr_ready.resolve_mode(None, {}, self.root), "warn")

    def test_config_file(self):
        os.makedirs(os.path.join(self.root, ".harness"))
        with open(os.path.join(self.root, ".harness", "config.json"), "w") as f:
            json.dump({"pr_ready_mode": "block"}, f)
        self.assertEqual(pr_ready.resolve_mode(None, {}, self.root), "block")

    def test_env_beats_config(self):
        os.makedirs(os.path.join(self.root, ".harness"))
        with open(os.path.join(self.root, ".harness", "config.json"), "w") as f:
            json.dump({"pr_ready_mode": "block"}, f)
        self.assertEqual(pr_ready.resolve_mode(None, {"HARNESS_PR_READY_MODE": "warn"}, self.root), "warn")

    def test_flag_beats_env(self):
        self.assertEqual(pr_ready.resolve_mode("block", {"HARNESS_PR_READY_MODE": "warn"}, self.root), "block")

    def test_invalid_values_ignored(self):
        self.assertEqual(pr_ready.resolve_mode("loud", {"HARNESS_PR_READY_MODE": "x"}, self.root), "warn")


class Detector(unittest.TestCase):
    def kinds(self, cmd):
        return [k for k, _ in pr_ready.detect_gated(cmd)]

    def test_positive(self):
        self.assertEqual(self.kinds("gh pr create --title x --body y"), ["create"])
        self.assertEqual(self.kinds("gh pr ready 12"), ["ready"])
        self.assertEqual(self.kinds("gh pr edit 12 --add-reviewer bob"), ["edit"])
        self.assertEqual(self.kinds("gh pr edit --add-reviewer=bob"), ["edit"])
        self.assertEqual(self.kinds("gh pr merge 12 --squash"), ["merge"])
        self.assertEqual(self.kinds("gh -R apolloio/leadgenie pr merge 12"), ["merge"])

    def test_negative(self):
        for cmd in ["gh pr view 12", "gh pr list", "gh pr edit 12 --title x", "gh pr checks", "git push",
                    "gh pr create --draft --title x", "gh pr create -d", "gh pr create -t x -d",
                    "gh pr ready --undo 12", "gh issue create", "ls"]:
            self.assertEqual(self.kinds(cmd), [], cmd)

    def test_chained(self):
        self.assertEqual(self.kinds("git push && gh pr create --fill"), ["create"])
        self.assertEqual(self.kinds("git push; gh pr ready 3"), ["ready"])
        self.assertEqual(self.kinds("gh pr create --draft && gh pr merge 3"), ["merge"])
        self.assertEqual(self.kinds("gh pr ready 3 && gh pr merge 3"), ["ready", "merge"])
        self.assertEqual(self.kinds("true || gh pr merge 4"), ["merge"])

    def test_draft_exemption_only_for_create(self):
        self.assertEqual(self.kinds("gh pr create --draft --fill"), [])
        self.assertEqual(self.kinds("gh pr create --fill"), ["create"])

    def test_pr_argument_parsing(self):
        self.assertEqual(pr_ready.detect_gated("gh pr merge 12 --squash"), [("merge", "12")])
        self.assertEqual(pr_ready.pr_number_from_arg("https://github.com/a/b/pull/55"), 55)
        self.assertIsNone(pr_ready.pr_number_from_arg("feature-branch"))

    def test_quoted_separator_not_split(self):
        self.assertEqual(self.kinds('gh pr create --draft --title "a && gh pr merge"'), ["unresolved"])


class Hook(Env):
    def payload(self, cmd, tool="Bash"):
        return {"tool_name": tool, "cwd": self.root, "tool_input": {"command": cmd}}

    def deps(self, mode):
        return dict(mode=mode, repo_root=self.root, gh=self.gh, git=self.git, env={})

    def test_ignores_other_tools_and_commands(self):
        self.assertEqual(pr_ready.hook(self.payload("gh pr merge 7", tool="Read"), **self.deps("block")), (0, "", ""))
        self.assertEqual(pr_ready.hook(self.payload("ls"), **self.deps("block")), (0, "", ""))

    def test_block_mode_exit_2_stderr(self):
        code, out, err = pr_ready.hook(self.payload("gh pr ready 7"), **self.deps("block"))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("BLOCKED", err)

    def test_warn_mode_missing_review_blocks(self):
        code, out, err = pr_ready.hook(self.payload("gh pr merge 7"), **self.deps("warn"))
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED", err)

    def test_warn_mode_adds_context_without_blocking(self):
        self.write(record(findings=[finding("F4", severity="minor", category="design", rule="B40")]))
        for _ in range(2):
            code, out, err = pr_ready.hook(self.payload("gh pr ready 7"), **self.deps("warn"))
            self.assertEqual((code, err), (0, ""))
            data = json.loads(out)["hookSpecificOutput"]
            self.assertEqual(data["hookEventName"], "PreToolUse")
            self.assertIn("TRIAGE REQUIRED", data["additionalContext"])
            self.assertIn("F4", data["additionalContext"])

    def test_clean_is_silent(self):
        self.write(record())
        self.assertEqual(pr_ready.hook(self.payload("gh pr ready 7"), **self.deps("block")), (0, "", ""))

    def test_chained_command_gated_old(self):
        code, _, _ = pr_ready.hook(self.payload("git push && gh pr merge 7"), **self.deps("block"))
        self.assertEqual(code, 2)


class SeverityAndCategoryTiers(Env):
    def gate_warn(self):
        return self.gate("warn")

    def test_blocker_blocks_even_with_a_warn_rule_tier(self):
        for sev in ("blocker", "major"):
            self.write(record(findings=[finding("F1", severity=sev, category="design", rule="B40")]))
            self.assertEqual(self.gate_warn()[0], 2, sev)

    def test_rule_id_field_is_read(self):
        self.write(record(findings=[finding("F1", severity="minor", category="design", rule=None, rule_id="B40")]))
        code, text, _ = self.gate_warn()
        self.assertEqual((code, text.startswith("TRIAGE REQUIRED")), (0, True))

    def test_category_tier_used_when_rule_has_no_tier(self):
        tiers = {"category:design": "warn", "category:perf": "block"}
        self.assertEqual(pr_ready.finding_tier(finding(severity="minor", category="design", rule="ZZ9"), tiers), "warn")
        self.assertEqual(pr_ready.finding_tier(finding(severity="nit", category="perf"), tiers), "block")
        self.assertEqual(pr_ready.finding_tier(finding(severity="nit", category="docs"), tiers), None)

    def test_category_tier_does_not_override_a_rule_tier(self):
        tiers = {"B1": "block", "category:design": "warn"}
        self.assertEqual(pr_ready.finding_tier(finding(severity="minor", category="design", rule="B1"), tiers), "block")

    def test_category_tier_warn_beats_must_triage_default(self):
        tiers = {"category:correctness": "warn"}
        self.assertEqual(pr_ready.finding_tier(finding(severity="minor", category="correctness"), tiers), "warn")
        self.assertEqual(pr_ready.finding_tier(finding(severity="minor", category="correctness"), {}), "block")

    def test_shipped_tiers_have_no_warn_for_unknown_only_rules(self):
        tiers = pr_ready.load_tiers(None)
        self.assertTrue(any(k.startswith("category:") for k in tiers))


class RecordValidation(Env):
    def test_empty_object_is_no_valid_review(self):
        self.write({}, sha=HEAD)
        for mode in ("warn", "block"):
            code, text, _ = self.gate(mode)
            self.assertEqual(code, 2)
            self.assertIn("No valid AI review record", text)

    def test_record_for_another_head_under_this_filename(self):
        self.write(record(head=OLD), sha=HEAD)
        code, text, _ = self.gate("block")
        self.assertEqual(code, 2)
        self.assertIn("head_sha", text)

    def test_record_for_another_repo(self):
        self.write(record(repo="apolloio/other"))
        code, text, _ = self.gate("block")
        self.assertEqual(code, 2)
        self.assertIn("apolloio/other", text)

    def test_same_repo_any_case_ok(self):
        self.write(record(repo="ApolloIO/LeadGenie"))
        self.assertEqual(self.gate("block")[0], 0)

    def test_missing_required_fields(self):
        for field in ("schema", "verdict", "findings", "reviewers"):
            rec = record()
            del rec[field]
            self.write(rec)
            code, text, _ = self.gate("block")
            self.assertEqual(code, 2, field)
            self.assertIn("No valid AI review record", text)

    def test_empty_reviewers_rejected_for_non_docs_diff_only(self):
        self.write(record(reviewers=[]))
        self.assertEqual(self.gate("block")[0], 2)

        def docs_gh(args, cwd=None):
            if args[:2] == ["repo", "view"]:
                return 0, json.dumps({"nameWithOwner": "apolloio/leadgenie"})
            return 0, json.dumps({"number": 7, "headRefOid": HEAD, "headRefName": "x",
                                  "url": "https://github.com/apolloio/leadgenie/pull/7", "files": [{"path": "docs/a.md"}, {"path": "README.md"}]})
        code, _, _ = pr_ready.gate(pr=7, mode="block", repo_root=self.root, cwd=self.root, gh=docs_gh, git=self.git, env={})
        self.assertEqual(code, 0)


class FailClosed(Env):
    def test_gh_failure_blocks_in_block_mode_and_warns_in_warn_mode(self):
        bad = lambda a, c=None: (1, "")
        code, text, _ = pr_ready.gate(pr=7, mode="block", repo_root=self.root, cwd=self.root, gh=bad, git=self.git, env={})
        self.assertEqual(code, 2)
        self.assertIn("could not run", text)
        code, text, _ = pr_ready.gate(pr=7, mode="warn", repo_root=self.root, cwd=self.root, gh=bad, git=self.git, env={})
        self.assertEqual(code, 0)
        self.assertIn("could not run", text)
        self.assertFalse(text.startswith("pr-ready OK"))

    def test_unreadable_gh_output(self):
        code, text, _ = pr_ready.gate(pr=7, mode="block", repo_root=self.root, cwd=self.root, gh=lambda a, c=None: (0, "not json"), git=self.git, env={})
        self.assertEqual(code, 2)

    def test_exception_in_a_dependency_fails_closed(self):
        def boom(args, cwd=None):
            raise RuntimeError("kaboom")
        code, text, _ = pr_ready.gate(pr=7, mode="block", repo_root=self.root, cwd=self.root, gh=boom, git=self.git, env={})
        self.assertEqual(code, 2)
        self.assertIn("kaboom", text)

    def test_one_failure_never_lets_another_pr_pass(self):
        deps = dict(mode="warn", repo_root=self.root, git=self.git, env={})
        bad = lambda a, c=None: (1, "")
        first = pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": "gh pr merge 8"}}, gh=bad, **deps)
        second = pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": "gh pr merge 9"}}, gh=bad, **deps)
        for out in (first, second):
            self.assertEqual(out[0], 0)
            self.assertIn("could not run", json.loads(out[1])["hookSpecificOutput"]["additionalContext"])

    def test_target_in_another_repo_is_unresolvable(self):
        code, text, _ = pr_ready.gate(pr=7, repo="owner/other", mode="block", repo_root=self.root, cwd=self.root, gh=self.gh, git=self.git, env={})
        self.assertEqual(code, 2)
        self.assertIn("owner/other", text)

    def test_target_in_the_local_repo_is_checked(self):
        self.write(record())
        code, _, _ = pr_ready.gate(pr=7, repo="ApolloIO/leadgenie", mode="block", repo_root=self.root, cwd=self.root, gh=self.gh, git=self.git, env={})
        self.assertEqual(code, 0)

    def test_hook_main_error_path(self):
        out = pr_ready.cannot_run("block", "error: x")
        self.assertEqual(out[0], 2)


class DetectorBypasses(unittest.TestCase):
    def kinds(self, cmd):
        return [k for k, _ in pr_ready.detect_gated(cmd)]

    def test_newline_separates_commands(self):
        self.assertEqual(self.kinds("printf x\ngh pr merge 12"), ["merge"])
        self.assertEqual(self.kinds("echo a\n\ngh pr ready 3\nls"), ["ready"])

    def test_newline_inside_quotes_does_not_split(self):
        self.assertEqual(self.kinds('gh pr create --draft --body "line1\ngh pr merge 3"'), ["unresolved"])

    def test_wrappers(self):
        for cmd in ("env gh pr merge 12", "env FOO=1 gh pr merge 12", "sudo gh pr merge 12", "sudo -u bob gh pr merge 12",
                    "nohup gh pr merge 12", "FOO=1 gh pr merge 12", "echo 12 | xargs gh pr merge", "command gh pr merge 12",
                    "time gh pr merge 12", "/usr/local/bin/gh pr merge 12", "env -i gh pr merge 12"):
            self.assertEqual(self.kinds(cmd), ["merge"], cmd)

    def test_groups_and_subshells(self):
        for cmd in ("(gh pr merge 12)", "{ gh pr merge 12; }", "echo $(gh pr merge 12)", "echo `gh pr merge 12`",
                    "if true; then gh pr merge 12; fi", "true && (cd x && gh pr merge 12)"):
            self.assertEqual(self.kinds(cmd), ["merge"], cmd)

    def test_shell_dash_c_and_eval(self):
        self.assertEqual(self.kinds("bash -c 'gh pr merge 12'"), ["merge"])
        self.assertEqual(self.kinds("sh -lc \"git push && gh pr ready 3\""), ["ready"])
        self.assertEqual(self.kinds("eval gh pr merge 12"), ["merge"])

    def test_value_flags_consume_the_next_token(self):
        self.assertEqual(self.kinds("gh pr create --title --draft"), ["create"])
        self.assertEqual(self.kinds("gh pr create --body --draft --fill"), ["create"])
        self.assertEqual(self.kinds("gh pr create -t x --draft"), [])
        self.assertEqual(pr_ready.detect_gated("gh pr edit --add-reviewer bob 12"), [("edit", "12")])
        self.assertEqual(pr_ready.detect_gated("gh pr merge --subject s --body b 12"), [("merge", "12")])
        self.assertEqual(pr_ready.detect_gated("gh pr ready --repo o/n 12"), [("ready", "12")])

    def test_redirects_do_not_become_the_pr_arg(self):
        self.assertEqual(pr_ready.detect_gated("gh pr ready 2>&1"), [("ready", None)])
        self.assertEqual(pr_ready.detect_gated("gh pr merge > out.txt 12"), [("merge", "12")])

    def test_branch_argument_kept(self):
        self.assertEqual(pr_ready.detect_gated("gh pr merge feature-x"), [("merge", "feature-x")])
        self.assertEqual(pr_ready.gh_target("feature-x"), "feature-x")
        self.assertEqual(pr_ready.gh_target("https://github.com/a/b/pull/55"), 55)

    def test_repo_flag_and_url_extracted(self):
        t = pr_ready.scan("gh -R owner/other pr merge 7")[0]
        self.assertEqual((t["repo"], t["pr_arg"]), ("owner/other", "7"))
        t = pr_ready.scan("gh pr merge 7 --repo=owner/other2")[0]
        self.assertEqual(t["repo"], "owner/other2")
        t = pr_ready.scan("gh pr ready https://github.com/o/n/pull/9")[0]
        self.assertEqual(t["repo"], "o/n")

    def test_cd_is_tracked(self):
        t = pr_ready.scan("cd sub && gh pr merge 7", "/work/repo")[0]
        self.assertEqual(t["cwd"], "/work/repo/sub")
        t = pr_ready.scan("cd /other/place; gh pr merge 7", "/work/repo")[0]
        self.assertEqual(t["cwd"], "/other/place")
        t = pr_ready.scan("gh pr merge 7", "/work/repo")[0]
        self.assertEqual(t["cwd"], "/work/repo")

    def test_push_is_detected_anywhere_in_the_call(self):
        for command in ("git push && gh pr ready 7", "git -C x push origin HEAD; gh pr merge 7",
                        "gh pr ready 7 && git push", "bash -c 'git push' && gh pr merge 7",
                        "eval 'git push origin HEAD:topic'; gh pr ready 7", "$(git push); gh pr merge 7"):
            self.assertTrue(pr_ready.contains_git_push(command, "/w", {}), command)

    def test_still_not_gated(self):
        for cmd in ("git push && gh pr view 7", "gh pr create --draft"):
            self.assertEqual(self.kinds(cmd), [], cmd)


class PushThenReady(Env):
    def setUp(self):
        super().setUp()
        self.local = "d" * 40

    def git2(self, args, cwd=None):
        if args[:2] == ["rev-parse", "HEAD"]:
            return 0, self.local
        if args[:3] == ["rev-parse", "--abbrev-ref", "--symbolic-full-name"]:
            return 0, "origin/akansh/feature"
        return self.git(args, cwd)

    def hook(self, cmd, mode="block"):
        return pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": cmd}},
                             mode=mode, repo_root=self.root, gh=self.gh, git=self.git2, env={})

    def test_ready_alone_checks_the_remote_head(self):
        self.write(record())
        self.assertEqual(self.hook("gh pr ready 7"), (0, "", ""))

    def test_every_combined_push_and_gate_form_blocks_in_both_modes(self):
        expected = "Next: run the git push on its own, then run the gh command in a separate call so the gate checks the pushed head."
        commands = ("git push && gh pr ready 7", "git push backup topic; gh pr merge 7",
                    "git push origin other:topic; gh pr edit 7 --add-reviewer bob",
                    "bash -c 'git push origin' && gh pr create --fill",
                    "eval 'git push origin HEAD:topic'; gh pr ready 7",
                    "gh pr merge 7 && (git push origin topic)")
        for mode in ("warn", "block"):
            for command in commands:
                code, _, err = self.hook(command, mode)
                self.assertEqual(code, 2, command)
                self.assertIn(expected, err)


class HookTargets(Env):
    def test_edit_add_reviewer_then_number_targets_that_pr(self):
        seen = []

        def gh(args, cwd=None):
            seen.append(args)
            return self.gh(args, cwd)
        pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": "gh pr edit --add-reviewer bob 12"}},
                      mode="block", repo_root=self.root, gh=gh, git=self.git, env={})
        self.assertIn("12", [a for call in seen for a in call])

    def test_other_repo_flag_blocks(self):
        code, _, err = pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": "gh -R owner/other pr merge 7"}},
                                     mode="block", repo_root=self.root, gh=self.gh, git=self.git, env={})
        self.assertEqual(code, 2)
        self.assertIn("owner/other", err)

    def test_cd_changes_the_working_directory_passed_on(self):
        cwds = []

        def gh(args, cwd=None):
            cwds.append(cwd)
            return self.gh(args, cwd)
        pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": "cd sub && gh pr merge 7"}},
                      mode="block", repo_root=self.root, gh=gh, git=self.git, env={})
        self.assertIn(os.path.join(self.root, "sub"), cwds)

    def test_hook_main_fail_closed_on_exception(self):
        import io
        import sys
        old = sys.stdin
        sys.stdin = io.StringIO("not json")
        try:
            err, out = io.StringIO(), io.StringIO()
            old_e, old_o = sys.stderr, sys.stdout
            sys.stderr, sys.stdout = err, out
            try:
                code = pr_ready.main(["--hook", "--mode", "block"])
            finally:
                sys.stderr, sys.stdout = old_e, old_o
        finally:
            sys.stdin = old
        self.assertEqual(code, 2)
        self.assertIn("could not run", err.getvalue())


class AstraReReviewProbes(Env):
    def hook(self, command, mode="block", **deps):
        supplied = dict(repo_root=self.root, gh=self.gh, git=self.git, env={}, mode=mode)
        supplied.update(deps)
        return pr_ready.hook({"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": command}}, **supplied)

    def test_raw_detector_fails_closed_when_target_cannot_be_bound(self):
        command = "eval 'runner=gh'; \"$runner\" pr merge feature-123"
        code, _, err = self.hook(command)
        self.assertEqual(code, 2)
        self.assertIn("run the gh command directly, not through a subshell or eval", err)
        code, out, _ = self.hook(command, mode="warn")
        self.assertEqual(code, 0)
        self.assertIn("WARNING", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_unresolved_target_uses_repository_configured_block_mode(self):
        os.makedirs(os.path.join(self.root, ".harness"), exist_ok=True)
        with open(os.path.join(self.root, ".harness", "config.json"), "w") as handle:
            json.dump({"pr_ready_mode": "block"}, handle)
        command = 'PR_URL="$(gh pr create --title feature --body body)"'
        payload = {"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": command}}
        code, _, err = pr_ready.hook(payload, gh=self.gh, git=self.git, env={})
        self.assertEqual(code, 2)
        self.assertIn("run the gh command directly", err)

    def test_subshell_cd_does_not_escape_scope(self):
        target = pr_ready.scan("(cd /other; true) ; gh pr merge 7", self.root)[0]
        self.assertEqual(target["cwd"], self.root)

    def test_astra_subshell_reconstruction_preserves_quoted_directory(self):
        spaced = os.path.join(self.root, "repo space")
        target = pr_ready.scan("(cd %s; gh pr merge 7)" % repr(spaced), self.root)[0]
        self.assertEqual(target["cwd"], spaced)
        target = pr_ready.scan("bash -c \"cd '%s'; gh pr merge 7\"" % spaced, self.root)[0]
        self.assertEqual(target["cwd"], spaced)
        target = pr_ready.scan("bash -c 'cd /other; true'; gh pr merge 7", self.root)[0]
        self.assertEqual(target["cwd"], self.root)

    def test_branch_target_attached_flags_repo_env_and_create_head(self):
        self.assertEqual(pr_ready.gh_target("feature-123"), "feature-123")
        hit = pr_ready.scan("gh -Rowner/repo pr create -tTitle --head topic")[0]
        self.assertEqual((hit["repo"], hit["head"]), ("owner/repo", "topic"))
        self.assertEqual(hit["kind"], "create")
        self.assertEqual(pr_ready.scan("gh pr create -tadd")[0]["kind"], "create")
        self.assertEqual(pr_ready.scan("GH_REPO=inline/repo gh pr merge 7")[0]["repo"], "inline/repo")
        self.assertEqual(pr_ready.scan("env GH_REPO=wrapped/repo gh pr merge 7")[0]["repo"], "wrapped/repo")
        self.assertEqual(pr_ready.scan("export GH_REPO=exported/repo; gh pr merge 7")[0]["repo"], "exported/repo")
        self.assertEqual(pr_ready.scan("gh pr merge 7", env={"GH_REPO": "process/repo"})[0]["repo"], "process/repo")
        topic_head = "e" * 40

        def git(args, cwd=None):
            if args[:2] == ["rev-parse", "topic"]:
                return 0, topic_head
            if args[:2] == ["diff", "--name-only"]:
                return 0, "a.rb"
            return self.git(args, cwd)

        self.write(record(head=topic_head), key="branch-topic")
        self.assertEqual(pr_ready.gate(mode="block", repo_root=self.root, cwd=self.root, creating=True,
                                       create_head="topic", gh=self.gh, git=git, env={})[0], 0)

    def test_gh_repo_assignments_reach_nested_shell_commands(self):
        commands = ("GH_REPO=nested/repo bash -c 'gh pr merge 7'",
                    "env GH_REPO=nested/repo sh -c 'gh pr merge 7'",
                    "GH_REPO=nested/repo eval 'gh pr merge 7'",
                    "export GH_REPO=nested/repo; (gh pr merge 7)")
        for command in commands:
            self.assertEqual(pr_ready.scan(command)[0]["repo"], "nested/repo", command)

    def test_every_gh_repo_environment_form_blocks_a_wrong_target(self):
        commands = ("GH_REPO=elsewhere/other gh pr merge 7",
                    "env GH_REPO=elsewhere/other gh pr merge 7",
                    "export GH_REPO=elsewhere/other; gh pr merge 7",
                    "env GH_REPO=elsewhere/other bash -c 'gh pr merge 7'")
        for command in commands:
            code, _, err = self.hook(command)
            self.assertEqual(code, 2, command)
            self.assertIn("elsewhere/other", err)
        payload = {"tool_name": "Bash", "cwd": self.root, "tool_input": {"command": "gh pr merge 7"}}
        code, _, err = pr_ready.hook(payload, repo_root=self.root, gh=self.gh,
                                     git=self.git, env={"GH_REPO": "elsewhere/other"}, mode="block")
        self.assertEqual(code, 2)
        self.assertIn("elsewhere/other", err)

    def test_shell_push_forms_are_all_rejected_before_record_evaluation(self):
        for command in ("bash -c 'git push'; gh pr merge 7", "eval 'git push origin HEAD:topic'; gh pr ready 7",
                        "git push origin local:remote; gh pr merge 7"):
            code, _, err = self.hook(command, mode="warn")
            self.assertEqual(code, 2, command)
            self.assertIn("run the git push on its own", err)

    def test_mode_is_resolved_before_root_discovery_exception(self):
        def boom(args, cwd=None):
            raise RuntimeError("root exploded")
        self.assertEqual(pr_ready.gate(cwd=self.root, git=boom, env={"HARNESS_PR_READY_MODE": "block"})[0], 2)
        code, text, _ = pr_ready.gate(cwd=self.root, git=boom, env={"HARNESS_PR_READY_MODE": "warn"})
        self.assertEqual(code, 0)
        self.assertIn("WARNING", text)

    def test_record_schema_rejects_astra_malformed_values(self):
        malformed = [record(schema={}), record(schema=True), record(schema=2.0), record(reviewers=[None]),
                     record(findings=[{}]), record(repo=""), record(verdict="MAYBE"), record(verdict={}),
                     record(verdict=[]), record(findings=[finding(severity=[])]),
                     record(findings=[finding(category=[])]),
                     record(findings=[finding(lens_severities={"backend-reviewer": ["major"]})]),
                     record(findings=[finding(disposition={"action": "wont_fix", "reason": []})])]
        for rec in malformed:
            self.write(rec)
            for mode in ("warn", "block"):
                self.assertEqual(self.gate(mode)[0], 2, rec)
        reasons = pr_ready.validate_record(record(reviewers=[None]), HEAD, "apolloio/leadgenie", ["README.md"])
        self.assertTrue(any("non-string reviewer" in reason for reason in reasons))

    def test_schema_accepts_only_plain_integer_versions(self):
        self.assertFalse(pr_ready.validate_record(record(schema=2), HEAD, "apolloio/leadgenie", ["a.rb"]))
        for schema in (True, 2.0, "1"):
            self.assertTrue(pr_ready.validate_record(record(schema=schema), HEAD, "apolloio/leadgenie", ["a.rb"]))

    def test_record_evaluation_exception_blocks_in_both_modes(self):
        self.write(record())
        original = pr_ready.check_record
        pr_ready.check_record = lambda *args, **kwargs: (_ for _ in ()).throw(TypeError("astra probe"))
        try:
            for mode in ("warn", "block"):
                code, text, _ = self.gate(mode)
                self.assertEqual(code, 2)
                self.assertIn("validation raised", text)
        finally:
            pr_ready.check_record = original

    def test_docs_exemption_is_extension_based_and_images_need_neighbor(self):
        self.assertTrue(pr_ready.docs_only(["docs/guide.md", "docs/diagram.svg"]))
        self.assertFalse(pr_ready.docs_only(["docs/generate.py"]))
        self.assertFalse(pr_ready.docs_only(["assets/lone.png"]))

    def test_explain_uses_the_gate_policy(self):
        tiers = {"B1": "warn", "category:design": "block"}
        self.assertIn("severity floor", pr_ready.finding_explanation(finding(severity="major", rule="B1"), tiers))
        self.assertIn("learned rule tier", pr_ready.finding_explanation(finding(severity="minor", rule="B1"), tiers))
        self.assertIn("must-triage category", pr_ready.finding_explanation(
            finding(severity="minor", category="correctness"), {}))
        self.assertEqual(pr_ready.finding_explanation([], {}), "block: malformed finding")

    def test_explain_calls_category_only_docs_and_design_nits_warn(self):
        os.makedirs(os.path.join(self.root, ".harness"), exist_ok=True)
        with open(os.path.join(self.root, ".harness", "rule-tiers.json"), "w") as handle:
            json.dump({"category:docs": "block", "category:design": "block"}, handle)
        path = os.path.join(self.root, "record.json")
        with open(path, "w") as handle:
            json.dump(record(findings=[finding("D", severity="nit", category="docs", rule=None),
                                       finding("UX", severity="minor", category="design", rule=None)]), handle)
        explanation = pr_ready.explain_record(path, self.root)
        self.assertIn("D: warn", explanation)
        self.assertIn("UX: warn", explanation)
        self.assertNotIn("must triage", explanation)

    def test_astra_docs_design_category_only_tier_warns_even_in_block_mode(self):
        os.makedirs(os.path.join(self.root, ".harness"), exist_ok=True)
        with open(os.path.join(self.root, ".harness", "rule-tiers.json"), "w") as handle:
            json.dump({"category:docs": "block", "category:design": "block"}, handle)
        for category in ("docs", "design"):
            item = finding(severity="nit", category=category, rule=None)
            self.assertEqual(pr_ready.finding_tier(item, {"category:" + category: "block"}), "warn")
            self.assertTrue(pr_ready.finding_explanation(item, {"category:" + category: "block"}).startswith("warn:"))
            self.write(record(findings=[item]))
            code, text, _ = self.gate("block")
            self.assertEqual(code, 0)
            self.assertTrue(text.startswith("TRIAGE REQUIRED"))


if __name__ == "__main__":
    unittest.main()
