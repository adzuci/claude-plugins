#!/usr/bin/env python3
"""Scan a leaked-data sample for values reserved by standards bodies for docs.

Reserved domains, fictional phone ranges, and documentation IP blocks cannot
appear in real customer data. Finding them proves a sample is fabricated. Not
finding them proves nothing.

Usage:
    python3 scan_reserved_values.py <sample.csv>
    python3 scan_reserved_values.py <sample.csv> --email-col WORK_EMAIL
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import json
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence

# RFC 2606 and RFC 6761 reserve these for documentation and testing.
RESERVED_TLDS = {"example", "test", "invalid", "localhost"}
RESERVED_DOMAINS = {"example.com", "example.net", "example.org"}

# RFC 5737 documentation ranges.
DOCUMENTATION_NETS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
)

EMAIL_RE = re.compile(r"^[^@\s]+@([^@\s]+)$")
IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_NON_DIGIT_RE = re.compile(r"\D")

EMAIL_HINTS = ("email", "mail")
PHONE_HINTS = ("phone", "dial", "mobile", "tel")
IP_HINTS = ("ip", "address_ip", "ip_address")


def is_reserved_domain(domain: str) -> bool:
    """True if the domain is reserved by RFC 2606 / RFC 6761."""
    if not domain:
        return False
    lowered = domain.strip().lower().rstrip(".")
    if lowered in RESERVED_DOMAINS:
        return True
    return lowered.rsplit(".", 1)[-1] in RESERVED_TLDS


def email_domain(value: str) -> Optional[str]:
    """Return the domain part of an email address, or None if not an address."""
    match = EMAIL_RE.match((value or "").strip())
    return match.group(1) if match else None


def is_reserved_email(value: str) -> bool:
    """True if an email address sits on a reserved domain."""
    domain = email_domain(value)
    return is_reserved_domain(domain) if domain else False


def is_fictional_phone(value: str) -> bool:
    """True for the NANP fictional range: exchange 555, line 0100-0199.

    Only 555-0100 through 555-0199 are reserved for fiction. Other 555 numbers
    are assignable, so flagging every 555 would produce false positives.
    """
    digits = _NON_DIGIT_RE.sub("", value or "")
    if len(digits) < 10:
        return False
    national = digits[-10:]
    exchange = national[3:6]
    line = national[6:]
    if exchange != "555":
        return False
    return line.startswith("01") and "0100" <= line <= "0199"


def is_documentation_ip(value: str) -> bool:
    """True if an address falls in an RFC 5737 documentation range."""
    candidate = (value or "").strip()
    if not IP_RE.match(candidate):
        return False
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return any(address in net for net in DOCUMENTATION_NETS)


def _columns_matching(fieldnames: Iterable[str], hints: Sequence[str]) -> List[str]:
    return [f for f in fieldnames if any(h in f.lower() for h in hints)]


def scan_rows(
    rows: Sequence[Dict[str, Any]],
    email_cols: Optional[Sequence[str]] = None,
    phone_cols: Optional[Sequence[str]] = None,
    ip_cols: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Count reserved values across a sample and return a verdict.

    The verdict is deliberately two-valued. "synthetic" means at least one
    value cannot exist in real data. Everything else is "inconclusive" — never
    "genuine", because this scan cannot establish authenticity.
    """
    rows = list(rows)
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    emails = list(email_cols) if email_cols else _columns_matching(fieldnames, EMAIL_HINTS)
    phones = list(phone_cols) if phone_cols else _columns_matching(fieldnames, PHONE_HINTS)
    addresses = list(ip_cols) if ip_cols else _columns_matching(fieldnames, IP_HINTS)

    reserved_emails = 0
    fictional_phones = 0
    documentation_ips = 0
    examples: List[str] = []

    for row in rows:
        for col in emails:
            if is_reserved_email(str(row.get(col, ""))):
                reserved_emails += 1
                if len(examples) < 5:
                    examples.append("{}={}".format(col, row.get(col)))
        for col in phones:
            if is_fictional_phone(str(row.get(col, ""))):
                fictional_phones += 1
                if len(examples) < 5:
                    examples.append("{}={}".format(col, row.get(col)))
        for col in addresses:
            if is_documentation_ip(str(row.get(col, ""))):
                documentation_ips += 1
                if len(examples) < 5:
                    examples.append("{}={}".format(col, row.get(col)))

    total = reserved_emails + fictional_phones + documentation_ips
    return {
        "rows": len(rows),
        "columns_scanned": {"email": emails, "phone": phones, "ip": addresses},
        "reserved_emails": reserved_emails,
        "fictional_phones": fictional_phones,
        "documentation_ips": documentation_ips,
        "examples": examples,
        "verdict": "synthetic" if total else "inconclusive",
        "note": (
            "Reserved values prove fabrication. Their absence proves nothing — "
            "this scan cannot establish that a sample is genuine."
        ),
    }


def _read_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample", help="CSV file to inspect")
    parser.add_argument("--email-col", action="append", default=None)
    parser.add_argument("--phone-col", action="append", default=None)
    parser.add_argument("--ip-col", action="append", default=None)
    args = parser.parse_args(argv)

    report = scan_rows(
        _read_rows(args.sample),
        email_cols=args.email_col,
        phone_cols=args.phone_col,
        ip_cols=args.ip_col,
    )
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
