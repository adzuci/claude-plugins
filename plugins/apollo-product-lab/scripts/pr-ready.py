#!/usr/bin/env python3
"""pr-ready: refuse to call a PR ready until the AI review ran on its current head and was triaged.

Manual:  python3 scripts/pr-ready.py [--pr N] [--mode warn|block] [--repo-root PATH]
Hook:    python3 scripts/pr-ready.py --hook   (Claude Code PreToolUse on Bash, JSON on stdin)

Contract: framework/50-review-gate.md. Standard library only; needs `gh` and `git` on PATH.
"""
import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys

_RULE_REGISTRY_SPEC = importlib.util.spec_from_file_location(
    "harness_rule_registry", os.path.join(os.path.dirname(os.path.abspath(__file__)), "rule_registry.py"))
_RULE_REGISTRY = importlib.util.module_from_spec(_RULE_REGISTRY_SPEC)
_RULE_REGISTRY_SPEC.loader.exec_module(_RULE_REGISTRY)
DEFAULT_REGISTRY = _RULE_REGISTRY.DEFAULT_REGISTRY
finding_rule_ids = _RULE_REGISTRY.finding_rule_ids

MUST_TRIAGE_CATEGORIES = {"correctness", "compliance", "data_loss", "wiring", "test_gap", "perf", "repo_convention"}
MUST_TRIAGE_SEVERITIES = {"blocker", "major"}
SEVERITY_RANK = {"nit": 0, "minor": 1, "major": 2, "blocker": 3}
BAD_VERDICTS = {"INCOMPLETE", "ESCALATE_HUMAN"}
MODES = ("warn", "block")
DEFAULT_TIERS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "framework", "eval", "replay",
                             "ads-m1-human-reviews", "rule-tiers.json")
CURRENT_SCHEMA = 2
OLD_SCHEMA = 1
TECHNICAL_REBUTTAL = re.compile(
    r"\b(?:"
    r"(?:can(?:no|')?t|not possible|impossible)(?:\s+\S+){0,6}\s+(?:batch(?:ing)?|bulk|index|hint|query|n\+1|scale|callbacks?)"
    r"|(?:batch(?:ing)?|bulk|index|hint|query|n\+1|scale|callbacks?)(?:\s+\S+){0,6}\s+(?:can(?:no|')?t|not possible|impossible)"
    r")\b", re.I)
EVIDENCE_PATH = re.compile(r"(?<![A-Za-z0-9_:/])(?P<path>[A-Za-z0-9_.\-/]+\.[A-Za-z0-9_+-]+):(?P<line>[1-9]\d*)")
EVIDENCE_URL = re.compile(r"https?://\S+", re.I)
EVIDENCE_EXPLANATION = re.compile(r"\b(?:explain|index)\s*:\s*\S+", re.I)
PLACEHOLDERS = {"todo", "tbd", "n", "a", "n/a", "na", "none", "x", "true", "false", "-"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
VALID_VERDICTS = {"APPROVE", "REQUEST_CHANGES", "BLOCK"} | BAD_VERDICTS
VALID_SEVERITIES = {"nit", "minor", "major", "blocker"}
PR_FILE_CAP = 30
GENERATED_BASENAMES = {
    "Gemfile.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "schema.rb", "structure.sql",
}
GENERATED_PARTS = {"fixtures", "recorded_fixtures", "__snapshots__"}


def run(cmd, cwd=None, strip=True):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, ""
    return p.returncode, p.stdout.strip() if strip else p.stdout


def default_gh(args, cwd=None):
    return run(["gh"] + list(args), cwd)


def default_git(args, cwd=None):
    return run(["git"] + list(args), cwd, strip=not args or args[0] != "show")


# ---------- mode ----------

def resolve_mode(flag=None, env=None, repo_root=None):
    env = os.environ if env is None else env
    if flag in MODES:
        return flag
    if env.get("HARNESS_PR_READY_MODE") in MODES:
        return env["HARNESS_PR_READY_MODE"]
    if repo_root:
        try:
            with open(os.path.join(repo_root, ".harness", "config.json")) as f:
                value = json.load(f).get("pr_ready_mode")
            if value in MODES:
                return value
        except (OSError, ValueError, AttributeError):
            pass
    return "warn"


# ---------- record rules ----------

class Problem(str):
    """A problem line plus its tier: block stops the command in every mode, warn only adds context in warn mode."""

    def __new__(cls, text, tier="block", block_in_block_mode=True):
        obj = super().__new__(cls, text)
        obj.tier = tier
        obj.block_in_block_mode = block_in_block_mode
        return obj


def tier_of(problem):
    return getattr(problem, "tier", "block")


def blocks_in_mode(problem, mode):
    return tier_of(problem) == "block" or (mode == "block" and getattr(problem, "block_in_block_mode", True))


def load_tiers(repo_root):
    for path in (os.path.join(repo_root or ".", ".harness", "rule-tiers.json"), DEFAULT_TIERS):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, ValueError):
            continue
    return {}


def load_rule_registry(path=DEFAULT_REGISTRY):
    try:
        return _RULE_REGISTRY.load_registry(path)[1]
    except (OSError, ValueError, TypeError):
        return {}


def registry_informational(finding, registry):
    rules = finding_rule_ids(finding)
    return (bool(rules) and all(rule in registry for rule in rules)
            and all(registry[rule]["status"] in ("shadow", "retired") for rule in rules))


def finding_tier(finding, tiers, registry=None):
    """block | warn | None. Severity blocker/major always blocks; learned tiers only decide the rest."""
    if not isinstance(finding, dict) or not isinstance(tiers, dict):
        return "block"
    registry = load_rule_registry() if registry is None else registry
    if registry_informational(finding, registry):
        return None
    severity = finding.get("severity")
    if isinstance(severity, str) and severity in MUST_TRIAGE_SEVERITIES:
        return "block"
    rules = finding.get("rule") or finding.get("rule_id")
    rules = rules if isinstance(rules, list) else [rules]
    known = [tiers[r] for r in rules if isinstance(r, str) and r in tiers]
    category_only = False
    if not known:
        value = finding.get("category")
        category = value.strip().lower() if isinstance(value, str) else ""
        if "category:" + category in tiers:
            known = [tiers["category:" + category]]
            category_only = True
    if category_only and severity in ("nit", "minor") and category in ("docs", "design"):
        return "warn"
    if "block" in known:
        return "block"
    if known:
        return "warn"
    return "block" if needs_triage(finding) else None


