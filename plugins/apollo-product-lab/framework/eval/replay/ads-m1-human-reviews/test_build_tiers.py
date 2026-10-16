import importlib.util
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location("build_tiers", os.path.join(HERE, "build_tiers.py"))
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)


def case(**kw):
    c = {"id": "x", "comment_kind": "line", "path": "a.rb", "line": 10}
    c.update(kw)
    return c


def outcome(oid, rules, category, out):
    return {"id": oid, "expected_rules": rules, "category": category, "outcome": out}


class Classify(unittest.TestCase):
    def test_explicit_reply_outcome_beats_nearby_line_movement(self):
        self.assertEqual(bt.classify(case(), ["Not fixed in this PR"], True), "declined")
        self.assertEqual(bt.classify(case(), ["Will be fixed in a follow-up ticket"], True), "deferred")
        self.assertEqual(bt.classify(case(), ["This hasn't been fixed in this PR"], True), "declined")
        self.assertEqual(bt.classify(case(), ["Will be updated in a follow-up ticket"], True), "deferred")

    def test_moved_lines_fix(self):
        self.assertEqual(bt.classify(case(), [], True), "fixed")

    def test_fix_words_fix(self):
        self.assertEqual(bt.classify(case(), ["Fixed in abc"], False), "fixed")
        self.assertEqual(bt.classify(case(), ["It wasn't, good catch. Fixed in e9c0e002b0c"], False), "fixed")
        self.assertEqual(bt.classify(case(comment_kind="review"), ["Done"], None), "fixed")
        self.assertEqual(bt.classify(case(), ["Done, moved it"], False), "fixed")
        self.assertEqual(bt.classify(case(), ["The field was updated in abc"], False), "fixed")

    def test_uncertain_or_future_fix_language_is_not_fixed(self):
        self.assertEqual(bt.classify(case(), ["I will update this"], False), "unknown")
        self.assertEqual(bt.classify(case(), ["This really has not been fixed"], False), "declined")
        self.assertEqual(bt.classify(case(), ["Thanks, fixed-looking output follows"], False), "unknown")
        self.assertEqual(bt.classify(case(), ["This hasn't been fixed in this PR"], False), "declined")

    def test_acknowledgement_is_unknown_not_declined(self):
        self.assertEqual(bt.classify(case(), ["Thanks, looking into it"], False), "unknown")

    def test_compare_failure_is_unknown(self):
        self.assertEqual(bt.classify(case(), [], None), "unknown")
        self.assertEqual(bt.classify(case(), ["Thanks"], None), "unknown")

    def test_no_reply_and_no_change_is_unknown(self):
        self.assertEqual(bt.classify(case(), [], False), "unknown")


class Moved(unittest.TestCase):
    commits = [{"sha": "c1", "parents": [{"sha": "p1"}], "commit": {"committer": {"date": "2026-01-01T00:00:00Z"}}},
               {"sha": "c2", "parents": [{"sha": "c1"}], "commit": {"committer": {"date": "2026-01-03T00:00:00Z"}}}]

    def test_compares_from_the_first_commit_after_the_comment(self):
        calls = []

        def compare(base, head):
            calls.append((base, head))
            return {"files": [{"filename": "a.rb", "patch": "@@ -10,2 +10,3 @@\n x"}]}
        self.assertTrue(bt.moved_after_comment(case(), "2026-01-02T00:00:00Z", self.commits, "H", compare))
        self.assertEqual(calls, [("c1", "H")])

    def test_no_commit_after_comment_means_unchanged(self):
        self.assertFalse(bt.moved_after_comment(case(), "2026-02-01T00:00:00Z", self.commits, "H", lambda b, h: {}))

    def test_compare_failure_is_none(self):
        def boom(b, h):
            raise bt.subprocess.CalledProcessError(1, "gh")
        self.assertIsNone(bt.moved_after_comment(case(), "2026-01-02T00:00:00Z", self.commits, "H", boom))

    def test_line_movement_must_be_within_three_lines(self):
        near = {"files": [{"filename": "a.rb", "patch": "@@ -13 +13 @@\n-old\n+new"}]}
        far = {"files": [{"filename": "a.rb", "patch": "@@ -14 +14 @@\n-old\n+new"}]}
        self.assertTrue(bt.patch_touches(near, "a.rb", 10))
        self.assertFalse(bt.patch_touches(far, "a.rb", 10))


class Tiers(unittest.TestCase):
    def test_fixed_blocks_declined_only_warns_unknown_ignored(self):
        t = bt.tiers([outcome("1", ["B1"], "repo convention", "fixed"), outcome("2", ["B1"], "repo convention", "declined"),
                      outcome("3", ["B2"], "comments policy", "declined"), outcome("4", ["B3"], "test quality", "unknown")])
        self.assertEqual(t["B1"], "block")
        self.assertEqual(t["B2"], "warn")
        self.assertNotIn("B3", t)
        self.assertEqual(t["category:repo_convention"], "block")
        self.assertEqual(t["category:docs"], "warn")
        self.assertNotIn("category:test_gap", t)

    def test_category_keys_are_canonical(self):
        t = bt.tiers([outcome("1", [], "data model/index/query perf", "fixed"), outcome("2", [], "concurrency/idempotency", "declined")])
        self.assertEqual(t, {"category:correctness": "block", "category:perf": "block"})

    def test_overrides_apply_last(self):
        out = bt.apply_overrides([outcome("1", ["B1"], "x", "declined")], {"1": "fixed"})
        self.assertEqual(out[0]["outcome"], "fixed")
        self.assertTrue(out[0]["overridden"])

    def test_checked_in_tiers_are_regenerated_from_outcomes(self):
        with open(os.path.join(HERE, "outcomes.json")) as f:
            outcomes = json.load(f)
        with open(os.path.join(HERE, "rule-tiers.json")) as f:
            checked_in = json.load(f)
        self.assertEqual(checked_in, bt.tiers(outcomes))


if __name__ == "__main__":
    unittest.main()
