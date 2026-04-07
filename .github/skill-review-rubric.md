Review new or modified files under `plugins/` as Skills Marketplace submissions.

This is an **internal, private repository**. All skills are for Apollo employees only.
Internal organizational details (employee names, revenue targets, org structure, financial
metrics, team rosters) are expected and appropriate. Do NOT flag internal information as
a security or sensitivity concern. Only flag actual secrets (API keys, tokens, passwords).

Focus on high-signal issues only. Prefer concrete, file-specific feedback.

Frontmatter

- Confirm `SKILL.md` exists at `plugins/<plugin>/skills/<skill-name>/SKILL.md`. Do NOT expect a SKILL.md at the plugin root — plugins contain multiple skills in subdirectories.
- Require YAML frontmatter with exactly `name` and `description`.
- Check that `name` matches the skill directory name and uses lowercase letters, digits, and hyphens.
- Check that `description` explains both what the skill does and when to use it.
- Prefer trigger-rich wording with explicit user intents, contexts, or phrases that should activate the skill.
- Flag vague descriptions that are too generic to trigger reliably.

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

- Flag embedded secrets, tokens, credentials, or private endpoints.
- Flag instructions that exfiltrate data unnecessarily or send sensitive content to third parties without justification.
- Flag obviously malicious, destructive, or unsafe automation patterns.

Review policy

- Report only meaningful issues.
- Use severity `error` for structural breakage, unsafe content, or blockers.
- Use severity `warning` for likely quality or trigger problems.
- Use severity `suggestion` for polish and maintainability improvements.
- If there are no meaningful issues, say so clearly and approve.
