"""Consistency checks between the marketplace and plugin manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO / "plugins"
EXPECTED_DISPLAY_NAMES = {
    "apollo-analytics": "Apollo Analytics",
    "apollo-eng": "Apollo Engineering",
    "apollo-eng-devops": "Apollo Engineering DevOps",
    "apollo-eng-fabric-surfaces": "Apollo Engineering Fabric Surfaces",
    "apollo-eng-leadership": "Apollo Engineering Leadership",
    "apollo-gtm": "Apollo Go-to-Market",
    "apollo-gtm-systems": "Apollo Go-to-Market Systems",
    "apollo-it": "Apollo Information Technology",
    "apollo-product": "Apollo Product",
    "apollo-rnd": "Apollo Research and Development",
    "apollo-legal": "Apollo Legal",
}


@pytest.fixture(scope="module")
def marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text())


def _registered_plugin_dirs() -> list[Path]:
    return sorted(p for p in PLUGINS_DIR.iterdir() if (p / ".claude-plugin" / "plugin.json").exists())


def test_marketplace_entries_resolve(marketplace):
    for entry in marketplace["plugins"]:
        source = (REPO / entry["source"]).resolve()
        assert source.is_dir(), f"{entry['name']}: source {entry['source']} is missing"
        assert (source / ".claude-plugin" / "plugin.json").exists(), (
            f"{entry['name']}: missing plugin.json at {entry['source']}"
        )


def test_marketplace_names_match_manifests(marketplace):
    for entry in marketplace["plugins"]:
        manifest = json.loads((REPO / entry["source"] / ".claude-plugin" / "plugin.json").read_text())
        assert manifest["name"] == entry["name"], (
            f"marketplace name '{entry['name']}' != plugin.json name '{manifest['name']}'"
        )


def test_every_plugin_dir_is_registered(marketplace):
    registered = {entry["name"] for entry in marketplace["plugins"]}
    for plugin_dir in _registered_plugin_dirs():
        assert plugin_dir.name in registered, (
            f"plugins/{plugin_dir.name} exists but is not in marketplace.json"
        )


def test_claude_display_names_are_title_case():
    for plugin_dir in _registered_plugin_dirs():
        manifest = json.loads((plugin_dir / ".claude-plugin" / "plugin.json").read_text())
        assert manifest["displayName"] == EXPECTED_DISPLAY_NAMES[manifest["name"]]
