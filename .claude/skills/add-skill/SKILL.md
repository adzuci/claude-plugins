---
name: add-skill
description: Add or update an Apollo marketplace skill in an existing plugin. Use when creating a new SKILL.md, moving a skill into a plugin, or fixing skill frontmatter, routing, validation, or review readiness in apolloio/claude-plugins.
disable-model-invocation: true
---

# Add Skill

Use this workflow in `apolloio/claude-plugins` when adding a skill to an existing plugin. If `/skill-creator` is available, use it first for general skill-authoring guidance, then apply the Apollo-specific checklist below.

## Workflow

1. Pick the target plugin and skill name.

   - Plugin path: `plugins/<plugin-name>/`
   - Skill path: `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`
   - Skill name must be lowercase kebab-case and match the directory exactly.

1. Start from the template:

   ```bash
   cp -r template/skills/example plugins/<plugin-name>/skills/<skill-name>
   ```

1. Set frontmatter:

   - `name`: exactly the skill directory name.
   - `description`: one concise line saying what the skill does. Avoid long trigger lists unless natural-language activation is intentionally needed.
   - `disable-model-invocation: true`: default to this for new skills unless the skill truly needs natural-language activation.
   - Do not add unsupported `arguments` frontmatter.

1. Keep `SKILL.md` concise.

   - Put only the core workflow in `SKILL.md`.
   - If the skill takes inputs, add a short `Usage` or `Inputs` section with CLI-style examples such as `/plugin-name:skill-name <target> --flag value`.
   - Move large examples, schemas, policies, or variants into `references/`.
   - Put deterministic helper code in `scripts/`.
   - Avoid extra process docs such as `README.md`, `INSTALLATION_GUIDE.md`, or `CHANGELOG.md` inside the skill folder.

1. Add tests when the skill ships scripts.

   - Put tests in `plugins/<plugin-name>/skills/<skill-name>/tests/`.
   - Keep script helpers at module scope.
   - Gate `print`, `sys.exit`, and `argparse` behind `if __name__ == "__main__":` so tests can import the module.
   - Add any extra test dependencies to the nearest `tests/requirements.txt`.

   `tests/conftest.py` should put the skill's `scripts/` directory on `sys.path`:

   ```python
   import sys
   from pathlib import Path

   SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
   if SCRIPTS.is_dir() and str(SCRIPTS) not in sys.path:
       sys.path.insert(0, str(SCRIPTS))
   ```

   Test files should import scripts with `pytest.importorskip` when the script may land separately:

   ```python
   import pytest

   my_module = pytest.importorskip("my_module")


   def test_helper_returns_expected():
       assert my_module.helper(42) == "expected"
   ```

   Add `from __future__ import annotations` to scripts that use `X | Y` union types and must run on Python 3.9. If a skill requires Python 3.10+ syntax such as `match`, add a module-level `pytest.skip(..., allow_module_level=True)` version guard.

1. Validate before pushing:

   ```bash
   mdformat plugins/<plugin-name>/skills/<skill-name>/SKILL.md
   claude plugin validate .
   python -m pytest tests/test_marketplace.py -q
   ```

   If Codex is installed and exposes plugin validation, also run:

   ```bash
   codex plugin validate .
   ```

   If Codex is unavailable or does not expose `plugin validate`, note that the CLI command was unavailable.

1. For large or complex skills, review against `./skill-review-rubric.md` before pushing.

   Treat a skill as complex when it has long instructions, scripts, references, multiple activation paths, external data access, or broad cross-team routing.

1. If the skill has scripts or tests, use `/test-skill` before pushing for targeted pytest runs.

## Review Checklist

- Frontmatter exists and includes `name` and `description`.
- `name` matches the skill directory exactly.
- Skill names are unique across plugins and repo-local `.claude/skills`.
- Description is concise and does not overfit to a long trigger list.
- New skills set `disable-model-invocation: true` unless natural-language activation is justified.
- Inputs, flags, or positional arguments are documented in the body when useful, not as unsupported frontmatter.
- `SKILL.md` is token-efficient and points to bundled resources only when needed.
- Scripts have pytest coverage when they contain meaningful logic.
- Markdown is formatted and plugin validation has run.
