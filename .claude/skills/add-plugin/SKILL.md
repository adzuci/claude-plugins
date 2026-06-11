---
name: add-plugin
description: Add or update an Apollo marketplace plugin with both Claude Code and Codex manifests, marketplace entries, README guidance, and validation. Use when asked to make a new plugin, publish a skill pack, or fix plugin packaging in apolloio/claude-plugins.
disable-model-invocation: true
---

# Add Plugin

Use this workflow in `apolloio/claude-plugins` whenever a top-level folder under `plugins/` should become an installable marketplace plugin.

## Workflow

1. Pick a lowercase kebab-case plugin name, for example `apollo-risk`.

1. Copy the templates into `plugins/<plugin-name>/`:

   ```text
   plugins/<plugin-name>/
   ├── .claude-plugin/plugin.json
   ├── .codex-plugin/plugin.json
   └── skills/<skill-name>/SKILL.md
   ```

   Start from:

   - `template/.claude-plugin/plugin.json`
   - `template/.codex-plugin/plugin.json`
   - `template/skills/example/SKILL.md`

1. Update both manifests:

   - Set `name` exactly equal to the plugin directory name.
   - Set Claude `displayName` and Codex `interface.displayName` to the same user-facing name.
   - Keep descriptions short and audience-specific.
   - In `.codex-plugin/plugin.json`, include `skills: "./skills/"` whenever the plugin has a `skills/` directory.
   - Include `mcpServers: "./.mcp.json"` only when `.mcp.json` exists.
   - Set Codex `interface.composerIcon` and `interface.logo` only when the plugin has a real, plugin-specific icon. Do not wire generic placeholder icons into the marketplace.

1. Add the plugin to both marketplace files:

   - `.claude-plugin/marketplace.json`
   - `.agents/plugins/marketplace.json`

   Keep entry order aligned between Claude and Codex. Codex entries must include `policy.installation`, `policy.authentication`, and `category`.

1. Add at least one real skill under `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`.

   - Skill frontmatter `name` must match the skill directory exactly.
   - `description` should say what the skill does and when to use it.
   - Keep detailed references or scripts inside the skill folder, not in the README.

1. Update README workflow docs only if the way to create, install, test, or publish plugins changed. Do not manually edit generated inventory tables in README.md or SKILL_INVENTORY.md.

1. Run validation:

   ```bash
   mdformat .
   claude plugin validate .
   python -m pytest tests/test_marketplace.py -q
   ```

   If Codex is installed and exposes plugin validation, also run `codex plugin validate .`; otherwise note that Codex validation was unavailable.

## Review Checklist

- Every `plugins/<plugin-name>` directory intended for publication has both manifest files.
- Every published plugin in `.claude-plugin/marketplace.json` also appears in `.agents/plugins/marketplace.json`.
- Every listed `source` path exists.
- Claude and Codex display names match unless there is a deliberate reason.
- Codex icon paths exist when `interface.composerIcon` or `interface.logo` is set, and generic placeholder icons are not wired into marketplace manifests.
- Every skill frontmatter `name` matches its skill directory.
- Skill names are unique across plugins and repo-local `.claude/skills`.
- Plugin descriptions are one sentence and say when the plugin or skill should be used.
