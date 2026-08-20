#!/usr/bin/env python3
"""Check record identifiers in a leaked-data sample against real Apollo formats.

This proves a sample synthetic. It never proves one genuine: a well-built fake
passes every check here. Only a row-level match against the source system
establishes possession.

Usage:
    python3 check_id_formats.py <sample.csv> --object-id-col APOLLO_TEAM_ID \\
        --salesforce-col SFDC_ACCOUNT_ID --entity Account
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

OBJECT_ID_RE = re.compile(r"^[0-9a-f]{24}$")
SALESFORCE_RE = re.compile(r"^[A-Za-z0-9]{15}([A-Za-z0-9]{3})?$")

# Salesforce 18-char checksum alphabet: 5 bits -> one character.
_SUFFIX_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"

# Standard Salesforce three-character object key prefixes.
SALESFORCE_PREFIXES = {
    "001": "Account",
    "003": "Contact",
    "005": "User",
    "006": "Opportunity",
    "00Q": "Lead",
    "500": "Case",
    "701": "Campaign",
}

_DIGITS_RE = re.compile(r"\D")


def is_object_id(value: str) -> bool:
    """True if value is a syntactically valid Mongo ObjectId.

    Apollo internal ids are 24 lowercase hex characters with no prefix.
    """
    return bool(OBJECT_ID_RE.match(value or ""))


def object_id_timestamp(value: str) -> Optional[datetime]:
    """Decode the 4-byte creation timestamp embedded in an ObjectId.

    Returns None when the value is not a valid ObjectId. A timestamp outside
    the plausible life of the data is itself a tell.
    """
    if not is_object_id(value):
        return None
    return datetime.fromtimestamp(int(value[:8], 16), tz=timezone.utc)


def salesforce_suffix(id15: str) -> str:
    """Compute the 3-character checksum that turns a 15-char id into 18 chars.

    Each group of five characters contributes five bits, least significant
    first, set when the character is an uppercase letter.
    """
    if len(id15) != 15:
        raise ValueError("Salesforce checksum requires exactly 15 characters")
    suffix = ""
    for chunk in range(3):
        bits = 0
        for offset in range(5):
            char = id15[chunk * 5 + offset]
            if char.isalpha() and char.isupper():
                bits |= 1 << offset
        suffix += _SUFFIX_ALPHABET[bits]
    return suffix


def is_salesforce_id(value: str) -> bool:
    """True if value is a syntactically valid 15- or 18-character Salesforce id.

    For 18-character ids the trailing checksum must agree with the first 15.
    """
    if not value or not SALESFORCE_RE.match(value):
        return False
    if len(value) == 18:
        return value[15:].upper() == salesforce_suffix(value[:15])
    return True


def salesforce_entity(value: str) -> Optional[str]:
    """Return the object name implied by a Salesforce id prefix, if recognised."""
    if not value or len(value) < 3:
        return None
    return SALESFORCE_PREFIXES.get(value[:3])


def prefix_matches(value: str, claimed_entity: str) -> bool:
    """True if the id's prefix matches the entity the sample claims it is.

    A valid-looking Contact id under an Account column is a mismatch worth
    reporting even though the id itself parses.
    """
    entity = salesforce_entity(value)
    if entity is None:
        return False
    return entity.lower() == (claimed_entity or "").lower()


def trailing_ordinal(value: str) -> Optional[int]:
    """Extract the trailing run of digits from an identifier, if any."""
    if not value:
        return None
    match = re.search(r"(\d+)$", value)
    return int(match.group(1)) if match else None


def ordinal_correlation(
    rows: Sequence[Dict[str, Any]],
    col_a: str,
    col_b: str,
    min_rows: int = 3,
) -> Dict[str, Any]:
    """Detect identifiers from two systems sharing a counter.

    Independent systems never generate matching ordinals. When the trailing
    number of two id columns agrees on most rows, the sample was produced by a
    loop rather than exported from two real systems.
    """
    compared = 0
    matching = 0
    for row in rows:
        left = trailing_ordinal(str(row.get(col_a, "")))
        right = trailing_ordinal(str(row.get(col_b, "")))
        if left is None or right is None:
            continue
        compared += 1
        if left == right:
            matching += 1

    if compared < min_rows:
        return {
            "compared": compared,
            "matching": matching,
            "correlated": False,
            "reason": "not enough rows",
        }

    ratio = matching / compared
    return {
        "compared": compared,
        "matching": matching,
        "ratio": round(ratio, 4),
        "correlated": ratio >= 0.9,
        "reason": "ordinals agree on most rows" if ratio >= 0.9 else "ordinals independent",
    }


def classify_column(values: Iterable[str], kind: str) -> Dict[str, Any]:
    """Score one column of identifiers as valid, mixed, or invalid."""
    checks = {"object_id": is_object_id, "salesforce": is_salesforce_id}
    if kind not in checks:
        raise ValueError("kind must be one of: {}".format(", ".join(sorted(checks))))
    check = checks[kind]

    observed = [str(v) for v in values if str(v).strip()]
    valid = sum(1 for v in observed if check(v))
    total = len(observed)

    if total == 0:
        verdict = "empty"
    elif valid == total:
        verdict = "valid"
    elif valid == 0:
        verdict = "invalid"
    else:
        verdict = "mixed"

    return {"kind": kind, "total": total, "valid": valid, "verdict": verdict}


def _read_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample", help="CSV file to inspect")
    parser.add_argument("--object-id-col", action="append", default=[])
    parser.add_argument("--salesforce-col", action="append", default=[])
    parser.add_argument("--entity", help="Entity the Salesforce column claims to be")
    parser.add_argument(
        "--correlate",
        nargs=2,
        metavar=("COL_A", "COL_B"),
        help="Two id columns to test for a shared counter",
    )
    args = parser.parse_args(argv)

    rows = _read_rows(args.sample)
    report: Dict[str, Any] = {"rows": len(rows), "columns": {}}

    for col in args.object_id_col:
        report["columns"][col] = classify_column((r.get(col, "") for r in rows), "object_id")

    for col in args.salesforce_col:
        result = classify_column((r.get(col, "") for r in rows), "salesforce")
        if args.entity:
            mismatches = sum(
                1 for r in rows if r.get(col) and not prefix_matches(r[col], args.entity)
            )
            result["entity_mismatches"] = mismatches
        report["columns"][col] = result

    if args.correlate:
        report["ordinal_correlation"] = ordinal_correlation(rows, *args.correlate)

    report["note"] = (
        "Format checks can prove a sample synthetic. They cannot prove it genuine."
    )
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
