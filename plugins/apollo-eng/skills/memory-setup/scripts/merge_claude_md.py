"""
merge_claude_md.py — Upsert the memory-setup managed block into ~/.claude/CLAUDE.md.

Usage:
    python merge_claude_md.py --vault VAULTPATH [--home HOME] [--block-file PATH]
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

from lib import render_template, upsert_claude_md

_SKILL_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_BLOCK_FILE = _SKILL_DIR / "templates" / "claude-md-block.md"

BEGIN_MARKER = "<!-- BEGIN memory-setup (apollo-eng) -->"
END_MARKER = "<!-- END memory-setup (apollo-eng) -->"


def resolve_block_file(path: str | None) -> Path:
    return Path(path).expanduser() if path else _DEFAULT_BLOCK_FILE


def merge(
    vault: str,
    home: Path,
    block_file: Path,
    now: int,
) -> dict:
    claude_md_path = home / ".claude" / "CLAUDE.md"

    # Read block template
    try:
        block_text = block_file.read_text()
    except OSError as e:
        return {"ok": False, "error": f"Failed to read block file {block_file}: {e}"}

    try:
        block = render_template(block_text, {"VAULT": vault})
    except ValueError as e:
        return {"ok": False, "error": f"Template rendering failed: {e}"}

    # Read existing CLAUDE.md (missing → "")
    existing = ""
    if claude_md_path.exists():
        try:
            existing = claude_md_path.read_text()
        except OSError as e:
            return {"ok": False, "error": f"Failed to read {claude_md_path}: {e}"}

    # Upsert
    new_content = upsert_claude_md(existing, block, BEGIN_MARKER, END_MARKER)

    # Backup before writing
    bak = None
    if claude_md_path.exists():
        bak_path = claude_md_path.parent / f"CLAUDE.md.bak-{now}"
        try:
            shutil.copy2(str(claude_md_path), str(bak_path))
        except OSError as e:
            return {"ok": False, "error": f"Failed to back up {claude_md_path}: {e}"}
        bak = str(bak_path)

    try:
        claude_md_path.parent.mkdir(parents=True, exist_ok=True)
        claude_md_path.write_text(new_content)
    except OSError as e:
        return {"ok": False, "error": f"Failed to write {claude_md_path}: {e}"}

    return {
        "ok": True,
        "claude_md": str(claude_md_path),
        "backup": bak,
        "vault": vault,
        "changed": new_content != existing,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge memory-setup block into CLAUDE.md.")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault.")
    parser.add_argument("--home", default=None, help="Override home directory.")
    parser.add_argument("--block-file", default=None,
                        help="Path to the managed block template (default: templates/claude-md-block.md).")
    parser.add_argument("--now", type=int, default=None,
                        help="Epoch timestamp for backups (default: current time).")
    args = parser.parse_args()

    home = Path(args.home).expanduser() if args.home else Path.home()
    block_file = resolve_block_file(args.block_file)
    now = args.now if args.now is not None else int(time.time())

    result = merge(vault=args.vault, home=home, block_file=block_file, now=now)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
