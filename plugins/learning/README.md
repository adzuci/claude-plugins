# learning

A weekly engineering self-retro that reflects your own work back to you as a small, ranked learning plan. The idea is [Harshit Pandey's](https://www.linkedin.com/in/harshit-pandey-84779114a/): keep the retro focused on the work you actually did, and turn it into concrete next steps.

## Skills

| Skill | Purpose |
| --- | --- |
| `/learning:self-retro` | Generate the weekly retro. Auto-detects its environment. |
| `/learning:learning-setup` | Schedule the weekly run and choose where reports are stored. |

## Two modes, auto-detected

`self-retro` picks its data source from the environment:

- **Local mode** — when Claude Code session files (`~/.claude/projects/`) are present, the retro is built from your own conversation transcripts via `parse_sessions.py`. Richest signal; runs offline.
- **Signals mode** — in a cloud or web routine with no local sessions, the retro is built from shipped output: GitHub PRs (authored + reviewed), Jira touches, and optionally Glean documents. Pairs with an LLM wiki (a git-backed Obsidian vault) so each scheduled run leaves a durable, reviewable file. See `skills/self-retro/references/web-routine.md` for the paste-ready routine prompt.

If neither local sessions nor engineering signals are reachable, the skill says it needs data rather than inventing a report. Force a mode with `--local` or `--signals`.

## Scheduling

`/learning:learning-setup` wires the weekly run using the scheduler native to your client (Claude Code `/schedule`, a Codex automation, or a Cowork/web routine), stores each report under `<vault>/reports/self-retro/`, and maintains a running meta index of past retros and whether their top item was acted on. It is confirmation-gated and never installs cron or launchd without an explicit request.

## Design guardrails

- Reflective, never punitive: the reports never use "gap / missed / failed / lacking", and every claim cites specific session or PR evidence.
- Report-only: `self-retro` generates and (on approval) saves; it does not change tickets, memory, or code.
- Honest about empty weeks and unreachable signals — it says so in one line rather than padding.
- No secret values in reports; PR numbers, issue keys, and repo names are fine.

## Credit

The self-retro concept and the "focus on where you actually spend your time" framing come from [Harshit Pandey](https://www.linkedin.com/in/harshit-pandey-84779114a/).
