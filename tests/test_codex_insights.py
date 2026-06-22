from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "apollo-eng" / "skills" / "codex-insights"
SCRIPTS = SKILL_DIR / "scripts"
NODE = shutil.which("node")


def run_node(script: str, *args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    assert NODE, "node is required for codex-insights script tests"
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [NODE, str(SCRIPTS / script), *args],
        cwd=cwd or REPO,
        env=merged,
        check=True,
        text=True,
        capture_output=True,
    )


def write_jsonl(path: Path, rows: list[dict | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [row if isinstance(row, str) else json.dumps(row) for row in rows]
    path.write_text("\n".join(lines) + "\n")


def token_count(ts: str, total: int, input_tokens: int | None = None) -> dict:
    input_value = input_tokens if input_tokens is not None else total
    return {
        "timestamp": ts,
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": {
                    "total_tokens": total,
                    "input_tokens": input_value,
                    "cached_input_tokens": 0,
                    "output_tokens": max(0, total - input_value),
                    "reasoning_output_tokens": 0,
                },
                "last_token_usage": {
                    "total_tokens": total,
                    "input_tokens": input_value,
                },
                "model_context_window": 200000,
            },
        },
    }


def isolated_env(tmp_path: Path, codex_home: Path) -> dict[str, str]:
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    return {
        "HOME": str(tmp_path / "home"),
        "CODEX_HOME": str(codex_home),
        "OBSIDIAN_VAULT": "",
        "PATH": str(empty_bin),
    }


def test_enumerator_handles_archives_malformed_json_missing_index_since_and_delta(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    active_id = "11111111-1111-1111-1111-111111111111"
    archived_id = "22222222-2222-2222-2222-222222222222"
    old_id = "33333333-3333-3333-3333-333333333333"

    write_jsonl(
        codex_home / "sessions" / f"{active_id}.jsonl",
        [
            {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"cwd": str(tmp_path / "repo")}},
            token_count("2026-01-01T00:10:00Z", 100),
            "{bad json",
            token_count("2026-01-03T00:10:00Z", 450),
        ],
    )
    write_jsonl(
        codex_home / "archived_sessions" / f"{archived_id}.jsonl",
        [
            {"timestamp": "2026-01-04T00:00:00Z", "type": "session_meta", "payload": {"cwd": str(tmp_path / "archive")}},
            token_count("2026-01-04T00:05:00Z", 200),
        ],
    )
    write_jsonl(codex_home / "sessions" / f"{old_id}.jsonl", [token_count("2025-12-01T00:00:00Z", 999)])

    result = run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "2026-01-02",
        "--sessions",
        "10",
        "--outdir",
        str(outdir),
        env=isolated_env(tmp_path, codex_home),
    )

    assert "2 exact sessions found" in result.stdout
    data = json.loads((outdir / "compact.json").read_text())
    assert data["snapshot"]["sessions_found"] == 2
    assert data["totals"]["total_tokens"] == 550

    active = next(session for session in data["sessions"] if session["id"] == active_id)
    assert active["total_tokens"] == 350
    assert active["window_basis"] == "delta_from_prior_token_count"
    assert active["errors"] == 1
    assert active["thread_name"] == active_id

    archived = next(session for session in data["sessions"] if session["id"] == archived_id)
    assert archived["total_tokens"] == 200
    assert archived["window_basis"] == "session_started_in_window"


def test_enumerator_missing_value_flags_fall_back_to_defaults(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    session_id = "44444444-4444-4444-4444-444444444444"
    write_jsonl(codex_home / "sessions" / f"{session_id}.jsonl", [token_count("2999-01-04T00:05:00Z", 200)])

    result = run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "--sessions",
        "--outdir",
        str(outdir),
        env=isolated_env(tmp_path, codex_home),
    )

    assert "1 exact sessions found" in result.stdout
    data = json.loads((outdir / "compact.json").read_text())
    assert data["since"] == "7d"
    assert data["snapshot"]["sessions_reported"] == 1


