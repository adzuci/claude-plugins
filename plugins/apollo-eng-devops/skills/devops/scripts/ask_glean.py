#!/usr/bin/env python3
"""Query Apollo's Glean via the local `glean` CLI for the devops SRE skill.

Mirrors the intercom-assistant Glean bridge: it shells out to the local `glean`
CLI (`glean agents run --json ...`) so runbook, postmortem, and RCA lookups use
the same authenticated path support reps already rely on. Stdlib-only so it runs
under the repo's Python 3.9 / 3.11 test matrix with no extra deps.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from textwrap import shorten
from typing import Any, Callable, Sequence


# No Apollo SRE Glean agent id is hardcoded on purpose: the real id must come
# from --agent-id or GLEAN_SRE_AGENT_ID so we never ship a guessed value.
AGENT_ID_ENV = "GLEAN_SRE_AGENT_ID"
MODES = ("runbook", "postmortem", "rca", "incident", "ask")


class GleanBridgeError(RuntimeError):
    """Expected user-facing Glean bridge error."""


@dataclass(frozen=True)
class GleanResult:
    agent_id: str
    mode: str
    question: str
    response: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default="ask")
    parser.add_argument("--question", required=True, help="SRE/runbook/postmortem/RCA question.")
    parser.add_argument("--context", help="Optional incident/service context to frame the query.")
    # Falls back to the env var so the real agent id lives in the environment, not the repo.
    parser.add_argument("--agent-id", default=os.environ.get(AGENT_ID_ENV))
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def compact(text: str, limit: int = 1600) -> str:
    squashed = " ".join(text.split())
    if len(squashed) <= limit:
        return squashed
    return shorten(squashed, width=limit, placeholder="...")


def resolve_agent_id(agent_id: str | None) -> str:
    if agent_id:
        return agent_id
    raise GleanBridgeError(
        "No Glean agent id provided. Pass --agent-id or set "
        f"`{AGENT_ID_ENV}` to Apollo's SRE Glean agent id (ask an SRE lead for "
        "the current value). Without it the Glean CLI cannot be targeted."
    )


def build_user_prompt(mode: str, question: str, context: str | None = None) -> str:
    parts = [
        "Use Apollo's approved internal knowledge sources only (runbooks, postmortems, RCAs, incident history).",
        f"Mode: {mode}.",
        f"SRE question: {question}",
    ]
    if context:
        parts.append("Incident/service context for framing only, not a verified fact: " + context)
    parts.extend(
        [
            "Return Markdown with: Summary, Detailed answer, Sources / links, Caveats.",
            "Do not invent runbook steps, SLOs, config values, owners, or incident outcomes.",
            "If no relevant source is found, say so plainly and suggest where an SRE should look next.",
        ]
    )
    return "\n".join(parts)


def build_agent_payload(agent_id: str, prompt: str) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "input": {"query": prompt},
    }


def find_glean_cli() -> str:
    glean_path = shutil.which("glean")
    if not glean_path:
        raise GleanBridgeError(
            "Glean CLI not found on PATH. Runbook/postmortem lookups via the CLI require the local "
            "`glean` CLI. Install/authenticate it, then run `glean auth login` or set `GLEAN_API_TOKEN`. "
            "A Glean MCP/search fallback may be used only as clearly labeled degraded research."
        )
    return glean_path


def run_glean_agent(
    agent_id: str,
    prompt: str,
    glean_path: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    payload = build_agent_payload(agent_id, prompt)
    proc = runner(
        [glean_path, "agents", "run", "--json", json.dumps(payload)],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    if proc.returncode != 0:
        message = compact(stderr or stdout or "glean agents run failed")
        if "not authenticated" in message.lower() or "GLEAN_API_TOKEN" in message:
            raise GleanBridgeError(
                f"Glean CLI is not authenticated: {message}\nRun `glean auth login` or set `GLEAN_API_TOKEN`."
            )
        raise GleanBridgeError(f"Glean CLI call failed: {message}")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise GleanBridgeError(
            f"Glean returned malformed JSON: {exc.msg}. Raw output: {compact(stdout)}"
        ) from exc
    response = extract_response_text(data)
    if not response:
        raise GleanBridgeError(
            f"Glean returned JSON without a readable response. Raw output: {compact(stdout)}"
        )
    return response


def extract_response_text(data: Any) -> str:
    direct = extract_direct_text(data)
    if direct:
        return direct
    fragments = list(iter_text_fragments(data))
    return "\n\n".join(dict.fromkeys(fragment.strip() for fragment in fragments if fragment.strip()))


def extract_direct_text(data: Any) -> str | None:
    if isinstance(data, str):
        return data.strip() or None
    if not isinstance(data, dict):
        return None
    for key in ("text", "answer", "response", "output", "content"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("result", "message", "assistantMessage", "finalResponse"):
        nested = extract_direct_text(data.get(key))
        if nested:
            return nested
    return None


def iter_text_fragments(data: Any) -> list[str]:
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "text" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(iter_text_fragments(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(iter_text_fragments(item))
    return found


def format_markdown(result: GleanResult) -> str:
    return "\n".join(
        [
            "# Glean CLI Result",
            "",
            f"- **Mode:** `{result.mode}`",
            f"- **Agent ID:** `{result.agent_id}`",
            "",
            "## Question",
            "",
            result.question,
            "",
            "## Answer",
            "",
            result.response,
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        agent_id = resolve_agent_id(args.agent_id)
        prompt = build_user_prompt(args.mode, args.question, args.context)
        response = run_glean_agent(agent_id, prompt, find_glean_cli())
    except GleanBridgeError as exc:
        print(exc, file=sys.stderr)
        return 1
    result = GleanResult(agent_id=agent_id, mode=args.mode, question=args.question, response=response)
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(format_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
