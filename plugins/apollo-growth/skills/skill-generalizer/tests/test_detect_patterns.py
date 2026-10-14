"""Tests for the skill-generalizer pattern scanner."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "detect_patterns.py"
pytest.importorskip("json")


def _load():
    spec = importlib.util.spec_from_file_location("detect_patterns", SCRIPT)
    if spec is None or spec.loader is None:
        pytest.skip("detect_patterns.py not available")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def dp():
    if not SCRIPT.exists():
        pytest.skip("detect_patterns.py has not landed yet")
    return _load()


def _scan(dp, tmp_path: Path, name: str, body: str):
    (tmp_path / name).write_text(body, encoding="utf-8")
    return dp.walk(tmp_path)


def _values(findings, category=None):
    return {f["match"] for f in findings if category is None or f["category"] == category}


def test_finds_notion_collection_id(dp, tmp_path):
    found = _scan(dp, tmp_path, "SKILL.md", "Target: collection://230ab2b3-b496-8092-97f9-000bf8e1c8c9\n")
    assert "collection://230ab2b3-b496-8092-97f9-000bf8e1c8c9" in _values(found, "external_id")


def test_finds_slack_channel_and_email(dp, tmp_path):
    found = _scan(dp, tmp_path, "SKILL.md", "Post in #growth-conversion-pd and ping a@b.io\n")
    assert "#growth-conversion-pd" in _values(found, "external_id")
    assert "a@b.io" in _values(found, "person")


def test_finds_home_and_absolute_paths(dp, tmp_path):
    found = _scan(dp, tmp_path, "SKILL.md", "Read ~/code/notes/voice.md and /Users/someone/x.md\n")
    paths = _values(found, "file_path")
    assert "~/code/notes/voice.md" in paths
    assert "/Users/someone/x.md" in paths


def test_earlier_pattern_wins_on_overlap(dp, tmp_path):
    """A collection:// URI must not also be reported as a bare uuid."""
    found = _scan(dp, tmp_path, "SKILL.md", "collection://230ab2b3-b496-8092-97f9-000bf8e1c8c9\n")
    names = {f["pattern_name"] for f in found}
    assert "notion_collection" in names
    assert "uuid" not in names


def test_line_numbers_are_one_indexed_and_correct(dp, tmp_path):
    body = "nothing here\nstill nothing\nemail: person@example.com\n"
    found = _scan(dp, tmp_path, "SKILL.md", body)
    hits = [f for f in found if f["category"] == "person"]
    assert len(hits) == 1
    assert hits[0]["line"] == 3


def test_offsets_do_not_suppress_later_matches(dp, tmp_path):
    """Regression: overlap bookkeeping must not drop identical values on later lines."""
    body = "\n".join(f"line {i} ping alice@example.com" for i in range(1, 6)) + "\n"
    found = _scan(dp, tmp_path, "SKILL.md", body)
    hits = [f for f in found if f["match"] == "alice@example.com"]
    assert len(hits) == 5
    assert [h["line"] for h in hits] == [1, 2, 3, 4, 5]


def test_skips_binary_and_vendor_paths(dp, tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.py").write_text("a@b.io\n", encoding="utf-8")
    (tmp_path / "img.png").write_bytes(b"\x89PNG a@b.io")
    assert dp.walk(tmp_path) == []


def test_collapse_duplicates_groups_by_value(dp, tmp_path):
    body = "a@b.io\nsomething else\na@b.io\n"
    collapsed = dp.collapse_duplicates(_scan(dp, tmp_path, "SKILL.md", body))
    emails = [c for c in collapsed["unique_candidates"] if c["value"] == "a@b.io"]
    assert len(emails) == 1
    assert len(emails[0]["occurrences"]) == 2
    assert collapsed["total_occurrences"] == 2


def test_cli_emits_json_and_rejects_bad_path(tmp_path):
    (tmp_path / "SKILL.md").write_text("collection://230ab2b3-b496-8092-97f9-000bf8e1c8c9\n", encoding="utf-8")
    ok = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert ok.returncode == 0
    assert json.loads(ok.stdout)["total_occurrences"] == 1

    bad = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "nope")], capture_output=True, text=True)
    assert bad.returncode == 1

# --- Regression tests for PR #284 review findings ---


def test_grouped_pattern_reports_the_group_not_the_whole_match(dp, tmp_path):
    """A capturing group is the identifier; group(0) drags in surrounding words."""
    a = _scan(dp, tmp_path, "a.md", "Jira project: CVR-123\n")
    assert _values(a, "external_id") == {"CVR"}


def test_same_id_reports_identically_across_phrasings(dp, tmp_path):
    """Two phrasings of one project key must collapse to a single candidate."""
    body = 'Jira project: CVR-123\nalso project key "CVR"\n'
    collapsed = dp.collapse_duplicates(_scan(dp, tmp_path, "a.md", body))
    keys = [c for c in collapsed["unique_candidates"] if c["pattern_name"] == "jira_project_key"]
    assert len(keys) == 1
    assert keys[0]["value"] == "CVR"
    assert len(keys[0]["occurrences"]) == 2


def test_wider_later_match_cannot_swallow_an_earlier_one(dp, tmp_path):
    """A Notion URL reports once, as the id, not also as a url."""
    found = _scan(dp, tmp_path, "a.md", "https://notion.so/32fab2b3b49681f588eccbf5855d5baf\n")
    assert {f["pattern_name"] for f in found} == {"notion_id_no_dashes"}


def test_hex_colors_are_not_slack_channels(dp, tmp_path):
    assert _scan(dp, tmp_path, "a.md", "brandColor #1f2937 and #abc and #1F2937FF\n") == []


def test_markdown_anchors_are_not_slack_channels(dp, tmp_path):
    assert _scan(dp, tmp_path, "a.md", "See [Setup](#setup-guide) below.\n") == []


def test_real_slack_channels_still_detected(dp, tmp_path):
    found = _scan(dp, tmp_path, "a.md", "Post in #growth-conversion-pd when live\n")
    assert _values(found, "external_id") == {"#growth-conversion-pd"}
