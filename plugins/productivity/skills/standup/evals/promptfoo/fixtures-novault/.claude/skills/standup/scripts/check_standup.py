#!/usr/bin/env python3
"""Validate the concise paste-ready portion of a standup update."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


WORD_LIMIT = 90
BULLET_LIMIT = 8


def metrics(text: str) -> dict[str, int | bool]:
    words = len(re.findall(r"\S+", text))
    bullets = len(re.findall(r"^\s*[-*]\s+\S", text, re.MULTILINE))
    return {
        "words": words,
        "bullets": bullets,
        "word_limit_exclusive": WORD_LIMIT,
        "bullet_limit_exclusive": BULLET_LIMIT,
        "valid": words < WORD_LIMIT and bullets < BULLET_LIMIT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", help="Read the paste-ready copy from this file.")
    source.add_argument("--text", help="Validate this literal text.")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()
    result = metrics(text)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
