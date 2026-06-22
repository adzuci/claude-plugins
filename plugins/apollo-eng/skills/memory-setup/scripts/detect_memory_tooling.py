"""
detect_memory_tooling.py — Detect existing memory tooling in the Claude Code
installation and report a classification JSON to stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from lib import classify_memory_tooling


def _load_json_file(path: Path) -> dict:
    """Load a JSON file; return {} on missing or malformed."""
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _dir_names(parent: Path) -> list:
    """Return immediate child directory names under *parent*, or [] if absent."""
    try:
        return [p.name for p in parent.iterdir() if p.is_dir()]
    except Exception:
        return []


def gather_info(home: Path | None = None) -> dict:
    if home is None:
        home = Path.home()

    claude_dir = home / ".claude"

    # Load main settings
    settings = _load_json_file(claude_dir / "settings.json")

    # Also check .mcp.json in home for MCP server names
    mcp_settings: dict = {}
    for mcp_path in [
        claude_dir / "settings.json",
        home / ".mcp.json",
        Path.cwd() / ".mcp.json",
    ]:
        data = _load_json_file(mcp_path)
        mcp_settings.update(data.get("mcpServers", {}))

    mcp_names = list(mcp_settings.keys())

    # Marketplace dirs and cache dirs
    marketplace_dirs = _dir_names(claude_dir / "plugins" / "marketplaces")
    cache_dirs = _dir_names(claude_dir / "plugins" / "cache")
    plugin_dirs = marketplace_dirs + cache_dirs

    result = classify_memory_tooling(settings, plugin_dirs, mcp_names)
    result["plugin_dirs"] = plugin_dirs
    result["mcp_names"] = mcp_names
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Detect memory tooling in Claude Code installation.")
    parser.add_argument("--home", metavar="PATH", default=None,
                        help="Override home directory (for testing).")
    args = parser.parse_args()

    home = Path(args.home) if args.home else None
    report = gather_info(home=home)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
