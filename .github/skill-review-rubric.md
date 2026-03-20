Review new or modified files under `plugins/` as Skills Marketplace submissions.

Focus on high-signal issues only. Prefer concrete, file-specific feedback.

Frontmatter

- Confirm `SKILL.md` exists at the root of each skill folder.
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
