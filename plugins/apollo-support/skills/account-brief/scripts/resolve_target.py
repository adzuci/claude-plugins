#!/usr/bin/env python3
"""Classify an account-brief target and build a read-only lookup plan.

Pure helpers only: no network calls, no MCP calls, no CLI execution. The agent
runs the returned plan against live sources (Snowflake, Salesforce, Intercom)
in the operator's own authenticated environment, or degrades to pasted data.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Sequence

# A Salesforce object id is 15 or 18 characters of [A-Za-z0-9] and always
# contains at least one digit (the 3-char key prefix, e.g. 001 for Account).
SFDC_ID = re.compile(r"[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$")
# A domain is dotted, has no '@' or whitespace, and uses domain-safe characters.
DOMAIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9-]+)+$")

TargetKind = str  # one of: "am", "domain", "account_id"


def classify_target(arg: str) -> TargetKind:
    """Classify a raw target string as an AM, a domain, or an account id.

    Precedence:
      1. Anything containing '@' is treated as a person (AM/contact email).
      2. An all-digits string, or a Salesforce-style 15/18-char id, is an account id.
      3. A dotted host with no space is a domain.
      4. A string containing a space, or any remaining bare token, is an AM name.
    """
    value = (arg or "").strip()
    if not value:
        raise ValueError("target is empty")

    if "@" in value:
        return "am"

    if value.isdigit():
        return "account_id"

    if " " not in value and "." not in value and SFDC_ID.fullmatch(value) and any(c.isdigit() for c in value):
        return "account_id"

    if " " not in value and DOMAIN.fullmatch(value):
        return "domain"

    return "am"


def _source(name: str, purpose: str, query_hint: str) -> dict[str, object]:
    """Build one OPTIONAL live-source step. Every source degrades to pasted data."""
    return {
        "source": name,
        "purpose": purpose,
        "query_hint": query_hint,
        "optional": True,
        "fallback": "If this source is unavailable, ask the operator to paste the data and mark those fields Unverified.",
    }


def build_lookup_plan(kind: TargetKind, value: str) -> dict[str, object]:
    """Describe which read-only sources to query for a classified target.

    The plan is advisory. The agent must not mutate any source. Query hints are
    generic and parameterized: they never embed report ids, org secrets, or ARR
    literals.
    """
    value = (value or "").strip()
    if kind not in {"am", "domain", "account_id"}:
        raise ValueError(f"unknown target kind: {kind!r}")

    if kind == "am":
        resolve_steps = [
            "Resolve the AM to their Salesforce owner id (match by email or full name).",
            "List the accounts they own (their book) before pulling per-account signals.",
        ]
        sources = [
            _source(
                "salesforce",
                "Find the AM's owned accounts (the book) and each account's health fields.",
                'sf api request rest --target-org apollo-sfdc "/services/data/vXX.X/query?q=<SOQL selecting accounts WHERE Owner matches the AM>"',
            ),
            _source(
                "snowflake",
                "Pull open and recent support tickets for every account in the AM's book.",
                'snow sql --connection apollo --query "<SELECT ticket rows for the book\'s account ids, last ~24h and open>"',
            ),
            _source(
                "intercom",
                "Cross-check company-level conversation context for accounts in the book.",
                "Intercom MCP: look up companies for the book's domains, then recent conversations.",
            ),
        ]
    elif kind == "domain":
        resolve_steps = [
            "Resolve the domain to a Salesforce account (match website/domain field).",
            "Resolve the same domain to an Intercom company when the MCP is available.",
        ]
        sources = [
            _source(
                "salesforce",
                "Resolve the domain to an account and read its health fields.",
                'sf api request rest --target-org apollo-sfdc "/services/data/vXX.X/query?q=<SOQL selecting the account WHERE domain/website matches>"',
            ),
            _source(
                "snowflake",
                "Pull open and recent support tickets for the resolved account.",
                'snow sql --connection apollo --query "<SELECT ticket rows WHERE account domain or id matches>"',
            ),
            _source(
                "intercom",
                "Read company profile and recent conversations for the domain.",
                "Intercom MCP: look up the company by domain, then recent conversations.",
            ),
        ]
    else:  # account_id
        resolve_steps = [
            "Use the account id directly as the primary key.",
            "Confirm the account exists in Salesforce before assembling the brief.",
        ]
        sources = [
            _source(
                "salesforce",
                "Read the account record and its health fields by id.",
                'sf api request rest --target-org apollo-sfdc "/services/data/vXX.X/sobjects/Account/<id>"',
            ),
            _source(
                "snowflake",
                "Pull open and recent support tickets for the account id.",
                'snow sql --connection apollo --query "<SELECT ticket rows WHERE account id matches>"',
            ),
            _source(
                "intercom",
                "Cross-check company conversation context once the domain is known.",
                "Intercom MCP: look up the company (via resolved domain), then recent conversations.",
            ),
        ]

    return {
        "kind": kind,
        "value": value,
        "read_only": True,
        "resolve_steps": resolve_steps,
        "sources": sources,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify an account-brief target and print its lookup plan.")
    parser.add_argument("target", help="AM name/email, a domain, or an account id.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    kind = classify_target(args.target)
    plan = build_lookup_plan(kind, args.target)
    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        print(f"Target: {args.target}")
        print(f"Classified as: {kind}")
        print("Resolve steps:")
        for step in plan["resolve_steps"]:
            print(f"  - {step}")
        print("Sources (all OPTIONAL, read-only):")
        for source in plan["sources"]:
            print(f"  - {source['source']}: {source['purpose']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
