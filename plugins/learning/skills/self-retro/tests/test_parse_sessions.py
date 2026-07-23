"""Smoke tests for the self-retro session parser."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "parse_sessions.py"
sys.path.insert(0, str(SCRIPT.parent))

import parse_sessions  # noqa: E402


def _write_session(dirpath, name, turns):
    path = Path(dirpath) / name
    with open(path, "w") as f:
        for role, text in turns:
            f.write(json.dumps({
                "type": role,
                "message": {"role": role, "content": text},
                "cwd": "/repo/app/models",
            }) + "\n")
    return str(path)


def test_extract_messages_reads_both_content_shapes():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "s.jsonl"
        with open(p, "w") as f:
            f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "hello"}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"role": "assistant",
                    "content": [{"type": "text", "text": "hi there"}]}}) + "\n")
        msgs = parse_sessions.extract_messages(str(p))
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["text"] == "hello"
    assert msgs[1]["text"] == "hi there"


def test_is_real_session_skips_toolonly():
    with tempfile.TemporaryDirectory() as d:
        toolonly = Path(d) / "tool.jsonl"
        with open(toolonly, "w") as f:
            f.write(json.dumps({"type": "user", "message": {"role": "user",
                    "content": [{"type": "tool_result", "content": "x"}]}}) + "\n")
        real = _write_session(d, "real.jsonl", [("user", "let's debug this")])
        assert parse_sessions.is_real_session(str(toolonly)) is False
        assert parse_sessions.is_real_session(real) is True


def test_no_sessions_exits_2():
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, HOME=d)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--days", "1"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 2
        assert "NO_SESSIONS_FOUND" in result.stderr
