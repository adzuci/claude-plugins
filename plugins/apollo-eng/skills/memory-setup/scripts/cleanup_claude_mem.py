"""
cleanup_claude_mem.py — Detect and optionally remove claude-mem / thedotmack
memory tooling from the Claude Code installation.

Default: dry-run (safe, read-only).  Pass --apply to make changes.

Usage:
    python cleanup_claude_mem.py [--apply] [--home HOME]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from lib import strip_claude_mem_hooks


def _load_settings(path: Path) -> dict:
    """Return parsed JSON or {} on missing/malformed."""
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _find_thedotmack_dirs(claude_dir: Path) -> list:
    """Find thedotmack* marketplace directories."""
    marketplaces = claude_dir / "plugins" / "marketplaces"
    try:
        return [
            str(p)
            for p in marketplaces.iterdir()
            if p.is_dir() and "thedotmack" in p.name.lower()
        ]
    except Exception:
        return []


def _disable_claude_mem_plugin(settings: dict) -> dict:
    """Set enabledPlugins['claude-mem@thedotmack'] = false if present."""
    import copy
    s = copy.deepcopy(settings)
    ep = s.get("enabledPlugins", {})
    if "claude-mem@thedotmack" in ep:
        ep["claude-mem@thedotmack"] = False
    s["enabledPlugins"] = ep
    return s


def run(home: Path, apply: bool, now: int) -> dict:
    claude_dir = home / ".claude"
    settings_path = claude_dir / "settings.json"

    settings = _load_settings(settings_path)
    new_settings, removed_hooks = strip_claude_mem_hooks(settings)
    thedotmack_dirs = _find_thedotmack_dirs(claude_dir)

    plan = {
        "dry_run": not apply,
        "hooks_to_remove": removed_hooks,
        "marketplace_dirs_to_remove": thedotmack_dirs,
        "enable_plugin_flag_to_clear": "claude-mem@thedotmack"
        if "enabledPlugins" in settings
        and settings["enabledPlugins"].get("claude-mem@thedotmack", False)
        else None,
    }

    if not apply:
        plan["note"] = (
            "Dry run — no changes made. Re-run with --apply to apply. "
            "Rollback: restore settings.json from the .bak file created on --apply."
        )
        return plan

    # --- Apply changes ---
    changes: list[str] = []

    # Backup and write stripped settings
    if removed_hooks or plan["enable_plugin_flag_to_clear"]:
        if settings_path.exists():
            bak = settings_path.parent / f"settings.json.bak-{now}"
            shutil.copy2(str(settings_path), str(bak))
            plan["settings_backup"] = str(bak)

        final_settings = new_settings
        if plan["enable_plugin_flag_to_clear"]:
            final_settings = _disable_claude_mem_plugin(final_settings)

        settings_path.write_text(json.dumps(final_settings, indent=2) + "\n")
        if removed_hooks:
            changes.append(f"Removed {len(removed_hooks)} claude-mem hook(s) from settings.json")
        if plan["enable_plugin_flag_to_clear"]:
            changes.append("Disabled claude-mem@thedotmack in enabledPlugins")

    # Remove marketplace dirs
    for d in thedotmack_dirs:
        try:
            shutil.rmtree(d)
            changes.append(f"Removed marketplace dir: {d}")
        except Exception as e:
            changes.append(f"Failed to remove {d}: {e}")

    plan["changes_applied"] = changes
    plan["rollback"] = (
        "To restore: copy settings.json.bak-<timestamp> back to settings.json. "
        "Re-install claude-mem from the thedotmack marketplace if needed."
    )
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect and remove claude-mem / thedotmack memory tooling."
    )
    parser.add_argument("--apply", action="store_true",
                        help="Actually apply changes (default is dry-run).")
    parser.add_argument("--home", default=None, help="Override home directory.")
    parser.add_argument("--now", type=int, default=None,
                        help="Epoch timestamp for backups (default: current time).")
    args = parser.parse_args()

    home = Path(args.home).expanduser() if args.home else Path.home()
    now = args.now if args.now is not None else int(time.time())

    result = run(home=home, apply=args.apply, now=now)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
