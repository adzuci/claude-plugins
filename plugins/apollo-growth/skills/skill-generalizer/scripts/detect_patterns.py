"""
First-pass scanner for hardcoded values in a skill folder.

Walks every text file under the given path, runs a set of regex patterns,
and prints JSON describing each candidate. The skill-generalizer SKILL.md
uses this output as a starting point; an LLM pass picks up everything
the regex misses.

Usage:
    python detect_patterns.py <path-to-skill-folder>

Categories (mirrors references/variable-taxonomy.md):
- external_id: Notion collection IDs, hex UUIDs, Jira keys, Slack channels,
               Amplitude project IDs, GitHub slugs
- person:      email addresses, @-handles
- url:         http/https URLs
- file_path:   paths starting with ~/, /Users/, /home/
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Skip these — they're never user content we'd want to extract.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".DS_Store"}
SKIP_EXT = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".skill"}

# Order matters — earlier patterns win when ranges overlap.
PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("external_id", "notion_collection",
     re.compile(r"collection://[0-9a-f-]{36}", re.IGNORECASE)),
    ("external_id", "uuid",
     re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)),
    ("external_id", "notion_id_no_dashes",
     re.compile(r"\b[0-9a-f]{32}\b", re.IGNORECASE)),
    ("external_id", "slack_channel",
     re.compile(r"#[a-z0-9][a-z0-9_-]{2,}\b")),
    ("external_id", "jira_project_key",
     re.compile(r"\b(?:project|key)[\s:=\"']*([A-Z]{2,6})[-\s\"']")),
    ("external_id", "amplitude_project_id",
     re.compile(r"(?:amplitude.*?(?:project|app).*?id|project_id|app_id)[\s:=\"']*?(\d{5,8})", re.IGNORECASE)),
    ("external_id", "github_repo",
     re.compile(r"github\.com[:/]([\w.-]+/[\w.-]+)")),
    ("person", "email",
     re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")),
    ("url", "calendly",
     re.compile(r"https?://calendly\.com/[\w./-]+")),
    ("url", "url",
     re.compile(r"https?://[\w./%?=&#:+-]+")),
    ("file_path", "home_path",
     re.compile(r"~/[\w./-]+")),
    ("file_path", "absolute_user_path",
     re.compile(r"/Users/[\w./-]+")),
    ("file_path", "absolute_home_path",
     re.compile(r"/home/[\w./-]+")),
]


# A bare `#rrggbb` colour or a Markdown anchor link is not a Slack channel.
HEX_COLOR = re.compile(r"^#(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$", re.IGNORECASE)


def match_span(m: "re.Match[str]") -> tuple[str, int, int]:
    """Return the value to report and its span.

    When a pattern has a capturing group, the group is the actual identifier and
    the full match carries surrounding words (``project: CVR-`` vs ``CVR``).
    Reporting group 0 there both splits one ID into several candidates and makes
    a placeholder swap delete the words around it.
    """
    if m.re.groups:
        return m.group(1), m.start(1), m.end(1)
    return m.group(0), m.start(), m.end()


def is_noise(pattern_name: str, value: str, line: str, start: int) -> bool:
    """Drop matches that are syntactically right but never a real candidate."""
    if pattern_name != "slack_channel":
        return False
    if HEX_COLOR.match(value):
        return True
    # Markdown anchor: [Setup](#setup-guide)
    return start > 0 and line[start - 1] == "("


def scan_file(path: Path, root: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    findings: list[dict] = []
    seen_spans: list[tuple[int, int]] = []
    rel = str(path.relative_to(root))

    line_offset = 0
    for line_num, line in enumerate(text.splitlines(), start=1):
        for category, name, pattern in PATTERNS:
            for m in pattern.finditer(line):
                value, m_start, m_end = match_span(m)
                if is_noise(name, value, line, m_start):
                    continue
                global_start = line_offset + m_start
                global_end = line_offset + m_end
                # True overlap, not just "starts inside". A later, wider match that
                # swallows an earlier one must lose, or "earlier patterns win" breaks
                # and a Notion URL reports as both an id and a url.
                if any(s < global_end and global_start < e for s, e in seen_spans):
                    continue
                seen_spans.append((global_start, global_end))
                findings.append({
                    "file": rel,
                    "line": line_num,
                    "category": category,
                    "pattern_name": name,
                    "match": value,
                    "context": line.strip()[:200],
                })
        line_offset += len(line) + 1
    return findings


def walk(root: Path) -> list[dict]:
    out: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_EXT:
            continue
        out.extend(scan_file(path, root))
    return out


def collapse_duplicates(findings: list[dict]) -> dict:
    by_value: dict[str, dict] = {}
    for f in findings:
        key = f"{f['category']}::{f['match']}"
        if key not in by_value:
            by_value[key] = {
                "category": f["category"],
                "pattern_name": f["pattern_name"],
                "value": f["match"],
                "occurrences": [],
            }
        by_value[key]["occurrences"].append({"file": f["file"], "line": f["line"], "context": f["context"]})
    return {"unique_candidates": list(by_value.values()), "total_occurrences": len(findings)}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python detect_patterns.py <path-to-skill-folder>", file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1
    findings = walk(root)
    print(json.dumps(collapse_duplicates(findings), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
