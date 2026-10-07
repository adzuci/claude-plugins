#!/usr/bin/env python3
"""Read and atomically update a privacy-minimal Slack monitor checkpoint."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1


def parse_utc(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a UTC offset")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise argparse.ArgumentTypeError("timestamp must be UTC")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def empty_state() -> dict[str, object]:
    return {"schema_version": SCHEMA_VERSION, "last_success": None, "surfaced_item_ids": []}


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return empty_state()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported checkpoint schema_version")
    if not isinstance(data.get("surfaced_item_ids"), list):
        raise ValueError("surfaced_item_ids must be a list")
    return data


def save_state(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def complete(path: Path, completed_at: str, item_ids: list[str]) -> dict[str, object]:
    state = load_state(path)
    existing = [str(item) for item in state["surfaced_item_ids"]]
    state["last_success"] = completed_at
    state["surfaced_item_ids"] = list(dict.fromkeys(existing + item_ids))[-1000:]
    save_state(path, state)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser("show", help="Print the checkpoint without changing it.")
    show_parser.add_argument("--state", type=Path, required=True)

    complete_parser = subparsers.add_parser("complete", help="Record a successful completed scan.")
    complete_parser.add_argument("--state", type=Path, required=True)
    complete_parser.add_argument("--completed-at", type=parse_utc, required=True)
    complete_parser.add_argument("--item-id", action="append", default=[])

    args = parser.parse_args()
    state_path = args.state.expanduser()
    state = load_state(state_path) if args.command == "show" else complete(state_path, args.completed_at, args.item_id)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
