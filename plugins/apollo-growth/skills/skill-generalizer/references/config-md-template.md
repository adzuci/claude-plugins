---
# Variables this skill needs. Replace each <UNSET> with your value.
# Lists use YAML list syntax: ["item1", "item2"]
{{FRONTMATTER_BLOCK: null}: null}
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it, so don't save your answers here.

Just run the skill. It reads this file for defaults, prompts you for anything still `<UNSET>`, and writes your answers to `~/.claude/plugin-config/<plugin>/<skill>.md`, which survives updates. To set values up front, create that file yourself using the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't re-ask for keys you deliberately left empty.

______________________________________________________________________

{{VARIABLE_DOCS}}

______________________________________________________________________

## A note on secrets

If any of your config values are secrets (API keys, tokens, passwords), be aware that this file is plain text inside the skill's directory. Don't commit it to a public repo, don't share it casually, and don't paste it into chat. v1 of this skill format does not have first-class secret handling.

## Claude.ai users

Persistence (this file getting auto-updated) only works in Claude Code, where the skill has filesystem access. On Claude.ai, the skill will re-prompt you for any `<UNSET>` values each new conversation. You can avoid that by editing this file directly before installing.
