# productivity plugin

Local-first task capture, session hygiene, end-of-day, and agent-operations workflows for Claude Code and Codex.

**Companion post:** [An operating loop for AI-assisted work](https://adzuci.github.io/claude-plugins/productivity.html)

## Skills

### `/productivity:productivity-setup`

Installs managed local copies of the portable core skills for every detected Claude Code and Codex client. After confirmation, it creates a Friday AI Coach schedule using the caller's native scheduler.

### `/productivity:ai-coach`

Reviews recent curated AI-work session notes for repeated friction, missed reusable workflows, and approval-safe memory candidates. Weekly mode writes a concise report to the user's Obsidian vault without changing durable memory.

### `/productivity:todo`

Captures one or more durable action items in an Obsidian Kanban backlog. It asks a concise question only when the task is materially ambiguous, preserves links and proper nouns, supports explicit urgent items, and writes idempotently to `backlog.md` under `## Inbox`.

### `/productivity:wrapup`

Checks for loose ends before clearing context — uncommitted changes, unpushed commits, open PRs, incomplete tasks, running background jobs. Tells you it's safe to `/clear` or lists what to resolve first.

### `/productivity:daily-wrapup`

End-of-day operating loop. Reviews yesterday's goals, summarizes what you accomplished today, previews tomorrow's calendar, optionally checks your on-call schedule, surfaces outstanding requests, and helps you commit goals for tomorrow. Writes goal commits to your Obsidian vault session note (works with the `memory` plugin).

Use `/productivity:todo` for immediate capture, `/productivity:daily-wrapup` for daily reflection and next-day planning, and `/productivity:wrapup` to check whether an individual AI/repo session is safe to clear.

### `/productivity:budgetclaw-setup`

Installs [budgetclaw](https://github.com/RoninForge/budgetclaw) in monitor-only mode on macOS with local Notification Center alerts. Sets a daily spend cap and fires a debounced popup when you breach it — no external services.

### `/productivity:create-agent`

Guided interview that turns a job description into a ready-to-use Claude Code skill. Answer a few questions about the agent's purpose, audience, tools, and vault access — the skill writes a `SKILL.md` in `.claude/skills/<name>/` and optionally registers the agent in your Obsidian vault under `agents/<name>.md`.

### `/productivity:agent-ops-setup`

Initializes private local tracking for scheduled agents. It references explicitly supplied or safely discovered schedule definitions without copying their contents, creates an append-only JSONL run ledger, and establishes an Obsidian-compatible Markdown summary location. It does not install background collection.

### `/productivity:agent-ops-report`

Builds an on-demand operational report from agent run ledgers and optional Claude or Codex JSONL/session artifacts. It reports status, duration, measured tokens, source coverage, and explicit data gaps without emitting prompt content, response content, or absolute session paths.

## Install

```
claude plugin marketplace add adzuci/claude-plugins
claude plugin install productivity@adzuci-plugins
```