def test_enumerator_normalizes_prompt_input_path_alias_failure(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    env = isolated_env(tmp_path, codex_home)
    bin_dir = Path(env["PATH"])
    fake_codex = bin_dir / "codex"
    fake_codex.write_text(
        """#!/bin/sh
echo "WARNING: proceeding, even though we could not create PATH aliases: Operation not permitted (os error 1)" >&2
echo "Error: Operation not permitted (os error 1)" >&2
exit 1
"""
    )
    fake_codex.chmod(0o755)
    session_id = "55555555-5555-5555-5555-555555555555"
    write_jsonl(codex_home / "sessions" / f"{session_id}.jsonl", [token_count("2999-01-04T00:05:00Z", 200)])

    run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "all",
        "--outdir",
        str(outdir),
        env=env,
    )

    data = json.loads((outdir / "compact.json").read_text())
    error = data["prompt_input"]["error"]
    assert "current sandbox" in error
    assert "PATH alias creation is denied" in error
    assert "WARNING:" not in error


def test_enumerator_audits_mcp_plugins_projects_and_runtime_verification(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    project = tmp_path / "support-project"
    stale = tmp_path / "missing-project"
    project_config = project / ".codex" / "config.toml"
    session_id = "55555555-5555-5555-5555-555555555555"
    codex_home.mkdir()
    project_config.parent.mkdir(parents=True)
    project_config.write_text(
        """
[mcp_servers.granola]
url = "https://mcp.granola.ai/mcp"

[plugins."notion@openai-curated"]
enabled = true
""".strip()
        + "\n"
    )
    (codex_home / "config.toml").write_text(
        f"""
model = "gpt-5.5"
model_reasoning_effort = "high"

[projects."{project}"]
trust_level = "trusted"

[projects."{stale}"]
trust_level = "trusted"

[projects."{stale}"]
trust_level = "trusted"

[features]
memories = true
js_repl = false

[desktop]
show-context-window-usage = true

[tui]
status_line = ["context-remaining", "used-tokens"]

[memories]
use_memories = true
generate_memories = true

[plugins."browser@openai-bundled"]
enabled = true

[plugins."unused@apollo-plugins"]
enabled = false

# Disabled for lean mode: [mcp_servers.sentry]
# url = "https://mcp.sentry.dev/mcp"

[mcp_servers.glean_default]
url = "https://apollo-io-be.glean.com/mcp/default"

[mcp_servers.context7]
enabled = false
url = "https://mcp.context7.com/mcp"
""".strip()
        + "\n"
    )
    write_jsonl(codex_home / "sessions" / f"{session_id}.jsonl", [token_count("2999-01-04T00:05:00Z", 200)])

    result = run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "all",
        "--outdir",
        str(outdir),
        env=isolated_env(tmp_path, codex_home),
    )

    assert "1 exact sessions found" in result.stdout
    data = json.loads((outdir / "compact.json").read_text())
    config = data["config"]
    assert config["mcp_servers"] == ["glean_default"]
    assert config["plugins"] == ["browser@openai-bundled", "notion@openai-curated"]
    assert config["feature_flags"]["desktop"]["show-context-window-usage"] is True
    assert config["feature_flags"]["tui"]["status_line"] == ["context-remaining", "used-tokens"]
    assert config["mcp_audit"]["enabled_global"][0]["status"] == "globally enabled"
    assert {row["name"] for row in config["mcp_audit"]["disabled_global"]} == {"context7", "sentry"}
    assert config["mcp_audit"]["project_scoped"][0]["name"] == "granola"
    assert config["mcp_audit"]["project_scoped"][0]["project_path"] == str(project)
    assert config["mcp_audit"]["runtime_verification"]["ok"] is False
    assert config["spend_monitoring"]["monitoring_api_spend"] is False
    assert config["spend_monitoring"]["codexbar_available"] is False
    assert "tmux_status_right_references_script" not in config["spend_monitoring"]
    assert "tmux_conf_existing_paths" not in config["spend_monitoring"]
    assert config["stale_project_entries"][0]["path"] == str(stale)
    assert config["duplicate_project_entries"][0]["path"] == str(stale)
    assert data["snapshot"]["enabled_global_mcp_count"] == 1
    assert data["snapshot"]["disabled_global_mcp_count"] == 2
    assert data["snapshot"]["project_scoped_mcp_count"] == 1
    assert "Project Scope" in {rec["mode"] for rec in data["recommendations"]}


