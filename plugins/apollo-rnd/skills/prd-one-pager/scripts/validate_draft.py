#!/usr/bin/env python3
"""Validate a PRD one-pager draft against the output contract."""

import re
import sys
from pathlib import Path

VALID_STATES = ("STATE: PRD_DRAFT_READY", "STATE: PRD_REVISION_READY")
REVIEW_NOTE_PHRASE = "responsible for verifying"
CITATION_LOOKBACK = 5  # lines back of current line scanned for a citation marker

HARD_STAT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?%"          # 25%, 25.5%
    r"|\$\d+(?:[.,]\d+)*[KMBkmb]?"  # $1000, $1.5M, $1.5m, $1,000
    r"|\b\d+(?:\.\d+)?x\b"          # 5x, 1.5x
    r"|\b\d{5,}\b"                  # 10000+ (4-digit years intentionally excluded)
)

CITATION_RE = re.compile(
    r"\[Source:"
    r"|\bSource:"                  # bare 'Source:' (e.g. italic *(Source: ...)* or trailing "Source: ...")
    r"|ASSUMPTION:"
    r"|INFERENCE:"
    r"|\[NEEDS SOURCE LINK"
    r"|\[NEEDS INPUT"
)

# Lines we never flag: header metadata and target/threshold rows in success-metrics tables.
SKIP_RE = re.compile(r"\*\*Date:\*\*|\*\*Owner:\*\*|≥|≤|>=|<=")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_draft.py <draft.md>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text()
    lines = text.splitlines()
    errors: list[str] = []

    non_empty = [l for l in lines if l.strip()]
    last = non_empty[-1].strip() if non_empty else ""
    if last not in VALID_STATES:
        errors.append(f"Last non-empty line must be one of {VALID_STATES}; got: {last!r}")

    if last == "STATE: PRD_DRAFT_READY" and REVIEW_NOTE_PHRASE not in text:
        errors.append(f"PRD_DRAFT_READY but Review note missing (expected phrase: {REVIEW_NOTE_PHRASE!r})")

    for i, line in enumerate(lines):
        if SKIP_RE.search(line):
            continue
        if not HARD_STAT_RE.search(line):
            continue
        start = max(0, i - CITATION_LOOKBACK)
        context = "\n".join(lines[start:i + 1])
        if not CITATION_RE.search(context):
            errors.append(f"Line {i + 1}: numeric claim without citation/label: {line.strip()!r}")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print("✓ Draft passes output contract checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
