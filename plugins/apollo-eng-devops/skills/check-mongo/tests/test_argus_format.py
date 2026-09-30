"""evaluate.py --format argus: the exact Slack post Argus should produce (<=120 words)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

mod = pytest.importorskip("evaluate")

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "evaluate.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
BULLETS = ("**Alert**", "**Root cause**", "**Couldn't verify**", "**Next step**")


def post(results, cluster="main", **kw):
    return mod.render_argus(mod.evaluate(results, cluster), **kw)


@pytest.mark.parametrize("name", ["healthy", "router_down", "router_missing", "multi_reset", "no_primary", "empty"])
def test_shape_and_word_budget(load, name):
    text = post(load(name))
    assert len(text.split()) <= 120, (len(text.split()), text)
    lines = text.splitlines()
    assert lines[0].startswith("*") and lines[0].endswith("*")
    assert lines[1].startswith("_") and lines[1].endswith("_") and lines[1].count(" · ") == 2
    assert "confidence 0." in lines[1]
    for b in BULLETS:
        assert sum(1 for line in lines if line.startswith(f"- {b}")) == 1, b
    assert lines[-1].startswith("cc:")


def test_states_each_router_up_state(load):
    text = post(load("router_down"))
    assert "mongos-main-3 down" in text
    for i in (0, 1, 2):
        assert f"mongos-main-{i} up" in text


def test_absent_router_is_named_absent(load):
    text = post(load("router_missing"))
    assert " absent" in text


def test_unknown_is_never_rendered_as_healthy(load):
    text = post(load("empty"))
    assert "UNKNOWN" in text.splitlines()[0]
    lowered = text.lower()
    assert "healthy" not in lowered and "all clear" not in lowered and "is resolved" not in lowered and "not resolved" in lowered
    assert "no data" in lowered


def test_never_calls_resolved_and_lists_human_only(load):
    for name in ("healthy", "router_down"):
        text = post(load(name))
        assert "HUMAN-ONLY" in text
        assert "15-30 min" in text


def test_escalate_names_the_check_and_stays_read_only(load):
    text = post(load("multi_reset"))
    assert "ESCALATE" in text.splitlines()[0]
    assert "restarts" in text
    assert "ssh" not in text and "mongosh" not in text.replace("HUMAN-ONLY", "")


def test_seven_routers_still_fit(load):
    r = load("healthy")
    for key in ("up", "uptime", "connections", "restarts", "mem_resident"):
        extra = [json.loads(json.dumps(s)) for s in r[key] if s["metric"].get("role") == "mongos"]
        for i, s in enumerate(extra):
            s["metric"]["instance"] = s["metric"]["instance"].replace(f"mongos-main-{i}", f"mongos-main-{i + 4}")
        r[key] += extra[:3]
    text = post(r)
    assert len(text.split()) <= 120
    assert "mongos-main-6 up" in text


def test_cli_format_argus_exit_codes(tmp_path):
    ok = subprocess.run([sys.executable, str(SCRIPT), "--results", str(FIXTURES / "router_down.json"),
                         "--format", "argus"], capture_output=True, text=True)
    assert ok.returncode == 0 and "**Alert**" in ok.stdout
    bad = subprocess.run([sys.executable, str(SCRIPT), "--results", str(tmp_path / "nope.json"),
                          "--format", "argus"], capture_output=True, text=True)
    assert bad.returncode == 2
    badc = subprocess.run([sys.executable, str(SCRIPT), "--results", str(FIXTURES / "healthy.json"),
                           "--cluster", "nope", "--format", "argus"], capture_output=True, text=True)
    assert badc.returncode == 2


def test_default_table_output_unchanged(load):
    r = mod.evaluate(load("healthy"), "main")
    assert mod.render_markdown(r).startswith("# check-mongo: main -> OK")
    assert "routers" in r  # additive key only