def non_empty(value):
    return bool(value.strip()) if isinstance(value, str) else bool(value)


def valid_lens_severities(value):
    return (isinstance(value, dict) and bool(value)
            and all(isinstance(role, str) and bool(role.strip())
                    and isinstance(severity, str) and severity in SEVERITY_RANK
                    for role, severity in value.items()))


def valid_downgrade_evidence(value):
    return (isinstance(value, dict)
            and isinstance(value.get("file"), str) and bool(value["file"].strip())
            and value["file"].strip().lower() not in PLACEHOLDERS
            and isinstance(value.get("line"), int) and not isinstance(value["line"], bool) and value["line"] > 0
            and isinstance(value.get("why"), str) and len(value["why"].strip()) >= 15
            and not placeholder_only(value["why"]))


def valid_size_waiver(value):
    return (isinstance(value, dict)
            and isinstance(value.get("reason"), str) and len(value["reason"].strip()) >= 15
            and not placeholder_only(value["reason"])
            and isinstance(value.get("approver"), str) and bool(value["approver"].strip())
            and value["approver"].strip().lower() not in PLACEHOLDERS)


def generated_file(path):
    normalized = str(path or "").replace("\\", "/").strip("/")
    parts = normalized.split("/")
    return (bool(normalized) and
            (parts[-1] in GENERATED_BASENAMES or bool(GENERATED_PARTS.intersection(parts))))


def review_file_count(files):
    return sum(not generated_file(path) for path in (files or []))


def placeholder_only(value, after_label=False):
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    if after_label and ":" in text:
        text = text.split(":", 1)[1]
    words = re.findall(r"[a-z0-9]+", text)
    return bool(words) and all(word in PLACEHOLDERS for word in words)


def valid_disposition_evidence(value):
    if not isinstance(value, str):
        return False
    evidence = value.strip()
    if len(evidence) < 15 or placeholder_only(evidence, after_label=True):
        return False
    return bool(EVIDENCE_PATH.search(evidence) or EVIDENCE_URL.search(evidence)
                or EVIDENCE_EXPLANATION.search(evidence))


def technical_rebuttal(reason):
    normalized = str(reason or "").translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    return TECHNICAL_REBUTTAL.search(normalized)


def evidence_references(value):
    if not isinstance(value, str):
        return []
    return [(match.group("path"), int(match.group("line"))) for match in EVIDENCE_PATH.finditer(value)]


def snapshot_reference_problem(path, line, head, repo_root, git):
    normalized = str(path or "").strip()
    if (not normalized or os.path.isabs(normalized)
            or ".." in normalized.replace("\\", "/").split("/")):
        return "%s:%s is not a repository-relative path" % (normalized or "?", line)
    ref = "%s:%s" % (head, normalized)
    rc, _ = git(["cat-file", "-e", ref], repo_root)
    if rc != 0:
        return "%s:%s does not exist at head %s" % (normalized, line, head[:10])
    rc, contents = git(["show", ref], repo_root)
    if rc != 0:
        return "%s:%s could not be read at head %s" % (normalized, line, head[:10])
    line_count = len(contents.splitlines())
    if line > line_count:
        return "%s:%s is outside the file's %s lines at head %s" % (normalized, line, line_count, head[:10])
    return None


def evidence_snapshot_problems(finding, head, repo_root, git):
    problems = []
    downgrade = finding.get("downgrade_evidence")
    if isinstance(downgrade, dict):
        problem = snapshot_reference_problem(downgrade.get("file"), downgrade.get("line"), head, repo_root, git)
        if problem:
            problems.append("%s has invalid downgrade_evidence: %s." % (finding.get("id", "?"), problem))
    disposition = finding.get("disposition")
    evidence = disposition.get("evidence") if isinstance(disposition, dict) else None
    for path, line in evidence_references(evidence):
        problem = snapshot_reference_problem(path, line, head, repo_root, git)
        if problem:
            problems.append("%s has invalid disposition.evidence: %s." % (finding.get("id", "?"), problem))
    return problems


def delta_provenance_problems(record, prior):
    prior_findings = prior.get("findings") if isinstance(prior, dict) else None
    if not isinstance(prior_findings, list):
        return ["The delta review's prior record has no findings list. Re-run the review."]
    current = {finding.get("id"): finding for finding in record.get("findings", [])
               if isinstance(finding, dict) and isinstance(finding.get("id"), str)}
    problems = []
    for old in prior_findings:
        if not isinstance(old, dict) or not isinstance(old.get("id"), str):
            problems.append("The delta review's prior record has a malformed finding. Re-run the review.")
            continue
        fid = old["id"]
        carried = current.get(fid)
        if carried is None:
            problems.append("Delta review dropped prior finding %s. Carry every prior finding forward." % fid)
            continue
        if carried.get("severity") != old.get("severity") or carried.get("lens_severities") != old.get("lens_severities"):
            if not valid_downgrade_evidence(carried.get("downgrade_evidence")):
                problems.append(
                    "Delta review changed %s's severity or lens_severities without downgrade_evidence. "
                    "Carry both forward unchanged or cite checked downgrade evidence." % fid)
    return problems


def highest_lens_severity(finding):
    if not isinstance(finding, dict):
        return None, None
    severities = finding.get("lens_severities")
    if not isinstance(severities, dict):
        return None, None
    ranked = [(SEVERITY_RANK[value], role, value) for role, value in severities.items()
              if isinstance(value, str) and value in SEVERITY_RANK]
    if not ranked:
        return None, None
    _, role, severity = max(ranked)
    return role, severity


def effective_finding(finding):
    """Restore the highest lens severity unless snapshot evidence supports a downgrade."""
    if not isinstance(finding, dict):
        return finding
    role, severity = highest_lens_severity(finding)
    recorded = finding.get("severity")
    if (isinstance(severity, str) and severity in SEVERITY_RANK
            and isinstance(recorded, str) and recorded in SEVERITY_RANK
            and SEVERITY_RANK[severity] > SEVERITY_RANK[recorded]
            and not valid_downgrade_evidence(finding.get("downgrade_evidence"))):
        restored = dict(finding)
        restored["severity"] = severity
        return restored
    return finding


