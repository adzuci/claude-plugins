import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "apollo-product-lab"
SCRIPTS = PLUGIN / "scripts"
REGISTRY_PATH = PLUGIN / "framework" / "rules" / "registry.yml"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


registry_lib = load("test_rule_registry", SCRIPTS / "rule_registry.py")
probe = load("test_rule_probe", SCRIPTS / "rule-probe.py")
promote = load("test_rule_promote", SCRIPTS / "rule-promote.py")
pr_ready = load("test_pr_ready_registry", SCRIPTS / "pr-ready.py")


class RegistryConsistency(unittest.TestCase):
    def assert_registry_rows(self, rows, registered, prompted):
        self.assertEqual(len(rows), len(registered))
        for rule in rows:
            self.assertEqual(set(rule), {"id", "agent", "status", "added", "source", "replay", "notes"})
            self.assertEqual(set(rule["replay"]), {"cases", "hits", "false_positives", "last_scored"})
            self.assertTrue(rule["source"])
            if rule["status"] in ("shadow", "active"):
                self.assertEqual(rule["agent"], prompted[rule["id"]]["agent"])
            else:
                self.assertNotIn(rule["id"], prompted)

    def assert_lifecycle_consistent(self, registered, prompted):
        expected = {rule_id for rule_id, rule in registered.items() if rule["status"] in ("shadow", "active")}
        self.assertEqual(expected, set(prompted))
        self.assertFalse({rule_id for rule_id, rule in registered.items()
                          if rule["status"] in ("candidate", "retired")} & set(prompted))

    def test_registry_has_one_evidence_bound_row_per_prompt_rule(self):
        data, registered = registry_lib.load_registry()
        prompted = registry_lib.prompt_rules()
        self.assert_registry_rows(data["rules"], registered, prompted)

    def test_prompt_and_lifecycle_statuses_are_consistent(self):
        _, registered = registry_lib.load_registry()
        prompted = registry_lib.prompt_rules()
        self.assert_lifecycle_consistent(registered, prompted)

    def test_lifecycle_invariants_allow_candidates_promotions_and_retirements(self):
        rows = [{"id": status.upper(), "agent": "backend-reviewer", "status": status,
                 "added": "2026-10-16", "source": ["test"],
                 "replay": {"cases": 0, "hits": 0, "false_positives": 0, "last_scored": None},
                 "notes": "test"}
                for status in ("candidate", "shadow", "active", "retired")]
        registered = {rule["id"]: rule for rule in rows}
        prompted = {"SHADOW": {"agent": "backend-reviewer"}, "ACTIVE": {"agent": "backend-reviewer"}}
        self.assert_lifecycle_consistent(registered, prompted)
        self.assert_registry_rows(rows, registered, prompted)
        registered["SHADOW"]["status"] = "active"
        registered["ACTIVE"]["status"] = "retired"
        prompted = {"SHADOW": {"agent": "backend-reviewer"}}
        self.assert_lifecycle_consistent(registered, prompted)
        self.assert_registry_rows(rows, registered, prompted)


class PrReadyRegistryPolicy(unittest.TestCase):
    def finding(self, rule):
        return {"id": "F1", "severity": "major", "category": "correctness", "rule": rule,
                "file": "x.rb", "line": 1, "summary": "problem", "disposition": None,
                "lens_severities": {"backend-reviewer": "major"}}

    def test_shadow_and_retired_findings_are_info_even_at_major(self):
        for status in ("shadow", "retired"):
            rules = {"B1": {"status": status}}
            finding = self.finding("B1")
            self.assertIsNone(pr_ready.finding_tier(finding, {"B1": "block"}, rules))
            self.assertTrue(pr_ready.finding_explanation(finding, {"B1": "block"}, rules).startswith("info:"))
        mixed = {"M43": {"status": "shadow"}, "IP2": {"status": "active"}}
        finding = self.finding(["M43", "IP2"])
        self.assertEqual(pr_ready.finding_tier(finding, {"M43": "block", "IP2": "block"}, mixed), "block")
        finding["severity"] = "minor"
        finding["lens_severities"] = {"db-perf": "major"}
        self.assertTrue(pr_ready.check_record(
            {"schema": 2, "verdict": "REQUEST_CHANGES", "findings": [finding]}, "a" * 40, str(ROOT),
            tiers={"M43": "block", "IP2": "block"}, registry=mixed))

    def test_pure_shadow_finding_never_validates_a_stale_fixed_commit(self):
        finding = self.finding("M43")
        finding["disposition"] = {"action": "fixed", "commit": "b" * 40}
        problems = pr_ready.check_record(
            {"schema": 2, "verdict": "REQUEST_CHANGES", "findings": [finding]}, "a" * 40, str(ROOT),
            git=lambda args, cwd=None: (1, ""), tiers={"M43": "block"},
            registry={"M43": {"status": "shadow"}})
        self.assertEqual(problems, [])

    def test_unknown_rule_is_a_record_validation_warning(self):
        problems = pr_ready.check_record({"schema": 2, "verdict": "REQUEST_CHANGES",
                                          "findings": [self.finding("ZZ99")]}, "a" * 40, str(ROOT),
                                         tiers={}, registry={})
        warning = next(problem for problem in problems if "Record-validation warning" in problem)
        self.assertEqual(pr_ready.tier_of(warning), "warn")
        self.assertFalse(pr_ready.blocks_in_mode(warning, "block"))


