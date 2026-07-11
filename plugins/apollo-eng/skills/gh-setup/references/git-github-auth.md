# Git And GitHub Auth Reference

## Preferred Path

Use SSH for Git remotes and `gh auth login` for GitHub API operations:

```bash
gh auth login --git-protocol ssh --web
```

This keeps `git push`, `gh pr create`, and other GitHub CLI calls on the same auth path without storing personal access tokens in repo config.

## Install `gh`

macOS with Homebrew:

```bash
brew install gh
```

Ubuntu or Debian:

```bash
type -p curl >/dev/null || sudo apt install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
sudo apt update
sudo apt install gh -y
```

Other platforms: <https://github.com/cli/cli#installation>

## Global Git Basics

```bash
git config --global user.name "Full Name"
git config --global user.email "user@apollo.io"
git config --global init.defaultBranch main
```

Optional preference if the user wants rebase-on-pull:

```bash
git config --global pull.rebase true
```

## SSH Key Setup

Check for an existing public key:

```bash
ls ~/.ssh/*.pub
```

Create a new key only if needed:

```bash
ssh-keygen -t ed25519 -C "user@apollo.io"
```

Add it to GitHub with `gh` after login:

```bash
gh ssh-key add ~/.ssh/id_ed25519.pub --title "$(hostname)-$(date +%Y-%m-%d)"
```

Test SSH:

```bash
ssh -T git@github.com
```

GitHub may return a message saying shell access is not provided; that is fine if authentication succeeded.

## Convert A Repo Remote To SSH

Inspect remotes:

```bash
git remote -v
```

Convert a GitHub HTTPS origin:

```bash
git remote set-url origin git@github.com:OWNER/REPO.git
```

Verify:

```bash
git remote -v
git ls-remote origin HEAD
```

## Troubleshooting

- `gh auth status` fails: run `gh auth login --git-protocol ssh --web`.
- Push prompts for username/password: convert the remote from HTTPS to SSH.
- SSH fails with no key: create or locate a key, add it with `gh ssh-key add`, then retry `ssh -T git@github.com`.
- Wrong GitHub account: run `gh auth status`, then `gh auth logout` and log in again with the correct account.
