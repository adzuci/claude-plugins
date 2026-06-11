---
name: remove-skill
description: Remove or deprecate an Apollo marketplace skill from an existing plugin. Use when asked to retire, delete, unpublish, or move a skill in apolloio/claude-plugins.
disable-model-invocation: true
---

# Remove Skill

Use this workflow in `apolloio/claude-plugins` when retiring a skill from an existing plugin.

## Workflow

1. Confirm the plugin and skill name.

   - Skill path: `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`
   - If the request is ambiguous, ask before deleting files.

1. Check for references before removal.

   - Search for `/plugin-name:skill-name`, `skill-name`, docs, tests, scripts, marketplace notes, and owner references.
   - If the skill is still used by a default-installed plugin or important workflow, recommend deprecation before deletion.

1. Delete `plugins/<plugin-name>/skills/<skill-name>/`.

1. Remove or update related tests, docs, references, and helper scripts that only existed for that skill.

1. Do not manually edit generated inventory tables in README.md or SKILL_INVENTORY.md.

1. Validate before pushing:

   ```bash
   mdformat .
   claude plugin validate .
   python -m pytest tests/test_marketplace.py -q
   ```

   If Codex is installed and exposes plugin validation, also run `codex plugin validate .`; otherwise note that Codex validation was unavailable.

## Review Checklist

- No repo references still route users to the removed skill.
- The parent plugin still has a valid manifest and, if published, at least one real skill.
- Owner communication or deprecation timing is called out when the skill is default-installed or broadly used.
- Validation passes after deletion.
