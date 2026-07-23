"""
install_sync.py — Enable scheduled git sync for the vault.

Two complementary mechanisms:
  1. obsidian-git plugin settings (data.json) — auto commit/pull while
     Obsidian is open.  Per-machine file, already gitignored by the vault.
  2. A launchd agent (macOS) running vault-sync.sh on an interval — covers
     headless writes (e.g. the SessionEnd hook) when Obsidian is closed.
     On non-macOS platforms a crontab line is suggested instead.

Usage:
    python install_sync.py --vault VAULTPATH [--interval SECONDS]
        [--home HOME] [--no-load] [--uninstall]
"""
from __future__ import annotations

import argparse
import getpass
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from lib import render_template

_SKILL_DIR = Path(__file__).resolve().parent.parent
_TEMPLATE_PATH = _SKILL_DIR / "templates" / "vault-sync.sh.tmpl"

# obsidian-git settings we enforce; every other existing key is preserved.
OBSIDIAN_GIT_SYNC_SETTINGS = {
    "autoSaveInterval": 10,       # minutes: auto commit-and-sync
    "autoPullInterval": 10,       # minutes
    "autoPushInterval": 0,        # push rides on the commit-and-sync
    "pullBeforePush": True,
    "disablePush": False,
    "commitMessage": "vault backup: {{date}}",
}


def render_launchd_plist(label: str, script: str, interval: int, log: str) -> str:
    """Return launchd plist XML for the sync agent."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{script}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log}</string>
    <key>StandardErrorPath</key>
    <string>{log}</string>
</dict>
</plist>
"""


def merge_obsidian_git_settings(existing: dict, desired: dict) -> dict:
    """Return existing settings with *desired* sync keys enforced on top."""
    merged = dict(existing)
    merged.update(desired)
    return merged


def _launchctl(args: list) -> None:
    try:
        subprocess.run(["launchctl"] + args, capture_output=True, text=True)
    except Exception:
        pass  # best-effort; the plist on disk is the source of truth


def _write_obsidian_git_settings(vault: Path, now: int) -> dict:
    data_path = vault / ".obsidian" / "plugins" / "obsidian-git" / "data.json"
    existing: dict = {}
    backup = None
    if data_path.exists():
        try:
            existing = json.loads(data_path.read_text())
        except Exception:
            existing = {}
        backup = data_path.parent / f"data.json.bak-{now}"
        shutil.copy2(str(data_path), str(backup))
    data_path.parent.mkdir(parents=True, exist_ok=True)
    merged = merge_obsidian_git_settings(existing, OBSIDIAN_GIT_SYNC_SETTINGS)
    data_path.write_text(json.dumps(merged, indent=2) + "\n")
    return {"path": str(data_path), "backup": str(backup) if backup else None}


def run(
    vault: Path,
    home: Path,
    interval: int,
    uninstall: bool,
    load: bool,
    now: int,
    platform_name: "str | None" = None,
) -> dict:
    platform_name = platform_name or platform.system()
    label = f"com.{getpass.getuser()}.vault-sync"
    script_path = home / ".claude" / "hooks" / "vault-sync.sh"
    plist_path = home / "Library" / "LaunchAgents" / f"{label}.plist"
    log_path = home / ".claude" / "logs" / "vault-sync.log"

    if uninstall:
        removed = []
        if platform_name == "Darwin" and load:
            _launchctl(["unload", str(plist_path)])
        for p in (plist_path, script_path):
            if p.exists():
                p.unlink()
                removed.append(str(p))
        return {
            "ok": True,
            "uninstalled": True,
            "removed": removed,
            "note": "obsidian-git data.json left in place (restore its .bak "
                    "file manually if you want the old settings back).",
        }

    if not (vault / ".git").exists():
        return {"ok": False, "error": f"Not a git repository: {vault}"}

    result: dict = {"ok": True, "vault": str(vault), "interval": interval}

    # 1. obsidian-git settings
    result["obsidian_git"] = _write_obsidian_git_settings(vault, now)
    # These keys are re-enforced on every run (manual edits to them are
    # overwritten; everything else in data.json is preserved).
    result["enforced_settings"] = sorted(OBSIDIAN_GIT_SYNC_SETTINGS)

    # 2. Headless sync script
    import shlex
    rendered = render_template(
        _TEMPLATE_PATH.read_text(), {"VAULT_SHELL": shlex.quote(str(vault))}
    )
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(rendered)
    script_path.chmod(0o755)
    result["sync_script"] = str(script_path)

    if platform_name == "Darwin":
        log_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(
            render_launchd_plist(label, str(script_path), interval, str(log_path))
        )
        result["launchd_plist"] = str(plist_path)
        result["log"] = str(log_path)
        if load:
            _launchctl(["unload", str(plist_path)])  # idempotent reload
            _launchctl(["load", str(plist_path)])
            result["loaded"] = True
        result["rollback"] = "python3 scripts/install_sync.py --uninstall"
    else:
        minutes = max(1, interval // 60)
        result["cron_line"] = f"*/{minutes} * * * * /bin/bash {script_path}"
        result["note"] = (
            "launchd is macOS-only; add the cron_line above with `crontab -e` "
            "to schedule headless sync on this platform."
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Enable scheduled git sync for the vault.")
    parser.add_argument("--vault", default=None, help="Path to the vault git repo.")
    parser.add_argument("--interval", type=int, default=900,
                        help="Sync interval in seconds (default 900 = 15 min).")
    parser.add_argument("--home", default=None, help="Override home directory.")
    parser.add_argument("--no-load", action="store_true",
                        help="Write files but skip launchctl load/unload.")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove the launchd agent and sync script.")
    parser.add_argument("--now", type=int, default=None,
                        help="Epoch timestamp for backups (default: current time).")
    args = parser.parse_args()

    if not args.uninstall and not args.vault:
        parser.error("--vault is required unless --uninstall is given")

    home = Path(args.home).expanduser() if args.home else Path.home()
    vault = Path(args.vault).expanduser().resolve() if args.vault else Path(".")
    now = args.now if args.now is not None else int(time.time())

    result = run(vault=vault, home=home, interval=args.interval,
                 uninstall=args.uninstall, load=not args.no_load, now=now)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