def finding_explanation(finding, tiers, registry=None):
    """Why this finding must be triaged, using exactly finding_tier's policy."""
    finding = effective_finding(finding)
    registry = load_rule_registry() if registry is None else registry
    cited = finding_rule_ids(finding)
    statuses = [(rule, registry[rule]["status"]) for rule in cited if rule in registry]
    if registry_informational(finding, registry):
        return "info: registry status %s" % ", ".join("%s=%s" % pair for pair in statuses)
    tier = finding_tier(finding, tiers, registry)
    if not tier:
        return None
    if not isinstance(finding, dict):
        return "block: malformed finding"
    reasons = []
    severity = finding.get("severity") if isinstance(finding, dict) else None
    value = finding.get("category") if isinstance(finding, dict) else None
    category = value.strip().lower() if isinstance(value, str) else ""
    if isinstance(severity, str) and severity in MUST_TRIAGE_SEVERITIES:
        reasons.append("severity floor (%s)" % severity)
    rules = finding.get("rule") or finding.get("rule_id")
    rules = rules if isinstance(rules, list) else [rules]
    learned = [(r, tiers[r]) for r in rules if isinstance(r, str) and r in tiers]
    if learned:
        reasons += ["learned rule tier %s=%s" % pair for pair in learned]
    elif "category:" + category in tiers:
        reasons.append("learned category tier category:%s=%s" % (category, tiers["category:" + category]))
    elif category in MUST_TRIAGE_CATEGORIES:
        reasons.append("must-triage category (%s)" % category)
    return "%s: %s" % (tier, ", ".join(reasons) or "gate policy")


def needs_triage(finding):
    if not isinstance(finding, dict):
        return True
    severity, category = finding.get("severity"), finding.get("category")
    return ((isinstance(severity, str) and severity in MUST_TRIAGE_SEVERITIES) or
            (isinstance(category, str) and category in MUST_TRIAGE_CATEGORIES))


def category_only_advisory(finding, tiers):
    """Docs/design nits learned only from a category stay advisory even in block mode."""
    if not isinstance(finding, dict) or not isinstance(tiers, dict):
        return False
    severity, category = finding.get("severity"), finding.get("category")
    if severity not in ("nit", "minor") or category not in ("docs", "design"):
        return False
    rules = finding.get("rule") or finding.get("rule_id")
    rules = rules if isinstance(rules, list) else [rules]
    return (not any(isinstance(rule, str) and rule in tiers for rule in rules) and
            "category:" + category in tiers)


def where(finding):
    if not isinstance(finding, dict):
        return "?"
    loc = finding.get("file")
    loc = loc if isinstance(loc, str) and loc else "?"
    if finding.get("line"):
        loc += ":%s" % finding["line"]
    return loc


def is_doc_file(path, files):
    """Text docs, plus images next to a text doc. A docs/ directory does not make code documentation."""
    ext = os.path.splitext(path)[1].lower()
    if ext in DOC_EXTENSIONS:
        return True
    if ext not in IMAGE_EXTENSIONS:
        return False
    parent = os.path.dirname(path)
    return any(os.path.dirname(other) == parent and os.path.splitext(other)[1].lower() in DOC_EXTENSIONS
               for other in (files or []))


def docs_only(files):
    return bool(files) and all(is_doc_file(f, files) for f in files)


def same_repo(a, b):
    return bool(a) and bool(b) and str(a).lower() == str(b).lower()


