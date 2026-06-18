#!/usr/bin/env python3
"""Check optional support-rotation tool dependencies."""

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


CLI_DEPENDENCIES = {
    "glean": "Install/authenticate the Glean CLI, then run `glean auth login` or set `GLEAN_API_TOKEN`.",
}

AGENT_TOOL_DEPENDENCIES = {
    "intercom_mcp": "Connect or refresh the Intercom MCP; otherwise paste the conversation thread.",
    "granola_mcp": "Connect Granola MCP for notes/transcripts, or paste notes/transcripts instead.",
    "google_drive_sheets": "Connect Google Drive/Sheets for the calibration rubric, or use the bundled rubric summary.",
    "slack": "Connect Slack for source thread lookups and escalation context, or paste the Slack context.",
}


def check_cli(name: str, nudge: str) -> DependencyStatus:
    path = shutil.which(name)
    if path:
        return DependencyStatus(name=name, status="available", detail=path, nudge="")
    return DependencyStatus(name=name, status="missing", detail="not found on PATH", nudge=nudge)


def check_agent_tool(name: str, nudge: str) -> DependencyStatus:
    return DependencyStatus(
        name=name,
        status="agent-check-required",
        detail="Python cannot inspect Codex/Claude MCP tool availability directly.",
        nudge=nudge,
    )


def collect_statuses() -> list[DependencyStatus]:
    statuses = [check_cli(name, nudge) for name, nudge in CLI_DEPENDENCIES.items()]
    statuses.extend(check_agent_tool(name, nudge) for name, nudge in AGENT_TOOL_DEPENDENCIES.items())
    return statuses


def format_markdown(statuses: list[DependencyStatus]) -> str:
    lines = ["# Intercom Assistant Dependency Check", ""]
    for item in statuses:
        marker = "OK" if item.status == "available" else "CHECK" if item.status == "agent-check-required" else "MISSING"
        lines.append(f"- **{item.name}**: {marker} - {item.detail}")
        if item.nudge:
            lines.append(f"  - Nudge: {item.nudge}")
    return "\n".join(lines)


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
        print(format_markdown(statuses))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
