---
name: productivity-setup
description: Install the portable productivity skill set for locally available Claude Code and Codex clients, configure an Obsidian vault, and create the caller-native Friday AI Coach schedule. Invoke with /productivity:productivity-setup or /productivity-setup.
disable-model-invocation: true
---

# Productivity Setup

Install managed local copies of `productivity-setup`, `todo`, `wrapup`, `daily-wrapup`, and `ai-coach`. Schedule only the AI Coach, using the product from which this setup skill is running.

## Usage

```text
/productivity:productivity-setup
/productivity:productivity-setup --vault ~/notes --friday-time 16:30
```

## 1. Detect And Confirm

Resolve the vault from an explicit argument, `$VAULT`, the current directory when it is an Obsidian vault, or `~/obsidian-vault`. Ask for the path if none exists.

Run the installer without `--apply`:

```bash
python3 scripts/install_productivity.py --vault <vault>
```

Show one concise confirmation containing:

- detected local clients and target directories,
- the five managed skills,
- the vault path,
- `Friday at 16:30` in the user's local timezone unless another time was supplied,
- the caller-native scheduled-task type.

Ask before applying because installation and schedule creation write outside the current project. If a target contains an unmanaged skill with the same name, preserve it and report the conflict; never overwrite it automatically.

## 2. Install

After confirmation, run:

```bash
python3 scripts/install_productivity.py --vault <vault> --apply
```

The script installs Claude copies under `~/.claude/skills` and Codex copies under `~/.codex/skills` only when those clients are installed. It removes Claude-only direct-invocation frontmatter from Codex copies, writes a managed marker for safe updates, and saves the selected vault in the permission-restricted `~/.config/adzuci-productivity/config.json`.

If this skill is running in a hosted client with no local CLI, skip local copying: the plugin already exposes the skills in the current client. Continue with the native schedule when available.

## 3. Schedule Friday AI Coach

Use the scheduler native to the current caller, not every detected client. Check existing schedules for the name `Weekly AI Coach` or a prompt/invocation containing `ai-coach`; update an equivalent Friday task instead of creating a duplicate.

- **Codex:** use the Automation creation/update tool. Configure a local weekly automation for Friday at 16:30 local time, with the vault as its working directory.
- **Claude Code:** use `/schedule` for a weekly Friday job and bind it to the vault repository/folder. Do not use `/loop`; loops expire after at most three days.
- **Claude Cowork/Desktop:** create a weekly Scheduled Task or routine with the vault folder attached when local files are required.
- **No native scheduler:** leave the skills installed and return the exact manual Friday command `/ai-coach weekly --vault <vault>`. Do not install cron or launchd without a separate explicit request.

Use this scheduled prompt:

```text
Run /ai-coach weekly against <vault>. Review the previous seven days of curated session notes, write the weekly coaching report, and make no durable memory changes without approval.
```

Require explicit confirmation immediately before creating or updating the schedule.

## 4. Verify

Verify each installed `SKILL.md`, report conflicts or unavailable clients, and show the schedule name, cadence, timezone, execution mode, and next run. End with the exact manual commands for each installed client.
