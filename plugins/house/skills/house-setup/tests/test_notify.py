"""Tests for the Twilio alert helper (dry-run by default; no real sends)."""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "notify.py"
spec = importlib.util.spec_from_file_location("house_notify", SCRIPT)
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)

NOON = dt.datetime(2026, 11, 11, 12, 0)
MIDNIGHT = dt.datetime(2026, 11, 11, 23, 30)


def write_config(tmp_path, **overrides):
    notify_cfg = {"to": "+19785551234", "from": "+15555550100", "profile": "house", "quiet_hours": "22-7"}
    notify_cfg.update(overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notify": notify_cfg}))
    return str(path)


def run(tmp_path, argv, now=NOON, runner=None, **cfg):
    out = io.StringIO()
    runner = runner or (lambda *a, **k: SimpleNamespace(returncode=0))
    code = notify.run(argv + ["--config", write_config(tmp_path, **cfg)], now=now, runner=runner, out=out)
    return code, out.getvalue()


@pytest.mark.parametrize(
    "spec,hour,expected",
    [("22-7", 23, True), ("22-7", 3, True), ("22-7", 12, False), ("9-17", 12, True), ("9-17", 20, False), ("bad", 3, False)],
)
def test_quiet_hours(spec, hour, expected):
    assert notify.in_quiet_hours(spec, dt.datetime(2026, 1, 1, hour)) is expected


def test_dry_run_sends_nothing_and_masks_numbers(tmp_path):
    called = []
    code, out = run(tmp_path, ["sms", "--message", "Test"], runner=lambda *a, **k: called.append(a))
    assert code == 0 and not called
    assert "Dry run" in out and "+19785551234" not in out and "1234" not in out.replace("XXXX", "")


def test_send_runs_twilio_cli(tmp_path):
    seen = []

    def runner(cmd, **kwargs):
        seen.append(cmd)
        return SimpleNamespace(returncode=0)

    code, _ = run(tmp_path, ["sms", "--message", "Pipe burst", "--send"], runner=runner)
    assert code == 0
    cmd = seen[0]
    assert cmd[:3] == ["twilio", "-p", "house"]
    assert "api:core:messages:create" in cmd and "Pipe burst" in cmd


def test_call_builds_escaped_twiml(tmp_path):
    seen = []
    run(tmp_path, ["call", "--message", "Temp <40 & falling", "--send"],
        runner=lambda cmd, **k: seen.append(cmd) or SimpleNamespace(returncode=0))
    twiml = seen[0][seen[0].index("--twiml") + 1]
    assert "&lt;40 &amp; falling" in twiml and twiml.startswith("<Response><Say>")


def test_quiet_hours_block_send(tmp_path):
    called = []
    code, out = run(tmp_path, ["sms", "--message", "x", "--send"], now=MIDNIGHT,
                    runner=lambda *a, **k: called.append(a))
    assert code == 3 and not called and "quiet hours" in out


def test_ignore_quiet_hours_allows_send(tmp_path):
    called = []
    code, _ = run(tmp_path, ["sms", "--message", "x", "--send", "--ignore-quiet-hours"], now=MIDNIGHT,
                  runner=lambda *a, **k: called.append(a) or SimpleNamespace(returncode=0))
    assert code == 0 and called


def test_rejects_bad_numbers_and_long_messages(tmp_path):
    assert run(tmp_path, ["sms", "--message", "x"], to="9785551234")[0] == 2
    assert run(tmp_path, ["sms", "--message", "x" * 400])[0] == 2


def test_failed_send_returns_error(tmp_path):
    code, _ = run(tmp_path, ["sms", "--message", "x", "--send"],
                  runner=lambda *a, **k: SimpleNamespace(returncode=1))
    assert code == 2
