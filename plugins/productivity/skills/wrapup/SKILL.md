---
name: wrapup
description: End-of-session check for loose ends (uncommitted changes, unpushed commits, undeleted merged branches, open PRs, incomplete tasks) before clearing context. Invoke with /productivity:wrapup.
disable-model-invocation: true
allowed-tools: Bash, TaskList
---

# Wrap Up

Check whether the current session has any **loose ends** before the context is cleared.

> You cannot run `/clear` yourself — it is a client-only command. This skill ends by either
> listing what's unfinished, or telling the user it's safe to type `/clear` themselves.

## Step 1: Run the checks (read-only)

Run these from the current repo. They make no changes.

```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && {
  git status --porcelain                       # uncommitted / untracked changes
  echo "--- stashes ---"; git stash list
  echo "--- unpushed (current branch) ---"; git log --oneline @{u}..HEAD 2>/dev/null
  echo "--- local branches ahead of remote ---"; git branch -vv | grep -E '\[.*ahead' || true
}
```

If `gh` is available, surface open PRs you authored:

```bash
gh pr list --author @me --state open --json number,title,headRefName \
  --jq '.[] | "#\(.number) \(.title) [\(.headRefName)]"' 2>/dev/null || true
```

Then consider **session-level** loose ends from this conversation:

- Incomplete items in the task list (check it if you used one).
- Background tasks or monitors still running.
- A merged PR whose branch was never deleted, or a PR you opened that isn't merged yet.
- Anything the user asked for in this session that isn't finished.

## Step 2: Classify

A session has **loose ends** if any of these are true:

- `git status --porcelain` is non-empty (uncommitted/untracked changes).
- `git stash list` is non-empty.
- The current branch has unpushed commits.
- An open PR you authored is unmerged/unreviewed and the user expected it landed.
- An incomplete in-session task, a running background job, or an unaddressed request.

Artifacts the user already knows about and accepts (e.g. a throwaway scratch file) are
**not** loose ends — mention them once, but don't block on them.

## Step 3: Optional Obsidian note

If the user asks to save a wrap-up note, write a concise Markdown session note before
recommending clear.

Resolve the vault from an explicit path, `$VAULT`, `~/.config/adzuci-productivity/config.json`, then `~/obsidian-vault`:

```bash
VAULT="${VAULT:-$HOME/obsidian-vault}"
# path: $VAULT/sessions/YYYY-MM-DD - <short-title>.md
```

If that vault path does not exist or cannot be written, ask for the correct Obsidian vault
path instead of guessing. Include:

- Goal
- What changed / what was learned
- Decisions made
- Files, docs, PRs, or external systems touched
- Commands or validations run
- Open follow-ups

Do not include secrets, token values, or long raw command output.

## Step 4: Report

**If loose ends exist** — list each with a one-line suggested action, then end with:

> ⚠️ Not safe to clear — N loose end(s) above. Resolve them, then run `/productivity:wrapup` again.

**If clean** — end with exactly:

> ✅ No loose ends: working tree clean, nothing unpushed, no open obligations.
> Safe to reset — type `/clear` to start fresh.

You cannot issue `/clear` yourself; the user types it.

## Archive mode

Use archive mode only when the user explicitly asks to archive, e.g. `/productivity:wrapup archive`.

Archive mode rules:

1. Run the same checks above.
1. If there are big loose ends, do not archive.
1. If there are only minor known/accepted leftovers, mention them without blocking.
1. Save the Obsidian session note first.
1. Confirm the note path.
1. In Codex Desktop, archive the thread only after the note is saved.
1. In CLI or any client where archive is unavailable, say it is safe to type `/clear` instead.

Big loose ends: uncommitted work, unpushed commits, unexpected stashes, running background
jobs, open obligations the user expected completed, failed required validation, or any
unresolved question that changes whether the session is done.

## Guardrails

- Read-only. Never commit, push, stash, or delete branches to "tidy up" unless the user
  explicitly asks — surfacing a loose end is the job, not silently resolving it.
- If not inside a git repo, skip the git checks and report only session-level items.
