#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKLIST = os.path.join(os.path.dirname(HERE), "framework", "templates", "grill-checklist.yml")


def checklist(path: str, persona: str) -> list[str]:
    current = None
    items = {}
    with open(path) as source:
        for line in source:
            heading = re.match(r"^([a-z][a-z-]*):\s*$", line)
            if heading:
                current = heading.group(1)
                items[current] = []
                continue
            item = re.match(r"^\s+-\s+(.+?)\s*$", line)
            if item and current:
                items[current].append(item.group(1))
    if persona not in items:
        raise ValueError(f"unknown persona {persona!r}")
    return items[persona]


def grill_answers(snapshot: str) -> set[str]:
    with open(snapshot) as source:
        text = source.read()
    match = re.search(r"^## Grill\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not match:
        return set()
    answers = set()
    for line in match.group(1).splitlines():
        item = re.match(r"^-\s+(.+?):\s+(.+)$", line)
        if not item:
            continue
        answer = item.group(2).strip()
        if re.fullmatch(r"deferred:\s*\S.*", answer) or re.search(r"\(source:\s*[^)]+\)\s*$", answer):
            answers.add(item.group(1).strip())
    return answers


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--checklist", default=CHECKLIST)
    args = parser.parse_args(argv)
    try:
        required = checklist(args.checklist, args.persona)
        present = grill_answers(args.snapshot)
    except (OSError, ValueError) as error:
        print(f"grill-check: {error}. Next: fix the snapshot path or persona", file=sys.stderr)
        return 2
    missing = [item for item in required if item not in present]
    if missing:
        print("grill-check: missing required decisions:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        print("Next: look up answerable facts, then add an answer with a source or defer it with a reason", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
