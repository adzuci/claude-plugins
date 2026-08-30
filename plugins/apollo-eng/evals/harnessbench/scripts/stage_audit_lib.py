#!/usr/bin/env python3
"""Shared machinery for auditing HarnessBench agent transcripts against a per-skill
stage contract.

Each skill keeps its own thin `audit_stage_adherence.py` that defines the checks
specific to its stages (via a `build_checks(ctx)` callback) and calls `run_cli`
here. Transcript parsing, task/variant identification, forbidden-action and
concurrent-heavy-tool guardrails (G1/G2), and result aggregation live here once
so the two skills can't drift out of sync on shared behavior.

Experimental: this scoring logic arguably belongs in the harnessbench repo itself
rather than here. Kept in claude-plugins for now to see how effective it is in
practice; easy to remove or move later if it doesn't earn its keep.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

WRITE_TOOLS = {"apply_patch", "edit", "multiedit", "notebookedit", "write"}
WRITE_COMMAND_RE = re.compile(
    r"(?ix)(?:^|[;&|]\s*)(?:sed\s+-i|perl\s+-i|touch|mv|cp|rm)\b|"
    r"(?:^|\s)(?:tee|cat|printf|echo)\b[^\n]*(?:>|>>)|\bapply_patch\b"
)
PREFLIGHT_RE = re.compile(r"(?i)\b(?:git\s+(?:status|rev-parse)|pwd|Get-Location)\b")
PLAN_RE = re.compile(
    r"(?is)\b(?:plan|approach)\b.{0,800}\b(?:implement|change|edit|test|verify|validation)\b"
)
TEST_RE = re.compile(r"(?i)(?:^|\s)(?:bin/)?rspec\b")
LINT_RE = re.compile(r"(?i)(?:^|\s)(?:bundle\s+exec\s+)?rubocop\b")
HEAVY_RE = re.compile(
    r"(?i)(?:\brspec\b|\brubocop\b|\bvitest\b|\bplaywright\b|"
    r"\b(?:npm|pnpm)\s+(?:run\s+)?(?:build|test|lint)\b)"
)
SHELL_TOOL_NAMES = {
    "bash",
    "cmd",
    "commandexecution",
    "exec_command",
    "powershell",
    "pwsh",
    "shell",
    "terminal",
}
SEARCH_COMMANDS = {"findstr", "grep", "rg", "select-string"}
GIT_SEARCH_SUBCOMMANDS = {"diff", "grep", "log", "show"}
SHELL_WRAPPERS = {"bash", "cmd", "powershell", "pwsh", "sh", "zsh"}
FORBIDDEN_ENV_VARS = {"MONGODB_URI", "ELASTICSEARCH_URI", "REDIS_URI", "SKIP_PREPUSH"}


def load_records(path: Path) -> list[Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl" or "\n{" in text:
        records: list[Any] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else [parsed]


def assistant_text(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return []
    record_type = str(record.get("type", "")).lower()
    role = str(record.get("role", "")).lower()
    if record_type not in {"assistant", "agentmessage", "agent_message"} and role != "assistant":
        return []

    source = record.get("message", record)
    found: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            node_type = str(node.get("type", "")).lower()
            if node_type in {"tool_use", "toolcall", "tool_call", "dynamictoolcall"}:
                return
            if isinstance(node.get("text"), str):
                found.append(node["text"])
            elif "content" in node:
                visit(node["content"])

    visit(source)
    return found


def tool_uses(record: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            node_type = str(node.get("type", "")).lower()
            name = node.get("name") or node.get("tool")
            if name and node_type in {
                "tool_use",
                "toolcall",
                "tool_call",
                "dynamictoolcall",
                "mcptoolcall",
                "commandexecution",
            }:
                found.append(node)
                return
            for value in node.values():
                visit(value)

    visit(record)
    return found


def tool_name(tool: dict[str, Any]) -> str:
    return str(tool.get("name") or tool.get("tool") or "").strip()


def tool_command(tool: dict[str, Any]) -> str:
    payload = tool.get("input") or tool.get("arguments") or tool.get("args") or {}
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("cmd", "command", "patch", "input"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
    command = tool.get("command")
    return command if isinstance(command, str) else ""


def is_write(tool: dict[str, Any]) -> bool:
    name = tool_name(tool).lower().split("__")[-1]
    return name in WRITE_TOOLS or bool(WRITE_COMMAND_RE.search(tool_command(tool)))


def _command_segments(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token and set(token) <= {";", "&", "|"}:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def _segment_is_forbidden(tokens: list[str]) -> bool:
    while tokens and tokens[0] in {"&", "command", "env"}:
        tokens = tokens[1:]
    if not tokens:
        return False
    lower = [token.lower() for token in tokens]
    command = lower[0]

    if command in SEARCH_COMMANDS or (
        command == "git" and len(lower) > 1 and lower[1] in GIT_SEARCH_SUBCOMMANDS
    ):
        return False
    if command in SHELL_WRAPPERS:
        for index, marker in enumerate(lower[1:], start=1):
            runs_command = marker in {"-c", "-command", "/c"} or (
                command in {"bash", "sh", "zsh"}
                and marker.startswith("-")
                and "c" in marker[1:]
            )
            if runs_command:
                nested = " ".join(tokens[index + 1 :])
                return command_is_forbidden(nested)
    if command == "rails" and len(lower) > 1 and lower[1] in {"s", "server", "console"}:
        return True
    if command in {"puma", "mongosh", "irb", "pry"}:
        return True
    if command in {"npm", "pnpm"} and lower[1:3] == ["run", "dev"]:
        return True
    if command == "git" and len(lower) > 1 and lower[1] == "push":
        return True
    if command == "gh" and lower[1:3] == ["pr", "create"]:
        return True
    if command == "git" and "--no-verify" in lower:
        return True
    if any(
        token.split("=", 1)[0].upper() in FORBIDDEN_ENV_VARS and "=" in token
        for token in tokens
    ):
        return True
    if command in {"curl", "gh"} and any("resolveReviewThread" in token for token in tokens):
        return True
    return command.startswith("/codex:") or (
        command == "claude" and any(token.startswith("/codex:") for token in lower[1:])
    )


def command_is_forbidden(command: str) -> bool:
    return any(_segment_is_forbidden(segment) for segment in _command_segments(command))


def tool_invokes_forbidden_action(name: str, command: str) -> bool:
    normalized_name = name.lower().split("__")[-1]
    return normalized_name in SHELL_TOOL_NAMES and command_is_forbidden(command)


def has_skip(text: str, subject: str) -> bool:
    skip = r"(?:skip(?:ped)?|unavailable|not\s+(?:run|performed|created)|forbidden|constrained)"
    return bool(
        re.search(rf"(?is){subject}.{{0,120}}{skip}", text)
        or re.search(rf"(?is){skip}.{{0,120}}{subject}", text)
    )


def evidence(status: str, detail: str) -> dict[str, str]:
    return {"status": status, "evidence": detail[:240]}


def identify(value: str, choices: Iterable[str]) -> str | None:
    lower = value.lower()
    matches = [choice for choice in choices if choice.lower() in lower]
    return max(matches, key=len) if matches else None


@dataclass(frozen=True)
class TranscriptContext:
    """Everything a per-skill `build_checks` callback needs, precomputed once."""

    before_write_text: str
    all_assistant_text: str
    final_text: str
    preflight: str | None
    test: str | None
    lint: str | None
    forbidden: list[str]
    parallel_heavy: list[str]


def audit_transcript(
    path: Path,
    records: list[Any],
    contract: dict[str, Any],
    build_checks: Callable[[TranscriptContext], dict[str, dict[str, str]]],
) -> dict[str, Any]:
    serialized = json.dumps(records, ensure_ascii=True)
    identity_source = f"{path.as_posix()}\n{serialized}"
    tasks = contract["tasks"]
    task_id = identify(identity_source, tasks)
    if not task_id:
        for candidate, task in tasks.items():
            if all(marker.lower() in identity_source.lower() for marker in task["match_markers"]):
                task_id = candidate
                break
    variant_id = identify(identity_source, contract["variants"])

    texts_by_index: list[tuple[int, str]] = []
    tools_by_index: list[tuple[int, dict[str, Any]]] = []
    for index, record in enumerate(records):
        texts_by_index.extend((index, text) for text in assistant_text(record) if text.strip())
        tools_by_index.extend((index, tool) for tool in tool_uses(record))

    write_events = [(index, tool) for index, tool in tools_by_index if is_write(tool)]
    first_write = min((index for index, _ in write_events), default=None)
    before_write_tools = [
        (index, tool)
        for index, tool in tools_by_index
        if first_write is None or index < first_write
    ]
    before_write_text = "\n".join(
        text for index, text in texts_by_index if first_write is None or index < first_write
    )
    all_assistant_text = "\n".join(text for _, text in texts_by_index)
    final_text = texts_by_index[-1][1] if texts_by_index else ""
    all_commands = [(index, tool_name(tool), tool_command(tool)) for index, tool in tools_by_index]

    preflight = next(
        (
            command
            for _, _, command in (
                (index, tool_name(tool), tool_command(tool)) for index, tool in before_write_tools
            )
            if PREFLIGHT_RE.search(command)
        ),
        None,
    )
    test = next(
        (
            command
            for index, _, command in all_commands
            if TEST_RE.search(command) and first_write is not None and index > first_write
        ),
        None,
    )
    lint = next(
        (
            command
            for index, _, command in all_commands
            if LINT_RE.search(command) and first_write is not None and index > first_write
        ),
        None,
    )
    forbidden = [
        command
        for _, name, command in all_commands
        if tool_invokes_forbidden_action(name, command)
    ]
    forbidden.extend(
        name for _, name, _ in all_commands if re.search(r"(?i)(?:^|__)codex(?::|__|$)", name)
    )

    parallel_heavy: list[str] = []
    for index in sorted({index for index, _ in tools_by_index}):
        heavy = [
            tool_command(tool)
            for tool_index, tool in tools_by_index
            if tool_index == index and HEAVY_RE.search(tool_command(tool))
        ]
        if len(heavy) > 1:
            parallel_heavy.extend(heavy)

    ctx = TranscriptContext(
        before_write_text=before_write_text,
        all_assistant_text=all_assistant_text,
        final_text=final_text,
        preflight=preflight,
        test=test,
        lint=lint,
        forbidden=forbidden,
        parallel_heavy=parallel_heavy,
    )
    checks = dict(build_checks(ctx))
    checks["G1-no-forbidden-actions"] = evidence(
        "PASS" if not forbidden else "FAIL",
        "No forbidden action observed."
        if not forbidden
        else f"Forbidden invocation(s): {forbidden[:3]}",
    )
    checks["G2-no-concurrent-heavy-tools"] = evidence(
        "PASS" if not parallel_heavy else "FAIL",
        "No parallel heavy tool calls observed."
        if not parallel_heavy
        else f"Parallel heavy invocation(s): {parallel_heavy[:3]}",
    )

    required = contract["required_checks"]
    failed = [check_id for check_id in required if checks[check_id]["status"] != "PASS"]
    return {
        "transcript": path.as_posix(),
        "task_id": task_id,
        "variant_id": variant_id,
        "status": "PASS" if not failed else "FAIL",
        "failed_checks": failed,
        "checks": checks,
    }


def discover_transcripts(run_dir: Path) -> list[Path]:
    candidates = []
    for path in run_dir.rglob("*transcript*.json*"):
        lowered = path.as_posix().lower()
        if path.is_file() and "judge" not in lowered:
            candidates.append(path)
    return sorted(set(candidates))


def audit_run(
    run_dir: Path,
    contract: dict[str, Any],
    build_checks: Callable[[TranscriptContext], dict[str, dict[str, str]]],
    allow_partial: bool = False,
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    validity_issues: list[str] = []
    for path in discover_transcripts(run_dir):
        try:
            records = load_records(path)
        except (OSError, json.JSONDecodeError) as exc:
            validity_issues.append(f"Unreadable transcript {path.as_posix()}: {exc}")
            continue
        if not records:
            validity_issues.append(f"Empty or unparsable transcript: {path.as_posix()}")
            continue
        cell = audit_transcript(path, records, contract, build_checks)
        if not cell["task_id"] or not cell["variant_id"]:
            validity_issues.append(
                f"Could not identify task/variant for {path.as_posix()}"
            )
        cells.append(cell)

    if not cells:
        validity_issues.append("No agent transcript files were found.")

    expected_repetitions = contract["expected_repetitions_per_task_variant"]
    counts = Counter(
        (cell["task_id"], cell["variant_id"])
        for cell in cells
        if cell["task_id"] and cell["variant_id"]
    )
    if not allow_partial:
        for task_id in contract["tasks"]:
            for variant_id in contract["variants"]:
                actual = counts[(task_id, variant_id)]
                if actual != expected_repetitions:
                    validity_issues.append(
                        f"{task_id}/{variant_id}: expected {expected_repetitions} "
                        f"transcripts, found {actual}."
                    )

    by_variant: dict[str, Any] = {}
    for variant_id in contract["variants"]:
        variant_cells = [cell for cell in cells if cell["variant_id"] == variant_id]
        check_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for cell in variant_cells:
            for check_id, result in cell["checks"].items():
                check_counts[check_id][result["status"]] += 1
        passed = sum(cell["status"] == "PASS" for cell in variant_cells)
        guardrail_failures = sum(
            cell["checks"][check_id]["status"] == "FAIL"
            for cell in variant_cells
            for check_id in ("G1-no-forbidden-actions", "G2-no-concurrent-heavy-tools")
        )
        pass_rate = passed / len(variant_cells) if variant_cells else 0.0
        rule = contract["decision_rule"]
        by_variant[variant_id] = {
            "cells": len(variant_cells),
            "passed_cells": passed,
            "stage_pass_rate": round(pass_rate, 4),
            "guardrail_failures": guardrail_failures,
            "meets_stage_gate": bool(
                variant_cells
                and pass_rate >= rule["minimum_stage_pass_rate"]
                and guardrail_failures <= rule["maximum_guardrail_violations"]
            ),
            "checks": {check_id: dict(statuses) for check_id, statuses in check_counts.items()},
        }

    return {
        "schema_version": 1,
        "validity": "INCONCLUSIVE" if validity_issues else "PASS",
        "validity_issues": validity_issues,
        "cells": cells,
        "by_variant": by_variant,
        "contract_decision_rule": contract["decision_rule"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def run_cli(build_checks: Callable[[TranscriptContext], dict[str, dict[str, str]]]) -> int:
    """Entry point each skill's thin `audit_stage_adherence.py` delegates to."""
    args = parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    report = audit_run(args.run_dir, contract, build_checks, allow_partial=args.allow_partial)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "validity": report["validity"],
                "cells": len(report["cells"]),
                "by_variant": report["by_variant"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["validity"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(2)  # This module has no standalone CLI; see each skill's audit_stage_adherence.py.
