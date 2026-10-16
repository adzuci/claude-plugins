#!/usr/bin/env python3
"""Explain failing and pending PR checks and give one next action for each."""
import argparse
import json
import os
import re
import subprocess
import sys

PATTERNS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "framework", "references", "ci-patterns.yml")
FAIL_BUCKETS = {"fail", "cancel", "failed", "cancelled"}
PENDING_BUCKETS = {"pending", "queued", "in_progress", "waiting"}
SPEC_PATH = re.compile(r"(?:^|[\s:(])((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:_spec|\.test|\.spec)\.(?:rb|py|js|jsx|ts|tsx))(?=[:\s)]|$)", re.M)
ERROR_LINE = re.compile(r"(?:error|exception|failed|failure|fatal|traceback|enoent)", re.I)


def run(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def default_gh(args, cwd=None):
    return run(["gh"] + list(args), cwd)


def default_git(args, cwd=None):
    return run(["git"] + list(args), cwd)


def _json_call(runner, args, label, ok_codes=(0,)):
    code, output = runner(args)
    if code not in ok_codes:
        raise RuntimeError("%s failed" % label)
    try:
        return json.loads(output)
    except (TypeError, ValueError):
        raise RuntimeError("%s returned invalid JSON" % label)


def load_patterns(path=PATTERNS_PATH):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise RuntimeError("cannot read CI patterns: %s" % exc)
    required = {"knapsack_empty_queue", "sensitive_file_approval", "policy-bot", "flaky_known"}
    if not isinstance(data, dict) or not required.issubset(data):
        raise RuntimeError("CI patterns must define %s" % ", ".join(sorted(required)))
    for name, item in data.items():
        if not isinstance(item, dict) or not isinstance(item.get("patterns"), list) or not isinstance(item.get("next"), str):
            raise RuntimeError("invalid CI pattern entry: %s" % name)
        try:
            for pattern in item["patterns"]:
                re.compile(pattern, re.I)
        except (re.error, TypeError) as exc:
            raise RuntimeError("invalid CI regex in %s: %s" % (name, exc))
    return data


def _run_id(link):
    match = re.search(r"/actions/runs/(\d+)", link or "")
    return match.group(1) if match else None


def _job_id(link):
    match = re.search(r"/job/(\d+)", link or "")
    return match.group(1) if match else None


def _job_log(output, check_name):
    prefixed = []
    for line in output.splitlines():
        match = re.match(r"^([^:\t]+)(?::|\t)(?:[^\t]*\t)?\s*(.*)$", line)
        if match and match.group(1).strip() == check_name:
            prefixed.append(match.group(2))
    return "\n".join(prefixed) if prefixed else output


def _first_error(log):
    for line in log.splitlines():
        cleaned = line.strip()
        if cleaned and ERROR_LINE.search(cleaned):
            return cleaned[:240]
    return next((line.strip()[:240] for line in log.splitlines() if line.strip()), "failure log had no error line")


def _matches(item, text):
    return any(re.search(pattern, text, re.I) for pattern in item.get("patterns", []))


def _behind_base(git, head_sha, base_ref):
    code, output = git(["rev-list", "--count", "%s..origin/%s" % (head_sha, base_ref)])
    if code:
        code, output = git(["rev-list", "--count", "%s..%s" % (head_sha, base_ref)])
    if code:
        return None
    try:
        return int(output.strip())
    except ValueError:
        return None


def classify_failure(check, log, changed_files, head_sha, base_ref, patterns, git, attempt=1):
    text = "%s\n%s" % (check.get("name", ""), log)
    for name in ("sensitive_file_approval", "policy-bot"):
        if _matches(patterns[name], text):
            return name, patterns[name]["next"], None
    if attempt > 1 and _matches(patterns["knapsack_empty_queue"], text):
        return "knapsack_empty_queue", patterns["knapsack_empty_queue"]["next"], "workflow rerun attempt %s" % attempt
    if _matches(patterns["flaky_known"], text):
        return "flaky_known", patterns["flaky_known"]["next"], None

    specs = set(SPEC_PATH.findall(log))
    changed = set(changed_files)
    behind = _behind_base(git, head_sha, base_ref)
    if specs and not any(path in changed for path in specs) and behind and behind > 0:
        return "stale_branch", "merge the base and rerun", "%s commit(s) behind; failing spec is not changed by the PR" % behind
    error = _first_error(log)
    return "real_failure", "fix the first error: %s" % error, error


def diagnose(pr, repo=None, gh=default_gh, git=default_git, patterns_path=PATTERNS_PATH):
    repo_args = ["--repo", repo] if repo else []
    pr_data = _json_call(gh, ["pr", "view", str(pr), "--json", "headRefOid,baseRefName,files"] + repo_args, "gh pr view")
    checks = _json_call(gh, ["pr", "checks", str(pr), "--json", "name,state,bucket,link,workflow"] + repo_args, "gh pr checks", (0, 1, 8))
    patterns = load_patterns(patterns_path)
    changed_files = [item.get("path") for item in pr_data.get("files", []) if item.get("path")]
    rows = []
    for check in checks:
        bucket = str(check.get("bucket") or check.get("state") or "").lower()
        if bucket in PENDING_BUCKETS:
            rows.append({"check": check.get("name", "unknown"), "state": "pending", "classification": "pending", "next": "wait for the check to finish"})
            continue
        if bucket not in FAIL_BUCKETS:
            continue
        log = ""
        attempt = 1
        run_id = _run_id(check.get("link"))
        if run_id:
            code, output = gh(["run", "view", run_id, "--json", "attempt"] + repo_args)
            if code == 0:
                try:
                    attempt = int(json.loads(output).get("attempt", 1))
                except (AttributeError, TypeError, ValueError):
                    attempt = 1
            job_id = _job_id(check.get("link"))
            job_args = ["--job", job_id] if job_id else []
            code, output = gh(["run", "view", run_id] + job_args + ["--log-failed"] + repo_args)
            if code == 0:
                log = "\n".join(_job_log(output, check.get("name", "unknown")).splitlines()[-80:])
        classification, next_action, detail = classify_failure(
            check, log, changed_files, pr_data.get("headRefOid", ""), pr_data.get("baseRefName", ""), patterns, git, attempt
        )
        rows.append({
            "check": check.get("name", "unknown"), "state": "failed", "classification": classification,
            "detail": detail, "next": next_action, "run_id": run_id, "log_tail": log,
        })
    return {"ok": not rows, "pr": pr, "head_sha": pr_data.get("headRefOid"), "checks": rows}


def render(result):
    if not result["checks"]:
        return "CI doctor: OK\nNo failing or pending checks."
    widths = [5, 7, 14]
    header = "%-*s  %-*s  %-*s  %s" % (widths[0], "State", widths[1], "Class", widths[2], "Check", "Next")
    lines = ["CI doctor: NEEDS ACTION", header, "-" * len(header)]
    for row in result["checks"]:
        lines.append("%-*s  %-*s  %-*s  %s" % (
            widths[0], row["state"], widths[1], row["classification"], widths[2], row["check"], row["next"]
        ))
        lines.append("Next: " + row["next"])
    return "\n".join(lines)


def main(argv=None, gh=default_gh, git=default_git):
    parser = argparse.ArgumentParser(description="Classify failing and pending checks on a PR.")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--repo")
    parser.add_argument("--patterns", default=PATTERNS_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = diagnose(args.pr, args.repo, gh, git, args.patterns)
        print(json.dumps(result, sort_keys=True) if args.json else render(result))
        return 0 if result["ok"] else 1
    except RuntimeError as exc:
        payload = {"ok": False, "error": str(exc), "next": "check gh/git access and the CI pattern file"}
        print(json.dumps(payload, sort_keys=True) if args.json else "Error: %s\nNext: %s" % (exc, payload["next"]), file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
