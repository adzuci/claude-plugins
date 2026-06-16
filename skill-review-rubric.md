Review new or modified files under `plugins/` and `.claude/skills/` as Skills Marketplace or repo-local skill submissions.

This is an **internal, private repository**. All skills are for Apollo employees only.
Internal organizational details (employee names, revenue targets, org structure, financial
metrics, team rosters) are expected and appropriate. Do NOT flag internal information as
a security or sensitivity concern. Only flag actual secrets (API keys, tokens, passwords).

Focus on high-signal issues only. Prefer concrete, file-specific feedback.

Frontmatter

- Confirm `SKILL.md` exists at `plugins/<plugin>/skills/<skill-name>/SKILL.md` or `.claude/skills/<skill-name>/SKILL.md`. Do NOT expect a SKILL.md at the plugin root — plugins contain multiple skills in subdirectories.
- Require YAML frontmatter with `name` and `description`. Expect `disable-model-invocation: true` for skills that should only activate by explicit command, and flag omissions as context bloat unless natural-language activation is clearly intentional.
- Check that `name` matches the skill directory name and uses lowercase letters, digits, and hyphens.
- Check that new skill names are unique across all plugins and repo-local `.claude/skills`. Flag cross-plugin duplicates even when the duplicate skills live in different plugins.
- Check that `description` concisely explains what the skill does. Do not reward long trigger lists by default.
- For skills with `disable-model-invocation: true`, prefer short command/catalog descriptions.
- Only ask for activation examples when natural-language activation is intentionally enabled.
- Do not ask authors to add unsupported `arguments` frontmatter. If a direct-invoked skill has required or useful optional inputs, expect a concise `Usage` or `Inputs` section in the body instead.

Descriptions — skill vs plugin

- **Plugin descriptions** (in `plugin.json` and `marketplace.json`) are short catalog blurbs identifying the team and broad scope. Do not demand activation examples in plugin descriptions.
- **Skill descriptions** (in `SKILL.md` frontmatter) should be short by default. Activation triggers, user intents, and context phrases belong there only for skills that intentionally omit `disable-model-invocation: true`.

Routing and activation

- Default new skills to `disable-model-invocation: true`. This keeps inactive skills from consuming routing context and avoids accidental activation.
- If a new or changed skill omits `disable-model-invocation: true`, require a clear reason the user would not know to invoke it explicitly.
- For direct-invoked skills, arguments can be passed as text in the slash-command invocation. Review for clear, concise usage examples rather than longer descriptions.
- For natural-language activated skills, check descriptions for trigger overlap with existing skills that the same user might have active. Flag broad or generic wording that could route common requests away from a more specific skill.
- Prefer descriptions that make the skill's audience and activation boundary clear without becoming a long list of phrases.

Structure

- Expect the standard pattern: `SKILL.md` plus optional `scripts/`, `references/`, and `assets/`.
- Flag unnecessary support docs such as `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md`, or similar extra process docs inside a skill.
- Check that optional resources directly support repeated execution of the skill.
- For each new `agents/<agent-name>.md`, consider a concise `suggestion` asking the author to add an agent README when it would help future maintainers understand why the agent exists, when to use it instead of a skill, and what operational contract or ownership expectations it carries.

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

Agent and skill design

- For complex or repeatable skills or agents, consider one concise `suggestion` that asks the author to clarify the workflow contract only when the review shows unclear determinism, unclear agent judgment boundaries, or an unclear next-step arc:
  - what should be deterministic, such as scripts, templates, fixed commands, or rubrics
  - what the agent should be allowed to interpret, explain, draft, or decide
  - what the user should be able to do next after the skill or agent runs
- Prefer this nudge for skills or agents that involve scoring, reviews, incidents, oncall, deployments, security, data changes, handoffs, or other workflows where inconsistent agent behavior would be costly.
- Keep this feedback advisory and concise. Use severity `suggestion` unless the same concern also creates a concrete execution, safety, or routing problem covered elsewhere in this rubric.

Security and safety

- Flag embedded secrets (API keys, tokens, passwords, credentials).
- Do NOT flag internal infrastructure references (Slack IDs, Grafana UIDs, GCS paths, internal URLs) — these are expected in an internal skills repo and are not secrets.
- Flag instructions that exfiltrate data unnecessarily or send sensitive content to third parties without justification.
- Flag obviously malicious, destructive, or unsafe automation patterns.

Review policy

- Report only meaningful issues.
- Use severity `error` for structural breakage, unsafe content, or blockers.
- Use severity `warning` for likely quality, routing, or context-bloat problems.
- Use severity `suggestion` for polish and maintainability improvements.

Verdict rules

Severity ranks error > warning > suggestion; the highest severity present determines the verdict.

- **REQUEST_CHANGES** — use ONLY when at least one `error`-severity issue exists.
- **COMMENT** — use when there are `warning`-severity issues but no errors.
- **APPROVE** — use when there are no issues, or only `suggestion`-severity items.
