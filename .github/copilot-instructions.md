# Repository Instructions

This repository is Apollo's shared Claude Code and Codex plugin marketplace.

When editing plugins:

- Keep Claude Code and Codex packaging in sync.
- Every published `plugins/<plugin>/` entry needs both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`.
- Update both marketplaces together: `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Use `/add-plugin` for new plugins, `/add-skill` for skills in existing plugins, `/test-skill` for skill script tests, and `/remove-plugin` or `/remove-skill` for removals when those repo-local Claude skills are available.
- Start manual plugin work from `template/.claude-plugin/plugin.json`, `template/.codex-plugin/plugin.json`, and `template/skills/example/SKILL.md`.
- Do not manually edit generated inventory tables in README.md or SKILL_INVENTORY.md; CI updates them after merge.
- Run `mdformat .`, `claude plugin validate .`, and `python -m pytest tests/test_marketplace.py -q` before proposing changes. If Codex is installed and exposes plugin validation, also run `codex plugin validate .`; otherwise report that Codex validation was unavailable.
