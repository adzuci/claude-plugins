---
name: gh-setup
description: Install gh and set up git for GitHub PR workflows. Activate when the user asks for gh setup, git setup, GitHub CLI auth, or help preparing to push PRs.
allowed-tools: Bash Read
---

# GitHub CLI Setup

Set up a developer machine for GitHub PR work with `git`, the `gh` CLI, SSH-based Git remotes, and `gh auth login`.

Use the bundled helper first:

```bash
SKILL_DIR="$(find ~/.claude/plugins "$PWD" -maxdepth 8 -path '*/gh-setup/scripts/setup_github_cli.py' -exec dirname {} \; 2>/dev/null | head -1 | xargs dirname)"
python3 "$SKILL_DIR/scripts/setup_github_cli.py" --check
```

Read `references/git-github-auth.md` when the user needs install commands, SSH setup, remote conversion, or auth troubleshooting.

## Workflow

1. Run the helper with `--check` and summarize the current state.

1. Prefer SSH for Git remotes. If the current repo uses HTTPS, show the SSH remote command from the helper and ask before changing it.

1. Prefer `gh auth login --git-protocol ssh --web` for GitHub auth used by PR pushes and `gh pr create`.

1. If `git config --global user.name` or `user.email` is missing, ask for the missing value before configuring it.

1. If the user explicitly asked for setup end-to-end, run the helper with the needed flags:

   ```bash
   python3 "$SKILL_DIR/scripts/setup_github_cli.py" --install-gh --configure-git --name "Full Name" --email "user@apollo.io"
   ```

1. After changes, rerun `--check` and report only what changed plus any remaining manual action, especially browser auth or adding an SSH key to GitHub.

## Guardrails

- Do not install packages or change global git config unless the user explicitly asked for setup or approved the plan.
- Do not create or overwrite SSH keys automatically; give the `ssh-keygen` command and let the user run it.
- Do not put tokens in git config, shell profiles, or files.
- If Homebrew is unavailable, give the OS-specific install path from the reference instead of improvising.
