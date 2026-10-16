import json, os, tempfile, unittest, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("run_replay", os.path.join(HERE, "run_replay.py"))
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)


def case(**kw):
    c = {"id": "x1", "pr": 1, "path": "a/b.rb", "line": 100, "category": "correctness/logic bug", "excerpt": "missing account validation",
         "expected_rules": ["B24", "IP14"], "rule_gap": False, "url": "u",
         "match": {"same_file": True, "line_tolerance": 8,
                   "any_of": {"rules": ["B24", "IP14"], "category": "correctness/logic bug"}}}
    c.update(kw)
    return c


def f(**kw):
    d = {"file": "a/b.rb", "line": 100, "rule": "B24", "category": "", "severity": "must-fix", "summary": "missing validation"}
    d.update(kw)
    return d


class Matcher(unittest.TestCase):
    def test_rule_hit(self):
        self.assertTrue(rr.case_matches(case(), f()))

    def test_category_hit_without_rule(self):
        self.assertTrue(rr.case_matches(case(), f(rule="", category="Correctness/logic bug")))

    def test_rules_only_rejects_category_only_credit(self):
        strict = case(match={"same_file": True, "line_tolerance": 8, "rules_only": True,
                             "any_of": {"rules": ["B46"], "category": "correctness/logic bug"}})
        self.assertFalse(rr.case_matches(strict, f(rule="", category="correctness")))
        self.assertTrue(rr.case_matches(strict, f(rule="B46", category="docs")))

    def test_line_within_tolerance(self):
        self.assertTrue(rr.case_matches(case(), f(line=108)))
        self.assertFalse(rr.case_matches(case(), f(line=109)))

    def test_wrong_file(self):
        self.assertFalse(rr.case_matches(case(), f(file="a/c.rb")))

    def test_wrong_rule_and_category(self):
        self.assertFalse(rr.case_matches(case(), f(rule="B99", category="naming")))

    def test_multi_rule_finding(self):
        self.assertTrue(rr.case_matches(case(), f(rule="B1/IP14")))

    def test_missing_line_does_not_match(self):
        self.assertFalse(rr.case_matches(case(), f(line=None)))

    def test_rule_id_field_matches(self):
        self.assertTrue(rr.case_matches(case(), f(rule="", rule_id="IP14")))
        self.assertTrue(rr.case_matches(case(), f(rule=None, rule_id=["B24"])))

    def test_canonical_reviewer_category_matches_mining_category(self):
        self.assertTrue(rr.case_matches(case(), f(rule="", category="correctness")))
        self.assertFalse(rr.case_matches(case(), f(rule="", category="docs")))

    def test_canonical_mapping_covers_every_mining_category(self):
        cats = {c["category"] for c in rr.load_cases(rr.DEFAULT_CASES)}
        for c in cats:
            self.assertIn(rr.canonical_category(c), rr.CANONICAL_CATEGORIES, c)

    def test_file_level_review_case(self):
        c = case(path=None, line=None, match={"same_file": False, "line_tolerance": None,
                 "any_of": {"rules": ["B27"], "category": "x"}})
        self.assertTrue(rr.case_matches(c, f(file="anything.rb", line=None, rule="B27")))
        self.assertFalse(rr.case_matches(c, f(rule="B1")))


class Diff(unittest.TestCase):
    def test_clean_and_route(self):
        raw = ("diff --git a/sorbet/rbi/x.rbi b/sorbet/rbi/x.rbi\n+x\n"
               "diff --git a/yarn.lock b/yarn.lock\n+x\n"
               "diff --git a/packs/ads/app/services/ads/s.rb b/packs/ads/app/services/ads/s.rb\n+Mongoid\n")
        text, files = rr.clean_diff(raw)
        self.assertEqual(files, ["packs/ads/app/services/ads/s.rb"])
        self.assertEqual(rr.route(files, text), ["backend-reviewer", "security-reviewer", "db-perf"])
        self.assertEqual(rr.route(["packages/ads/a.tsx"], ""), ["frontend-reviewer"])
        self.assertEqual(rr.route(["packs/ads/spec/a_spec.rb"], ""), ["backend-reviewer"])
        self.assertEqual(rr.route(["config/routes.rb"], "+  resources :accounts"),
                         ["backend-reviewer", "security-reviewer"])


