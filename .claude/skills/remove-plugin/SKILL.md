---
name: remove-plugin
description: Remove or deprecate an Apollo marketplace plugin. Use when asked to retire, delete, unpublish, or remove a top-level plugin from apolloio/claude-plugins.
disable-model-invocation: true
---

# Remove Plugin

Use this workflow in `apolloio/claude-plugins` when retiring a top-level plugin under `plugins/`.

## Workflow

1. Confirm the plugin name.

   - Plugin path: `plugins/<plugin-name>/`
   - If the request does not name one plugin clearly, ask before deleting files.

1. Check for rollout dependencies before removal.

   - Search the repo for `/plugin-name:` invocations, marketplace entries, docs, tests, and references.
   - If the plugin is installed by default, required for a group, or owned by another team, recommend deprecation before deletion.

1. Remove the plugin from both marketplace files:

   - `.claude-plugin/marketplace.json`
   - `.agents/plugins/marketplace.json`

1. Delete `plugins/<plugin-name>/` only after marketplace removal and reference cleanup are clear.

1. Update docs only when workflow or user-facing availability changes. Do not manually edit generated inventory tables in README.md or SKILL_INVENTORY.md.

1. Validate before pushing:

   ```bash
   mdformat .
   claude plugin validate .
   python -m pytest tests/test_marketplace.py -q
   ```

   If Codex is installed and exposes plugin validation, also run `codex plugin validate .`; otherwise note that Codex validation was unavailable.

## Review Checklist

- The plugin is gone from both marketplace files.
- No docs or examples still point users to the removed plugin.
- The removal plan accounts for default installs, required installs, and owner communication.
- Validation passes after the plugin directory is removed.