def validate_record(record, head, repo=None, files=None):
    """Reasons a record cannot count as a review of this head. Empty list means valid."""
    if not isinstance(record, dict):
        return ["it is not a JSON object"]
    reasons = []
    schema = record.get("schema")
    if type(schema) is not int or schema not in (OLD_SCHEMA, CURRENT_SCHEMA):
        reasons.append("its schema is not integer version 1 or 2")
    delta_of = record.get("delta_of")
    if delta_of is not None and (not isinstance(delta_of, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", delta_of)):
        reasons.append("its delta_of is not a 40-character commit sha")
    if not isinstance(record.get("repo"), str) or not record["repo"].strip():
        reasons.append("its repo is not a non-empty string")
    elif repo and not same_repo(record["repo"], repo):
        reasons.append("it is for repo %s, not %s" % (record["repo"], repo))
    verdict = record.get("verdict")
    if not isinstance(verdict, str) or verdict not in VALID_VERDICTS:
        reasons.append("its verdict is not APPROVE, REQUEST_CHANGES, BLOCK, INCOMPLETE or ESCALATE_HUMAN")
    if not isinstance(record.get("findings"), list):
        reasons.append("it has no findings list")
    else:
        for index, finding in enumerate(record["findings"], 1):
            if not isinstance(finding, dict):
                reasons.append("finding %s is not an object" % index)
                continue
            if not isinstance(finding.get("id"), str) or not finding["id"].strip():
                reasons.append("finding %s has no non-empty id" % index)
            severity = finding.get("severity")
            if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
                reasons.append("finding %s has an invalid severity" % index)
            if not isinstance(finding.get("category"), str) or not finding["category"].strip():
                reasons.append("finding %s has no non-empty category" % index)
            if not isinstance(finding.get("file"), str) or not finding["file"].strip():
                reasons.append("finding %s has no non-empty file" % index)
            label = finding.get("id") or index
            lens = finding.get("lens_severities")
            if schema == CURRENT_SCHEMA and not valid_lens_severities(lens):
                reasons.append("finding %s has invalid lens_severities" % label)
            elif lens is not None and not valid_lens_severities(lens):
                reasons.append("finding %s has invalid lens_severities" % label)
            downgrade = finding.get("downgrade_evidence")
            if downgrade is not None and not valid_downgrade_evidence(downgrade):
                reasons.append("finding %s has invalid downgrade_evidence" % label)
            disp = finding.get("disposition")
            if isinstance(disp, dict) and "evidence" in disp and not valid_disposition_evidence(disp.get("evidence")):
                reasons.append("finding %s has invalid disposition.evidence" % label)
            if isinstance(disp, dict) and "rebuttal" in disp and not isinstance(disp.get("rebuttal"), bool):
                reasons.append("finding %s has invalid disposition.rebuttal" % label)
    reviewers = record.get("reviewers")
    if not isinstance(reviewers, list):
        reasons.append("it has no reviewers list")
    elif any(not isinstance(r, str) or not r.strip() for r in reviewers):
        reasons.append("its reviewers list contains an empty or non-string reviewer")
    elif not reviewers and not docs_only(files):
        reasons.append("its reviewers list must contain non-empty strings for a non-docs diff")
    if record.get("head_sha") != head:
        reasons.append("its head_sha is %s, not %s" % (str(record.get("head_sha"))[:10], head[:10]))
    return reasons


def size_problems(key_dir, head, files, readfile=None):
    count = review_file_count(files)
    if count <= PR_FILE_CAP:
        return []
    readfile = readfile or (lambda p: open(p).read())
    try:
        record = json.loads(readfile(os.path.join(key_dir, head + ".json")))
    except (OSError, ValueError):
        record = None
    waiver = record.get("size_waiver") if isinstance(record, dict) else None
    if valid_size_waiver(waiver):
        return []
    detail = " The existing size_waiver is invalid." if waiver is not None else ""
    return [Problem(
        "PR size is %s review files after generated-file exclusions; the cap is %s.%s "
        "Next: split the PR, or add size_waiver with a 15+ character reason and named approver to the current-head review record."
        % (count, PR_FILE_CAP, detail), "warn")]


def check_record(record, head, repo_root, git=default_git, tiers=None, prior=None, registry=None):
    """Return a list of problems (reasons 2 to 5) for a valid record that is for the current head."""
    tiers = load_tiers(repo_root) if tiers is None else tiers
    registry = load_rule_registry() if registry is None else registry
    problems = []
    if record.get("schema") == OLD_SCHEMA:
        problems.append(Problem(
            "This review uses schema 1. Re-run the review to record lens_severities and structured evidence.",
            "warn"))
    if record.get("delta_of") is not None:
        problems.extend(Problem(problem) for problem in delta_provenance_problems(record, prior))
    verdict = record.get("verdict")
    if isinstance(verdict, str) and verdict in BAD_VERDICTS:
        problems.append("The review verdict is %s. Re-run the code-review skill on head %s until it completes with a verdict a human can act on." % (verdict, head))
    for f in record.get("findings", []):
        if not isinstance(f, dict):
            problems.append(Problem("The review contains a malformed finding.", "block"))
            continue
        fid = f.get("id", "?")
        disp = f.get("disposition")
        unknown = sorted(set(finding_rule_ids(f)) - set(registry))
        if unknown:
            problems.append(Problem(
                "Record-validation warning: %s cites rule id(s) absent from the registry: %s."
                % (fid, ", ".join(unknown)), "warn", False))
        if registry_informational(f, registry):
            continue
        problems.extend(Problem(problem) for problem in evidence_snapshot_problems(f, head, repo_root, git))
        role, lens_severity = highest_lens_severity(f)
        recorded_severity = f.get("severity")
        if (isinstance(lens_severity, str) and lens_severity in SEVERITY_RANK
                and isinstance(recorded_severity, str) and recorded_severity in SEVERITY_RANK
                and SEVERITY_RANK[lens_severity] > SEVERITY_RANK[recorded_severity]
                and not valid_downgrade_evidence(f.get("downgrade_evidence"))):
            problems.append(Problem(
                "%s is recorded %s but %s rated it %s, with no downgrade_evidence. "
                "Next: restore the higher severity or cite the snapshot line that refutes it."
                % (fid, recorded_severity, role, lens_severity)))
        label = "%s (%s/%s) %s: %s" % (fid, f.get("severity"), f.get("category"), where(f), f.get("summary", f.get("claim", "")))
        if disp is None:
            tier = finding_tier(effective_finding(f), tiers, registry)
            if tier:
                problems.append(Problem(
                    "Untriaged %s. Next: triage %s: fix it, or set disposition to wont_fix/deferred with a reason." % (label, fid),
                    tier, not category_only_advisory(f, tiers)))
            continue
        action = disp.get("action") if isinstance(disp, dict) else None
        if action == "fixed":
            commit = disp.get("commit")
            ok = False
            if commit:
                rc, _ = git(["merge-base", "--is-ancestor", commit, head], repo_root)
                ok = rc == 0
            if not ok:
                problems.append("%s says fixed in %s, but that commit is not an ancestor of head %s. Next: record the real fix commit for %s." % (fid, commit or "(no commit)", head[:10], fid))
        elif action == "wont_fix":
            reason = disp.get("reason")
            if not isinstance(reason, str) or len(reason.strip()) < 15:
                problems.append("%s is wont_fix without a reason (15+ characters). Next: write why %s is not being fixed." % (fid, fid))
        elif action == "deferred":
            ticket, reason = disp.get("ticket"), disp.get("reason")
            if not (isinstance(ticket, str) and ticket.strip() and isinstance(reason, str) and reason.strip()):
                problems.append("%s is deferred without a ticket and reason. Next: add both for %s." % (fid, fid))
        else:
            problems.append("%s has an unknown disposition action %r. Next: use fixed, wont_fix or deferred." % (fid, action))
        if action in ("wont_fix", "deferred"):
            if not isinstance(disp.get("rebuttal"), bool):
                problems.append(Problem(
                    "%s must set disposition.rebuttal to true or false. "
                    "Use true only when disputing the finding, and then add evidence." % fid))
                continue
            rebuttal = disp.get("rebuttal") is True
            evidence_ok = valid_disposition_evidence(disp.get("evidence"))
            claim = technical_rebuttal(disp.get("reason"))
            if rebuttal and not evidence_ok:
                problems.append(Problem(
                    "%s is marked rebuttal:true without valid evidence. "
                    "Next: add evidence with a path:line, URL, explain: output or index: definition, or fix it."
                    % fid))
            elif not rebuttal and claim:
                problems.append(Problem(
                    "%s's reason reads like a technical rebuttal. If it disputes the finding, set rebuttal: true "
                    "and add evidence; otherwise keep rebuttal: false." % fid, "warn", False))
    return problems


def evaluate(key_dir, head, repo_root, git=default_git, listdir=os.listdir, readfile=None, repo=None, files=None):
    """key_dir is .harness/reviews/<pr> or .harness/reviews/branch-<branch>. Returns the problems list."""
    readfile = readfile or (lambda p: open(p).read())
    path = os.path.join(key_dir, head + ".json")
    try:
        record = json.loads(readfile(path))
    except (OSError, ValueError):
        record = None
    if record is not None:
        try:
            reasons = validate_record(record, head, repo, files)
        except Exception as error:
            reasons = ["validation raised %s" % error]
        if reasons:
            return [Problem("No valid AI review record for head %s: %s. Next: run the code-review skill on head %s." %
                            (head[:10], "; ".join(reasons), head), "block")]
        try:
            prior = None
            if record.get("delta_of") is not None:
                prior_path = os.path.join(key_dir, record["delta_of"] + ".json")
                try:
                    prior = json.loads(readfile(prior_path))
                except (OSError, ValueError):
                    prior = None
                prior_reasons = validate_record(prior, record["delta_of"], repo, files)
                if prior_reasons or prior.get("verdict") in BAD_VERDICTS:
                    return [Problem(
                        "Next: re-run a full review; the prior review it builds on is missing, invalid or incomplete.",
                        "block")]
            return check_record(record, head, repo_root, git, prior=prior)
        except Exception as error:
            return [Problem("No valid AI review record for head %s: validation raised %s. Next: run the code-review skill on head %s." %
                            (head[:10], error, head), "block")]
    best = None
    try:
        names = [n for n in listdir(key_dir) if n.endswith(".json")]
    except OSError:
        names = []
    for n in names:
        try:
            rec = json.loads(readfile(os.path.join(key_dir, n)))
        except (OSError, ValueError):
            continue
        if not isinstance(rec, dict):
            continue
        stamp = rec.get("reviewed_at") or ""
        if best is None or stamp > best[0]:
            best = (stamp, rec.get("head_sha") or n[:-5])
    newest = None
    if best:
        sha = best[1]
        rc, out = git(["rev-list", "--count", "%s..%s" % (sha, head)], repo_root)
        behind = "%s commit(s) behind" % out if rc == 0 and out else "an unknown number of commits behind"
        newest = "The newest review is for %s, %s head." % (sha[:10], behind)
    return ["No AI review record for head %s. %s Next: run the code-review skill on head %s." % (head[:10], newest or "No review has run yet.", head)]


# ---------- PR / branch resolution ----------

def resolve_pr(pr, cwd, gh=default_gh):
    """Return (info, why). info has number, head, repo, branch, files; why explains a failure."""
    args = ["pr", "view"] + ([str(pr)] if pr else []) + ["--json", "headRefOid,number,url,headRefName,baseRefName,files"]
    rc, out = gh(args, cwd)
    if rc != 0:
        return None, "gh %s failed (exit %s)" % (" ".join(args[:3]), rc)
    try:
        data = json.loads(out)
        m = re.match(r"https?://[^/]+/([^/]+/[^/]+)/pull/", data.get("url") or "")
        return {"number": int(data["number"]), "head": data["headRefOid"], "repo": m.group(1) if m else None,
                "branch": data.get("headRefName"),
                "base": data.get("baseRefName"),
                "files": [f.get("path") for f in data.get("files") or [] if isinstance(f, dict) and f.get("path")]}, None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, "gh pr view returned something unreadable"


def local_repo(cwd, gh=default_gh):
    rc, out = gh(["repo", "view", "--json", "nameWithOwner"], cwd)
    if rc != 0:
        return None
    try:
        return json.loads(out).get("nameWithOwner")
    except (ValueError, AttributeError):
        return None


def branch_key(git, cwd, requested_branch=None):
    if requested_branch:
        branch = requested_branch
        rc, sha = git(["rev-parse", requested_branch], cwd)
        rc2 = rc
    else:
        rc, branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
        rc2, sha = git(["rev-parse", "HEAD"], cwd)
    if rc != 0 or rc2 != 0 or not branch or branch == "HEAD":
        return None
    return "branch-" + branch.replace("/", "__"), sha


def branch_files(git, cwd, target="HEAD", base=None):
    bases = ["origin/" + base, base] if base else ["origin/HEAD", "origin/master", "origin/main"]
    for base in bases:
        rc, out = git(["diff", "--name-only", "%s...%s" % (base, target)], cwd)
        if rc == 0:
            return [x for x in out.splitlines() if x]
    return None


def repo_root_of(path, git=default_git):
    rc, out = git(["rev-parse", "--show-toplevel"], path)
    return out if rc == 0 and out else os.path.abspath(path or ".")


def format_report(problems, mode, subject):
    if mode == "block":
        lines = ["pr-ready BLOCKED for %s. Fix these before marking the PR ready, asking for review or merging:" % subject]
    else:
        lines = ["TRIAGE REQUIRED for %s." % subject,
                 "Triage every item below exactly as you would a human review comment: fix it, or record wont_fix/deferred with a reason in the review record. Do this before asking a human to review."]
    for i, p in enumerate(problems, 1):
        lines.append("%d. %s" % (i, p))
    return "\n".join(lines)


def cannot_run(mode, why):
    """The gate could not decide. Block mode fails closed; warn mode tells the agent to check by hand."""
    if mode == "block":
        return 2, "pr-ready BLOCKED: the review gate could not run (%s). Fix that, or check the review record by hand and run the command from a shell that is not gated." % why, mode
    return 0, "pr-ready WARNING: the review gate could not run (%s). Check by hand that the AI review ran on the current head and was triaged before asking a human to review." % why, mode


def gate(pr=None, mode=None, repo_root=None, cwd=None, creating=False, repo=None, create_head=None, create_base=None, gh=default_gh,
         git=default_git, env=None, listdir=os.listdir, readfile=None):
    """Returns (exit_code, text, mode). exit 2 when something blocks. Exit 0 with text not starting
    'pr-ready OK' is warn-level context for the agent."""
    cwd = cwd or os.getcwd()
    env = os.environ if env is None else env
    mode_from_flag_or_env = mode if mode in MODES else env.get("HARNESS_PR_READY_MODE")
    mode = resolve_mode(mode, env, None)
    try:
        root = repo_root or repo_root_of(cwd, git)
        if mode_from_flag_or_env not in MODES:
            mode = resolve_mode(None, env, root)
    except Exception as e:
        return cannot_run(mode, "error: %s" % e)
    try:
        return _gate(pr, mode, root, cwd, creating, repo, create_head, create_base, gh, git, listdir, readfile)
    except Exception as e:
        return cannot_run(mode, "error: %s" % e)


def _gate(pr, mode, root, cwd, creating, repo, create_head, create_base, gh, git, listdir, readfile):
    reviews = os.path.join(root, ".harness", "reviews")
    local = local_repo(cwd, gh)
    if repo and not same_repo(repo, local):
        return cannot_run(mode, "the command targets %s but the local repository is %s, so its review record cannot be checked here" % (repo, local or "unknown"))
    if creating:
        keyed = branch_key(git, cwd, create_head)
        if not keyed:
            return cannot_run(mode, "cannot determine the current branch")
        key, head = keyed
        subject = "new PR on %s at %s" % (key[len("branch-"):].replace("__", "/"), head[:10])
        files = branch_files(git, cwd, create_head or "HEAD", create_base)
        if files is None:
            return cannot_run(mode, "the base diff is unavailable. Next: fetch the base branch")
        key_dir = os.path.join(reviews, key)
        problems = evaluate(key_dir, head, root, git, listdir, readfile, repo=local, files=files)
        problems += size_problems(key_dir, head, files, readfile)
        problems = [p + " (No PR exists yet: either create it with --draft and run the review there, or write the record under .harness/reviews/%s/.)" % key if p.startswith("No ") else p for p in problems]
    else:
        info, why = resolve_pr(pr, cwd, gh)
        if not info:
            return cannot_run(mode, why)
        if repo and info["repo"] and not same_repo(repo, info["repo"]):
            return cannot_run(mode, "the PR resolved to %s, not %s" % (info["repo"], repo))
        head = info["head"]
        subject = "PR #%s at %s" % (info["number"], head[:10])
        files = info["files"]
        key_dir = os.path.join(reviews, str(info["number"]))
        problems = evaluate(key_dir, head, root, git, listdir, readfile,
                            repo=info["repo"] or local, files=files)
        problems += size_problems(key_dir, head, files, readfile)
    if not problems:
        return 0, "pr-ready OK: %s reviewed on current head and triaged." % subject, mode
    blocking = any(blocks_in_mode(p, mode) for p in problems)
    text = format_report(problems, "block" if blocking else "warn", subject)
    return (2 if blocking else 0), text, mode


# ---------- command detection ----------

SEPARATORS = {"&&", "||", ";", "|", "&", "|&", ";;", "(", ")"}
FLAGS_WITH_ARG = {"-R", "--repo", "-B", "--base", "-H", "--head", "-t", "--title", "-b", "--body", "-F", "--body-file",
                  "-r", "--reviewer", "-a", "--assignee", "-l", "--label", "-m", "--milestone", "-p", "--project",
                  "-T", "--template", "--add-reviewer", "--remove-reviewer", "--add-assignee", "--remove-assignee",
                  "--add-label", "--remove-label", "--add-project", "--remove-project", "-A", "--author-email",
                  "--match-head-commit", "--subject"}
ENV_ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")
WRAPPERS = {"command", "exec", "time", "builtin", "nohup", "sudo", "env", "xargs", "nice", "timeout", "stdbuf",
            "!", "{", "}", "if", "then", "else", "elif", "do", "while", "until"}
WRAPPER_FLAG_ARGS = {"sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-T", "-U"}, "env": {"-u", "-C", "-S"},
                     "xargs": {"-I", "-n", "-P", "-L", "-s", "-d", "-E", "-a"}, "nice": {"-n"}, "timeout": {"-s", "-k"},
                     "stdbuf": {"-i", "-o", "-e"}}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
PR_URL = re.compile(r"^https?://[^/]+/([^/]+/[^/]+)/pull/(\d+)")


def preprocess(command):
    """Turn unquoted newlines and backticks into command separators; drop line continuations."""
    out, i, n = [], 0, len(command)
    sq = dq = False
    while i < n:
        c = command[i]
        if sq:
            sq = c != "'"
        elif dq:
            if c == "\\" and i + 1 < n:
                out.append(c)
                i += 1
                c = command[i]
            elif c == '"':
                dq = False
        elif c == "\\" and i + 1 < n:
            if command[i + 1] == "\n":
                i += 2
                continue
            out.append(c)
            i += 1
            c = command[i]
        elif c == "'":
            sq = True
        elif c == '"':
            dq = True
        elif c in "\n`":
            c = " ; "
        out.append(c)
        i += 1
    return "".join(out)


def tokenize(command):
    lex = shlex.shlex(preprocess(command), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        return list(lex)
    except ValueError:
        return preprocess(command).split()


def split_segments(command):
    segments, cur = [], []
    for t in tokenize(command or ""):
        if t in SEPARATORS:
            segments.append(cur)
            cur = []
        else:
            cur.append(t)
    segments.append(cur)
    return [strip_redirects(s) for s in segments if s]


def strip_redirects(tokens):
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r"[<>&]+", t):
            i += 2
            continue
        if t.isdigit() and i + 1 < len(tokens) and re.fullmatch(r"[<>&]+", tokens[i + 1]):
            i += 1
            continue
        out.append(t)
        i += 1
    return out


def unwrap(tokens):
    k = 0
    while k < len(tokens):
        t = tokens[k]
        if ENV_ASSIGN.fullmatch(t):
            k += 1
            continue
        base = os.path.basename(t)
        if base in WRAPPERS:
            k += 1
            argflags = WRAPPER_FLAG_ARGS.get(base, set())
            while k < len(tokens) and tokens[k].startswith("-") and len(tokens[k]) > 1:
                k += 2 if tokens[k] in argflags else 1
            if base == "timeout" and k < len(tokens):
                k += 1
            continue
        break
    return tokens[k:]


def parse_gh(rest):
    """Return a dict for a gated gh pr command (kind, pr_arg, repo) or None."""
    repo = None
    i = 0
    while i < len(rest) and rest[i].startswith("-"):
        a = rest[i]
        if a in ("-R", "--repo") and i + 1 < len(rest):
            repo = rest[i + 1]
            i += 2
        elif a.startswith("-R") and len(a) > 2:
            repo = a[2:]
            i += 1
        elif a.startswith("--repo="):
            repo = a.split("=", 1)[1]
            i += 1
        else:
            i += 2 if a in FLAGS_WITH_ARG else 1
    if i + 1 >= len(rest) or rest[i] != "pr":
        return None
    sub, args = rest[i + 1], rest[i + 2:]
    pr_arg, draft, undo, add_reviewer, head, base = None, False, False, False, None, None
    j = 0
    while j < len(args):
        a = args[j]
        if a in FLAGS_WITH_ARG:
            if a in ("-R", "--repo") and j + 1 < len(args):
                repo = args[j + 1]
            if a in ("-H", "--head") and j + 1 < len(args):
                head = args[j + 1]
            if a in ("-B", "--base") and j + 1 < len(args):
                base = args[j + 1]
            if a == "--add-reviewer":
                add_reviewer = True
            j += 2
            continue
        if a.startswith("--repo="):
            repo = a.split("=", 1)[1]
        elif a.startswith("-R") and len(a) > 2:
            repo = a[2:]
        elif a.startswith("--head="):
            head = a.split("=", 1)[1]
        elif a.startswith("--base="):
            base = a.split("=", 1)[1]
        elif a.startswith("-H") and len(a) > 2:
            head = a[2:]
        elif a.startswith("-B") and len(a) > 2:
            base = a[2:]
        elif a.startswith("--add-reviewer="):
            add_reviewer = True
        elif re.match(r"^-[RtHbF]", a) and len(a) > 2:
            pass
        elif a in ("--draft", "--draft=true", "-d"):
            draft = True
        elif a == "--undo":
            undo = True
        elif not a.startswith("-") and pr_arg is None:
            pr_arg = a
        j += 1
    m = PR_URL.match(pr_arg or "")
    if m and not repo:
        repo = m.group(1)
    if sub == "create":
        return {"kind": "create", "pr_arg": None, "repo": repo, "draft": draft, "head": head, "base": base}
    if sub == "ready" and not undo:
        return {"kind": "ready", "pr_arg": pr_arg, "repo": repo}
    if sub == "merge":
        return {"kind": "merge", "pr_arg": pr_arg, "repo": repo}
    if sub == "edit" and add_reviewer:
        return {"kind": "edit", "pr_arg": pr_arg, "repo": repo}
    return None


def is_git_push(rest):
    """Whether tokens after `git` invoke push, including git's global options."""
    i = 0
    while i < len(rest) and rest[i].startswith("-"):
        i += 2 if rest[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    return i < len(rest) and rest[i] == "push"


def _raw_gated_count(command):
    """Conservative backstop for quoting/subshell forms the shell tokenizer cannot bind safely."""
    count = 0
    for match in re.finditer(r"(?is)\bgh\b.*?\bpr\s+(merge|ready|create|edit)\b", command or ""):
        kind = match.group(1).lower()
        tail = (command or "")[match.start():match.start() + 400]
        if kind == "create" and re.search(r"(?:^|\s)(?:--draft(?:=true)?|-d)(?:\s|$)", tail):
            continue
        if kind == "ready" and re.search(r"(?:^|\s)--undo(?:\s|$)", tail):
            continue
        if kind == "edit" and "--add-reviewer" not in tail:
            continue
        count += 1
    return count


def _scan(command, cwd, depth, env):
    targets = []
    tokens = tokenize(command or "")
    state = {"cwd": cwd, "env": dict(env), "has_push": False}

    def process(seg):
        if not seg:
            return
        inline = dict(token.split("=", 1) for token in seg
                      if token.startswith("GH_REPO=") and ENV_ASSIGN.fullmatch(token))
        command_env = dict(state["env"])
        command_env.update(inline)
        toks = unwrap(strip_redirects(seg))
        if not toks:
            base0 = os.path.basename(next((x for x in seg if not ENV_ASSIGN.fullmatch(x)), ""))
            if base0 == "env" and "-S" in seg and depth < 3:
                pos = seg.index("-S")
                if pos + 1 < len(seg):
                    sub, sub_push = _scan(seg[pos + 1], state["cwd"], depth + 1, state["env"])
                    targets.extend(sub)
                    state["has_push"] = state["has_push"] or sub_push
            return
        base = os.path.basename(toks[0])
        if base in ("cd", "pushd"):
            args = [a for a in toks[1:] if not a.startswith("-")]
            if args and state["cwd"] is not None:
                state["cwd"] = os.path.normpath(os.path.join(state["cwd"], os.path.expanduser(args[0])))
            return
        if base == "export":
            state["env"].update(inline)
            return
        if base in SHELLS and depth < 3:
            for k, a in enumerate(toks[1:], 1):
                if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a) and k + 1 < len(toks):
                    sub, sub_push = _scan(toks[k + 1], state["cwd"], depth + 1, command_env)
                    targets.extend(sub)
                    state["has_push"] = state["has_push"] or sub_push
                    return
        if base == "eval" and depth < 3:
            sub, sub_push = _scan(" ".join(toks[1:]), state["cwd"], depth + 1, command_env)
            targets.extend(sub)
            state["has_push"] = state["has_push"] or sub_push
            return
        if base == "git":
            state["has_push"] = state["has_push"] or is_git_push(toks[1:])
            return
        if base != "gh":
            return
        hit = parse_gh(toks[1:])
        if not hit:
            return
        hit["repo"] = hit.get("repo") or inline.get("GH_REPO") or state["env"].get("GH_REPO")
        if hit["kind"] == "create":
            if not hit.pop("draft"):
                targets.append(dict(hit, cwd=state["cwd"]))
        else:
            targets.append(dict(hit, cwd=state["cwd"]))

    cur, i = [], 0
    while i < len(tokens):
        token = tokens[i]
        if token == "(":
            process(cur)
            cur = []
            level, j = 1, i + 1
            while j < len(tokens) and level:
                level += tokens[j] == "("
                level -= tokens[j] == ")"
                j += 1
            inner = shlex.join(tokens[i + 1:j - 1])
            sub, sub_push = _scan(inner, state["cwd"], depth + 1, state["env"])
            targets.extend(sub)
            state["has_push"] = state["has_push"] or sub_push
            i = j
            continue
        if token in SEPARATORS:
            process(cur)
            cur = []
        else:
            cur.append(token)
        i += 1
    process(cur)
    return targets, state["has_push"]


def scan(command, cwd=None, depth=0, env=None):
    """Walk a chained command in order. Target cwd follows `cd`; repository follows GH_REPO."""
    env = os.environ if env is None else env
    targets, _ = _scan(command, cwd, depth, env)
    if depth == 0 and _raw_gated_count(command) > len(targets):
        targets.append({"kind": "unresolved", "pr_arg": None, "repo": None, "cwd": cwd})
    return targets


def contains_git_push(command, cwd=None, env=None):
    """Conservatively find a git push anywhere in this Bash call, including shell/eval strings."""
    env = os.environ if env is None else env
    _, found = _scan(command, cwd, 0, env)
    if found:
        return True
    return bool(re.search(r"(?is)(?:^|[\s;&|()`])(?:[^\s;&|()`]*/)?git(?:\s+[^\s;&|()`]+)*?\s+push(?:\s|$|[;&|()`])",
                          command or ""))


def detect_gated(command):
    """All gated gh pr commands in a possibly chained command, as [(kind, pr_arg)]."""
    return [(t["kind"], t["pr_arg"]) for t in scan(command)]


def pr_number_from_arg(arg):
    if not arg:
        return None
    if str(arg).isdigit():
        return int(arg)
    m = PR_URL.match(str(arg))
    return int(m.group(2)) if m else None


def gh_target(arg):
    """What to hand to `gh pr view`: a number for a number or URL, else the branch name."""
    n = pr_number_from_arg(arg)
    return n if n is not None else (arg or None)


def hook(payload, **deps):
    """Return (exit_code, stdout, stderr) for a Claude Code PreToolUse payload.
    Block-level problems: exit 2 with stderr. Warn-level: exit 0 with additionalContext JSON on stdout."""
    if payload.get("tool_name") != "Bash":
        return 0, "", ""
    command = (payload.get("tool_input") or {}).get("command", "")
    cwd = payload.get("cwd") or os.getcwd()
    scan_env = deps.get("env")
    targets = scan(command, cwd, env=scan_env)
    if not targets:
        return 0, "", ""
    if contains_git_push(command, cwd, scan_env):
        message = "Next: run the git push on its own, then run the gh command in a separate call so the gate checks the pushed head."
        return 2, "", "pr-ready BLOCKED: " + message + "\n"
    worst, texts = 0, []
    for t in targets:
        if t["kind"] == "unresolved":
            root = deps.get("repo_root") or repo_root_of(t["cwd"] or cwd, deps.get("git", default_git))
            mode = resolve_mode(deps.get("mode"), scan_env, root)
            message = "Next: run the gh command directly, not through a subshell or eval, so the gate can check it"
            if mode == "block":
                worst = 2
                texts.append("pr-ready BLOCKED: " + message)
            else:
                texts.append("pr-ready WARNING: " + message)
            continue
        code, text, _ = gate(pr=gh_target(t["pr_arg"]), cwd=t["cwd"] or cwd, creating=(t["kind"] == "create"),
                             repo=t["repo"], create_head=t.get("head"), create_base=t.get("base"), **deps)
        worst = max(worst, code)
        if not text.startswith("pr-ready OK"):
            texts.append(text)
    if not texts:
        return 0, "", ""
    text = "\n\n".join(texts)
    if worst == 2:
        return 2, "", text + "\n"
    return 0, json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}}), ""


