"""Consistency checks between the marketplace and plugin manifests."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = REPO / ".agents" / "plugins" / "marketplace.json"
PLUGINS_DIR = REPO / "plugins"
SKILL_INVENTORY = REPO / "SKILL_INVENTORY.md"
UPDATE_INVENTORY_SCRIPT = REPO / ".github" / "scripts" / "update-skill-inventory.py"
PLUGIN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
EXPECTED_DISPLAY_NAMES = {
    "apollo-analytics": "Apollo Analytics",
    "apollo-eng": "Apollo Engineering",
    "apollo-eng-agentic-engineering": "Apollo Engineering Agentic Engineering",
    "apollo-eng-devops": "Apollo Engineering DevOps",
    "apollo-eng-fabric-surfaces": "Apollo Engineering Fabric Surfaces",
    "apollo-eng-leadership": "Apollo Engineering Leadership",
    "apollo-gtm": "Apollo Go-to-Market",
    "apollo-gtm-systems": "Apollo Go-to-Market Systems",
    "apollo-it": "Apollo Information Technology",
    "apollo-product": "Apollo Product",
    "apollo-support": "Apollo Support",
    "apollo-rnd": "Apollo Research and Development",
    "apollo-legal": "Apollo Legal",
    "apollo-people": "Apollo People",
    "apollo-marketing": "Apollo Marketing",
    "apollo-gtm-enablement": "Apollo GTM Enablement",
    "apollo-risk": "Apollo Risk",
    "apollo-corpsec": "Apollo Corporate Security",
    "apollo-talent": "Apollo Talent",
    "apollo-procurement": "Apollo Procurement",
    "apollo-accounting": "Apollo Accounting",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines()
    assert lines and lines[0].strip() == "---", f"{path}: missing YAML frontmatter"

    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    raise AssertionError(f"{path}: unterminated YAML frontmatter")


def _load_inventory_script():
    spec = importlib.util.spec_from_file_location("update_skill_inventory", UPDATE_INVENTORY_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_generated_block(path: Path, start: str, end: str) -> str:
    content = path.read_text()
    assert start in content, f"{path}: missing {start}"
    assert end in content, f"{path}: missing {end}"
    return content.split(start, 1)[1].split(end, 1)[0].strip()


@pytest.fixture(scope="module")
def marketplace() -> dict:
    return _load_json(MARKETPLACE)


@pytest.fixture(scope="module")
def codex_marketplace() -> dict:
    return _load_json(CODEX_MARKETPLACE)


def _registered_plugin_dirs() -> list[Path]:
    return sorted(p for p in PLUGINS_DIR.iterdir() if (p / ".claude-plugin" / "plugin.json").exists())


def _published_plugin_dirs(marketplace) -> list[Path]:
    return [REPO / entry["source"] for entry in marketplace["plugins"]]


def test_marketplace_entries_resolve(marketplace):
    for entry in marketplace["plugins"]:
        source = (REPO / entry["source"]).resolve()
        assert source.is_dir(), f"{entry['name']}: source {entry['source']} is missing"
        assert (source / ".claude-plugin" / "plugin.json").exists(), (
            f"{entry['name']}: missing plugin.json at {entry['source']}"
        )


def test_marketplace_names_match_manifests(marketplace):
    for entry in marketplace["plugins"]:
        manifest = _load_json(REPO / entry["source"] / ".claude-plugin" / "plugin.json")
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
        manifest = _load_json(plugin_dir / ".claude-plugin" / "plugin.json")
        assert manifest["displayName"] == EXPECTED_DISPLAY_NAMES[manifest["name"]]


def test_codex_marketplace_matches_claude_marketplace(marketplace, codex_marketplace):
    claude_names = [entry["name"] for entry in marketplace["plugins"]]
    codex_names = [entry["name"] for entry in codex_marketplace["plugins"]]

    assert len(claude_names) == len(set(claude_names))
    assert len(codex_names) == len(set(codex_names))
    assert codex_names == claude_names

    for claude_entry, codex_entry in zip(marketplace["plugins"], codex_marketplace["plugins"]):
        name = claude_entry["name"]
        assert codex_entry["source"]["source"] == "local"
        assert codex_entry["source"]["path"] == claude_entry["source"]
        assert codex_entry["policy"]["installation"] == "AVAILABLE"
        assert codex_entry["policy"]["authentication"] == "ON_INSTALL"
        assert codex_entry["category"], f"{name}: missing Codex marketplace category"


def test_codex_manifests_exist_for_published_plugins(marketplace):
    for entry in marketplace["plugins"]:
        source = REPO / entry["source"]
        assert (source / ".codex-plugin" / "plugin.json").exists(), (
            f"{entry['name']}: missing Codex plugin.json at {entry['source']}"
        )


def test_codex_display_names_match_claude_manifests(marketplace):
    for entry in marketplace["plugins"]:
        source = REPO / entry["source"]
        claude_manifest = _load_json(source / ".claude-plugin" / "plugin.json")
        codex_manifest = _load_json(source / ".codex-plugin" / "plugin.json")
        assert codex_manifest["interface"]["displayName"] == claude_manifest["displayName"]


def test_codex_declared_icons_exist(marketplace):
    for entry in marketplace["plugins"]:
        source = REPO / entry["source"]
        codex_manifest = _load_json(source / ".codex-plugin" / "plugin.json")
        interface = codex_manifest["interface"]
        for field in ("composerIcon", "logo"):
            asset_path = interface.get(field)
            if asset_path is None:
                continue
            assert asset_path.startswith("./"), f"{entry['name']}: {field} must be relative"
            assert (source / asset_path).exists(), (
                f"{entry['name']}: {field} asset does not exist: {asset_path}"
            )


def test_plugin_manifests_have_required_codex_and_claude_fields(marketplace):
    for plugin_dir in _published_plugin_dirs(marketplace):
        claude_manifest = _load_json(plugin_dir / ".claude-plugin" / "plugin.json")
        codex_manifest = _load_json(plugin_dir / ".codex-plugin" / "plugin.json")

        assert claude_manifest["name"] == plugin_dir.name
        assert PLUGIN_NAME_RE.match(claude_manifest["name"])
        assert SEMVER_RE.match(claude_manifest["version"])
        for field in ("displayName", "description"):
            assert claude_manifest[field]

        assert codex_manifest["name"] == claude_manifest["name"]
        assert codex_manifest["version"] == claude_manifest["version"]
        assert SEMVER_RE.match(codex_manifest["version"])
        for field in ("description", "repository", "license"):
            assert codex_manifest[field]

        interface = codex_manifest["interface"]
        for field in ("displayName", "shortDescription", "developerName", "category"):
            assert interface[field], f"{plugin_dir.name}: missing Codex interface.{field}"


def test_codex_declared_paths_exist(marketplace):
    for plugin_dir in _published_plugin_dirs(marketplace):
        codex_manifest = _load_json(plugin_dir / ".codex-plugin" / "plugin.json")
        if (plugin_dir / "skills").is_dir():
            assert codex_manifest["skills"] == "./skills/"

        mcp_servers = codex_manifest.get("mcpServers")
        if mcp_servers is not None:
            assert mcp_servers.startswith("./"), f"{plugin_dir.name}: mcpServers must be relative"
            assert (plugin_dir / mcp_servers).exists(), f"{plugin_dir.name}: mcpServers path is missing"


def test_skill_frontmatter_names_are_unique_and_match_directories(marketplace):
    skill_paths: list[Path] = []
    for plugin_dir in _published_plugin_dirs(marketplace):
        skill_paths.extend(sorted((plugin_dir / "skills").glob("*/SKILL.md")))
    skill_paths.extend(sorted((REPO / ".claude" / "skills").glob("*/SKILL.md")))

    by_name: dict[str, list[Path]] = {}
    for path in skill_paths:
        frontmatter = _parse_frontmatter(path)
        skill_name = frontmatter.get("name")
        assert skill_name == path.parent.name, f"{path}: frontmatter name must match directory"
        assert PLUGIN_NAME_RE.match(skill_name), f"{path}: skill name must be lowercase kebab-case"
        assert frontmatter.get("description"), f"{path}: description is required"
        by_name.setdefault(skill_name, []).append(path)

    duplicates = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    assert not duplicates, "skill names must be unique across plugins and repo-local .claude/skills"


def test_generated_inventory_files_are_current(monkeypatch):
    monkeypatch.chdir(REPO)
    inventory = _load_inventory_script()

    readme_plugin_table = _extract_generated_block(
        REPO / "README.md", inventory.README_PLUGIN_START, inventory.README_PLUGIN_END
    )
    assert readme_plugin_table == inventory.build_plugin_table()

    skill_table = _extract_generated_block(
        SKILL_INVENTORY, inventory.SKILL_START, inventory.SKILL_END
    )
    assert skill_table == inventory.build_skill_table()