def test_enumerator_skips_multiline_toml_values_without_poisoning_following_keys(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    session_id = "66666666-6666-6666-6666-666666666666"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        """
[tui]
status_line = [
  "context-remaining",
  "used-tokens",
]
status_line_use_colors = true

[mcp_servers.glean_default]
url = "https://apollo-io-be.glean.com/mcp/default"
""".strip()
        + "\n"
    )
    write_jsonl(codex_home / "sessions" / f"{session_id}.jsonl", [token_count("2999-01-04T00:05:00Z", 200)])

    run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "all",
        "--outdir",
        str(outdir),
        env=isolated_env(tmp_path, codex_home),
    )

    config = json.loads((outdir / "compact.json").read_text())["config"]
    assert config["feature_flags"]["tui"]["status_line"] == ["context-remaining", "used-tokens"]
    assert config["feature_flags"]["tui"]["status_line_use_colors"] is True
    assert config["mcp_servers"] == ["glean_default"]


def test_enumerator_summarizes_skill_usage_and_mcp_attribution(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    session_id = "77777777-7777-7777-7777-777777777777"
    (codex_home / "skills" / "used-skill").mkdir(parents=True)
    (codex_home / "skills" / "used-skill" / "SKILL.md").write_text(
        "---\nname: used-skill\ndescription: Used in test.\n---\n"
    )
    (codex_home / "skills" / "unused-skill").mkdir(parents=True)
    (codex_home / "skills" / "unused-skill" / "SKILL.md").write_text(
        "---\nname: unused-skill\ndescription: Unused in test.\n---\n"
    )
    write_jsonl(
        codex_home / "sessions" / f"{session_id}.jsonl",
        [
            token_count("2999-01-04T00:05:00Z", 200),
            {"type": "event_msg", "payload": {"type": "user_message", "text": "$used-skill /usage"}},
            {"type": "response_item", "payload": {"type": "function_call", "name": "mcp__glean_default__search"}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "Original token count: 1200\nresult"}},
        ],
    )

    run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "all",
        "--outdir",
        str(outdir),
        env=isolated_env(tmp_path, codex_home),
    )

    data = json.loads((outdir / "compact.json").read_text())
    skill_usage = data["skill_usage"]
    assert skill_usage["inventory_count"] == 2
    assert skill_usage["usage_seen"] is True
    assert skill_usage["status_seen"] is False
    assert skill_usage["invoked"][0]["invocation"] == "$used-skill"
    assert skill_usage["unused_model_invoked"][0]["invocation"] == "$unused-skill"

    attribution = data["mcp_attribution"]
    assert attribution["exact_credit_attribution_available"] is False
    assert attribution["servers"][0]["server"] == "glean_default"
    assert attribution["servers"][0]["estimated_tool_output_tokens"] == 1200


def test_shipped_codex_insights_files_are_portable() -> None:
    for path in SKILL_DIR.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="ignore")
            assert "/Users/adamblackwell" not in text, path
            assert "~/.claude" not in text, path
            assert ".claude/codex-insights" not in text, path


