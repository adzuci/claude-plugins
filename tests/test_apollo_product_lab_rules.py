import json
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "apollo-product-lab"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "apollo_product_lab"
CASES = PLUGIN / "framework" / "eval" / "replay" / "ads-m1-human-reviews" / "cases.jsonl"
TIERS = CASES.parent / "rule-tiers.json"
REPO_RULES = CASES.parent / "repo-rules.json"
SOURCES = list((PLUGIN / "agents").glob("*.md")) + [PLUGIN / "framework" / "apollo-infra-patterns.md",
                                                    PLUGIN / "skills" / "code-review" / "SKILL.md"]
FIXTURE_EXPECTATIONS = {
    "b46_positive.diff": ("b46", True),
    "b46_negative.diff": ("b46", False),
    "m43_positive.diff": ("m43", True),
    "m43_negative.diff": ("m43", False),
    "m44_positive.diff": ("m44", True),
    "m44_negative.diff": ("m44", False),
}


def added_lines(diff):
    return "\n".join(line[1:] for line in diff.splitlines()
                     if line.startswith("+") and not line.startswith("+++"))


def fixture_flags(rule, diff):
    added = added_lines(diff)
    if rule == "b46":
        return bool(re.search(r"next\s+unless\s+.*update_all\(.*\)\s*==\s*1", added))
    if rule == "m43":
        return bool(re.search(r"\beach\s+do\b[\s\S]*\.(?:update_all|update_one|find_one_and_update|delete_\w+)\b",
                              diff)) and not bool(re.search(r"\.(?:save!?|create!?|upsert)\b", added))
    if rule == "m44":
        residual = bool(re.search(r"\$(?:expr|where)\b", added))
        scan_evidence = bool(re.search(
            r"(?:explain[^\n]*(?:COLLSCAN|docsExamined)|documents?\s+(?:examined|scanned)[^\n]*(?:based|basis))",
            added, re.I))
        return residual and scan_evidence
    raise ValueError("unknown fixture rule %s" % rule)


def definition_lines(text):
    ids = set()
    for line in text.splitlines():
        m = re.match(r"^\s*(?:[-*]\s+|#{1,6}\s+|\|\s*)\**([A-Z]{1,2}\d+)\b", line)
        if m:
            ids.add(m.group(1))
    return ids


def defined_rules():
    ids = set()
    for p in SOURCES:
        ids |= definition_lines(p.read_text())
    return ids | set(json.loads(REPO_RULES.read_text())["ids"])


def cited_rules():
    text = "\n".join(p.read_text() for p in (PLUGIN / "agents").glob("*reviewer.md")) + (PLUGIN / "agents" / "db-perf.md").read_text()
    text = re.sub(r"\b[A-Z]{1,2}\d+\s*(?:\u2013|-| to )\s*[A-Z]{0,2}\d+\b", " ", text)
    return set(re.findall(r"\b([A-Z]{1,2}\d+)\b", text)) - {"DS1", "DS2"}


class RuleReferences(unittest.TestCase):
    def test_review_honesty_rules_exist(self):
        self.assertTrue({"B46", "M43", "M44"}.issubset(defined_rules()))

    def test_every_case_rule_is_defined_by_a_reviewer(self):
        defined = defined_rules()
        missing = set()
        for line in CASES.read_text().splitlines():
            missing |= {r for r in json.loads(line)["expected_rules"] if r not in defined}
        self.assertEqual(missing, set())

    def test_every_tier_rule_is_defined_by_a_reviewer(self):
        defined = defined_rules()
        rules = {k for k in json.loads(TIERS.read_text()) if not k.startswith("category:")}
        self.assertEqual(rules - defined, set())

    def test_every_rule_the_reviewers_cite_is_defined_somewhere(self):
        self.assertEqual(cited_rules() - defined_rules(), set())

    def test_a_mention_alone_does_not_define_a_rule(self):
        self.assertEqual(definition_lines("see B99 for details\n- B38 (category x)\n### IP3 fan out\n- **IP4** y\n| IP5 | z |"),
                         {"B38", "IP3", "IP4", "IP5"})

    def test_review_honesty_rules_keep_their_scope_qualifiers(self):
        db = (PLUGIN / "agents" / "db-perf.md").read_text()
        backend = (PLUGIN / "agents" / "backend-reviewer.md").read_text()
        m43 = next(line for line in db.splitlines() if line.startswith("- M43"))
        m44 = next(line for line in db.splitlines() if line.startswith("- M44"))
        b46 = next(line for line in backend.splitlines() if line.startswith("- B46"))
        for term in ("independent", "callbacks", "validations", "ordered: false"):
            self.assertIn(term, m43)
        for term in ("evidence of excess scanning", "documents examined per call", "Partial-index ineligibility alone",
                     "hinted queries"):
            self.assertIn(term, m44)
        for term in ("unexplained dropped work", "idempotent no-ops", "metric or log"):
            self.assertIn(term, b46)

    def test_review_honesty_behavioral_fixture_pairs_exist(self):
        for name, (rule, expected) in FIXTURE_EXPECTATIONS.items():
            fixture = (FIXTURES / name).read_text()
            self.assertIn("diff --git", fixture)
            self.assertEqual(fixture_flags(rule, fixture), expected, name)

    def test_review_honesty_replay_cases_use_exact_rules_and_correct_ip_aliases(self):
        cases = {c["id"]: c for c in map(json.loads, CASES.read_text().splitlines())}
        expected = {
            "ads-m1-4294474986": ["M43", "IP2"],
            "ads-m1-4294465092": ["M44", "IP12"],
            "ads-m1-4294522479": ["B46"],
        }
        for case_id, rules in expected.items():
            self.assertEqual(cases[case_id]["expected_rules"], rules)
            self.assertTrue(cases[case_id]["match"]["rules_only"])
        tiers = json.loads(TIERS.read_text())
        self.assertEqual(tiers["IP2"], "block")
        self.assertEqual(tiers["IP12"], "block")
        self.assertNotIn("IP11", tiers)

    def test_delta_review_instructions_preserve_original_lens_severities(self):
        skill = (PLUGIN / "skills" / "code-review" / "SKILL.md").read_text()
        self.assertIn("every carried finding keeps its original `lens_severities` unchanged", skill)


if __name__ == "__main__":
    unittest.main()
