# {{SKILL_NAME}}

{{SKILL_PURPOSE_PARAGRAPH}}

This skill was generalized from a personal version using `skill-generalizer`. It needs a small amount of setup before first use.

## Install

Drop this folder into `~/.claude/skills/` (or your platform's equivalent). The skill should appear in your available skills list.

If you got this as a `.skill` file (a ZIP), unzip it into `~/.claude/skills/`.

## Configure

`config.md` in this skill's directory lists every variable the skill needs, each set to `<UNSET>`, with documentation for what it means. That file ships with the skill, so a plugin update replaces it. Your answers go somewhere you own instead.

You have two options:

1. **Run the skill and let it ask you.** Invoke the skill normally. The first time, Claude notices the unset values, asks you for each one, and saves your answers to `~/.claude/plugin-config/<plugin>/<skill>.md`. From then on, it stays out of your way, and plugin updates don't disturb it.
1. **Set the values up front.** Create `~/.claude/plugin-config/<plugin>/<skill>.md` yourself with a YAML frontmatter block using the same keys as `config.md`. Anything you leave out falls back to the shipped default.

An empty string is a real answer meaning "intentionally blank", so the skill won't keep asking about keys you deliberately left empty.

## Variables

{{VARIABLE_LIST_BY_CATEGORY}}

## Dependencies

{{DEPENDENCIES_BLOCK}}

## Bundled documentation

This skill ships with reference documentation in its `references/` folder. The skill reads these files at runtime to inform its behavior — they're not optional. If you want the skill to behave differently (use your team's voice guide instead of this one, follow your own rubric), edit or replace the bundled files. The paths inside SKILL.md are skill-relative (`references/<filename>`), so swapping the content out is enough; you don't need to touch SKILL.md.

{{BUNDLED_DOCS_BLOCK}}

## A note on secrets

If any variables are secrets (API keys, tokens), `config.md` is a plain file in this skill's folder. Don't commit it to a public repo or share it casually. v1 of this skill format does not have first-class secret handling.

## Claude.ai vs Claude Code

The persistence trick (the skill writing your answers back to `config.md`) only works in Claude Code, where skills have filesystem access. On Claude.ai, the skill will re-prompt you for any unset values each new conversation. The simplest workaround is to edit `config.md` manually once before you install on Claude.ai.

## Source

Generalized from a personal skill using [skill-generalizer](https://github.com/...). Filing bugs or improvements? Open an issue against whichever repo this skill lives in.
