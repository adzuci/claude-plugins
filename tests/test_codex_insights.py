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
    empty_bin.mkdir(exist_ok=True)
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


def function_call(name: str, arguments: str = "{}", ts: str | None = None) -> dict:
    row = {"type": "response_item", "payload": {"type": "function_call", "name": name, "arguments": arguments}}
    if ts:
        row["timestamp"] = ts
    return row


def function_call_output(original_token_count: int, ts: str | None = None) -> dict:
    row = {
        "type": "response_item",
        "payload": {"type": "function_call_output", "output": f"Original token count: {original_token_count}"},
    }
    if ts:
        row["timestamp"] = ts
    return row


def user_message(text: str, ts: str | None = None) -> dict:
    row = {"type": "event_msg", "payload": {"type": "user_message", "text": text}}
    if ts:
        row["timestamp"] = ts
    return row


def response_user_message(text: str, ts: str | None = None) -> dict:
    row = {
        "type": "response_item",
        "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]},
    }
    if ts:
        row["timestamp"] = ts
    return row


def test_enumerator_emits_efficiency_week_credits_and_burn_ledger(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex"
    outdir = tmp_path / "scratch"
    lean_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    churn_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # Small, clean session: reads lean and carries work-output signals.
    write_jsonl(
        codex_home / "sessions" / f"{lean_id}.jsonl",
        [
            {"timestamp": "2026-07-06T00:00:00Z", "type": "session_meta", "payload": {"cwd": str(tmp_path / "repo")}},
            response_user_message("injected environment context"),
            response_user_message("fix the api bug"),
            user_message("fix the api bug"),
            function_call("apply_patch"),
            function_call("shell", '{"command": ["bash", "-lc", "pytest -q"]}'),
            function_call("shell", '{"command": ["bash", "-lc", "git commit -m fix"]}'),
            token_count("2026-07-06T00:05:00Z", 8000, input_tokens=6000),
            {"timestamp": "2026-07-06T00:06:00Z", "type": "event_msg", "payload": {"type": "task_complete", "last_agent_message": "done"}},
        ],
    )
    # Large cold re-ingest: 300k uncached input replay → not lean.
    write_jsonl(
        codex_home / "sessions" / f"{churn_id}.jsonl",
        [
            {"timestamp": "2026-07-07T00:00:00Z", "type": "session_meta", "payload": {"cwd": str(tmp_path / "repo")}},
            user_message("keep going"),
            token_count("2026-07-07T00:05:00Z", 320000, input_tokens=300000),
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
    lean = next(s for s in data["sessions"] if s["id"] == lean_id)
    churn = next(s for s in data["sessions"] if s["id"] == churn_id)

    assert lean["efficiency"] == "lean"
    assert lean["edit_events"] >= 1
    assert lean["test_events"] == 1
    assert lean["commit_events"] == 1
    # Current logs emit response_item/user rows (including injected context) plus
    # one event_msg/user_message for the human prompt. Count only the latter.
    assert lean["user_prompt_count"] == 1
    assert lean["completed"] is True
    assert lean["credits"] == 8
    assert lean["week"] == "2026-07-06"  # 2026-07-06 is itself a Monday

    assert churn["efficiency"] in {"loose", "thrashy"}
    assert churn["efficiency_signals"]["cold_reingest"] == 3

    # Snapshot + aggregate additions.
    assert data["snapshot"]["credits"] == data["totals"]["credits"]
    assert set(data["snapshot"]["efficiency_mix"]) == {"lean", "loose", "thrashy"}

    weeks = {w["week"]: w for w in data["by_week"]}
    assert set(weeks) == {"2026-07-06"}  # both sessions fall in the same ISO week
    week = weeks["2026-07-06"]
    assert week["total_tokens"] == 328000
    assert week["efficiency_tokens"]["lean"] == 8000

    ledger = {row["id"]: row for row in data["burn_analysis"]["sessions"]}
    assert ledger[lean_id]["roi"] is None
    assert ledger[lean_id]["outcome"] is None
    assert ledger[lean_id]["efficiency"] == "lean"
    assert data["burn_analysis"]["overall_verdict"] is None


def test_enumerator_windows_churn_signals_not_just_tokens(tmp_path: Path) -> None:
    # Regression for PR #175 review: a --since window must recompute the per-session
    # churn / work-output counts (prompts, edits, tool reuse, large outputs), not mix
    # window-scoped token totals with LIFETIME counts. Otherwise a long-lived session
    # is mislabeled on the default 7d run.
    codex_home = tmp_path / "codex"
    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    write_jsonl(
        codex_home / "sessions" / f"{session_id}.jsonl",
        [
            {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"cwd": str(tmp_path / "repo")}},
            # --- heavy activity BEFORE the window (January) ---
            user_message("p1", ts="2026-01-01T00:01:00Z"),
            user_message("p2", ts="2026-01-01T00:02:00Z"),
            user_message("p3", ts="2026-01-01T00:03:00Z"),
            function_call("apply_patch", ts="2026-01-01T00:04:00Z"),
            function_call("apply_patch", ts="2026-01-01T00:05:00Z"),
            function_call_output(9000, ts="2026-01-01T00:06:00Z"),
            function_call_output(9000, ts="2026-01-01T00:07:00Z"),
            token_count("2026-01-01T01:00:00Z", 100000, input_tokens=100000),
            token_count("2026-01-02T01:00:00Z", 300000, input_tokens=300000),
            # --- light activity INSIDE the window (July) ---
            user_message("recent question", ts="2026-07-02T00:00:00Z"),
            function_call("shell", '{"command": ["bash", "-lc", "ls"]}', ts="2026-07-02T00:01:00Z"),
            token_count("2026-07-02T00:05:00Z", 305000, input_tokens=302000),
        ],
    )

    windowed_dir = tmp_path / "windowed"
    run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "2026-07-01",
        "--outdir",
        str(windowed_dir),
        env=isolated_env(tmp_path, codex_home),
    )
    windowed = json.loads((windowed_dir / "compact.json").read_text())
    w = next(s for s in windowed["sessions"] if s["id"] == session_id)
    assert w["window_basis"] == "delta_from_prior_token_count"
    assert w["total_tokens"] == 5000  # 305k - 300k prior count
    # Counts are scoped to the window, not lifetime.
    assert w["user_prompt_count"] == 1
    assert w["edit_events"] == 0
    assert w["high_output_events"] == 0
    assert w["token_events"] == 1
    assert w["tool_calls"] == 1
    assert w["tools"] == {"shell": 1}
    assert "signal_events" not in w  # internal buffer never serialized

    lifetime_dir = tmp_path / "lifetime"
    run_node(
        "enumerate_codex_sessions.mjs",
        "--since",
        "all",
        "--outdir",
        str(lifetime_dir),
        env=isolated_env(tmp_path, codex_home),
    )
    lifetime = json.loads((lifetime_dir / "compact.json").read_text())
    a = next(s for s in lifetime["sessions"] if s["id"] == session_id)
    assert a["total_tokens"] == 305000
    assert a["user_prompt_count"] == 4
    assert a["edit_events"] == 2
    assert a["high_output_events"] == 2
    assert a["tool_calls"] == 3
    # The whole point: windowed counts are strictly smaller than lifetime counts.
    assert w["user_prompt_count"] < a["user_prompt_count"]


def test_render_report_shows_burn_vs_output_lead(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    report = tmp_path / "report.html"
    data = minimal_compact(tmp_path)
    data["totals"]["credits"] = 328
    data["by_week"] = [
        {
            "week": "2026-06-29",
            "total_tokens": 328000,
            "credits": 328,
            "sessions": 2,
            "prompts": 2,
            "efficiency_tokens": {"lean": 8000, "loose": 320000, "thrashy": 0},
            "efficiency_count": {"lean": 1, "loose": 1, "thrashy": 0},
        }
    ]
    data["burn_analysis"] = {
        "overall_verdict": None,
        "weekly": [],
        "sessions": [
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "label": "fix the api bug",
                "total_tokens": 8000,
                "credits": 8,
                "efficiency": "lean",
                "edit_events": 1,
                "test_events": 1,
                "commit_events": 1,
                "user_prompt_count": 1,
                "completed": True,
                "roi": None,
                "outcome": None,
                "verdict": None,
            }
        ],
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
    assert "Week by Week" in html
    assert "Burn vs Output" in html
    assert "were not judged in this run" in html
    assert "efficiency" in html
    # Deterministic config sections still render.
    assert "Measured Action Plan" in html
    assert "Where Tokens Went" in html


def test_render_report_merges_judgments(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    judgments = tmp_path / "judgments.json"
    report = tmp_path / "report.html"
    data = minimal_compact(tmp_path)
    data["burn_analysis"] = {
        "overall_verdict": None,
        "weekly": [],
        "sessions": [
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "label": "fix the api bug",
                "total_tokens": 320000,
                "credits": 320,
                "efficiency": "loose",
                "completed": True,
                "roi": None,
                "outcome": None,
                "verdict": None,
            }
        ],
    }
    compact.write_text(json.dumps(data))
    judgments.write_text(
        json.dumps(
            {
                "overall_verdict": "Of ~320 credits, one session landed a real fix but was overpriced by a cold re-ingest.",
                "weekly": [{"week": "2026-06-29", "headline": "One replay-heavy debugging session."}],
                "sessions": [
                    {
                        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                        "roi": "overpriced",
                        "outcome": "landed",
                        "verdict": "Fix applied, but a 300k cold re-ingest inflated the bill.",
                    }
                ],
            }
        )
    )

    run_node(
        "render_report.mjs",
        str(compact),
        "--out",
        str(report),
        "--judgments",
        str(judgments),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )
    html = report.read_text()
    assert "overpriced" in html
    assert "landed" in html
    assert "cold re-ingest inflated the bill" in html
    assert "one session landed a real fix" in html
    assert "were not judged in this run" not in html


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


def test_site_bundle_omits_burn_analysis_labels_and_verdicts(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    report = tmp_path / "private-report.html"
    site_dir = tmp_path / "site"
    data = minimal_compact(tmp_path)
    data["by_week"] = [
        {
            "week": "2026-06-29",
            "total_tokens": 8000,
            "credits": 8,
            "sessions": 1,
            "prompts": 1,
            "efficiency_tokens": {"lean": 8000, "loose": 0, "thrashy": 0},
            "efficiency_count": {"lean": 1, "loose": 0, "thrashy": 0},
        }
    ]
    data["burn_analysis"] = {
        "overall_verdict": "Private overall verdict naming a secret customer thread",
        "weekly": [{"week": "2026-06-29", "headline": "Private weekly headline"}],
        "sessions": [
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "label": "Private customer incident thread",
                "verdict": "Private per-session verdict",
                "efficiency": "lean",
            }
        ],
    }
    compact.write_text(json.dumps(data))
    report.write_text("<h1>private</h1>")

    run_node(
        "build_site_bundle.mjs",
        str(compact),
        "--report",
        str(report),
        "--site-dir",
        str(site_dir),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )

    public_json = json.loads((site_dir / "public" / "data" / "compact.json").read_text())
    public_text = json.dumps(public_json)
    assert "burn_analysis" not in public_json
    assert public_json["by_week"][0]["total_tokens"] == 8000
    for forbidden in [
        "Private customer incident thread",
        "Private overall verdict",
        "Private weekly headline",
        "Private per-session verdict",
    ]:
        assert forbidden not in public_text


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
