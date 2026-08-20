# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Repo Purpose

This is Apollo's shared Claude Code and Codex skills marketplace. Skills live in `plugins/<plugin>/skills/<skill-name>/SKILL.md` and are installable via the `apollo-plugins` private marketplace.

## Adding a Skill

- For a new top-level plugin, use `/add-plugin` first. It keeps Claude Code and Codex manifests, marketplace entries, docs, and validation in sync.
- For a skill in an existing plugin, use `/add-skill` first. It wraps general skill-authoring guidance and adds Apollo checks for frontmatter, direct-only invocation, token efficiency, validation, and review readiness.
- For skill script tests, use `/test-skill`. It keeps pytest layout, dependency installation, targeted runs, and marketplace validation consistent.
- For removals, use `/remove-plugin` or `/remove-skill` so marketplace entries, references, default-install risk, and validation are checked together.
- Copy `template/skills/example/SKILL.md` to `plugins/<plugin>/skills/<skill-name>/SKILL.md`
- Set `name` in frontmatter to match the directory name exactly (enforced by CI)
- Set `description` to one concise line describing what the skill does. Avoid long trigger lists unless natural-language activation is intentional.
- Default new skills to `disable-model-invocation: true` so they do not add routing context unless the user calls them. Only omit it when natural-language activation is intentional.
- Invoke commands are `/plugin-name:skill-name` (e.g. `/apollo-eng:pr-description`)
- If a direct-invoked skill needs inputs, document them in the skill body as concise usage examples (e.g. `/plugin-name:skill-name <target> --flag value`). Do not add unsupported `arguments` frontmatter.
- Keep both plugin manifests when adding or changing a plugin: `.claude-plugin/plugin.json` for Claude Code and `.codex-plugin/plugin.json` for Codex
- Keep both marketplace files in sync: `.claude-plugin/marketplace.json` for Claude Code and `.agents/plugins/marketplace.json` for Codex
- Do not hand-bump `version` in either plugin manifest. `release-please` (`.github/workflows/release-please.yml`, `release-please-config.json`, `.release-please-manifest.json`) owns versioning per plugin via `extra-files` and bumps both manifests automatically from Conventional Commit messages on merge to `main`.
- Repo-local `.claude/skills` must work for Claude Code users who do not have Codex installed. Do not make those skills depend on Codex-only commands.

## Validation

```bash
mdformat .
claude plugin validate .
codex plugin validate .  # if available
python -m pytest tests/test_marketplace.py -q
```

Run these before committing. If the local Codex CLI does not expose `plugin validate`, note that Codex validation was unavailable.

CI regenerates the skill inventory on every PR and fails if `README.md` or `SKILL_INVENTORY.md` are stale, so you no longer have to remember to run it by hand. If that check (the `inventory` job in `validate.yml`) goes red, regenerate and commit:

```bash
python .github/scripts/update-skill-inventory.py && python -m pytest tests/test_marketplace.py -q
```

CI enforces Markdown formatting, Claude plugin validation, marketplace parity, skill-inventory freshness, plugin manifest schema, Codex display metadata and asset paths, skill frontmatter naming, and cross-plugin skill name uniqueness. Keep this section updated when CI checks change.

## GitHub CLI Prerequisite

This repo enables `apollo-eng` in `.claude/settings.json`, so `/apollo-eng:gh-setup` is available to Claude Code sessions here.

Before running repo-local `.claude/skills` that create, update, or push PRs, check that `gh` is installed and authenticated. If `gh` is missing, unauthenticated, or the current repo uses HTTPS remotes, run `/apollo-eng:gh-setup` first. It installs/checks GitHub CLI, nudges SSH Git remotes, and uses `gh auth login --git-protocol ssh --web` for PR push workflows.

For pre-push review, use `/review`. It loads `skill-review-rubric.md` and scales review depth to the change size; use it especially for large or complex skills with long instructions, scripts, references, broad routing, external data access, or cross-team impact. Reviewers should flag new skills that omit `disable-model-invocation: true` unless natural-language activation is justified.

Use `/update-review-rubric` to inspect recent PR review-bot output, propose evidence-backed rubric improvements, and ask which ones to implement before editing review rules.

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

CI runs `mdformat --check` and markdownlint on changed Markdown files in each PR.

## Testing

If a skill ships executable code, use `/test-skill` and add pytest tests in a sibling `tests/` directory. CI runs `python -m pytest -q` from the repo root on Python 3.9 and 3.11.

- Keep pure helpers at module scope so they can be imported and tested directly.
- Use `pytest.importorskip("module_name")` at the top of each test file so the
  suite skips cleanly when scripts haven't landed yet.
- Add `from __future__ import annotations` to any script using `X | Y` union type
  syntax so it runs on Python 3.9. If a skill truly needs 3.10+, add a
  `pytest.skip` version guard at the top of its test file.
- Install deps with `pip install -r tests/requirements.txt` and run
  `python -m pytest -q` before committing.

See the README "Testing Skill Scripts" section for the concise convention.

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
- The README plugin inventory and `SKILL_INVENTORY.md` are generated by `.github/scripts/update-skill-inventory.py` — do not edit those generated tables manually

## Self-Improvement

When corrected, suggest an update to this file to prevent the same mistake again.

## Tool Loop Guardrails

- If the same tool call, command, search, or file read fails twice with the same
  inputs or returns no new information twice, stop repeating it.
- Before a third attempt, state what has already been tried, what changed since
  the last attempt, and why the retry should produce different evidence.
- If there is no concrete change in inputs, permissions, working directory,
  query, or target file, switch tactics: inspect adjacent files, use a different
  source, narrow the query, or ask the user for the missing input.
- Treat repeated empty results as evidence. Report the absence clearly instead
  of continuing broad searches.
- For long-running or flaky commands, capture the failure mode once, then retry
  only with a specific adjustment such as a timeout, narrower scope, or required
  sandbox escalation.

## Token Guardrails

- Start with targeted discovery: use `rg`, `rg --files`, `git diff`, and narrow
  `sed`/`nl` ranges before opening whole files.
- Do not read generated, vendored, build, lockfile, or large log files unless
  the task specifically depends on them. Prefer searching for exact symbols or
  errors first.
- Keep command output bounded. Use focused paths, line ranges, `--max-count`,
  `tail`, or test filters when full output is not needed.
- After two broad searches without useful signal, stop and narrow the question:
  identify the likely file, symbol, owner, route, or data source before more
  tool calls.
- Run the smallest meaningful validation first. Use full test suites only when
  the change touches shared behavior, release gates, or the user asks for it.
- Summarize large evidence instead of copying it. Include file paths, line
  numbers, and the key finding rather than dumping whole outputs.
- Before using expensive connectors, web searches, or multi-source lookups,
  check local repo context and existing docs first unless current external state
  is required.

## Skill Routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.
