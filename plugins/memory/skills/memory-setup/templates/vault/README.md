# Memory Vault

This repository is a local-first memory layer for AI-assisted work. Obsidian is
the human-readable interface; Markdown and git are the durable source of truth.

Start in [`index.md`](index.md). It maps the folders and keeps both humans and
AI assistants from scanning the whole vault.

## Finish setup in Obsidian

1. Open Obsidian.
2. Choose **Open folder as vault** and select this repository's root folder.
3. When prompted, trust the vault and enable the installed community plugins:
   `realclaudian` and `obsidian-git`.
4. Confirm the Git plugin is configured for automatic commit and pull every
   15 minutes.

The setup skill launches Obsidian on macOS, but Obsidian requires the first
folder-as-vault selection in its UI.

## How capture works

- Claude Code's `SessionEnd` hook appends metadata and a short summary to
  `sessions/YYYY-MM-DD.md`.
- Codex and Antigravity can append compatible entries through their importers.
- Raw transcripts stay outside the normal vault-reading path.
- Future sessions begin at `index.md` and read only relevant notes.

## Folder map

| Path | Purpose |
| --- | --- |
| `index.md` | Token-efficient navigation hub |
| `sessions/` | Daily AI-session logs |
| `memory/` | Durable facts, project context, and references |
| `agents/` | Agent job briefs, tools, and guardrails |
| `raw/` | Inbox for unprocessed captures |
| `runbooks/` | Repeatable procedures and drift notes |
| `handoffs/` | Open loops and active-thread handoffs |
| `recipes/` | Short symptom-to-command references |
| `wiki/` | Topic-organized knowledge |
| `friction-log.md` | Repetitive work worth automating |

## Git and privacy

The default work setup uses a private repository in the `apolloio` GitHub
organization. Personal or sensitive non-company notes should use the personal
private-repository option instead. Never make this repository public without
reviewing every file and its git history.

With a remote configured, setup enables two complementary 15-minute sync paths:
the Obsidian Git plugin while Obsidian is open and a headless scheduler for
session-hook writes. Check recent sync activity with:

```bash
git status
git log --oneline -5
git remote -v
```

Optional `git-crypt` support protects configured sensitive directories in the
remote repository. It does not rewrite plaintext from older commits unless you
explicitly migrate history.

## Recovery

- Git history is the rollback path for Markdown changes.
- Setup backs up managed settings before editing them.
- Re-running memory setup is designed to be idempotent.
- To remove scheduled sync, rerun `install_sync.py --uninstall` from the
  memory-setup skill directory.

Record setup issues in `setup-log.md` so the next machine or maintainer can see
what happened.
