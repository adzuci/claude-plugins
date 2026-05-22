#!/usr/bin/env python3
"""
analyze_context.py — Parse /context output and identify potential issues.

Accepts raw /context output (passed via stdin or --input file) and returns
structured JSON identifying items that shouldn't be in context on a cold start.

Usage:
    claude -p '/context' | python3 analyze_context.py
    python3 analyze_context.py --input /tmp/context-output.txt
    python3 analyze_context.py --input-json '{"pct": 45, "contributors": [...]}'
"""

import argparse
import json
import re
import sys

BASELINE_THRESHOLD_PCT = 15

SUSPECT_PATTERNS = [
    (r"node_modules", "node_modules should be in .claudeignore"),
    (r"\.git/", ".git/ should be in .claudeignore"),
    (r"dist/", "dist/ build output should be in .claudeignore"),
    (r"build/", "build/ output should be in .claudeignore"),
    (r"vendor/", "vendor/ should be in .claudeignore"),
    (r"\.next/", ".next/ build cache should be in .claudeignore"),
    (r"__pycache__", "__pycache__ should be in .claudeignore"),
    (r"\.pyc$", ".pyc files should be in .claudeignore"),
    (r"package-lock\.json", "package-lock.json is large; consider .claudeignore"),
    (r"yarn\.lock", "yarn.lock is large; consider .claudeignore"),
    (r"pnpm-lock\.yaml", "pnpm-lock.yaml is large; consider .claudeignore"),
    (r"Gemfile\.lock", "Gemfile.lock is large; consider .claudeignore"),
    (r"poetry\.lock", "poetry.lock is large; consider .claudeignore"),
    (r"Cargo\.lock", "Cargo.lock is large; consider .claudeignore"),
    (r"\.min\.js$", "minified JS files are not useful for Claude"),
    (r"\.min\.css$", "minified CSS files are not useful for Claude"),
    (r"\.map$", "source map files should be in .claudeignore"),
    (r"coverage/", "coverage reports should be in .claudeignore"),
    (r"\.coverage", "coverage files should be in .claudeignore"),
    (r"\.log$", "log files should be in .claudeignore"),
    (r"tmp/", "tmp/ should be in .claudeignore"),
    (r"temp/", "temp/ should be in .claudeignore"),
]

HIGH_PCT_THRESHOLD = 5.0


def parse_context_output(raw_text):
    """Parse raw /context command output into structured data."""
    lines = raw_text.strip().splitlines()
    result = {"pct": None, "contributors": []}

    for line in lines:
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
        if pct_match and result["pct"] is None:
            if "context" in line.lower() or "window" in line.lower():
                result["pct"] = float(pct_match.group(1))
                continue

        contributor_match = re.match(
            r"^\s*(?:[-•]\s*)?(.+?):\s*(\d+(?:\.\d+)?)\s*%", line
        )
        if contributor_match:
            name = contributor_match.group(1).strip()
            pct = float(contributor_match.group(2))
            result["contributors"].append({"name": name, "pct": pct})

    return result


def analyze_contributors(contributors):
    """Analyze contributors for potential issues."""
    issues = []
    high_pct_items = []

    for item in contributors:
        name = item.get("name", "")
        pct = item.get("pct", 0)

        for pattern, reason in SUSPECT_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                issues.append({
                    "name": name,
                    "pct": pct,
                    "reason": reason,
                    "fix": f"Add to .claudeignore: {_suggest_ignore_pattern(name)}",
                })
                break

        if pct >= HIGH_PCT_THRESHOLD:
            high_pct_items.append({"name": name, "pct": pct})

    return issues, high_pct_items


def _suggest_ignore_pattern(name):
    """Suggest a .claudeignore pattern for a given file/directory."""
    if "/" in name:
        parts = name.split("/")
        for suspect in ["node_modules", "dist", "build", "vendor", ".next",
                        "__pycache__", "coverage", "tmp", "temp", ".git"]:
            if suspect in parts:
                return f"{suspect}/"
    for pattern, _ in SUSPECT_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            clean = pattern.replace(r"\.", ".").replace("$", "")
            if clean.endswith("/"):
                return clean
            return f"*{clean}" if clean.startswith(".") else clean
    return name


def generate_fix(issues):
    """Generate a combined .claudeignore fix suggestion."""
    if not issues:
        return None
    patterns = set()
    for issue in issues:
        fix = issue.get("fix", "")
        match = re.search(r"Add to \.claudeignore:\s*(.+)", fix)
        if match:
            patterns.add(match.group(1).strip())
    if not patterns:
        return None
    snippet = "\n".join(sorted(patterns))
    return f"Add to .claudeignore:\n{snippet}"


def main():
    parser = argparse.ArgumentParser(
        description="Analyze /context output for token efficiency issues."
    )
    parser.add_argument(
        "--input", metavar="FILE", help="Read /context output from file"
    )
    parser.add_argument(
        "--input-json",
        metavar="JSON",
        help='Provide parsed context as JSON: {"pct": N, "contributors": [...]}',
    )
    parser.add_argument(
        "--out", metavar="FILE", help="Write JSON to file (default: stdout)"
    )
    args = parser.parse_args()

    if args.input_json:
        context_data = json.loads(args.input_json)
    elif args.input:
        with open(args.input) as f:
            raw = f.read()
        context_data = parse_context_output(raw)
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
        context_data = parse_context_output(raw)
    else:
        print(
            "ERROR: provide --input FILE, --input-json JSON, or pipe /context output",
            file=sys.stderr,
        )
        sys.exit(1)

    baseline_pct = context_data.get("pct")
    contributors = context_data.get("contributors", [])

    issues, high_pct_items = analyze_contributors(contributors)

    baseline_ok = baseline_pct is not None and baseline_pct <= BASELINE_THRESHOLD_PCT
    has_issues = len(issues) > 0

    if baseline_pct is not None and not baseline_ok:
        baseline_fix = (
            f"Context baseline is {baseline_pct}% (threshold: {BASELINE_THRESHOLD_PCT}%). "
            "Review the top contributors below and add unnecessary items to .claudeignore."
        )
    else:
        baseline_fix = ""

    result = {
        "baseline_pct": baseline_pct,
        "baseline_ok": baseline_ok,
        "baseline_threshold": BASELINE_THRESHOLD_PCT,
        "baseline_fix": baseline_fix,
        "issues": issues,
        "high_pct_items": high_pct_items,
        "combined_fix": generate_fix(issues),
        "score": 1 if (baseline_ok and not has_issues) else 0,
    }

    output = json.dumps(result, indent=2)

    if args.out:
        with open(args.out, "w") as f:
            f.write(output)
        print(f"Context analysis written to {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
