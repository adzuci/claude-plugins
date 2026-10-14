"""Tests for the config.md frontmatter loader shipped with generalized skills."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

LOADER = Path(__file__).resolve().parent.parent / "references" / "config_loader.py"


def _load():
    spec = importlib.util.spec_from_file_location("config_loader", LOADER)
    if spec is None or spec.loader is None:
        pytest.skip("config_loader.py not available")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cl():
    if not LOADER.exists():
        pytest.skip("config_loader.py has not landed yet")
    return _load()


CONFIG = '''---
team_name: "Growth Conversion"
jira_project_key: CVR
retries: 3
threshold: 0.05
enabled: true
disabled: false
missing: null
assignees: ["alice", "bob"]
empty_list: []
unset_value: "<UNSET>"
blank: ""
---

# Setup Guide

Body text is ignored.
'''


def test_parses_scalars_and_types(cl):
    cfg = cl.parse_frontmatter(CONFIG)
    assert cfg["team_name"] == "Growth Conversion"
    assert cfg["jira_project_key"] == "CVR"
    # Numbers stay strings on purpose: config values are identifiers, and
    # coercing them loses leading zeros and trailing-zero version numbers.
    assert cfg["retries"] == "3"
    assert cfg["threshold"] == "0.05"
    assert cfg["enabled"] is True
    assert cfg["disabled"] is False
    assert cfg["missing"] is None


def test_parses_flow_lists(cl):
    cfg = cl.parse_frontmatter(CONFIG)
    assert cfg["assignees"] == ["alice", "bob"]
    assert cfg["empty_list"] == []


def test_body_is_not_parsed_as_config(cl):
    cfg = cl.parse_frontmatter(CONFIG)
    assert "Body text is ignored" not in cfg
    assert "# Setup Guide" not in cfg


def test_missing_frontmatter_returns_empty(cl):
    assert cl.parse_frontmatter("# Just a heading\n\nNo frontmatter here.\n") == {}


def test_is_unset_only_covers_genuinely_missing_values(cl):
    assert cl.is_unset("<UNSET>")
    assert cl.is_unset(None)
    # An empty value is a deliberate answer in this format, not a missing one.
    assert not cl.is_unset("")
    assert not cl.is_unset("   ")
    assert not cl.is_unset([])
    assert not cl.is_unset("CVR")
    assert not cl.is_unset(["alice"])
    assert not cl.is_unset(0)


def test_load_config_reads_a_file(cl, tmp_path):
    path = tmp_path / "config.md"
    path.write_text(CONFIG, encoding="utf-8")
    assert cl.load_config(path)["jira_project_key"] == "CVR"


def test_load_config_raises_when_absent(cl, tmp_path):
    with pytest.raises(FileNotFoundError):
        cl.load_config(tmp_path / "nope" / "config.md")

# --- Regression tests for PR #284 review findings ---


def test_empty_string_is_a_deliberate_answer_not_unset(cl):
    """Shipped configs use "" to mean "skip this"; re-asking defeats the point."""
    assert not cl.is_unset("")
    assert not cl.is_unset("   ")
    assert not cl.is_unset([])
    assert cl.is_unset("<UNSET>")
    assert cl.is_unset(None)


def test_inline_comment_is_stripped(cl):
    cfg = cl.parse_frontmatter('---\nkey: "CVR"  # the project key\n---\n')
    assert cfg["key"] == "CVR"


def test_hash_inside_quotes_survives(cl):
    cfg = cl.parse_frontmatter('---\nchan: "#growth-conversion-pd"  # deploys\n---\n')
    assert cfg["chan"] == "#growth-conversion-pd"


def test_unquoted_leading_hash_is_kept_as_a_channel(cl):
    cfg = cl.parse_frontmatter("---\nchan: #growth-conversion-pd\n---\n")
    assert cfg["chan"] == "#growth-conversion-pd"


def test_identifiers_keep_their_exact_form(cl):
    """Numeric coercion destroyed leading zeros and trailing-zero versions."""
    cfg = cl.parse_frontmatter("---\nid: 007\nver: 1.10\n---\n")
    assert cfg["id"] == "007"
    assert cfg["ver"] == "1.10"


def test_frontmatter_without_trailing_newline_parses(cl):
    assert cl.parse_frontmatter("---\nkey: CVR\n---") == {"key": "CVR"}


def test_saved_answers_override_shipped_defaults(cl, tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "USER_CONFIG_ROOT", tmp_path / "plugin-config")
    shipped = tmp_path / "config.md"
    shipped.write_text('---\na: "<UNSET>"\nb: ""\nc: "default"\n---\n', encoding="utf-8")

    cl.save_config("apollo-growth", "jira-task", {"a": "CVR", "b": ""})
    merged = cl.load_config(shipped, plugin="apollo-growth", skill="jira-task")

    assert merged["a"] == "CVR"      # answered
    assert merged["b"] == ""         # deliberate blank preserved
    assert merged["c"] == "default"  # untouched shipped default


def test_saved_config_lives_outside_the_skill_folder(cl, tmp_path, monkeypatch):
    """The whole point: a plugin update must not wipe the user's answers."""
    monkeypatch.setattr(cl, "USER_CONFIG_ROOT", tmp_path / "plugin-config")
    written = cl.save_config("apollo-growth-product", "jira-task", {"k": "v"})
    assert written == tmp_path / "plugin-config" / "apollo-growth-product" / "jira-task.md"
    assert cl.parse_frontmatter(written.read_text(encoding="utf-8")) == {"k": "v"}


def test_load_config_without_plugin_returns_shipped_only(cl, tmp_path):
    shipped = tmp_path / "config.md"
    shipped.write_text('---\na: "<UNSET>"\n---\n', encoding="utf-8")
    assert cl.load_config(shipped) == {"a": "<UNSET>"}
