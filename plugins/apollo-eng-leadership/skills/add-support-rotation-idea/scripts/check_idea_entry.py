#!/usr/bin/env python3
"""Validate an Ideation Log entry draft and suggest research queries."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass


TITLE_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")
VALID_IMPACTS = {"high", "medium", "low"}


@dataclass
class Field:
    name: str
    value: str | None


def word_count(text: str) -> int:
    return len(TITLE_WORD_RE.findall(text))


def clean_terms(*parts: str | None) -> str:
    text = " ".join(part or "" for part in parts)
    words = TITLE_WORD_RE.findall(text)
    return " ".join(words[:12])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check support-rotation idea fields before creating a Notion entry."
    )
    parser.add_argument("--title", required=True, help="3-8 word idea name")
    parser.add_argument("--description", required=True, help="Entry description")
    parser.add_argument("--product-area", required=True, help="Affected Apollo product area")
    parser.add_argument("--entry-type", required=True, help="Primary entry type")
    parser.add_argument("--impact", required=True, help="High, Medium, or Low")
    parser.add_argument("--effort", required=True, help="Engineering effort estimate")
    parser.add_argument("--who", required=True, help="Affected user/customer segment")
    parser.add_argument("--next-step", required=True, help="Owner, team, or next action")
    parser.add_argument(
        "--keywords",
        default="",
        help="Optional comma-separated search keywords for Glean/ERD lookup",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    title_words = word_count(args.title)
    if title_words < 3 or title_words > 8:
        errors.append(f"Idea name must be 3-8 words; got {title_words}: {args.title!r}")

    description_words = word_count(args.description)
    if description_words > 800:
        errors.append(f"Description must be under 800 words; got {description_words}.")
    if description_words < 25:
        warnings.append("Description is short; verify it has concrete observed behavior and evidence.")

    required = [
        Field("product area", args.product_area),
        Field("entry type", args.entry_type),
        Field("impact", args.impact),
        Field("effort", args.effort),
        Field("who is affected", args.who),
        Field("next step", args.next_step),
    ]
    for field in required:
        if not (field.value or "").strip():
            errors.append(f"Missing required field: {field.name}.")

    if args.impact.strip().lower() not in VALID_IMPACTS:
        warnings.append("Impact should usually be High, Medium, or Low.")

    vague_values = {"unknown", "n/a", "tbd", "unclear", "?"}
    for field in required:
        if (field.value or "").strip().lower() in vague_values:
            warnings.append(f"{field.name.title()} is uncertain; use Glean or ask a clarification.")

    terms = clean_terms(args.product_area, args.title, args.keywords)

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("OK: draft passes hard checks.")

    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if terms:
        print("SUGGESTED GLEAN SEARCHES:")
        print(
            "  glean search --page-size 5 --fields "
            f"results.document.title,results.document.url,results.snippets {terms!r}"
        )
        print(
            "  glean search --page-size 5 --fields "
            f"results.document.title,results.document.url,results.snippets {terms + ' ERD'!r}"
        )

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
