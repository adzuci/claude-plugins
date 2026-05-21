# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Repo Purpose

This is Apollo's shared Claude Code skills marketplace. Skills live in `plugins/<plugin>/skills/<skill-name>/SKILL.md` and are installable via the `apollo-plugins` private marketplace.

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

## Testing

If a skill ships executable code (e.g. Python in `scripts/`), add pytest tests
in a sibling `tests/` directory. CI runs `python -m pytest -q` from the repo root
(Python 3.9 and 3.11 matrix) and auto-installs any `plugins/**/scripts/requirements.txt`
or `plugins/**/tests/requirements.txt` it finds.

- Keep pure helpers at module scope so they can be imported and tested directly.
- Use `pytest.importorskip("module_name")` at the top of each test file so the
  suite skips cleanly when scripts haven't landed yet.
- Add `from __future__ import annotations` to any script using `X | Y` union type
  syntax so it runs on Python 3.9. If a skill truly needs 3.10+, add a
  `pytest.skip` version guard at the top of its test file.
- Install deps with `pip install -r tests/requirements.txt` and run
  `python -m pytest -q` before committing.

See the README "Testing Skill Scripts" section for the full convention.

## Documentation

This repo is read by both engineers and non-engineers (PMs, GTM, designers
installing skills). Keep that audience in mind when editing docs.

- **Update the README whenever you change how to create, modify, test, install,
  or run things** — workflow changes that aren't reflected in the README
  effectively don't exist. CLAUDE.md is a pointer; the README is the source
  of truth.
- **Title case headers** (e.g. `## Testing Skill Scripts`, not `## Testing skill scripts`).
- **Be concise.** Cut redundant explanation, prefer code snippets over prose,
  and don't repeat the same concept in multiple sections.
- **Lead with the recipe, not the rationale.** Non-engineers want copy-paste
  steps; deeper "why" notes can come after.
- **Skip jargon when a plain word works.** When a technical term is necessary
  (e.g. `pytest.importorskip`), give a one-line explanation in context.

## Git & PRs

- **Branches**: Use the format `<user>/<ticket>-description-of-changes` (e.g. `adzuci/ABC-123-add-bump-version-workflow`).
- **Commits**: Use Conventional Commits format (e.g. `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`). Prefix with a ticket if one exists, otherwise keep messages concise.
- Keep commit messages short, meaningful, and descriptive. Focus on the reason for the change and what it solves — do not list individual code changes (that information is in the diff).
- Always run the `apollo-eng:pr-description` skill before creating a PR
- The README skill inventory table is auto-updated by CI on merge — do not edit it manually

## Self-Improvement

When corrected, suggest an update to this file to prevent the same mistake again.

## Skill Routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.
