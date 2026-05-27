Review new or modified files under `plugins/` as Skills Marketplace submissions.

This is an **internal, private repository**. All skills are for Apollo employees only.
Internal organizational details (employee names, revenue targets, org structure, financial
metrics, team rosters) are expected and appropriate. Do NOT flag internal information as
a security or sensitivity concern. Only flag actual secrets (API keys, tokens, passwords).

Focus on high-signal issues only. Prefer concrete, file-specific feedback.

Frontmatter

- Confirm `SKILL.md` exists at `plugins/<plugin>/skills/<skill-name>/SKILL.md`. Do NOT expect a SKILL.md at the plugin root — plugins contain multiple skills in subdirectories.
- Require YAML frontmatter with `name` and `description`. Also allow `disable-model-invocation: true` for skills that should only activate by explicit command.
- Check that `name` matches the skill directory name and uses lowercase letters, digits, and hyphens.
- Check that `description` explains both what the skill does and when to use it.
- Prefer trigger-rich wording with explicit user intents, contexts, or phrases that should activate the skill.
- Flag vague descriptions that are too generic to trigger reliably.

Descriptions — skill vs plugin

- **Plugin descriptions** (in `plugin.json` and `marketplace.json`) are short catalog blurbs identifying the team and broad scope. Do not demand trigger-rich wording in plugin descriptions.
- **Skill descriptions** (in `SKILL.md` frontmatter) are where activation triggers, user intents, and context phrases belong. Apply the trigger-richness checks only to skill-level descriptions.

Routing and activation

- Check new or changed skill descriptions for trigger overlap with existing skills that the same user might have active. Flag broad or generic wording that could route common requests away from a more specific skill.
- Prefer descriptions that make the skill's audience and activation boundary clear, especially for company-wide or cross-team skills.
- Prefer `disable-model-invocation: true` for new skills unless the skill needs natural-language activation. If it is omitted, look for a clear reason the user would not know to invoke the skill explicitly.

Structure

- Expect the standard pattern: `SKILL.md` plus optional `scripts/`, `references/`, and `assets/`.
- Flag unnecessary support docs such as `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md`, or similar extra process docs inside a skill.
- Check that optional resources directly support repeated execution of the skill.

Progressive disclosure

- Keep `SKILL.md` concise and under roughly 500 lines.
- Move large reference material, exhaustive examples, schemas, or variant-specific details into `references/`.
- Ensure `SKILL.md` points to reference files clearly when extra material exists.
- Prefer one-level-deep references linked directly from `SKILL.md`.
- Flag duplicated material copied across `SKILL.md` and reference files.
- Exception: agent files (`agents/*.md`) and `SKILL.md` files serve different runtimes (Cowork agents vs Claude Code skills). Overlap between these is expected and acceptable — both need to be self-contained. Only flag duplication within the same runtime (e.g., two SKILL.md files repeating the same content, or SKILL.md duplicating a `references/` file).

Instruction quality

- Prefer imperative instructions that tell the agent what to do.
- Check whether the workflow is specific enough to execute without guesswork.
- Prefer concise examples over long explanation blocks.
- Reward instructions that explain why a step matters when that improves correctness.
- Flag missing examples or missing decision guidance when the task is fragile or ambiguous.

Security and safety

- Flag embedded secrets (API keys, tokens, passwords, credentials).
- Do NOT flag internal infrastructure references (Slack IDs, Grafana UIDs, GCS paths, internal URLs) — these are expected in an internal skills repo and are not secrets.
- Flag instructions that exfiltrate data unnecessarily or send sensitive content to third parties without justification.
- Flag obviously malicious, destructive, or unsafe automation patterns.

Review policy

- Report only meaningful issues.
- Use severity `error` for structural breakage, unsafe content, or blockers.
- Use severity `warning` for likely quality or trigger problems.
- Use severity `suggestion` for polish and maintainability improvements.

Verdict rules

Severity ranks error > warning > suggestion; the highest severity present determines the verdict.

- **REQUEST_CHANGES** — use ONLY when at least one `error`-severity issue exists.
- **COMMENT** — use when there are `warning`-severity issues but no errors.
- **APPROVE** — use when there are no issues, or only `suggestion`-severity items.