class RuleProbe(unittest.TestCase):
    def test_prepare_writes_on_and_string_removed_off_briefs_without_model_calls(self):
        source = PLUGIN / "agents" / "backend-reviewer.md"
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            manifest = probe.prepare("B46", directory)
            on = (Path(directory) / "on" / source.name).read_text()
            off = (Path(directory) / "off" / source.name).read_text()
            self.assertIn("- B46 ", on)
            self.assertNotIn("- B46 ", off)
            self.assertEqual(manifest["case_ids"], ["ads-m1-4294522479"])
            self.assertTrue((Path(directory) / "on" / "brief.md").exists())
            self.assertTrue((Path(directory) / "off" / "brief.md").exists())
        self.assertEqual(source.read_bytes(), before)

    def test_score_pair_uses_injected_scorer_and_records_on_greater_than_off(self):
        reports = {
            "on": {"scored_cases": 13, "by_rule": {"B46": {"caught": 2, "total": 3, "recall": 0.667}},
                   "false_positives_by_rule": {"B46": {"caught": 1, "total": 10, "recall": 0.1}},
                   "scored_case_ids": ["case%s" % i for i in range(13)]},
            "off": {"scored_cases": 13, "by_rule": {"B46": {"caught": 0, "total": 3, "recall": 0.0}},
                    "false_positives_by_rule": {"B46": {"caught": 0, "total": 10, "recall": 0.0}},
                    "scored_case_ids": ["case%s" % i for i in range(13)]},
        }
        with tempfile.TemporaryDirectory() as directory:
            path, result = probe.score_pair("B46", "on", "off", scorer=lambda value: reports[value],
                                            probes_dir=directory, today="2026-10-16")
            self.assertTrue(result["adds_hits"])
            self.assertTrue(result["complete"])
            self.assertEqual(result["on"]["hits"], 2)
            self.assertEqual(json.loads(Path(path).read_text()), result)

    def test_score_pair_marks_disjoint_equal_sized_case_sets_incomplete(self):
        reports = {
            "on": {"scored_cases": 4, "scored_case_ids": ["a", "b", "c", "d"],
                   "by_rule": {"B46": {"caught": 3, "total": 3, "recall": 1.0}},
                   "false_positives_by_rule": {"B46": {"caught": 0, "total": 1, "recall": 0.0}}},
            "off": {"scored_cases": 4, "scored_case_ids": ["e", "f", "g", "h"],
                    "by_rule": {"B46": {"caught": 0, "total": 3, "recall": 0.0}},
                    "false_positives_by_rule": {"B46": {"caught": 0, "total": 1, "recall": 0.0}}},
        }
        with tempfile.TemporaryDirectory() as directory:
            _, result = probe.score_pair("B46", "on", "off", scorer=lambda value: reports[value],
                                         probes_dir=directory, today="2026-10-16")
            self.assertFalse(result["complete"])
            rule = RulePromotion().registry()["rules"][0]
            self.assertIsNone(promote.proposed_change(rule, [result]))

    def test_score_pair_rejects_astras_missing_off_output(self):
        cases = [{"id": "case%s" % i, "expected_rules": ["B46"], "rule_gap": False,
                  "category": "correctness", "pr": 1, "path": "x.rb", "line": i * 100,
                  "url": "https://example.test/%s" % i,
                  "match": {"same_file": True, "any_of": {"rules": ["B46"], "category": "correctness"},
                            "line_tolerance": 1}} for i in range(3)]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            cases_path = base / "cases.jsonl"
            cases_path.write_text("".join(json.dumps(case) + "\n" for case in cases))
            outcomes = base / "outcomes.json"
            outcomes.write_text(json.dumps([{"id": case["id"], "outcome": "fixed"} for case in cases]))
            for mode in ("on", "off"):
                run = base / mode
                run.mkdir()
                output = run / "findings.json"
                (run / "groups.json").write_text(json.dumps([
                    {"case_ids": [case["id"] for case in cases], "outputs": {"backend": str(output)}}]))
                if mode == "on":
                    output.write_text(json.dumps([{"rule": "B46", "file": "x.rb", "line": case["line"]}
                                                  for case in cases]))
            scorer = lambda path: probe.score_run(path, str(cases_path), str(outcomes))
            with self.assertRaisesRegex(ValueError, "missing or unreadable output"):
                probe.score_pair("B46", str(base / "on"), str(base / "off"), scorer=scorer,
                                 probes_dir=str(base / "probes"))

    def test_score_pair_requires_real_declined_cases(self):
        report = {"scored_cases": 3, "by_rule": {"B46": {"caught": 3, "total": 3, "recall": 1.0}},
                  "should_not_flag": {"flagged": 0, "total": 0, "rate": 0},
                  "scored_case_ids": ["a", "b", "c"]}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no declined cases"):
                probe.score_pair("B46", "on", "off", scorer=lambda path: report,
                                 probes_dir=directory)


