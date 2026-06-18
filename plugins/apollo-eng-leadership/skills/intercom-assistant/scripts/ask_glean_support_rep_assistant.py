#!/usr/bin/env python3
"""Call Apollo's Glean Support Rep Assistant from intercom-assistant."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from textwrap import shorten
from typing import Any, Callable, Sequence


DEFAULT_AGENT_ID = "90b93c53b44840d5b25a7836d4042304"
MODES = ("intro", "live", "deescalate", "macro-suggest", "monitor", "ask")


class GleanSupportRepAssistantError(RuntimeError):
    """Expected user-facing Glean bridge error."""


@dataclass(frozen=True)
class AssistantResult:
    agent_id: str
    mode: str
    question: str
    response: str
    glean_assistant: str | None = None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default="ask")
    parser.add_argument("--question", required=True, help="Customer product/process/how-to question.")
    parser.add_argument("--customer-context", help="Optional customer/account context to keep separate from Glean facts.")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID)
    parser.add_argument(
        "--glean-assistant",
        help=(
            "Optional assistant/source wrapper to request from Glean, for example "
            "`zendesk-kb` to ground the answer in Zendesk KB pages."
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def compact(text: str, limit: int = 1600) -> str:
    squashed = " ".join(text.split())
    if len(squashed) <= limit:
        return squashed
    return shorten(squashed, width=limit, placeholder="...")


def build_user_prompt(
    mode: str,
    question: str,
    customer_context: str | None = None,
    glean_assistant: str | None = None,
) -> str:
    parts = [
        "Use Apollo's Glean Support Rep Assistant approved sources only.",
        f"Mode: {mode}.",
        f"Customer product/process/how-to question: {question}",
    ]
    if glean_assistant:
        parts.extend(
            [
                f"Requested Glean assistant/source wrapper: {glean_assistant}.",
                (
                    "When the wrapper is `zendesk-kb`, ground the answer in Apollo Zendesk KB/IKB pages: "
                    "summarize the canonical guidance, include KB page titles or URLs when available, "
                    "and call out when no matching KB page is found."
                ),
            ]
        )
    if customer_context:
        parts.append(
            "Customer-specific context for framing only. Do not treat it as verified by Glean: "
            + customer_context
        )
    parts.extend(
        [
            "Return Markdown with: Summary, Detailed answer, Sources / verification notes, Escalation caveats.",
            "Do not invent account-specific facts, plan limits, permissions, outages, refunds, credits, or policy exceptions.",
            "If no relevant information is found, say so plainly and suggest the normal Support escalation path.",
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
        raise GleanSupportRepAssistantError(
            "Glean CLI not found on PATH. Exact Support Rep Assistant output requires the local "
            "`glean` CLI. Install/authenticate it, then run `glean auth login` or set `GLEAN_API_TOKEN`. "
            "A Glean MCP/search fallback may be used only as regular Glean research, not as Support Rep Assistant output."
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
            raise GleanSupportRepAssistantError(
                f"Glean CLI is not authenticated: {message}\nRun `glean auth login` or set `GLEAN_API_TOKEN`."
            )
        raise GleanSupportRepAssistantError(f"Glean Support Rep Assistant call failed: {message}")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise GleanSupportRepAssistantError(
            f"Glean returned malformed JSON: {exc.msg}. Raw output: {compact(stdout)}"
        ) from exc
    response = extract_response_text(data)
    if not response:
        raise GleanSupportRepAssistantError(
            f"Glean returned JSON without a readable assistant response. Raw output: {compact(stdout)}"
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


def format_markdown(result: AssistantResult) -> str:
    return "\n".join(
        [
            "# Glean Support Rep Assistant Result",
            "",
            f"- **Mode:** `{result.mode}`",
            f"- **Agent ID:** `{result.agent_id}`",
            f"- **Glean assistant:** `{result.glean_assistant or 'default'}`",
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
    prompt = build_user_prompt(args.mode, args.question, args.customer_context, args.glean_assistant)
    response = run_glean_agent(args.agent_id, prompt, find_glean_cli())
    result = AssistantResult(
        agent_id=args.agent_id,
        mode=args.mode,
        question=args.question,
        response=response,
        glean_assistant=args.glean_assistant,
    )
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(format_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
