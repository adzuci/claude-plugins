# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Repo Purpose

This is Apollo's shared Claude Code and Codex skills marketplace. Skills live in `plugins/<plugin>/skills/<skill-name>/SKILL.md` and are installable via the `apollo-plugins` private marketplace.

## Adding a Skill

- Copy `template/skills/example/SKILL.md` to `plugins/<plugin>/skills/<skill-name>/SKILL.md`
- Set `name` in frontmatter to match the directory name exactly (enforced by CI)
- Set `description` to one line describing what the skill does and when to activate it
- Invoke commands are `/plugin-name:skill-name` (e.g. `/apollo-eng:pr-description`)
- Keep both plugin manifests when adding or changing a plugin: `.claude-plugin/plugin.json` for Claude Code and `.codex-plugin/plugin.json` for Codex
- Keep both marketplace files in sync: `.claude-plugin/marketplace.json` for Claude Code and `.agents/plugins/marketplace.json` for Codex

## Validation

```bash
claude plugin validate .
codex plugin validate .
```

Run these before committing. CI also runs the Claude validation on every PR.

## Formatting

Install mdformat once:

```bash
pip install mdformat mdformat-frontmatter
```

Run it on any Markdown files you edit before committing:

```bash
# Format a specific file
mdformat <file.md>

# Format everything (run from repo root)
mdformat .
```

CI runs `mdformat --check .` on every PR and will fail if files are not formatted.

## Git & PRs

- **Branches**: Use the format `<user>/<ticket>-description-of-changes` (e.g. `adzuci/ABC-123-add-bump-version-workflow`).
- **Commits**: Use Conventional Commits format (e.g. `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`). Prefix with a ticket if one exists, otherwise keep messages concise.
- Keep commit messages short, meaningful, and descriptive. Focus on the reason for the change and what it solves — do not list individual code changes (that information is in the diff).
- Always run the `apollo-eng:pr-description` skill before creating a PR
- The README skill inventory table is auto-updated by CI on merge — do not edit it manually

## Self-Improvement

When corrected, suggest an update to this file to prevent the same mistake again.

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.