class RulePromotion(unittest.TestCase):
    def registry(self, status="shadow", cases=5, hits=3):
        return {"schema": 1, "rules": [{"id": "B46", "agent": "backend-reviewer", "status": status,
                                          "added": "2026-10-16", "source": ["seed"],
                                          "replay": {"cases": cases, "hits": hits, "false_positives": 0,
                                                     "last_scored": "2026-10-16"}, "notes": "test"}]}

    def write_probe(self, directory, date="2026-10-16", hits=3, fp=0.1, adds=True, cases=5):
        Path(directory, "B46-%s.json" % date).write_text(json.dumps(
            {"rule": "B46", "scored": date, "complete": True,
             "on": {"cases": cases, "hits": hits, "false_positives": 1, "declined_cases": 10,
                    "false_positive_rate": fp},
             "off": {"cases": cases, "hits": 0, "false_positives": 0, "declined_cases": 10,
                     "false_positive_rate": 0}, "adds_hits": adds}))

    def test_thresholds_promote_and_apply_registry_only_when_requested(self):
        agent_hashes = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                        for path in registry_lib.RULE_SOURCES.values()}
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            registry = base / "registry.yml"
            registry.write_text(json.dumps(self.registry()))
            probes = base / "probes"
            proposals = base / "proposals"
            probes.mkdir()
            self.write_probe(probes)
            _, patch, changes = promote.build_proposal(str(registry), str(probes), str(proposals),
                                                        today="2026-10-16")
            self.assertEqual(changes[0][1:3], ("shadow", "active"))
            self.assertEqual(json.loads(registry.read_text())["rules"][0]["status"], "shadow")
            self.assertIn('"status": "active"', Path(patch).read_text())
            promote.build_proposal(str(registry), str(probes), str(proposals), today="2026-10-17",
                                   apply_registry=True)
            applied = json.loads(registry.read_text())["rules"][0]
            self.assertEqual(applied["status"], "active")
            self.assertEqual(applied["replay"], {"cases": 5, "hits": 3, "false_positives": 1,
                                                 "last_scored": "2026-10-16"})
        self.assertEqual(agent_hashes, {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                        for path in registry_lib.RULE_SOURCES.values()})

    def test_missing_or_insufficient_evidence_never_promotes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            registry = base / "registry.yml"
            probes = base / "probes"
            proposals = base / "proposals"
            probes.mkdir()
            registry.write_text(json.dumps(self.registry(cases=2, hits=2)))
            self.write_probe(probes, cases=2, hits=2)
            self.assertFalse(promote.build_proposal(str(registry), str(probes), str(proposals))[2])
            registry.write_text(json.dumps(self.registry(cases=5, hits=3)))
            for path in probes.iterdir():
                path.unlink()
            self.assertFalse(promote.build_proposal(str(registry), str(probes), str(proposals))[2])

    def test_retirement_thresholds(self):
        rule = self.registry(status="active")["rules"][0]
        high_fp = [{"scored": "2026-10-16", "complete": True,
                    "on": {"hits": 2, "false_positive_rate": 0.31}}]
        self.assertEqual(promote.proposed_change(rule, high_fp)[0], "retired")
        zero_hits = [{"scored": "2026-10-%02d" % day,
                      "complete": True, "on": {"hits": 0, "false_positive_rate": 0.0}}
                     for day in (16, 15, 14)]
        self.assertEqual(promote.proposed_change(rule, zero_hits)[0], "retired")
        zero_hits[1]["complete"] = False
        self.assertIsNone(promote.proposed_change(rule, zero_hits))


if __name__ == "__main__":
    unittest.main()
