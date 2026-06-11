<!-- Keep this concise. State why the change exists, what changed, and how you tested it. -->

## Why

<!-- What problem, request, or cleanup led to this PR? -->

## What Changed

<!-- Brief bullets. Mention affected plugins, skills, manifests, docs, or CI. -->

## How To Test

<!-- Paste commands run and any manual verification. If not tested, say why. -->

## Reviewer Notes

<!-- Anything reviewers should focus on? Keep blank if none. -->

## Change Type

- [ ] New skill or plugin
- [ ] Update to existing skill(s)
- [ ] Repo/config/docs only (template, README, marketplace, etc.)
- [ ] Other (describe below)

## Checklist

- [ ] Skill frontmatter `name` matches its directory and has a concise `description`
- [ ] New skills use `disable-model-invocation: true` unless natural-language activation is intentional
- [ ] New or changed plugins keep Claude and Codex manifests/marketplaces in sync
- [ ] README or repo guidance updated if workflow changed
- [ ] Tests or validation commands are listed above

## AI Tooling Contribution

If AI helped, check one score per metric. Keep any notes short.

**ai_speed_boost_impact**

- [ ] 0 — Human-only, no AI assist
- [ ] 1 — Light suggestions
- [ ] 2 — Minor snippets/fixes
- [ ] 3 — Noticeable implementation or debugging help
- [ ] 4 — AI wrote large chunks; author directed/reviewed
- [ ] 5 — AI heavy lift; author validated/polished

**ai_ideation_help_impact**

- [ ] 0 — No ideation help
- [ ] 1 — Tiny spark
- [ ] 2 — A few useful ideas/unblocks
- [ ] 3 — Clear direction from prompts
- [ ] 4 — Shaped the solution significantly
- [ ] 5 — Co-designed the approach

## AI Documentation Usage

- **docs_used**: <!-- e.g., CLAUDE.md, README.md, skill-review-rubric.md -->
- **docs_helpfulness_score**: <!-- 0-5 -->
- **what_worked_well**:
- **gaps**:
