#!/usr/bin/env python3
"""Require evidence beside completion claims in a Markdown status report."""
import argparse
import json
import os
import re
import subprocess
import sys

CLAIM = re.compile(r"\b(done|fixed|pass|passes|passed|merged|pushed|deployed|verified|green|works)\b", re.I)
NEGATED = re.compile(r"\b(?:not|never)\b[^.;]*(?:done|fixed|pass(?:es|ed)?|merged|pushed|deployed|verified|green|works)\b", re.I)
PLANNED = re.compile(r"^\s*(?:[-*]\s*)?(?:next|todo|plan(?:ned)?|later)\s*:", re.I)
SHA = re.compile(r"(?<![0-9a-f])([0-9a-f]{7,40})(?![0-9a-f])", re.I)
URL = re.compile(r"https?://[^\s)>]+", re.I)
CMD_EXIT = re.compile(r"\bcmd\s*:.+\bexit(?:\s+status)?\s*(?:[:=]|code\s*)?\s*0\b", re.I)
PATH_TOKEN = re.compile(r"`([^`]+)`|(?<![\w/])((?:(?:\.?\.?/)?[\w.-]+(?:/[\w .-]+)+\.[A-Za-z0-9_-]+)|(?:[\w.-]+\.(?:log|txt|json|xml|out)))")


def run(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def default_git(args, cwd=None):
    return run(["git"] + list(args), cwd)


def _path_exists(value, report_dir, cwd):
    value = value.strip().rstrip(".,:;")
    if not value or value.lower().startswith(("cmd:", "http://", "https://")):
        return False
    candidates = [value] if os.path.isabs(value) else [os.path.join(report_dir, value), os.path.join(cwd, value)]
    return any(os.path.isfile(path) for path in candidates)


def evidence(text, report_dir, cwd, git):
    if URL.search(text) or CMD_EXIT.search(text):
        return True
    for sha in SHA.findall(text):
        if git(["cat-file", "-e", "%s^{commit}" % sha], cwd)[0] == 0:
            return True
    for match in PATH_TOKEN.finditer(text):
        value = match.group(1) or match.group(2)
        if _path_exists(value, report_dir, cwd):
            return True
    return False


def claim_clauses(line):
    return [clause.strip() for clause in re.split(r"(?:[.!?](?:\s+|$)|;|\n+)", line)
            if CLAIM.search(clause) and not NEGATED.search(clause) and not PLANNED.search(clause)]


def verify_report(path, git=default_git, cwd=None):
    cwd = os.path.abspath(cwd or os.getcwd())
    report = os.path.abspath(path)
    try:
        with open(report) as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise RuntimeError("cannot read report: %s" % exc)
    unsupported = []
    checked = 0
    for index, line in enumerate(lines):
        clauses = claim_clauses(line)
        if not clauses:
            continue
        cursor = index + 1
        following = []
        while cursor < len(lines) and (not lines[cursor].strip() or lines[cursor][:1].isspace()):
            if lines[cursor].strip():
                following.append(lines[cursor])
            cursor += 1
        for clause in clauses:
            checked += 1
            if not evidence("\n".join([clause] + following), os.path.dirname(report), cwd, git):
                unsupported.append({"line": index + 1, "claim": clause, "next": "add a resolving commit sha, URL, existing output path, or cmd: line with exit status 0"})
    return {"ok": not unsupported, "report": report, "claims_checked": checked, "unsupported": unsupported}


def render(result):
    if result["ok"]:
        return "Claims verified: OK (%s claim line(s))" % result["claims_checked"]
    lines = ["Claims verified: NEEDS ACTION"]
    for item in result["unsupported"]:
        lines.extend(["Line %s: %s" % (item["line"], item["claim"]), "Next: " + item["next"]])
    return "\n".join(lines)


def main(argv=None, git=default_git):
    parser = argparse.ArgumentParser(description="Check that status-report claims carry nearby evidence.")
    parser.add_argument("report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = verify_report(args.report, git)
        print(json.dumps(result, sort_keys=True) if args.json else render(result))
        return 0 if result["ok"] else 1
    except RuntimeError as exc:
        payload = {"ok": False, "error": str(exc), "next": "check the report path and repository"}
        print(json.dumps(payload, sort_keys=True) if args.json else "Error: %s\nNext: %s" % (exc, payload["next"]), file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
