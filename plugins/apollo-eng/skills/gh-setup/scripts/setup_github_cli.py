#!/usr/bin/env python3
"""Inspect and optionally set up git + GitHub CLI for PR workflows."""

import argparse
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, check=False):
    completed = subprocess.run(
        cmd,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def first_line(text):
    return text.splitlines()[0] if text else ""


def git_config(key):
    code, out, _ = run(["git", "config", "--global", "--get", key])
    return out if code == 0 else ""


def git_remotes():
    if not shutil.which("git"):
        return []
    code, out, _ = run(["git", "remote", "-v"])
    if code != 0:
        return []
    remotes = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            remotes.append((parts[0], parts[1]))
    return remotes


def https_to_ssh(url):
    match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        return ""
    owner, repo = match.groups()
    return "git@github.com:%s/%s.git" % (owner, repo)


def ssh_public_keys():
    ssh_dir = Path.home() / ".ssh"
    if not ssh_dir.is_dir():
        return []
    return sorted(str(path) for path in ssh_dir.glob("*.pub"))


def install_gh():
    if shutil.which("gh"):
        return "gh already installed"
    if platform.system() == "Darwin" and shutil.which("brew"):
        code, out, err = run(["brew", "install", "gh"])
        if code == 0:
            return "installed gh with Homebrew"
        raise RuntimeError(err or out or "brew install gh failed")
    return "manual install required; see references/git-github-auth.md"


def set_git_config_if_needed(key, value):
    if git_config(key) == value:
        return False, "%s already %s" % (key, value)
    run(["git", "config", "--global", key, value], check=True)
    return True, "set %s" % key


def configure_git(args):
    actions = []
    if args.name:
        actions.append(set_git_config_if_needed("user.name", args.name))
    if args.email:
        actions.append(set_git_config_if_needed("user.email", args.email))
    if args.default_branch:
        actions.append(set_git_config_if_needed("init.defaultBranch", args.default_branch))
    if args.pull_rebase:
        actions.append(set_git_config_if_needed("pull.rebase", "true"))
    return actions


def collect_state():
    gh_path = shutil.which("gh") or ""
    git_path = shutil.which("git") or ""
    gh_status_code, gh_status_out, gh_status_err = (1, "", "gh not installed")
    gh_version = ""
    if gh_path:
        _, version_out, _ = run(["gh", "--version"])
        gh_version = first_line(version_out)
        gh_status_code, gh_status_out, gh_status_err = run(["gh", "auth", "status"])

    remotes = git_remotes()
    https_remotes = []
    for name, url in remotes:
        ssh_url = https_to_ssh(url)
        if ssh_url:
            https_remotes.append((name, url, ssh_url))

    return {
        "git_path": git_path,
        "gh_path": gh_path,
        "gh_version": gh_version,
        "gh_auth_ok": gh_status_code == 0,
        "gh_auth_detail": gh_status_out or gh_status_err,
        "user_name": git_config("user.name") if git_path else "",
        "user_email": git_config("user.email") if git_path else "",
        "default_branch": git_config("init.defaultBranch") if git_path else "",
        "pull_rebase": git_config("pull.rebase") if git_path else "",
        "ssh_keys": ssh_public_keys(),
        "https_remotes": https_remotes,
    }


def render_report(state):
    lines = []
    lines.append("GitHub CLI setup check")
    lines.append("")
    lines.append("Installed tools:")
    lines.append("- git: %s" % (state["git_path"] or "missing"))
    lines.append("- gh: %s" % (state["gh_version"] or "missing"))
    lines.append("")
    lines.append("Git config:")
    lines.append("- user.name: %s" % (state["user_name"] or "missing"))
    lines.append("- user.email: %s" % (state["user_email"] or "missing"))
    lines.append("- init.defaultBranch: %s" % (state["default_branch"] or "missing; recommend main"))
    if state["pull_rebase"]:
        lines.append("- pull.rebase: %s" % state["pull_rebase"])
    lines.append("")
    lines.append("GitHub auth:")
    if state["gh_auth_ok"]:
        lines.append("- gh auth status: authenticated")
    else:
        lines.append("- gh auth status: not ready")
        lines.append("- recommended: gh auth login --git-protocol ssh --web")
    lines.append("")
    lines.append("SSH:")
    if state["ssh_keys"]:
        lines.append("- public keys found: %s" % ", ".join(state["ssh_keys"]))
        lines.append("- add a key if needed: gh ssh-key add ~/.ssh/id_ed25519.pub --title \"$(hostname)-$(date +%Y-%m-%d)\"")
    else:
        lines.append("- no public SSH key found")
        email = state["user_email"] or "user@apollo.io"
        lines.append("- create one: ssh-keygen -t ed25519 -C \"%s\"" % email)
    lines.append("")
    lines.append("Remotes:")
    if state["https_remotes"]:
        for name, url, ssh_url in state["https_remotes"]:
            lines.append("- %s uses HTTPS: %s" % (name, url))
            lines.append("  convert: git remote set-url %s %s" % (name, ssh_url))
    else:
        lines.append("- no GitHub HTTPS remotes detected")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Inspect current state and print recommendations")
    parser.add_argument("--install-gh", action="store_true", help="Install gh when possible")
    parser.add_argument("--configure-git", action="store_true", help="Apply supplied global git config values")
    parser.add_argument("--name", help="Value for git config --global user.name")
    parser.add_argument("--email", help="Value for git config --global user.email")
    parser.add_argument("--default-branch", default="main", help="Value for init.defaultBranch")
    parser.add_argument("--pull-rebase", action="store_true", help="Set pull.rebase true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if not any([args.check, args.install_gh, args.configure_git]):
        args.check = True

    if args.install_gh:
        print(install_gh())

    if args.configure_git:
        if not shutil.which("git"):
            raise RuntimeError("git is not installed")
        actions = configure_git(args)
        changed = [message for did_change, message in actions if did_change]
        unchanged = [message for did_change, message in actions if not did_change]
        if changed:
            print("configured git: %s" % ", ".join(changed))
        elif unchanged:
            print("git config already up to date: %s" % ", ".join(unchanged))
        else:
            print("no git config changes requested")

    print(render_report(collect_state()))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        raise SystemExit(1)
