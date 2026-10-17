#!/usr/bin/env python3
"""Validate and atomically refresh the controlled approved-tools snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VALID_DELIVERY = {"CLI", "SaaS", "OSS", "library", "extension", "MCP", "hybrid"}
VALID_STATUS = {"APPROVED", "APPROVED_WITH_CONDITIONS", "RESTRICTED_OR_DENIED"}
REQUIRED_TOOL_FIELDS = {
    "id", "names", "delivery", "status", "scope", "data_classes", "conditions",
    "owner", "reviewed_at", "source_url",
}


def parse_datetime(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return value


def require_url(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an https URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must be an https URL")
    return value


def require_strings(value: object, field: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(f"{field} must be a {'possibly empty ' if allow_empty else 'non-empty '}list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must contain non-empty strings")
    return sorted({item.strip() for item in value}, key=str.casefold)


def validate_export(payload: object, input_sha256: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("source must be a schema_version 1 JSON object")
    snapshot = payload.get("snapshot")
    tools = payload.get("tools")
    if not isinstance(snapshot, dict) or not isinstance(tools, list):
        raise ValueError("source must contain snapshot and tools")
    required_snapshot = {"effective_at", "owner", "reviewed_by", "source_sha256", "source_url", "status"}
    missing = required_snapshot - snapshot.keys()
    if missing:
        raise ValueError(f"snapshot is missing: {', '.join(sorted(missing))}")
    if snapshot.get("status") != "AUTHORITATIVE":
        raise ValueError("snapshot.status must be AUTHORITATIVE")
    for field in ("owner", "reviewed_by"):
        if not isinstance(snapshot.get(field), str) or not snapshot[field].strip():
            raise ValueError(f"snapshot.{field} is required")
    parse_datetime(snapshot.get("effective_at"), "snapshot.effective_at")
    require_url(snapshot.get("source_url"), "snapshot.source_url")
    source_sha = snapshot.get("source_sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64 or any(c not in "0123456789abcdef" for c in source_sha):
        raise ValueError("snapshot.source_sha256 must be 64 lowercase hex characters")

    normalized_tools = []
    seen_ids: set[str] = set()
    seen_aliases: set[str] = set()
    for index, raw in enumerate(tools):
        if not isinstance(raw, dict):
            raise ValueError(f"tools[{index}] must be an object")
        missing = REQUIRED_TOOL_FIELDS - raw.keys()
        if missing:
            raise ValueError(f"tools[{index}] is missing: {', '.join(sorted(missing))}")
        if not isinstance(raw["id"], str):
            raise ValueError(f"tools[{index}].id must be a string")
        tool_id = raw["id"].strip()
        if not tool_id or tool_id in seen_ids:
            raise ValueError(f"duplicate or empty tool id: {tool_id!r}")
        seen_ids.add(tool_id)
        names = require_strings(raw["names"], f"tools[{index}].names")
        domains = require_strings(raw.get("domains", []), f"tools[{index}].domains", allow_empty=True)
        repositories = require_strings(raw.get("repositories", []), f"tools[{index}].repositories", allow_empty=True)
        packages = require_strings(raw.get("packages", []), f"tools[{index}].packages", allow_empty=True)
        for alias in names + domains + repositories + packages:
            key = alias.casefold()
            if key in seen_aliases:
                raise ValueError(f"duplicate alias, domain, or package: {alias}")
            seen_aliases.add(key)
        delivery = require_strings(raw["delivery"], f"tools[{index}].delivery")
        if not set(delivery) <= VALID_DELIVERY:
            raise ValueError(f"tools[{index}].delivery has an unsupported value")
        if not isinstance(raw["status"], str) or raw["status"] not in VALID_STATUS:
            raise ValueError(f"tools[{index}].status has an unsupported value")
        for field in ("scope", "owner"):
            if not isinstance(raw[field], str) or not raw[field].strip():
                raise ValueError(f"tools[{index}].{field} is required")
        reviewed_at = parse_datetime(raw["reviewed_at"], f"tools[{index}].reviewed_at")
        expires_at = raw.get("expires_at")
        if expires_at is not None:
            parse_datetime(expires_at, f"tools[{index}].expires_at")
        version_scope = raw.get("version_scope")
        if version_scope is not None and not isinstance(version_scope, str):
            raise ValueError(f"tools[{index}].version_scope must be a string or null")
        require_url(raw["source_url"], f"tools[{index}].source_url")
        normalized_tools.append({
            "id": tool_id,
            "names": names,
            "domains": domains,
            "repositories": repositories,
            "packages": packages,
            "delivery": delivery,
            "status": raw["status"],
            "scope": raw["scope"].strip(),
            "version_scope": version_scope,
            "data_classes": require_strings(raw["data_classes"], f"tools[{index}].data_classes", allow_empty=True),
            "conditions": require_strings(raw["conditions"], f"tools[{index}].conditions", allow_empty=True),
            "owner": raw["owner"].strip(),
            "reviewed_at": reviewed_at,
            "expires_at": expires_at,
            "source_url": raw["source_url"],
        })

    normalized_snapshot = dict(snapshot)
    normalized_snapshot["owner"] = snapshot["owner"].strip()
    normalized_snapshot["reviewed_by"] = snapshot["reviewed_by"].strip()
    normalized_snapshot["import_sha256"] = input_sha256
    return {"schema_version": 1, "snapshot": normalized_snapshot, "tools": sorted(normalized_tools, key=lambda item: item["id"])}


def index_tools(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict) or not isinstance(payload.get("tools"), list):
        return {}
    return {str(item.get("id")): item for item in payload["tools"] if isinstance(item, dict) and item.get("id")}


def diff_snapshots(current: object, proposed: dict[str, Any]) -> dict[str, list[str]]:
    before = index_tools(current)
    after = index_tools(proposed)
    return {
        "added": sorted(after.keys() - before.keys()),
        "changed": sorted(key for key in after.keys() & before.keys() if after[key] != before[key]),
        "removed": sorted(before.keys() - after.keys()),
    }


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def validate_apply(changes: dict[str, list[str]], authorized_by: str | None, allow_removals: bool) -> str:
    if not authorized_by or not authorized_by.strip():
        raise ValueError("--authorized-by is required with --apply")
    if changes["removed"] and not allow_removals:
        raise ValueError("snapshot removes records; inspect the dry-run and pass --allow-removals to confirm")
    return authorized_by.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--authorized-by")
    parser.add_argument("--allow-removals", action="store_true")
    parser.add_argument("--audit")
    args = parser.parse_args()

    source_bytes = args.source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    proposed = validate_export(json.loads(source_bytes), source_hash)
    current = json.loads(args.target.read_text(encoding="utf-8")) if args.target.exists() else {}
    changes = diff_snapshots(current, proposed)
    summary = {"mode": "apply" if args.apply else "dry-run", "input_sha256": source_hash, **changes}

    if args.apply:
        authorized_by = validate_apply(changes, args.authorized_by, args.allow_removals)
        now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        proposed["snapshot"]["generated_at"] = now
        proposed["snapshot"]["updated_by"] = authorized_by
        atomic_write(args.target, proposed)
        # The audit log is local and gitignored; the printed record goes in the snapshot PR as the shared trail.
        audit_path = Path(args.audit) if args.audit else args.target.with_suffix(".audit.jsonl")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"at": now, "authorized_by": authorized_by, **summary}
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        summary["audit_log"] = str(audit_path)
        summary["audit_record"] = record

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
