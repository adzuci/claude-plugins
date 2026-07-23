---
name: learning-setup
description: Schedule the weekly self-retro, choose where reports are stored, and (for cloud runs) print the paste-ready web-routine prompt. Invoke with /learning:learning-setup or /learning-setup.
disable-model-invocation: true
---

# Learning Setup

Set up the weekly `self-retro` on a schedule and decide where its reports land. Confirmation-gated: nothing is scheduled or written outside the current project without explicit approval.

## Usage

```text
/learning:learning-setup
/learning:learning-setup --vault ~/obsidian-vault --day friday --time 09:00
```

## 1. Resolve the environment and vault

Detect which environment the weekly run will use, the same way `self-retro` does:

- **Local sessions present** (`~/.claude/projects/` has recent `*.jsonl`) → the scheduled run will use **local mode**.
- **No local sessions, GitHub reachable** → the scheduled run will use **signals mode** (a cloud/web routine).

Resolve the vault (the LLM wiki where reports are stored) from an explicit `--vault`, `$VAULT`, the current directory when it is an Obsidian vault, `~/.config/adzuci-productivity/config.json`, then `~/obsidian-vault`. Ask for the path if none exists. The vault should be git-backed so each run leaves a durable, reviewable, pushable file.

Show one concise confirmation with: the detected mode, the vault path and report location (`<vault>/reports/self-retro/`), the schedule (default **Friday 09:00** local time), and the caller-native scheduler that will be used. Ask before proceeding.

## 2. Schedule the weekly run

Use the scheduler native to the current caller. Check existing schedules for a `Weekly Self-Retro` name or an invocation containing `self-retro`; update the equivalent job instead of creating a duplicate.

- **Claude Code:** use `/schedule` for a weekly job bound to the vault folder. Do not use `/loop` (loops expire within three days).
- **Codex:** use the Automation creation/update tool for a weekly local automation with the vault as its working directory.
- **Claude Cowork/Desktop or web:** create a weekly Scheduled Task / routine. For a cloud routine with no local files, use **signals mode** and attach the git-backed vault so the run can commit its report.
- **No native scheduler:** leave the skill installed and return the exact manual command below. Do not install cron or launchd without a separate explicit request.

Scheduled prompt for **local mode**:

```text
Run /self-retro --local --days 7. Save the report into <vault>/reports/self-retro/ and update the meta index. Make no other durable changes without approval.
```

Scheduled prompt for **signals mode** (cloud/web routine): use the full paste-ready prompt in `../self-retro/references/web-routine.md`, with the identity fields filled in. It gathers GitHub/Jira/Glean signals, writes `<vault>/reports/self-retro/YYYY-MM-DD.md`, updates the meta index, commits and pushes, and optionally DMs Slack.

Require explicit confirmation immediately before creating or updating the schedule.

## 3. Storage convention

Each run writes `<vault>/reports/self-retro/YYYY-MM-DD.md` (the week's report) and appends one row to `<vault>/reports/self-retro/index.md` — a running meta report: date, mode, top learning-plan item, and a checkbox for whether it was acted on. Create parent directories on first run. Rerunning the same date replaces that day's file idempotently; never rewrite prior weeks.

## 4. Verify

Report the schedule name, cadence, timezone, execution mode, next run, resolved mode, and report location. End with the exact manual command so the user can run it any time:

```text
/self-retro --days 7
```
