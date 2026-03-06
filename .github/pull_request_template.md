## Description

<!-- What does this PR do? -->

## Type of change

- [ ] New skill or plugin
- [ ] Update to existing skill(s)
- [ ] Repo/config/docs only (template, README, marketplace, etc.)
- [ ] Other (describe below)

## How to test / verify

<!-- Steps for reviewers to validate -->

## Checklist

- [ ] Skill(s) follow the [Agent Skills spec](https://agentskills.io/specification) (frontmatter `name`, `description`)
- [ ] If adding a **new plugin** it is registered in `.claude-plugin/marketplace.json`
- [ ] README or docs updated if needed

## AI Tooling Contribution

Please provide an impact score (0-5 scale) for using AI Code Editor tools (e.g., Cursor, GitHub Copilot, Windsurf, etc.) in the relevant phases of this PR

> [!NOTE]
> Check exactly one per metric for each section

- **ai_speed_boost_impact**

  - [ ] 0 — _Human-only, no AI assist_
  - [ ] 1 — _Light suggestions; manual flow._
  - [ ] 2 — _Minor speed-ups (fixes/snippets)._
  - [ ] 3 — _Noticeable boost (tests/debugging/scaffolding)._
  - [ ] 4 — _AI wrote large chunks; I orchestrated._
  - [ ] 5 — _AI heavy-lift; I polished._

- **ai_ideation_help_impact**

  - [ ] 0 — _No ideation help needed._
  - [ ] 1 — _Tiny spark; mostly my plan._
  - [ ] 2 — _A few useful ideas/unblocks._
  - [ ] 3 — _Clear direction from prompts._
  - [ ] 4 — _Shaped the solution significantly._
  - [ ] 5 — _Co-designed the approach._

## AI Documentation Usage

This section will be populated automatically by the AI Code Editor tools (e.g., Cursor, GitHub Copilot, Windsurf, etc.) assistant to summarize how project documentation/rule files guided its output.

- **docs_used**: \_\_ [e.g., .cursor/rules/backend.mdc, .windsurf/rules/backend.md] (Comma-separated list of **repo-relative rule file paths that actually exist in the codebase**)\_

- **docs_helpfulness_score**: \_\_ [e.g., 4] (0-5 numeric assessment of how useful the referenced docs were)\_

- **what_worked_well**: \_\_ [e.g., The backend-security rule clarified input validation pattern which saved time.]\_

- **gaps**: \_\_ [e.g., No rule for batch processing patterns, unclear lock duration convention.]\_
