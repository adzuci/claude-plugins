#!/usr/bin/env python3
"""Learn which review rules block and which only warn, from what we did with past human comments.

Outcome per case:
  fixed     with no reply, a hunk moved within 3 lines after the comment; or our reply clearly describes a completed fix
  declined  our reply says we are not doing it (won't, keeping, intentional ...)
  deferred  our reply says follow-up, ticket, later or defer
  unknown   anything else, including any API or compare failure, and replies that are only acknowledgements

`outcomes-overrides.json` ({case id: {"outcome": ..., "reason": ...}}) holds audited labels and is applied last.

A rule with a fixed case blocks. A category blocks for the must-triage categories or when one of its fixed
cases is major/blocker; otherwise it warns. Deferred and unknown outcomes contribute nothing. Category keys
use the canonical reviewer vocabulary (`category:<name>`), which is what scripts/pr-ready.py looks up.

Usage: python3 build_tiers.py [--author LOGIN] [--from-outcomes | --relabel-stored]
Writes outcomes.json (per case) and rule-tiers.json (rule id and category:<canonical> -> block | warn).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_replay import canonical_category  # noqa: E402

REPO = "apolloio/leadgenie"
TOLERANCE = 3
FIX_WORD = r"(?:fixed|done|changed|removed|moved|renamed|updated|switched|dropped|added)"
FIX_TOKEN = re.compile(r"\b" + FIX_WORD + r"\b", re.I)
FIXED_IN_COMMIT = re.compile(r"\bfixed\s+in\s+(?:[0-9a-f]{7,40}\b|(?:the\s+)?commit\b)", re.I)
FIX_DESCRIPTION = re.compile(
    r"^\s*(?:" + FIX_WORD + r"\b|(?:i|we|this|that|it|the\s+\w+(?:\s+\w+){0,3})\s+"
    r"(?:(?:have|has|was|were)\s+|(?:i|we)['’]ve\s+)?" + FIX_WORD + r"\b)", re.I)
DEFERRED = re.compile(r"\b(?:follow[\s-]?up|ticket|defer(?:red|ring)?|(?:fix|handle|address|do|change)\w*\s+(?:it\s+)?later)\b", re.I)
FUTURE_FIX = re.compile(r"\bwill(?:\s+be)?\b", re.I)
NEGATIVE = re.compile(r"\b(?:hasn'?t(?:\s+been)?\s+fixed|has\s+not(?:\s+been)?\s+fixed|not\s+fixed|won'?t\s+fix|"
                      r"will\s+not|isn'?t|wasn'?t|not\s+in\s+this\s+pr|"
                      r"leaving\s+(?:it\s+)?as\s+is|keeping\s+(?:it\s+)?as\s+is|intentional|"
                      r"on\s+purpose|by\s+design|out\s+of\s+scope)\b", re.I)
NEGATION_WORD = re.compile(r"^(?:hasn'?t|not|won'?t|isn'?t|wasn'?t)$", re.I)
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? ")
MUST_TRIAGE_CATEGORIES = {"correctness", "compliance", "data_loss", "wiring", "test_gap", "perf", "repo_convention"}


def gh_json(path):
    out = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True, check=True).stdout
    return json.loads(out.replace("][", ","))


def head_for_pr(pr, runner=subprocess.run):
    """Return the PR head, or None when it cannot be fetched or decoded."""
    try:
        result = runner(["gh", "pr", "view", str(pr), "-R", REPO, "--json", "headRefOid"],
                        capture_output=True, text=True, check=True)
        return json.loads(result.stdout)["headRefOid"]
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError):
        return None


def patch_touches(data, path, line):
    for f in data.get("files", []):
        if f.get("filename") != path and f.get("previous_filename") != path:
            continue
        if f.get("status") == "removed" or line is None:
            return True
        for hunk_line in (f.get("patch") or "").splitlines():
            m = HUNK.match(hunk_line)
            if m:
                start, length = int(m.group(1)), int(m.group(2) or 1)
                if start - TOLERANCE <= line <= start + length + TOLERANCE:
                    return True
    return False


def first_commit_after(commits, created_at):
    """The first PR commit whose committer date is after the comment, as (sha, parent_sha) or None."""
    later = [c for c in commits if c["commit"]["committer"]["date"] > created_at]
    if not later:
        return None
    by_sha = {c["sha"]: c for c in later}
    children = defaultdict(list)
    indegree = {sha: 0 for sha in by_sha}
    for child in later:
        for parent in child.get("parents") or []:
            parent_sha = parent.get("sha") if isinstance(parent, dict) else None
            if parent_sha in by_sha:
                children[parent_sha].append(child["sha"])
                indegree[child["sha"]] += 1
    order = {c["sha"]: index for index, c in enumerate(commits)}
    ready = [c for c in later if indegree[c["sha"]] == 0]
    ready.sort(key=lambda c: (c["commit"]["committer"]["date"], order[c["sha"]]))
    c = ready[0]
    return c["sha"], (c.get("parents") or [{}])[0].get("sha")


def moved_after_comment(case, created_at, commits, head, compare):
    """True | False | None (None: could not tell). compare(base, head) returns the compare API json."""
    try:
        first = first_commit_after(commits, created_at)
        if first is None:
            return False
        sha, parent = first
        data = compare(parent or sha, head)
        return patch_touches(data, case["path"], case.get("line"))
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError):
        return None


def classify(case, ours, moved):
    """ours: our reply bodies; moved: True | False | None. Returns the outcome string."""
    ours = [body for body in ours if isinstance(body, str)]
    def unnegated_fix(body):
        for sentence in re.split(r"[.!?;\n]+", body):
            statement = FIX_DESCRIPTION.match(sentence)
            explicit = FIXED_IN_COMMIT.search(sentence)
            if (not statement and not explicit) or FUTURE_FIX.search(sentence):
                continue
            match = explicit or next((candidate for candidate in FIX_TOKEN.finditer(sentence)
                                      if candidate.start() < statement.end()), None)
            words = list(re.finditer(r"[\w']+", sentence))
            before = [word.group() for word in words if match and word.end() <= match.start()][-4:]
            if match and not any(NEGATION_WORD.match(word) for word in before):
                return True
        return False

    has_fix = any(unnegated_fix(body) for body in ours)
    if has_fix:
        return "fixed"
    if any(DEFERRED.search(body) for body in ours):
        return "deferred"
    if any(NEGATIVE.search(body) for body in ours):
        return "declined"
    if not ours and isinstance(case, dict) and case.get("comment_kind") == "line" and moved is True:
        return "fixed"
    return "unknown"


def tiers(outcomes):
    seen = defaultdict(set)
    for o in outcomes:
        if o["outcome"] not in ("fixed", "declined"):
            continue
        keys = [(rule, o["outcome"]) for rule in o["expected_rules"]]
        canon = canonical_category(o["category"])
        if canon:
            category_blocks = canon in MUST_TRIAGE_CATEGORIES or (o["outcome"] == "fixed" and o.get("severity") in ("blocker", "major"))
            keys.append(("category:" + canon, "fixed" if category_blocks else "declined"))
        for key, contribution in keys:
            seen[key].add(contribution)
    return {k: ("block" if "fixed" in v else "warn") for k, v in sorted(seen.items())}


def apply_overrides(outcomes, overrides):
    for o in outcomes:
        if o["id"] in overrides:
            override = overrides[o["id"]]
            if isinstance(override, dict):
                o["outcome"] = override["outcome"]
                o["override_reason"] = override.get("reason")
            else:
                o["outcome"] = override
            o["overridden"] = True
    return outcomes


def rebuild_tiers_from_outcomes(outcomes_path, overrides_path, tiers_path):
    """Offline tier rebuild used by --from-outcomes and its regression test."""
    outcomes = json.load(open(outcomes_path))
    try:
        overrides = json.load(open(overrides_path))
    except (OSError, ValueError):
        overrides = {}
    with open(tiers_path, "w") as f:
        json.dump(tiers(apply_overrides(outcomes, overrides)), f, indent=1, sort_keys=True)


def relabel_stored(outcomes_path, overrides_path, tiers_path):
    """Reclassify stored replies/movement and rebuild both generated files without GitHub."""
    outcomes = json.load(open(outcomes_path))
    try:
        overrides = json.load(open(overrides_path))
    except (OSError, ValueError):
        overrides = {}
    for outcome in outcomes:
        reply = outcome.get("our_reply")
        if not isinstance(reply, str) and "moved" not in outcome:
            continue
        relabeled = classify(
            {"comment_kind": outcome.get("comment_kind", "line")},
            [reply] if isinstance(reply, str) else [], outcome.get("moved"))
        outcome["outcome"] = relabeled
        outcome.pop("overridden", None)
        outcome.pop("override_reason", None)
    apply_overrides(outcomes, overrides)
    with open(outcomes_path, "w") as f:
        json.dump(outcomes, f, indent=1, sort_keys=True)
    with open(tiers_path, "w") as f:
        json.dump(tiers(outcomes), f, indent=1, sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default="akansh-eng")
    ap.add_argument("--from-outcomes", action="store_true", help="rebuild rule-tiers.json from stored outcomes without GitHub")
    ap.add_argument("--relabel-stored", action="store_true", help="relabel stored replies/movement and rebuild tiers without GitHub")
    ns = ap.parse_args()
    outcomes_path = os.path.join(HERE, "outcomes.json")
    overrides_path = os.path.join(HERE, "outcomes-overrides.json")
    tiers_path = os.path.join(HERE, "rule-tiers.json")
    if ns.from_outcomes:
        rebuild_tiers_from_outcomes(outcomes_path, overrides_path, tiers_path)
        return
    if ns.relabel_stored:
        relabel_stored(outcomes_path, overrides_path, tiers_path)
        return
    cases = [json.loads(line) for line in open(os.path.join(HERE, "cases.jsonl")) if line.strip()]
    try:
        overrides = json.load(open(overrides_path))
    except (OSError, ValueError):
        overrides = {}
    compare = lambda base, head: json.loads(subprocess.run(
        ["gh", "api", f"repos/{REPO}/compare/{base}...{head}"], capture_output=True, text=True, check=True).stdout)
    outcomes = []
    for pr in sorted({c["pr"] for c in cases}):
        head = head_for_pr(pr)
        if head is None:
            for case in (c for c in cases if c["pr"] == pr):
                outcomes.append({"id": case["id"], "pr": pr, "url": case["url"], "category": case["category"],
                                 "expected_rules": case["expected_rules"], "severity": case.get("severity"),
                                 "outcome": "unknown", "comment_kind": case["comment_kind"], "moved": None,
                                 "our_reply": None})
            continue
        replies, created = defaultdict(list), {}
        for c in gh_json(f"repos/{REPO}/pulls/{pr}/comments"):
            created[c["id"]] = c.get("created_at")
            if c.get("in_reply_to_id"):
                replies[c["in_reply_to_id"]].append(c)
        try:
            commits = gh_json(f"repos/{REPO}/pulls/{pr}/commits")
        except subprocess.CalledProcessError:
            commits = None
        for case in (c for c in cases if c["pr"] == pr):
            ours = [r["body"] for r in replies.get(case["comment_id"], []) if r["user"]["login"] == ns.author]
            moved = None
            if case["comment_kind"] == "line" and commits is not None and created.get(case["comment_id"]):
                moved = moved_after_comment(case, created[case["comment_id"]], commits, head, compare)
            outcomes.append({"id": case["id"], "pr": pr, "url": case["url"], "category": case["category"],
                             "expected_rules": case["expected_rules"], "outcome": classify(case, ours, moved),
                             "severity": case.get("severity"), "comment_kind": case["comment_kind"], "moved": moved,
                             "our_reply": (ours[0][:200] if ours else None)})
    apply_overrides(outcomes, overrides)
    with open(outcomes_path, "w") as f:
        json.dump(outcomes, f, indent=1, sort_keys=True)
    with open(tiers_path, "w") as f:
        json.dump(tiers(outcomes), f, indent=1, sort_keys=True)
    counts = defaultdict(int)
    for o in outcomes:
        counts[o["outcome"]] += 1
    print(dict(counts))


if __name__ == "__main__":
    main()