def explain_record(path, repo_root=None):
    with open(path) as handle:
        record = json.load(handle)
    tiers = load_tiers(repo_root or os.getcwd())
    registry = load_rule_registry()
    lines = []
    findings = record.get("findings", []) if isinstance(record, dict) else []
    findings = findings if isinstance(findings, list) else []
    for finding in findings:
        fid = finding.get("id", "?") if isinstance(finding, dict) else "?"
        why = finding_explanation(finding, tiers, registry)
        if why and why.startswith("info:"):
            lines.append("%s: info (%s)" % (fid, why))
        elif why and why.startswith("warn:"):
            lines.append("%s: warn (%s)" % (fid, why))
        else:
            lines.append("%s: must triage (%s)" % (fid, why) if why else "%s: may remain untriaged" % fid)
    return "\n".join(lines) if lines else "No findings."


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate PR readiness on a triaged AI review of the current head.")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--repo-root")
    ap.add_argument("--hook", action="store_true", help="Claude Code PreToolUse hook mode (JSON on stdin)")
    ap.add_argument("--explain", metavar="RECORD", help="explain which findings in a review record must be triaged")
    ns = ap.parse_args(argv)
    if ns.explain:
        try:
            print(explain_record(ns.explain, ns.repo_root))
            return 0
        except Exception as e:
            mode = resolve_mode(ns.mode, os.environ, None)
            code, text, _ = cannot_run(mode, "error: %s" % e)
            print(text, file=sys.stderr if code else sys.stdout)
            return code
    if ns.hook:
        try:
            payload = json.load(sys.stdin)
            code, out, err = hook(payload, mode=ns.mode)
        except Exception as e:
            try:
                mode = resolve_mode(ns.mode, None, os.getcwd())
            except Exception:
                mode = "block"
            code, out, err = 0, "", ""
            c, text, _ = cannot_run(mode, "error: %s" % e)
            if c == 2:
                code, err = 2, text + "\n"
            else:
                out = json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}})
        if out:
            sys.stdout.write(out)
        if err:
            sys.stderr.write(err)
        return code
    code, text, _ = gate(pr=ns.pr, mode=ns.mode, repo_root=ns.repo_root)
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
