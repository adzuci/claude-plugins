# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Repo Purpose

This is Apollo's shared Claude Code skills marketplace. Skills live in `plugins/<plugin>/skills/<skill-name>/SKILL.md` and are installable via the `apollo-skills` private marketplace.

## Adding a Skill

- Copy `template/skills/example/SKILL.md` to `plugins/<plugin>/skills/<skill-name>/SKILL.md`
- Set `name` in frontmatter to match the directory name exactly (enforced by CI)
- Set `description` to one line describing what the skill does and when to activate it
- Invoke commands are `/plugin-name:skill-name` (e.g. `/apollo-eng:pr-description`)

## Validation

```bash
claude plugin validate .
```

Run this before committing. CI also runs it on every PR.

## Git & PRs

- Prefix commits with a ticket if one exists, otherwise keep messages concise
- Always run the `apollo-eng:pr-description` skill before creating a PR
- The README skill inventory table is auto-updated by CI on merge — do not edit it manually

## Self-Improvement

When corrected, suggest an update to this file to prevent the same mistake again.
