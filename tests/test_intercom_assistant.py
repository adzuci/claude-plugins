import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "apollo-eng-leadership" / "skills" / "intercom-assistant"


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


def test_skill_router_covers_support_rotation_copilot_modes():
    skill = read_skill_file("SKILL.md")

    for mode in ("setup", "monitor", "recap", "wrapup", "calibration", "report"):
        assert f"`{mode}`" in skill

    assert "ask_glean_support_rep_assistant.py" in skill
    assert "routing-and-macros.md" in skill
    assert "Granola is optional" in skill


def test_setup_mode_teaches_intercom_granola_and_closeout_macro():
    setup = read_skill_file("references/setup-mode.md")
    granola = read_skill_file("references/granola-recipes.md")

    assert "Intercom Details To Pin" in setup
    assert "`granola-recipes.md`" in setup
    assert "## `/Wrap-up`" in granola
    assert "# /Stall" in granola
    assert "# /Deescalate" in granola
    assert "<name> Closeout" in setup
    assert "I'll go ahead and close this out" in setup
    assert "https://docs.granola.ai/help-center/getting-more-from-your-notes/recipes" in setup


def test_recap_recipe_is_read_only_and_has_required_fields():
    recap = read_skill_file("references/recap-recipe.md")

    for field in ("Quick Script:", "Customer:", "Issue:", "Outcome:"):
        assert field in recap
    assert "Include optional fields only when they have useful content" in recap
    assert "Do not update Intercom automatically" in recap
    assert "`recap` or `wrapup`" in recap
    assert "<name> Closeout" in recap


def test_routing_reference_has_key_macros_and_clear_route_guardrail():
    routing = read_skill_file("references/routing-and-macros.md")

    assert "`Escalate to Billing`" in routing
    assert "`Escalate to Billing Renewals`" in routing
    assert "`Escalate to CA - Transfer Chat`" in routing
    assert "`Escalate to Blockages`" in routing
    assert "`Escalate to External Fraud (Chats)`" in routing
    assert "only when the route is clear" in routing
    assert "confirm exact names in IKB" in routing


def test_call_nudges_include_direct_answer_call_language():
    nudges = read_skill_file("references/call-nudges.md")

    assert "Answer Call button" in nudges
    assert "enable your mic and share your screen" in nudges
    assert "Do not offer a call by default" in nudges


def test_dependency_checker_nudges_for_missing_glean(monkeypatch):
    deps = load_script("check_dependencies.py")
    monkeypatch.setattr(deps.shutil, "which", lambda _name: None)

    statuses = deps.collect_statuses()
    glean = next(item for item in statuses if item.name == "glean")

    assert glean.status == "missing"
    assert "glean auth login" in glean.nudge
    assert any(item.name == "intercom_mcp" for item in statuses)


def test_glean_bridge_prompt_and_missing_cli_nudge(monkeypatch):
    bridge = load_script("ask_glean_support_rep_assistant.py")

    prompt = bridge.build_user_prompt(
        "intro",
        "How do exports work?",
        "Acme account",
        glean_assistant="zendesk-kb",
    )
    assert "approved sources only" in prompt
    assert "How do exports work?" in prompt
    assert "Requested Glean assistant/source wrapper: zendesk-kb" in prompt
    assert "Apollo Zendesk KB/IKB pages" in prompt
    assert "Do not invent account-specific facts" in prompt
    assert "macro-suggest" in bridge.MODES

    monkeypatch.setattr(bridge.shutil, "which", lambda _name: None)
    with pytest.raises(bridge.GleanSupportRepAssistantError) as exc:
        bridge.find_glean_cli()
    assert "glean auth login" in str(exc.value)
    assert "not as Support Rep Assistant output" in str(exc.value)


def test_glean_bridge_uses_cli_preserved_payload_shape():
    bridge = load_script("ask_glean_support_rep_assistant.py")

    payload = bridge.build_agent_payload("agent-123", "prompt text")

    assert payload == {"agent_id": "agent-123", "input": {"query": "prompt text"}}


def test_glean_bridge_extracts_nested_text():
    bridge = load_script("ask_glean_support_rep_assistant.py")

    calls = []

    def runner(*_args, **_kwargs):
        calls.append(_args[0])
        return subprocess.CompletedProcess(
            args=["glean"],
            returncode=0,
            stdout='{"result":{"message":{"fragments":[{"text":"Use the export settings page."}]}}}',
            stderr="",
        )

    answer = bridge.run_glean_agent("agent", "prompt", "/usr/bin/glean", runner=runner)
    assert answer == "Use the export settings page."
    sent_payload = json_from_cli_args(calls[0])
    assert sent_payload["agent_id"] == "agent"
    assert sent_payload["input"]["query"] == "prompt"


def test_daily_report_renderer_escapes_html_and_counts_statuses():
    report = load_script("render_daily_report.py")

    html = report.render_html(
        {
            "title": "My Day",
            "calls": [
                {
                    "customer": "<Acme>",
                    "issue": "Export issue",
                    "outcome": "Resolved",
                    "status": "resolved",
                    "product_signals": ["Confusing export button"],
                },
                {"customer": "Beta", "issue": "Billing", "outcome": "Escalated", "status": "escalated"},
            ],
            "themes": ["Exports"],
        },
        "2026-06-18",
    )

    assert "&lt;Acme&gt;" in html
    assert '<div class="kpi-value">2</div>' in html
    assert "Confusing export button" in html
    assert "Support Rotation Daily Report" not in html
