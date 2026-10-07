#!/usr/bin/env python3
"""Collect open apolloio/claude-plugins PR facts for triage (read-only, stdlib + gh)."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

REPO = "apolloio/claude-plugins"
STALE_DAYS = 42
LIST_FIELDS = (
    "number,title,author,isDraft,createdAt,labels,additions,deletions,"
    "changedFiles,baseRefName,headRefName,mergeable,reviewDecision,reviewRequests"
)
FAIL_RUNS = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}
FAIL_STATES = {"FAILURE", "ERROR"}
SHARED_EXACT = {
    "README.md",
    "SKILL_INVENTORY.md",
    "tests/test_marketplace.py",
}
SHARED_PREFIXES = (
    ".claude-plugin/",
    ".codex-plugin/",
    ".agents/",
    ".github/",
)


def gh_json(args):
    out = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def gh_text(args):
    out = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True)
    return out.stdout


def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def cutoff_date(today=None, days=STALE_DAYS):
    return (today or datetime.now(timezone.utc).date()) - timedelta(days=days)


def last_commit_date(commits):
    """ISO date string of the last commit in the list, or None."""
    if not commits:
        return None
    c = commits[-1]
    return c.get("committedDate") or c.get("authoredDate")


def checks_status(rollup):
    """'failing' | 'pending' | 'green' per the triage rule."""
    pending = False
    for item in rollup or []:
        kind = item.get("__typename")
        if kind == "StatusContext":
            if (item.get("state") or "").upper() in FAIL_STATES:
                return "failing"
            continue
        if (item.get("conclusion") or "").upper() in FAIL_RUNS:
            return "failing"
        if item.get("status") and item.get("status").upper() != "COMPLETED":
            pending = True
    return "pending" if pending else "green"


def parse_codeowners(text):
    """List of (pattern, owners) in file order."""
    rules = []
    for line in (text or "").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        rules.append((parts[0], parts[1:]))
    return rules


def pattern_matches(pattern, path):
    if pattern == "*":
        return True
    anchored = pattern.startswith("/")
    pat = pattern.lstrip("/")
    if pat.endswith("/"):
        return path.startswith(pat) if anchored else (
            path.startswith(pat) or ("/" + pat) in ("/" + path)
        )
    if anchored:
        return fnmatch.fnmatchcase(path, pat) or path.startswith(pat + "/")
    return fnmatch.fnmatchcase(path, pat) or fnmatch.fnmatchcase(
        path.rsplit("/", 1)[-1], pat
    )


def owners_for_path(rules, path):
    """Most specific match: longest pattern, later entry wins ties; '*' is the floor."""
    best = None
    best_len = -1
    for pattern, owners in rules:
        if pattern_matches(pattern, path):
            length = 0 if pattern == "*" else len(pattern.strip("/"))
            if length >= best_len:
                best, best_len = owners, length
    return best or []


def is_shared(path):
    return path in SHARED_EXACT or path.startswith(SHARED_PREFIXES) or (
        path.startswith("release-please") or path == ".release-please-manifest.json"
    )


def pr_owners(rules, paths):
    """Union of owners over non-shared paths (all paths if only shared ones)."""
    picked = [p for p in paths if not is_shared(p)] or list(paths)
    seen = []
    for p in picked:
        for o in owners_for_path(rules, p):
            if o not in seen:
                seen.append(o)
    return seen


def approvals_newer_than_head(latest_reviews, head_date):
    if not head_date:
        return False
    head = parse_ts(head_date)
    return any(
        r.get("state") == "APPROVED"
        and r.get("submittedAt")
        and parse_ts(r["submittedAt"]) > head
        for r in latest_reviews or []
    )


def stacked_on(base, heads):
    """(base branch, PR number) when base != main; heads maps head branch -> PR number."""
    if not base or base == "main":
        return None
    return {"base": base, "pr": heads.get(base)}


def build_record(pr, detail, paths, rules, heads, cutoff):
    last = last_commit_date(detail.get("commits"))
    return {
        "number": pr["number"],
        "title": pr["title"],
        "author": (pr.get("author") or {}).get("login"),
        "draft": pr["isDraft"],
        "created": pr["createdAt"][:10],
        "last_commit_date": last[:10] if last else None,
        "additions": pr["additions"],
        "base": pr["baseRefName"],
        "stacked_on": stacked_on(pr["baseRefName"], heads),
        "labels": [lb["name"] for lb in pr.get("labels", [])],
        "mergeable": pr["mergeable"],
        "review_decision": pr.get("reviewDecision"),
        "requested_reviewers": [
            r.get("login") or r.get("name") for r in pr.get("reviewRequests", [])
        ],
        "checks": checks_status(detail.get("statusCheckRollup")),
        "owners": pr_owners(rules, paths),
        "approvals_newer_than_head": approvals_newer_than_head(
            detail.get("latestReviews"), last
        ),
        "stale_candidate": bool(last) and parse_ts(last).date() < cutoff,
    }


def collect(today=None):
    cutoff = cutoff_date(today)
    prs = gh_json(["pr", "list", "-R", REPO, "--limit", "200", "--state", "open",
                   "--json", LIST_FIELDS])
    heads = {p["headRefName"]: p["number"] for p in prs}
    co = gh_text(["api", f"repos/{REPO}/contents/.github/CODEOWNERS",
                  "-H", "Accept: application/vnd.github.raw"])
    rules = parse_codeowners(co)
    records = []
    for pr in prs:
        n = str(pr["number"])
        detail = gh_json(["pr", "view", n, "-R", REPO, "--json",
                          "commits,statusCheckRollup,latestReviews"])
        names = gh_text(["pr", "diff", n, "-R", REPO, "--name-only"]).split()
        records.append(build_record(pr, detail, names, rules, heads, cutoff))
    return cutoff, records


def to_table(records):
    cols = ["number", "author", "draft", "created", "last_commit_date", "additions",
            "base", "stacked_on", "checks", "mergeable", "review_decision", "owners",
            "approvals_newer_than_head", "stale_candidate", "labels", "title"]
    rows = ["\t".join(cols)]
    for r in records:
        cells = []
        for c in cols:
            v = r[c]
            if c == "stacked_on":
                v = ("#%s" % v["pr"] if v and v["pr"] else v["base"]) if v else ""
            elif isinstance(v, list):
                v = ",".join(str(x) for x in v)
            cells.append(str(v))
        rows.append("\t".join(cells))
    return "\n".join(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", action="store_true", help="TSV instead of JSON")
    args = ap.parse_args(argv)
    try:
        cutoff, records = collect()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"collect_prs failed: {exc}", file=sys.stderr)
        return 1
    header = f"# snapshot={date.today()} stale_cutoff={cutoff} open={len(records)}"
    if args.table:
        print(header)
        print(to_table(records))
    else:
        print(json.dumps({"snapshot": str(date.today()), "stale_cutoff": str(cutoff),
                          "prs": records}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