class Cases(unittest.TestCase):
    def test_cases_file_shape(self):
        cs = rr.load_cases(rr.DEFAULT_CASES)
        self.assertGreater(len(cs), 100)
        schema = json.load(open(os.path.join(HERE, "..", "cases.schema.json")))["$defs"]["review_replay_case"]
        ids = set()
        for c in cs:
            self.assertEqual(set(schema["required"]) - set(c), set())
            self.assertLessEqual(len(c["excerpt"].split()), 40)
            self.assertNotIn(c["id"], ids)
            ids.add(c["id"])


class Assign(unittest.TestCase):
    def test_one_finding_matches_at_most_one_case(self):
        cs = [case(id="a", line=100), case(id="b", line=104), case(id="c", line=108)]
        got = rr.assign(cs, [f(line=104)])
        self.assertEqual(got, {"b": 0})

    def test_greedy_by_smallest_distance(self):
        cs = [case(id="a", line=100), case(id="b", line=106)]
        got = rr.assign(cs, [f(line=105), f(line=100)])
        self.assertEqual(got, {"a": 1, "b": 0})

    def test_unrelated_finding_does_not_match(self):
        self.assertEqual(rr.assign([case()], [f(rule="B99", category="naming")]), {})


class Score(unittest.TestCase):
    def run_score(self, cases, findings, outcomes):
        with tempfile.TemporaryDirectory() as d:
            cp = os.path.join(d, "cases.jsonl")
            open(cp, "w").write("".join(json.dumps(c) + "\n" for c in cases))
            op = os.path.join(d, "outcomes.json")
            json.dump([{"id": k, "outcome": v} for k, v in outcomes.items()], open(op, "w"))
            os.makedirs(os.path.join(d, "g", "findings"))
            out = os.path.join(d, "g", "findings", "backend-reviewer.json")
            json.dump(findings, open(out, "w"))
            json.dump([{"group": "g", "case_ids": [c["id"] for c in cases], "outputs": {"backend-reviewer": out}}],
                      open(os.path.join(d, "groups.json"), "w"))

            class A:
                runs, cases_ = d, cp
            A.cases = cp
            A.outcomes = op
            rr.cmd_score(A)
            self.assertTrue(os.path.exists(os.path.join(d, "report.md")))
            return json.load(open(os.path.join(d, "report.json")))

    def test_end_to_end_scores_fixed_cases_only(self):
        rep = self.run_score([case(id="c1"), case(id="c2", line=500)],
                             [f(line=103), f(file="z.rb", rule="B2")], {"c1": "fixed", "c2": "fixed"})
        self.assertEqual(rep["overall"], {"caught": 1, "total": 2, "recall": 0.5})
        self.assertEqual(rep["noise_findings"], 1)
        self.assertEqual([m["id"] for m in rep["misses"]], ["c2"])

    def test_declined_case_flagged_is_a_false_positive_not_recall(self):
        rep = self.run_score([case(id="c1"), case(id="c2", line=500)], [f(line=100)], {"c1": "declined", "c2": "fixed"})
        self.assertEqual(rep["overall"]["total"], 1)
        self.assertEqual(rep["overall"]["caught"], 0)
        self.assertEqual(rep["should_not_flag"]["total"], 1)
        self.assertEqual(rep["should_not_flag"]["flagged"], 1)
        self.assertEqual([m["id"] for m in rep["misses"]], ["c2"])

    def test_unknown_reported_separately(self):
        rep = self.run_score([case(id="c1"), case(id="c2", line=500)], [f(line=100)], {"c1": "unknown"})
        self.assertEqual(rep["overall"]["total"], 0)
        self.assertEqual(rep["unknown_outcome"], {"total": 2, "caught": 1})

    def test_one_finding_cannot_catch_three_cases(self):
        cs = [case(id="a", line=100), case(id="b", line=101), case(id="c", line=102)]
        rep = self.run_score(cs, [f(line=101)], {"a": "fixed", "b": "fixed", "c": "fixed"})
        self.assertEqual(rep["overall"]["caught"], 1)
        self.assertEqual(rep["noise_findings"], 0)

    def test_rule_id_findings_score(self):
        rep = self.run_score([case(id="c1")], [{"file": "a/b.rb", "line": 100, "rule_id": "B24", "category": "correctness"}],
                             {"c1": "fixed"})
        self.assertEqual(rep["overall"]["caught"], 1)


if __name__ == "__main__":
    unittest.main()
