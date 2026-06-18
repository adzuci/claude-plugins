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


def test_private_report_mentions_memory_setup(tmp_path: Path) -> None:
    compact = tmp_path / "compact.json"
    report = tmp_path / "report.html"
    compact.write_text(json.dumps(minimal_compact(tmp_path)))

    run_node(
        "render_report.mjs",
        str(compact),
        "--out",
        str(report),
        env=isolated_env(tmp_path, tmp_path / "codex"),
    )

    html = report.read_text()
    assert "Karpathy LLM Wiki memory system" in html
    assert "/apollo-eng:memory-setup" in html


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
    assert "Karpathy LLM Wiki memory system" in index_html
    assert "/apollo-eng:memory-setup" in index_html
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
