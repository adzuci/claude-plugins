# Memory

`memory` is a portable skill for setting up a local, git-backed Obsidian vault that captures useful AI working-session notes instead of letting them disappear into chat history.

Current support note: the setup flow has been tested on macOS. Linux and Windows compatibility reports and PRs are welcome.

It includes:

- `memory-setup` skill instructions for a gated, user-approved setup flow
- Python scripts for vault scaffolding, Obsidian plugin installation, Claude Code hook registration, and optional Codex/Antigravity imports
- Templates for the generated vault and the managed `CLAUDE.md` memory block
- Tests for the idempotent setup helpers

## Invoke

```text
/memory:memory-setup
```

With encryption for sensitive directories (git-crypt):

```text
/memory:memory-setup crypt
```

The `crypt` argument works on a fresh vault, migrates an existing vault in
place, and unlocks a clone on a second machine. The exported key goes into
your password manager (1Password `op` CLI supported); see
`skills/memory-setup/references/encryption.md` for the full model.

## Install

From Codex:

```bash
codex plugin marketplace add adzuci/claude-plugins
codex plugin add memory@adzuci-plugins
```

From Claude Code:

```bash
claude plugin marketplace add adzuci/claude-plugins
claude plugin install memory@adzuci-plugins
```

## What It Installs

The default Claude Code path sets up:

- A local Obsidian vault under a user-selected parent directory
- `claudian` and `obsidian-git` as Obsidian community plugins
- A `SessionEnd` hook in `~/.claude/settings.json`
- A managed memory block in `~/.claude/CLAUDE.md`
- Optional scheduled git sync: obsidian-git auto commit/pull while Obsidian is open, plus a launchd agent (macOS) that pulls/commits/pushes headlessly so multiple machines stay converged
- Optional git-crypt encryption of sensitive directories (`crypt` argument)

Codex and Antigravity compatibility paths append summaries into the same vault without writing to `~/.claude` unless the user explicitly asks for shared Claude setup.

## Safety Model

The skill is deliberately gated. It explains the cost and trade-offs first, runs read-only preflight checks, asks for setup inputs, and requires approval before write steps.

Re-running is designed to be safe:

- Hook registration is idempotent
- `CLAUDE.md` updates replace one managed block
- Existing vault directories are not overwritten
- Session importers track already-ingested sessions
- git-crypt setup is dry-run by default, never exports the key inside the vault, and never prints key material
- Scheduled sync skips locked git-crypt checkouts and in-progress rebases, and `--uninstall` removes everything it installed

## History

An early version of this workflow used `claude-mem` for about a week in April
2026. It was replaced by the explicit `SessionEnd` capture flow described here,
which keeps the generated notes and write path visible. The setup skill retains
dry-run detection and cleanup support so existing `claude-mem` users can migrate
without silently changing their configuration.
