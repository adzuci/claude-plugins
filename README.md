# claude-plugins

[![CI](https://github.com/adzuci/claude-plugins/actions/workflows/ci.yml/badge.svg)](https://github.com/adzuci/claude-plugins/actions/workflows/ci.yml)
[![GitHub Pages](https://img.shields.io/badge/site-GitHub%20Pages-2359d1)](https://adzuci.github.io/claude-plugins/)

Public Claude Code and Codex plugins for local-first AI workflows.

The flagship plugin is **`memory`**: a setup skill for creating a local, git-backed Obsidian vault that captures durable notes from AI working sessions. The **`productivity`** plugin builds on that vault with task capture, session hygiene, daily planning, and a weekly AI coach; **`career`** adds a job-market intelligence sweep.

The [companion site](https://adzuci.github.io/claude-plugins/) has one post per plugin: [Memory as reliability practice](https://adzuci.github.io/claude-plugins/memory.html) · [An operating loop for AI-assisted work](https://adzuci.github.io/claude-plugins/productivity.html) · [Job search as market intelligence](https://adzuci.github.io/claude-plugins/career.html)

![Memory setup architecture](docs/assets/memory-system-diagram.svg)

## Why This Exists

AI sessions can be useful in the moment and still disappear as soon as the thread ends. The assistant helped debug a strange failure, compare trade-offs, draft a review, or clarify a decision, but the useful context stayed trapped in a transcript.

`memory` is a small attempt to make that context durable without making it mysterious:

- Obsidian for plain Markdown that stays inspectable
- git for auditable history
- explicit setup gates before anything writes to dotfiles
- Claude Code session capture as the first-class path
- compatibility notes for Codex and Antigravity so the memory belongs to the person, not one assistant

The goal is not a grand second-brain system. The goal is lower re-orientation cost: fewer repeated explanations, fewer lost decisions, and a clearer trail from “we figured this out” to “we can reuse this later.”

## What the `memory` Plugin Does

| Skill | Purpose |
| --- | --- |
| `/memory:memory-setup` | Set up an Obsidian-backed memory vault with Claude Code session capture and optional Codex/Antigravity importers. |
| `/memory:memory-setup crypt` | Encrypt sensitive vault dirs with git-crypt; the key is handed to your password manager, never committed. See `plugins/memory/skills/memory-setup/references/encryption.md` for what it does and does not protect. |

Setup also offers scheduled git sync (obsidian-git settings plus a launchd agent on macOS; a ready-made cron line elsewhere) so the vault converges across machines without manual pushes.

The default Claude Code path sets up:

- a local Obsidian vault under a user-selected parent directory
- `claudian` and `obsidian-git` as Obsidian community plugins
- a `SessionEnd` hook in `~/.claude/settings.json`
- a managed memory block in `~/.claude/CLAUDE.md`

Current support note: the setup flow has been tested on macOS. Linux and Windows compatibility reports and PRs are very welcome.

## What the `productivity` Plugin Does

| Skill | Purpose |
| --- | --- |
| `/productivity:productivity-setup` | Install managed local copies of the core skills for each detected Claude Code and Codex client, record the vault in `~/.config/adzuci-productivity/config.json`, and schedule the Friday AI Coach. |
| `/productivity:todo` | Capture durable tasks in the vault's Kanban `backlog.md` — idempotent, with explicit urgent promotion. |
| `/productivity:ai-coach` | Weekly report-only review of curated session notes for repeated friction and reusable workflows. |
| `/productivity:wrapup` | Pre-`/clear` hygiene check: uncommitted work, unpushed commits, open loose ends. |
| `/productivity:daily-wrapup` | End-of-day review, tomorrow preview, and goal capture into the vault session note. |
| `/productivity:budgetclaw-setup` | Claude Code spend monitoring with local macOS notifications. |

It also ships `create-agent` and the `agent-ops-setup`/`agent-ops-report` pair for privacy-safe scheduled-agent operations. See `plugins/productivity/README.md` for details.

## Install

Claude Code marketplace metadata lives in `.claude-plugin/marketplace.json`.

Codex marketplace metadata lives in `.agents/plugins/marketplace.json`.

For Codex:

```bash
codex plugin marketplace add adzuci/claude-plugins
codex plugin add memory@adzuci-plugins
```

For Claude Code:

```bash
claude plugin marketplace add adzuci/claude-plugins
claude plugin install memory@adzuci-plugins
```

Then invoke the setup skill:

```text
/memory:memory-setup
```

The other plugins install the same way (`claude plugin install productivity@adzuci-plugins`, `claude plugin install career@adzuci-plugins`).

## Safety Model

This skill is intentionally cautious because it touches personal knowledge and local configuration.

- It explains the trade-offs before setup.
- It runs read-only preflight checks first.
- It asks before installing Obsidian.
- It backs up settings before editing.
- It keeps generated memory in plain Markdown.
- It is designed to be rerunnable and idempotent where possible.

The repo includes CI for the bundled Python scripts and plugin metadata:

- compile all memory setup scripts and tests
- run the pytest suite on Python 3.9 and 3.12
- validate marketplace and plugin JSON
- verify the static site references existing assets

## Repository Structure

```text
.claude-plugin/
  marketplace.json
.agents/
  plugins/
    marketplace.json
.github/
  workflows/
    ci.yml
docs/
  index.html          # blog landing page
  memory.html  productivity.html  career.html
  assets/
plugins/
  memory/
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    README.md
    skills/memory-setup/
      SKILL.md
      scripts/
      templates/
      references/
      tests/
  productivity/
    .claude-plugin/plugin.json
    README.md
    skills/
      productivity-setup/  todo/  ai-coach/
      wrapup/  daily-wrapup/  budgetclaw-setup/
      create-agent/  agent-ops-setup/  agent-ops-report/
  career/
    skills/market-sweep/
```

## Development

This repo is intentionally small, but the bar for changes is still: can someone else install it, understand what it writes, and recover cleanly if something goes wrong?

Run the skill tests:

```bash
python3 -m pytest plugins/memory/skills/memory-setup/tests -q
python3 -m pytest plugins/productivity/skills/todo/tests plugins/productivity/skills/productivity-setup/tests -q
```

Validate the plugin metadata with the CLI available in your environment:

```bash
claude plugin validate .
```

## Contributing

If this workflow is useful, please open an issue or PR. The most valuable feedback is concrete:

- setup failures on a real machine
- Linux or Windows compatibility fixes
- missing preflight checks
- unclear install instructions
- unsafe or surprising writes
- compatibility fixes for Claude Code, Codex, Antigravity, Obsidian, or git

Small, focused PRs are welcome. Please include the command you ran, the environment you tested on, and whether `python3 -m pytest plugins/memory/skills/memory-setup/tests -q` passed.

## License

MIT
