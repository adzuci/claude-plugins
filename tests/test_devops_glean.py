import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "apollo-eng-devops" / "skills" / "devops"


def read_skill_file(relative: str) -> str:
    return (SKILL_DIR / relative).read_text()


def load_script(name: str):
    path = SKILL_DIR / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def json_from_cli_args(args: list[str]) -> dict:
    json_flag = args.index("--json")
    return json.loads(args[json_flag + 1])


def test_skill_documents_glean_cli_bridge():
    skill = read_skill_file("SKILL.md")

    assert "ask_glean.py" in skill
    assert "references/glean-cli.md" in skill
    assert "glean auth login" in skill
    assert "GLEAN_SRE_AGENT_ID" in skill


def test_glean_cli_reference_documents_runtime_and_agent_id_assumption():
    ref = read_skill_file("references/glean-cli.md")

    assert "glean agents run --json" in ref
    assert "glean auth login" in ref
    assert "GLEAN_SRE_AGENT_ID" in ref
    # The unknown agent id must stay flagged, not guessed.
    assert "intentionally left unset" in ref


def test_glean_bridge_prompt_stays_source_bound():
    bridge = load_script("ask_glean.py")

    prompt = bridge.build_user_prompt("postmortem", "es8 latency RCA follow-ups", "INC-123 es cluster")
    assert "approved internal knowledge sources only" in prompt
    assert "es8 latency RCA follow-ups" in prompt
    assert "INC-123 es cluster" in prompt
    assert "Do not invent runbook steps" in prompt
    assert "runbook" in bridge.MODES


def test_glean_bridge_requires_agent_id():
    bridge = load_script("ask_glean.py")

    with pytest.raises(bridge.GleanBridgeError) as exc:
        bridge.resolve_agent_id(None)
    assert "GLEAN_SRE_AGENT_ID" in str(exc.value)
    assert bridge.resolve_agent_id("agent-xyz") == "agent-xyz"


def test_glean_bridge_missing_cli_nudge(monkeypatch):
    bridge = load_script("ask_glean.py")

    monkeypatch.setattr(bridge.shutil, "which", lambda _name: None)
    with pytest.raises(bridge.GleanBridgeError) as exc:
        bridge.find_glean_cli()
    assert "glean auth login" in str(exc.value)


def test_glean_bridge_payload_shape():
    bridge = load_script("ask_glean.py")

    payload = bridge.build_agent_payload("agent-123", "prompt text")
    assert payload == {"agent_id": "agent-123", "input": {"query": "prompt text"}}


def test_glean_bridge_main_reports_errors_cleanly(monkeypatch, capsys):
    bridge = load_script("ask_glean.py")

    monkeypatch.delenv("GLEAN_SRE_AGENT_ID", raising=False)
    exit_code = bridge.main(["--question", "es8 latency runbook"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GLEAN_SRE_AGENT_ID" in err


def test_glean_bridge_extracts_nested_text():
    bridge = load_script("ask_glean.py")

    calls = []

    def runner(*_args, **_kwargs):
        calls.append(_args[0])
        return subprocess.CompletedProcess(
            args=["glean"],
            returncode=0,
            stdout='{"result":{"message":{"fragments":[{"text":"Restart the consumer group."}]}}}',
            stderr="",
        )

    answer = bridge.run_glean_agent("agent", "prompt", "/usr/bin/glean", runner=runner)
    assert answer == "Restart the consumer group."
    sent_payload = json_from_cli_args(calls[0])
    assert sent_payload["agent_id"] == "agent"
    assert sent_payload["input"]["query"] == "prompt"