def test_obsidian_updater_skips_without_explicit_vault(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    compact.write_text(json.dumps(minimal_compact(tmp_path)))

    result = run_node(
        "update_obsidian_project.mjs",
        str(compact),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )

    assert "Obsidian not configured" in result.stdout
    assert not (tmp_path / "home" / "wiki").exists()


def test_obsidian_updater_disabled_does_not_require_compact_input(tmp_path: Path) -> None:
    result = run_node(
        "update_obsidian_project.mjs",
        str(tmp_path / "missing-compact.json"),
        "--no-obsidian",
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )

    assert "Obsidian disabled" in result.stdout


def test_private_report_uses_dense_action_sections(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    report = tmp_path / "report.html"
    data = minimal_compact(tmp_path)
    data["flags"]["context_load"] = 1
    data["totals"]["input_tokens"] = 100000
    compact.write_text(json.dumps(data))

    run_node(
        "render_report.mjs",
        str(compact),
        "--out",
        str(report),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )

    html = report.read_text()
    assert "Measured Action Plan" in html
    assert "Workflow Rules" in html
    assert "Durable memory:" in html
    assert "Context reset discipline" in html
    assert "/compact" in html
    assert "targeted search first" in html
    assert "/apollo-eng:token-efficiency-assessment" in html
    assert "Skill surface hygiene" in html
    assert "MCP credit attribution: estimate only" in html
    assert "Shareable Codex Site" not in html
    assert "Power Modes" not in html
    assert "Two-Agent Intervention" not in html
    assert "Karpathy LLM Wiki memory system" not in html
    assert "/apollo-eng:memory-setup" not in html
    assert "self-cost: unavailable" not in html


def test_private_report_recommends_codexbar_without_tmux_audit(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    report = tmp_path / "report.html"
    data = minimal_compact(tmp_path)
    data["config"]["spend_monitoring"] = {
        "monitoring_api_spend": False,
        "codexbar_available": True,
        "codex_cost_script_path": str(tmp_path / "home" / ".local" / "bin" / "codex-cost.sh"),
        "codex_cost_script_exists": False,
        "codex_status_line_mentions_spend": False,
    }
    data["config"]["feature_flags"] = {
        "desktop": {"show-context-window-usage": True},
        "tui": {
            "status_line": [
                "current-dir",
                "git-branch",
                "model-with-reasoning",
                "context-remaining",
                "used-tokens",
                "total-input-tokens",
                "total-output-tokens",
                "five-hour-limit",
                "weekly-limit",
            ],
            "status_line_use_colors": True,
        },
    }
    compact.write_text(json.dumps(data))

    run_node(
        "render_report.mjs",
        str(compact),
        "--out",
        str(report),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )

    html = report.read_text()
    assert "Insights / Suggestions" in html
    assert "API spend monitor: codexbar installed" in html
    assert "Tmux integration missing" not in html
    assert "Tmux config" not in html
    assert "Codex status line: detected with extra items" in html
    assert "extra status items not included" in html
    assert "Remove five-hour-limit, weekly-limit" in html
    assert "brew install --cask codexbar" in html
    assert "cat &gt; ~/.local/bin/codex-cost.sh &lt;&lt;'EOF'" in html
    assert "OUTPUT=$(codexbar cost --provider codex 2&gt;/dev/null)" in html
    assert "CUSTOM_COST=$(awk -v creds=&quot;$CREDITS&quot; 'BEGIN {printf &quot;%.2f&quot;, creds * 0.04}')" in html
    assert "echo &quot;Codex: \\$${CUSTOM_COST}&quot;" in html
    assert "chmod +x ~/.local/bin/codex-cost.sh" in html
    assert "set -g status-right &quot;#[fg=green]#( ~/.local/bin/codex-cost.sh )&quot;" in html
    assert "[desktop]" in html
    assert "show-context-window-usage = true" in html
    assert "[tui]" in html
    assert 'status_line = [&quot;current-dir&quot;, &quot;git-branch&quot;, &quot;model-with-reasoning&quot;, &quot;context-remaining&quot;, &quot;used-tokens&quot;, &quot;total-input-tokens&quot;, &quot;total-output-tokens&quot;]' in html
    assert "status_line_use_colors = true" in html
    assert 'status_line = [&quot;current-dir&quot;, &quot;git-branch&quot;, &quot;model-with-reasoning&quot;, &quot;context-remaining&quot;, &quot;used-tokens&quot;, &quot;total-input-tokens&quot;, &quot;total-output-tokens&quot;, &quot;five-hour-limit&quot;, &quot;weekly-limit&quot;]' not in html


def test_public_site_bundle_scrubs_sensitive_data_and_builds(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    report = tmp_path / "private-report.html"
    site_dir = tmp_path / "site"
    data = minimal_compact(tmp_path)
    data["sessions"] = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "thread_name": "Private customer incident thread",
            "cwd": str(tmp_path / "secret-repo"),
            "file": str(tmp_path / "secret-session.jsonl"),
            "path": str(tmp_path / "secret-path"),
            "final_message": "raw private final message",
            "token_history": [{"total_tokens": 1}],
            "total_token_usage": {"total_tokens": 123},
            "last_token_usage": {"total_tokens": 45},
            "total_tokens": 123,
            "window_basis": "lifetime_all",
            "flags": [{"key": "context_load", "label": "large context load"}],
        }
    ]
    data["config"]["config_path"] = str(tmp_path / "home" / ".codex" / "config.toml")
    data["config"]["lean_profile_path"] = str(tmp_path / "home" / ".codex" / "lean.config.toml")
    data["recommendations"][0]["artifact"] = f"read {tmp_path}/secret"
    compact.write_text(json.dumps(data))
    report.write_text("<h1>Private customer incident thread</h1>")

    run_node(
        "build_site_bundle.mjs",
        str(compact),
        "--report",
        str(report),
        "--site-dir",
        str(site_dir),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )
    subprocess.run([NODE, "build.mjs"], cwd=site_dir, check=True, text=True, capture_output=True)

    public_json = json.loads((site_dir / "public" / "data" / "compact.json").read_text())
    public_text = json.dumps(public_json)
    index_html = (site_dir / "public" / "index.html").read_text()

    assert public_json["sessions"][0]["label"] == "Session 1"
    assert "Sessions analyzed" in index_html
    assert "Top sessions shown" in index_html
    assert "Insights / Suggestions" in index_html
    assert "Measured Action Plan" in index_html
    assert "Skill hygiene" in index_html
    assert "MCP attribution" in index_html
    assert "Karpathy LLM Wiki memory system" not in index_html
    assert "/apollo-eng:memory-setup" not in index_html
    for forbidden in [
        "Private customer incident thread",
        "raw private final message",
        "token_history",
        "total_token_usage",
        "last_token_usage",
        "secret-repo",
        "secret-session",
        str(tmp_path),
    ]:
        assert forbidden not in public_text
        assert forbidden not in index_html

    assert (site_dir / "dist" / "client").is_dir()
    assert (site_dir / "dist" / "server" / "index.js").is_file()


def minimal_compact(tmp_path: Path) -> dict:
    return {
        "generated_at": "2026-01-05T00:00:00Z",
        "since": "7d",
        "actual_range": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-05T00:00:00Z"},
        "source_confidence": "exact Codex token_count events",
        "snapshot": {
            "generated_at": "2026-01-05T00:00:00Z",
            "since": "7d",
            "sessions_found": 1,
            "sessions_reported": 1,
            "total_tokens": 123,
            "reasoning_output_tokens": 0,
            "tool_calls": 0,
            "mcp_count": 0,
            "plugin_count": 0,
            "lean_profile_exists": False,
        },
        "totals": {
            "total_tokens": 123,
            "input_tokens": 100,
            "cached_input_tokens": 0,
            "output_tokens": 23,
            "reasoning_output_tokens": 0,
            "tool_calls": 0,
            "tool_output_tokens": 0,
        },
        "config": {
            "config_path": str(tmp_path / "home" / ".codex" / "config.toml"),
            "lean_profile_path": str(tmp_path / "home" / ".codex" / "lean.config.toml"),
            "lean_profile_exists": False,
            "model": "",
            "model_reasoning_effort": "",
            "memories_enabled": False,
            "generate_memories": False,
            "mcp_servers": [],
            "plugins": [],
        },
        "prompt_input": {"ok": False, "error": "not captured"},
        "doctor": {"ok": False, "error": "not captured"},
        "ccusage": {"available": False, "error": "not captured"},
        "sessions": [],
        "flags": {},
        "recommendations": [
            {
                "title": "Use the lean Codex profile for small tasks",
                "mode": "Lean",
                "rationale": "Use a focused profile for local code and shell work.",
                "artifact": "codex -p lean",
            }
        ],
    }
