"""
install_hook.py — Install the SessionEnd hook script and register it in
~/.claude/settings.json.

Usage:
    python install_hook.py --vault VAULTPATH [--home HOME] [--now EPOCH_INT]
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

from lib import merge_session_end_hook, render_template

_SKILL_DIR = Path(__file__).resolve().parent.parent
_TEMPLATE_PATH = _SKILL_DIR / "templates" / "session-end.sh.tmpl"
_HOOK_CMD = "~/.claude/hooks/session-end.sh"


def _backup_path(base: Path, now: int) -> Path:
    return base.parent / f"{base.name}.bak-{now}"


def _load_settings(path: Path) -> tuple[dict, str | None, bool]:
    """Return (settings_dict, error, should_backup). Missing -> ({}, None, False)."""
    if not path.exists():
        return {}, None, False
    try:
        return json.loads(path.read_text()), None, False
    except json.JSONDecodeError:
        return {}, "settings.json is malformed JSON.", True
    except OSError as exc:
        return {}, f"settings.json could not be read: {exc}", False


def install(vault: str, home: Path, now: int) -> dict:
    hooks_dir = home / ".claude" / "hooks"
    hook_script = hooks_dir / "session-end.sh"
    settings_path = home / ".claude" / "settings.json"

    # Validate settings before mutating the filesystem. A malformed settings
    # file must stop the install without replacing the hook script.
    settings, settings_error, should_backup = _load_settings(settings_path)

    if settings_error:
        bak = None
        backup_ok = None
        if should_backup:
            bak = _backup_path(settings_path, now)
            backup_ok = True
            try:
                shutil.copy2(str(settings_path), str(bak))
            except OSError as exc:
                backup_ok = False
                bak = f"{bak} (backup FAILED: {exc})"
        return {
            "ok": False,
            "backup_ok": backup_ok,
            "error": f"{settings_error} "
                     + (f"Backed up to {bak}. " if bak else "")
                     + "Please fix manually before re-running.",
            "backup": str(bak) if bak else None,
        }

    # --- Render hook script from template ---
    try:
        template_text = _TEMPLATE_PATH.read_text()
        rendered = render_template(template_text, {"VAULT": vault})
    except (OSError, ValueError) as e:
        return {"ok": False, "error": f"Template rendering failed: {e}"}

    # Write hook script
    try:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_script.write_text(rendered)
        hook_script.chmod(0o755)
    except OSError as exc:
        return {"ok": False, "error": f"Hook script write failed: {exc}"}

    # Backup settings before writing
    if settings_path.exists():
        bak = _backup_path(settings_path, now)
        try:
            shutil.copy2(str(settings_path), str(bak))
        except OSError as exc:
            return {"ok": False, "error": f"settings.json backup failed: {exc}", "backup": str(bak)}
    else:
        bak = None

    # Merge hook
    new_settings = merge_session_end_hook(settings, _HOOK_CMD)

    # Write new settings
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(new_settings, indent=2) + "\n")
    except OSError as exc:
        return {"ok": False, "error": f"settings.json write failed: {exc}"}

    return {
        "ok": True,
        "hook_script": str(hook_script),
        "settings": str(settings_path),
        "settings_backup": str(bak) if bak else None,
        "vault": vault,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Install SessionEnd hook for memory vault.")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault.")
    parser.add_argument("--home", default=None, help="Override home directory.")
    parser.add_argument("--now", type=int, default=None,
                        help="Epoch timestamp for backups (default: current time).")
    args = parser.parse_args()

    home = Path(args.home).expanduser() if args.home else Path.home()
    now = args.now if args.now is not None else int(time.time())

    result = install(vault=args.vault, home=home, now=now)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
