"""
check_env.py — Read-only environment detection for memory-setup onboarding.

Prints a JSON object to stdout (and optionally writes it to --out PATH).
Never raises on missing tools — reports False for any detection that fails.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


def _run(cmd: list, timeout: int = 10) -> tuple[bool, str]:
    """Run a command; return (success, stdout). Never raises."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            text=True,
        )
        return r.returncode == 0, r.stdout
    except Exception:
        return False, ""


def detect_macos() -> bool:
    try:
        return platform.system() == "Darwin"
    except Exception:
        return False


def detect_brew() -> bool:
    return shutil.which("brew") is not None


def detect_obsidian(is_mac: bool) -> bool:
    if is_mac and Path("/Applications/Obsidian.app").exists():
        return True
    ok, out = _run(["brew", "list", "--cask"])
    if ok and "obsidian" in out.lower().split():
        return True
    return False


def detect_which(name: str) -> bool:
    return shutil.which(name) is not None


def detect_path(path_str: str, kind: str = "any") -> bool:
    p = Path(path_str).expanduser()
    if kind == "dir":
        return p.is_dir()
    if kind == "file":
        return p.is_file()
    return p.exists()


def detect_vault_candidate(path_str: str) -> dict | bool:
    """Return a dict with vault state when path_str is given, else False."""
    if not path_str:
        return False
    p = Path(path_str).expanduser()
    if not p.exists():
        return {"exists": False, "non_empty": False, "vault_has_git": False}
    non_empty = p.is_dir() and any(True for _ in p.iterdir())
    vault_has_git = (p / ".git").exists()
    return {"exists": True, "non_empty": non_empty, "vault_has_git": vault_has_git}


def build_report(vault_candidate: str = "") -> dict:
    is_mac = detect_macos()
    brew = detect_brew()
    obsidian = detect_obsidian(is_mac)
    git = detect_which("git")
    node = detect_which("node")
    npm = detect_which("npm")
    claude_on_path = detect_which("claude")
    codex_on_path = detect_which("codex")
    jq = detect_which("jq")
    gh = detect_which("gh")
    brew_info_writable = os.access("/usr/local/share/info", os.W_OK)
    vault_info = detect_vault_candidate(vault_candidate) if vault_candidate else None

    report: dict = {
        "macos": is_mac,
        "brew": brew,
        "brew_info_writable": brew_info_writable,
        "obsidian": obsidian,
        "git": git,
        "gh": gh,
        "node": node,
        "npm": npm,
        "claude": claude_on_path,
        "codex": codex_on_path,
        "jq": jq,
        "git_crypt": detect_which("git-crypt"),
        "op": detect_which("op"),
        "codex_sessions": detect_path("~/.codex/sessions", "dir"),
        "codex_session_index": detect_path("~/.codex/session_index.jsonl", "file"),
        "codex_config": detect_path("~/.codex/config.toml", "file"),
        "antigravity_brain": detect_path("~/.gemini/antigravity/brain", "dir"),
        "antigravity_hooks": detect_path("~/.gemini/config/hooks.json", "file"),
        "antigravity_skills": detect_path("~/.gemini/config/skills", "dir"),
    }
    if vault_candidate:
        report["vault_candidate"] = vault_candidate
        if isinstance(vault_info, dict):
            report["vault_exists"] = vault_info["non_empty"]
            report["vault_has_git"] = vault_info["vault_has_git"]
        else:
            report["vault_exists"] = vault_info

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect environment for memory-setup.")
    parser.add_argument("--out", metavar="PATH", help="Write JSON to this file in addition to stdout.")
    parser.add_argument("--vault-candidate", metavar="PATH", default="",
                        help="Path to check for an existing vault.")
    args = parser.parse_args()

    report = build_report(vault_candidate=args.vault_candidate)
    output = json.dumps(report, indent=2)
    print(output)

    if args.out:
        Path(args.out).write_text(output + "\n")


if __name__ == "__main__":
    main()
