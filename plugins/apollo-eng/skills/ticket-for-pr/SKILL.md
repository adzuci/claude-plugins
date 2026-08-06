---
name: ticket-for-pr
description: Create a Jira ticket for an existing GitHub PR, prefix the PR title with the ticket key, and link the ticket in the PR description. The ticket states the problem that existed before the PR, not the fix.
argument-hint: <PR number or URL>
disable-model-invocation: true
---

# Ticket for PR

Given a GitHub PR (URL or number), create a Jira ticket describing the problem the PR solves, retitle the PR with the ticket key as a prefix, and link the ticket in the PR body.

## Tooling: prefer CLI, fall back to MCP

The workflow below is written against the `gh` and `jira` CLIs — prefer them whenever installed and authenticated (`command -v jira && jira me`, `gh auth status`). They're faster, scriptable, and their quirks are documented here.

If a CLI is missing or unauthenticated but a matching MCP server is connected (Atlassian/Jira MCP for the ticket side, GitHub MCP for the PR side), fall back to MCP **for that side only** — the two sides are independent, so e.g. `gh` + Jira-MCP is a fine combination. When using MCP, read [references/mcp-fallback.md](references/mcp-fallback.md) for the capability mapping and caveats. If neither a CLI nor an MCP server covers a required side, tell the user what's missing instead of improvising.

**Before running any `jira` CLI command, read [references/jira-cli.md](references/jira-cli.md).** The go-jira CLI has silent-failure quirks (immutable issue type, `create` vs `edit` flag differences, markdown body mangling) that cost a delete-and-recreate round trip if hit cold. These gotchas are CLI-specific — MCP has its own, covered in its own reference.

## Configuration

Two mappings drive this skill, both of which live in the user's global or project `CLAUDE.md` (look for a Jira section):

- **repo → Jira project** (which project key to create tickets in)
- **GitHub login → Jira email** (for assigning the ticket)

If a needed mapping is missing, ask the user rather than guessing — a ticket in the wrong project or assigned to the wrong person creates cleanup work and notification noise. After the user answers, suggest they add the mapping to `CLAUDE.md` so future runs don't have to ask.

## Workflow

### 1. Read the PR

```
gh pr view <n> --repo <org>/<repo> --json title,body,files,commits,author,state,mergedAt
```

Get `org/repo` from `git remote -v` if not given. Use the body and diff to understand *what problem existed before this PR* — that framing drives the ticket description. The `/describe-changes` skill can help if the PR body is thin.

### 2. Handle an existing ticket prefix

If the PR title already carries a **real** ticket prefix, stop and ask the user (via `AskUserQuestion`) which they want, then follow their choice:

- **Follow-up ticket** — create a new ticket referencing the existing one as a follow-up/regression, and *replace* the title prefix with the new key.
- **New ticket, keep both** — create a new ticket, keep the existing prefix in the title, link the new ticket in the body.
- **Update the existing ticket** — no new ticket; amend the existing ticket's description/status instead.

Never silently reuse or overwrite a real ticket key — the existing key may be tracked in sprints, dashboards, or release notes.

A `NOTICKET` placeholder (`[NOTICKET] `, `NOTICKET: `, `NOTICKET `) is **not** a real prefix — strip and replace it without asking.

### 3. Draft the description as pre-PR framing

Write the description as it would have read *before* the fix existed: the gap, bug, or missing behavior. The problem statement only — no solution, no "we changed X to Y", no mention of the new functions. Mirror the PR's problem/motivation section, phrased as open work to be done. Keep the summary short and specific.

**Example:**

- PR body says: *"Rewrote the retry logic in `sync_worker` to use exponential backoff; added jitter to avoid thundering herd."*
- Ticket says: *"`sync_worker` retries failed syncs at a fixed interval, so simultaneous failures across workers retry in lockstep and overload the upstream API."*

### 4. Create the ticket

Pick the type before creating — **type cannot be changed afterward** (see the reference file). Default is `Task`; use `Bug` when the PR clearly fixes a defect, including defects introduced by an earlier ticket.

```
jira issue create -t <Task|Bug> -s "<summary>" -p <PROJECT> \
  --template <(printf '%s' "<markdown body>") -a "<author email>" --no-input
```

Assign to the **PR author**, not whoever asked for the ticket, unless the user says otherwise — the author owns the change and should own its record. Capture the returned key and browse URL (e.g. `.../browse/TICKET-474` → `TICKET-474`).

### 5. Retitle the PR

Take the current title, strip a leading `NOTICKET` prefix and any prefix the user asked to replace in step 2, then prepend the new key. Check the result doesn't end up double-prefixed.

```
gh pr edit <n> --repo <org>/<repo> --title "[TICKET-NNN] <cleaned original title>"
```

### 6. Link the ticket in the PR body

A title prefix alone isn't clickable — the body must carry a markdown link to the browse URL. Fetch the current body (`gh pr view <n> --json body -q .body`), then `gh pr edit <n> --body "..."`:

- If the body has a natural spot (a Problem/context section that mentions the work), link it inline there.
- Otherwise prepend a one-line reference: `Ticket: [TICKET-NNN](<browse url>)`.
- Never leave a bare, unlinked ticket key in the body — this applies to Jira descriptions too (see reference file for Jira-side link syntax).

### 7. Set ticket status from PR state

Using `state`/`mergedAt` from step 1:

- **Merged** — the work already shipped, close it: `jira issue move TICKET-NNN "Done"`. If the project gates the transition on required fields, set them first (project-specific requirements live in `CLAUDE.md`).
- **Open (incl. draft)** — leave it active: `jira issue move TICKET-NNN "In Progress"`.
- **Closed unmerged** — ambiguous (abandoned? superseded?), ask the user instead of guessing.

### 8. Report

Give the user the ticket URL and the new PR title, and note the ticket status that was set.
