"""
scaffold_vault.py — Create and initialize a git-backed Obsidian vault.

Usage:
    python scaffold_vault.py --name NAME --parent PARENT [--remote URL]

Computes <parent>/<name>-vault.  If the directory exists and is non-empty,
prints an error JSON and exits nonzero (caller asks the user).  Otherwise
copies templates/vault/ into it, runs git init, optionally adds a remote,
and creates an initial commit.  Does NOT auto-push.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list, cwd: Path | None = None) -> tuple[bool, str, str]:
    """Run a command; return (success, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", str(e)


def scaffold(name: str, parent: str, remote: str | None = None) -> dict:
    vault_path = Path(parent).expanduser() / f"{name}-vault"

    # Guard: existing non-empty dir
    if vault_path.exists():
        try:
            children = list(vault_path.iterdir())
        except Exception:
            children = []
        if children:
            return {
                "ok": False,
                "error": f"Vault directory '{vault_path}' already exists and is not empty. "
                         "Please choose a different name or parent, or remove the existing directory.",
                "vault": str(vault_path),
            }

    # Locate templates/vault/ relative to this script
    skill_dir = Path(__file__).resolve().parent.parent
    templates_vault = skill_dir / "templates" / "vault"

    if not templates_vault.is_dir():
        return {
            "ok": False,
            "error": f"Template directory not found: {templates_vault}",
            "vault": str(vault_path),
        }

    # Copy template tree
    try:
        shutil.copytree(str(templates_vault), str(vault_path), dirs_exist_ok=True)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to copy templates: {e}",
            "vault": str(vault_path),
        }

    # git init
    ok, out, err = _run(["git", "init"], cwd=vault_path)
    if not ok:
        return {
            "ok": False,
            "error": f"git init failed: {err}",
            "vault": str(vault_path),
        }

    # Optional remote
    if remote:
        ok, out, err = _run(["git", "remote", "add", "origin", remote], cwd=vault_path)
        if not ok:
            # Non-fatal — report but continue
            pass

    # Initial commit
    _run(["git", "add", "--all"], cwd=vault_path)
    ok, out, err = _run(
        ["git", "commit", "--allow-empty", "-m", "chore: initial vault scaffold"],
        cwd=vault_path,
    )
    commit_ok = ok

    return {
        "ok": True,
        "vault": str(vault_path),
        "remote": remote or None,
        "initial_commit": commit_ok,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a git-backed Obsidian vault.")
    parser.add_argument("--name", required=True, help="Vault name (directory will be <name>-vault).")
    parser.add_argument("--parent", required=True, help="Parent directory for the vault.")
    parser.add_argument("--remote", default=None, help="Optional git remote URL.")
    args = parser.parse_args()

    result = scaffold(name=args.name, parent=args.parent, remote=args.remote)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
