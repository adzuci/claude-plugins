#!/usr/bin/env python3
"""Check optional tool-intake command dependencies."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    status: str
    detail: str
    nudge: str


def collect_statuses() -> list[DependencyStatus]:
    path = shutil.which("glean")
    if path:
        return [DependencyStatus("glean", "available", path, "Run `glean auth status` before searching.")]
    return [
        DependencyStatus(
            "glean",
            "missing",
            "not found on PATH",
            "On macOS run `brew install gleanwork/tap/glean-cli`, then `glean auth login`.",
        )
    ]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    statuses = collect_statuses()
    if args.json:
        print(json.dumps([asdict(item) for item in statuses], indent=2))
    else:
        for item in statuses:
            print(f"{item.name}: {item.status} - {item.detail}")
            print(f"Next: {item.nudge}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
