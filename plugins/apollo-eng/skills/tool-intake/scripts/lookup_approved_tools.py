#!/usr/bin/env python3
"""Find candidate records in an approved-tools snapshot without granting approval."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def normalized_targets(value: str) -> set[str]:
    raw = value.strip().casefold().rstrip("/")
    targets = {raw}
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    if parsed.netloc:
        host = parsed.netloc.split("@")[-1].split(":")[0]
        normalized_host = host.removeprefix("www.")
        path = parsed.path.strip("/")
        if normalized_host != "github.com":
            targets.add(normalized_host)
        if path and normalized_host == "github.com":
            # Only GitHub paths identify a repo; other paths ("docs", "pricing") would over-match.
            targets.add(f"github.com/{path}")
    return {target for target in targets if target}


def record_identifiers(record: dict[str, Any]) -> set[str]:
    values = []
    for field in ("names", "domains", "repositories", "packages"):
        if isinstance(record.get(field), list):
            values.extend(record[field])
    identifiers = set()
    for value in values:
        if isinstance(value, str):
            identifiers.update(normalized_targets(value))
    return identifiers


def is_expired(record: dict[str, Any], now: dt.datetime | None = None) -> bool:
    expires_at = record.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at:
        return False
    try:
        parsed = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True  # malformed expiry: force reconfirmation rather than crash
    if parsed.tzinfo is None:
        return True  # timezone-less expiry is ambiguous: force reconfirmation
    current = now or dt.datetime.now(dt.timezone.utc)
    return parsed <= current


def lookup(snapshot: object, target: str, now: dt.datetime | None = None) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {"result": "APPROVAL_SOURCE_UNCONFIGURED", "matches": []}
    metadata = snapshot.get("snapshot")
    tools = snapshot.get("tools")
    if not isinstance(metadata, dict) or metadata.get("status") != "AUTHORITATIVE" or not isinstance(tools, list):
        return {"result": "APPROVAL_SOURCE_UNCONFIGURED", "matches": []}
    wanted = normalized_targets(target)
    matches = [record for record in tools if isinstance(record, dict) and wanted & record_identifiers(record)]
    if not matches:
        return {"result": "NO_MATCH_REVIEW_REQUIRED", "matches": []}
    if len(matches) > 1:
        return {"result": "AMBIGUOUS", "matches": matches}
    record = matches[0]
    result = "STALE_RECONFIRM" if is_expired(record, now) else "CANDIDATE_RECORD_REQUIRES_SCOPE_CHECK"
    return {"result": result, "matches": [record]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    payload = json.loads(args.snapshot.read_text(encoding="utf-8"))
    print(json.dumps(lookup(payload, args.target), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
